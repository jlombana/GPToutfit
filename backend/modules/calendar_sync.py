"""Calendar synchronization module for GPToutfit (FR-44).

Fetches events from Google Calendar or Microsoft Outlook APIs and
generates occasion hints via GPT-4o-mini. Never persists events to disk.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from openai import AsyncOpenAI

from backend.config import settings
from backend.modules.retry import call_openai_with_retry

logger = logging.getLogger(__name__)


async def fetch_google_events(access_token: str, days_ahead: int = 30) -> list[dict]:
    """Fetch events from Google Calendar API v3.

    Args:
        access_token: OAuth2 access token with calendar.readonly scope.
        days_ahead: Number of days ahead to fetch events.

    Returns:
        List of raw event dicts from Google Calendar API.
    """
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            params={
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 50,
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15.0,
        )

    if resp.status_code == 401:
        raise PermissionError("Google Calendar token expired")
    resp.raise_for_status()
    return resp.json().get("items", [])


async def fetch_outlook_events(access_token: str, days_ahead: int = 30) -> list[dict]:
    """Fetch events from Microsoft Graph Calendar API.

    Args:
        access_token: OAuth2 access token with Calendars.Read scope.
        days_ahead: Number of days ahead to fetch events.

    Returns:
        List of raw event dicts from Microsoft Graph API.
    """
    now = datetime.now(timezone.utc)
    start = now.strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
    end = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://graph.microsoft.com/v1.0/me/calendarView",
            params={"startDateTime": start, "endDateTime": end, "$orderby": "start/dateTime", "$top": 50},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15.0,
        )

    if resp.status_code == 401:
        raise PermissionError("Outlook Calendar token expired")
    resp.raise_for_status()
    return resp.json().get("value", [])


def _normalize_google_event(raw: dict) -> dict[str, Any]:
    """Convert a Google Calendar event to our standard format."""
    start = raw.get("start", {})
    dt_str = start.get("dateTime", start.get("date", ""))
    date_obj = _parse_date(dt_str)
    return {
        "id": raw.get("id", ""),
        "title": raw.get("summary", "Untitled Event"),
        "date": date_obj.strftime("%Y-%m-%d") if date_obj else "",
        "time": date_obj.strftime("%H:%M") if date_obj and "dateTime" in start else "",
        "location": raw.get("location", ""),
        "occasion_hint": "",
    }


def _normalize_outlook_event(raw: dict) -> dict[str, Any]:
    """Convert a Microsoft Graph event to our standard format."""
    start = raw.get("start", {})
    dt_str = start.get("dateTime", "")
    date_obj = _parse_date(dt_str)
    location = raw.get("location", {})
    loc_name = location.get("displayName", "") if isinstance(location, dict) else ""
    return {
        "id": raw.get("id", ""),
        "title": raw.get("subject", "Untitled Event"),
        "date": date_obj.strftime("%Y-%m-%d") if date_obj else "",
        "time": date_obj.strftime("%H:%M") if date_obj else "",
        "location": loc_name,
        "occasion_hint": "",
    }


def _parse_date(dt_str: str) -> Optional[datetime]:
    """Parse various date/datetime formats."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


async def generate_occasion_hints(events: list[dict]) -> list[dict]:
    """Use GPT-4o-mini to generate occasion hints for each event.

    Args:
        events: List of normalized event dicts.

    Returns:
        Same list with occasion_hint populated.
    """
    if not events:
        return events

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Batch all events into a single prompt for efficiency
    event_lines = []
    for i, evt in enumerate(events):
        line = f"{i+1}. \"{evt['title']}\" on {evt['date']}"
        if evt.get("time"):
            line += f" at {evt['time']}"
        if evt.get("location"):
            line += f" ({evt['location']})"
        event_lines.append(line)

    prompt = (
        "For each calendar event below, generate a concise one-line occasion "
        "description suitable for outfit recommendations. Be specific about "
        "formality level and setting.\n\n"
        + "\n".join(event_lines)
        + "\n\nRespond with one line per event, numbered to match. "
        "Example: 1. Casual dinner at an Italian restaurant, evening, smart casual"
    )

    async def _call() -> str:
        response = await client.responses.create(
            model=settings.guardrail_model,
            instructions="You are a concise fashion occasion classifier.",
            input=prompt,
        )
        return response.output_text or ""

    try:
        raw = await call_openai_with_retry(_call)
        lines = raw.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Parse "1. description"
            dot_idx = line.find(".")
            if dot_idx > 0 and dot_idx <= 3:
                try:
                    idx = int(line[:dot_idx]) - 1
                    hint = line[dot_idx + 1:].strip()
                    if 0 <= idx < len(events):
                        events[idx]["occasion_hint"] = hint
                except ValueError:
                    pass
    except Exception:
        logger.exception("Failed to generate occasion hints")

    # Fallback: use title as hint if GPT failed
    for evt in events:
        if not evt["occasion_hint"]:
            evt["occasion_hint"] = evt["title"]

    return events


async def sync_calendar(
    provider: str, access_token: str, days_ahead: int = 30
) -> list[dict]:
    """Full calendar sync: fetch events, normalize, generate hints.

    Args:
        provider: "google" or "outlook".
        access_token: OAuth2 access token.
        days_ahead: Number of days to look ahead.

    Returns:
        List of event dicts with occasion hints.

    Raises:
        PermissionError: If the token is expired/invalid.
        ValueError: If the provider is unknown.
    """
    if provider == "google":
        raw_events = await fetch_google_events(access_token, days_ahead)
        events = [_normalize_google_event(e) for e in raw_events]
    elif provider == "outlook":
        raw_events = await fetch_outlook_events(access_token, days_ahead)
        events = [_normalize_outlook_event(e) for e in raw_events]
    else:
        raise ValueError(f"Unknown calendar provider: {provider}")

    # Filter out empty/cancelled events
    events = [e for e in events if e["title"] and e["date"]]

    events = await generate_occasion_hints(events)

    logger.info("[CALENDAR] provider=%s events=%d days=%d", provider, len(events), days_ahead)
    return events

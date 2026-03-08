"""Calendar OAuth and sync routes for GPToutfit (FR-44).

Provides OAuth flows for Google Calendar and Microsoft Outlook,
plus a sync endpoint that fetches events and generates occasion hints.
"""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.config import settings
from backend.modules.calendar_demo import get_demo_events
from backend.modules.calendar_sync import sync_calendar

router = APIRouter(prefix="/wardrobe/calendar")
logger = logging.getLogger(__name__)

# --- Google Calendar OAuth ---

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


@router.get("/auth/google")
async def google_auth() -> RedirectResponse:
    """Redirect to Google OAuth consent screen."""
    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="Google Calendar not configured")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/auth/google/callback")
async def google_callback(code: str = "") -> RedirectResponse:
    """Exchange Google auth code for access token and redirect to frontend."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15.0,
        )

    if resp.status_code != 200:
        logger.error("Google token exchange failed: %s", resp.text)
        raise HTTPException(status_code=502, detail="Failed to exchange Google auth code")

    token_data = resp.json()
    access_token = token_data.get("access_token", "")
    # Never log the actual token
    logger.info("[GOOGLE-AUTH] Token exchange successful")

    return RedirectResponse(f"/?calendar_token={access_token}&calendar_provider=google")


# --- Microsoft Outlook OAuth ---

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MICROSOFT_SCOPE = "Calendars.Read"


@router.get("/auth/outlook")
async def outlook_auth() -> RedirectResponse:
    """Redirect to Microsoft OAuth consent screen."""
    if not settings.microsoft_client_id:
        raise HTTPException(status_code=500, detail="Microsoft Calendar not configured")

    params = {
        "client_id": settings.microsoft_client_id,
        "redirect_uri": settings.microsoft_redirect_uri,
        "response_type": "code",
        "scope": f"openid {MICROSOFT_SCOPE}",
        "prompt": "consent",
    }
    return RedirectResponse(f"{MICROSOFT_AUTH_URL}?{urlencode(params)}")


@router.get("/auth/outlook/callback")
async def outlook_callback(code: str = "") -> RedirectResponse:
    """Exchange Microsoft auth code for access token and redirect to frontend."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            MICROSOFT_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "redirect_uri": settings.microsoft_redirect_uri,
                "grant_type": "authorization_code",
                "scope": f"openid {MICROSOFT_SCOPE}",
            },
            timeout=15.0,
        )

    if resp.status_code != 200:
        logger.error("Microsoft token exchange failed: %s", resp.text)
        raise HTTPException(status_code=502, detail="Failed to exchange Microsoft auth code")

    token_data = resp.json()
    access_token = token_data.get("access_token", "")
    logger.info("[OUTLOOK-AUTH] Token exchange successful")

    return RedirectResponse(f"/?calendar_token={access_token}&calendar_provider=outlook")


# --- Calendar Sync ---


class CalendarSyncRequest(BaseModel):
    """Request body for calendar sync."""
    provider: str
    access_token: str
    days_ahead: int = 30


@router.post("/sync")
async def calendar_sync(req: CalendarSyncRequest) -> dict:
    """Sync calendar events and generate occasion hints.

    Returns list of upcoming events with AI-generated occasion descriptions.
    Never stores events or tokens on disk.
    """
    if req.provider not in ("google", "outlook"):
        raise HTTPException(status_code=400, detail="provider must be 'google' or 'outlook'")

    try:
        events = await sync_calendar(
            provider=req.provider,
            access_token=req.access_token,
            days_ahead=req.days_ahead,
        )
    except PermissionError:
        raise HTTPException(status_code=401, detail="Calendar token expired. Please reconnect.")
    except Exception as exc:
        logger.exception("Calendar sync failed")
        raise HTTPException(status_code=500, detail="Calendar sync failed") from exc

    return {"events": events}


# --- Demo Calendar (FR-49) ---


class DemoCalendarRequest(BaseModel):
    """Request body for demo calendar events."""
    username: str


@router.post("/demo")
async def calendar_demo(req: DemoCalendarRequest) -> dict:
    """Get hardcoded demo calendar events for a user.

    No OAuth needed — returns pre-configured events with occasion hints.
    """
    events = get_demo_events(req.username.strip().lower())
    return {"events": events, "demo": True}

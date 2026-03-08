"""Calendar demo events for GPToutfit (FR-49).

Provides hardcoded calendar events for demo users (no real OAuth needed).
Each user can have pre-configured events with occasion hints.
"""

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Hardcoded demo events for Javier — 5 events spanning the next 2 weeks
def _generate_javier_events() -> list[dict]:
    """Generate 5 demo events for Javier, relative to today's date."""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return [
        {
            "id": "demo-javier-1",
            "title": "Team Standup & Sprint Review",
            "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "09:30",
            "location": "Office — Conference Room B",
            "occasion_hint": "Professional office meeting, business casual dress code, daytime indoor setting",
            "editable": True,
        },
        {
            "id": "demo-javier-2",
            "title": "Dinner with Laura",
            "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "time": "20:00",
            "location": "Nobu Restaurant",
            "occasion_hint": "Romantic dinner at an upscale Japanese restaurant, evening, smart casual to semi-formal",
            "editable": True,
        },
        {
            "id": "demo-javier-3",
            "title": "Saturday Brunch with Friends",
            "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "time": "11:30",
            "location": "The Ivy Chelsea Garden",
            "occasion_hint": "Weekend brunch at a trendy outdoor terrace, relaxed smart casual, daytime",
            "editable": True,
        },
        {
            "id": "demo-javier-4",
            "title": "Client Presentation — Q2 Strategy",
            "date": (today + timedelta(days=8)).strftime("%Y-%m-%d"),
            "time": "14:00",
            "location": "WeWork Moorgate, 5th Floor",
            "occasion_hint": "Formal client-facing business presentation, full business attire, professional setting",
            "editable": True,
        },
        {
            "id": "demo-javier-5",
            "title": "Weekend Getaway — Cotswolds",
            "date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "time": "10:00",
            "location": "Soho Farmhouse, Oxfordshire",
            "occasion_hint": "Rural countryside weekend getaway, layered casual outdoor wear, autumn countryside style",
            "editable": True,
        },
    ]


# Registry of demo events per user
DEMO_EVENTS: dict[str, callable] = {
    "javier": _generate_javier_events,
}


def get_demo_events(username: str) -> list[dict]:
    """Get demo calendar events for a given user.

    Args:
        username: Lowercase username (e.g. "javier").

    Returns:
        List of demo event dicts, or empty list if user has no demo events.
    """
    generator = DEMO_EVENTS.get(username)
    if generator:
        events = generator()
        logger.info("[CALENDAR-DEMO] Loaded %d events for user '%s'", len(events), username)
        return events
    return []

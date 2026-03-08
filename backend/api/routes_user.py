"""User data routes for GPToutfit (FR-46).

Provides endpoints for user wardrobe persistence and search history.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.modules.database import (
    add_wardrobe_item,
    clear_wardrobe,
    get_search_history,
    get_wardrobe,
    remove_wardrobe_item,
    save_wardrobe,
)

router = APIRouter(prefix="/user")
logger = logging.getLogger(__name__)


class WardrobeItem(BaseModel):
    """Single wardrobe item."""
    id: str
    productDisplayName: Optional[str] = ""
    name: Optional[str] = ""
    articleType: Optional[str] = ""
    baseColour: Optional[str] = ""
    image_url: Optional[str] = ""
    price: Optional[float] = None
    source: Optional[str] = ""


class WardrobeSyncRequest(BaseModel):
    """Full wardrobe sync request."""
    items: list[WardrobeItem]


@router.get("/{username}/wardrobe")
async def get_user_wardrobe(username: str) -> dict:
    """Get all wardrobe items for a user."""
    items = get_wardrobe(username.strip().lower())
    return {"items": items, "count": len(items)}


@router.post("/{username}/wardrobe")
async def sync_user_wardrobe(username: str, req: WardrobeSyncRequest) -> dict:
    """Sync (replace) all wardrobe items for a user."""
    uname = username.strip().lower()
    items_dicts = [item.dict() for item in req.items]
    count = save_wardrobe(uname, items_dicts)
    return {"saved": count}


@router.post("/{username}/wardrobe/item")
async def add_user_wardrobe_item(username: str, item: WardrobeItem) -> dict:
    """Add a single item to user's wardrobe."""
    uname = username.strip().lower()
    added = add_wardrobe_item(uname, item.dict())
    return {"added": added}


@router.delete("/{username}/wardrobe/{item_id}")
async def delete_user_wardrobe_item(username: str, item_id: str) -> dict:
    """Remove a single item from user's wardrobe."""
    uname = username.strip().lower()
    removed = remove_wardrobe_item(uname, item_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Item not found in wardrobe")
    return {"removed": True}


@router.delete("/{username}/wardrobe")
async def clear_user_wardrobe(username: str) -> dict:
    """Clear all wardrobe items for a user."""
    uname = username.strip().lower()
    count = clear_wardrobe(uname)
    return {"cleared": count}


@router.get("/{username}/history")
async def get_user_history(username: str, limit: int = 20) -> dict:
    """Get recent search history for a user."""
    history = get_search_history(username.strip().lower(), limit)
    return {"history": history}

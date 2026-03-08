"""SQLite database module for GPToutfit (FR-46).

Manages user wardrobe persistence and search history using SQLite.
Database file: data/user_data.db
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "user_data.db"
_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    """Get or create the SQLite connection (singleton)."""
    global _conn
    if _conn is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_tables(_conn)
        logger.info("[DB] Connected to %s", _DB_PATH)
    return _conn


def _init_tables(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS wardrobe_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            item_id TEXT NOT NULL,
            product_name TEXT DEFAULT '',
            article_type TEXT DEFAULT '',
            base_colour TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            price REAL,
            source TEXT DEFAULT '',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, item_id)
        );

        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            search_type TEXT NOT NULL,
            query_text TEXT DEFAULT '',
            search_mode TEXT DEFAULT '',
            result_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_wardrobe_user ON wardrobe_items(username);
        CREATE INDEX IF NOT EXISTS idx_history_user ON search_history(username);
    """)
    conn.commit()


def get_wardrobe(username: str) -> list[dict]:
    """Get all wardrobe items for a user.

    Args:
        username: Lowercase username.

    Returns:
        List of wardrobe item dicts.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM wardrobe_items WHERE username = ? ORDER BY added_at DESC",
        (username,),
    ).fetchall()
    return [
        {
            "id": row["item_id"],
            "productDisplayName": row["product_name"],
            "articleType": row["article_type"],
            "baseColour": row["base_colour"],
            "image_url": row["image_url"],
            "price": row["price"],
            "source": row["source"],
        }
        for row in rows
    ]


def save_wardrobe(username: str, items: list[dict]) -> int:
    """Replace all wardrobe items for a user (full sync).

    Args:
        username: Lowercase username.
        items: List of wardrobe item dicts.

    Returns:
        Number of items saved.
    """
    conn = _get_conn()
    conn.execute("DELETE FROM wardrobe_items WHERE username = ?", (username,))
    for item in items:
        conn.execute(
            """INSERT OR REPLACE INTO wardrobe_items
               (username, item_id, product_name, article_type, base_colour, image_url, price, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                username,
                str(item.get("id", "")),
                item.get("productDisplayName", item.get("name", "")),
                item.get("articleType", ""),
                item.get("baseColour", ""),
                item.get("image_url", ""),
                item.get("price"),
                item.get("source", ""),
            ),
        )
    conn.commit()
    logger.info("[DB] Saved %d wardrobe items for '%s'", len(items), username)
    return len(items)


def add_wardrobe_item(username: str, item: dict) -> bool:
    """Add a single item to user's wardrobe.

    Args:
        username: Lowercase username.
        item: Wardrobe item dict.

    Returns:
        True if inserted, False if already exists.
    """
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO wardrobe_items
               (username, item_id, product_name, article_type, base_colour, image_url, price, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                username,
                str(item.get("id", "")),
                item.get("productDisplayName", item.get("name", "")),
                item.get("articleType", ""),
                item.get("baseColour", ""),
                item.get("image_url", ""),
                item.get("price"),
                item.get("source", ""),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def remove_wardrobe_item(username: str, item_id: str) -> bool:
    """Remove a single item from user's wardrobe.

    Args:
        username: Lowercase username.
        item_id: Item ID to remove.

    Returns:
        True if removed, False if not found.
    """
    conn = _get_conn()
    cursor = conn.execute(
        "DELETE FROM wardrobe_items WHERE username = ? AND item_id = ?",
        (username, item_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def clear_wardrobe(username: str) -> int:
    """Remove all wardrobe items for a user.

    Args:
        username: Lowercase username.

    Returns:
        Number of items removed.
    """
    conn = _get_conn()
    cursor = conn.execute(
        "DELETE FROM wardrobe_items WHERE username = ?", (username,)
    )
    conn.commit()
    return cursor.rowcount


def add_search_history(
    username: str, search_type: str, query_text: str,
    search_mode: str = "", result_count: int = 0
) -> None:
    """Record a search in the history.

    Args:
        username: Lowercase username.
        search_type: "stylist", "discover", or "keyword".
        query_text: The search query or occasion text.
        search_mode: "complementary" or "similarity" (for stylist).
        result_count: Number of results returned.
    """
    conn = _get_conn()
    conn.execute(
        """INSERT INTO search_history (username, search_type, query_text, search_mode, result_count)
           VALUES (?, ?, ?, ?, ?)""",
        (username, search_type, query_text, search_mode, result_count),
    )
    conn.commit()


def get_search_history(username: str, limit: int = 20) -> list[dict]:
    """Get recent search history for a user.

    Args:
        username: Lowercase username.
        limit: Max number of records.

    Returns:
        List of search history dicts.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM search_history WHERE username = ? ORDER BY created_at DESC LIMIT ?",
        (username, limit),
    ).fetchall()
    return [dict(row) for row in rows]

"""Mock inventory and pricing module.

Returns simulated stock availability and pricing for catalog items.
In production, replace with calls to RetailNext inventory and pricing APIs.
"""
import hashlib


def get_inventory_status(item_id: str) -> dict:
    """Return mock inventory status for a catalog item.

    Args:
        item_id: Catalog item identifier.

    Returns:
        Dict with status, label, quantity, and price fields.
    """
    h = int(hashlib.md5(item_id.encode()).hexdigest(), 16)
    status_idx = h % 4
    statuses = [
        {"status": "in_stock", "label": "In Stock", "quantity": 8},
        {"status": "low_stock", "label": "Low Stock", "quantity": 2},
        {"status": "online_only", "label": "Online Only", "quantity": 0},
        {"status": "in_stock", "label": "In Stock", "quantity": 15},
    ]
    result = statuses[status_idx]
    # Mock price: deterministic $29-$189 range based on item_id
    price_cents = 2900 + (h % 1600) * 10
    result["price"] = round(price_cents / 100, 2)
    return result

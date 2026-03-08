"""Feedback storage module for like/dislike actions."""

_feedback: dict[str, list] = {"likes": [], "dislikes": []}


def record_feedback(item_id: str, action: str) -> None:
    """Append item_id to the appropriate list."""
    if action == "like":
        _feedback["likes"].append(item_id)
    elif action == "dislike":
        _feedback["dislikes"].append(item_id)


def get_feedback_summary() -> dict:
    """Return summary counts for likes and dislikes."""
    return {"likes": len(_feedback["likes"]), "dislikes": len(_feedback["dislikes"])}

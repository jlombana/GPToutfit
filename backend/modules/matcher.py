"""RAG matching module using cosine similarity.

Finds complementary or similar clothing items by comparing embedding vectors,
applying gender/articleType filters, and returning top-K results.

Supports two modes:
- "complementary": finds items that complete an outfit (different categories)
- "similarity": finds visually/stylistically similar items (same category)

See TASK-06 in docs/TASKS.md for implementation spec.
"""
import logging

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Complement map: articleType -> list of complementary articleTypes
# ---------------------------------------------------------------------------
COMPLEMENT_MAP = {
    # Tops (men/women)
    "Shirts":         ["Jeans", "Trousers", "Shorts", "Casual Shoes", "Formal Shoes",
                       "Belts", "Jackets", "Blazers", "Watches", "Ties"],
    "Tshirts":        ["Jeans", "Shorts", "Casual Shoes", "Sneakers", "Jackets",
                       "Sports Shoes", "Sweatshirts", "Caps", "Backpacks"],
    "Sweatshirts":    ["Jeans", "Track Pants", "Casual Shoes", "Sneakers",
                       "Sports Shoes", "Caps", "Backpacks"],
    "Jackets":        ["Jeans", "Trousers", "Shirts", "Tshirts", "Casual Shoes",
                       "Formal Shoes", "Scarves"],
    "Blazers":        ["Trousers", "Formal Shoes", "Shirts", "Ties", "Watches",
                       "Belts"],
    "Kurtas":         ["Jeans", "Leggings", "Sandals", "Flats", "Earrings",
                       "Clutches"],
    "Kurtis":         ["Leggings", "Jeans", "Flats", "Sandals", "Earrings",
                       "Handbags"],
    "Tops":           ["Jeans", "Skirts", "Shorts", "Casual Shoes", "Heels", "Flats",
                       "Sandals", "Handbags", "Earrings"],
    "Sweaters":       ["Jeans", "Trousers", "Casual Shoes", "Formal Shoes", "Scarves"],
    "Tunics":         ["Jeans", "Leggings", "Flats", "Sandals", "Handbags"],

    # Bottoms
    "Jeans":          ["Shirts", "Tshirts", "Casual Shoes", "Sneakers", "Jackets",
                       "Belts", "Tops", "Sweatshirts", "Sports Shoes", "Watches"],
    "Trousers":       ["Shirts", "Formal Shoes", "Belts", "Blazers", "Jackets",
                       "Watches", "Ties"],
    "Shorts":         ["Tshirts", "Sneakers", "Casual Shoes", "Sandals", "Sports Shoes",
                       "Tops", "Caps", "Sunglasses"],
    "Track Pants":    ["Tshirts", "Sweatshirts", "Sports Shoes", "Sneakers", "Caps",
                       "Backpacks"],
    "Skirts":         ["Tops", "Shirts", "Heels", "Flats", "Sandals", "Casual Shoes",
                       "Handbags"],

    # Dresses
    "Dresses":        ["Heels", "Flats", "Sandals", "Casual Shoes", "Jackets",
                       "Handbags", "Earrings", "Clutches"],
    "Sarees":         ["Kurtas", "Heels", "Sandals", "Flats", "Earrings", "Clutches"],
    "Night suits":    ["Flip Flops", "Sandals"],

    # Footwear
    "Casual Shoes":   ["Jeans", "Shorts", "Tshirts", "Shirts", "Jackets", "Backpacks"],
    "Formal Shoes":   ["Trousers", "Shirts", "Belts", "Blazers", "Watches"],
    "Heels":          ["Dresses", "Skirts", "Jeans", "Trousers", "Tops", "Clutches",
                       "Handbags"],
    "Flats":          ["Dresses", "Skirts", "Jeans", "Kurtas", "Kurtis", "Tops",
                       "Handbags"],
    "Sandals":        ["Dresses", "Shorts", "Skirts", "Kurtas", "Tops", "Sunglasses"],
    "Sneakers":       ["Jeans", "Shorts", "Tshirts", "Sweatshirts", "Track Pants",
                       "Backpacks", "Caps"],
    "Sports Shoes":   ["Track Pants", "Shorts", "Tshirts", "Sweatshirts", "Backpacks"],
    "Flip Flops":     ["Shorts", "Tshirts", "Sunglasses"],

    # Accessories
    "Watches":        ["Shirts", "Blazers", "Trousers", "Formal Shoes", "Belts"],
    "Belts":          ["Jeans", "Trousers", "Shirts", "Formal Shoes", "Blazers"],
    "Ties":           ["Shirts", "Blazers", "Trousers", "Formal Shoes"],
    "Sunglasses":     ["Tshirts", "Shirts", "Dresses", "Shorts", "Casual Shoes"],
    "Handbags":       ["Dresses", "Tops", "Jeans", "Heels", "Flats", "Skirts"],
    "Clutches":       ["Dresses", "Heels", "Sarees", "Earrings"],
    "Backpacks":      ["Tshirts", "Jeans", "Sneakers", "Shorts", "Caps"],
    "Wallets":        ["Jeans", "Trousers", "Belts", "Formal Shoes"],
    "Caps":           ["Tshirts", "Jeans", "Sneakers", "Shorts", "Sunglasses"],
    "Earrings":       ["Dresses", "Tops", "Kurtas", "Sarees", "Heels"],
    "Scarves":        ["Jackets", "Sweaters", "Shirts", "Jeans", "Trousers"],
}

DEFAULT_COMPLEMENTS = ["Jeans", "Casual Shoes", "Shirts", "Tshirts", "Jackets",
                       "Tops", "Dresses", "Heels", "Watches", "Handbags",
                       "Sunglasses", "Belts"]

# Maps GPT-4o-mini article type variations to canonical COMPLEMENT_MAP keys
ARTICLE_TYPE_ALIASES: dict[str, str] = {
    "polo shirt": "Shirts",
    "polo shirts": "Shirts",
    "polo": "Shirts",
    "button-down shirt": "Shirts",
    "dress shirt": "Shirts",
    "oxford shirt": "Shirts",
    "henley": "Tshirts",
    "tank top": "Tshirts",
    "crop top": "Tops",
    "blouse": "Tops",
    "tunic": "Tops",
    "cardigan": "Sweaters",
    "pullover": "Sweaters",
    "hoodie": "Sweatshirts",
    "hoodies": "Sweatshirts",
    "joggers": "Track Pants",
    "chinos": "Trousers",
    "pants": "Trousers",
    "leggings": "Track Pants",
    "suit jacket": "Blazers",
    "sport coat": "Blazers",
    "coat": "Jackets",
    "overcoat": "Jackets",
    "parka": "Jackets",
    "boots": "Casual Shoes",
    "loafers": "Formal Shoes",
    "oxfords": "Formal Shoes",
    "trainers": "Sneakers",
    "running shoes": "Sports Shoes",
    "pumps": "Heels",
    "stilettos": "Heels",
    "wedges": "Heels",
    "mules": "Flats",
    "espadrilles": "Flats",
    "jumpsuit": "Dresses",
    "romper": "Dresses",
    "gown": "Dresses",
    "maxi dress": "Dresses",
    "mini dress": "Dresses",
    "midi dress": "Dresses",
    "kurta": "Kurtas",
    "kurti": "Kurtis",
    "saree": "Sarees",
    "sari": "Sarees",
    "belt": "Belts",
    "tie": "Ties",
    "night suit": "Night suits",
    "pajamas": "Night suits",
    "pyjamas": "Night suits",
    # Accessories
    "watch": "Watches",
    "wristwatch": "Watches",
    "sunglasses": "Sunglasses",
    "shades": "Sunglasses",
    "handbag": "Handbags",
    "purse": "Handbags",
    "tote": "Handbags",
    "tote bag": "Handbags",
    "clutch": "Clutches",
    "clutch bag": "Clutches",
    "backpack": "Backpacks",
    "rucksack": "Backpacks",
    "wallet": "Wallets",
    "cap": "Caps",
    "baseball cap": "Caps",
    "hat": "Caps",
    "beanie": "Caps",
    "earring": "Earrings",
    "stud earrings": "Earrings",
    "scarf": "Scarves",
    "muffler": "Scarves",
    "sneaker": "Sneakers",
    "socks": "Socks",
    "briefs": "Briefs",
    "boxer": "Briefs",
    "bra": "Bra",
    "sports bra": "Bra",
}


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity score (0.0 if either vector has zero norm).
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _normalize_article_type(article_type: str) -> str:
    """Normalize articleType for comparison (handle singular/plural)."""
    return article_type.strip().lower().rstrip("s")


def _resolve_article_type(article_type: str) -> str:
    """Resolve an article type to its canonical COMPLEMENT_MAP key."""
    at = article_type.strip()
    # Exact match
    if at in COMPLEMENT_MAP:
        return at
    # Alias lookup (case-insensitive)
    alias_key = at.lower()
    if alias_key in ARTICLE_TYPE_ALIASES:
        return ARTICLE_TYPE_ALIASES[alias_key]
    # Normalized match against COMPLEMENT_MAP keys
    norm = _normalize_article_type(at)
    for key in COMPLEMENT_MAP:
        if _normalize_article_type(key) == norm:
            return key
    # Substring match: check if any COMPLEMENT_MAP key is contained in the type
    at_lower = at.lower()
    for key in COMPLEMENT_MAP:
        if key.lower() in at_lower or at_lower in key.lower():
            return key
    return at


def _get_complement_types(article_type: str) -> list[str]:
    """Look up complementary article types from the COMPLEMENT_MAP."""
    resolved = _resolve_article_type(article_type)
    logger.info("[COMPLEMENT] '%s' resolved to '%s'", article_type, resolved)
    if resolved in COMPLEMENT_MAP:
        return COMPLEMENT_MAP[resolved]
    return DEFAULT_COMPLEMENTS


def find_matches(
    query_embedding: list[float],
    catalog: list[dict],
    cached_embeddings: dict,
    query_gender: str,
    query_article_type: str,
    threshold: float = 0.6,
    top_k: int = 2,
    search_mode: str = "complementary",
) -> list[dict]:
    """Find top-K matching items from the catalog.

    Args:
        query_embedding: Embedding vector of the uploaded item description.
        catalog: List of catalog item dicts.
        cached_embeddings: Dict mapping item_id to embedding vector.
        query_gender: Gender of the uploaded item.
        query_article_type: Article type of the uploaded item.
        threshold: Minimum cosine similarity score.
        top_k: Maximum number of results to return.
        search_mode: "complementary" or "similarity".

    Returns:
        List of matching item dicts with added similarity_score field,
        sorted by score descending.
    """
    resolved_type = _resolve_article_type(query_article_type or "")
    q_norm = _normalize_article_type(resolved_type)
    q_gender_lower = (query_gender or "").strip().lower()

    # Determine allowed article types based on search mode
    if search_mode == "similarity":
        # Only items of the SAME type (using resolved canonical type)
        logger.info("[SIMILARITY] Input type: %s (resolved: %s)", query_article_type, resolved_type)
    else:
        # Complementary: only items of DIFFERENT, complementary types
        complement_types = _get_complement_types(query_article_type or "")
        complement_norms = {_normalize_article_type(t) for t in complement_types}
        logger.info("[COMPLEMENTARY] Input type: %s → searching in: %s",
                    query_article_type, complement_types)

    candidates: list[dict] = []
    candidate_ids: list = []
    for item in catalog:
        g = str(item.get("gender", "") or "").strip().lower()
        at = str(item.get("articleType", "") or "")
        at_norm = _normalize_article_type(at)

        # Gender filter
        if q_gender_lower != "unisex" and g != "unisex" and g != q_gender_lower:
            continue

        # Article type filter based on mode
        if search_mode == "similarity":
            if at_norm != q_norm:
                continue
        else:
            if at_norm not in complement_norms:
                continue

        # Resolve embedding key
        item_id = item.get("id", "")
        emb_key = None
        str_key = str(item_id)
        if str_key in cached_embeddings:
            emb_key = str_key
        elif item_id in cached_embeddings:
            emb_key = item_id
        elif isinstance(item_id, (int, float)) and int(item_id) in cached_embeddings:
            emb_key = int(item_id)

        if emb_key is not None:
            candidates.append(item)
            candidate_ids.append(emb_key)

    logger.info("[%s] Candidates after filter: %d",
                search_mode.upper(), len(candidates))

    if not candidates:
        return []

    query_vec = np.array(query_embedding, dtype=np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []

    emb_matrix = np.array([cached_embeddings[cid] for cid in candidate_ids], dtype=np.float32)
    norms = np.linalg.norm(emb_matrix, axis=1)
    mask = norms > 0
    scores = np.zeros(len(candidates), dtype=np.float32)
    scores[mask] = emb_matrix[mask] @ query_vec / (norms[mask] * query_norm)

    # Relax threshold: cross-category scores lower, similarity also benefits from more candidates
    if search_mode == "complementary":
        effective_threshold = threshold * 0.60
    else:
        effective_threshold = threshold * 0.85
    logger.info("[%s] Threshold: %.3f (base %.3f), max score: %.4f, candidates: %d",
                search_mode.upper(), effective_threshold, threshold,
                float(scores.max()) if len(scores) > 0 else 0, len(candidates))

    # FR-48: Adaptive threshold — drop in 0.05 steps until min 6 results or 0.10 floor
    MIN_RESULTS = 6
    FLOOR_THRESHOLD = 0.10
    STEP = 0.05
    current_threshold = effective_threshold
    above = scores >= current_threshold
    while int(above.sum()) < MIN_RESULTS and current_threshold > FLOOR_THRESHOLD:
        current_threshold -= STEP
        if current_threshold < FLOOR_THRESHOLD:
            current_threshold = FLOOR_THRESHOLD
        above = scores >= current_threshold
        logger.info("[%s] Adaptive threshold lowered to %.3f → %d results",
                    search_mode.upper(), current_threshold, int(above.sum()))

    if not above.any():
        return []

    # Similarity benefits from more candidates for the guardrail to evaluate
    effective_top_k = top_k + 3 if search_mode == "similarity" else top_k
    indices = np.where(above)[0]
    top_indices = indices[np.argsort(-scores[indices])][:effective_top_k]

    results = []
    for idx in top_indices:
        match = dict(candidates[idx])
        match["similarity_score"] = float(scores[idx])
        results.append(match)

    return results

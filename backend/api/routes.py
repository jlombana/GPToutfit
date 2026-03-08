"""API route definitions for GPToutfit.

Defines the REST endpoints and orchestrates the analysis pipeline.
No business logic here -- delegates to modules.

See TASK-08 in docs/TASKS.md for implementation spec.
"""
import base64
import logging
from pathlib import Path

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from openai import AsyncOpenAI
from pydantic import BaseModel

from backend.config import settings
from backend.data import loader
from backend.modules import embeddings, guardrail, image_analyzer, matcher
from backend.modules.feedback import record_feedback
from backend.modules.inventory import get_inventory_status
from backend.modules.retry import call_openai_with_retry

router = APIRouter()
logger = logging.getLogger(__name__)

_IMAGES_DIR = Path(__file__).resolve().parents[2] / "sample_clothes" / "sample_images_large"
_catalog = None
_embeddings = None


def _get_data():
    """Load catalog/embeddings once and reuse across requests."""
    global _catalog, _embeddings
    if _catalog is None:
        _catalog = loader.load_catalog(settings.catalog_csv_path)
        _embeddings = embeddings.load_cached_embeddings(settings.embeddings_cache_path)
        sample = loader.build_description(_catalog[0]) if _catalog else "N/A"
        logger.info("Embeddings loaded (%d items). Sample: %s", len(_embeddings), sample)
    return _catalog, _embeddings


def _add_image_urls(matches: list[dict]) -> list[dict]:
    """Add image_url field to matches that have a product image on disk."""
    for match in matches:
        item_id = match.get("id", "")
        img_path = _IMAGES_DIR / f"{item_id}.jpg"
        if img_path.exists():
            match["image_url"] = f"/images/{item_id}.jpg"
    return matches


def _compute_match_label(score: float) -> dict:
    """Translate a raw cosine similarity score into a qualitative label."""
    if score >= 0.55:
        return {"match_label": "Perfect Match", "label_color": "#2D7A2D"}
    if score >= 0.45:
        return {"match_label": "Great Pick", "label_color": "#1A3A5C"}
    return {"match_label": "Style Edit", "label_color": "#B8860B"}


def _add_inventory(matches: list[dict]) -> list[dict]:
    """Attach mock inventory status to each match."""
    for match in matches:
        item_id = str(match.get("id", ""))
        if item_id:
            match["inventory"] = get_inventory_status(item_id)
    return matches


@router.post("/analyze")
async def analyze(
    image: UploadFile = File(default=None),
    occasion: str = Form(default=""),
    search_mode: str = Form(default="complementary"),
) -> dict:
    """Analyze uploaded clothing image and return validated outfit matches."""
    if image is None:
        raise HTTPException(status_code=400, detail="No image file provided")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="No image file provided")

    occasion = occasion.strip()
    search_mode = search_mode.strip() if search_mode in ("complementary", "similarity") else "complementary"

    try:
        uploaded_item = await image_analyzer.analyze_image(
            image_bytes, occasion=occasion, search_mode=search_mode,
        )
        query_embedding = await embeddings.generate_embedding(uploaded_item["description"])
        catalog, cached_embeddings = _get_data()

        candidate_matches = matcher.find_matches(
            query_embedding=query_embedding,
            catalog=catalog,
            cached_embeddings=cached_embeddings,
            query_gender=uploaded_item["gender"],
            query_article_type=uploaded_item["articleType"],
            threshold=settings.cosine_similarity_threshold,
            top_k=settings.top_k_matches,
            search_mode=search_mode,
        )
        validated_matches = await guardrail.validate_matches(
            original_description=uploaded_item["description"],
            candidates=candidate_matches,
            occasion=occasion,
            search_mode=search_mode,
        )
        validated_matches = _add_image_urls(validated_matches)
        validated_matches = _add_inventory(validated_matches)

        # Add match quality labels
        for m in validated_matches:
            score = m.get("similarity_score", 0)
            m.update(_compute_match_label(score))

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analyze pipeline failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    # Build base64 preview of the uploaded image for the frontend
    uploaded_preview = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"

    return {
        "uploaded_item": uploaded_item,
        "uploaded_preview": uploaded_preview,
        "occasion": occasion,
        "search_mode": search_mode,
        "matches": validated_matches,
    }

@router.get("/health")
async def health() -> dict:
    """Service liveness check endpoint."""
    return {"status": "ok"}


@router.post("/feedback")
async def feedback(body: dict) -> dict:
    """Record like/dislike feedback for a recommendation item."""
    item_id = body.get("item_id")
    action = body.get("action")
    if not item_id or action not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="item_id and action (like/dislike) required")
    record_feedback(str(item_id), action)
    return {"status": "recorded"}


class DiscoverRequest(BaseModel):
    """Request body for the wardrobe discover endpoint."""
    occasion: str
    gender: str
    style_vibe: str
    top_k: int = 20


class CompanionItem(BaseModel):
    """Single item for companion evaluation."""
    name: str
    category: str
    description: str = ""


class CompanionRequest(BaseModel):
    """Request body for the AI companion evaluation endpoint."""
    occasion: str
    items: list[CompanionItem]
    profile_context: str = ""
    purchase_context: str = ""


class FormalityRequest(BaseModel):
    """Request body for formality classification."""
    occasion: str


class TryOnBasketItem(BaseModel):
    """Single basket item for generative try-on."""
    name: str
    articleType: str = ""
    baseColour: str = ""
    productDisplayName: str = ""


class TryOnGenerativeRequest(BaseModel):
    """Request body for generative try-on endpoint (FR-42)."""
    person_image_base64: str = ""
    basket_items: list[TryOnBasketItem]
    gender: str
    style_vibe: str = ""
    cached_description: str = ""


class KeywordSearchRequest(BaseModel):
    """Request body for keyword search endpoint."""
    query: str
    gender: str = ""
    top_k: int = 6


@router.post("/api/classify-formality")
async def classify_formality(req: FormalityRequest) -> dict:
    """Classify an occasion into a formality tier via GPT-4o-mini."""
    occasion = req.occasion.strip()
    if not occasion:
        raise HTTPException(status_code=400, detail="occasion is required")

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        async def _classify() -> str:
            response = await client.responses.create(
                model=settings.guardrail_model,
                instructions=(
                    "Classify the following occasion into exactly one of these tiers: "
                    "Formal, Smart Casual, Casual, Active/Resort. "
                    "Return ONLY the tier name, nothing else."
                ),
                input=occasion,
            )
            return (response.output_text or "Casual").strip()

        tier = await call_openai_with_retry(_classify)

        # Validate tier
        valid_tiers = {"Formal", "Smart Casual", "Casual", "Active/Resort"}
        if tier not in valid_tiers:
            tier = "Casual"

        # Map tier to required categories
        tier_categories = {
            "Formal": ["Top", "Bottom", "Outerwear", "Footwear", "Accessory"],
            "Smart Casual": ["Top", "Bottom", "Footwear"],
            "Casual": ["Top", "Bottom", "Footwear"],
            "Active/Resort": ["Top", "Bottom"],
        }

        return {
            "tier": tier,
            "required_categories": tier_categories.get(tier, ["Top", "Bottom", "Footwear"]),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Formality classification failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/api/keyword-search")
async def keyword_search(req: KeywordSearchRequest) -> dict:
    """Keyword search — embeds text and returns cosine-similar catalog items.

    No GPT call in this path. Designed for speed (<2s).
    """
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    try:
        query_embedding = await embeddings.generate_embedding(query)
        catalog, cached_embeddings = _get_data()

        # Gender filter
        gender_lower = req.gender.strip().lower() if req.gender else ""
        candidates = []
        candidate_ids = []
        for item in catalog:
            if gender_lower and gender_lower != "non-binary":
                g = str(item.get("gender", "") or "").strip().lower()
                if g != "unisex" and g != gender_lower:
                    continue

            item_id = item.get("id", "")
            str_key = str(item_id)
            emb_key = None
            if str_key in cached_embeddings:
                emb_key = str_key
            elif item_id in cached_embeddings:
                emb_key = item_id
            elif isinstance(item_id, (int, float)) and int(item_id) in cached_embeddings:
                emb_key = int(item_id)

            if emb_key is not None:
                candidates.append(item)
                candidate_ids.append(emb_key)

        if not candidates:
            return {"items": [], "count": 0}

        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return {"items": [], "count": 0}

        emb_matrix = np.array(
            [cached_embeddings[cid] for cid in candidate_ids], dtype=np.float32
        )
        norms = np.linalg.norm(emb_matrix, axis=1)
        mask = norms > 0
        scores = np.zeros(len(candidates), dtype=np.float32)
        if mask.any():
            masked_emb = emb_matrix[mask]
            masked_norms = norms[mask]
            dot_products = masked_emb @ query_vec
            scores[mask] = dot_products / (masked_norms * query_norm)

        threshold = 0.30
        above = scores >= threshold
        if not above.any():
            return {"items": [], "count": 0}

        indices = np.where(above)[0]
        top_indices = indices[np.argsort(-scores[indices])][:req.top_k]

        results = []
        for idx in top_indices:
            item = candidates[idx]
            item_id = item.get("id", "")
            img_path = _IMAGES_DIR / f"{item_id}.jpg"
            results.append({
                "id": item_id,
                "name": item.get("productDisplayName", "Unnamed Item"),
                "articleType": item.get("articleType", ""),
                "baseColour": item.get("baseColour", ""),
                "gender": item.get("gender", ""),
                "image_url": f"/images/{item_id}.jpg" if img_path.exists() else "",
                "similarity_score": float(scores[idx]),
            })

        logger.info("[KEYWORD-SEARCH] query=%r gender=%s results=%d",
                    query, req.gender, len(results))
        return {"items": results, "count": len(results)}

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Keyword search failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/wardrobe/tryon-generative")
async def tryon_generative(req: TryOnGenerativeRequest) -> dict:
    """Generative Try-On via gpt-image-1 (with photo) or DALL-E 3 (model mode).

    With photo: uses images.edit + gpt-image-1 to dress the REAL person.
    Without photo: uses images.generate + dall-e-3 to create editorial image.
    Never persists person_image_base64 to disk or logs.
    """
    import io as _io

    if not req.basket_items:
        raise HTTPException(status_code=400, detail="At least one basket item is required")

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Build outfit description from basket items
        item_list_str = ", ".join(
            f"{it.baseColour} {it.productDisplayName or it.name}".strip()
            for it in req.basket_items[:5]
        )
        style = req.style_vibe or "contemporary"
        has_photo = bool(req.person_image_base64)

        if has_photo:
            # --- PATH A: gpt-image-1 with real photo (preserves the person) ---
            edit_prompt = (
                f"Keep this exact person — same face, body, skin tone, hair. "
                f"Dress them in the following outfit: {item_list_str}. "
                f"Full body shot from head to shoes, centered in frame, "
                f"natural studio lighting, clean white background, "
                f"realistic fabric textures and draping. "
                f"Style: {style} editorial fashion photography. High resolution."
            )

            # Decode base64 to bytes for the images.edit endpoint
            photo_bytes = base64.b64decode(req.person_image_base64)
            photo_file = _io.BytesIO(photo_bytes)
            photo_file.name = "person.png"

            async def _edit_image() -> str:
                response = await client.images.edit(
                    model="gpt-image-1",
                    image=photo_file,
                    prompt=edit_prompt,
                    size="1024x1536",
                    n=1,
                )
                item = response.data[0]
                if item.url:
                    return item.url
                elif item.b64_json:
                    return f"data:image/png;base64,{item.b64_json}"
                return ""

            generated_url = await call_openai_with_retry(_edit_image)

            logger.info("[TRYON-GEN] mode=photo model=gpt-image-1 items=%d",
                        len(req.basket_items))

            return {
                "generated_image_url": generated_url,
                "prompt_used": edit_prompt,
                "description": "Photo-based try-on (real person preserved)",
                "model_used": "gpt-image-1",
            }

        else:
            # --- PATH B: DALL-E 3 for model mode (no photo provided) ---
            gender_desc = "male" if req.gender.lower() in ("men", "male") else "female"
            description = (
                f"A confident {gender_desc} fashion model in their late 20s, "
                f"athletic build, natural skin tone, standing in a relaxed but poised pose"
            )

            dalle_prompt = (
                f"Fashion editorial photograph: {description}. "
                f"The person is wearing the following outfit: {item_list_str}. "
                f"Full body shot from head to shoes, centered in frame, "
                f"natural studio lighting, clean white background, "
                f"realistic fabric textures and draping. "
                f"Style: {style}. High resolution, 4K detail."
            )

            async def _generate_image() -> str:
                response = await client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt,
                    size="1024x1792",
                    quality="standard",
                    n=1,
                )
                return response.data[0].url

            generated_url = await call_openai_with_retry(_generate_image)

            logger.info("[TRYON-GEN] mode=model model=dall-e-3 items=%d",
                        len(req.basket_items))

            return {
                "generated_image_url": generated_url,
                "prompt_used": dalle_prompt,
                "description": description,
                "model_used": "dall-e-3",
            }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Generative try-on failed")
        raise HTTPException(status_code=500, detail="Image generation failed") from exc


@router.post("/wardrobe/discover")
async def wardrobe_discover(req: DiscoverRequest) -> dict:
    """Occasion-based outfit discovery for AI Wardrobe (FR-35).

    Embeds the occasion string, searches full catalog (gender-filtered,
    no articleType filter), and generates an outfit concept via GPT-4o-mini.
    """
    if not req.occasion.strip():
        raise HTTPException(status_code=400, detail="occasion is required")

    try:
        # 1. Embed the occasion string
        query_embedding = await embeddings.generate_embedding(req.occasion)
        catalog, cached_embeddings = _get_data()

        # 2. Filter catalog by gender (keep matching + Unisex)
        gender_lower = req.gender.strip().lower()
        candidates = []
        candidate_ids = []
        for item in catalog:
            g = str(item.get("gender", "") or "").strip().lower()
            if gender_lower != "non-binary" and g != "unisex" and g != gender_lower:
                continue

            item_id = item.get("id", "")
            str_key = str(item_id)
            emb_key = None
            if str_key in cached_embeddings:
                emb_key = str_key
            elif item_id in cached_embeddings:
                emb_key = item_id
            elif isinstance(item_id, (int, float)) and int(item_id) in cached_embeddings:
                emb_key = int(item_id)

            if emb_key is not None:
                candidates.append(item)
                candidate_ids.append(emb_key)

        logger.info("[DISCOVER] Gender=%s, candidates after filter: %d",
                    req.gender, len(candidates))

        if not candidates:
            return {"outfit_concept": "", "items": []}

        # 3. Cosine similarity — NO articleType filter
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return {"outfit_concept": "", "items": []}

        emb_matrix = np.array(
            [cached_embeddings[cid] for cid in candidate_ids], dtype=np.float32
        )
        norms = np.linalg.norm(emb_matrix, axis=1)
        mask = norms > 0
        scores = np.zeros(len(candidates), dtype=np.float32)
        if mask.any():
            masked_emb = emb_matrix[mask]
            masked_norms = norms[mask]
            dot_products = masked_emb @ query_vec
            scores[mask] = dot_products / (masked_norms * query_norm)

        # Threshold 0.25 per FR-35
        threshold = 0.25
        above = scores >= threshold
        if not above.any():
            return {"outfit_concept": "", "items": []}

        indices = np.where(above)[0]
        top_indices = indices[np.argsort(-scores[indices])][:req.top_k]

        results = []
        for idx in top_indices:
            item = candidates[idx]
            item_id = item.get("id", "")
            img_path = _IMAGES_DIR / f"{item_id}.jpg"
            results.append({
                "id": item_id,
                "name": item.get("productDisplayName", "Unnamed Item"),
                "articleType": item.get("articleType", ""),
                "baseColour": item.get("baseColour", ""),
                "image_url": f"/images/{item_id}.jpg" if img_path.exists() else "",
                "similarity_score": float(scores[idx]),
                "reason": "",
            })

        # 4. Generate outfit_concept via GPT-4o-mini
        item_names = [r["name"] for r in results[:10]]
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        async def _gen_concept() -> str:
            response = await client.responses.create(
                model=settings.guardrail_model,
                instructions="You are a personal stylist.",
                input=(
                    f"Occasion: {req.occasion}. Style: {req.style_vibe}. "
                    f"Gender: {req.gender}. Items found: {', '.join(item_names)}. "
                    "Write 2-3 sentences describing the outfit concept for this "
                    "occasion. Be specific and editorial."
                ),
            )
            return response.output_text or ""

        outfit_concept = await call_openai_with_retry(_gen_concept)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Wardrobe discover failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    return {"outfit_concept": outfit_concept, "items": results}


@router.post("/api/companion-evaluate")
async def companion_evaluate(req: CompanionRequest) -> dict:
    """AI Stylist Companion — evaluates an outfit selection for an occasion.

    Returns overall score, per-item scores, verdict, and improvement suggestion.
    """
    if not req.occasion.strip():
        raise HTTPException(status_code=400, detail="occasion is required")
    if not req.items:
        raise HTTPException(status_code=400, detail="at least one item is required")

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        items_text = ", ".join(
            f"{it.name} ({it.category})" for it in req.items
        )

        system_prompt = (
            "You are an expert fashion stylist. You will receive a list of "
            "clothing items and the occasion the user is dressing for. "
            "Evaluate how well the outfit works for that occasion. "
            'Return ONLY a JSON object with no markdown. Schema: '
            '{ "overall_score": float (0-10), '
            '"items": [{ "name": string, "score": float, "comment": string }], '
            '"verdict": string (2-3 sentences), '
            '"improvement": string (1 actionable suggestion) }'
        )

        profile_section = ""
        if req.profile_context:
            profile_section = f"\nUser profile: {req.profile_context}\n"
        if req.purchase_context:
            profile_section += f"{req.purchase_context}\n"

        user_prompt = (
            f"Occasion: {req.occasion}\n"
            f"Outfit items: {items_text}\n"
            f"{profile_section}"
            "Evaluate this outfit for the stated occasion."
        )

        async def _call_companion() -> str:
            response = await client.responses.create(
                model=settings.guardrail_model,
                instructions=system_prompt,
                input=user_prompt,
            )
            return response.output_text or ""

        import json as _json
        import re as _re
        import time as _time

        start = _time.time()
        raw = await call_openai_with_retry(_call_companion)
        latency_ms = int((_time.time() - start) * 1000)

        # Parse JSON from response
        try:
            result = _json.loads(raw.strip())
        except _json.JSONDecodeError:
            match = _re.search(r"\{.*\}", raw, flags=_re.DOTALL)
            if not match:
                raise ValueError("Companion response is not valid JSON")
            result = _json.loads(match.group(0))

        logger.info(
            "[COMPANION] occasion_len=%d items=%d score=%.1f latency_ms=%d",
            len(req.occasion), len(req.items),
            result.get("overall_score", 0), latency_ms,
        )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Companion evaluation failed")
        raise HTTPException(status_code=500, detail="Style advice unavailable. Try again.") from exc

"""Guardrail validation module using GPT-4o-mini.

Validates candidate matches by asking the LLM whether each item
genuinely complements or is similar to the uploaded clothing item.

See TASK-07 in docs/TASKS.md for implementation spec.
"""
import json
import re

from openai import AsyncOpenAI

from backend.config import settings
from backend.modules.retry import call_openai_with_retry


def _parse_guardrail_response(raw_text: str) -> dict:
    """Parse and validate guardrail JSON output."""
    text = raw_text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Guardrail response is not valid JSON")
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Guardrail response must be a JSON object")
    if "approved" not in parsed or "reasoning" not in parsed:
        raise ValueError("Guardrail response must include approved and reasoning")

    return parsed


def _build_complementary_prompt(
    original_description: str, candidate_summary: dict, occasion: str,
) -> str:
    """Build guardrail prompt for complementary mode."""
    occasion_line = ""
    if occasion:
        occasion_line = (
            f"\nThis outfit is intended for: {occasion}. "
            "Factor this into your evaluation.\n"
        )

    return (
        "You are a sharp, confident personal stylist speaking directly to the customer. "
        "Your voice is warm, authoritative, and editorial — like a trusted fashion editor "
        "who knows exactly why an outfit works.\n\n"
        "Evaluate whether the candidate item COMPLEMENTS the original as part of a "
        "cohesive outfit. They should be DIFFERENT types of clothing that work together.\n\n"
        "Be GENEROUS with approvals. If the items are different garment types and could "
        "plausibly be worn together, APPROVE. Color coordination (matching, complementary, "
        "or analogous tones), shared style register (both casual, both formal, etc.), or "
        "seasonal compatibility are all valid reasons to approve. Only reject if there is "
        "a clear aesthetic clash.\n\n"
        "A good complementary match: original=blue shirt, candidate=navy chinos. "
        "A good complementary match: original=turquoise skirt, candidate=turquoise top. "
        "A bad complementary match: original=blue shirt, candidate=similar blue shirt.\n\n"
        "RULES:\n"
        "- Respond ONLY in English.\n"
        "- Return ONLY valid JSON: {\"approved\": boolean, \"reasoning\": string}\n"
        "- If approved, write the reasoning as a confident personal stylist speaking directly "
        "to the customer. Use first-person editorial voice. Start with the style logic, not "
        "the product description. Keep to 2-3 sentences maximum.\n"
        "- Good tone examples:\n"
        '  - "The structured silhouette of your blazer calls for something relaxed below — '
        'these slim chinos balance the look without competing for attention."\n'
        '  - "Turquoise tones run through both pieces creating a cohesive monochromatic palette. '
        'The flat sole keeps the casualness your skirt establishes."\n'
        '- Bad tone (AVOID): "The candidate item, a printed turquoise blue kurta, complements '
        'the original casual flared skirt due to the color harmony."\n'
        "- Reference specific color theory, name the style aesthetic, suggest occasions, "
        "and mention actual colors and textures — not generic praise.\n"
        "- If rejected, briefly explain why it clashes (1 sentence).\n\n"
        f"Original item: {original_description}\n"
        f"Candidate item: {json.dumps(candidate_summary, ensure_ascii=True)}"
        f"{occasion_line}"
    )


def _build_similarity_prompt(
    original_description: str, candidate_summary: dict, occasion: str,
) -> str:
    """Build guardrail prompt for similarity mode."""
    preference_line = ""
    if occasion:
        preference_line = (
            f"\nCustomer preferences: {occasion}. "
            "Factor these preferences into your evaluation.\n"
        )

    return (
        "You are a fashion shopping assistant helping a customer find items similar "
        "to one they already like.\n\n"
        "Evaluate whether the candidate item is SIMILAR to the original item. "
        "They should be the same general TYPE of clothing (e.g. both shirts, both shoes, "
        "both dresses). Be GENEROUS — differences in color, pattern, fabric, or specific "
        "sub-style are perfectly fine as long as the core garment type matches. "
        "The customer wants to browse alternatives, not find an exact duplicate.\n\n"
        "A good similarity match: original=blue striped shirt, candidate=red checked shirt. "
        "A good similarity match: original=casual brown shoes, candidate=formal black shoes. "
        "A bad similarity match: original=blue shirt, candidate=black jeans.\n\n"
        "RULES:\n"
        "- Respond ONLY in English.\n"
        "- Return ONLY valid JSON: {\"approved\": boolean, \"reasoning\": string}\n"
        "- If approved, explain in 2-3 sentences what makes this a good alternative — "
        "focus on shared style DNA, color relationship, and how it could serve as a "
        "substitute. Use a confident, helpful shopping assistant voice.\n"
        "- Good tone: \"Same relaxed button-down silhouette in a warmer blue wash — "
        "if you like the original, this gives you the same vibe with a subtle pattern twist.\"\n"
        "- If rejected, briefly explain why it's too different (1 sentence).\n\n"
        f"Original item: {original_description}\n"
        f"Candidate item: {json.dumps(candidate_summary, ensure_ascii=True)}"
        f"{preference_line}"
    )


async def validate_matches(
    original_description: str,
    candidates: list[dict],
    occasion: str = "",
    search_mode: str = "complementary",
) -> list[dict]:
    """Validate candidate matches through LLM guardrail.

    Args:
        original_description: Text description of the uploaded item.
        candidates: List of candidate match dicts from the matcher.
        occasion: Optional occasion context (e.g. "garden wedding").
        search_mode: "complementary" or "similarity".

    Returns:
        List of approved candidates, each with an added 'reasoning' field.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    approved_candidates: list[dict] = []

    for candidate in candidates:
        candidate_summary = {
            "productDisplayName": candidate.get("productDisplayName", ""),
            "articleType": candidate.get("articleType", ""),
            "baseColour": candidate.get("baseColour", ""),
            "gender": candidate.get("gender", ""),
        }

        if search_mode == "similarity":
            prompt = _build_similarity_prompt(original_description, candidate_summary, occasion)
        else:
            prompt = _build_complementary_prompt(
                original_description, candidate_summary, occasion,
            )

        async def _call_model() -> str:
            response = await client.responses.create(
                model=settings.guardrail_model,
                input=prompt,
            )
            return response.output_text or ""

        raw_output = await call_openai_with_retry(_call_model)
        parsed = _parse_guardrail_response(raw_output)

        if bool(parsed["approved"]):
            approved_candidate = dict(candidate)
            approved_candidate["reasoning"] = str(parsed["reasoning"])
            approved_candidates.append(approved_candidate)

    return approved_candidates

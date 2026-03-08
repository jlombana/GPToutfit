"""Image analysis module using GPT-4o-mini vision.

Accepts raw image bytes, sends to OpenAI vision endpoint, and returns
structured clothing attributes.

See TASK-04 in docs/TASKS.md for implementation spec.
"""
import base64
import imghdr
import json
import re

from openai import AsyncOpenAI

from backend.config import settings
from backend.modules.retry import call_openai_with_retry

REQUIRED_KEYS = ["style", "color", "gender", "articleType", "description"]


def _detect_mime_type(image_bytes: bytes) -> str:
    """Infer MIME type from raw image bytes."""
    detected = imghdr.what(None, h=image_bytes)
    if detected == "jpeg":
        return "image/jpeg"
    if detected == "png":
        return "image/png"
    if detected == "webp":
        return "image/webp"
    return "image/jpeg"


def _extract_json_object(raw_text: str) -> dict:
    """Parse a JSON object from model output."""
    text = raw_text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Model response is not valid JSON")
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Model response JSON must be an object")

    missing = [key for key in REQUIRED_KEYS if key not in parsed]
    if missing:
        raise ValueError(f"Model response missing keys: {missing}")

    return parsed


async def analyze_image(
    image_bytes: bytes, occasion: str = "", search_mode: str = "complementary",
) -> dict:
    """Analyze a clothing image and extract structured attributes.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        occasion: Optional occasion context (e.g. "garden wedding").
        search_mode: "complementary" or "similarity".

    Returns:
        Dict with keys: style, color, gender, articleType, description.
    """
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = _detect_mime_type(image_bytes)
    data_url = f"data:{mime_type};base64,{image_b64}"

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Mode-specific instructions
    if search_mode == "similarity":
        mode_instruction = (
            "\nThe description should focus on the SPECIFIC visual characteristics "
            "of this exact item — its style, cut, pattern, texture, and color details. "
            "Think like a shopper looking for alternatives to this exact item."
        )
    else:
        mode_instruction = (
            "\nThe description should capture the overall style and vibe of this item "
            "so we can find pieces that COMPLEMENT it to build a complete outfit. "
            "Think like a personal stylist building a complete look."
        )

    occasion_instruction = ""
    if occasion and search_mode == "complementary":
        occasion_instruction = (
            f"\nThe customer needs this outfit for the following occasion: {occasion}. "
            "Prioritize items appropriate for this event."
        )
    elif occasion and search_mode == "similarity":
        occasion_instruction = (
            f"\nThe customer has these preferences for similar items: {occasion}. "
            "Emphasize these aspects in the description to help find the best alternatives."
        )

    prompt = (
        "You are a fashion analysis assistant. Analyze the clothing item in the image "
        "and return ONLY valid JSON with keys: style, color, gender, articleType, description.\n"
        "Use concise values.\n"
        "When describing occasions or usage context, use terms from this list when applicable: "
        "Formal, Casual, Smart Casual, Sports, Ethnic, Party.\n"
        "One-shot example output:\n"
        '{"style":"casual","color":"navy blue","gender":"Men","articleType":"Shirts",'
        '"description":"A casual navy blue button-down shirt with a slim fit"}'
        f"{mode_instruction}"
        f"{occasion_instruction}"
    )

    async def _call_model() -> str:
        response = await client.responses.create(
            model=settings.vision_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )
        return response.output_text or ""

    raw_output = await call_openai_with_retry(_call_model)
    return _extract_json_object(raw_output)

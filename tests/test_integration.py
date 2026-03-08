from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.main import app


def _catalog_fixture() -> list[dict]:
    return [
        {"id": 1, "gender": "Men", "articleType": "Shirts", "baseColour": "Blue", "productDisplayName": "Blue Shirt"},
        {"id": 2, "gender": "Men", "articleType": "Trousers", "baseColour": "Khaki", "productDisplayName": "Khaki Chino"},
        {"id": 3, "gender": "Unisex", "articleType": "Shoes", "baseColour": "White", "productDisplayName": "White Sneaker"},
        {"id": 4, "gender": "Women", "articleType": "Dresses", "baseColour": "Black", "productDisplayName": "Black Dress"},
        {"id": 5, "gender": "Men", "articleType": "Jackets", "baseColour": "Gray", "productDisplayName": "Gray Blazer"},
    ]


def _embeddings_fixture() -> dict:
    base = [0.1] * 3072
    return {1: base, 2: base, 3: base, 4: base, 5: base}


def test_analyze_happy_path() -> None:
    fake_uploaded = {
        "style": "Casual",
        "color": "Blue",
        "gender": "Men",
        "articleType": "Shirts",
        "description": "Blue casual men's shirt",
    }

    async def fake_validate(original_description: str, candidates: list[dict], **kwargs) -> list[dict]:
        return [{**c, "reasoning": "Test reasoning"} for c in candidates]

    with TestClient(app) as client, \
        patch("backend.modules.image_analyzer.analyze_image", new=AsyncMock(return_value=fake_uploaded)), \
        patch("backend.modules.embeddings.generate_embedding", new=AsyncMock(return_value=[0.1] * 3072)), \
        patch("backend.modules.guardrail.validate_matches", new=AsyncMock(side_effect=fake_validate)), \
        patch("backend.data.loader.load_catalog", return_value=_catalog_fixture()), \
        patch("backend.modules.embeddings.load_cached_embeddings", return_value=_embeddings_fixture()):
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        response = client.post(
            "/analyze",
            files={"image": ("test.jpg", fake_jpeg, "image/jpeg")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "uploaded_item" in payload
    assert "uploaded_preview" in payload
    assert payload["uploaded_preview"].startswith("data:image")
    assert isinstance(payload.get("matches"), list)


def test_analyze_no_image_returns_400() -> None:
    with TestClient(app) as client:
        response = client.post("/analyze")

    assert response.status_code == 400
    assert response.json()["detail"] == "No image file provided"


def test_analyze_empty_image_returns_400() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            files={"image": ("empty.jpg", b"", "image/jpeg")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "No image file provided"

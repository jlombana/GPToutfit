import os
from types import SimpleNamespace

import pytest

# Ensure settings initialization succeeds in tests
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.fixture
def sample_catalog() -> list[dict]:
    return [
        {
            "id": 1,
            "productDisplayName": "Navy Shirt",
            "gender": "Men",
            "articleType": "Shirts",
            "baseColour": "Navy",
            "usage": "Casual",
            "season": "Summer",
        },
        {
            "id": 2,
            "productDisplayName": "Khaki Chino",
            "gender": "Men",
            "articleType": "Trousers",
            "baseColour": "Khaki",
            "usage": "Casual",
            "season": "Summer",
        },
        {
            "id": 3,
            "productDisplayName": "White Sneaker",
            "gender": "Unisex",
            "articleType": "Casual Shoes",
            "baseColour": "White",
            "usage": "Sports",
            "season": "All",
        },
        {
            "id": 4,
            "productDisplayName": "Black Dress",
            "gender": "Women",
            "articleType": "Dresses",
            "baseColour": "Black",
            "usage": "Party",
            "season": "Winter",
        },
    ]


@pytest.fixture
def sample_embeddings() -> dict:
    return {
        1: [1.0, 0.0, 0.0],
        2: [0.99, 0.01, 0.0],
        3: [0.95, 0.05, 0.0],
        4: [0.0, 1.0, 0.0],
    }


@pytest.fixture
def mock_openai_client() -> SimpleNamespace:
    class FakeEmbeddingsAPI:
        async def create(self, model: str, input: str):
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1] * 3072)])

    return SimpleNamespace(embeddings=FakeEmbeddingsAPI())

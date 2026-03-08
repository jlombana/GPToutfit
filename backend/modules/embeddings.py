"""Embedding generation and caching module.

Generates text embeddings via text-embedding-3-large and manages
the pickle-based embedding cache.

See TASK-05 in docs/TASKS.md for implementation spec.
"""
import pickle
from pathlib import Path

from openai import AsyncOpenAI

from backend.config import settings
from backend.modules.retry import call_openai_with_retry


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text.

    Args:
        text: Input text to embed.

    Returns:
        List of floats (3072 dimensions).
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def _call_model() -> list[float]:
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    embedding = await call_openai_with_retry(_call_model)
    return [float(value) for value in embedding]


def load_cached_embeddings(cache_path: str) -> dict:
    """Load pre-computed embeddings from a pickle file.

    Args:
        cache_path: Path to the .pkl file.

    Returns:
        Dict mapping item_id to embedding vector.
    """
    path = Path(cache_path)
    if not path.exists():
        return {}

    with path.open("rb") as file:
        data = pickle.load(file)

    if not isinstance(data, dict):
        raise ValueError("Embeddings cache must be a dict mapping item_id to vectors")

    return data


def save_embeddings_cache(embeddings: dict, cache_path: str) -> None:
    """Save embeddings dict to a pickle file.

    Args:
        embeddings: Dict mapping item_id to embedding vector.
        cache_path: Path to write the .pkl file.
    """
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as file:
        pickle.dump(embeddings, file)

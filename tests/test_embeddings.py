from types import SimpleNamespace

import pytest

from backend.modules.embeddings import (
    generate_embedding,
    load_cached_embeddings,
    save_embeddings_cache,
)


@pytest.mark.asyncio
async def test_generate_embedding_uses_openai_and_returns_float_list(monkeypatch, mock_openai_client) -> None:
    class FakeAsyncOpenAI:
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.embeddings = mock_openai_client.embeddings

    async def passthrough(callable_obj, *args, **kwargs):
        return await callable_obj(*args, **kwargs)

    monkeypatch.setattr("backend.modules.embeddings.AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setattr("backend.modules.embeddings.call_openai_with_retry", passthrough)

    emb = await generate_embedding("blue casual shirt")
    assert isinstance(emb, list)
    assert len(emb) == 3072
    assert all(isinstance(x, float) for x in emb)


def test_load_cached_embeddings_missing_file_returns_empty_dict(tmp_path) -> None:
    missing = tmp_path / "missing.pkl"
    assert load_cached_embeddings(str(missing)) == {}


def test_save_and_load_cached_embeddings_roundtrip(tmp_path) -> None:
    cache_path = tmp_path / "cache.pkl"
    expected = {"1": [0.1, 0.2], "2": [0.3, 0.4]}

    save_embeddings_cache(expected, str(cache_path))
    loaded = load_cached_embeddings(str(cache_path))

    assert loaded == expected


def test_load_cached_embeddings_raises_for_invalid_pickle_type(tmp_path) -> None:
    cache_path = tmp_path / "bad.pkl"
    with cache_path.open("wb") as f:
        import pickle

        pickle.dump([1, 2, 3], f)

    with pytest.raises(ValueError):
        load_cached_embeddings(str(cache_path))

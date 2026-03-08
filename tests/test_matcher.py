import pytest

from backend.modules.matcher import _normalize_article_type, cosine_similarity, find_matches


def test_cosine_similarity_zero_vector_returns_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_normalize_article_type_handles_singular_plural() -> None:
    assert _normalize_article_type(" Shirt ") == "shirt"
    assert _normalize_article_type("Shirts") == "shirt"


def test_find_matches_empty_catalog_returns_empty(sample_embeddings: dict) -> None:
    matches = find_matches(
        query_embedding=[1.0, 0.0, 0.0],
        catalog=[],
        cached_embeddings=sample_embeddings,
        query_gender="Men",
        query_article_type="Shirts",
        threshold=0.6,
        top_k=2,
    )
    assert matches == []


def test_find_matches_no_matches_above_threshold(sample_catalog: list[dict], sample_embeddings: dict) -> None:
    matches = find_matches(
        query_embedding=[0.0, 0.0, 1.0],
        catalog=sample_catalog,
        cached_embeddings=sample_embeddings,
        query_gender="Men",
        query_article_type="Shirts",
        threshold=0.95,
        top_k=2,
    )
    assert matches == []


def test_find_matches_unisex_both_directions(sample_catalog: list[dict], sample_embeddings: dict) -> None:
    men_query = find_matches(
        query_embedding=[1.0, 0.0, 0.0],
        catalog=sample_catalog,
        cached_embeddings=sample_embeddings,
        query_gender="Men",
        query_article_type="Shirts",
        threshold=0.6,
        top_k=3,
    )
    assert any(item["id"] == 3 for item in men_query)

    unisex_query = find_matches(
        query_embedding=[1.0, 0.0, 0.0],
        catalog=sample_catalog,
        cached_embeddings=sample_embeddings,
        query_gender="Unisex",
        query_article_type="Shirt",
        threshold=0.6,
        top_k=5,
    )
    returned_ids = {item["id"] for item in unisex_query}
    assert {2, 3}.issubset(returned_ids)


def test_find_matches_sorted_and_top_k(sample_catalog: list[dict], sample_embeddings: dict) -> None:
    matches = find_matches(
        query_embedding=[1.0, 0.0, 0.0],
        catalog=sample_catalog,
        cached_embeddings=sample_embeddings,
        query_gender="Men",
        query_article_type="Shirt",
        threshold=0.6,
        top_k=1,
    )

    assert len(matches) == 1
    assert "similarity_score" in matches[0]
    assert matches[0]["id"] == 2
    assert matches[0]["similarity_score"] >= 0.6

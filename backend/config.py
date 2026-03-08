"""Configuration module for GPToutfit.

Loads environment variables via pydantic-settings and provides a single
Settings object used across the application.

See TASK-01 in docs/TASKS.md for implementation spec.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    vision_model: str = Field(default="gpt-4o-mini", alias="VISION_MODEL")
    guardrail_model: str = Field(default="gpt-4o-mini", alias="GUARDRAIL_MODEL")
    embedding_model: str = Field(default="text-embedding-3-large", alias="EMBEDDING_MODEL")
    cosine_similarity_threshold: float = Field(default=0.4, alias="COSINE_SIMILARITY_THRESHOLD")
    top_k_matches: int = Field(default=5, alias="TOP_K_MATCHES")
    catalog_csv_path: str = Field(default="data/sample_styles.csv", alias="CATALOG_CSV_PATH")
    embeddings_cache_path: str = Field(default="data/embeddings_cache.pkl", alias="EMBEDDINGS_CACHE_PATH")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

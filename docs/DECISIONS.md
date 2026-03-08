# Architectural Decision Records (ADRs)

## ADR-001: FastAPI as Backend Framework
- **Status:** Accepted
- **Context:** Need a Python web framework for REST API with async support.
- **Decision:** Use FastAPI with uvicorn.
- **Rationale:** Native async/await for non-blocking OpenAI calls, automatic OpenAPI
  docs generation, Pydantic integration for request/response validation, excellent
  performance for I/O-bound workloads.
- **Alternatives considered:** Flask (no native async), Django (too heavy for this scope).

## ADR-002: Pickle for Embeddings Cache
- **Status:** Accepted
- **Context:** Need to persist pre-computed embeddings for fast retrieval.
- **Decision:** Use Python pickle files (.pkl) to store embeddings.
- **Rationale:** Zero infrastructure overhead, fast serialization of numpy arrays,
  sufficient for MVP with ~1K-44K items. No need for a vector database at this scale.
- **Alternatives considered:** FAISS (overkill for MVP), ChromaDB (adds dependency),
  SQLite (not optimized for vector operations).
- **Migration path:** Can migrate to FAISS or a vector DB if scale demands it.

## ADR-003: Vanilla HTML/JS Frontend
- **Status:** Accepted
- **Context:** Need a UI for image upload and results display.
- **Decision:** Single index.html with vanilla JavaScript and CSS.
- **Rationale:** Minimal scope — only one page with upload and display. No routing,
  state management, or component reuse needed. Avoids build tooling complexity.
- **Alternatives considered:** React (overkill), Vue (unnecessary complexity).

## ADR-004: GPT-4o-mini for Both Vision and Guardrail
- **Status:** Accepted
- **Context:** Need vision analysis and text-based validation.
- **Decision:** Use gpt-4o-mini for both the image analysis and guardrail steps.
- **Rationale:** Cost-effective, fast, sufficient quality for clothing analysis.
  Same model simplifies configuration. Guardrail doesn't need a larger model since
  it's a focused yes/no validation with reasoning.
- **Alternatives considered:** GPT-4o (higher cost, marginal quality gain for this use case).

## ADR-005: text-embedding-3-large for Embeddings
- **Status:** Accepted
- **Context:** Need high-quality embeddings for semantic matching of clothing items.
- **Decision:** Use text-embedding-3-large (3072 dimensions).
- **Rationale:** Highest quality OpenAI embedding model. Better semantic capture
  of style, color, and fashion concepts than smaller models.
- **Alternatives considered:** text-embedding-3-small (lower quality, minor cost savings).

## ADR-006: Mandatory Guardrail Step
- **Status:** Accepted
- **Context:** RAG matching alone may return items that are semantically similar
  but don't actually work as an outfit together.
- **Decision:** Every candidate match MUST pass through the guardrail validator
  before being returned to the user.
- **Rationale:** Cosine similarity captures semantic closeness but not fashion
  compatibility. A second LLM pass acts as quality control, confirming items
  complement each other rather than just being related.
- **Trade-off:** Adds latency and API cost per request, but significantly improves
  result quality.

## ADR-007: Shared Retry Wrapper for OpenAI Calls
- **Status:** Accepted
- **Context:** OpenAI API can return rate limit or transient errors.
- **Decision:** All OpenAI calls use a shared retry wrapper with exponential backoff,
  max 10 attempts.
- **Rationale:** Centralizes error handling, prevents duplicate retry logic across
  modules, makes the system resilient to transient failures.

## ADR-008: Pydantic Settings for Configuration
- **Status:** Accepted
- **Context:** Need to load and validate environment variables.
- **Decision:** Use pydantic-settings BaseSettings class.
- **Rationale:** Type-safe config, automatic .env loading, validation at startup
  (fail fast if OPENAI_API_KEY is missing), single source of truth for all settings.

## ADR-009: Filter Logic — Gender + ArticleType
- **Status:** Accepted
- **Context:** Need to ensure recommendations make sense as outfit pairings.
- **Decision:** Filter matches to same gender (or Unisex) AND different articleType
  than the uploaded item.
- **Rationale:** Recommending a men's dress to complement a women's blouse doesn't
  make sense. Recommending another blouse to go with a blouse doesn't either.
  These filters enforce basic outfit logic before semantic matching.

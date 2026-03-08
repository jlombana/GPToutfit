# GPToutfit — Technical Architecture Document

**Version:** 1.1
**Date:** 2026-03-06
**Author:** Claude Code (Lead Architect)
**Status:** Phase 2 Complete

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-06 | Claude Code | Initial release — Phase 1 MVP architecture |
| 1.1 | 2026-03-06 | Claude Code | Phase 2 COMPLETE — Added feedback module, POST /feedback, vectorized matcher, startup caching, Docker, tests, /images/ mount, updated API spec |

---

## 1. Executive Summary

GPToutfit is an AI-powered clothing matchmaker that receives a clothing image and returns complementary outfit recommendations from a catalog. The system combines computer vision (GPT-4o-mini), semantic search (text-embedding-3-large + cosine similarity), and LLM-based validation (guardrail layer) to deliver curated, reasoned outfit suggestions with an editorial stylist voice.

---

## 2. System Architecture

### 2.1 High-Level Diagram

```
+------------------+       +-------------------------------------------+
|    FRONTEND      |       |              BACKEND (FastAPI)             |
|                  | POST  |                                           |
|  index.html      |------>|  routes.py (/analyze)                     |
|  (outfit board + | image |       |                                   |
|   wishlist +     |       |       v                                   |
|   feedback)      |       |  [1] image_analyzer.py                    |
|                  |       |       GPT-4o-mini (vision)                |
|                  |       |       -> {style,color,gender,             |
|                  |       |          articleType,description}         |
|                  |       |       |                                   |
|                  |       |       v                                   |
|                  |       |  [2] embeddings.py                       |
|                  |       |       text-embedding-3-large              |
|                  |       |       -> query vector (3072 dims)         |
|                  |       |       |                                   |
|                  |       |       v                                   |
|                  |       |  [3] matcher.py (vectorized numpy)        |
|                  |       |       matrix cosine similarity + filters  |
|                  |       |       -> top-5 candidates                 |
|                  |       |       |                                   |
|                  |       |       v                                   |
|                  |       |  [4] guardrail.py (editorial voice)       |
|                  |  JSON |       GPT-4o-mini (validation)            |
|  <-- results <---+------+       -> approved matches + reasoning     |
|  (+ image_url,   |       |                                           |
|   uploaded_      |       |  /feedback -> feedback.py (in-memory)     |
|   preview)       |       |  /images/  -> sample_images/ (static)     |
|                  |       |                                           |
+------------------+       +-------------------------------------------+

+-------------------+       +-----------------+
| OFFLINE SCRIPT    |       |                 |
| generate_         |------>| embeddings      |
| embeddings.py     |       | _cache.pkl      |
| (one-time)        |       | (1000 vectors)  |
+-------------------+       +-----------------+
        |
        v
+-----------------+
| sample_styles   |
| .csv (catalog)  |
+-----------------+
```

### 2.2 Request Flow (POST /analyze)

```
1. User uploads image (JPEG/PNG/WebP)
2. routes.py receives multipart form data
3. image_analyzer.py:
   - Encodes image to base64
   - Sends to GPT-4o-mini vision with structured prompt
   - Parses JSON response: {style, color, gender, articleType, description}
4. embeddings.py:
   - Generates embedding vector from description text
   - Returns 3072-dimension float vector
5. _get_data() loads catalog + embeddings (cached after first call)
6. matcher.py (vectorized):
   - Filters: same gender (or Unisex) + different articleType
   - Builds numpy matrix of candidate embeddings
   - Computes all cosine similarities in one vectorized operation
   - Returns top-5 above threshold (0.4)
7. guardrail.py (editorial voice):
   - For each candidate, asks GPT-4o-mini: "Does this complement the original?"
   - Uses fashion editor persona with color theory, aesthetic naming, occasion context
   - Parses {approved: bool, reasoning: string}
   - Returns only approved items with editorial reasoning
8. _add_image_urls() attaches product image paths to matches
9. routes.py returns JSON: {uploaded_item, uploaded_preview (base64), matches (with image_url)}
```

---

## 3. Technology Stack

### 3.1 Backend

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Language | Python | 3.11+ | Async ecosystem, AI library support |
| Framework | FastAPI | >=0.110 | Native async, auto OpenAPI docs, Pydantic integration |
| Server | uvicorn | >=0.30 | High-performance ASGI server |
| Config | pydantic-settings | >=2.0 | Type-safe env loading, fail-fast validation |
| Testing | pytest + pytest-asyncio | latest | Async test support, >80% coverage |
| Container | Docker + docker-compose | latest | Portable deployment with healthcheck |

### 3.2 AI Models

| Model | Provider | Use Case | Dimensions |
|-------|----------|----------|------------|
| gpt-4o-mini | OpenAI | Image analysis (vision) | — |
| gpt-4o-mini | OpenAI | Guardrail validation (editorial voice) | — |
| text-embedding-3-large | OpenAI | Semantic embeddings | 3072 |

### 3.3 Data Layer

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Catalog | CSV (pandas) | Simple, portable, sufficient for 1K-44K items |
| Embeddings | Pickle (.pkl) | Zero infrastructure, fast numpy serialization |
| Vector Search | numpy vectorized cosine similarity | Matrix operations for 44K scale, no external DB needed |
| Feedback | In-memory dict | Sufficient for MVP, persistence planned for Phase 3 |

### 3.4 Frontend

| Component | Technology | Justification |
|-----------|-----------|---------------|
| UI | Vanilla HTML/JS/CSS | Single page, no framework overhead needed |
| Fonts | Google Fonts (Outfit, Fraunces) | Editorial typography — serif + sans-serif |
| Styling | CSS custom properties | Consistent theming, premium muted palette |
| Storage | sessionStorage | Client-side wishlist (session-scoped) |

---

## 4. Module Architecture

### 4.1 Module Dependency Graph

```
backend/api/routes.py (orchestration)
    |
    +-- backend/modules/image_analyzer.py
    |       +-- backend/modules/retry.py
    |       +-- backend/config.py
    |
    +-- backend/modules/embeddings.py
    |       +-- backend/modules/retry.py
    |       +-- backend/config.py
    |
    +-- backend/modules/matcher.py
    |       (pure numpy — vectorized matrix operations)
    |
    +-- backend/modules/guardrail.py
    |       +-- backend/modules/retry.py
    |       +-- backend/config.py
    |
    +-- backend/modules/feedback.py
    |       (pure Python — in-memory store)
    |
    +-- backend/data/loader.py
            (pure pandas — no external dependencies)
```

### 4.2 Module Descriptions

#### image_analyzer.py
- **Input:** Raw image bytes
- **Output:** Dict {style, color, gender, articleType, description}
- **AI Model:** GPT-4o-mini (vision endpoint)
- **Key logic:** Base64 encoding, MIME detection, JSON parsing with fallback regex extraction
- **Resilience:** Retry wrapper for transient API errors

#### embeddings.py
- **Input:** Text string
- **Output:** List[float] (3072 dimensions)
- **AI Model:** text-embedding-3-large
- **Key logic:** Embedding generation, pickle cache load/save
- **Resilience:** Retry wrapper for transient API errors

#### matcher.py
- **Input:** Query embedding, catalog, cached embeddings, gender, articleType
- **Output:** Top-K items with similarity scores
- **AI Model:** None (pure computation)
- **Key logic:**
  - Gender filter: match query gender OR "Unisex"; if query is "Unisex", match all
  - ArticleType filter: exclude same type (normalized singular/plural via rstrip("s"))
  - **Vectorized numpy:** Builds N x 3072 matrix, computes all cosine similarities in one operation
  - Sort descending, return top-K above threshold
- **Performance:** < 2s for 44K items (matrix operations vs Python for-loop)

#### guardrail.py
- **Input:** Original description + candidate list
- **Output:** Approved candidates with editorial reasoning
- **AI Model:** GPT-4o-mini
- **Key logic:** Per-candidate validation with fashion editor persona — references color theory (complementary, analogous, monochromatic), names style aesthetics, suggests occasions, explains silhouette balance
- **Resilience:** Retry wrapper for transient API errors

#### feedback.py
- **Input:** item_id (str) + action ("like" | "dislike")
- **Output:** None (stores in-memory)
- **Key logic:** Appends to `_feedback["likes"]` or `_feedback["dislikes"]` dict
- **Persistence:** In-memory only — resets on restart (Phase 3: database)
- **Helper:** `get_feedback_summary()` returns counts and recent items

#### retry.py
- **Shared utility** for all OpenAI calls
- Exponential backoff: wait = min(2^attempt, 60) seconds
- Max 10 retries
- Only retries transient errors: RateLimitError, APITimeoutError, APIConnectionError
- Non-transient errors (AuthenticationError, etc.) propagate immediately

#### loader.py
- Reads CSV via pandas, fills NaN with empty strings
- `build_description()` concatenates: name, articleType, baseColour, gender, usage, season

#### config.py
- Pydantic BaseSettings loading from .env
- Singleton: `settings = Settings()`
- Fails fast if OPENAI_API_KEY not set

---

## 5. Data Architecture

### 5.1 Catalog Schema (sample_styles.csv)

| Column | Type | Example |
|--------|------|---------|
| id | int | 27152 |
| gender | str | Men, Women, Unisex, Boys, Girls |
| masterCategory | str | Apparel, Accessories, Footwear |
| subCategory | str | Topwear, Bottomwear |
| articleType | str | Shirts, Tshirts, Jeans, Flats |
| baseColour | str | Blue, Red, Navy Blue |
| season | str | Summer, Fall, Winter, Spring |
| year | float | 2012.0 |
| usage | str | Casual, Formal, Sports |
| productDisplayName | str | Mark Taylor Men Striped Blue Shirt |

### 5.2 Embedding Cache (embeddings_cache.pkl)

```python
{
    27152: [0.0123, -0.0456, ...],  # 3072 floats
    10469: [0.0234, -0.0567, ...],
    # ... 1000 entries
}
```

### 5.3 Product Images (sample_images/)

- 1,000 JPEG images named by catalog ID: `{id}.jpg`
- Served via FastAPI static mount at `/images/{id}.jpg`
- Referenced in match responses as `image_url` field

### 5.4 Catalog Statistics

| Metric | Value |
|--------|-------|
| Total items | 1,000 (architecture supports 44K) |
| Gender distribution | Men: 575, Women: 358, Unisex: 28, Girls: 20, Boys: 19 |
| Article types | 44 distinct types |
| Embedding dimensions | 3,072 per item |
| Cache file size | ~24 MB |
| Product images | 1,000 JPEGs |

---

## 6. API Specification

### 6.1 POST /analyze

**Request:** multipart/form-data with `image` file field
**Response (200):**
```json
{
  "uploaded_item": {
    "style": "casual",
    "color": "turquoise",
    "gender": "Women",
    "articleType": "Skirt",
    "description": "A casual turquoise flared skirt..."
  },
  "uploaded_preview": "data:image/jpeg;base64,/9j/4AAQ...",
  "matches": [
    {
      "id": 12345,
      "productDisplayName": "Catwalk Women Ballerina Turquoise Casual Shoe",
      "gender": "Women",
      "articleType": "Flats",
      "baseColour": "Turquoise Blue",
      "similarity_score": 0.516,
      "reasoning": "The candidate item coordinates perfectly with the original turquoise skirt due to their matching color, creating a monochromatic look...",
      "image_url": "/images/12345.jpg"
    }
  ]
}
```

**Error responses:** 400 (no image), 500 (API failure)

### 6.2 GET /health

**Response (200):** `{"status": "ok"}`

### 6.3 POST /feedback

**Request:** JSON body
```json
{
  "item_id": "12345",
  "action": "like"
}
```

**Response (200):** `{"status": "recorded"}`
**Error responses:** 400 (missing item_id or invalid action)

### 6.4 Static Mounts

| Path | Source | Description |
|------|--------|-------------|
| `/images/{id}.jpg` | `sample_clothes/sample_images/` | Product images |
| `/` | `frontend/` | Frontend SPA (HTML mode) |

---

## 7. Performance Characteristics

| Stage | Latency | Notes |
|-------|---------|-------|
| Image analysis | ~2-3s | Single GPT-4o-mini vision call |
| Query embedding | ~1s | Single text-embedding-3-large call |
| Catalog matching | <100ms | Vectorized numpy matrix cosine similarity (1K items) |
| Guardrail validation | ~10-15s | 5 sequential GPT-4o-mini calls |
| **Total request** | **~15-20s** | Dominated by guardrail (sequential) |

### 7.1 Performance Optimizations (Phase 2 — DONE)
- **Startup caching:** Catalog + embeddings loaded once via `_get_data()` lazy init, not per-request
- **Vectorized matching:** numpy matrix operations replace Python for-loop — scales to 44K items in < 2s

### 7.2 Optimization Opportunities (Phase 3)
- Parallelize guardrail calls (asyncio.gather) — could reduce guardrail from ~15s to ~3s
- Use FAISS for vector search at 44K+ scale (optional, numpy sufficient for 44K)

---

## 8. Security

| Concern | Mitigation |
|---------|-----------|
| API key exposure | Keys in .env (gitignored), centralized in ~/.secrets/ |
| Image injection | Images processed in-memory, never saved to disk |
| XSS in results | Frontend renders text content, no raw HTML injection |
| CORS | Open for development (allow all origins) — restrict in production |
| Container | Non-root user in Dockerfile |

---

## 9. Infrastructure

### 9.1 Development Environment

```bash
# Setup
cp .env.template .env          # Add OPENAI_API_KEY
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate embeddings (one-time)
PYTHONPATH=. python scripts/generate_embeddings.py

# Run server
PYTHONPATH=. uvicorn backend.main:app --reload
# Visit http://localhost:8000
```

### 9.2 Docker Deployment

```bash
# Build and run
docker-compose build
docker-compose up -d
curl http://localhost:8000/health  # {"status": "ok"}
docker-compose down
```

**Docker configuration:**
- Base image: `python:3.11-slim`
- Non-root user for security
- Port 8000 exposed
- `.env` file mounted for secrets
- `data/` volume persisted across rebuilds
- Health check: `curl -f http://localhost:8000/health`

### 9.3 Secrets Management

```
~/.secrets/              (drwx------)
  GPToutfit               (-rw-------)  OPENAI_API_KEY
```

### 9.4 Test Suite

```bash
# Run all tests
pytest tests/ -v --tb=short

# Test structure
tests/
  __init__.py
  conftest.py              # Shared fixtures: sample catalog, embeddings, mock OpenAI
  test_matcher.py          # find_matches, cosine_similarity, _normalize_article_type
  test_loader.py           # load_catalog, build_description
  test_embeddings.py       # generate_embedding (mocked), load/save cache
  test_integration.py      # Full /analyze pipeline with mocked OpenAI
```

**Coverage:** >80% on core modules (matcher, loader, embeddings)

---

## 10. Architectural Decisions Record (Summary)

| ID | Decision | Rationale |
|----|----------|-----------|
| ADR-001 | FastAPI | Async support, auto OpenAPI docs |
| ADR-002 | Pickle for embeddings | Zero infra for MVP |
| ADR-003 | Vanilla HTML frontend | Single page, no build tools needed |
| ADR-004 | GPT-4o-mini for vision + guardrail | Cost-effective, sufficient quality |
| ADR-005 | text-embedding-3-large | Highest quality embeddings |
| ADR-006 | Mandatory guardrail | Cosine similarity alone doesn't ensure outfit compatibility |
| ADR-007 | Shared retry wrapper | Centralized resilience logic |
| ADR-008 | Pydantic Settings | Type-safe config, fail-fast validation |
| ADR-009 | Gender + ArticleType filters | Basic outfit logic before semantic matching |
| ADR-010 | Startup caching (lazy init) | Catalog/embeddings loaded once, not per-request |
| ADR-011 | Vectorized numpy matching | Matrix cosine similarity for 44K scale performance |
| ADR-012 | Editorial stylist voice | Guardrail upgraded to fashion editor persona |
| ADR-013 | In-memory feedback | Sufficient for MVP; persistence in Phase 3 |
| ADR-014 | Docker containerization | Portable deployment with healthcheck |

Full ADRs: see docs/DECISIONS.md

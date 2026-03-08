# CLAUDE.md - GPToutfit Architectural Source of Truth

## Project Overview
GPToutfit is an AI-powered clothing matchmaker with two main sections:
- **AI Stylist** — Upload a clothing image and get complementary or similar item recommendations
- **AI Wardrobe** — Describe an occasion and get a complete outfit suggestion, save items to a shared wardrobe basket, and try them on via CSS composite

## Pipelines

### AI Stylist (item-first discovery)
```
User uploads image
       |
       v
[Image Analyzer] -- GPT-4o-mini (vision) --> structured description
       |                                      {style, color, gender, articleType}
       v
[Embeddings + Matcher] -- text-embedding-3-large --> cosine similarity search
       |                                             against pre-computed catalog embeddings
       v
[Guardrail Validator] -- GPT-4o-mini --> confirms outfit compatibility
       |
       v
Curated results with AI reasoning + Save-to-Wardrobe checkboxes
```

### AI Wardrobe (occasion-first discovery)
```
User describes occasion + profile (gender, style vibe)
       |
       v
[POST /wardrobe/discover] -- text-embedding-3-large --> embed occasion text
       |                                                cosine search full catalog
       |                                                (gender filter, NO articleType filter)
       v
[GPT-4o-mini] --> generates outfit_concept (2-3 editorial sentences)
       |
       v
Results grid grouped by category + Save-to-Wardrobe checkboxes
       |
       v
[My Wardrobe] -- shared basket (sessionStorage) -- [Try It On] CSS composite
```

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, uvicorn
- **Frontend:** Vanilla HTML/JS/CSS (single page, premium editorial design)
- **AI Models:**
  - `gpt-4o-mini` — image analysis + guardrail validation + outfit concept generation
  - `text-embedding-3-large` — catalog embeddings + query embeddings
- **Data:** CSV catalog (~10K items from Kaggle dataset), product images served via `/images/{id}.jpg`
- **Photos:** Try-on model/user images served via `/photos/`

## Hard Constraints (NEVER violate)
1. API keys loaded via `os.getenv()` — NEVER hardcoded
2. Embeddings MUST be pre-computed and cached (pickle file)
3. Guardrail validation is MANDATORY before returning results (AI Stylist pipeline)
4. Retry on all OpenAI calls: exponential backoff, max 10 attempts
5. Each module (analyzer, matcher, guardrail) must be independently replaceable
6. Try-on photos are client-side only — NEVER uploaded to the server

## Tuned Parameters (validated empirically)
These values were tuned against the real catalog. Do NOT revert to original spec values without re-testing.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base cosine threshold | 0.4 | Cross-category items score 0.45-0.55; original 0.6 filtered out valid matches |
| Complementary effective threshold | 0.4 × 0.60 = 0.24 | Cross-category descriptions are semantically distant |
| Similarity effective threshold | 0.4 × 0.85 = 0.34 | Same-category items score higher naturally |
| Discover threshold | 0.25 | Occasion text → product embedding is inherently noisy |
| Top-K (AI Stylist) | 5 | With 2, guardrail often rejected both → zero results for user |
| Top-K (Discover) | 20 | Occasion search needs breadth across categories |

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /analyze | AI Stylist — upload image, get matches. Params: `image` (file), `occasion` (str), `search_mode` (complementary/similarity) |
| POST | /wardrobe/discover | AI Wardrobe — occasion-based discovery. JSON body: `{occasion, gender, style_vibe, top_k}` |
| GET | /health | Liveness check |
| POST | /feedback | Like/dislike feedback. JSON body: `{item_id, action}` |

## Project Structure
```
GPToutfit/
  CLAUDE.md              # This file - architectural truth
  .env.template          # Required environment variables
  .gitignore
  README.md

  docs/
    PROJECT_BRIEF.md     # Onboarding for Codex
    ARCHITECTURE.md      # System diagram + components
    DECISIONS.md         # ADRs
    TASKS.md             # Atomic tasks for Codex
    api-contracts.md     # API endpoint specs
    Project Documentation/
      functional_requirements_GPToutfit.md   # FR v4.0 — AI Wardrobe spec
      project_tracker_GPToutfit.md           # PM v4.0 — Sprint roadmap
      technical_architecture_GPToutfit.md    # System architecture doc

  .planning/
    REQUIREMENTS.md      # All requirements with IDs
    ROADMAP.md           # Phased delivery plan

  backend/
    main.py              # FastAPI entry point + static mounts (/images/, /photos/, /)
    config.py            # Settings loader
    api/
      routes.py          # API routes: /analyze, /wardrobe/discover, /health, /feedback
    modules/
      image_analyzer.py  # GPT-4o-mini vision analysis
      embeddings.py      # Embedding generation + caching
      matcher.py         # Vectorized numpy cosine similarity search
      guardrail.py       # Match validation layer (editorial stylist voice)
      feedback.py        # In-memory like/dislike feedback store
      inventory.py       # Mock inventory status
      retry.py           # Shared OpenAI retry wrapper
    data/
      loader.py          # CSV catalog loader with USAGE_SYNONYMS enrichment

  frontend/
    index.html           # AI Stylist + AI Wardrobe (SPA, section toggle)

  Photos/                # Try-on model/user images
    john.png             # Male AI model
    Lucy.png             # Female AI model
    javier_full.png      # Male user photo
    Laura_full.png       # Female user photo

  sample_clothes/
    sample_styles.csv    # Clothing catalog (~10K items)
    sample_images_large/ # Product images ({id}.jpg), served at /images/

  scripts/
    generate_embeddings.py  # One-time embedding precomputation
    expand_catalog.py       # Stratified 10K sample from Kaggle dataset

  tests/
    conftest.py          # Shared test fixtures
    test_matcher.py      # Matcher unit tests
    test_loader.py       # Loader unit tests
    test_embeddings.py   # Embeddings unit tests (mocked OpenAI)
    test_integration.py  # Full pipeline integration test

  Dockerfile             # python:3.11-slim, non-root user
  docker-compose.yml     # Port 8000, healthcheck, .env mount

  data/
    embeddings_cache.pkl # Pre-computed embeddings (pickle)
```

## Coding Standards
- Type hints on all function signatures
- Docstrings on all public functions (Google style)
- No business logic in routes — delegate to modules
- All OpenAI calls go through a shared retry wrapper
- Config accessed via a single Settings object (pydantic-settings)

## Key Architectural Decisions
- See docs/DECISIONS.md for full ADR log
- FastAPI chosen for async support and auto-generated OpenAPI docs
- Pickle for embeddings cache (simplicity over DB for MVP)
- Single HTML frontend (no framework) to minimize scope
- Guardrail as separate module to allow independent tuning
- AI Wardrobe Discover lives in its own tab, not in AI Stylist (v4.0 decision)
- Shared wardrobe basket via sessionStorage bridges AI Stylist and AI Wardrobe
- Try-on is CSS composite only (client-side) — AI generative try-on deferred to Phase 4

## Running the Project
```bash
# 1. Setup
cp .env.template .env   # Fill in OPENAI_API_KEY
pip install -r requirements.txt

# 2. Pre-compute embeddings
python scripts/generate_embeddings.py

# 3. Start server
uvicorn backend.main:app --reload
```

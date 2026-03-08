# GPToutfit — Codex Task Prompts

> These are self-contained task prompts for OpenAI Codex. Each task is independent and includes all context needed for implementation. Execute them in order.

---

## Task 1: Unit Tests (02-01)

**Goal:** Write unit tests for the three core backend modules: matcher, loader, and embeddings. Target >80% coverage for each.

**Files to create:**
- `tests/test_matcher.py`
- `tests/test_loader.py`
- `tests/test_embeddings.py`
- `tests/__init__.py` (empty)
- `tests/conftest.py` (shared fixtures)

**Context — what each module does:**

### `backend/modules/matcher.py`
- `find_matches(query_embedding, catalog, cached_embeddings, query_gender, query_article_type, threshold, top_k)` → list[dict]
  - Filters catalog: same gender (or Unisex) + different articleType
  - Computes cosine similarity between query_embedding and each item's cached embedding
  - Returns top_k items above threshold, sorted by score descending
  - Each result has an added `similarity_score` field
- `cosine_similarity(vec_a, vec_b)` → float (numpy dot product / norms)
- `_normalize_article_type(article_type)` → str (strip, lowercase, remove trailing 's')

### `backend/data/loader.py`
- `load_catalog(csv_path)` → list[dict] — reads CSV with pandas, fills NaN with ""
- `build_description(item)` → str — joins productDisplayName, articleType, baseColour, gender, usage, season

### `backend/modules/embeddings.py`
- `generate_embedding(text)` → list[float] — calls OpenAI API (mock this)
- `load_cached_embeddings(cache_path)` → dict — loads pickle file
- `save_embeddings_cache(embeddings, cache_path)` → None — saves pickle file

**Test requirements:**
1. Use `pytest` as test framework
2. Mock all OpenAI API calls — never make real API calls in tests
3. Use `tmp_path` fixture for file I/O tests (pickle, CSV)
4. Test edge cases:
   - Empty catalog
   - No matches above threshold
   - Unisex gender matching (both directions)
   - Singular/plural articleType normalization ("Shirt" vs "Shirts")
   - Zero-vector embeddings (cosine similarity should return 0.0)
   - Missing pickle file (should return empty dict)
   - CSV with NaN values
5. Create a small sample CSV fixture (5-10 rows) and sample embeddings dict for tests
6. Add `pytest` and `pytest-asyncio` to requirements.txt if not present

**File structure:**
```
tests/
  __init__.py
  conftest.py          # Shared fixtures: sample catalog, sample embeddings, mock OpenAI
  test_matcher.py      # Tests for find_matches, cosine_similarity, _normalize_article_type
  test_loader.py       # Tests for load_catalog, build_description
  test_embeddings.py   # Tests for generate_embedding (mocked), load/save cache
```

**Run with:** `pytest tests/ -v --tb=short`

---

## Task 2: Integration Test (02-02)

**Goal:** Write an integration test that exercises the full `/analyze` pipeline end-to-end with mocked OpenAI responses.

**File to create:** `tests/test_integration.py`

**Context — the API endpoint:**

`POST /analyze` accepts `multipart/form-data` with an `image` field (JPEG/PNG/WebP bytes).

The pipeline:
1. `analyze_image(image_bytes)` → calls GPT-4o-mini vision → returns `{style, color, gender, articleType, description}`
2. `generate_embedding(description)` → calls text-embedding-3-large → returns 3072-dim vector
3. `load_catalog(csv_path)` → reads CSV
4. `load_cached_embeddings(cache_path)` → loads pickle
5. `find_matches(...)` → cosine similarity filtering
6. `validate_matches(...)` → calls GPT-4o-mini for each candidate → returns approved items with reasoning
7. `_add_image_urls(matches)` → adds `image_url` field if product image exists on disk
8. Returns `{uploaded_item, uploaded_preview (base64), matches}`

**Test requirements:**
1. Use `pytest` + `httpx` + FastAPI's `TestClient`
2. Mock ALL OpenAI calls using `unittest.mock.patch`:
   - Mock `analyze_image` to return a fixed dict: `{style: "Casual", color: "Blue", gender: "Men", articleType: "Shirts", description: "Blue casual men's shirt"}`
   - Mock `generate_embedding` to return a fixed 3072-dim vector (e.g., all 0.1s)
   - Mock `validate_matches` to return all candidates with reasoning "Test reasoning"
3. Use a small test CSV (5 rows) and a matching pickle file with pre-computed fake embeddings
4. Create a minimal 1x1 JPEG test image (can be generated with Python's `struct` module or a bytes literal)
5. Test scenarios:
   - Happy path: upload image → get matches with image_url and uploaded_preview
   - No image provided → 400
   - Empty image bytes → 400
   - No matches above threshold → empty matches array with proper no-match response
6. Verify response structure: `uploaded_item`, `uploaded_preview` (starts with "data:image"), `matches` (list with `reasoning`, `image_url`, `similarity_score`)

**Run with:** `pytest tests/test_integration.py -v`

---

## Task 3: Docker + docker-compose (02-03)

**Goal:** Containerize GPToutfit with Docker and docker-compose for portable deployment.

**Files to create:**
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

**Context — project structure:**
```
GPToutfit/
  backend/          # Python FastAPI app
  frontend/         # Static HTML (served by FastAPI)
  sample_clothes/   # CSV catalog + product images (1000 JPGs)
  scripts/          # Embedding generation script
  data/             # Embeddings cache (pickle file, ~50MB)
  requirements.txt  # Python deps
  .env.template     # Environment variables
```

**Server command:** `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

**Requirements:**
1. `Dockerfile`:
   - Base image: `python:3.11-slim`
   - Install requirements.txt
   - Copy backend/, frontend/, sample_clothes/, data/ directories
   - Expose port 8000
   - CMD: uvicorn backend.main:app --host 0.0.0.0 --port 8000
   - Use a non-root user for security
   - Multi-stage build is NOT needed (single stage is fine for this project)

2. `docker-compose.yml`:
   - Single service: `gptoutfit`
   - Build from current directory
   - Map port 8000:8000
   - Mount `.env` file for secrets (env_file: .env)
   - Mount `data/` volume so embeddings cache persists across rebuilds
   - Health check: `curl -f http://localhost:8000/health`

3. `.dockerignore`:
   - Ignore: `.git`, `__pycache__`, `*.pyc`, `.env`, `venv/`, `node_modules/`, `.planning/`, `docs/`
   - Do NOT ignore: `data/`, `sample_clothes/`, `frontend/`, `backend/`

**Test with:**
```bash
docker-compose build
docker-compose up -d
curl http://localhost:8000/health  # Should return {"status":"ok"}
docker-compose down
```

---

## Task 4: Recommendation Feedback & Save (02-08 / FR-18)

**Goal:** Add like/dislike buttons and a session-based wishlist to the frontend. Store feedback in-memory on the backend for future model refinement.

**Files to modify:**
- `frontend/index.html` — add UI buttons and wishlist panel
- `backend/api/routes.py` — add feedback endpoint
- Create: `backend/modules/feedback.py` — in-memory feedback store

**Requirements:**

### Frontend (in `frontend/index.html`):
1. Add to each `.match-card-body` (after the reasoning paragraph):
   - A like button (thumbs up icon) and dislike button (thumbs down icon)
   - When clicked, send POST to `/feedback` with: `{item_id, action: "like"|"dislike"}`
   - Visual feedback: liked cards get a subtle green left border, disliked get a muted opacity
   - A "Save to wishlist" bookmark icon — adds the item to a client-side wishlist array

2. Add a "Wishlist" floating panel (bottom-right corner):
   - Shows count badge when items are saved
   - Click to expand and see saved items (name + image thumbnail)
   - "Remove" button per item
   - Wishlist persists in `sessionStorage` (not localStorage — session only)

### Backend:
3. Create `backend/modules/feedback.py`:
   ```python
   # In-memory feedback store (dict of lists)
   _feedback: dict[str, list] = {"likes": [], "dislikes": []}

   def record_feedback(item_id: str, action: str) -> None:
       # Append to likes or dislikes list

   def get_feedback_summary() -> dict:
       # Return counts and recent items
   ```

4. Add to `backend/api/routes.py`:
   ```python
   @router.post("/feedback")
   async def feedback(body: dict) -> dict:
       # Validate: item_id (str) and action ("like" or "dislike")
       # Call record_feedback()
       # Return {"status": "recorded"}
   ```

**Design rules:**
- Like/dislike buttons should be minimal — small icons, not prominent
- Wishlist panel should not interfere with the outfit board layout
- All styling must use the existing CSS variables (--accent, --border, --muted, etc.)
- No external libraries — pure vanilla JS

---

## Task 5: Full 44K Catalog + Performance (02-04)

**Goal:** Support the full 44,391-item catalog with acceptable performance.

**Context:**
- Current catalog: `sample_clothes/sample_styles.csv` (1,000 items)
- Full catalog: needs to be downloaded from the OpenAI Cookbook dataset
- Embeddings are pre-computed via `scripts/generate_embeddings.py` and cached in `data/embeddings_cache.pkl`
- Current: catalog and embeddings are loaded from disk on EVERY request (in `routes.py`)

**Files to modify:**
- `backend/api/routes.py` — load catalog + embeddings once at startup, not per-request
- `backend/data/loader.py` — add startup cache function
- `backend/modules/matcher.py` — optimize for 44K items (numpy vectorized operations)

**Requirements:**

### 1. Startup caching (most important):
In `routes.py`, load catalog and embeddings ONCE at module level or in a FastAPI startup event:
```python
@app.on_event("startup")
async def load_data():
    global _catalog, _embeddings
    _catalog = load_catalog(settings.catalog_csv_path)
    _embeddings = load_cached_embeddings(settings.embeddings_cache_path)
```
Then use `_catalog` and `_embeddings` in the `/analyze` endpoint instead of loading per-request.

### 2. Vectorized matching:
In `matcher.py`, replace the Python for-loop with numpy matrix operations:
```python
# Instead of looping through each item:
# 1. Build a numpy matrix of all candidate embeddings (N x 3072)
# 2. Compute all cosine similarities in one vectorized operation
# 3. Apply threshold filter
# 4. Sort and take top_k
```
This should reduce matching time from O(N) Python loop to a single numpy operation.

### 3. Update config defaults:
In `.env.template`, note that `COSINE_SIMILARITY_THRESHOLD` and `TOP_K_MATCHES` may need re-tuning with the larger catalog. Do NOT change the defaults — just add a comment.

**Performance target:** < 2 seconds for the matching step (excluding OpenAI API calls) with 44K items.

**Test:** Run the server with the full catalog and verify `/analyze` still returns results in < 20s total.

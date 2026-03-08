# Implementation Tasks for Codex

> Read CLAUDE.md and docs/ARCHITECTURE.md before starting any task.
> Each task is atomic and self-contained. Complete them in order.

---

## TASK-01: Configuration Module
- **Status:** READY
- **Files:** `backend/config.py`
- **Read first:** `CLAUDE.md`, `.env.template`
- **Spec:**
  - Create a `Settings` class extending `pydantic_settings.BaseSettings`
  - Fields: `openai_api_key` (str, required), `vision_model` (str, default "gpt-4o-mini"),
    `guardrail_model` (str, default "gpt-4o-mini"), `embedding_model` (str, default
    "text-embedding-3-large"), `cosine_similarity_threshold` (float, default 0.6),
    `top_k_matches` (int, default 2), `catalog_csv_path` (str, default
    "data/sample_styles.csv"), `embeddings_cache_path` (str, default
    "data/embeddings_cache.pkl"), `host` (str, default "0.0.0.0"), `port` (int, default 8000)
  - Add `model_config` with `env_file = ".env"`
  - Export a singleton: `settings = Settings()`
- **Acceptance criteria:**
  1. `from backend.config import settings` works
  2. `settings.openai_api_key` reads from OPENAI_API_KEY env var
  3. All defaults match .env.template values
  4. App fails fast if OPENAI_API_KEY is not set
- **Do NOT:** Add any OpenAI client initialization here. That belongs in modules.

---

## TASK-02: OpenAI Retry Wrapper
- **Status:** READY
- **Files:** `backend/modules/retry.py` (new file)
- **Read first:** `CLAUDE.md`, `backend/config.py`
- **Spec:**
  - Create `async def call_openai_with_retry(callable, *args, max_retries=10, **kwargs)`
  - Implements exponential backoff: wait = min(2^attempt, 60) seconds
  - Catches `openai.RateLimitError`, `openai.APITimeoutError`, `openai.APIConnectionError`
  - Raises after max_retries exhausted
  - Logs each retry attempt with attempt number
- **Acceptance criteria:**
  1. Retries up to 10 times on transient errors
  2. Exponential backoff with cap at 60 seconds
  3. Raises original exception after max retries
  4. Does not retry on non-transient errors (e.g., AuthenticationError)
- **Do NOT:** Add global state or singletons. This is a pure utility function.

---

## TASK-03: CSV Catalog Loader
- **Status:** READY
- **Files:** `backend/data/loader.py`
- **Read first:** `CLAUDE.md`, `backend/config.py`, `data/sample_styles.csv` (headers)
- **Spec:**
  - `def load_catalog(csv_path: str) -> list[dict]`
  - Reads CSV using pandas
  - Returns list of dicts, each with at minimum: `id`, `productDisplayName`,
    `gender`, `articleType`, `baseColour`, `usage`, `season`
  - Handles missing values gracefully (fill NaN with empty string)
  - `def build_description(item: dict) -> str` — concatenates relevant fields
    into a single text description for embedding
- **Acceptance criteria:**
  1. Returns list of dicts from CSV
  2. All expected fields present in each dict
  3. No NaN values in output
  4. `build_description` returns a human-readable string combining key attributes
- **Do NOT:** Filter or transform data beyond loading and NaN handling.

---

## TASK-04: Image Analyzer Module
- **Status:** READY
- **Files:** `backend/modules/image_analyzer.py`
- **Read first:** `CLAUDE.md`, `backend/modules/retry.py`, `backend/config.py`
- **Spec:**
  - `async def analyze_image(image_bytes: bytes) -> dict`
  - Encodes image to base64
  - Sends to GPT-4o-mini vision endpoint with structured prompt
  - Prompt must request: style, color, gender, articleType, description
  - Returns dict with those keys
  - Uses retry wrapper for the API call
  - Response must be parsed as JSON (instruct model to return JSON)
- **Acceptance criteria:**
  1. Accepts raw image bytes, returns structured dict
  2. Dict contains keys: style, color, gender, articleType, description
  3. Uses retry wrapper
  4. Handles model returning non-JSON gracefully (retry or error)
- **Do NOT:** Save the image to disk. Process in-memory only.

---

## TASK-05: Embeddings Module
- **Status:** READY
- **Files:** `backend/modules/embeddings.py`
- **Read first:** `CLAUDE.md`, `backend/modules/retry.py`, `backend/config.py`
- **Spec:**
  - `async def generate_embedding(text: str) -> list[float]`
    - Calls text-embedding-3-large via OpenAI API
    - Uses retry wrapper
    - Returns embedding vector (list of floats)
  - `def load_cached_embeddings(cache_path: str) -> dict`
    - Loads pickle file containing {item_id: embedding_vector} mapping
    - Returns the dict
  - `def save_embeddings_cache(embeddings: dict, cache_path: str) -> None`
    - Saves embeddings dict to pickle file
- **Acceptance criteria:**
  1. `generate_embedding` returns a list of floats (3072 dimensions)
  2. `load_cached_embeddings` loads from pickle without error
  3. `save_embeddings_cache` writes valid pickle file
  4. Uses retry wrapper on API calls
- **Do NOT:** Implement batch embedding logic here. That goes in the script.

---

## TASK-06: Matcher Module
- **Status:** READY
- **Files:** `backend/modules/matcher.py`
- **Read first:** `CLAUDE.md`, `backend/modules/embeddings.py`, `backend/data/loader.py`
- **Spec:**
  - `def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float`
    - Computes cosine similarity between two vectors using numpy
  - `def find_matches(query_embedding, catalog, cached_embeddings, query_gender,
    query_article_type, threshold=0.6, top_k=2) -> list[dict]`
    - Filters catalog: same gender (or Unisex), different articleType
    - Computes cosine similarity for each remaining item
    - Returns top-K items above threshold, sorted by score descending
    - Each result includes: item data + similarity_score
- **Acceptance criteria:**
  1. Cosine similarity returns float between -1 and 1
  2. Gender filter: keeps items matching query gender OR "Unisex"
  3. ArticleType filter: excludes items with same articleType as query
  4. Returns at most top_k items
  5. All returned items have similarity >= threshold
  6. Results sorted by similarity descending
- **Do NOT:** Make any API calls. This is pure computation.

---

## TASK-07: Guardrail Module
- **Status:** READY
- **Files:** `backend/modules/guardrail.py`
- **Read first:** `CLAUDE.md`, `backend/modules/retry.py`, `backend/config.py`
- **Spec:**
  - `async def validate_matches(original_description: str,
    candidates: list[dict]) -> list[dict]`
    - For each candidate, sends prompt to GPT-4o-mini asking:
      "Does [candidate] complement [original item] as an outfit?"
    - Expects structured response: {approved: bool, reasoning: str}
    - Uses retry wrapper
    - Returns only approved candidates, each with added `reasoning` field
- **Acceptance criteria:**
  1. All candidates are validated (none skipped)
  2. Only approved candidates are returned
  3. Each returned candidate includes `reasoning` string
  4. Uses retry wrapper for each API call
  5. Handles model returning non-JSON gracefully
- **Do NOT:** Modify the candidate data beyond adding the `reasoning` field.

---

## TASK-08: API Route — POST /analyze
- **Status:** BLOCKED (depends on TASK-01 through TASK-07)
- **Files:** `backend/api/routes.py`, `backend/main.py`
- **Read first:** `CLAUDE.md`, `docs/api-contracts.md`, all module stubs
- **Spec:**
  - `POST /analyze` — accepts multipart/form-data with image file
  - Orchestration flow:
    1. Receive image → `image_analyzer.analyze_image()`
    2. Generate query embedding → `embeddings.generate_embedding()`
    3. Load catalog + cached embeddings
    4. Find matches → `matcher.find_matches()`
    5. Validate → `guardrail.validate_matches()`
    6. Return results as JSON
  - `GET /health` — returns `{"status": "ok"}`
  - Wire routes into FastAPI app in main.py
- **Acceptance criteria:**
  1. POST /analyze accepts image file upload
  2. Returns JSON array of validated matches with reasoning
  3. Returns appropriate error codes (400 for no image, 500 for API failures)
  4. GET /health returns 200
  5. Pipeline never returns results that skipped guardrail
- **Do NOT:** Put business logic directly in the route handler. Call modules.

---

## TASK-09: Embedding Generation Script
- **Status:** READY
- **Files:** `scripts/generate_embeddings.py`
- **Read first:** `CLAUDE.md`, `backend/modules/embeddings.py`, `backend/data/loader.py`
- **Spec:**
  - Standalone script (not part of the server)
  - Loads catalog CSV via loader
  - For each item, builds description string and generates embedding
  - Saves all embeddings to pickle cache file
  - Prints progress (e.g., "Processing item 50/1000")
  - Handles interruption gracefully (saves partial progress)
- **Acceptance criteria:**
  1. Generates embeddings for all catalog items
  2. Saves to configured cache path
  3. Shows progress output
  4. Can resume from partial cache (skips items already embedded)
  5. Uses retry wrapper for API calls
- **Do NOT:** Start the FastAPI server. This is an offline script.

---

## TASK-10: Frontend UI
- **Status:** READY
- **Files:** `frontend/index.html`
- **Read first:** `CLAUDE.md`, `docs/api-contracts.md`
- **Spec:**
  - Single HTML file with embedded CSS and JS
  - Image upload area (file input + drag-and-drop)
  - "Analyze" button to trigger POST /analyze
  - Loading spinner while waiting
  - Results section: cards for each match showing productDisplayName,
    articleType, baseColour, similarity score, and AI reasoning
  - Error display for failed requests
- **Acceptance criteria:**
  1. Can select and upload an image file
  2. Shows loading state during analysis
  3. Displays match results as styled cards
  4. Shows error messages on failure
  5. Works in modern browsers (Chrome, Firefox, Safari)
- **Do NOT:** Use any frontend framework or build tools. Pure HTML/JS/CSS.

---

## TASK-11: FastAPI Static File Serving + CORS
- **Status:** BLOCKED (depends on TASK-08)
- **Files:** `backend/main.py`
- **Read first:** `CLAUDE.md`, `backend/main.py`
- **Spec:**
  - Mount `frontend/` directory as static files at root
  - Add CORS middleware (allow all origins for development)
  - Serve index.html at `/`
- **Acceptance criteria:**
  1. Visiting http://localhost:8000/ serves the frontend
  2. Frontend can call /analyze without CORS errors
- **Do NOT:** Add authentication or production CORS restrictions for MVP.

---

## TASK-12: Requirements File
- **Status:** READY
- **Files:** `requirements.txt`
- **Spec:**
  - List all Python dependencies with pinned major versions:
    `fastapi`, `uvicorn[standard]`, `openai`, `python-multipart`,
    `pydantic-settings`, `pandas`, `numpy`, `python-dotenv`
- **Acceptance criteria:**
  1. `pip install -r requirements.txt` succeeds
  2. All imports across the codebase resolve
- **Do NOT:** Add testing or development dependencies here.

# GPToutfit - System Architecture

## System Diagram

```
+------------------+       +-------------------------------------------+
|                  |       |              BACKEND (FastAPI)             |
|    FRONTEND      |       |                                           |
|                  |       |  +-------------+    +------------------+  |
|  +------------+  | POST  |  |   routes.py |    |   config.py      |  |
|  | index.html |--+------>|  | /analyze    |--->| Settings loader  |  |
|  | (upload +  |  | image |  +------+------+    +------------------+  |
|  |  results)  |  |       |         |                                 |
|  +------------+  |       |         v                                 |
|                  |       |  +------+----------+                      |
|                  |       |  | image_analyzer  |  GPT-4o-mini         |
|                  |       |  | (vision)        |  (vision endpoint)   |
|                  |       |  +------+----------+                      |
|                  |       |         |                                 |
|                  |       |         | structured description          |
|                  |       |         | {style, color, gender,          |
|                  |       |         |  articleType, description}      |
|                  |       |         v                                 |
|                  |       |  +------+----------+    +--------------+  |
|                  |       |  | embeddings.py   |--->| cached       |  |
|                  |       |  | (query embed)   |    | embeddings   |  |
|                  |       |  +------+----------+    | (.pkl file)  |  |
|                  |       |         |                +--------------+  |
|                  |       |         v                                  |
|                  |       |  +------+----------+                      |
|                  |       |  | matcher.py      |                      |
|                  |       |  | cosine sim      |                      |
|                  |       |  | top-K=2         |                      |
|                  |       |  | threshold>=0.6  |                      |
|                  |       |  | filter: gender, |                      |
|                  |       |  |   articleType   |                      |
|                  |       |  +------+----------+                      |
|                  |       |         |                                  |
|                  |       |         | candidate matches               |
|                  |       |         v                                  |
|                  |       |  +------+----------+                      |
|                  |  JSON |  | guardrail.py    |  GPT-4o-mini         |
|  <results>   <---+------+--| validates each  |  (text endpoint)     |
|                  |       |  | match as outfit |                      |
|                  |       |  +------+----------+                      |
|                  |       |                                           |
+------------------+       +-------------------------------------------+

+-------------------+
| OFFLINE SCRIPTS   |
|                   |
| generate_         |    +-----------------+
| embeddings.py --->|--->| sample_styles   |
| (one-time run)    |    | .csv            |
|                   |    +-----------------+
| Reads CSV,        |           |
| calls embedding   |           v
| API, writes       |    +-----------------+
| .pkl cache        |    | embeddings      |
+-------------------+    | _cache.pkl      |
                         +-----------------+
```

## Component Descriptions

### Frontend (`frontend/index.html`)
Single-page application with:
- Image upload form (drag-and-drop or file picker)
- Loading state while processing
- Results display: matched items with images, names, and AI reasoning
- Error handling for failed requests

### API Layer (`backend/api/routes.py`)
- `POST /analyze` — accepts image upload, orchestrates the pipeline, returns matches
- `GET /health` — health check endpoint
- No business logic — delegates everything to modules

### Image Analyzer (`backend/modules/image_analyzer.py`)
- Sends uploaded image to GPT-4o-mini vision endpoint
- Extracts: style, color palette, gender, articleType, free-text description
- Returns structured dict for downstream use
- Uses retry wrapper for API resilience

### Embeddings (`backend/modules/embeddings.py`)
- `generate_embedding(text)` — calls text-embedding-3-large
- `load_cached_embeddings(path)` — loads pre-computed catalog embeddings from .pkl
- Used both at query time (for the analyzed description) and offline (for catalog)

### Matcher (`backend/modules/matcher.py`)
- Computes cosine similarity between query embedding and all catalog embeddings
- Applies filters: same gender (or Unisex), different articleType
- Returns top-K (K=2) items above threshold (0.6)
- Returns candidate list with similarity scores

### Guardrail (`backend/modules/guardrail.py`)
- Receives: original item description + candidate matches
- Sends to GPT-4o-mini: "Would these items work together as an outfit?"
- Returns validated matches with AI-generated reasoning
- Filters out any items that don't pass validation

### Config (`backend/config.py`)
- Pydantic Settings class loading from .env
- Single source for all configuration values
- Validates required fields at startup

### Data Loader (`backend/data/loader.py`)
- Reads sample_styles.csv into structured format
- Provides catalog access to matcher module

### Embedding Script (`scripts/generate_embeddings.py`)
- Offline script run once (or when catalog changes)
- Reads CSV, generates embedding for each item, saves to .pkl cache

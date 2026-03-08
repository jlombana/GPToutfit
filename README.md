# GPToutfit - AI-Powered Clothing Matchmaker

Upload a clothing image and get AI-curated outfit recommendations.

## How It Works

1. **Upload** an image of a clothing item
2. **Analyze** — GPT-4o-mini vision extracts style, color, gender, and type
3. **Match** — RAG search finds complementary items from the catalog using embeddings
4. **Validate** — Guardrail layer confirms each match works as an outfit
5. **Results** — Curated recommendations with AI-generated reasoning

## Quick Start

```bash
# 1. Clone and setup
cp .env.template .env
# Edit .env and add your OPENAI_API_KEY

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your catalog
# Place sample_styles.csv in data/

# 4. Generate embeddings (one-time)
python scripts/generate_embeddings.py

# 5. Start the server
uvicorn backend.main:app --reload

# 6. Open http://localhost:8000
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system diagram.

```
Image -> Analyzer -> Embeddings -> Matcher -> Guardrail -> Results
```

## Project Structure

```
backend/           # FastAPI server + pipeline modules
frontend/          # Single-page upload UI
scripts/           # Offline embedding generation
data/              # Catalog CSV + embedding cache
docs/              # Architecture, decisions, tasks
```

## Tech Stack

- **Backend:** Python, FastAPI
- **AI:** OpenAI GPT-4o-mini (vision + guardrail), text-embedding-3-large
- **Frontend:** Vanilla HTML/JS/CSS

# GPToutfit — AI-Powered Clothing Matchmaker

GPToutfit is an intelligent fashion assistant that combines computer vision, natural language processing, and vector similarity search to help you discover outfits. Upload a photo of a clothing item and get curated recommendations, or describe an occasion and receive a complete outfit suggestion — all powered by OpenAI's latest models.

Built as a full-stack application with a FastAPI backend and a premium editorial-style frontend, GPToutfit demonstrates how RAG (Retrieval-Augmented Generation) pipelines can be applied beyond traditional text use cases.

---

## Features

### AI Stylist — Image-Based Discovery
Upload a photo of any clothing item and GPToutfit will:
1. **Analyze** the image using GPT-4o-mini vision to extract style, color palette, gender, and article type
2. **Search** a 10,000-item catalog using text-embedding-3-large cosine similarity
3. **Validate** each match through a guardrail layer that acts as an editorial stylist, rejecting clashing combinations
4. **Present** curated results with AI-generated reasoning explaining why each piece works

Supports two search modes:
- **Complementary** — finds items that pair well (e.g., upload a blazer, get matching trousers)
- **Similarity** — finds visually similar alternatives (e.g., upload a dress, get similar styles)

### AI Wardrobe — Occasion-Based Discovery
Describe where you're going and GPToutfit builds an outfit:
1. **Input** an occasion (e.g., "summer wedding in Tuscany") plus your gender and style vibe
2. **Search** the full catalog across all categories using semantic embedding search
3. **Generate** an editorial outfit concept describing the look
4. **Display** results grouped by category (tops, bottoms, shoes, accessories)

### My Wardrobe — Save, Collect & Try On
- Save items from either AI Stylist or AI Wardrobe into a shared wardrobe basket
- Browse your saved collection across sessions
- **Try It On** — CSS composite overlay that places selected items on model photos for a quick visual preview (fully client-side, no images uploaded)

---

## Architecture

```
                        GPToutfit Pipeline
                        ==================

  AI Stylist                              AI Wardrobe
  ----------                              -----------
  Image Upload                            Occasion Text
       |                                       |
       v                                       v
  [GPT-4o-mini Vision]                  [text-embedding-3-large]
  Extract: style, color,                Embed occasion description
  gender, articleType                          |
       |                                       v
       v                                  [Cosine Search]
  [text-embedding-3-large]              Full catalog, gender filter
  Embed structured description                 |
       |                                       v
       v                                  [GPT-4o-mini]
  [Cosine Similarity Search]            Generate outfit concept
  Catalog embeddings (numpy)                   |
       |                                       v
       v                                  Results Grid
  [Guardrail Validator]                  (grouped by category)
  GPT-4o-mini confirms compatibility
       |
       v
  Curated Results
  (with AI reasoning)


              Shared Wardrobe Basket
              ----------------------
              sessionStorage bridge
                     |
                     v
              [Try It On]
              CSS composite overlay
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, uvicorn |
| **Frontend** | Vanilla HTML/JS/CSS (single-page app, editorial design) |
| **Vision Analysis** | OpenAI GPT-4o-mini (multimodal) |
| **Guardrail Validation** | OpenAI GPT-4o-mini |
| **Embeddings** | OpenAI text-embedding-3-large |
| **Vector Search** | NumPy vectorized cosine similarity |
| **Data** | CSV catalog (~10K items), pickle embedding cache |
| **Containerization** | Docker + Docker Compose |

---

## Dataset — Fashion Product Images (Kaggle)

GPToutfit uses the **Fashion Product Images Dataset** from Kaggle, which contains **44,000+ fashion product images** with rich metadata.

**Download the dataset here:**
https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset

> **Why aren't the images included in this repository?**
> The full dataset weighs **~25 GB** (images + archive). GitHub has a 100 MB per-file limit and repositories this large are impractical to clone. Instead, you download the dataset separately and place it in the expected directory structure.

### Setting Up the Dataset

1. **Download** the dataset from Kaggle (you'll need a free Kaggle account)

2. **Extract** the archive into the project:
   ```
   sample_clothes/
     sample_images_large/
       fashion-dataset/          <-- extract here
         styles.csv              # 44,446 items with metadata
         images.csv              # Image metadata
         images/                 # Product images (id.jpg)
           1163.jpg
           1164.jpg
           ...
   ```

3. **Run the catalog expansion script** to create a stratified 10K sample:
   ```bash
   python scripts/expand_catalog.py --size 10000 --seed 42
   ```
   This will:
   - Read the full `styles.csv` (44K items)
   - Take a gender-stratified random sample of 10,000 items
   - Copy only those 10,000 images to `sample_clothes/sample_images_large/`
   - Write the working catalog to `data/sample_styles.csv`
   - Invalidate any stale embedding caches

4. **Generate embeddings** for the sampled catalog:
   ```bash
   python scripts/generate_embeddings.py
   ```
   This pre-computes text-embedding-3-large vectors for all 10K items and caches them in `data/embeddings_cache.pkl`.

### Dataset Columns

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Unique product ID (maps to `{id}.jpg`) | `15970` |
| `gender` | Target gender | Men, Women, Boys, Girls, Unisex |
| `masterCategory` | Top-level category | Apparel, Accessories, Footwear |
| `subCategory` | Sub-category | Topwear, Bottomwear, Watches |
| `articleType` | Specific type | Tshirts, Jeans, Casual Shoes |
| `baseColour` | Primary color | Navy Blue, Black, White |
| `season` | Target season | Summer, Winter, Fall, Spring |
| `year` | Year of product | 2012, 2016, 2017 |
| `usage` | Usage context | Casual, Formal, Sports, Ethnic |
| `productDisplayName` | Full product name | "Turtle Check Men Navy Blue Shirt" |

---

## Quick Start

### Prerequisites
- Python 3.11+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- The Fashion Product Images dataset (see above)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/jlombana/GPToutfit.git
cd GPToutfit

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.template .env
# Edit .env and set your OPENAI_API_KEY

# 5. Download and setup the dataset (see "Dataset" section above)
python scripts/expand_catalog.py --size 10000

# 6. Generate embeddings (one-time, takes ~5 minutes)
python scripts/generate_embeddings.py

# 7. Start the server
uvicorn backend.main:app --reload

# 8. Open http://localhost:8000
```

### Docker

```bash
# Build and run
docker compose up --build

# The app will be available at http://localhost:8000
```

> Note: Make sure `data/embeddings_cache.pkl` exists before building. The Docker volume mounts `./data` so the cache persists across rebuilds.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | AI Stylist — upload an image, get outfit matches |
| `POST` | `/wardrobe/discover` | AI Wardrobe — occasion-based outfit discovery |
| `GET` | `/health` | Liveness check |
| `POST` | `/feedback` | Submit like/dislike feedback for a recommendation |

### Example: AI Stylist

```bash
curl -X POST http://localhost:8000/analyze \
  -F "image=@my_shirt.jpg" \
  -F "occasion=casual friday" \
  -F "search_mode=complementary"
```

### Example: AI Wardrobe

```bash
curl -X POST http://localhost:8000/wardrobe/discover \
  -H "Content-Type: application/json" \
  -d '{"occasion": "summer wedding in Tuscany", "gender": "Men", "style_vibe": "smart casual", "top_k": 20}'
```

---

## Project Structure

```
GPToutfit/
  backend/
    main.py                 # FastAPI entry point, static file mounts
    config.py               # Pydantic settings loader
    api/
      routes.py             # /analyze, /wardrobe/discover, /health, /feedback
    modules/
      image_analyzer.py     # GPT-4o-mini vision — extracts clothing attributes
      embeddings.py         # text-embedding-3-large — generation + caching
      matcher.py            # NumPy vectorized cosine similarity search
      guardrail.py          # GPT-4o-mini validation — editorial stylist voice
      feedback.py           # In-memory like/dislike store
      inventory.py          # Mock inventory status
      retry.py              # Shared OpenAI retry wrapper (exponential backoff)
    data/
      loader.py             # CSV catalog loader with usage synonym enrichment

  frontend/
    index.html              # Single-page app (AI Stylist + AI Wardrobe + My Wardrobe)

  scripts/
    expand_catalog.py       # Stratified sampling from full Kaggle dataset
    generate_embeddings.py  # One-time embedding precomputation

  tests/
    test_matcher.py         # Matcher unit tests
    test_loader.py          # Loader unit tests
    test_embeddings.py      # Embeddings unit tests (mocked OpenAI)
    test_integration.py     # Full pipeline integration test

  Photos/                   # Try-on model/user photos (CSS composite)
  sample_clothes/           # Catalog CSV + product images
  data/                     # Embeddings cache (pickle)
  docs/                     # Architecture docs, decisions, API contracts
```

---

## How It Works Under the Hood

### Embedding Strategy
Each catalog item is converted to a rich text description combining all its metadata fields, then embedded using `text-embedding-3-large`. These embeddings are pre-computed once and cached as a pickle file, enabling instant cosine similarity lookups at query time.

### Guardrail Validation
Raw similarity search can produce technically similar but aesthetically clashing results. The guardrail module sends each candidate match to GPT-4o-mini with the prompt: *"As an editorial fashion stylist, would you recommend these items together?"* — filtering out mismatches and providing human-readable reasoning.

### Tuned Thresholds
The similarity thresholds were empirically tuned against the real catalog:

| Parameter | Value | Why |
|-----------|-------|-----|
| Base cosine threshold | 0.40 | Cross-category items score 0.45-0.55; default 0.6 was too strict |
| Complementary threshold | 0.24 | Cross-category text descriptions are semantically distant |
| Similarity threshold | 0.34 | Same-category items naturally score higher |
| Discover threshold | 0.25 | Occasion text to product embedding is inherently noisy |
| Top-K (Stylist) | 5 | With fewer candidates, guardrail rejections often left zero results |
| Top-K (Discover) | 20 | Occasion search needs breadth across categories |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is for educational and research purposes. The Fashion Product Images Dataset is provided by [Param Aggarwal on Kaggle](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset) under its own license terms.

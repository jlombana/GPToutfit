# API Contracts

## POST /analyze

Upload a clothing image and receive outfit recommendations (complementary or similar items).

### Request
- **Method:** POST
- **Content-Type:** multipart/form-data
- **Body:**
  - `image` (file, required) — image file (JPEG, PNG, WebP)
  - `occasion` (string, optional) — occasion context, e.g. "garden wedding"
  - `search_mode` (string, optional) — `"complementary"` (default) or `"similarity"`

### Response (200 OK)
```json
{
  "uploaded_item": {
    "style": "casual",
    "color": "navy blue",
    "gender": "Men",
    "articleType": "Shirts",
    "description": "A casual navy blue button-down shirt with a slim fit"
  },
  "uploaded_preview": "data:image/jpeg;base64,/9j/4AAQ...",
  "occasion": "",
  "search_mode": "complementary",
  "matches": [
    {
      "id": 12345,
      "productDisplayName": "Khaki Chinos",
      "gender": "Men",
      "articleType": "Trousers",
      "baseColour": "Khaki",
      "similarity_score": 0.52,
      "reasoning": "The structured silhouette of your shirt calls for something relaxed below — these slim chinos balance the look.",
      "image_url": "/images/12345.jpg",
      "match_label": "Great Pick",
      "label_color": "#1A3A5C",
      "inventory": {
        "in_stock": true,
        "quantity": 12
      }
    }
  ]
}
```

### Response (400 Bad Request)
```json
{
  "detail": "No image file provided"
}
```

### Response (500 Internal Server Error)
```json
{
  "detail": "Internal server error"
}
```

---

## GET /health

Health check endpoint.

### Response (200 OK)
```json
{
  "status": "ok"
}
```

---

## POST /feedback

Record like/dislike feedback for a recommendation.

### Request
- **Method:** POST
- **Content-Type:** application/json
- **Body:**
```json
{
  "item_id": "12345",
  "action": "like"
}
```

`action` must be `"like"` or `"dislike"`.

### Response (200 OK)
```json
{
  "status": "recorded"
}
```

### Response (400 Bad Request)
```json
{
  "detail": "item_id and action (like/dislike) required"
}
```

---

## POST /wardrobe/discover

Occasion-based outfit discovery for AI Wardrobe. Embeds the occasion string, searches the full catalog (gender-filtered, no articleType filter), and generates an outfit concept via GPT-4o-mini.

### Request
- **Method:** POST
- **Content-Type:** application/json
- **Body:**
```json
{
  "occasion": "garden wedding in summer",
  "gender": "Women",
  "style_vibe": "Minimalist",
  "top_k": 20
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `occasion` | string | yes | — | Occasion description |
| `gender` | string | yes | — | User's gender for catalog filtering |
| `style_vibe` | string | yes | — | Style preference (e.g. "Minimalist", "Streetwear") |
| `top_k` | int | no | 20 | Max items to return |

### Response (200 OK)
```json
{
  "outfit_concept": "For a summer garden wedding, lean into soft florals and breathable fabrics...",
  "items": [
    {
      "id": 12345,
      "name": "Floral Midi Dress",
      "articleType": "Dresses",
      "baseColour": "Pink",
      "image_url": "/images/12345.jpg",
      "similarity_score": 0.48,
      "reason": ""
    }
  ]
}
```

### Response (400 Bad Request)
```json
{
  "detail": "occasion is required"
}
```

### Response (500 Internal Server Error)
```json
{
  "detail": "Internal server error"
}
```

---

## POST /api/companion-evaluate

AI Stylist Companion — evaluates an outfit selection against an occasion and returns a score with actionable advice.

### Request
- **Method:** POST
- **Content-Type:** application/json
- **Body:**
```json
{
  "occasion": "casual dinner, summer evening",
  "items": [
    { "name": "White Linen Shirt", "category": "Shirts", "description": "White Shirts" },
    { "name": "Navy Chinos", "category": "Trousers", "description": "Navy Trousers" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `occasion` | string | yes | Occasion the outfit is for |
| `items` | array | yes | List of outfit items with name, category, and optional description |

### Response (200 OK)
```json
{
  "overall_score": 7.4,
  "items": [
    { "name": "White Linen Shirt", "score": 9.0, "comment": "Perfect breathable choice for summer" },
    { "name": "Navy Chinos", "score": 8.0, "comment": "Classic pairing with the linen shirt" }
  ],
  "verdict": "Strong casual look. The linen shirt keeps it breezy while the chinos add structure.",
  "improvement": "Consider swapping for loafers instead of boots for a lighter summer feel."
}
```

### Response (400 Bad Request)
```json
{
  "detail": "occasion is required"
}
```

### Response (500 Internal Server Error)
```json
{
  "detail": "Style advice unavailable. Try again."
}
```

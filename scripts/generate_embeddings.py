"""One-time embedding generation script for the clothing catalog.

Reads the catalog CSV, generates embeddings for each item using
text-embedding-3-large, and saves them to a pickle cache file.

See TASK-09 in docs/TASKS.md for implementation spec.

Usage:
    python scripts/generate_embeddings.py
"""
import asyncio

from backend.config import settings
from backend.data.loader import build_description, load_catalog
from backend.modules.embeddings import (
    generate_embedding,
    load_cached_embeddings,
    save_embeddings_cache,
)


async def main() -> None:
    """Generate and persist embeddings for all catalog items."""
    catalog = load_catalog(settings.catalog_csv_path)
    total = len(catalog)
    embeddings_cache = load_cached_embeddings(settings.embeddings_cache_path)

    print(f"Loaded {total} catalog items.")
    print(f"Loaded {len(embeddings_cache)} cached embeddings.")

    try:
        for index, item in enumerate(catalog, start=1):
            item_id = item.get("id")
            if item_id in embeddings_cache or str(item_id) in embeddings_cache:
                print(f"Skipping item {index}/{total} (id={item_id}) - already embedded")
                continue

            print(f"Processing item {index}/{total} (id={item_id})")
            description = build_description(item)
            embedding = await generate_embedding(description)
            embeddings_cache[item_id] = embedding

        save_embeddings_cache(embeddings_cache, settings.embeddings_cache_path)
        print(f"Done. Saved {len(embeddings_cache)} embeddings to {settings.embeddings_cache_path}")
    except KeyboardInterrupt:
        save_embeddings_cache(embeddings_cache, settings.embeddings_cache_path)
        print("\nInterrupted. Partial progress saved.")
    except Exception:
        save_embeddings_cache(embeddings_cache, settings.embeddings_cache_path)
        print("Error occurred. Partial progress saved.")
        raise

if __name__ == "__main__":
    asyncio.run(main())

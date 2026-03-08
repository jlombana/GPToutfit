"""Expand the GPToutfit catalog to 10,000 items from the local Kaggle dataset.

Reads from sample_clothes/sample_images_large/fashion-dataset/styles.csv,
takes a stratified random sample, copies images to sample_images_large/,
and writes the new catalog CSV to data/sample_styles.csv.

Usage:
    python scripts/expand_catalog.py [--seed 42] [--size 10000]
"""
import argparse
import os
import shutil

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "sample_clothes", "sample_images_large", "fashion-dataset")
SOURCE_CSV = os.path.join(DATASET_DIR, "styles.csv")
SOURCE_IMAGES = os.path.join(DATASET_DIR, "images")
TARGET_CSV = os.path.join(BASE_DIR, "data", "sample_styles.csv")
TARGET_IMAGES = os.path.join(BASE_DIR, "sample_clothes", "sample_images_large")

REQUIRED_COLS = [
    "id", "gender", "masterCategory", "subCategory",
    "articleType", "baseColour", "season", "year",
    "usage", "productDisplayName",
]

CACHE_FILES = [
    os.path.join(BASE_DIR, "data", "embeddings_cache.pkl"),
    os.path.join(BASE_DIR, "data", "sample_styles_with_embeddings.csv"),
]


def main(size: int = 10_000, seed: int = 42) -> None:
    print(f"Loading full dataset from {SOURCE_CSV}...")
    df_full = pd.read_csv(SOURCE_CSV, on_bad_lines="skip")
    print(f"  Full dataset: {len(df_full):,} rows")

    missing = [c for c in REQUIRED_COLS if c not in df_full.columns]
    if missing:
        raise ValueError(f"Missing columns in source CSV: {missing}")

    # Filter to rows whose image exists
    print("Checking which IDs have images available...")
    available_ids = set()
    for f in os.listdir(SOURCE_IMAGES):
        if f.endswith((".jpg", ".png")):
            try:
                available_ids.add(int(f.split(".")[0]))
            except ValueError:
                pass
    df_full = df_full[df_full["id"].isin(available_ids)].copy()
    print(f"  Rows with images: {len(df_full):,}")

    # Stratified sample by gender
    actual_size = min(size, len(df_full))
    frac = actual_size / len(df_full)
    sample = (
        df_full.groupby("gender", group_keys=False)
        .apply(lambda g: g.sample(frac=frac, random_state=seed))
    )
    sample = sample.sample(n=actual_size, random_state=seed)[REQUIRED_COLS].reset_index(drop=True)

    print(f"  Sample: {len(sample):,} rows")
    print(f"  Gender distribution:\n{sample['gender'].value_counts().to_string()}")
    print(f"  ArticleTypes: {sample['articleType'].nunique()}")

    # Write CSV
    sample.to_csv(TARGET_CSV, index=False)
    print(f"\nCSV written: {TARGET_CSV} ({len(sample):,} rows)")

    # Copy images
    print(f"\nCopying images to {TARGET_IMAGES}...")
    os.makedirs(TARGET_IMAGES, exist_ok=True)
    copied, skipped = 0, 0
    for item_id in sample["id"]:
        src = os.path.join(SOURCE_IMAGES, f"{item_id}.jpg")
        dst = os.path.join(TARGET_IMAGES, f"{item_id}.jpg")
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            copied += 1
        else:
            skipped += 1
    print(f"  Copied: {copied}, already existed: {skipped}")

    # Invalidate embedding caches
    print("\nInvalidating embeddings cache...")
    for path in CACHE_FILES:
        if os.path.exists(path):
            os.remove(path)
            print(f"  Deleted: {path}")

    print("\n" + "=" * 60)
    print("CATALOG EXPANSION COMPLETE")
    print(f"  Rows:         {len(sample):,}")
    print(f"  ArticleTypes: {sample['articleType'].nunique()}")
    print(f"  Genders:      {sample['gender'].nunique()}")
    print(f"  Images:       {copied + skipped:,}")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. PYTHONPATH=. python scripts/generate_embeddings.py")
    print("  2. uvicorn backend.main:app --reload")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand GPToutfit catalog")
    parser.add_argument("--size", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(size=args.size, seed=args.seed)

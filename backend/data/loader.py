"""CSV catalog loader module.

Reads the clothing catalog CSV and provides structured data access.

See TASK-03 in docs/TASKS.md for implementation spec.
"""
import pandas as pd

REQUIRED_FIELDS = [
    "id",
    "productDisplayName",
    "gender",
    "articleType",
    "baseColour",
    "usage",
    "season",
]

USAGE_SYNONYMS = {
    "Formal":       "formal office business professional work job interview meeting corporate",
    "Casual":       "casual everyday relaxed weekend informal brunch daily",
    "Smart Casual": "smart casual business casual semi-formal smart",
    "Sports":       "sports athletic activewear gym workout running training outdoor",
    "Ethnic":       "ethnic traditional cultural festive wedding ceremony Diwali festival",
    "Party":        "party evening occasion going out nightout gala wedding celebration dinner",
    "Travel":       "travel comfortable journey trip vacation holiday",
    "Home":         "home loungewear comfortable indoor relaxed",
    "NA":           "",
}

SEASON_CONTEXT = {
    "Summer":   "summer hot weather lightweight breathable",
    "Winter":   "winter cold weather warm layering",
    "Fall":     "fall autumn transitional",
    "Spring":   "spring mild weather",
    "NA":       "",
}


def load_catalog(csv_path: str) -> list[dict]:
    """Load clothing catalog from CSV file.

    Args:
        csv_path: Path to the sample_styles.csv file.

    Returns:
        List of dicts, each representing a catalog item with keys:
        id, productDisplayName, gender, articleType, baseColour, usage, season.
    """
    df = pd.read_csv(csv_path)
    df = df.fillna("")

    for field in REQUIRED_FIELDS:
        if field not in df.columns:
            df[field] = ""

    return df.to_dict(orient="records")


def build_description(item: dict) -> str:
    """Build a rich natural-language description for embedding.

    Combines all CSV fields plus usage synonyms and season context
    to close the semantic gap with GPT-4o-mini query descriptions.
    """
    name = str(item.get("productDisplayName", "") or "").strip()
    article_type = str(item.get("articleType", "") or "").strip()
    base_colour = str(item.get("baseColour", "") or "").strip()
    gender = str(item.get("gender", "") or "").strip()
    usage = str(item.get("usage", "") or "").strip()
    season = str(item.get("season", "") or "").strip()
    sub_category = str(item.get("subCategory", "") or "").strip()
    master_category = str(item.get("masterCategory", "") or "").strip()

    usage_context = USAGE_SYNONYMS.get(usage, usage.lower())
    season_context = SEASON_CONTEXT.get(season, season.lower())

    description = (
        f"{name}. "
        f"A {usage.lower()} {gender.lower()}'s {article_type.lower()} "
        f"in {base_colour.lower()}, suitable for {season.lower()} season. "
        f"Category: {sub_category}, {master_category}. "
        f"Occasions: {usage_context}. "
        f"Season context: {season_context}."
    )

    return description.strip()

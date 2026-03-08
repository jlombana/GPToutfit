import pandas as pd

from backend.data.loader import build_description, load_catalog


def test_load_catalog_fills_nan(tmp_path) -> None:
    csv_path = tmp_path / "catalog.csv"
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "productDisplayName": "Navy Shirt",
                "gender": "Men",
                "articleType": "Shirts",
                "baseColour": "Navy",
                "usage": None,
                "season": None,
            }
        ]
    )
    df.to_csv(csv_path, index=False)

    rows = load_catalog(str(csv_path))
    assert len(rows) == 1
    assert rows[0]["usage"] == ""
    assert rows[0]["season"] == ""


def test_load_catalog_ensures_expected_fields(tmp_path) -> None:
    csv_path = tmp_path / "catalog.csv"
    pd.DataFrame([{"id": 1, "productDisplayName": "Only Name"}]).to_csv(csv_path, index=False)

    row = load_catalog(str(csv_path))[0]
    for key in ["id", "productDisplayName", "gender", "articleType", "baseColour", "usage", "season"]:
        assert key in row


def test_build_description_is_human_readable() -> None:
    item = {
        "productDisplayName": "Navy Shirt",
        "articleType": "Shirts",
        "baseColour": "Navy",
        "gender": "Men",
        "usage": "Casual",
        "season": "Summer",
    }
    description = build_description(item)
    assert "Navy Shirt" in description
    assert "shirts" in description.lower()
    assert "summer" in description.lower()

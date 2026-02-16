import csv
import json

from ceda_pipeline.data_sources import load_denue_rows, load_market_source, load_scian_rows


def test_load_market_source_from_csv_with_defaults(tmp_path):
    path = tmp_path / "markets.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["market_name", "address_raw", "state", "municipality", "lat", "lon"])
        writer.writeheader()
        writer.writerow(
            {
                "market_name": "Central Test",
                "address_raw": "Calle 1",
                "state": "CDMX",
                "municipality": "Iztapalapa",
                "lat": "19.5",
                "lon": "-99.1",
            }
        )

    rows = load_market_source(str(path))
    assert rows[0]["market_id"] == "ROW-1"
    assert rows[0]["source_page"] == 0


def test_load_denue_rows_filters_by_year_when_present(tmp_path):
    path = tmp_path / "denue.json"
    path.write_text(
        json.dumps(
            [
                {"id": "1", "name": "A", "address": "X", "lat": 1, "lon": 2, "scian": "461110", "year": 2021},
                {"id": "2", "name": "B", "address": "Y", "lat": 1, "lon": 2, "scian": "461110", "year": 2022},
            ]
        ),
        encoding="utf-8",
    )

    filtered = load_denue_rows(str(path), year=2022)
    assert [row["id"] for row in filtered] == ["2"]


def test_load_scian_rows_validates_required_fields(tmp_path):
    good = tmp_path / "scian.json"
    good.write_text(
        json.dumps([{"code": "46", "title": "Comercio", "level": 2, "parent_code": None}]),
        encoding="utf-8",
    )

    rows = load_scian_rows(str(good))
    assert rows[0]["code"] == "46"

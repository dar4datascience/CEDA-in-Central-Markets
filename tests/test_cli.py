import csv
import json

from ceda_pipeline import cli
from ceda_pipeline.cli import main


def _write_market_csv(path):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "market_id",
                "market_name",
                "address_raw",
                "state",
                "municipality",
                "source_page",
                "source_text",
                "lat",
                "lon",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "market_id": "m1",
                "market_name": "Central",
                "address_raw": "Calle 1",
                "state": "CDMX",
                "municipality": "Iztapalapa",
                "source_page": "1",
                "source_text": "row",
                "lat": "19.5",
                "lon": "-99.5",
            }
        )


def _write_denue_json(path):
    path.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "name": "Inside",
                    "address": "Addr",
                    "lat": 19.5,
                    "lon": -99.5,
                    "scian": "461110",
                    "year": 2022,
                }
            ]
        ),
        encoding="utf-8",
    )


def _write_scian_json(path):
    path.write_text(
        json.dumps(
            [
                {"code": "46", "title": "Comercio", "level": 2, "parent_code": None},
                {"code": "461", "title": "Menor", "level": 3, "parent_code": "46"},
                {"code": "461110", "title": "Abarrotes", "level": 6, "parent_code": "461"},
            ]
        ),
        encoding="utf-8",
    )


def test_cli_runs_with_bbox(tmp_path):
    market = tmp_path / "market.csv"
    denue = tmp_path / "denue.json"
    scian = tmp_path / "scian.json"
    output = tmp_path / "out.json"

    _write_market_csv(market)
    _write_denue_json(denue)
    _write_scian_json(scian)

    rc = main(
        [
            "--market-source",
            str(market),
            "--denue-source",
            str(denue),
            "--scian-source",
            str(scian),
            "--market-reference",
            "m1",
            "--year",
            "2022",
            "--bbox",
            "19.0,20.0,-100.0,-99.0",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["results"][0]["establishment_id"] == "1"


def test_cli_runs_with_radius_using_market_center(tmp_path):
    market = tmp_path / "market.csv"
    denue = tmp_path / "denue.json"
    scian = tmp_path / "scian.json"
    output = tmp_path / "out-radius.json"

    _write_market_csv(market)
    _write_denue_json(denue)
    _write_scian_json(scian)

    rc = main(
        [
            "--market-source",
            str(market),
            "--denue-source",
            str(denue),
            "--scian-source",
            str(scian),
            "--market-reference",
            "m1",
            "--year",
            "2022",
            "--radius-m",
            "50",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["input"]["geofence"]["type"] == "radius"


def test_cli_auto_downloads_market_and_scian_sources(tmp_path, monkeypatch):
    market = tmp_path / "market.csv"
    denue = tmp_path / "denue.json"
    scian = tmp_path / "scian.json"
    output = tmp_path / "out-auto.json"

    _write_market_csv(market)
    _write_denue_json(denue)
    _write_scian_json(scian)

    monkeypatch.setattr(cli, "download_central_markets_pdf", lambda destination_dir, force=False: str(market))
    monkeypatch.setattr(cli, "download_scian_source", lambda destination_dir, force=False: str(scian))

    rc = main(
        [
            "--denue-source",
            str(denue),
            "--market-reference",
            "m1",
            "--year",
            "2022",
            "--bbox",
            "19.0,20.0,-100.0,-99.0",
            "--data-dir",
            str(tmp_path / "cache"),
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["results"][0]["establishment_id"] == "1"

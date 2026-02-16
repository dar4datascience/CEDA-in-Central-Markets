import csv
import json

from openpyxl import Workbook

from ceda_pipeline import data_sources
from ceda_pipeline.data_sources import (
    download_central_markets_pdf,
    download_scian_source,
    load_denue_rows,
    load_market_source,
    load_scian_rows,
)


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


def test_download_central_markets_pdf_uses_cache(tmp_path, monkeypatch):
    target_path = tmp_path / "DirectorioNacionaldeCentralesdeAbasto.pdf"
    target_path.write_bytes(b"cached-pdf")

    called = {"value": False}

    def _fake_download_to_file(*, url, target_path, user_agent):  # noqa: ANN001
        called["value"] = True

    monkeypatch.setattr(data_sources, "_download_to_file", _fake_download_to_file)

    result = download_central_markets_pdf(str(tmp_path), force=False)
    assert result.endswith("DirectorioNacionaldeCentralesdeAbasto.pdf")
    assert not called["value"]


def test_download_scian_source_downloads_fixed_xlsx_url(tmp_path, monkeypatch):
    def _fake_download_to_file(*, url, target_path, user_agent):  # noqa: ANN001
        target_path.write_bytes(b"xlsx-bytes")

    monkeypatch.setattr(data_sources, "_download_to_file", _fake_download_to_file)

    resolved = download_scian_source(str(tmp_path), force=True)
    assert resolved.endswith("scian_2023_categorias_y_productos.xlsx")
    assert (tmp_path / "scian_source_manifest.json").exists()

    manifest = json.loads((tmp_path / "scian_source_manifest.json").read_text(encoding="utf-8"))
    assert manifest["download_url"] == data_sources.SCIAN_XLSX_URL


def test_load_scian_rows_from_xlsx_with_spanish_headers(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Código", "Categoría", "Nivel", "Código Padre"])
    sheet.append(["46", "Comercio", 2, None])
    sheet.append(["461110", "Abarrotes", 6, "46111"])

    path = tmp_path / "scian.xlsx"
    workbook.save(path)

    rows = load_scian_rows(str(path))
    assert rows[0]["code"] == "46"
    assert rows[0]["title"] == "Comercio"
    assert rows[1]["parent_code"] == "46111"

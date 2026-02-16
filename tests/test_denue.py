from ceda_pipeline.denue import build_raw_extract_metadata, normalize_denue_rows, resolve_denue_source


def test_resolve_denue_source_for_year():
    source = resolve_denue_source(2020, {2020: "https://example.com/denue-2020.csv"})
    assert source.endswith("denue-2020.csv")


def test_normalize_denue_rows_uses_aliases():
    rows = [
        {
            "denue_id": "abc",
            "nombre": "Tienda",
            "direccion": "Calle 1",
            "latitud": 19.4,
            "longitud": -99.1,
            "codigo_scian": "461110",
            "status": "ACTIVO",
        }
    ]

    normalized = normalize_denue_rows(rows, year=2021)
    assert normalized[0].establishment_id == "abc"
    assert normalized[0].year == 2021


def test_raw_extract_metadata_has_hash_and_year():
    meta = build_raw_extract_metadata(2022, "https://example.com", b"payload")
    assert meta["year"] == 2022
    assert len(meta["hash"]) == 64

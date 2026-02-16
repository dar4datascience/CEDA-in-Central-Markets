from ceda_pipeline.scian import load_scian_catalog, map_scian_codes


def test_load_scian_catalog_and_validate_hierarchy():
    catalog = load_scian_catalog(
        [
            {"code": "46", "title": "Comercio", "level": 2, "parent_code": None},
            {"code": "461", "title": "Comercio al por menor", "level": 3, "parent_code": "46"},
            {"code": "461110", "title": "Abarrotes", "level": 6, "parent_code": "461"},
        ],
        version="2023",
        version_date="2023-01-01",
    )

    mapped, unknown = map_scian_codes(["461110", "999999"], catalog)
    assert len(mapped) == 1
    assert unknown == ["999999"]


def test_load_scian_catalog_rejects_bad_code_format():
    try:
        load_scian_catalog(
            [{"code": "AA11", "title": "Bad", "level": 4, "parent_code": None}],
            version="2023",
            version_date="2023-01-01",
        )
    except ValueError as exc:
        assert "Invalid SCIAN code format" in str(exc)
    else:
        raise AssertionError("Expected invalid SCIAN format to fail")

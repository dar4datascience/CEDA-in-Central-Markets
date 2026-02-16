from ceda_pipeline.markets import parse_market_rows


def _sample_rows():
    return [
        {
            "market_id": "2",
            "market_name": "Central de Abasto B",
            "address_raw": "Av. Siempre Viva 456",
            "state": "Jalisco",
            "municipality": "Guadalajara",
            "source_page": 10,
            "source_text": "fragment-2",
        },
        {
            "market_id": "1",
            "market_name": "Central de Ábasto A",
            "address_raw": "  Calle Falsa 123  ",
            "state": "CDMX",
            "municipality": "Iztapalapa",
            "source_page": 9,
            "source_text": "fragment-1",
        },
    ]


def test_parse_market_rows_is_deterministic_and_normalized():
    parsed = parse_market_rows(_sample_rows())

    assert [row.market_id for row in parsed] == ["1", "2"]
    assert parsed[0].normalized_name == "CENTRAL DE ABASTO A"
    assert parsed[0].normalized_address == "CALLE FALSA 123"


def test_parse_market_rows_requires_expected_fields():
    bad = _sample_rows()[0].copy()
    bad.pop("source_page")

    try:
        parse_market_rows([bad])
    except ValueError as exc:
        assert "source_page" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing required field")

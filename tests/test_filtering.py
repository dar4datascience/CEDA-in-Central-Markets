from ceda_pipeline.filtering import filter_establishments, resolve_market_reference
from ceda_pipeline.models import DenueEstablishment, MarketRecord


def _markets():
    return [
        MarketRecord(
            market_id="m1",
            market_name="Central Uno",
            address_raw="Calle 1",
            state="State",
            municipality="Muni",
            source_page=1,
            source_text="src",
            normalized_name="CENTRAL UNO",
            normalized_address="CALLE 1",
        )
    ]


def test_resolve_market_reference_by_id_and_address():
    market = resolve_market_reference("m1", _markets())
    assert market.market_name == "Central Uno"

    market_by_address = resolve_market_reference("calle 1", _markets())
    assert market_by_address.market_id == "m1"


def test_filter_establishments_in_bbox():
    establishments = [
        DenueEstablishment("1", "A", "Addr", 19.5, -99.5, "461110", None, 2022),
        DenueEstablishment("2", "B", "Addr", 21.0, -99.5, "461110", None, 2022),
    ]
    geofence = {"type": "bbox", "min_lat": 19.0, "max_lat": 20.0, "min_lon": -100.0, "max_lon": -99.0}

    filtered = filter_establishments(establishments, geofence)
    assert [row.establishment_id for row in filtered] == ["1"]

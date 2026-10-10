from ceda_pipeline.geocode import (
    GeocodeLowConfidenceError,
    apply_geocoding,
    build_geofence,
    point_in_geofence,
)
from ceda_pipeline.models import MarketRecord


def _market():
    return MarketRecord(
        market_id="m1",
        market_name="Central",
        address_raw="Address",
        state="State",
        municipality="Municipality",
        source_page=1,
        source_text="src",
        normalized_name="CENTRAL",
        normalized_address="ADDRESS",
    )


def test_apply_geocoding_rejects_low_confidence_without_approval():
    try:
        apply_geocoding(_market(), {"lat": 19.0, "lon": -99.0, "confidence": 0.2}, min_confidence=0.8)
    except GeocodeLowConfidenceError:
        pass
    else:
        raise AssertionError("Expected GeocodeLowConfidenceError")


def test_apply_geocoding_allows_manual_approval():
    updated = apply_geocoding(
        _market(),
        {"lat": 19.0, "lon": -99.0, "confidence": 0.2},
        min_confidence=0.8,
        manual_approval=True,
    )

    assert updated.geocode_status == "approved"
    assert updated.lat == 19.0


def test_build_geofence_and_boundary_behavior():
    bbox = build_geofence({"type": "bbox", "min_lat": 19.0, "max_lat": 20.0, "min_lon": -100.0, "max_lon": -99.0})
    assert point_in_geofence(19.0, -99.5, bbox)

    polygon = build_geofence(
        {
            "type": "polygon",
            "coordinates": [(19.0, -100.0), (20.0, -100.0), (20.0, -99.0), (19.0, -99.0)],
        }
    )
    assert point_in_geofence(19.5, -99.5, polygon)
    assert not point_in_geofence(18.5, -99.5, polygon)
    # border points count as inside
    assert point_in_geofence(19.0, -99.5, polygon)
    assert point_in_geofence(19.0, -100.0, polygon)

    radius = {"type": "radius", "center": (19.0, -99.0), "radius_m": 0.0}
    assert point_in_geofence(19.0, -99.0, radius)

from __future__ import annotations

import math
from dataclasses import replace
from math import isclose

from .models import MarketRecord


class GeocodeLowConfidenceError(ValueError):
    pass


class GeocodeResult(dict):
    """Minimal mapping type: {'lat': float, 'lon': float, 'confidence': float}."""


def apply_geocoding(
    record: MarketRecord,
    result: GeocodeResult,
    *,
    min_confidence: float,
    manual_approval: bool = False,
) -> MarketRecord:
    confidence = float(result["confidence"])
    if confidence < min_confidence and not manual_approval:
        raise GeocodeLowConfidenceError(
            f"Geocode confidence {confidence:.3f} below threshold {min_confidence:.3f}"
        )

    return replace(
        record,
        lat=float(result["lat"]),
        lon=float(result["lon"]),
        geocode_confidence=confidence,
        geocode_status="approved" if manual_approval else "accepted",
    )


def build_geofence(geofence: dict[str, object]) -> dict[str, object]:
    kind = str(geofence.get("type", "")).lower()
    if kind == "radius":
        center = geofence["center"]
        radius_m = float(geofence["radius_m"])
        if radius_m <= 0:
            raise ValueError("radius_m must be positive")
        return {"type": "radius", "center": center, "radius_m": radius_m}

    if kind == "bbox":
        min_lat = float(geofence["min_lat"])
        max_lat = float(geofence["max_lat"])
        min_lon = float(geofence["min_lon"])
        max_lon = float(geofence["max_lon"])
        if min_lat > max_lat or min_lon > max_lon:
            raise ValueError("Invalid bbox bounds")
        return {
            "type": "bbox",
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
        }

    raise ValueError(f"Unsupported geofence type: {kind}")


def point_in_geofence(lat: float, lon: float, geofence: dict[str, object]) -> bool:
    """Deterministic border behavior: border points are considered inside."""
    if geofence["type"] == "bbox":
        return (
            geofence["min_lat"] <= lat <= geofence["max_lat"]
            and geofence["min_lon"] <= lon <= geofence["max_lon"]
        )

    if geofence["type"] == "radius":
        center_lat, center_lon = geofence["center"]
        dist = _distance_m(lat, lon, center_lat, center_lon)
        return dist < geofence["radius_m"] or isclose(dist, geofence["radius_m"], rel_tol=0.0, abs_tol=1e-6)

    raise ValueError(f"Unsupported geofence type: {geofence['type']}")


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Haversine distance in meters.
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    earth_radius_m = 6_371_000.0
    return earth_radius_m * c

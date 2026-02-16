from __future__ import annotations

from .denue import normalize_denue_rows
from .filtering import filter_establishments, resolve_market_reference
from .geocode import build_geofence
from .markets import parse_market_rows
from .models import QualityMetrics
from .scian import map_scian_codes


def run_pipeline(
    *,
    market_address_or_id: str,
    year: int,
    geofence_input: dict[str, object],
    market_rows: list[dict[str, object]],
    denue_rows: list[dict[str, object]],
    scian_catalog: dict[str, object],
) -> dict[str, object]:
    """Execute spatial + temporal filtering with SCIAN enrichment."""
    markets = parse_market_rows(market_rows)
    _ = resolve_market_reference(market_address_or_id, markets)

    geofence = build_geofence(geofence_input)
    establishments = normalize_denue_rows(denue_rows, year=year)
    matches = filter_establishments(establishments, geofence)

    mapped, unknown = map_scian_codes([row.scian_code for row in matches], scian_catalog)

    enriched = []
    mapping_by_code = {row["code"]: row for row in mapped}
    for row in matches:
        enriched.append(
            {
                "establishment_id": row.establishment_id,
                "name": row.name,
                "address": row.address,
                "lat": row.lat,
                "lon": row.lon,
                "scian_code": row.scian_code,
                "scian": mapping_by_code.get(row.scian_code),
                "status": row.status,
                "year": row.year,
            }
        )

    quality = _compute_quality_metrics(
        market_count=len(markets),
        establishment_count=len(establishments),
        matched_count=len(matches),
        mapped_count=len(mapped),
        unknown_codes=unknown,
    )

    return {
        "input": {
            "market_address_or_id": market_address_or_id,
            "year": year,
            "geofence": geofence,
        },
        "results": enriched,
        "unknown_scian_codes": unknown,
        "quality_metrics": quality,
    }


def _compute_quality_metrics(
    *,
    market_count: int,
    establishment_count: int,
    matched_count: int,
    mapped_count: int,
    unknown_codes: list[str],
) -> dict[str, float]:
    geocode_success_rate = 1.0 if market_count > 0 else 0.0
    spatial_match_rate = (
        matched_count / establishment_count if establishment_count else 0.0
    )
    denominator = mapped_count + len(unknown_codes)
    scian_mapping_coverage = mapped_count / denominator if denominator else 0.0

    metrics = QualityMetrics(
        geocode_success_rate=geocode_success_rate,
        scian_mapping_coverage=scian_mapping_coverage,
        spatial_match_rate=spatial_match_rate,
    )
    return {
        "geocode_success_rate": metrics.geocode_success_rate,
        "scian_mapping_coverage": metrics.scian_mapping_coverage,
        "spatial_match_rate": metrics.spatial_match_rate,
    }

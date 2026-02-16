from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .data_sources import (
    download_central_markets_pdf,
    download_scian_source,
    load_denue_rows,
    load_market_source,
    load_scian_rows,
)
from .filtering import resolve_market_reference
from .geocode import apply_geocoding
from .geocoding_service import NominatimGeocoder, load_geocode_cache, save_geocode_cache
from .markets import parse_market_rows
from .pipeline import run_pipeline
from .scian import load_scian_catalog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run DENUE central markets pipeline with real data files")
    parser.add_argument("--market-source", help="Optional path to central market source (CSV/JSON/PDF)")
    parser.add_argument("--denue-source", required=True, help="Path to DENUE rows file (CSV/JSON)")
    parser.add_argument("--scian-source", help="Optional path to SCIAN catalog file (CSV/JSON)")
    parser.add_argument("--market-reference", required=True, help="Market id or address")
    parser.add_argument("--year", required=True, type=int, help="Target year")
    parser.add_argument("--data-dir", default="data/sources", help="Local canonical source cache directory")
    parser.add_argument("--refresh-market-source", action="store_true", help="Force re-download of canonical central-markets PDF")
    parser.add_argument("--refresh-scian-source", action="store_true", help="Force re-download of canonical SCIAN source")

    geo_group = parser.add_mutually_exclusive_group(required=True)
    geo_group.add_argument("--bbox", help="min_lat,max_lat,min_lon,max_lon")
    geo_group.add_argument("--radius-m", type=float, help="Radius in meters around market center")

    parser.add_argument("--center", help="Optional center lat,lon for radius geofence")
    parser.add_argument("--geocode-if-missing", action="store_true", help="Geocode selected market when center is not provided")
    parser.add_argument("--geocode-threshold", type=float, default=0.7)
    parser.add_argument("--geocode-cache", help="Optional cache JSON path for geocoding results")
    parser.add_argument("--geocoder-user-agent", default="ceda-central-markets/0.1", help="User-Agent for Nominatim")
    parser.add_argument("--geocoder-email", help="Optional email for Nominatim")

    parser.add_argument("--scian-version", default="latest")
    parser.add_argument("--scian-version-date", default=str(date.today()))
    parser.add_argument("--output", help="Output JSON file path. Defaults to stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    market_source_path = args.market_source
    if not market_source_path:
        market_source_path = download_central_markets_pdf(
            destination_dir=str(Path(args.data_dir) / "central_markets"),
            force=args.refresh_market_source,
        )

    scian_source_path = args.scian_source
    if not scian_source_path:
        scian_source_path = download_scian_source(
            destination_dir=str(Path(args.data_dir) / "scian"),
            force=args.refresh_scian_source,
        )

    market_rows = load_market_source(market_source_path)
    market_records = parse_market_rows(market_rows)
    selected = resolve_market_reference(args.market_reference, market_records)

    geofence_input = _build_geofence_input(args=args, selected_market=selected)

    denue_rows = load_denue_rows(args.denue_source, year=args.year)
    scian_rows = load_scian_rows(scian_source_path)
    scian_catalog = load_scian_catalog(
        scian_rows,
        version=args.scian_version,
        version_date=args.scian_version_date,
    )

    result = run_pipeline(
        market_address_or_id=args.market_reference,
        year=args.year,
        geofence_input=geofence_input,
        market_rows=market_rows,
        denue_rows=denue_rows,
        scian_catalog=scian_catalog,
    )

    payload = json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


def _build_geofence_input(*, args: argparse.Namespace, selected_market: object) -> dict[str, object]:
    if args.bbox:
        min_lat, max_lat, min_lon, max_lon = [float(part.strip()) for part in args.bbox.split(",")]
        return {
            "type": "bbox",
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
        }

    if args.radius_m is None:
        raise ValueError("--radius-m is required when --bbox is not provided")

    center = None
    if args.center:
        lat, lon = [float(part.strip()) for part in args.center.split(",")]
        center = (lat, lon)

    market = selected_market
    if center is None:
        market_lat = getattr(market, "lat")
        market_lon = getattr(market, "lon")
        if market_lat is not None and market_lon is not None:
            center = (market_lat, market_lon)

    if center is None and args.geocode_if_missing:
        geocoder = NominatimGeocoder(user_agent=args.geocoder_user_agent, email=args.geocoder_email)
        cache = load_geocode_cache(args.geocode_cache)
        key = getattr(market, "address_raw")
        geocode_result = cache.get(key)
        if geocode_result is None:
            geocode_result = geocoder.geocode(key)
            cache[key] = geocode_result
            save_geocode_cache(args.geocode_cache, cache)

        updated = apply_geocoding(
            market,
            geocode_result,
            min_confidence=args.geocode_threshold,
            manual_approval=False,
        )
        center = (updated.lat, updated.lon)

    if center is None:
        raise ValueError(
            "Radius geofence needs a center. Provide --center, lat/lon in market source, or use --geocode-if-missing."
        )

    return {"type": "radius", "center": center, "radius_m": args.radius_m}


if __name__ == "__main__":
    raise SystemExit(main())

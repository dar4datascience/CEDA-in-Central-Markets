from __future__ import annotations

from .geocode import point_in_geofence
from .models import DenueEstablishment, MarketRecord
from .normalize import normalize_text


def resolve_market_reference(
    market_reference: str,
    markets: list[MarketRecord],
) -> MarketRecord:
    by_id = {m.market_id: m for m in markets}
    if market_reference in by_id:
        return by_id[market_reference]

    normalized_address = normalize_text(market_reference)
    for market in markets:
        if market.normalized_address == normalized_address:
            return market

    raise ValueError(f"Unknown market reference: {market_reference}")


def filter_establishments(
    establishments: list[DenueEstablishment],
    geofence: dict[str, object],
) -> list[DenueEstablishment]:
    return [
        est
        for est in establishments
        if point_in_geofence(est.lat, est.lon, geofence)
    ]

from __future__ import annotations

from dataclasses import asdict

from .models import MarketRecord
from .normalize import normalize_text


REQUIRED_MARKET_FIELDS = {
    "market_id",
    "market_name",
    "address_raw",
    "state",
    "municipality",
    "source_page",
    "source_text",
}


def parse_market_rows(rows: list[dict[str, object]]) -> list[MarketRecord]:
    """Build deterministic MarketRecord entries from extracted PDF rows."""
    parsed: list[MarketRecord] = []
    for row in rows:
        missing = REQUIRED_MARKET_FIELDS - row.keys()
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"Market row is missing required fields: {missing_list}")

        parsed.append(
            MarketRecord(
                market_id=str(row["market_id"]),
                market_name=str(row["market_name"]).strip(),
                address_raw=str(row["address_raw"]).strip(),
                state=str(row["state"]).strip(),
                municipality=str(row["municipality"]).strip(),
                source_page=int(row["source_page"]),
                source_text=str(row["source_text"]),
                normalized_name=normalize_text(str(row["market_name"])),
                normalized_address=normalize_text(str(row["address_raw"])),
                lat=float(row["lat"]) if row.get("lat") not in {None, ""} else None,
                lon=float(row["lon"]) if row.get("lon") not in {None, ""} else None,
                geocode_confidence=(
                    float(row["geocode_confidence"])
                    if row.get("geocode_confidence") not in {None, ""}
                    else None
                ),
                geocode_status=(
                    str(row["geocode_status"]).strip()
                    if row.get("geocode_status") not in {None, ""}
                    else None
                ),
            )
        )

    return sorted(parsed, key=lambda item: item.market_id)


def market_to_dict(record: MarketRecord) -> dict[str, object]:
    return asdict(record)

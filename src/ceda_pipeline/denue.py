from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from .models import DenueEstablishment


DENUE_SOURCE_BY_YEAR: dict[int, str] = {}

DENUE_FIELD_ALIASES = {
    "id": "establishment_id",
    "denue_id": "establishment_id",
    "establecimiento_id": "establishment_id",
    "nombre": "name",
    "name": "name",
    "direccion": "address",
    "address": "address",
    "latitud": "lat",
    "lat": "lat",
    "longitud": "lon",
    "lon": "lon",
    "codigo_scian": "scian_code",
    "scian": "scian_code",
    "status": "status",
}


def resolve_denue_source(year: int, source_by_year: dict[int, str] | None = None) -> str:
    sources = source_by_year or DENUE_SOURCE_BY_YEAR
    try:
        return sources[year]
    except KeyError as exc:
        raise ValueError(f"No DENUE source configured for year {year}") from exc


def build_raw_extract_metadata(year: int, source_url: str, payload: bytes) -> dict[str, str | int]:
    now = datetime.now(timezone.utc).isoformat()
    digest = sha256(payload).hexdigest()
    return {
        "source_url": source_url,
        "retrieval_timestamp": now,
        "year": year,
        "hash": digest,
    }


def normalize_denue_rows(rows: list[dict[str, object]], *, year: int) -> list[DenueEstablishment]:
    normalized: list[DenueEstablishment] = []

    for row in rows:
        renamed: dict[str, object] = {}
        for key, value in row.items():
            alias = DENUE_FIELD_ALIASES.get(key.lower())
            if alias:
                renamed[alias] = value

        required = {"establishment_id", "name", "address", "lat", "lon", "scian_code"}
        missing = required - renamed.keys()
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"DENUE row missing required normalized fields: {missing_list}")

        normalized.append(
            DenueEstablishment(
                establishment_id=str(renamed["establishment_id"]),
                name=str(renamed["name"]).strip(),
                address=str(renamed["address"]).strip(),
                lat=float(renamed["lat"]),
                lon=float(renamed["lon"]),
                scian_code=str(renamed["scian_code"]).strip(),
                status=str(renamed.get("status")) if renamed.get("status") is not None else None,
                year=year,
            )
        )

    return normalized

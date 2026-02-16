from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketRecord:
    market_id: str
    market_name: str
    address_raw: str
    state: str
    municipality: str
    source_page: int
    source_text: str
    normalized_name: str
    normalized_address: str
    lat: float | None = None
    lon: float | None = None
    geocode_confidence: float | None = None
    geocode_status: str | None = None


@dataclass(frozen=True)
class DenueEstablishment:
    establishment_id: str
    name: str
    address: str
    lat: float
    lon: float
    scian_code: str
    status: str | None
    year: int


@dataclass(frozen=True)
class ScianCatalogEntry:
    code: str
    title: str
    level: int
    parent_code: str | None
    version: str
    version_date: str


@dataclass(frozen=True)
class QualityMetrics:
    geocode_success_rate: float
    scian_mapping_coverage: float
    spatial_match_rate: float

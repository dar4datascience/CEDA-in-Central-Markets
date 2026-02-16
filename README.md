# CEDA-in-Central-Markets

Python pipeline for resolving DENUE establishments around a central market with an explicit `(market_address_or_id, year, geofence)` contract.

## Canonical sources

1. DENUE (INEGI): https://www.inegi.org.mx/temas/directorio/#informacion_general
2. Directorio Nacional de Centrales de Abasto (PDF):
   http://www.protlcuem.gob.mx/work/models/Prologyca/Resource/2/1/images/DirectorioNacionaldeCentralesdeAbasto.pdf
3. Latest SCIAN (INEGI): https://www.inegi.org.mx/scian/

## Repository layout

- `src/ceda_pipeline/markets.py`: central market parsing and normalization with provenance fields.
- `src/ceda_pipeline/geocode.py`: geocoding acceptance rules and geofence behavior.
- `src/ceda_pipeline/denue.py`: year-aware DENUE source resolution + schema normalization.
- `src/ceda_pipeline/filtering.py`: spatial/temporal filtering helpers.
- `src/ceda_pipeline/scian.py`: SCIAN catalog load, hierarchy validation, and code mapping.
- `src/ceda_pipeline/pipeline.py`: orchestration entrypoint (`run_pipeline`).
- `tests/`: unit and regression tests for each pipeline step.

## Input/output contract

`run_pipeline(...)` expects:

- `market_address_or_id`
- `year`
- `geofence_input` (`bbox` or `radius`)
- normalized/extracted input rows for markets, DENUE, and SCIAN catalog

Returns:

- deterministic `results`
- unresolved `unknown_scian_codes`
- `quality_metrics`:
  - `geocode_success_rate`
  - `scian_mapping_coverage`
  - `spatial_match_rate`

## Determinism and quality gates

- No silent fallback in core filtering and normalization.
- Geofence border points are treated as inside.
- Low-confidence geocoding is rejected unless manually approved.
- Required test suites are included for parser, geospatial logic, year resolution/schema normalization, SCIAN mapping, and longitudinal regression.

## Reproducibility

- Python package metadata and test config are pinned in `pyproject.toml`.
- Run metadata helper captures immutable DENUE retrieval metadata (`source_url`, `retrieval_timestamp`, `year`, `hash`).
- SCIAN version + version date must be provided on catalog load and preserved through mapping outputs.

## Development

```bash
python -m pip install -e .[dev]
pytest -q
```

## Running with real data

The repository now includes a CLI entrypoint:

```bash
ceda-pipeline \
  --denue-source data/denue_2022.csv \
  --market-reference MKT-001 \
  --year 2022 \
  --bbox 19.0,20.0,-100.0,-99.0 \
  --output outputs/market_2022.json
```

When `--market-source` is omitted, the CLI automatically downloads and caches the canonical central-markets PDF from:

- `http://www.protlcuem.gob.mx/work/models/Prologyca/Resource/2/1/images/DirectorioNacionaldeCentralesdeAbasto.pdf`

When `--scian-source` is omitted, the CLI discovers and downloads the latest downloadable SCIAN file from:

- `https://www.inegi.org.mx/scian/`

By default, downloaded canonical sources are stored under `data/sources/` and reused on future runs.

Force fresh downloads with:

- `--refresh-market-source`
- `--refresh-scian-source`

Radius geofence mode can reuse market coordinates from your market source:

```bash
ceda-pipeline \
  --market-source data/central_markets.csv \
  --denue-source data/denue_2022.csv \
  --scian-source data/scian_latest.csv \
  --market-reference MKT-001 \
  --year 2022 \
  --radius-m 1500 \
  --output outputs/market_2022_radius.json
```

If your market source does not include `lat`/`lon`, enable geocoding:

```bash
ceda-pipeline \
  --market-source data/central_markets.csv \
  --denue-source data/denue_2022.csv \
  --scian-source data/scian_latest.csv \
  --market-reference "CENTRAL DE ABASTO ..." \
  --year 2022 \
  --radius-m 1500 \
  --geocode-if-missing \
  --geocode-cache .cache/geocode.json
```

### Expected file schemas

- Market source (`CSV/JSON`, preferred):
  - required: `market_id`, `market_name`, `address_raw`, `state`, `municipality`, `source_page`, `source_text`
  - optional: `lat`, `lon`, `geocode_confidence`, `geocode_status`
- DENUE source (`CSV/JSON`): aliases are accepted (`id`/`denue_id`, `name`/`nombre`, `address`/`direccion`, `lat`/`latitud`, `lon`/`longitud`, `scian`/`codigo_scian`)
- SCIAN source (`CSV/JSON`): `code`, `title`, `level`, `parent_code`

### PDF caveat

`--market-source` accepts PDF via `pypdf` text extraction, but table structure in the central-markets PDF may vary. If extraction is noisy, export/curate the parsed rows to CSV and use CSV as the canonical market input.

### External service note

`--geocode-if-missing` uses OpenStreetMap Nominatim. Respect their usage policy and provide a descriptive `--geocoder-user-agent` (and optionally `--geocoder-email`).
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


def load_market_source(path: str) -> list[dict[str, object]]:
    source_path = Path(path)
    suffix = source_path.suffix.lower()

    if suffix == ".pdf":
        return extract_market_rows_from_pdf(source_path)

    rows = _load_structured_rows(source_path)
    normalized_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        normalized_rows.append(
            {
                "market_id": row.get("market_id") or f"ROW-{index}",
                "market_name": row.get("market_name") or row.get("name") or "",
                "address_raw": row.get("address_raw") or row.get("address") or "",
                "state": row.get("state") or "",
                "municipality": row.get("municipality") or "",
                "source_page": int(row.get("source_page", 0) or 0),
                "source_text": row.get("source_text") or "",
                "lat": row.get("lat"),
                "lon": row.get("lon"),
                "geocode_confidence": row.get("geocode_confidence"),
                "geocode_status": row.get("geocode_status"),
            }
        )

    return normalized_rows


def load_denue_rows(path: str, *, year: int) -> list[dict[str, object]]:
    rows = _load_structured_rows(Path(path))
    filtered: list[dict[str, object]] = []
    for row in rows:
        row_year = row.get("year")
        if row_year in {None, ""}:
            filtered.append(row)
            continue

        if int(row_year) == year:
            filtered.append(row)

    return filtered


def load_scian_rows(path: str) -> list[dict[str, object]]:
    rows = _load_structured_rows(Path(path))
    expected = {"code", "title", "level", "parent_code"}
    normalized: list[dict[str, object]] = []
    for row in rows:
        missing = {field for field in expected if field not in row}
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"SCIAN row missing required fields: {missing_list}")
        normalized.append(row)

    return normalized


def extract_market_rows_from_pdf(path: Path) -> list[dict[str, object]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError("pypdf is required for PDF ingestion. Install dependencies first.") from exc

    reader = PdfReader(str(path))
    results: list[dict[str, object]] = []
    row_index = 0
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for line in text.splitlines():
            compact = re.sub(r"\s+", " ", line).strip()
            if not compact:
                continue

            parts = _split_market_line(compact)
            if len(parts) < 4:
                continue

            row_index += 1
            state, municipality, market_name = parts[0], parts[1], parts[2]
            address = " ".join(parts[3:])
            results.append(
                {
                    "market_id": f"PDF-{page_number}-{row_index}",
                    "market_name": market_name,
                    "address_raw": address,
                    "state": state,
                    "municipality": municipality,
                    "source_page": page_number,
                    "source_text": compact,
                }
            )

    if not results:
        raise ValueError(
            "No market rows were extracted from PDF. Provide a cleaned CSV/JSON extract or adjust parser heuristics."
        )

    return results


def _split_market_line(line: str) -> list[str]:
    for delimiter in ("|", ";", "\t"):
        if delimiter in line:
            return [piece.strip() for piece in line.split(delimiter) if piece.strip()]

    return [piece.strip() for piece in re.split(r"\s{2,}", line) if piece.strip()]


def _load_structured_rows(path: Path) -> list[dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        raise ValueError("Expected JSON array of objects")

    raise ValueError(f"Unsupported file format: {suffix}. Use CSV, JSON, or PDF for market source.")

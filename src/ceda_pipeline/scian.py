from __future__ import annotations

import re

from .models import ScianCatalogEntry


def load_scian_catalog(rows: list[dict[str, object]], *, version: str, version_date: str) -> dict[str, ScianCatalogEntry]:
    catalog: dict[str, ScianCatalogEntry] = {}
    for row in rows:
        code = str(row["code"]).strip()
        valid = code.isdigit() and len(code) in {2, 3, 4, 5, 6}
        if not valid and not re.fullmatch(r"\d{2}-\d{2}", code):
            raise ValueError(f"Invalid SCIAN code format: {code}")

        parent_code = str(row["parent_code"]).strip() if row.get("parent_code") else None
        catalog[code] = ScianCatalogEntry(
            code=code,
            title=str(row["title"]).strip(),
            level=int(row["level"]),
            parent_code=parent_code,
            version=version,
            version_date=version_date,
        )

    _validate_hierarchy(catalog)
    return catalog


def map_scian_codes(
    scian_codes: list[str],
    catalog: dict[str, ScianCatalogEntry],
) -> tuple[list[dict[str, object]], list[str]]:
    mapped: list[dict[str, object]] = []
    unknown: list[str] = []

    for code in scian_codes:
        entry = catalog.get(code)
        if entry is None:
            unknown.append(code)
            continue

        mapped.append(
            {
                "code": entry.code,
                "title": entry.title,
                "level": entry.level,
                "parent_code": entry.parent_code,
                "version": entry.version,
                "version_date": entry.version_date,
            }
        )

    return mapped, unknown


def _validate_hierarchy(catalog: dict[str, ScianCatalogEntry]) -> None:
    for code, entry in catalog.items():
        if entry.parent_code and entry.parent_code not in catalog:
            raise ValueError(f"Missing parent SCIAN code {entry.parent_code} for {code}")

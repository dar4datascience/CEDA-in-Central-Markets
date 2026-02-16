from __future__ import annotations

import re
import unicodedata


_whitespace_re = re.compile(r"\s+")


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(value: str, *, uppercase: bool = True) -> str:
    value = strip_accents(value.strip())
    value = _whitespace_re.sub(" ", value)
    return value.upper() if uppercase else value.lower()

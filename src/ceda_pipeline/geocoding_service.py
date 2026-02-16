from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class NominatimGeocoder:
    def __init__(self, *, user_agent: str, email: str | None = None, timeout_s: float = 10.0) -> None:
        self.user_agent = user_agent
        self.email = email
        self.timeout_s = timeout_s

    def geocode(self, address: str) -> dict[str, float | str]:
        params = {"q": address, "format": "json", "limit": 1}
        if self.email:
            params["email"] = self.email

        url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=self.timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not payload:
            raise ValueError(f"No geocoding candidate found for address: {address}")

        top = payload[0]
        importance = float(top.get("importance", 0.5))
        confidence = min(max(importance, 0.0), 1.0)
        return {
            "lat": float(top["lat"]),
            "lon": float(top["lon"]),
            "confidence": confidence,
            "display_name": str(top.get("display_name", "")),
        }


def load_geocode_cache(path: str | None) -> dict[str, dict[str, float | str]]:
    if not path:
        return {}

    cache_path = Path(path)
    if not cache_path.exists():
        return {}

    with cache_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return dict(raw)


def save_geocode_cache(path: str | None, cache: dict[str, dict[str, float | str]]) -> None:
    if not path:
        return

    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=True, indent=2, sort_keys=True)

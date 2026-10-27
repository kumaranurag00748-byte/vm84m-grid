from __future__ import annotations

import time
from typing import Any

import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


class ElexonError(RuntimeError):
    pass


class ElexonClient:
    def __init__(self, timeout_seconds: float = 20, cache_seconds: int = 300) -> None:
        self.timeout_seconds = timeout_seconds
        self.cache_seconds = cache_seconds
        self._cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    def _get(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        cache_key = f"{path}?{sorted(params.items())}"
        cached = self._cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < self.cache_seconds:
            return cached[1]
        try:
            response = requests.get(f"{BASE_URL}{path}", params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise ElexonError(f"Elexon request failed: {exc}") from exc
        except ValueError as exc:
            raise ElexonError("Elexon returned invalid JSON") from exc
        if not isinstance(payload, list):
            raise ElexonError("Elexon returned an unexpected response shape")
        records = [item for item in payload if isinstance(item, dict)]
        self._cache[cache_key] = (time.monotonic(), records)
        return records

    def actuals(self) -> list[dict[str, Any]]:
        return self._get(
            "/datasets/FUELHH/stream",
            {"settlementDateFrom": "2026-01-01", "settlementDateTo": "2026-01-31", "fuelType": "WIND"},
        )

    def forecasts(self) -> list[dict[str, Any]]:
        return self._get(
            "/datasets/WINDFOR/stream",
            {"publishDateTimeFrom": "2025-12-30T00:00:00Z", "publishDateTimeTo": "2026-02-01T00:00:00Z"},
        )

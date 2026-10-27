from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite, sqrt
from typing import Any


JANUARY_START = date(2026, 1, 1)
JANUARY_END = date(2026, 1, 31)
FORECAST_LOOKBACK_START = datetime(2025, 12, 30, tzinfo=timezone.utc)
FORECAST_LOOKAHEAD_END = datetime(2026, 2, 1, tzinfo=timezone.utc)


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def interval_key(value: str | datetime) -> str:
    timestamp = parse_timestamp(value) if isinstance(value, str) else value
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def hour_key(value: str | datetime) -> str:
    timestamp = parse_timestamp(value) if isinstance(value, str) else value
    hourly = timestamp.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return hourly.isoformat().replace("+00:00", "Z")


def decision_cutoff(delivery_start: datetime) -> datetime:
    delivery_day = delivery_start.astimezone(timezone.utc).date()
    return datetime.combine(delivery_day - timedelta(days=1), time(23, 59, 59), tzinfo=timezone.utc)


@dataclass(frozen=True)
class MatchedInterval:
    start_time: str
    forecast: float
    actual: float
    forecast_publish_time: str
    error: float
    absolute_error: float
    percentage_error: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "startTime": self.start_time,
            "forecast": self.forecast,
            "actual": self.actual,
            "forecastPublishTime": self.forecast_publish_time,
            "error": round(self.error, 2),
            "absoluteError": round(self.absolute_error, 2),
            "percentageError": round(self.percentage_error, 2) if self.percentage_error is not None else None,
        }


def select_latest_forecasts(
    forecasts: list[dict[str, Any]],
    start_date: date = JANUARY_START,
    end_date: date = JANUARY_END,
) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for item in forecasts:
        try:
            delivery = parse_timestamp(str(item["startTime"]))
            published = parse_timestamp(str(item["publishTime"]))
            generation = float(item["generation"])
        except (KeyError, TypeError, ValueError):
            continue
        if (
            not isfinite(generation)
            or not start_date <= delivery.date() <= end_date
            or published > decision_cutoff(delivery)
        ):
            continue
        key = interval_key(delivery)
        current = selected.get(key)
        if current is None or published > parse_timestamp(str(current["publishTime"])):
            selected[key] = {
                "startTime": key,
                "publishTime": published.isoformat().replace("+00:00", "Z"),
                "generation": generation,
            }
    return [selected[key] for key in sorted(selected)]


def match_intervals(
    actuals: list[dict[str, Any]],
    forecasts: list[dict[str, Any]],
) -> list[MatchedInterval]:
    actual_values_by_hour: dict[str, list[float]] = {}
    for item in actuals:
        try:
            key = hour_key(str(item["startTime"]))
            generation = float(item["generation"])
            if not isfinite(generation):
                continue
            actual_values_by_hour.setdefault(key, []).append(generation)
        except (KeyError, TypeError, ValueError):
            continue

    actual_by_hour = {
        key: sum(values) / len(values) for key, values in actual_values_by_hour.items()
    }
    matches: list[MatchedInterval] = []
    for forecast in select_latest_forecasts(forecasts):
        start_time = str(forecast["startTime"])
        actual = actual_by_hour.get(hour_key(start_time))
        if actual is None:
            continue
        forecast_value = float(forecast["generation"])
        if not isfinite(forecast_value):
            continue
        error = forecast_value - actual
        matches.append(
            MatchedInterval(
                start_time=start_time,
                forecast=forecast_value,
                actual=actual,
                forecast_publish_time=str(forecast["publishTime"]),
                error=error,
                absolute_error=abs(error),
                percentage_error=(abs(error) / abs(actual) * 100) if actual else None,
            )
        )
    return matches


def calculate_metrics(matches: list[MatchedInterval]) -> dict[str, float | int | None]:
    if not matches:
        return {"matchedIntervals": 0, "mae": None, "rmse": None, "bias": None, "meanAbsolutePercentageError": None}
    errors = [item.error for item in matches]
    absolute_errors = [abs(error) for error in errors]
    percentage_errors = [item.percentage_error for item in matches if item.percentage_error is not None]
    return {
        "matchedIntervals": len(matches),
        "mae": round(sum(absolute_errors) / len(absolute_errors), 2),
        "rmse": round(sqrt(sum(error * error for error in errors) / len(errors)), 2),
        "bias": round(sum(errors) / len(errors), 2),
        "meanAbsolutePercentageError": round(sum(percentage_errors) / len(percentage_errors), 2)
        if percentage_errors
        else None,
    }

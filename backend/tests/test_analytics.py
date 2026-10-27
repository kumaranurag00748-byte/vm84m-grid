from datetime import datetime, timezone

from app.analytics import calculate_metrics, match_intervals, select_latest_forecasts


def test_selects_latest_forecast_before_day_ahead_cutoff():
    forecasts = [
        {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2025-12-31T09:00:00Z", "generation": 90},
        {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": 110},
        {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-02T00:00:00Z", "generation": 999},
    ]
    selected = select_latest_forecasts(forecasts)
    assert selected[0]["generation"] == 110


def test_matches_and_calculates_metrics():
    forecasts = [{"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": 110}]
    actuals = [
        {"startTime": "2026-01-02T00:00:00+00:00", "generation": 100},
        {"startTime": "2026-01-02T00:30:00+00:00", "generation": 120},
    ]
    matches = match_intervals(actuals, forecasts)
    assert matches[0].actual == 110
    assert matches[0].error == 0
    assert calculate_metrics(matches) == {
        "matchedIntervals": 1,
        "mae": 0.0,
        "rmse": 0.0,
        "bias": 0.0,
        "meanAbsolutePercentageError": 0.0,
    }


def test_empty_and_zero_actual_are_safe():
    assert calculate_metrics([])["matchedIntervals"] == 0
    forecasts = [{"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": 1}]
    actuals = [{"startTime": "2026-01-02T00:00:00Z", "generation": 0}]
    assert match_intervals(actuals, forecasts)[0].percentage_error is None


def test_ignores_non_finite_upstream_values():
    forecasts = [
        {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": "NaN"},
        {"startTime": "2026-01-02T01:00:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": 100},
    ]
    actuals = [
        {"startTime": "2026-01-02T00:00:00Z", "generation": 100},
        {"startTime": "2026-01-02T01:00:00Z", "generation": 100},
    ]
    assert len(match_intervals(actuals, forecasts)) == 1

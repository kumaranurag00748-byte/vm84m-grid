from fastapi.testclient import TestClient

from app.main import app, client


def test_dashboard_returns_metrics_and_provenance(monkeypatch):
    monkeypatch.setattr(
        client,
        "actuals",
        lambda: [{"startTime": "2026-01-02T00:00:00Z", "generation": 100}],
    )
    monkeypatch.setattr(
        client,
        "forecasts",
        lambda: [{"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": 110}],
    )
    response = TestClient(app).get("/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["mae"] == 10
    assert payload["metadata"]["forecastDataset"] == "WINDFOR"
    assert payload["metadata"]["analysisResolution"].startswith("Hourly")

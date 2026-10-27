from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analytics import calculate_metrics, match_intervals
from .elexon import ElexonClient, ElexonError

app = FastAPI(title="Wind Procurement Insight API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
client = ElexonClient()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    try:
        actuals = client.actuals()
        forecasts = client.forecasts()
        matches = match_intervals(actuals, forecasts)
    except ElexonError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "metrics": calculate_metrics(matches),
        "data": [item.as_dict() for item in matches],
        "metadata": {
            "actualDataset": "FUELHH",
            "forecastDataset": "WINDFOR",
            "fuelType": "WIND",
            "deliveryWindow": "2026-01-01 to 2026-01-31",
            "selectionRule": "Latest forecast published by 23:59:59 UTC on the day before delivery",
            "analysisResolution": "Hourly; half-hourly FUELHH actuals are averaged to align with WINDFOR",
            "actualRecords": len(actuals),
            "forecastRecords": len(forecasts),
        },
    }

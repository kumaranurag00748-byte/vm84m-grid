# Grid / Signal

Grid / Signal is a local-ready prototype for UK day-ahead wind procurement decisions. It compares the latest wind generation forecast available before a delivery day with Elexon BMRS actual wind generation for January 2026.

## Product view

The dashboard provides:

- Mean absolute error (MAE), root mean squared error (RMSE), forecast bias, and matched interval coverage.
- A 30-minute actual-versus-forecast chart with a delivery-day filter.
- A ranked list of the largest forecast misses to support procurement review.
- Data provenance and the exact forecast selection rule used by the analysis.

For each January delivery interval, the app selects the latest `WINDFOR` record published by `23:59:59 UTC` on the preceding day. Actuals come from `FUELHH` with `fuelType=WIND`. The forecast request deliberately spans 2025-12-30 through 2026-02-01 so the edge days are available. The live WINDFOR response is hourly while FUELHH is half-hourly, so the two half-hourly actual values are averaged into an hourly actual before comparison. This avoids comparing an hourly forecast to only one half-hour of actual generation.

## Run locally

### Python backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`, with interactive OpenAPI documentation at `/docs`.

### React frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Set `VITE_API_URL` when the backend is not running at `http://localhost:8000`.

### Docker

```powershell
docker compose up --build
```

The frontend is served at `http://localhost:5173` and the API at `http://localhost:8000`.

## Tests and validation

```powershell
cd backend
pytest
cd ..\frontend
npm run build
```

The backend tests cover day-ahead cutoff selection, timestamp normalization, joining, metrics, and zero-safe percentage errors. The app uses the public Elexon BMRS API and does not require an API key.

## Repository layout

```text
backend/
  app/analytics.py  # cutoff selection, joining, and accuracy metrics
  app/elexon.py     # validated HTTP client and short-lived cache
  app/main.py       # FastAPI routes and response shape
  tests/             # analytics unit tests
frontend/
  src/App.jsx       # dashboard and interaction state
  src/styles.css    # responsive visual system
docker-compose.yml
```

## Design notes

The backend owns all data access and analytical rules so that the browser never makes a direct third-party API request. Requests have explicit timeouts, HTTP/JSON validation, and a five-minute in-memory cache. A failed upstream request returns a visible `502` error to the UI rather than silently showing stale or empty data.

This prototype was developed with AI assistance (GitHub Copilot SDK in VS Code) for scaffolding and implementation review. All analytical assumptions and code paths were manually checked against the Elexon endpoint requirements.

## Deployment

The project is containerized and can be deployed to any service supporting Docker. For a hosted split deployment, set `VITE_API_URL` at frontend build time to the public backend URL and restrict backend CORS to the deployed frontend origin. Provider credentials and a public repository are intentionally not included in this local-ready project.

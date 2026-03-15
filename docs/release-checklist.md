# Technical release checklist

## Already in place
- **API:** FastAPI v1 routes are explicit about request/response contracts, include health/pipeline/insights/models/explanations, and rely on typed Pydantic schemas. Logging honors `LOG_LEVEL` and `ENV=production` by default.
- **Dashboard:** Streamlit UI runs as a thin API client with hardened loading/error states, clear empty messaging, and workflow-driven sections backed by config that points to the Compose API.
- **Docker/Compose:** Both API and dashboard images build with all runtime deps, expose their ports, and restart with `unless-stopped`; Compose maps 8000/8501 and uses headless Streamlit defaults.
- **CI:** GitHub Actions workflow runs `ruff`, `black`, `pytest`, builds both containers, and performs a Compose smoke test hitting `/health`.
- **Config/env:** `.env.example` documents production defaults (`ENV`, `DEBUG`, `LOG_LEVEL`, `API_V1_PREFIX`) and Compose surfaces them to containers.

## Should verify before real deployment
- Confirm `.env` values match the target environment (API host/port, dashboard API base URL, logging level) and secrets live outside the repo.
- Exercise the Compose smoke check (`docker compose up --build`, `curl /health`, `docker compose down`) on the deployment host to ensure networking and volumes are sane.
- Ensure data artifacts (raw/processed/features/models/insights/llm folders) are persisted or backed up if required by the chosen storage strategy.

## Future improvements
- Add structured observability (request tracing, dashboards, metrics) once a real deployment surface is defined.
- Introduce real CI deployment staging and multi-env configuration (e.g., environment-specific overrides, secret management) to replace the current `.env` defaults.
- Harden data ingestion (scheduling/retries) and pipeline orchestration beyond the local Compose runner when scaling past a single machine.

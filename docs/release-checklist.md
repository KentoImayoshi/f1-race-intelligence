# Technical release checklist

## Already done
- **API:** FastAPI app with typed routes, health/pipeline/insights endpoints, Pydantic schemas, and logging honoring `LOG_LEVEL`/`ENV`.
- **Dashboard:** Streamlit UI acts as a thin client to the API, has defensive loading/error states, and shares configuration via Compose.
- **Docker/Compose:** API and dashboard buildable images, exposed ports (8000/8501), restart policies, and Compose wiring of shared env vars and volumes.
- **CI:** GitHub Actions run linting (`ruff`, `black`), `pytest`, container builds, and a Compose smoke test hitting the API health endpoint.
- **Config/env:** `.env.example` documents production defaults and Compose injects those values; runtime honors overrides for host, port, and logging.

## Should do before real deployment
- Verify the environment-specific `.env` (host/port, API base URL, secrets) is stored outside the repo and matches the deployment network.
- Run `docker compose up --build`, hit `/health` from the target host, then `docker compose down` to confirm container networking/volumes perform as expected.
- Confirm persistence/backups for the `data/` folders the pipeline relies on (raw, processed, features, insights) before traffic arrives.

## Current known limitations
- Data ingestion is local only; there is no scheduler, retries, or remote storage configured yet.
- Observability is limited to basic logging—no metrics, tracing, or alerting that would be needed in production.
- No multi-environment CI/CD path exists; the current workflow stops after smoke tests without deployment steps.

## Future improvements
- Add structured observability (metrics, tracing, dashboards) once a deployment surface is chosen.
- Implement environment-aware config overrides/secret stores and explicit staging vs. production gates.
- Harden ingestion/analysis orchestration beyond Compose, e.g., scheduled jobs or lightweight workflow runners.

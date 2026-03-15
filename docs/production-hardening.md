# Production hardening notes

This project is intentionally simple, but these small defaults make the current stack easier to treat like a production-friendly service.

## Environment defaults

The API service now exposes and honors these variables by default (see `.env.example` for reference):

- `ENV=production` (tier identifier used in logging/config)
- `DEBUG=false` (keep FastAPI in non-reload, non-debug mode)
- `LOG_LEVEL=INFO` (drives `f1_core.logging.configure_logging`)
- `API_V1_PREFIX=/api/v1` (keeps the versioned contract stable)

The dashboard already relies on `F1_API_BASE_URL`, `F1_API_PREFIX`, and Streamlit driver variables; the Compose setup now defaults to `STREAMLIT_SERVER_HEADLESS=1` and a pinned port so the container behaves predictably.

## Runtime considerations

- Both services restart with `restart: unless-stopped` so simple failures recover locally.
- The API runs via `uvicorn` binding `0.0.0.0:8000`; the dashboard binds `Streamlit` to `8501` with headless mode on.
- Use `docker compose -f docker-compose.yml up --build` to exercise the stack and `docker compose down` when you are finished.

Keeping these defaults in place keeps the stack deterministic for production-like runs without introducing any extra infrastructure.

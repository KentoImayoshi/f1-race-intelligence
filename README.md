# F1 Race Intelligence AI Monorepo

This repo is a Python monorepo with modular packages and apps. It focuses on a minimal, typed foundation that is easy to evolve.

## Bootstrap (local dev)

```bash
bash scripts/bootstrap_dev.sh
```

## Run API

```bash
uvicorn f1_api.main:app --reload
```

## Run Dashboard

```bash
streamlit run apps/dashboard/src/f1_dashboard/app.py
```

## Run with Docker Compose

The minimal `docker compose up --build` workflow starts both the API (port 8000) and the Streamlit dashboard (port 8501) together. The compose manifest lives at the repository root and points at the Dockerfiles under `infra/docker`. The dashboard service has `F1_API_BASE_URL` set to `http://api:8000` so it can reach the API via the internal compose network.

```bash
docker compose up --build
```

The API container exposes a `HEALTHCHECK` that polls `GET /ready` so orchestrators wait for storage readiness before traffic is routed, and Docker Compose reuses the same probe when bootstrapping the stack.

## Run Tests

```bash
.venv/bin/pytest
```

## Run Ingestion (raw)

```bash
.venv/bin/python -m f1_ingestion.cli --output-dir data/raw
```

Expected artifact:

- `data/raw/raw_session_results.parquet`

### Test Conventions

- Unit tests live in `tests/unit/` and are marked with `@pytest.mark.unit`.
- Integration tests live in `tests/integration/` and are marked with `@pytest.mark.integration`.

### Run Test Subsets

```bash
.venv/bin/pytest -m unit
```

```bash
.venv/bin/pytest -m integration
```

### HTTP Integration Tests

HTTP-style integration tests are skipped by default in this environment.
To run them explicitly:

```bash
RUN_HTTP_INTEGRATION=1 .venv/bin/pytest -m integration
```

### Health and readiness

The API exposes two lightweight endpoints:

- `GET /health`: reports whether the service is running (returns `{"status": "ok"}`).
- `GET /ready`: ensures the expected `data/` subdirectories can be created and returns their paths so orchestrators can confirm storage readiness before routing traffic.

### FastF1 Integration Test (opt-in)

The real FastF1 ingestion test is skipped by default. To run it explicitly:

```bash
RUN_FASTF1_INTEGRATION=1 .venv/bin/pytest -m integration -k fastf1_real
```

Recommended real-data parameters for manual runs:

```bash
.venv/bin/python -m f1_ingestion.cli --source fastf1 --year 2024 --grand-prix 1 --session R
```

## Layout

- `apps/api` FastAPI app
- `apps/dashboard` Streamlit app
- `packages/core` shared config/logging
- `packages/ingestion` placeholder
- `packages/features` placeholder
- `packages/models` placeholder
- `packages/insights` placeholder
- `packages/llm` placeholder
- `data/` raw, processed, features
- `infra/` docker and ci scaffolding (empty)

## Latest run metadata

The API exposes `GET /api/v1/meta/last-run`, which returns the most recent run manifest enriched with operational signals:

- `artifact_availability`: a list of artifacts with their expected paths and whether the file exists (`exists`, plus a short `status` string like `available` or `missing`).
- `provenance`: the model and explainer names (and optional versions) that produced the intelligence.
- `freshness`: derived from the run timestamp (`status` is `recent`, `stale`, or `unknown`, and `age_seconds` reports how long ago the run finished).
- `execution_status`: high-level outcome of the run (`success`, `degraded`, or `failed`), which tracks whether the explanation generation hit a fallback path.

Example response fragment:

```json
{
  "status": "success",
  "artifacts": {
    "raw": "data/raw/raw_session_results.parquet"
  },
  "artifact_availability": [
    { "artifact_name": "raw", "expected_path": "data/raw/raw_session_results.parquet", "exists": true, "status": "available" }
  ],
  "provenance": {
    "model_name": "baseline_driver_scores",
    "explainer_name": "top_driver_explanations",
    "model_version": "v1",
    "explainer_version": "v1"
  },
  "freshness": {
    "status": "recent",
    "age_seconds": 120
  },
  "execution_status": "success"
}
```

### Operational guidance

- **When to check**: call `/api/v1/meta/last-run` after running the pipeline (via dashboard or POST endpoint) or when you need a quick sanity check that artifacts are landing as expected.
- **Interpret execution_status**: `success` means the full pipeline completed, `degraded` indicates the explanation step used the fallback artifact, and `failed` would only trigger if an error prevented manifest persistence (currently logged and reflected here if surfaced).
- **Use freshness + artifact_availability together**: a stale freshness status plus missing artifacts usually means the run should be re-triggered before downstream analysis; recent freshness with `exists: true` is what operators should aim for.
- **Artifact troubleshooting**: each entry in `artifact_availability` lists the expected path and existence flag—use it to confirm that storage paths match the pipeline outputs before digging deeper into the pipeline logs.

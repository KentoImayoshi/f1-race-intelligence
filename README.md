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

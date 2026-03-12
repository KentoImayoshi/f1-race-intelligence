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
pytest
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

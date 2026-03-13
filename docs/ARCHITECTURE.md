# Architecture Baseline

## System purpose
F1 Race Intelligence AI is a monorepo-grade intelligence pipeline. It exists to collect, normalize, analyze, and explain Formula 1 session data with deterministic layers that can be inspected locally, then serve the results through a minimal API and a paired Streamlit dashboard. Every layer is intentionally small, observable, and replaceable so the project can grow without accruing refactoring debt.

## Package and app boundaries
- `packages/core`: shared configuration, logging, and constants consumed by apps and packages that expose services.
- `packages/ingestion`: raw ingestion contracts and CLI/service functions. Writes `data/raw/raw_session_results.parquet`.
- `packages/processing`: normalization functions that read the raw parquet and emit `data/processed/processed_session_results.parquet`.
- `packages/features`: derives the first set of typed features (`data/features/features_session_results.parquet`).
- `packages/models`: builds a baseline analytical artifact (`data/models/baseline_session_driver_scores.parquet`).
- `packages/insights`: structures insight rows (`data/insights/insights_session_top_drivers.parquet`).
- `packages/llm`: generates grounded explanations (`data/llm/explanations_session_top_drivers.parquet`).
- `apps/api`: FastAPI app that only depends on `packages/core` plus the packaged transformations; it exposes read-only endpoints and a pipeline orchestrator without embedding data logic.
- `apps/dashboard`: Streamlit client that hits the API endpoints; it must not call the pipeline services directly.

## Data flow (raw → dashboard)
1. **Ingestion** reads external sources (currently seed data) into `data/raw/raw_session_results.parquet`.
2. **Processing** normalizes the raw file into `data/processed/processed_session_results.parquet`.
3. **Features** expands processed rows with derived columns in `data/features/features_session_results.parquet`.
4. **Models** consumes features and writes `data/models/baseline_session_driver_scores.parquet`.
5. **Insights** generates structured insight rows in `data/insights/insights_session_top_drivers.parquet`.
6. **LLM explanations** renders grounded narrative statements into `data/llm/explanations_session_top_drivers.parquet`.
7. **API** exposes read-only access to the artifacts and can re-run the entire sequence through `/api/v1/pipeline/run-session-baseline`.
8. **Dashboard** triggers the pipeline endpoint and displays the API responses.

## Artifact locations
- `data/raw/` for the first ingestion outputs.
- `data/processed/` for normalized session data.
- `data/features/` for derived feature tables.
- `data/models/` for analytical baseline scores.
- `data/insights/` for structured insights.
- `data/llm/` for grounded explanations.

## Dependency rules (allowed call graph)
- Apps/packages may depend on `packages/core` for shared config.
- Higher layers may read lower-layer artifacts but should always go through the packaged services (`ingestion` → `processing` → `features` → `models` → `insights` → `llm`).
- The FastAPI app (`apps/api`) can import package services but never writes to private directories; it orchestrates through the published APIs.
- The dashboard only depends on the API over HTTP; it cannot import internal packages.

## Anti-goals and constraints
- No distributed job scheduling, background queues, or streaming architectures in this phase.
- No external LLM calls; explanations must always be grounded in the structured artifacts.
- No Docker/CI scaffolding is added yet; keep everything runnable locally.
- Avoid hidden logic: each package exposes explicit services and contracts.

## Current intentional simplifications
- Flat files under `data/` instead of databases or buckets.
- Deterministic, synchronous pipeline (no background processing).
- API endpoints are read-only except for the single pipeline trigger.
- Dashboard is a thin HTTP client that does not duplicate data logic.

## Future extension points
- Swap ingestion with a real FastF1 fetcher or other data providers.
- Replace file persistence with lightweight databases or cloud storage (respecting the same contracts).
- Expand insights and explanation algorithms while keeping contracts explicit.
- Add observability/instrumentation hooks around each pipeline step.
- Harden the API (authentication, throttling) once the local flow stabilizes.

## Orchestration guardrail
- The pipeline service (`apps/api/src/f1_api/services/pipeline.py`) is intentionally the only component that imports multiple downstream packages and coordinates ingestion → processing → features → models → insights → llm. It owns the single POST `/api/v1/pipeline/run-session-baseline` endpoint and is the explicit heel for cross-layer flows.
- Read-only API routes (insights, models, explanations) must consume artifacts, not orchestrate additional packages. If an API needs more data, it should either read the relevant artifact via the shared paths or call the pipeline endpoint.
- The dashboard remains a thin HTTP client of the API; it must neither import nor call services under `packages/` directly.

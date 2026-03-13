# Plans

## Current stage — deterministic pipeline + serving
- Completed: ingestion → normalization → features → baseline models → structured insights → grounded explanations → read-only API + Streamlit dashboard.
- Done criteria: artifacts under `data/` exist, contracts are typed, API endpoints are stable, and the dashboard can trigger the pipeline and display the outputs.

## Next stage — hardening
1. **What to do:** add better logging, tests, config validation, and basic docs around observability.
2. **Decision gate:** pipeline artifacts are reproducible, tests pass (`pytest` + dashboard syntax checks), and architecture docs are in place (this commit).
3. **Done:** documented flows, consistent config, predictable error handling, and a maintenance-ready README.

## Stage after that — expand intelligence
- **Goals:** add new data sources (FastF1), richer modelling, and confidence-aware explanations.
- **Decision gate:** demonstration of reliable ingestion from multiple sources and deterministic outputs from the current stack.
- **Done:** new services adhere to the same contracts, additional tests covering the expanded sources, and extensions announced in PLANS.

## Future stage — automation / production readiness
- Prove CI/CD, containerization, and authenticated API access while preserving the explicit layer boundaries above.
- Decision gate: readiness metrics (lint/test pass, integration flow verified) trigger scaling the stack quietly.

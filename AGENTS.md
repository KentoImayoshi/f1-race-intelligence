# AGENTS.md

## Project
**Name:** F1 Race Intelligence AI

## Purpose
This project exists to build a practical F1 intelligence system that starts simple and evolves in layers.

The goal is **not** to build a giant AI platform from day one.  
The goal is to create a working product in small steps, where each phase leaves the project in a better, testable, and production-friendly state.

The system should be designed with this mindset:

- start narrow
- make each layer observable
- prefer boring and reliable solutions
- keep data flow explicit
- keep modules replaceable
- optimize for iteration, not premature sophistication

---

## Product vision
The system should help answer questions such as:

- What happened in a race weekend?
- Which drivers/teams overperformed or underperformed?
- What strategic patterns can be extracted from sessions?
- What insights can be generated from structured and semi-structured F1 data?
- How can raw race data become usable intelligence?

This is an **intelligence pipeline**, not just a chatbot.

---

## Core system mentality

### 1. Build from data to intelligence
Always think in this order:

1. **Collect**
2. **Normalize**
3. **Store**
4. **Analyze**
5. **Serve**
6. **Explain**

Do not jump straight to LLM features before the data layer is reliable.

### 2. Prefer explicit pipelines over magic
Every transformation should be understandable.

Bad:
- hidden logic
- giant scripts doing everything
- scraping + transformation + API response in one file

Good:
- ingestion isolated
- transformation isolated
- analysis isolated
- API isolated

### 3. Make the project evolvable
Every major part should be replaceable later:
- data source can change
- storage can change
- orchestration can change
- intelligence layer can become more advanced later

### 4. First make it work locally
Before worrying about cloud, scale, or automation:
- run locally
- inspect outputs
- validate assumptions
- save artifacts
- document the flow

### 5. Production is a consequence of discipline
Production-readiness comes from:
- good folder structure
- clear contracts
- typed code
- logs
- tests
- reproducible environments
- small deployable units

---

## Initial scope
The first versions should focus on **one narrow end-to-end flow**.

Suggested initial slice:
- ingest race/session data
- normalize into consistent schemas
- persist locally
- generate basic metrics/insights
- expose them through an API
- optionally summarize them with AI later

Do not start with:
- multi-agent orchestration
- advanced RAG
- vector databases
- dashboards with too many features
- real-time streaming
- complicated infra

These may come later only if the simple version proves useful.

---

## Development phases
The project is divided into days/phases.  
Agents should respect the phase and avoid pulling future complexity too early.

### Day 1 — Foundation
Goal:
- initialize repository
- define folder structure
- define stack
- configure environment
- set coding standards
- create minimal runnable app

Deliverables:
- project skeleton
- `README.md`
- `.env.example`
- dependency management
- lint/format config
- minimal FastAPI app running

### Day 2 — Data ingestion
Goal:
- obtain F1 data from chosen sources
- create first ingestion pipeline
- save raw data locally

Deliverables:
- source client(s)
- fetch scripts/services
- raw data directory or database tables
- basic logging
- failure handling

### Day 3 — Normalization layer
Goal:
- transform raw inputs into stable internal schemas

Deliverables:
- pydantic/domain models
- normalization functions
- cleaned datasets
- validation rules
- consistent naming conventions

### Day 4 — Analysis layer
Goal:
- generate useful metrics and race intelligence from normalized data

Deliverables:
- analysis services
- derived metrics
- comparison logic
- race/session summaries
- deterministic outputs first

### Day 5 — API layer
Goal:
- expose data and insights through endpoints

Deliverables:
- FastAPI routes
- request/response schemas
- service layer wiring
- health endpoint
- versioned API structure

### Day 6 — AI layer
Goal:
- add AI only after deterministic data flow is working

Deliverables:
- prompt layer
- summarization or explanation service
- clear grounding in project data
- traceable inputs/outputs

### Day 7 — Hardening
Goal:
- improve quality, observability, and maintainability

Deliverables:
- tests
- better logs
- config cleanup
- error handling improvements
- basic docs
- first production-minded review

---

## What agents should optimize for
When contributing to this repo, agents must optimize for:

- clarity
- modularity
- explicit data flow
- maintainability
- testability
- small incremental progress

Agents should avoid:
- unnecessary abstractions
- premature optimization
- giant refactors without need
- adding new frameworks without clear benefit
- hiding important logic behind convenience wrappers

---

## Technical preferences
Unless explicitly changed, prefer:

- **Python 3.11+**
- **FastAPI** for API layer
- **Pydantic** for schemas/validation
- **Requests/httpx** for data fetching
- **SQLModel / SQLAlchemy** or simple file persistence initially
- **pytest** for tests
- **ruff** for lint/format
- **uv** or **pip + venv** for environment management
- **Docker** only after the local flow is stable

Keep the stack minimal.

---

## Suggested folder structure
Agents should prefer a structure close to this:

```text
f1-race-intelligence-ai/
├─ app/
│  ├─ api/
│  │  ├─ routes/
│  │  └─ deps/
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logging.py
│  │  └─ constants.py
│  ├─ domain/
│  │  ├─ models/
│  │  └─ schemas/
│  ├─ services/
│  │  ├─ ingestion/
│  │  ├─ normalization/
│  │  ├─ analysis/
│  │  └─ ai/
│  ├─ repositories/
│  └─ main.py
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ artifacts/
├─ tests/
├─ scripts/
├─ .env.example
├─ README.md
├─ pyproject.toml
└─ AGENTS.md
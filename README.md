# F1 Race Intelligence AI

Pragmatic, incremental F1 intelligence pipeline. Start small, keep data flow explicit, and evolve in layers.

## Local setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -e ".[dev]"
```

3. Create your environment file.

```bash
cp .env.example .env
```

## Run the API

```bash
uvicorn app.main:app --reload
```

## Verify

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

## Structure

- `app/` application code
- `data/` raw/processed/artifacts
- `tests/` tests
- `scripts/` local scripts

# F1 Race Intelligence AI

Pragmatic, incremental F1 intelligence pipeline. Start small, keep data flow explicit, and evolve in layers.

## Quick start

1. Create a virtual environment and install deps.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Run the API.

```bash
uvicorn app.main:app --reload
```

3. Check health.

```bash
curl http://127.0.0.1:8000/health
```

## Structure

- `app/` application code
- `data/` raw/processed/artifacts
- `tests/` tests
- `scripts/` local scripts

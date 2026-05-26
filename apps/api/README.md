# f1-api

Minimal FastAPI app for the monorepo.

## Runtime dependency note

The API installs `fastf1` as a direct runtime dependency because ingestion providers are invoked
through API pipeline flows. This keeps local editable installs and Docker runtime behavior aligned.

#!/usr/bin/env bash
set -euo pipefail

python -m pip install -U pip

python -m pip install -e packages/core
python -m pip install -e packages/ingestion
python -m pip install -e packages/processing
python -m pip install -e packages/features
python -m pip install -e packages/models
python -m pip install -e packages/insights
python -m pip install -e packages/llm

python -m pip install -e apps/api
python -m pip install -e apps/dashboard

python -m pip install pytest ruff black httpx

# FastF1 is required by the real-data ingestion path used by the API pipeline.
python -c "import fastf1"

#!/usr/bin/env bash
set -euo pipefail

python -m pip install -U pip

python -m pip install -e packages/core
python -m pip install -e packages/models
python -m pip install -e packages/ingestion
python -m pip install -e packages/features
python -m pip install -e packages/insights
python -m pip install -e packages/llm

python -m pip install -e apps/api
python -m pip install -e apps/dashboard

python -m pip install pytest ruff black

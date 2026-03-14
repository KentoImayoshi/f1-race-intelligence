FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/api /app/apps/api
COPY packages /app/packages

EXPOSE 8000

RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir \
    -e /app/packages/core \
    -e /app/packages/ingestion \
    -e /app/packages/processing \
    -e /app/packages/features \
    -e /app/packages/models \
    -e /app/packages/insights \
    -e /app/packages/llm \
    -e /app/apps/api

WORKDIR /app/apps/api
CMD ["uvicorn", "f1_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

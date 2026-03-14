FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/api /app/apps/api
COPY packages /app/packages

RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir -e /app/packages/core
RUN pip install --no-cache-dir -e /app/apps/api

WORKDIR /app/apps/api
CMD ["uvicorn", "f1_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

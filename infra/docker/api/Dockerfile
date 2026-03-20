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
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request, sys; from urllib.error import URLError, HTTPError; \
try: resp = urllib.request.urlopen('http://localhost:8000/ready', timeout=3); \
except (URLError, HTTPError): sys.exit(1); \
sys.exit(0 if resp.status == 200 else 1)"
CMD ["uvicorn", "f1_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

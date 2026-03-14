FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/dashboard /app/apps/dashboard
COPY packages /app/packages

RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir -e /app/packages/core
RUN pip install --no-cache-dir -e /app/apps/dashboard

WORKDIR /app/apps/dashboard
CMD ["streamlit", "run", "src/f1_dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# App code + data
COPY app/ app/

EXPOSE 8000
# Render injects $PORT; fall back to 8000 for local use
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]


# Backend container for Render (Docker runtime). Root Directory = backend.
# Serves the API only; it reads from Supabase at runtime, so no content/ or scripts/.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

WORKDIR /app

# Install deps first (cached layer) — needs the lockfile + pinned Python.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

# App code.
COPY app ./app

# Render injects $PORT. Shell form so the variable expands.
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT

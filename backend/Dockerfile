# syntax=docker/dockerfile:1

# Buyam-Sellam backend — FastAPI.
# Build context: repository root (so it can read pyproject.toml + uv.lock).

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install uv and resolve dependencies straight from pyproject.toml + uv.lock
# (single source of truth — no separate requirements.txt to drift).
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

# Copy the FastAPI app + core game logic.
COPY backend ./backend

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

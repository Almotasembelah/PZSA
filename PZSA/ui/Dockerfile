FROM python:3.12-slim AS base

# System deps (needed for opencv + kafka + build)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy workspace metadata so uv can resolve deps
COPY pyproject.toml ./

# Copy service + shared packages only
COPY PZSA/configs ./PZSA/configs
COPY PZSA/services/streaming ./PZSA/services/streaming
COPY PZSA/ui ./PZSA/ui

# Install uv
RUN pip install --no-cache-dir uv

# Install only this project's dependencies
RUN uv sync --project ui --no-dev

# Ensure project venv is active
ENV PATH="/app/ui/.venv/bin:$PATH"

CMD ["uv", "run", "--project", "ui", "PZSA/ui/src/app.py"]

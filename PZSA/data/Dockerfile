FROM python:3.12-slim AS base

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
COPY PZSA/data ./PZSA/data

# Install uv
RUN pip install --no-cache-dir uv

# Install only this project's dependencies
RUN uv sync --project data --no-dev
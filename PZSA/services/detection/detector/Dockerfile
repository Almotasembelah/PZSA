FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy workspace metadata so uv can resolve deps
COPY pyproject.toml ./
COPY uv.lock ./

# Copy service + shared packages only
COPY PZSA/configs ./PZSA/configs
COPY PZSA/services/detection/detector ./PZSA/services/detection/detector

# Install uv
RUN pip install --no-cache-dir uv

RUN uv sync --all-packages --no-dev

CMD ["uv", "run", "python", "-m", "PZSA.services.detection.detector.src.detect"]
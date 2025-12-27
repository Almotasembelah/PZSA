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
COPY PZSA/controller ./PZSA/controller
COPY PZSA/data ./PZSA/data
COPY PZSA/services/detection/violation_checker ./PZSA/services/detection/violation_checker

# Install uv
RUN pip install --no-cache-dir uv

# Install only this project's dependencies
RUN uv sync --project violation_checker --no-dev

# Ensure project venv is active
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "--project", "violation_checker", "PZSA/services/detection/violation_checker/src/check_violation.py"]

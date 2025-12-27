# Dockerfile
FROM base:latest as base-layer

COPY . /app
WORKDIR /app

# Optional: re-run uv if service-specific deps differ
RUN uv pip install --system

CMD ["python"]
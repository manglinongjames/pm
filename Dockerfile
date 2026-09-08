FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

WORKDIR /app/backend

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/app ./app
COPY --from=frontend-builder /app/frontend/out ./app/static/frontend

RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

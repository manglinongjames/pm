# Backend Agent Guide

## Purpose

The backend hosts the FastAPI service for the Project Management MVP and will become the source of truth for authentication, Kanban persistence, and AI orchestration.

## Current Scope (Part 3)

- FastAPI service entrypoint at `app/main.py`.
- Routes:
	- `GET /` serves the exported frontend Kanban app.
	- `GET /api/health` returns service health.
	- `GET /api/hello` returns example JSON response.
- Frontend static assets are served from `app/static/frontend/`.

## Stack and Packaging

- Python 3.12+
- FastAPI
- Uvicorn
- Dependency management defined in `pyproject.toml` and installed with `uv` inside Docker.

## Design Rules

- Keep API design simple and explicit.
- Favor pure functions and small route handlers where possible.
- Avoid introducing auth/database/AI features until their planned steps.
- Return consistent JSON structures for API endpoints.

## Run Path

- Container build and run are managed from repository root via scripts in `../scripts/`.
- Runtime service listens on port `8000`.

## Next Planned Changes

- Add authentication flow in Part 4.
- Add SQLite schema and persistence in Parts 5-7.
- Add OpenRouter integration and structured AI updates in Parts 8-10.
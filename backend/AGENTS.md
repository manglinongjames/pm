# Backend Agent Guide

## Purpose

The backend hosts the FastAPI service for the Project Management MVP and will become the source of truth for authentication, Kanban persistence, and AI orchestration.

## Current Scope (Part 6)

- FastAPI service entrypoint at `app/main.py`.
- Routes:
	- `GET /` serves the exported frontend Kanban app.
	- `GET /api/health` returns service health.
	- `GET /api/hello` returns example JSON response.
	- `GET /api/users/{username}/board` fetches persisted board state.
	- `PATCH /api/users/{username}/columns/{column_id}` renames columns.
	- `POST /api/users/{username}/columns/{column_id}/cards` creates cards.
	- `PATCH /api/users/{username}/cards/{card_id}` updates card title/description.
	- `DELETE /api/users/{username}/cards/{card_id}` deletes cards.
	- `POST /api/users/{username}/cards/{card_id}/move` moves cards across columns/positions.
- Frontend static assets are served from `app/static/frontend/`.
- SQLite persistence is implemented in `app/kanban_store.py`.

## Stack and Packaging

- Python 3.12+
- FastAPI
- Uvicorn
- Dependency management defined in `pyproject.toml` and installed with `uv` inside Docker.

## Design Rules

- Keep API design simple and explicit.
- Favor pure functions and small route handlers where possible.
- Keep validation/error mapping consistent (400 validation, 404 not found, 500 unexpected errors).
- Return consistent JSON structures for API endpoints.

## Run Path

- Container build and run are managed from repository root via scripts in `../scripts/`.
- Runtime service listens on port `8000`.

## Next Planned Changes

- Replace frontend in-memory board state with backend persistence calls in Part 7.
- Add OpenRouter integration and structured AI updates in Parts 8-10.
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.kanban_store import (
    StoreNotFoundError,
    StoreValidationError,
    create_card_for_user,
    delete_card_for_user,
    get_board_for_user,
    initialize_database,
    move_card_for_user,
    rename_column_for_user,
    update_card_for_user,
)

STATIC_DIR = Path(__file__).parent / "static"
DEFAULT_FRONTEND_DIR = STATIC_DIR / "frontend"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "pm.db"


def resolve_frontend_dir() -> Path:
    frontend_dir = os.getenv("PM_FRONTEND_DIST_DIR")
    if frontend_dir:
        return Path(frontend_dir)
    return DEFAULT_FRONTEND_DIR


def resolve_db_path() -> Path:
    db_path = os.getenv("PM_DB_PATH")
    if db_path:
        return Path(db_path)
    return DEFAULT_DB_PATH


class RenameColumnBody(BaseModel):
    title: str


class CreateCardBody(BaseModel):
    title: str
    details: str = ""


class UpdateCardBody(BaseModel):
    title: str | None = None
    details: str | None = None


class MoveCardBody(BaseModel):
    toColumnId: str
    toPosition: int | None = None


def create_app(frontend_dir: Path | None = None, db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db_file = (db_path or resolve_db_path()).resolve()
    initialize_database(db_file)

    def handle_store_error(error: Exception) -> HTTPException:
        if isinstance(error, StoreValidationError):
            return HTTPException(status_code=400, detail=str(error))
        if isinstance(error, StoreNotFoundError):
            return HTTPException(status_code=404, detail=str(error))
        return HTTPException(status_code=500, detail="Unexpected backend error.")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/hello")
    def hello() -> dict[str, str]:
        return {"message": "Hello from FastAPI"}

    @app.get("/api/users/{username}/board")
    def get_board(username: str) -> dict:
        try:
            return get_board_for_user(db_file, username)
        except Exception as error:
            raise handle_store_error(error) from error

    @app.patch("/api/users/{username}/columns/{column_id}")
    def rename_column(username: str, column_id: str, body: RenameColumnBody) -> dict:
        try:
            return rename_column_for_user(
                db_file,
                username,
                column_id,
                body.title,
            )
        except Exception as error:
            raise handle_store_error(error) from error

    @app.post("/api/users/{username}/columns/{column_id}/cards")
    def create_card(username: str, column_id: str, body: CreateCardBody) -> dict:
        try:
            return create_card_for_user(
                db_file,
                username,
                column_id,
                body.title,
                body.details,
            )
        except Exception as error:
            raise handle_store_error(error) from error

    @app.patch("/api/users/{username}/cards/{card_id}")
    def update_card(username: str, card_id: str, body: UpdateCardBody) -> dict:
        try:
            return update_card_for_user(
                db_file,
                username,
                card_id,
                body.title,
                body.details,
            )
        except Exception as error:
            raise handle_store_error(error) from error

    @app.delete("/api/users/{username}/cards/{card_id}")
    def delete_card(username: str, card_id: str) -> dict:
        try:
            return delete_card_for_user(db_file, username, card_id)
        except Exception as error:
            raise handle_store_error(error) from error

    @app.post("/api/users/{username}/cards/{card_id}/move")
    def move_card(username: str, card_id: str, body: MoveCardBody) -> dict:
        try:
            return move_card_for_user(
                db_file,
                username,
                card_id,
                body.toColumnId,
                body.toPosition,
            )
        except Exception as error:
            raise handle_store_error(error) from error

    frontend_root = (frontend_dir or resolve_frontend_dir()).resolve()
    if frontend_root.exists() and (frontend_root / "index.html").exists():
        app.mount("/", StaticFiles(directory=frontend_root, html=True), name="frontend")
    else:
        @app.get("/")
        def frontend_not_built() -> PlainTextResponse:
            return PlainTextResponse(
                "Frontend export not found. Build frontend before starting backend.",
                status_code=503,
            )

    return app


app = create_app()

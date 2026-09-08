import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"
DEFAULT_FRONTEND_DIR = STATIC_DIR / "frontend"


def resolve_frontend_dir() -> Path:
    frontend_dir = os.getenv("PM_FRONTEND_DIST_DIR")
    if frontend_dir:
        return Path(frontend_dir)
    return DEFAULT_FRONTEND_DIR


def create_app(frontend_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/hello")
    def hello() -> dict[str, str]:
        return {"message": "Hello from FastAPI"}

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

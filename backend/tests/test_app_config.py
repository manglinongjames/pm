import os
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import create_app, resolve_frontend_dir


class AppConfigTests(unittest.TestCase):
    def test_resolve_frontend_dir_uses_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            previous = os.environ.get("PM_FRONTEND_DIST_DIR")
            os.environ["PM_FRONTEND_DIST_DIR"] = temp_dir
            try:
                resolved = resolve_frontend_dir()
                self.assertEqual(resolved, Path(temp_dir))
            finally:
                if previous is None:
                    os.environ.pop("PM_FRONTEND_DIST_DIR", None)
                else:
                    os.environ["PM_FRONTEND_DIST_DIR"] = previous

    def test_create_app_registers_api_routes(self) -> None:
        app = create_app(frontend_dir=Path("missing-frontend-dir"))
        route_paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/api/health", route_paths)
        self.assertIn("/api/hello", route_paths)

    def test_create_app_mounts_frontend_when_index_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            frontend_dir = Path(temp_dir)
            (frontend_dir / "index.html").write_text("<h1>Kanban Studio</h1>", encoding="utf-8")
            app = create_app(frontend_dir=frontend_dir)
            mount_names = {route.name for route in app.routes if hasattr(route, "name")}
            self.assertIn("frontend", mount_names)


if __name__ == "__main__":
    unittest.main()

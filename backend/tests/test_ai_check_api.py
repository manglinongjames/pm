import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import create_app
from app.openrouter_client import OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterUpstreamError


class AiCheckApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_root = Path(self.temp_dir.name)

        frontend_dir = temp_root / "frontend"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        (frontend_dir / "index.html").write_text("<h1>Kanban Studio</h1>", encoding="utf-8")

        db_path = temp_root / "pm.db"
        self.app = create_app(frontend_dir=frontend_dir, db_path=db_path)
        self.client_manager = TestClient(self.app)
        self.client = self.client_manager.__enter__()

    def tearDown(self) -> None:
        self.client_manager.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_ai_check_returns_503_when_key_is_missing(self) -> None:
        with patch("app.main.resolve_openrouter_api_key", return_value=""):
            response = self.client.post("/api/users/user/ai/check")

        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENROUTER_API_KEY", response.json()["detail"])

    def test_ai_check_success_payload(self) -> None:
        with patch("app.main.OpenRouterClient") as client_class:
            instance = client_class.return_value
            instance.check_connectivity.return_value = {
                "model": "openai/gpt-oss-120b",
                "answer": "4",
                "expectedAnswer": "4",
                "matchesExpectedAnswer": True,
            }

            with patch("app.main.resolve_openrouter_api_key", return_value="test-key"):
                response = self.client.post("/api/users/user/ai/check")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "ok": True,
                "provider": "openrouter",
                "model": "openai/gpt-oss-120b",
                "answer": "4",
                "expectedAnswer": "4",
                "matchesExpectedAnswer": True,
            },
        )
        client_class.assert_called_once_with(api_key="test-key")

    def test_ai_check_maps_auth_failure(self) -> None:
        with patch("app.main.OpenRouterClient") as client_class:
            instance = client_class.return_value
            instance.check_connectivity.side_effect = OpenRouterAuthError(401, "bad key")

            with patch("app.main.resolve_openrouter_api_key", return_value="test-key"):
                response = self.client.post("/api/users/user/ai/check")

        self.assertEqual(response.status_code, 502)
        self.assertIn("authentication failed", response.json()["detail"].lower())

    def test_ai_check_maps_rate_limit_failure(self) -> None:
        with patch("app.main.OpenRouterClient") as client_class:
            instance = client_class.return_value
            instance.check_connectivity.side_effect = OpenRouterRateLimitError(429, "too many")

            with patch("app.main.resolve_openrouter_api_key", return_value="test-key"):
                response = self.client.post("/api/users/user/ai/check")

        self.assertEqual(response.status_code, 502)
        self.assertIn("rate limit", response.json()["detail"].lower())

    def test_ai_check_maps_generic_upstream_failure(self) -> None:
        with patch("app.main.OpenRouterClient") as client_class:
            instance = client_class.return_value
            instance.check_connectivity.side_effect = OpenRouterUpstreamError(500, "gateway down")

            with patch("app.main.resolve_openrouter_api_key", return_value="test-key"):
                response = self.client.post("/api/users/user/ai/check")

        self.assertEqual(response.status_code, 502)
        self.assertIn("request failed", response.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
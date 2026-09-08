import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def find_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class AppIntegrationTests(unittest.TestCase):
    def test_api_and_frontend_root_served(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            frontend_dir = Path(temp_dir)
            (frontend_dir / "index.html").write_text(
                "<html><body><h1>Kanban Studio</h1></body></html>",
                encoding="utf-8",
            )

            port = find_open_port()
            env = os.environ.copy()
            env["PM_FRONTEND_DIST_DIR"] = str(frontend_dir)
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--app-dir",
                    str(BACKEND_DIR),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--log-level",
                    "warning",
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                base_url = f"http://127.0.0.1:{port}"
                for _ in range(80):
                    try:
                        with urllib.request.urlopen(
                            f"{base_url}/api/health", timeout=1
                        ) as response:
                            if response.status == 200:
                                break
                    except Exception:
                        time.sleep(0.1)
                else:
                    self.fail("Server did not become ready in time")

                with urllib.request.urlopen(f"{base_url}/api/health", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    payload = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(payload, {"status": "ok"})

                with urllib.request.urlopen(f"{base_url}/api/hello", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    payload = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(payload, {"message": "Hello from FastAPI"})

                with urllib.request.urlopen(f"{base_url}/", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    body = response.read().decode("utf-8")
                    self.assertIn("Kanban Studio", body)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()


if __name__ == "__main__":
    unittest.main()

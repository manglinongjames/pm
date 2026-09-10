from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib import error, request

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"


class OpenRouterError(Exception):
    """Base error for OpenRouter integration failures."""


class OpenRouterConfigError(OpenRouterError):
    """Raised when required local configuration is missing."""


class OpenRouterUpstreamError(OpenRouterError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


class OpenRouterAuthError(OpenRouterUpstreamError):
    """Raised when upstream authentication fails."""


class OpenRouterRateLimitError(OpenRouterUpstreamError):
    """Raised when upstream rate limits the request."""


RequestSender = Callable[[str, dict[str, Any], dict[str, str], float], tuple[int, dict[str, Any]]]


def _read_env_file_value(env_file: Path, key: str) -> str:
    if not env_file.exists():
        return ""

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        left, right = line.split("=", 1)
        if left.strip() != key:
            continue

        value = right.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        return value

    return ""


def resolve_openrouter_api_key() -> str:
    env_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if env_key:
        return env_key

    # Repository root is two levels above backend/app.
    repo_root = Path(__file__).resolve().parents[2]
    file_key = _read_env_file_value(repo_root / ".env", "OPENROUTER_API_KEY").strip()
    return file_key


def build_connectivity_payload() -> dict[str, Any]:
    return {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "What is 2+2? Reply with only the number.",
            }
        ],
        "temperature": 0,
    }


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                chunks.append(item["text"])
        return "".join(chunks).strip()

    return ""


def _decode_json(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _send_json_request(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout_seconds: float,
) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            return response.getcode(), _decode_json(response.read())
    except error.HTTPError as exc:
        return exc.code, _decode_json(exc.read())
    except error.URLError as exc:
        raise OpenRouterUpstreamError(502, f"OpenRouter request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OpenRouterUpstreamError(504, "OpenRouter request timed out.") from exc


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 20.0,
        request_sender: RequestSender | None = None,
    ):
        key = api_key.strip()
        if not key:
            raise OpenRouterConfigError("OPENROUTER_API_KEY is not configured.")

        self._api_key = key
        self._timeout_seconds = timeout_seconds
        self._request_sender = request_sender or _send_json_request

    def check_connectivity(self) -> dict[str, Any]:
        payload = build_connectivity_payload()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        status_code, response_payload = self._request_sender(
            OPENROUTER_CHAT_URL,
            payload,
            headers,
            self._timeout_seconds,
        )

        if status_code in (401, 403):
            raise OpenRouterAuthError(status_code, "OpenRouter authentication failed.")
        if status_code == 429:
            raise OpenRouterRateLimitError(status_code, "OpenRouter rate limit reached.")
        if status_code >= 400:
            raise OpenRouterUpstreamError(status_code, f"OpenRouter returned status {status_code}.")

        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenRouterUpstreamError(502, "OpenRouter response was missing choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenRouterUpstreamError(502, "OpenRouter response choice was invalid.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenRouterUpstreamError(502, "OpenRouter response message was invalid.")

        answer = _extract_text_content(message.get("content"))
        if not answer:
            raise OpenRouterUpstreamError(502, "OpenRouter response content was empty.")

        return {
            "model": OPENROUTER_MODEL,
            "answer": answer,
            "expectedAnswer": "4",
            "matchesExpectedAnswer": answer == "4",
        }
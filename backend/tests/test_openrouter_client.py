import unittest

from app.openrouter_client import (
    OPENROUTER_CHAT_URL,
    OPENROUTER_MODEL,
    OpenRouterAuthError,
    OpenRouterClient,
    OpenRouterRateLimitError,
    OpenRouterUpstreamError,
    build_connectivity_payload,
)


class OpenRouterClientTests(unittest.TestCase):
    def test_build_connectivity_payload_uses_expected_model(self) -> None:
        payload = build_connectivity_payload()

        self.assertEqual(payload["model"], OPENROUTER_MODEL)
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["messages"][0]["content"], "What is 2+2? Reply with only the number.")

    def test_check_connectivity_formats_request_and_parses_response(self) -> None:
        captured: dict = {}

        def fake_sender(url: str, payload: dict, headers: dict, timeout_seconds: float):
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            captured["timeout_seconds"] = timeout_seconds
            return 200, {
                "choices": [
                    {
                        "message": {
                            "content": "4",
                        }
                    }
                ]
            }

        client = OpenRouterClient(
            api_key="test-key",
            timeout_seconds=12.5,
            request_sender=fake_sender,
        )

        result = client.check_connectivity()

        self.assertEqual(captured["url"], OPENROUTER_CHAT_URL)
        self.assertEqual(captured["payload"]["model"], OPENROUTER_MODEL)
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(captured["timeout_seconds"], 12.5)
        self.assertEqual(result["answer"], "4")
        self.assertTrue(result["matchesExpectedAnswer"])

    def test_check_connectivity_handles_array_content(self) -> None:
        def fake_sender(_url: str, _payload: dict, _headers: dict, _timeout_seconds: float):
            return 200, {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "4"},
                            ]
                        }
                    }
                ]
            }

        client = OpenRouterClient(api_key="test-key", request_sender=fake_sender)
        result = client.check_connectivity()

        self.assertEqual(result["answer"], "4")

    def test_check_connectivity_maps_auth_error(self) -> None:
        def fake_sender(_url: str, _payload: dict, _headers: dict, _timeout_seconds: float):
            return 401, {}

        client = OpenRouterClient(api_key="test-key", request_sender=fake_sender)

        with self.assertRaises(OpenRouterAuthError):
            client.check_connectivity()

    def test_check_connectivity_maps_rate_limit_error(self) -> None:
        def fake_sender(_url: str, _payload: dict, _headers: dict, _timeout_seconds: float):
            return 429, {}

        client = OpenRouterClient(api_key="test-key", request_sender=fake_sender)

        with self.assertRaises(OpenRouterRateLimitError):
            client.check_connectivity()

    def test_check_connectivity_rejects_unexpected_response_format(self) -> None:
        def fake_sender(_url: str, _payload: dict, _headers: dict, _timeout_seconds: float):
            return 200, {"id": "missing-choices"}

        client = OpenRouterClient(api_key="test-key", request_sender=fake_sender)

        with self.assertRaises(OpenRouterUpstreamError):
            client.check_connectivity()


if __name__ == "__main__":
    unittest.main()
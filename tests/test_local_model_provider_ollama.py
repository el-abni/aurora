from __future__ import annotations

import json
import unittest
from unittest import mock
from urllib import error as urllib_error

from aurora.local_model.contracts import (
    LocalModelProviderError,
    LocalModelRequest,
)
from aurora.local_model.provider_ollama import (
    DEFAULT_OLLAMA_EXPLAIN_TIMEOUT_MS,
    DEFAULT_OLLAMA_KEEP_ALIVE,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_TIMEOUT_MS,
    OLLAMA_PROVIDER_NAME,
    OllamaLocalModelProvider,
    resolve_local_model_provider_from_environment,
)


def _sample_request(*, capability: str = "summarize", outcome: str = "planned") -> LocalModelRequest:
    return LocalModelRequest(
        capability=capability,
        schema={"schema_id": "aurora.decision_record.v1"},
        stable_ids={"action_id": "procurar", "route_id": "host_package.procurar", "event_id": "planned"},
        facts={
            "request": {"original_text": "procurar firefox"},
            "policy": {"policy_outcome": "allow"},
            "environment_resolution": {"status": "resolved"},
            "target_resolution": {"status": "resolved", "package_name": "firefox"},
            "execution_route": {"route_id": "host_package.procurar"},
            "execution": {"event_id": "planned"},
            "outcome": outcome,
        },
        presentation={"summary": "Aurora encontrou a rota de procura no host."},
    )


class _FakeHttpResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _FakeHttpResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self._body


class OllamaLocalModelProviderTests(unittest.TestCase):
    def test_environment_resolution_uses_canonical_defaults(self) -> None:
        provider, fallback_reason = resolve_local_model_provider_from_environment(
            environ={"AURORA_LOCAL_MODEL_PROVIDER": "ollama"}
        )

        self.assertEqual(fallback_reason, "")
        self.assertIsInstance(provider, OllamaLocalModelProvider)
        self.assertEqual(provider.provider_name, OLLAMA_PROVIDER_NAME)
        self.assertEqual(provider.model_name, DEFAULT_OLLAMA_MODEL)
        self.assertEqual(provider.url, "http://127.0.0.1:11434/api/generate")
        self.assertEqual(provider.timeout_ms, DEFAULT_OLLAMA_TIMEOUT_MS)
        self.assertTrue(provider.uses_default_timeout)
        self.assertEqual(provider.keep_alive, DEFAULT_OLLAMA_KEEP_ALIVE)

    def test_unsupported_provider_is_normalized_to_provider_unavailable(self) -> None:
        provider, fallback_reason = resolve_local_model_provider_from_environment(
            environ={"AURORA_LOCAL_MODEL_PROVIDER": "legacy-provider"}
        )

        self.assertIsNone(provider)
        self.assertEqual(fallback_reason, "provider_unavailable")

    def test_provider_posts_to_generate_endpoint_and_returns_response(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout: float):
            captured["url"] = request.full_url
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _FakeHttpResponse(b'{"response":"Resumo curto do kernel."}')

        provider, fallback_reason = resolve_local_model_provider_from_environment(
            environ={
                "AURORA_LOCAL_MODEL_PROVIDER": "ollama",
                "AURORA_LOCAL_MODEL_MODEL": "fixture-model",
                "AURORA_LOCAL_MODEL_URL": "http://127.0.0.1:11434",
                "AURORA_LOCAL_MODEL_TIMEOUT_MS": "1000",
            }
        )
        self.assertEqual(fallback_reason, "")

        with mock.patch("aurora.local_model.provider_ollama.urllib_request.urlopen", side_effect=fake_urlopen):
            response = provider.assist(_sample_request())

        self.assertEqual(response.capability, "summarize")
        self.assertEqual(response.text, "Resumo curto do kernel.")
        self.assertEqual(captured["url"], "http://127.0.0.1:11434/api/generate")
        body = captured["body"]
        self.assertEqual(body["model"], "fixture-model")
        self.assertEqual(body["stream"], False)
        self.assertEqual(body["keep_alive"], DEFAULT_OLLAMA_KEEP_ALIVE)
        self.assertEqual(body["options"]["num_predict"], 64)
        self.assertEqual(captured["timeout"], 1.0)
        self.assertIn("Kernel facts are authoritative.", body["prompt"])

    def test_explain_uses_extended_default_timeout_floor(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout: float):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _FakeHttpResponse(b'{"response":"Explicacao curta do kernel."}')

        provider = OllamaLocalModelProvider(
            model_name="fixture-model",
            url="http://127.0.0.1:11434/api/generate",
            timeout_ms=DEFAULT_OLLAMA_TIMEOUT_MS,
            uses_default_timeout=True,
        )

        with mock.patch("aurora.local_model.provider_ollama.urllib_request.urlopen", side_effect=fake_urlopen):
            response = provider.assist(_sample_request(capability="explain", outcome="blocked"))

        self.assertEqual(response.capability, "explain")
        self.assertEqual(captured["timeout"], DEFAULT_OLLAMA_EXPLAIN_TIMEOUT_MS / 1000.0)
        self.assertEqual(captured["body"]["options"]["num_predict"], 96)

    def test_explain_honors_explicit_timeout_override(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout: float):
            captured["timeout"] = timeout
            return _FakeHttpResponse(b'{"response":"Explicacao curta do kernel."}')

        provider = OllamaLocalModelProvider(
            model_name="fixture-model",
            url="http://127.0.0.1:11434/api/generate",
            timeout_ms=25000,
            uses_default_timeout=False,
        )

        with mock.patch("aurora.local_model.provider_ollama.urllib_request.urlopen", side_effect=fake_urlopen):
            provider.assist(_sample_request(capability="explain", outcome="blocked"))

        self.assertEqual(captured["timeout"], 25.0)

    def test_provider_invalid_response_raises_provider_error(self) -> None:
        provider = OllamaLocalModelProvider(
            model_name="fixture-model",
            url="http://127.0.0.1:11434/api/generate",
            timeout_ms=1000,
        )

        with mock.patch(
            "aurora.local_model.provider_ollama.urllib_request.urlopen",
            return_value=_FakeHttpResponse(b'{"done":true}'),
        ):
            with self.assertRaises(LocalModelProviderError) as context:
                provider.assist(_sample_request())

        self.assertEqual(context.exception.reason, "provider_invalid_response")
        self.assertEqual(context.exception.provider_name, "ollama")

    def test_provider_timeout_raises_provider_error(self) -> None:
        provider = OllamaLocalModelProvider(
            model_name="fixture-model",
            url="http://127.0.0.1:11434/api/generate",
            timeout_ms=25,
            uses_default_timeout=False,
        )

        with mock.patch(
            "aurora.local_model.provider_ollama.urllib_request.urlopen",
            side_effect=urllib_error.URLError(TimeoutError("timed out")),
        ):
            with self.assertRaises(LocalModelProviderError) as context:
                provider.assist(_sample_request())

        self.assertEqual(context.exception.reason, "provider_timeout")
        self.assertEqual(context.exception.provider_name, "ollama")


if __name__ == "__main__":
    unittest.main()

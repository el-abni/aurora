from __future__ import annotations

import json
import os
import socket
from collections.abc import Mapping
from dataclasses import dataclass
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .contracts import (
    FALLBACK_REASON_PROVIDER_CONNECTION_ERROR,
    FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
    FALLBACK_REASON_PROVIDER_NOT_CONFIGURED,
    FALLBACK_REASON_PROVIDER_TIMEOUT,
    FALLBACK_REASON_PROVIDER_UNAVAILABLE,
    LOCAL_MODEL_AUTHORITY_PROFILE,
    LocalModelProvider,
    LocalModelProviderError,
    LocalModelRequest,
    LocalModelResponse,
)

OLLAMA_PROVIDER_NAME = "ollama"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b-instruct"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
# v1.0.0 keeps 60000 ms as the base operational default calibrated by real smoke.
# The explain path gets a higher default floor because real blocked-case probes ran
# too close to that limit. This is an operational guardrail, not eternal policy.
DEFAULT_OLLAMA_TIMEOUT_MS = 60000
DEFAULT_OLLAMA_EXPLAIN_TIMEOUT_MS = 90000
DEFAULT_OLLAMA_KEEP_ALIVE = "15m"

_OLLAMA_NUM_PREDICT_BY_CAPABILITY = {
    "clarify": 48,
    "disambiguate_limited": 48,
    "summarize": 64,
    "explain": 96,
}


def _string(value: object, *, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _timeout_config(value: object) -> tuple[int, bool]:
    raw = _string(value)
    if not raw:
        return DEFAULT_OLLAMA_TIMEOUT_MS, True
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_OLLAMA_TIMEOUT_MS, True
    if parsed <= 0:
        return DEFAULT_OLLAMA_TIMEOUT_MS, True
    return parsed, False


def _normalize_generate_url(value: object) -> str:
    candidate = _string(value, default=DEFAULT_OLLAMA_URL)
    if "://" not in candidate:
        candidate = f"http://{candidate}"

    parts = urllib_parse.urlsplit(candidate)
    scheme = parts.scheme or "http"
    netloc = parts.netloc
    path = parts.path.rstrip("/")

    if not netloc and path:
        netloc = path
        path = ""

    if path != "/api/generate":
        path = f"{path}/api/generate" if path else "/api/generate"

    return urllib_parse.urlunsplit((scheme, netloc, path, parts.query, parts.fragment))


def _capability_instructions(capability: str) -> str:
    if capability == "clarify":
        return "Point only to the ambiguity that needs clarification."
    if capability == "disambiguate_limited":
        return "Point only to the already structured candidates and ask for a choice."
    if capability == "explain":
        return "Explain the kernel decision without inventing support or route changes."
    return "Summarize the kernel decision briefly without changing the operational truth."


def _provider_payload(request: LocalModelRequest) -> dict[str, object]:
    return {
        "requested_capability": request.capability,
        "authority_profile": LOCAL_MODEL_AUTHORITY_PROFILE,
        "advisory_only": True,
        "schema": dict(request.schema),
        "stable_ids": dict(request.stable_ids),
        "facts": dict(request.facts),
        "presentation": dict(request.presentation),
    }


def _build_prompt(request: LocalModelRequest) -> str:
    payload_json = json.dumps(
        _provider_payload(request),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    lines = [
        "You are the optional local assistive layer for Aurora.",
        "Kernel facts are authoritative.",
        f"Requested capability: {request.capability}.",
        _capability_instructions(request.capability),
        "Return only a short plain-text answer in pt-BR.",
        "Do not decide policy, support, block, confirmation, route, execution, or operational truth.",
        "If the payload is insufficient, state the ambiguity without inventing facts.",
        f"Payload JSON: {payload_json}",
    ]
    return "\n".join(lines)


def _num_predict(capability: str) -> int:
    return _OLLAMA_NUM_PREDICT_BY_CAPABILITY.get(capability, 64)


@dataclass(frozen=True)
class OllamaLocalModelProvider(LocalModelProvider):
    model_name: str = DEFAULT_OLLAMA_MODEL
    url: str = f"{DEFAULT_OLLAMA_URL}/api/generate"
    timeout_ms: int = DEFAULT_OLLAMA_TIMEOUT_MS
    uses_default_timeout: bool = True
    keep_alive: str = DEFAULT_OLLAMA_KEEP_ALIVE
    provider_name: str = OLLAMA_PROVIDER_NAME

    def _request_timeout_ms(self, request: LocalModelRequest) -> int:
        if self.uses_default_timeout and request.capability == "explain":
            return max(self.timeout_ms, DEFAULT_OLLAMA_EXPLAIN_TIMEOUT_MS)
        return self.timeout_ms

    def assist(self, request: LocalModelRequest) -> LocalModelResponse:
        request_timeout_ms = self._request_timeout_ms(request)
        payload = {
            "model": self.model_name,
            "prompt": _build_prompt(request),
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {"num_predict": _num_predict(request.capability)},
        }
        http_request = urllib_request.Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(http_request, timeout=request_timeout_ms / 1000.0) as response:
                raw_body = response.read()
        except urllib_error.HTTPError as exc:
            raise LocalModelProviderError(
                FALLBACK_REASON_PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
            ) from exc
        except urllib_error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise LocalModelProviderError(
                    FALLBACK_REASON_PROVIDER_TIMEOUT,
                    provider_name=self.provider_name,
                ) from exc
            if isinstance(reason, OSError):
                raise LocalModelProviderError(
                    FALLBACK_REASON_PROVIDER_CONNECTION_ERROR,
                    provider_name=self.provider_name,
                ) from exc
            raise LocalModelProviderError(
                FALLBACK_REASON_PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
            ) from exc
        except (OSError, TimeoutError, socket.timeout) as exc:
            if isinstance(exc, (TimeoutError, socket.timeout)):
                raise LocalModelProviderError(
                    FALLBACK_REASON_PROVIDER_TIMEOUT,
                    provider_name=self.provider_name,
                ) from exc
            raise LocalModelProviderError(
                FALLBACK_REASON_PROVIDER_CONNECTION_ERROR,
                provider_name=self.provider_name,
            ) from exc

        try:
            decoded = raw_body.decode("utf-8")
            response_payload = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocalModelProviderError(
                FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
                provider_name=self.provider_name,
            ) from exc

        if not isinstance(response_payload, dict):
            raise LocalModelProviderError(
                FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
                provider_name=self.provider_name,
            )

        response_text = response_payload.get("response")
        if not isinstance(response_text, str):
            raise LocalModelProviderError(
                FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
                provider_name=self.provider_name,
            )

        return LocalModelResponse(capability=request.capability, text=response_text)


def resolve_ollama_provider_from_environment(
    *,
    environ: Mapping[str, str] | None = None,
) -> OllamaLocalModelProvider:
    source = environ if environ is not None else os.environ
    timeout_ms, uses_default_timeout = _timeout_config(source.get("AURORA_LOCAL_MODEL_TIMEOUT_MS"))
    return OllamaLocalModelProvider(
        model_name=_string(source.get("AURORA_LOCAL_MODEL_MODEL"), default=DEFAULT_OLLAMA_MODEL),
        url=_normalize_generate_url(source.get("AURORA_LOCAL_MODEL_URL")),
        timeout_ms=timeout_ms,
        uses_default_timeout=uses_default_timeout,
    )


def resolve_local_model_provider_from_environment(
    *,
    environ: Mapping[str, str] | None = None,
) -> tuple[LocalModelProvider | None, str]:
    source = environ if environ is not None else os.environ
    provider_name = _string(source.get("AURORA_LOCAL_MODEL_PROVIDER")).lower()
    if not provider_name:
        return None, FALLBACK_REASON_PROVIDER_NOT_CONFIGURED
    if provider_name != OLLAMA_PROVIDER_NAME:
        return None, FALLBACK_REASON_PROVIDER_UNAVAILABLE
    return resolve_ollama_provider_from_environment(environ=source), ""

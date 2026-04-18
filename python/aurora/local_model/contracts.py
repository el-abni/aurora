from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

MODEL_OFF = "model_off"
MODEL_ON = "model_on"
MODEL_MODES = (MODEL_OFF, MODEL_ON)

LOCAL_MODEL_INPUT_SCHEMA_ID = "aurora.local_model.input.v1"
LOCAL_MODEL_AUTHORITY_PROFILE = "aurora.local_model.limited_assist.v1"

LOCAL_MODEL_ALLOWED_CAPABILITIES = (
    "clarify",
    "summarize",
    "explain",
    "disambiguate_limited",
)

LOCAL_MODEL_FORBIDDEN_AUTHORITIES = (
    "policy",
    "support",
    "block",
    "confirmation",
    "route",
    "execution",
    "operational_truth",
)

LOCAL_MODEL_CONSUMED_SECTIONS = (
    "schema",
    "stable_ids",
    "facts.request",
    "facts.policy",
    "facts.environment_resolution",
    "facts.target_resolution",
    "facts.execution_route",
    "facts.execution",
    "presentation.summary",
)

FALLBACK_REASON_PROVIDER_NOT_CONFIGURED = "provider_not_configured"
FALLBACK_REASON_PROVIDER_CONNECTION_ERROR = "provider_connection_error"
FALLBACK_REASON_PROVIDER_TIMEOUT = "provider_timeout"
FALLBACK_REASON_PROVIDER_INVALID_RESPONSE = "provider_invalid_response"
FALLBACK_REASON_PROVIDER_UNAVAILABLE = "provider_unavailable"
FALLBACK_REASON_PROVIDER_RETURNED_EMPTY_OUTPUT = "provider_returned_empty_output"

LOCAL_MODEL_FALLBACK_REASONS = (
    FALLBACK_REASON_PROVIDER_NOT_CONFIGURED,
    FALLBACK_REASON_PROVIDER_CONNECTION_ERROR,
    FALLBACK_REASON_PROVIDER_TIMEOUT,
    FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
    FALLBACK_REASON_PROVIDER_UNAVAILABLE,
    FALLBACK_REASON_PROVIDER_RETURNED_EMPTY_OUTPUT,
)

_LOCAL_MODEL_FALLBACK_REASON_ALIASES = {
    "provider_not_supported": FALLBACK_REASON_PROVIDER_UNAVAILABLE,
    "provider_returned_forbidden_capability": FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
    "provider_returned_capability_mismatch": FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
}


def normalize_local_model_fallback_reason(reason: object, *, default: str = "") -> str:
    raw = str(reason or "").strip()
    if not raw:
        return default
    normalized = raw.replace("-", "_").lower()
    canonical = _LOCAL_MODEL_FALLBACK_REASON_ALIASES.get(normalized, normalized)
    if canonical in LOCAL_MODEL_FALLBACK_REASONS:
        return canonical
    return default or canonical


@dataclass(frozen=True)
class LocalModelRequest:
    capability: str
    schema: Mapping[str, object]
    stable_ids: Mapping[str, object]
    facts: Mapping[str, object]
    presentation: Mapping[str, object]


@dataclass(frozen=True)
class LocalModelResponse:
    capability: str
    text: str


class LocalModelProvider(Protocol):
    provider_name: str

    def assist(self, request: LocalModelRequest) -> LocalModelResponse:
        ...


class LocalModelProviderError(RuntimeError):
    def __init__(self, reason: str, *, provider_name: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.provider_name = provider_name


@dataclass(frozen=True)
class LocalModelState:
    mode: str = MODEL_OFF
    status: str = "disabled"
    authority_profile: str = LOCAL_MODEL_AUTHORITY_PROFILE
    advisory_only: bool = True
    input_schema_id: str = LOCAL_MODEL_INPUT_SCHEMA_ID
    consumed_sections: tuple[str, ...] = LOCAL_MODEL_CONSUMED_SECTIONS
    requested_capability: str = "none"
    provider_name: str = ""
    allowed_capabilities: tuple[str, ...] = LOCAL_MODEL_ALLOWED_CAPABILITIES
    forbidden_authorities: tuple[str, ...] = LOCAL_MODEL_FORBIDDEN_AUTHORITIES
    fallback_reason: str = ""
    output_text: str = ""

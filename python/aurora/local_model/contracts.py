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

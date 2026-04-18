from __future__ import annotations

import os
from dataclasses import replace

from .contracts import (
    MODEL_OFF,
    MODEL_MODES,
    FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
    FALLBACK_REASON_PROVIDER_NOT_CONFIGURED,
    FALLBACK_REASON_PROVIDER_RETURNED_EMPTY_OUTPUT,
    FALLBACK_REASON_PROVIDER_UNAVAILABLE,
    LOCAL_MODEL_ALLOWED_CAPABILITIES,
    LocalModelProvider,
    LocalModelProviderError,
    LocalModelRequest,
    LocalModelState,
    normalize_local_model_fallback_reason,
)
from .provider_ollama import resolve_local_model_provider_from_environment


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def resolve_local_model_mode(
    mode: str | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> str:
    candidate = mode
    if candidate is None:
        source = environ if environ is not None else os.environ
        candidate = source.get("AURORA_MODEL_MODE", "")
    normalized = str(candidate or "").strip().lower()
    if normalized in MODEL_MODES:
        return normalized
    return MODEL_OFF


def _requested_capability(payload: dict[str, object]) -> str:
    facts = _mapping(payload.get("facts"))
    policy = _mapping(facts.get("policy"))
    target_resolution = _mapping(facts.get("target_resolution"))
    environment_resolution = _mapping(facts.get("environment_resolution"))
    immutable_context = _mapping(policy.get("immutable_host_context"))
    trust_gaps = _string_list(policy.get("trust_gaps"))

    if target_resolution.get("status") == "ambiguous" and _string_list(target_resolution.get("candidates")):
        return "disambiguate_limited"

    if (
        immutable_context.get("host_is_immutable") is True
        and "immutable_surface_selection_required" in trust_gaps
    ):
        return "clarify"

    if str(environment_resolution.get("status") or "") in {"ambiguous", "missing", "not_found", "unresolved"}:
        return "clarify"

    if facts.get("outcome") == "blocked":
        return "explain"

    return "summarize"


def build_local_model_state(
    payload: dict[str, object],
    *,
    mode: str | None = None,
    provider: LocalModelProvider | None = None,
    environ: dict[str, str] | None = None,
) -> LocalModelState:
    resolved_mode = resolve_local_model_mode(mode, environ=environ)
    requested_capability = _requested_capability(payload)
    state = LocalModelState(mode=resolved_mode, requested_capability=requested_capability)

    if resolved_mode == MODEL_OFF:
        return state

    resolved_provider = provider
    if resolved_provider is None:
        resolved_provider, fallback_reason = resolve_local_model_provider_from_environment(environ=environ)
        if resolved_provider is None:
            return replace(
                state,
                status="fallback_deterministic",
                fallback_reason=normalize_local_model_fallback_reason(
                    fallback_reason,
                    default=FALLBACK_REASON_PROVIDER_NOT_CONFIGURED,
                ),
            )

    request = LocalModelRequest(
        capability=requested_capability,
        schema=_mapping(payload.get("schema")),
        stable_ids=_mapping(payload.get("stable_ids")),
        facts=_mapping(payload.get("facts")),
        presentation=_mapping(payload.get("presentation")),
    )
    provider_name = str(getattr(resolved_provider, "provider_name", "") or "")

    try:
        response = resolved_provider.assist(request)
    except LocalModelProviderError as exc:
        return replace(
            state,
            status="fallback_deterministic",
            provider_name=exc.provider_name or provider_name,
            fallback_reason=normalize_local_model_fallback_reason(
                exc.reason,
                default=FALLBACK_REASON_PROVIDER_UNAVAILABLE,
            ),
        )

    if response.capability not in LOCAL_MODEL_ALLOWED_CAPABILITIES:
        return replace(
            state,
            status="fallback_deterministic",
            provider_name=provider_name,
            fallback_reason=FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
        )

    if response.capability != requested_capability:
        return replace(
            state,
            status="fallback_deterministic",
            provider_name=provider_name,
            fallback_reason=FALLBACK_REASON_PROVIDER_INVALID_RESPONSE,
        )

    output_text = str(response.text)
    if not output_text.strip():
        return replace(
            state,
            status="fallback_deterministic",
            provider_name=provider_name,
            fallback_reason=FALLBACK_REASON_PROVIDER_RETURNED_EMPTY_OUTPUT,
        )

    return replace(
        state,
        status="completed",
        provider_name=provider_name,
        output_text=output_text,
    )


def local_model_state_to_dict(state: LocalModelState) -> dict[str, object]:
    return {
        "mode": state.mode,
        "status": state.status,
        "authority_profile": state.authority_profile,
        "advisory_only": state.advisory_only,
        "input_schema_id": state.input_schema_id,
        "consumed_sections": list(state.consumed_sections),
        "requested_capability": state.requested_capability,
        "provider_name": state.provider_name,
        "allowed_capabilities": list(state.allowed_capabilities),
        "forbidden_authorities": list(state.forbidden_authorities),
        "fallback_reason": state.fallback_reason,
        "output_text": state.output_text,
    }

from __future__ import annotations

import copy

from aurora.contracts.decisions import DecisionRecord
from aurora.contracts.decision_record_schema import (
    decision_record_facts,
    decision_record_presentation,
    decision_record_schema_metadata,
)
from aurora.contracts.stable_ids import decision_record_stable_ids
from aurora.local_model.contracts import LocalModelProvider
from aurora.local_model.seam import build_local_model_state, local_model_state_to_dict


def _legacy_top_level_payload(facts: dict[str, object], record: DecisionRecord) -> dict[str, object]:
    legacy_payload = copy.deepcopy(facts)
    if record.execution is not None and "execution" in legacy_payload:
        execution_payload = legacy_payload["execution"]
        if isinstance(execution_payload, dict):
            execution_payload["summary"] = record.execution.summary
            if record.execution.pre_probe is not None and execution_payload.get("pre_probe") is not None:
                execution_payload["pre_probe"]["summary"] = record.execution.pre_probe.summary
            if record.execution.post_probe is not None and execution_payload.get("post_probe") is not None:
                execution_payload["post_probe"]["summary"] = record.execution.post_probe.summary
    return legacy_payload


def decision_record_to_dict(
    record: DecisionRecord,
    *,
    model_mode: str | None = None,
    model_provider: LocalModelProvider | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, object]:
    facts = decision_record_facts(record)
    presentation = decision_record_presentation(record)
    payload: dict[str, object] = {
        "schema": decision_record_schema_metadata(),
        "stable_ids": decision_record_stable_ids(record),
        "facts": facts,
        "presentation": presentation,
    }
    payload["facts"]["local_model"] = local_model_state_to_dict(
        build_local_model_state(
            payload,
            mode=model_mode,
            provider=model_provider,
            environ=environ,
        )
    )

    payload.update(_legacy_top_level_payload(facts, record))
    payload["summary"] = presentation["summary"]
    return payload

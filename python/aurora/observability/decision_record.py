from __future__ import annotations

import copy

from aurora.contracts.decisions import DecisionRecord
from aurora.contracts.decision_record_schema import (
    decision_record_facts,
    decision_record_presentation,
    decision_record_schema_metadata,
)
from aurora.contracts.stable_ids import decision_record_stable_ids


def decision_record_to_dict(record: DecisionRecord) -> dict[str, object]:
    facts = decision_record_facts(record)
    presentation = decision_record_presentation(record)
    payload: dict[str, object] = {
        "schema": decision_record_schema_metadata(),
        "stable_ids": decision_record_stable_ids(record),
        "facts": facts,
        "presentation": presentation,
    }

    legacy_payload = copy.deepcopy(facts)
    if record.execution is not None and "execution" in legacy_payload:
        execution_payload = legacy_payload["execution"]
        if isinstance(execution_payload, dict):
            execution_payload["summary"] = record.execution.summary
            if record.execution.pre_probe is not None and execution_payload.get("pre_probe") is not None:
                execution_payload["pre_probe"]["summary"] = record.execution.pre_probe.summary
            if record.execution.post_probe is not None and execution_payload.get("post_probe") is not None:
                execution_payload["post_probe"]["summary"] = record.execution.post_probe.summary

    payload.update(legacy_payload)
    payload["summary"] = presentation["summary"]
    return payload

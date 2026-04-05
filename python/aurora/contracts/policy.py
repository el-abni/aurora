from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyAssessment:
    domain_kind: str
    source_type: str
    trust_level: str
    software_criticality: str
    trust_signals: tuple[str, ...]
    trust_gaps: tuple[str, ...]
    policy_outcome: str
    requires_confirmation: bool
    confirmation_supplied: bool
    reversal_level: str
    reason: str
    execution_surface: str = "host"

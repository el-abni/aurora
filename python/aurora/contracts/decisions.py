from __future__ import annotations

from dataclasses import dataclass

from .execution import ExecutionResult, ExecutionRoute
from .host import HostProfile
from .policy import PolicyAssessment
from .requests import SemanticRequest


@dataclass(frozen=True)
class DecisionRecord:
    request: SemanticRequest
    host_profile: HostProfile | None
    policy: PolicyAssessment | None
    execution_route: ExecutionRoute | None
    outcome: str
    summary: str
    execution: ExecutionResult | None = None

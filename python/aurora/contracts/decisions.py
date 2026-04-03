from __future__ import annotations

from dataclasses import dataclass

from .execution import ExecutionResult, ExecutionRoute
from .host import HostProfile
from .policy import PolicyAssessment
from .requests import SemanticRequest


@dataclass(frozen=True)
class TargetResolution:
    original_target: str
    consulted_target: str = ""
    consulted_targets: tuple[str, ...] = ()
    resolved_target: str = ""
    status: str = "not_needed"
    source: str = ""
    canonicalized: bool = False
    candidates: tuple[str, ...] = ()
    reason: str = ""
    diagnostic_command: tuple[str, ...] = ()
    diagnostic_exit_code: int | None = None
    diagnostic_stdout: str = ""
    diagnostic_stderr: str = ""


@dataclass(frozen=True)
class DecisionRecord:
    request: SemanticRequest
    host_profile: HostProfile | None
    policy: PolicyAssessment | None
    target_resolution: TargetResolution | None
    execution_route: ExecutionRoute | None
    outcome: str
    summary: str
    execution: ExecutionResult | None = None

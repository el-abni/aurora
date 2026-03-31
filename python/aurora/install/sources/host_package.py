from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest
from aurora.linux.host_package import build_host_package_route


def build_host_package_candidate(
    request: SemanticRequest,
    profile: HostProfile,
    *,
    target: str | None = None,
) -> ExecutionRoute | None:
    resolved_target = target if target is not None and target.strip() else request.target
    return build_host_package_route(request.intent, resolved_target, profile)

from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest
from aurora.linux.host_package import build_host_package_route


def build_host_package_candidate(
    request: SemanticRequest,
    profile: HostProfile,
) -> ExecutionRoute | None:
    return build_host_package_route(request.intent, request.target, profile)

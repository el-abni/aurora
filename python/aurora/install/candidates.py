from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest
from aurora.install.sources.host_package import build_host_package_candidate


def build_route_candidates(request: SemanticRequest, profile: HostProfile | None) -> tuple[ExecutionRoute, ...]:
    if request.domain_kind != "host_package" or profile is None:
        return ()
    route = build_host_package_candidate(request, profile)
    if route is None:
        return ()
    return (route,)

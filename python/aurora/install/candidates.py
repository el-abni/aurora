from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest
from aurora.install.sources.aur import build_aur_candidate
from aurora.install.sources.copr import build_copr_candidate
from aurora.install.sources.flatpak import build_flatpak_candidate
from aurora.install.sources.host_package import build_host_package_candidate


def build_route_candidates(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    target: str | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[ExecutionRoute, ...]:
    if profile is None:
        return ()

    route = None
    if request.domain_kind == "host_package":
        if request.requested_source == "copr":
            route = build_copr_candidate(request, profile, target=target, environ=environ)
        elif request.requested_source == "aur":
            route = build_aur_candidate(request, profile, target=target)
        else:
            route = build_host_package_candidate(request, profile, target=target)
    elif request.domain_kind == "user_software":
        route = build_flatpak_candidate(request, profile, target=target)

    if route is None:
        return ()
    return (route,)

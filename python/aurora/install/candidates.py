from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest
from aurora.linux.host_maintenance import build_host_maintenance_route
from aurora.linux.distrobox import build_distrobox_candidate
from aurora.linux.rpm_ostree import build_rpm_ostree_candidate
from aurora.install.sources.aur import build_aur_candidate
from aurora.install.sources.copr import build_copr_candidate
from aurora.install.sources.flatpak import build_flatpak_candidate
from aurora.install.sources.host_package import build_host_package_candidate
from aurora.install.sources.ppa import build_ppa_candidate
from aurora.linux.toolbox import build_toolbox_candidate


def build_route_candidates(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    target: str | None = None,
    environment_resolution=None,
    toolbox_profile: HostProfile | None = None,
    distrobox_profile: HostProfile | None = None,
    rpm_ostree_status=None,
    environ: dict[str, str] | None = None,
) -> tuple[ExecutionRoute, ...]:
    if profile is None:
        return ()

    route = None
    if request.execution_surface == "toolbox":
        route = build_toolbox_candidate(
            request,
            profile,
            toolbox_profile=toolbox_profile,
            environment_resolution=environment_resolution,
            target=target,
        )
    elif request.execution_surface == "distrobox":
        route = build_distrobox_candidate(
            request,
            profile,
            distrobox_profile=distrobox_profile,
            environment_resolution=environment_resolution,
            target=target,
        )
    elif request.execution_surface == "rpm_ostree":
        route = build_rpm_ostree_candidate(
            request,
            profile,
            target=target,
            status_observation=rpm_ostree_status,
        )
    elif request.domain_kind == "host_package":
        if request.requested_source == "ppa":
            route = build_ppa_candidate(request, profile, target=target)
        elif request.requested_source == "copr":
            route = build_copr_candidate(request, profile, target=target, environ=environ)
        elif request.requested_source == "aur":
            route = build_aur_candidate(request, profile, target=target)
        else:
            route = build_host_package_candidate(request, profile, target=target)
    elif request.domain_kind == "host_maintenance":
        route = build_host_maintenance_route(request.intent, profile)
    elif request.domain_kind == "user_software":
        route = build_flatpak_candidate(request, profile, target=target)

    if route is None:
        return ()
    return (route,)

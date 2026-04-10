from __future__ import annotations

from aurora.contracts.decisions import DecisionRecord
from aurora.contracts.requests import SemanticRequest
from aurora.install.candidates import build_route_candidates
from aurora.install.domain_classifier import classify_text
from aurora.install.policy_engine import assess_policy
from aurora.install.route_selector import select_route
from aurora.install.sources.aur import (
    aur_target_resolution_blocks,
    resolve_aur_target,
    resolved_aur_target,
)
from aurora.install.sources.copr import (
    copr_target_resolution_blocks,
    resolve_copr_target,
    resolved_copr_target,
)
from aurora.install.sources.flatpak import (
    flatpak_effective_remote,
    flatpak_remote_origin,
    flatpak_target_resolution_blocks,
    resolve_flatpak_target,
    resolved_flatpak_target,
)
from aurora.install.sources.ppa import (
    ppa_target_resolution_blocks,
    resolve_ppa_target,
    resolved_ppa_target,
)
from aurora.linux.distrobox import (
    distrobox_target_resolution_blocks,
    observe_distrobox_profile,
    resolve_distrobox_environment,
    resolve_distrobox_target,
)
from aurora.linux.host_profile import detect_host_profile
from aurora.linux.host_package import resolve_host_package_target
from aurora.linux.rpm_ostree import (
    observe_rpm_ostree_status,
    resolve_rpm_ostree_target,
    rpm_ostree_target_resolution_blocks,
)
from aurora.linux.toolbox import (
    observe_toolbox_profile,
    resolve_toolbox_environment,
    resolve_toolbox_target,
    toolbox_target_resolution_blocks,
)
from aurora.semantics.pipeline import has_confirmation_marker


def _summary_for_request(request: SemanticRequest) -> str:
    if not request.target:
        return "Sem ação aberta."

    def source_coordinate_label(fallback: str) -> str:
        if request.source_coordinate:
            return request.source_coordinate
        return fallback

    if request.execution_surface == "rpm_ostree" and request.domain_kind == "host_package":
        if request.intent == "procurar":
            return f"Vou inspecionar o pacote '{request.target}' na superfície rpm-ostree do host imutável."
        if request.intent == "instalar":
            return f"Vou adicionar o pacote '{request.target}' ao próximo deployment rpm-ostree."
        if request.intent == "remover":
            return f"Vou remover o pacote '{request.target}' do próximo deployment rpm-ostree."

    if request.execution_surface == "distrobox" and request.domain_kind == "host_package":
        environment_label = request.environment_target or "distrobox explicitamente solicitada"
        if request.intent == "procurar":
            return f"Vou procurar o pacote '{request.target}' dentro da distrobox '{environment_label}'."
        if request.intent == "instalar":
            return f"Vou instalar o pacote '{request.target}' dentro da distrobox '{environment_label}'."
        if request.intent == "remover":
            return f"Vou remover o pacote '{request.target}' dentro da distrobox '{environment_label}'."

    if request.execution_surface == "toolbox" and request.domain_kind == "host_package":
        environment_label = request.environment_target or "toolbox explicitamente solicitada"
        if request.intent == "procurar":
            return f"Vou procurar o pacote '{request.target}' dentro da toolbox '{environment_label}'."
        if request.intent == "instalar":
            return f"Vou instalar o pacote '{request.target}' dentro da toolbox '{environment_label}'."
        if request.intent == "remover":
            return f"Vou remover o pacote '{request.target}' dentro da toolbox '{environment_label}'."

    if request.domain_kind == "host_package":
        if request.requested_source == "ppa":
            if request.intent == "instalar":
                return (
                    f"Vou instalar o pacote do host '{request.target}' via PPA "
                    f"'{source_coordinate_label('explicitamente pedido')}'."
                )
            if request.intent == "remover":
                return (
                    f"Vou remover o pacote do host '{request.target}' via PPA "
                    f"'{source_coordinate_label('explicitamente pedido')}'."
                )
        if request.requested_source == "copr":
            if request.intent == "procurar":
                return (
                    f"Vou inspecionar o pacote do host '{request.target}' no COPR "
                    f"'{source_coordinate_label('explicitamente pedido')}'."
                )
            if request.intent == "instalar":
                return (
                    f"Vou instalar o pacote do host '{request.target}' via COPR "
                    f"'{source_coordinate_label('explicitamente pedido')}'."
                )
            if request.intent == "remover":
                return (
                    f"Vou remover o pacote do host '{request.target}' via COPR "
                    f"'{source_coordinate_label('explicitamente pedido')}'."
                )
        if request.requested_source == "aur":
            if request.intent == "procurar":
                return f"Vou procurar o pacote do host '{request.target}' pela rota AUR."
            if request.intent == "instalar":
                return f"Vou instalar o pacote do host '{request.target}' pela rota AUR."
            if request.intent == "remover":
                return f"Vou remover o pacote do host '{request.target}' pela rota AUR."
        if request.intent == "procurar":
            return f"Vou procurar o pacote do host '{request.target}'."
        if request.intent == "instalar":
            return f"Vou instalar o pacote do host '{request.target}'."
        if request.intent == "remover":
            return f"Vou remover o pacote do host '{request.target}'."

    if request.domain_kind == "user_software":
        effective_remote = flatpak_effective_remote(request)
        remote_origin = flatpak_remote_origin(request)
        if request.intent == "procurar":
            if effective_remote:
                if remote_origin == "default":
                    return (
                        f"Vou procurar o software do usuário '{request.target}' via flatpak "
                        f"no remote default '{effective_remote}'."
                    )
                return (
                    f"Vou procurar o software do usuário '{request.target}' via flatpak "
                    f"no remote explícito '{effective_remote}'."
                )
            return f"Vou procurar o software do usuário '{request.target}' via flatpak."
        if request.intent == "instalar":
            if effective_remote:
                if remote_origin == "default":
                    return (
                        f"Vou instalar o software do usuário '{request.target}' via flatpak "
                        f"no remote default '{effective_remote}'."
                    )
                return (
                    f"Vou instalar o software do usuário '{request.target}' via flatpak "
                    f"no remote explícito '{effective_remote}'."
                )
            return f"Vou instalar o software do usuário '{request.target}' via flatpak."
        if request.intent == "remover":
            if effective_remote:
                return (
                    f"Vou remover o software do usuário '{request.target}' via flatpak "
                    f"com restrição de remote '{effective_remote}'."
                )
            return f"Vou remover o software do usuário '{request.target}' via flatpak."

    return "Sem ação aberta."


def _outcome_for_request(
    request: SemanticRequest,
    policy_outcome: str | None,
    *,
    environment_resolution=None,
    target_resolution=None,
) -> str:
    if request.status == "OUT_OF_SCOPE":
        return "out_of_scope"
    if request.status == "BLOCKED":
        return "blocked"
    if _environment_resolution_blocks(request, environment_resolution):
        return "blocked"
    if _target_resolution_blocks(request, target_resolution):
        return "blocked"
    if policy_outcome in {"block", "require_confirmation"}:
        return "blocked"
    return "planned"


def _summary(
    request: SemanticRequest,
    *,
    environment_resolution=None,
    target_resolution=None,
) -> str:
    if _environment_resolution_blocks(request, environment_resolution) and environment_resolution is not None:
        return environment_resolution.reason
    if _target_resolution_blocks(request, target_resolution) and target_resolution is not None:
        return target_resolution.reason
    return _summary_for_request(request)


def _resolve_environment(
    request: SemanticRequest,
    profile,
    *,
    environ: dict[str, str] | None = None,
):
    if request.execution_surface == "distrobox":
        return resolve_distrobox_environment(request, profile, environ=environ)
    if request.execution_surface == "toolbox":
        return resolve_toolbox_environment(request, profile, environ=environ)
    return None


def _resolve_target(
    request: SemanticRequest,
    profile,
    *,
    toolbox_profile=None,
    environ: dict[str, str] | None = None,
):
    if request.execution_surface == "rpm_ostree":
        return resolve_rpm_ostree_target(request, profile, environ=environ)
    if request.execution_surface == "distrobox":
        return resolve_distrobox_target(request, toolbox_profile, environ=environ)
    if request.execution_surface == "toolbox":
        return resolve_toolbox_target(request, toolbox_profile, environ=environ)
    if request.domain_kind == "user_software":
        return resolve_flatpak_target(request, profile, environ=environ)
    if request.domain_kind == "host_package":
        if request.requested_source == "ppa":
            return resolve_ppa_target(request, profile, environ=environ)
        if request.requested_source == "copr":
            return resolve_copr_target(request, profile, environ=environ)
        if request.requested_source == "aur":
            return resolve_aur_target(request, profile, environ=environ)
        return resolve_host_package_target(request, profile, environ=environ)
    return None


def _resolved_target(request: SemanticRequest, target_resolution) -> str:
    if request.execution_surface == "rpm_ostree":
        if target_resolution is not None and target_resolution.resolved_target:
            return target_resolution.resolved_target
        return request.target
    if request.execution_surface == "distrobox":
        if target_resolution is not None and target_resolution.resolved_target:
            return target_resolution.resolved_target
        return request.target
    if request.execution_surface == "toolbox":
        if target_resolution is not None and target_resolution.resolved_target:
            return target_resolution.resolved_target
        return request.target
    if request.domain_kind == "user_software":
        return resolved_flatpak_target(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "ppa":
        return resolved_ppa_target(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "copr":
        return resolved_copr_target(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "aur":
        return resolved_aur_target(request, target_resolution)
    if target_resolution is not None and target_resolution.resolved_target:
        return target_resolution.resolved_target
    return request.target


def _target_resolution_blocks(request: SemanticRequest, target_resolution) -> bool:
    if target_resolution is None:
        return False
    if request.execution_surface == "rpm_ostree":
        return rpm_ostree_target_resolution_blocks(target_resolution)
    if request.execution_surface == "distrobox":
        return distrobox_target_resolution_blocks(target_resolution)
    if request.execution_surface == "toolbox":
        return toolbox_target_resolution_blocks(target_resolution)
    if request.domain_kind == "user_software":
        return flatpak_target_resolution_blocks(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "ppa":
        return ppa_target_resolution_blocks(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "copr":
        return copr_target_resolution_blocks(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "aur":
        return aur_target_resolution_blocks(request, target_resolution)
    return target_resolution.status in {"ambiguous", "not_found", "unresolved"}


def _environment_resolution_blocks(request: SemanticRequest, environment_resolution) -> bool:
    if request.execution_surface not in {"toolbox", "distrobox"} or environment_resolution is None:
        return False
    return environment_resolution.status in {"missing", "not_found", "unresolved", "ambiguous"}


def _confirmation_supplied(request: SemanticRequest, *, confirmed: bool) -> bool:
    if confirmed:
        return True
    return has_confirmation_marker(request.original_text)


def plan_request(
    request: SemanticRequest,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
) -> DecisionRecord:
    profile = None
    policy = None
    environment_resolution = None
    target_resolution = None
    route = None
    toolbox_profile = None
    toolbox_profile_probe = None
    distrobox_profile = None
    distrobox_profile_probe = None
    rpm_ostree_status = None
    confirmation_supplied = _confirmation_supplied(request, confirmed=confirmed)

    if request.domain_kind in {"host_package", "user_software"}:
        profile = detect_host_profile(environ)
        if request.execution_surface == "rpm_ostree":
            rpm_ostree_status = observe_rpm_ostree_status(environ=environ)
        environment_resolution = _resolve_environment(request, profile, environ=environ)
        if (
            request.execution_surface in {"toolbox", "distrobox"}
            and environment_resolution is not None
            and environment_resolution.status == "resolved"
            and environment_resolution.resolved_environment
        ):
            if request.execution_surface == "toolbox":
                toolbox_profile_probe = observe_toolbox_profile(
                    environment_resolution.resolved_environment,
                    environ=environ,
                )
                toolbox_profile = toolbox_profile_probe.profile if toolbox_profile_probe.observed else None
            else:
                distrobox_profile_probe = observe_distrobox_profile(
                    environment_resolution.resolved_environment,
                    environ=environ,
                )
                distrobox_profile = (
                    distrobox_profile_probe.profile if distrobox_profile_probe.observed else None
                )
        policy = assess_policy(
            request,
            profile,
            confirmation_supplied=confirmation_supplied,
            environ=environ,
            environment_resolution=environment_resolution,
            toolbox_profile=toolbox_profile,
            toolbox_profile_probe=toolbox_profile_probe,
            distrobox_profile=distrobox_profile,
            distrobox_profile_probe=distrobox_profile_probe,
            rpm_ostree_status=rpm_ostree_status,
        )
        target_resolution = _resolve_target(
            request,
            profile,
            toolbox_profile=toolbox_profile if request.execution_surface == "toolbox" else distrobox_profile,
            environ=environ,
        )
        if not _environment_resolution_blocks(request, environment_resolution) and not _target_resolution_blocks(request, target_resolution):
            route = select_route(
                build_route_candidates(
                    request,
                    profile,
                    target=_resolved_target(request, target_resolution),
                    environ=environ,
                    environment_resolution=environment_resolution,
                    toolbox_profile=toolbox_profile,
                    distrobox_profile=distrobox_profile,
                    rpm_ostree_status=rpm_ostree_status,
                )
            )

    outcome = _outcome_for_request(
        request,
        policy.policy_outcome if policy else None,
        environment_resolution=environment_resolution,
        target_resolution=target_resolution,
    )
    return DecisionRecord(
        request=request,
        host_profile=profile,
        policy=policy,
        target_resolution=target_resolution,
        execution_route=route,
        outcome=outcome,
        summary=_summary(
            request,
            environment_resolution=environment_resolution,
            target_resolution=target_resolution,
        ),
        environment_resolution=environment_resolution,
        toolbox_profile=toolbox_profile,
        distrobox_profile=distrobox_profile,
        rpm_ostree_status=rpm_ostree_status,
    )


def plan_text(
    text: str,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
) -> DecisionRecord:
    return plan_request(classify_text(text), environ=environ, confirmed=confirmed)

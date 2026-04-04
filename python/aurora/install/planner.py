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
from aurora.linux.host_profile import detect_host_profile
from aurora.linux.host_package import resolve_host_package_target
from aurora.semantics.pipeline import has_confirmation_marker


def _summary_for_request(request: SemanticRequest) -> str:
    if not request.target:
        return "Sem acao aberta."

    if request.domain_kind == "host_package":
        if request.requested_source == "ppa":
            if request.intent == "instalar":
                return (
                    f"Instalar o pacote do host '{request.target}' via PPA "
                    f"'{request.source_coordinate or '-'}'."
                )
            if request.intent == "remover":
                return (
                    f"Remover o pacote do host '{request.target}' via PPA "
                    f"'{request.source_coordinate or '-'}'."
                )
        if request.requested_source == "copr":
            if request.intent == "procurar":
                return (
                    f"Inspecionar o pacote do host '{request.target}' no COPR "
                    f"'{request.source_coordinate or '-'}'."
                )
            if request.intent == "instalar":
                return (
                    f"Instalar o pacote do host '{request.target}' via COPR "
                    f"'{request.source_coordinate or '-'}'."
                )
            if request.intent == "remover":
                return (
                    f"Remover o pacote do host '{request.target}' via COPR "
                    f"'{request.source_coordinate or '-'}'."
                )
        if request.requested_source == "aur":
            if request.intent == "procurar":
                return f"Procurar o pacote AUR '{request.target}'."
            if request.intent == "instalar":
                return f"Instalar o pacote AUR '{request.target}'."
            if request.intent == "remover":
                return f"Remover o pacote AUR '{request.target}'."
        if request.intent == "procurar":
            return f"Procurar o pacote do host '{request.target}'."
        if request.intent == "instalar":
            return f"Instalar o pacote do host '{request.target}'."
        if request.intent == "remover":
            return f"Remover o pacote do host '{request.target}'."

    if request.domain_kind == "user_software":
        effective_remote = flatpak_effective_remote(request)
        remote_origin = flatpak_remote_origin(request)
        if request.intent == "procurar":
            if effective_remote:
                if remote_origin == "default":
                    return (
                        f"Procurar o software do usuario '{request.target}' via flatpak "
                        f"no remote default '{effective_remote}'."
                    )
                return (
                    f"Procurar o software do usuario '{request.target}' via flatpak "
                    f"no remote explicito '{effective_remote}'."
                )
            return f"Procurar o software do usuario '{request.target}' via flatpak."
        if request.intent == "instalar":
            if effective_remote:
                if remote_origin == "default":
                    return (
                        f"Instalar o software do usuario '{request.target}' via flatpak "
                        f"no remote default '{effective_remote}'."
                    )
                return (
                    f"Instalar o software do usuario '{request.target}' via flatpak "
                    f"no remote explicito '{effective_remote}'."
                )
            return f"Instalar o software do usuario '{request.target}' via flatpak."
        if request.intent == "remover":
            if effective_remote:
                return (
                    f"Remover o software do usuario '{request.target}' via flatpak "
                    f"com restricao de remote '{effective_remote}'."
                )
            return f"Remover o software do usuario '{request.target}' via flatpak."

    return "Sem acao aberta."


def _outcome_for_request(
    request: SemanticRequest,
    policy_outcome: str | None,
    *,
    target_resolution=None,
) -> str:
    if request.status == "OUT_OF_SCOPE":
        return "out_of_scope"
    if request.status == "BLOCKED":
        return "blocked"
    if _target_resolution_blocks(request, target_resolution):
        return "blocked"
    if policy_outcome in {"block", "require_confirmation"}:
        return "blocked"
    return "planned"


def _summary(
    request: SemanticRequest,
    *,
    target_resolution=None,
) -> str:
    if _target_resolution_blocks(request, target_resolution) and target_resolution is not None:
        return target_resolution.reason
    return _summary_for_request(request)


def _resolve_target(
    request: SemanticRequest,
    profile,
    *,
    environ: dict[str, str] | None = None,
):
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
    if request.domain_kind == "user_software":
        return flatpak_target_resolution_blocks(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "ppa":
        return ppa_target_resolution_blocks(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "copr":
        return copr_target_resolution_blocks(request, target_resolution)
    if request.domain_kind == "host_package" and request.requested_source == "aur":
        return aur_target_resolution_blocks(request, target_resolution)
    return target_resolution.status in {"ambiguous", "not_found", "unresolved"}


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
    target_resolution = None
    route = None
    confirmation_supplied = _confirmation_supplied(request, confirmed=confirmed)

    if request.domain_kind in {"host_package", "user_software"}:
        profile = detect_host_profile(environ)
        policy = assess_policy(
            request,
            profile,
            confirmation_supplied=confirmation_supplied,
            environ=environ,
        )
        target_resolution = _resolve_target(request, profile, environ=environ)
        if not _target_resolution_blocks(request, target_resolution):
            route = select_route(
                build_route_candidates(
                    request,
                    profile,
                    target=_resolved_target(request, target_resolution),
                    environ=environ,
                )
            )

    outcome = _outcome_for_request(
        request,
        policy.policy_outcome if policy else None,
        target_resolution=target_resolution,
    )
    return DecisionRecord(
        request=request,
        host_profile=profile,
        policy=policy,
        target_resolution=target_resolution,
        execution_route=route,
        outcome=outcome,
        summary=_summary(request, target_resolution=target_resolution),
    )


def plan_text(
    text: str,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
) -> DecisionRecord:
    return plan_request(classify_text(text), environ=environ, confirmed=confirmed)

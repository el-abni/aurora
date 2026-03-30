from __future__ import annotations

from aurora.contracts.decisions import DecisionRecord
from aurora.contracts.requests import SemanticRequest
from aurora.install.candidates import build_route_candidates
from aurora.install.domain_classifier import classify_text
from aurora.install.policy_engine import assess_policy
from aurora.install.route_selector import select_route
from aurora.linux.host_profile import detect_host_profile


def _summary_for_request(request: SemanticRequest) -> str:
    if request.domain_kind != "host_package" or not request.target:
        return "Sem acao aberta."
    if request.intent == "procurar":
        return f"Procurar o pacote do host '{request.target}'."
    if request.intent == "instalar":
        return f"Instalar o pacote do host '{request.target}'."
    if request.intent == "remover":
        return f"Remover o pacote do host '{request.target}'."
    return "Sem acao aberta."


def _outcome_for_request(
    request: SemanticRequest,
    policy_outcome: str | None,
) -> str:
    if request.status == "OUT_OF_SCOPE":
        return "out_of_scope"
    if request.status == "BLOCKED":
        return "blocked"
    if policy_outcome in {"block", "require_confirmation"}:
        return "blocked"
    return "planned"


def plan_request(
    request: SemanticRequest,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
) -> DecisionRecord:
    profile = None
    policy = None
    route = None

    if request.domain_kind == "host_package":
        profile = detect_host_profile(environ)
        policy = assess_policy(request, profile, confirmation_supplied=confirmed)
        route = select_route(build_route_candidates(request, profile))

    outcome = _outcome_for_request(request, policy.policy_outcome if policy else None)
    return DecisionRecord(
        request=request,
        host_profile=profile,
        policy=policy,
        execution_route=route,
        outcome=outcome,
        summary=_summary_for_request(request),
    )


def plan_text(
    text: str,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
) -> DecisionRecord:
    return plan_request(classify_text(text), environ=environ, confirmed=confirmed)

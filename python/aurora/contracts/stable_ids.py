from __future__ import annotations

import re

from .decisions import DecisionRecord
from .execution import ExecutionRoute
from .requests import SemanticRequest

ACTION_IDS = frozenset({"procurar", "instalar", "remover"})

ROUTE_IDS = frozenset(
    {
        "host_package.procurar",
        "host_package.instalar",
        "host_package.remover",
        "aur.procurar",
        "aur.instalar",
        "aur.remover",
        "copr.procurar",
        "copr.instalar",
        "copr.remover",
        "ppa.instalar",
        "flatpak.procurar",
        "flatpak.instalar",
        "flatpak.remover",
        "toolbox.procurar",
        "toolbox.instalar",
        "toolbox.remover",
        "distrobox.procurar",
        "distrobox.instalar",
        "distrobox.remover",
        "rpm_ostree.procurar",
        "rpm_ostree.instalar",
        "rpm_ostree.remover",
    }
)

LEGACY_ROUTE_ALIASES = {
    "host_package.search": "host_package.procurar",
}

EVENT_IDS = frozenset(
    {
        "decision.blocked",
        "decision.out_of_scope",
        "decision.planned",
        "execution.backend_missing",
        "execution.blocked",
        "execution.confirmation_required",
        "execution.executed",
        "execution.executed_with_backend_warning",
        "execution.no_results",
        "execution.noop",
        "execution.not_implemented",
        "execution.operational_error",
        "execution.package_not_found",
        "execution.probe_missing",
        "execution.state_confirmation_failed",
    }
)

_EVENT_ID_RE = re.compile(r"^(decision|execution)\.[a-z_]+$")


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def stable_action_id(request: SemanticRequest, route: ExecutionRoute | None = None) -> str | None:
    for candidate in (request.intent, route.action_name if route is not None else ""):
        normalized = _normalize_token(candidate)
        if normalized in ACTION_IDS:
            return normalized
    return None


def stable_route_id(route: ExecutionRoute | None) -> str | None:
    if route is None:
        return None

    candidate = LEGACY_ROUTE_ALIASES.get(route.route_name, route.route_name)
    if candidate not in ROUTE_IDS:
        raise ValueError(f"rota fora do contrato estável desta linha: {candidate}")
    return candidate


def stable_event_id(record: DecisionRecord) -> str:
    if record.execution is not None and record.execution.status:
        candidate = f"execution.{_normalize_token(record.execution.status)}"
    else:
        candidate = f"decision.{_normalize_token(record.outcome)}"

    if not _EVENT_ID_RE.fullmatch(candidate) or candidate not in EVENT_IDS:
        raise ValueError(f"evento fora do contrato estável desta linha: {candidate}")
    return candidate


def decision_record_stable_ids(record: DecisionRecord) -> dict[str, str | None]:
    return {
        "action_id": stable_action_id(record.request, record.execution_route),
        "route_id": stable_route_id(record.execution_route),
        "event_id": stable_event_id(record),
    }

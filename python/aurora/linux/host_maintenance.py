from __future__ import annotations

from aurora.contracts.decisions import TargetResolution
from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest

_SYSTEM_TARGET = "sistema"


def resolve_host_maintenance_target(request: SemanticRequest) -> TargetResolution | None:
    if request.domain_kind != "host_maintenance":
        return None
    if request.intent != "atualizar":
        return TargetResolution(
            original_target=request.target,
            status="unresolved",
            source="host_maintenance_scope",
            reason="a manutencao do host desta rodada abre apenas a acao 'atualizar'.",
        )
    if request.target.strip().lower() != _SYSTEM_TARGET:
        return TargetResolution(
            original_target=request.target,
            status="unresolved",
            source="host_maintenance_scope",
            reason="a atualizacao do sistema do host desta rodada foi aberta apenas para 'sistema'.",
        )
    return TargetResolution(
        original_target=request.target,
        consulted_target=request.target,
        resolved_target=_SYSTEM_TARGET,
        status="direct",
        source="host_maintenance_scope",
        reason="escopo explicito de manutencao do host confirmado para o sistema local.",
    )


def build_host_maintenance_route(
    intent: str,
    profile: HostProfile,
) -> ExecutionRoute | None:
    if intent != "atualizar":
        return None
    if profile.mutability != "mutable" or profile.linux_family != "arch":
        return None
    if "pacman" not in profile.package_backends:
        return None

    notes = [
        "a atualizacao do sistema ficou restrita ao host Arch mutavel nesta abertura.",
        "a rota usa apenas o backend oficial do host e nao abre AUR implicita.",
        "esta manutencao exige confirmacao explicita antes da execucao real.",
    ]
    if profile.observed_third_party_package_tools:
        helpers = ", ".join(profile.observed_third_party_package_tools)
        notes.append(
            f"helpers de fonte terceira observados ({helpers}) nao ampliam host_maintenance nesta rodada."
        )

    return ExecutionRoute(
        route_name="host_maintenance.atualizar",
        action_name="atualizar",
        backend_name="sudo + pacman",
        command=("sudo", "pacman", "-Syu"),
        required_commands=("sudo", "pacman"),
        implemented=True,
        requires_privilege_escalation=True,
        interactive_passthrough=True,
        notes=tuple(notes),
    )

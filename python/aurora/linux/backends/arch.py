from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile


def arch_host_package_contract_notes(profile: HostProfile) -> tuple[str, ...]:
    notes = ["host_package em Arch usa pacman como backend oficial nesta rodada."]
    if profile.observed_third_party_package_tools:
        observed = ", ".join(profile.observed_third_party_package_tools)
        notes.append(
            f"helpers de fonte terceira observados ({observed}) nao ampliam o contrato de host_package nesta rodada."
        )
    return tuple(notes)


def build_arch_search_route(target: str, profile: HostProfile) -> ExecutionRoute:
    return ExecutionRoute(
        route_name="host_package.search",
        action_name="procurar",
        backend_name="pacman",
        command=("pacman", "-Ss", "--", target),
        required_commands=("pacman",),
        implemented=True,
        notes=arch_host_package_contract_notes(profile),
    )

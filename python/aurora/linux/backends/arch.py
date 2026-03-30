from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile


def build_arch_search_route(target: str, profile: HostProfile) -> ExecutionRoute:
    backends = set(profile.package_backends)
    if "pacman" in backends:
        return ExecutionRoute(
            route_name="host_package.search",
            action_name="procurar",
            backend_name="pacman",
            command=("pacman", "-Ss", "--", target),
            required_commands=("pacman",),
            implemented=True,
        )
    if "paru" in backends:
        return ExecutionRoute(
            route_name="host_package.search",
            action_name="procurar",
            backend_name="paru",
            command=("paru", "-Ss", "--", target),
            required_commands=("paru",),
            implemented=True,
        )
    return ExecutionRoute(
        route_name="host_package.search",
        action_name="procurar",
        backend_name="pacman",
        command=("pacman", "-Ss", "--", target),
        required_commands=("pacman",),
        implemented=True,
    )

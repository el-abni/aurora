from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile


def build_opensuse_search_route(target: str, _profile: HostProfile) -> ExecutionRoute:
    return ExecutionRoute(
        route_name="host_package.search",
        action_name="procurar",
        backend_name="zypper",
        command=("zypper", "search", "--", target),
        required_commands=("zypper",),
        implemented=True,
    )

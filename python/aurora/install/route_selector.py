from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute


def select_route(candidates: tuple[ExecutionRoute, ...]) -> ExecutionRoute | None:
    return candidates[0] if candidates else None

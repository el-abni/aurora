from __future__ import annotations

from aurora.install.execution_handoff import execute_decision
from aurora.install.planner import plan_text


def inspect_text(
    text: str,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
):
    return plan_text(text, environ=environ, confirmed=confirmed)


def execute_text(
    text: str,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
) -> int:
    return execute_decision(plan_text(text, environ=environ, confirmed=confirmed), environ=environ)

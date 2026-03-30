from __future__ import annotations

from aurora.install.planner import plan_text

from .render import render_decision_record


def render_dev_report(
    text: str,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
) -> str:
    return render_decision_record(plan_text(text, environ=environ, confirmed=confirmed))

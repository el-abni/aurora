from __future__ import annotations

from aurora.install.planner import plan_text
from aurora.local_model.contracts import LocalModelProvider

from .render import render_decision_record


def render_dev_report(
    text: str,
    environ: dict[str, str] | None = None,
    *,
    confirmed: bool = False,
    model_mode: str | None = None,
    model_provider: LocalModelProvider | None = None,
) -> str:
    return render_decision_record(
        plan_text(text, environ=environ, confirmed=confirmed),
        model_mode=model_mode,
        model_provider=model_provider,
        environ=environ,
    )

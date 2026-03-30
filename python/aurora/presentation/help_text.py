from __future__ import annotations

from aurora.paths import resource_path
from aurora.version import read_version


def render_help() -> str:
    template = resource_path("resources", "help.txt").read_text(encoding="utf-8")
    return template.format(version=read_version())

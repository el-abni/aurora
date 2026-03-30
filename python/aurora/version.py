from __future__ import annotations

from .paths import resource_path


def read_version() -> str:
    return resource_path("VERSION").read_text(encoding="utf-8").strip()

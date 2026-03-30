from __future__ import annotations

FIELD_WIDTH = 24


def field(label: str, value: str) -> str:
    resolved = value if value else "-"
    return f"{label + ':':<{FIELD_WIDTH}} {resolved}"

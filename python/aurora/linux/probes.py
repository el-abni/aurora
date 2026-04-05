from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

OS_RELEASE_ENV = "AURORA_OS_RELEASE_PATH"
OSTREE_BOOTED_ENV = "AURORA_OSTREE_BOOTED"


def parse_os_release_text(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        parsed[key.strip().upper()] = value.strip()
    return parsed


def read_os_release(environ: dict[str, str]) -> dict[str, str]:
    path = Path(environ.get(OS_RELEASE_ENV, "/etc/os-release"))
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    return parse_os_release_text(raw)


def split_like(value: str) -> tuple[str, ...]:
    return tuple(token for token in value.lower().split() if token)


def tokenize(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(token for token in re.split(r"[^a-z0-9._+-]+", value.lower()) if token)


def detect_available_commands(commands: tuple[str, ...], environ: dict[str, str]) -> tuple[str, ...]:
    path = environ.get("PATH", os.environ.get("PATH"))
    detected: list[str] = []
    for command in commands:
        if shutil.which(command, path=path) is not None:
            detected.append(command)
    return tuple(detected)

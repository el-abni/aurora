from __future__ import annotations

import os
from pathlib import Path


def _package_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_share_dir(environ: dict[str, str] | None = None) -> Path:
    resolved_environ = os.environ if environ is None else environ
    candidates: list[Path] = []

    env_share = resolved_environ.get("AURORA_SHARE_DIR")
    if env_share:
        candidates.append(Path(env_share).expanduser())

    candidates.append(_package_repo_root())
    candidates.append(Path.home() / ".local" / "share" / "aurora")

    for candidate in candidates:
        if (candidate / "python" / "aurora").exists() and (candidate / "VERSION").exists():
            return candidate

    return candidates[0]


def resource_path(*parts: str, environ: dict[str, str] | None = None) -> Path:
    return resolve_share_dir(environ) / Path(*parts)

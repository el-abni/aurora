from __future__ import annotations

import os
from pathlib import Path

from .probes import OSTREE_BOOTED_ENV, tokenize

ATOMIC_IDS = {
    "aurora",
    "bazzite",
    "bluefin",
    "fedora-coreos",
    "kinoite",
    "microos",
    "onyx",
    "opensuse-microos",
    "sericea",
    "silverblue",
}

ATOMIC_VARIANTS = {"atomic", "coreos", "immutable", "kinoite", "microos", "ostree", "sericea", "silverblue", "onyx"}


def detect_mutability(
    distro_id: str,
    variant_id: str,
    name: str,
    pretty_name: str,
    environ: dict[str, str] | None = None,
) -> str:
    resolved_environ = os.environ if environ is None else environ
    atomic_tokens = {
        *(tokenize(distro_id)),
        *(tokenize(variant_id)),
        *(tokenize(name)),
        *(tokenize(pretty_name)),
    }
    if distro_id in ATOMIC_IDS:
        return "atomic"
    if variant_id in ATOMIC_VARIANTS:
        return "atomic"
    if atomic_tokens & (ATOMIC_IDS | ATOMIC_VARIANTS):
        return "atomic"
    if resolved_environ.get(OSTREE_BOOTED_ENV, "").strip() == "1":
        return "atomic"
    if Path("/run/ostree-booted").exists():
        return "atomic"
    return "mutable"

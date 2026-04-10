from __future__ import annotations

import os
import sys
from typing import Sequence

from aurora.app import execute_text
from aurora.observability.dev_command import render_dev_report
from aurora.presentation.help_text import render_help
from aurora.presentation.messages import invalid_command_message, missing_dev_phrase_message
from aurora.version import read_version

HELP_TOKENS = {"ajuda", "help", "--help", "-h"}
VERSION_TOKENS = {"version", "--version", "-v"}
CONFIRM_TOKENS = {"--confirm", "--yes"}


def _extract_global_flags(args: list[str]) -> tuple[list[str], bool]:
    confirmed = os.environ.get("AURORA_AUTO_CONFIRM", "").strip() == "1"
    filtered: list[str] = []
    for arg in args:
        if arg in CONFIRM_TOKENS:
            confirmed = True
            continue
        filtered.append(arg)
    return filtered, confirmed


def main(argv: Sequence[str] | None = None) -> int:
    args, confirmed = _extract_global_flags(list(argv if argv is not None else sys.argv[1:]))
    if not args:
        print(invalid_command_message())
        return 1

    first = args[0].strip().lower()

    if first in HELP_TOKENS:
        print(render_help())
        return 0

    if first in VERSION_TOKENS:
        print(f"Aurora {read_version()}")
        return 0

    if first == "dev":
        phrase = " ".join(args[1:]).strip()
        if not phrase:
            print(missing_dev_phrase_message())
            return 1
        print(render_dev_report(phrase, confirmed=confirmed))
        return 0

    text = " ".join(args).strip()
    return execute_text(text, confirmed=confirmed)

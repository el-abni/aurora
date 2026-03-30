from __future__ import annotations

from .intent import is_command_token
from .normalize import normalize_token


def split_actions(tokens: list[str]) -> list[list[str]]:
    actions: list[list[str]] = []
    current: list[str] = []

    for index, token in enumerate(tokens):
        normalized = normalize_token(token)
        if current and normalized == "depois":
            if current and normalize_token(current[-1]) == "e":
                current.pop()
            actions.append(current)
            current = []
            continue
        if current and normalized == "e":
            next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
            if next_token and is_command_token(normalize_token(next_token)):
                actions.append(current)
                current = []
                continue
        current.append(token)

    if current:
        actions.append(current)

    return actions or [tokens]

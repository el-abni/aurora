from __future__ import annotations

from aurora.contracts.requests import PreparedAction

PACKAGE_DOMAIN_NOISE_TOKENS = {
    "a",
    "app",
    "aplicacao",
    "aplicativo",
    "aplicativos",
    "as",
    "o",
    "os",
    "pacote",
    "pacotes",
    "programa",
    "programas",
    "um",
    "uma",
    "uns",
    "umas",
}


def extract_target_token_pairs(action: PreparedAction) -> list[tuple[str, str]]:
    start = 1
    while start < len(action.normalized_tokens):
        token = action.normalized_tokens[start]
        if token not in PACKAGE_DOMAIN_NOISE_TOKENS:
            break
        start += 1
    return list(zip(action.original_tokens[start:], action.normalized_tokens[start:]))


def extract_package_target(action: PreparedAction) -> str:
    return " ".join(original for original, _normalized in extract_target_token_pairs(action)).strip()

from __future__ import annotations

from aurora.contracts.requests import PreparedAction

_PACKAGE_DOMAIN_NOISE_TOKENS = {
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


def extract_package_target(action: PreparedAction) -> str:
    start = 1
    while start < len(action.normalized_tokens):
        token = action.normalized_tokens[start]
        if token not in _PACKAGE_DOMAIN_NOISE_TOKENS:
            break
        start += 1
    return " ".join(action.original_tokens[start:]).strip()

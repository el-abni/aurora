from __future__ import annotations

ALIASES = {
    "procure": "procurar",
    "buscar": "procurar",
    "busque": "procurar",
    "instale": "instalar",
    "remova": "remover",
    "apagar": "remover",
    "apague": "remover",
}

KNOWN_INTENTS = {"ajuda", "dev", "procurar", "instalar", "remover"}


def canonicalize_intent(token: str) -> str:
    normalized = ALIASES.get(token, token)
    return normalized


def is_command_token(token: str) -> bool:
    return canonicalize_intent(token) in KNOWN_INTENTS

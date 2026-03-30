from __future__ import annotations

from aurora.contracts.requests import SemanticRequest
from aurora.semantics.entities import extract_package_target
from aurora.semantics.intent import canonicalize_intent
from aurora.semantics.pipeline import prepare_text


def classify_text(text: str) -> SemanticRequest:
    phrase, actions = prepare_text(text)
    if not actions:
        return SemanticRequest(
            original_text=text.strip(),
            normalized_text=phrase.normalized_text,
            intent="desconhecida",
            domain_kind="unknown",
            status="OUT_OF_SCOPE",
            reason="nao consegui identificar uma acao valida.",
            action_count=0,
        )

    if len(actions) != 1:
        return SemanticRequest(
            original_text=phrase.original_text,
            normalized_text=phrase.normalized_text,
            intent="sequencia",
            domain_kind="unknown",
            status="OUT_OF_SCOPE",
            reason="esta rodada aceita uma acao por vez, mesmo que o split ja exista.",
            observations=("sequencias ficaram para depois",),
            action_count=len(actions),
        )

    action = actions[0]
    first_token = action.normalized_tokens[0] if action.normalized_tokens else ""
    intent = canonicalize_intent(first_token)

    if intent in {"procurar", "instalar", "remover"}:
        target = extract_package_target(action)
        if not target:
            return SemanticRequest(
                original_text=action.original_action,
                normalized_text=action.normalized_action,
                intent=intent,
                domain_kind="host_package",
                status="BLOCKED",
                reason="faltou o alvo do pacote do host.",
            )
        return SemanticRequest(
            original_text=action.original_action,
            normalized_text=action.normalized_action,
            intent=intent,
            domain_kind="host_package",
            target=target,
            status="CONSISTENT",
            reason="pedido enquadrado no dominio host_package.",
        )

    return SemanticRequest(
        original_text=action.original_action,
        normalized_text=action.normalized_action,
        intent=intent or "desconhecida",
        domain_kind="unknown",
        status="OUT_OF_SCOPE",
        reason="o pedido ficou fora do recorte aberto desta rodada.",
    )

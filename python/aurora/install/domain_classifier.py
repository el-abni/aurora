from __future__ import annotations

from aurora.contracts.requests import SemanticRequest
from aurora.semantics.entities import extract_package_target, extract_target_token_pairs
from aurora.semantics.intent import canonicalize_intent
from aurora.semantics.pipeline import prepare_text

_FLATPAK_HINT_TOKENS = {"flatpak", "flathub"}
_AUR_HINT_TOKENS = {"aur"}
_SOURCE_PREPOSITIONS = {"com", "do", "da", "em", "na", "no", "pela", "pelo", "usando", "via"}


def _extract_source_target(action, *, hint_tokens: set[str]) -> str:
    pairs = extract_target_token_pairs(action)
    if not pairs:
        return ""

    while len(pairs) >= 2 and pairs[0][1] in _SOURCE_PREPOSITIONS and pairs[1][1] in hint_tokens:
        pairs = pairs[2:]

    if pairs and pairs[0][1] in hint_tokens:
        pairs = pairs[1:]

    if len(pairs) >= 2 and pairs[-2][1] in _SOURCE_PREPOSITIONS and pairs[-1][1] in hint_tokens:
        pairs = pairs[:-2]
    elif pairs and pairs[-1][1] in hint_tokens:
        pairs = pairs[:-1]

    return " ".join(original for original, _normalized in pairs).strip()


def _source_hint(action, *, hint_tokens: set[str]) -> str | None:
    pairs = extract_target_token_pairs(action)
    for index in range(len(pairs) - 1):
        if pairs[index][1] in _SOURCE_PREPOSITIONS and pairs[index + 1][1] in hint_tokens:
            return pairs[index + 1][1]
    return None


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
        requested_source = ""
        flatpak_hint = _source_hint(action, hint_tokens=_FLATPAK_HINT_TOKENS)
        if flatpak_hint is not None:
            target = _extract_source_target(action, hint_tokens=_FLATPAK_HINT_TOKENS)
            observations = ("domain_selection:explicit_user_software", f"source_hint:{flatpak_hint}")
            domain_kind = "user_software"
            requested_source = "flatpak"
            missing_target_reason = "faltou o alvo do software do usuario marcado via flatpak."
            consistent_reason = (
                f"pedido explicitamente marcado como '{flatpak_hint}', entao foi enquadrado em user_software."
            )
        else:
            aur_hint = _source_hint(action, hint_tokens=_AUR_HINT_TOKENS)
            if aur_hint is not None:
                target = _extract_source_target(action, hint_tokens=_AUR_HINT_TOKENS)
                observations = ("domain_selection:explicit_host_package_source", f"source_hint:{aur_hint}")
                domain_kind = "host_package"
                requested_source = "aur"
                missing_target_reason = "faltou o alvo do pacote do host marcado via aur."
                consistent_reason = (
                    "pedido explicitamente marcado como 'aur', entao foi enquadrado em host_package "
                    "com fonte separada AUR."
                )
            else:
                target = extract_package_target(action)
                observations = ("domain_selection:default_host_package",)
                domain_kind = "host_package"
                missing_target_reason = "faltou o alvo do pacote do host."
                consistent_reason = "pedido enquadrado no dominio host_package por default seguro desta rodada."

        if not target:
            return SemanticRequest(
                original_text=action.original_action,
                normalized_text=action.normalized_action,
                intent=intent,
                domain_kind=domain_kind,
                requested_source=requested_source,
                status="BLOCKED",
                reason=missing_target_reason,
                observations=observations,
            )
        return SemanticRequest(
            original_text=action.original_action,
            normalized_text=action.normalized_action,
            intent=intent,
            domain_kind=domain_kind,
            requested_source=requested_source,
            target=target,
            status="CONSISTENT",
            reason=consistent_reason,
            observations=observations,
        )

    return SemanticRequest(
        original_text=action.original_action,
        normalized_text=action.normalized_action,
        intent=intent or "desconhecida",
        domain_kind="unknown",
        status="OUT_OF_SCOPE",
        reason="o pedido ficou fora do recorte aberto desta rodada.",
    )

from __future__ import annotations

from dataclasses import dataclass
import re

from aurora.contracts.requests import SemanticRequest
from aurora.semantics.entities import extract_package_target, extract_target_token_pairs
from aurora.semantics.intent import canonicalize_intent
from aurora.semantics.pipeline import prepare_text

_FLATPAK_HINT_TOKENS = {"flatpak", "flathub"}
_AUR_HINT_TOKENS = {"aur"}
_COPR_HINT_TOKENS = {"copr"}
_SOURCE_PREPOSITIONS = {"com", "do", "da", "em", "na", "no", "pela", "pelo", "usando", "via"}
_COPR_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class _CoprSelection:
    target: str = ""
    source_coordinate: str = ""
    hint_found: bool = False
    reason: str = ""


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


def _looks_like_copr_repository(token: str) -> bool:
    return _COPR_REPOSITORY_RE.fullmatch(token.strip()) is not None


def _extract_copr_selection(action) -> _CoprSelection:
    pairs = extract_target_token_pairs(action)
    for index in range(1, len(pairs)):
        if pairs[index - 1][1] not in _SOURCE_PREPOSITIONS or pairs[index][1] not in _COPR_HINT_TOKENS:
            continue

        target_pairs = pairs[: index - 1]
        repository_pairs = pairs[index + 1 :]
        if not target_pairs:
            return _CoprSelection(
                hint_found=True,
                reason="faltou o alvo do pacote do host marcado via copr.",
            )
        if len(repository_pairs) != 1:
            return _CoprSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                hint_found=True,
                reason=(
                    "faltou a coordenada explicita do repositório COPR no formato owner/project."
                ),
            )

        repository_original, repository_normalized = repository_pairs[0]
        if not _looks_like_copr_repository(repository_normalized):
            return _CoprSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                hint_found=True,
                reason=(
                    "a coordenada do repositório COPR precisa ser explicita e conservadora "
                    "no formato owner/project."
                ),
            )

        return _CoprSelection(
            target=" ".join(original for original, _normalized in target_pairs).strip(),
            source_coordinate=repository_original,
            hint_found=True,
        )

    return _CoprSelection()


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
        source_coordinate = ""
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
            copr_selection = _extract_copr_selection(action)
            if copr_selection.hint_found:
                target = copr_selection.target
                source_coordinate = copr_selection.source_coordinate
                observations = (
                    "domain_selection:explicit_host_package_source",
                    "source_hint:copr",
                    f"copr_repo:{source_coordinate}" if source_coordinate else "copr_repo:-",
                )
                domain_kind = "host_package"
                requested_source = "copr"
                missing_target_reason = copr_selection.reason or "faltou o alvo do pacote do host marcado via copr."
                consistent_reason = (
                    "pedido explicitamente marcado como 'copr', entao foi enquadrado em host_package "
                    "com fonte separada COPR e repositório explicito."
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
                source_coordinate=source_coordinate,
                status="BLOCKED",
                reason=missing_target_reason,
                observations=observations,
            )
        if requested_source == "copr" and not source_coordinate:
            return SemanticRequest(
                original_text=action.original_action,
                normalized_text=action.normalized_action,
                intent=intent,
                domain_kind=domain_kind,
                requested_source=requested_source,
                source_coordinate=source_coordinate,
                target=target,
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
            source_coordinate=source_coordinate,
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

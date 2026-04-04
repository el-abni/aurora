from __future__ import annotations

from dataclasses import dataclass
import re

from aurora.contracts.requests import SemanticRequest
from aurora.install.sources.flatpak import flatpak_remote_name_is_explicit
from aurora.install.sources.ppa import ppa_coordinate_is_explicit
from aurora.semantics.entities import extract_package_target, extract_target_token_pairs
from aurora.semantics.intent import canonicalize_intent
from aurora.semantics.pipeline import prepare_text

_FLATPAK_HINT_TOKENS = {"flatpak", "flathub"}
_AUR_HINT_TOKENS = {"aur"}
_COPR_HINT_TOKENS = {"copr"}
_PPA_HINT_TOKENS = {"ppa"}
_SOURCE_PREPOSITIONS = {"com", "do", "da", "em", "na", "no", "pela", "pelo", "usando", "via"}
_COPR_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class _CoprSelection:
    target: str = ""
    source_coordinate: str = ""
    hint_found: bool = False
    reason: str = ""


@dataclass(frozen=True)
class _PpaSelection:
    target: str = ""
    source_coordinate: str = ""
    hint_found: bool = False
    reason: str = ""


@dataclass(frozen=True)
class _FlatpakSelection:
    target: str = ""
    source_coordinate: str = ""
    hint_found: bool = False
    reason: str = ""
    hint_token: str = ""
    source_coordinate_required: bool = False


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


def _extract_ppa_selection(action) -> _PpaSelection:
    pairs = extract_target_token_pairs(action)
    for index in range(1, len(pairs)):
        if pairs[index - 1][1] not in _SOURCE_PREPOSITIONS or pairs[index][1] not in _PPA_HINT_TOKENS:
            continue

        target_pairs = pairs[: index - 1]
        coordinate_pairs = pairs[index + 1 :]
        if not target_pairs:
            return _PpaSelection(
                hint_found=True,
                reason="faltou o alvo do pacote do host marcado via ppa.",
            )
        if len(coordinate_pairs) != 1:
            return _PpaSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                hint_found=True,
                reason="faltou a coordenada explicita do PPA no formato canonico ppa:owner/name.",
            )

        coordinate_original, coordinate_normalized = coordinate_pairs[0]
        if not ppa_coordinate_is_explicit(coordinate_normalized):
            return _PpaSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                hint_found=True,
                reason=(
                    "a coordenada do PPA precisa ser explicita e conservadora "
                    "no formato canonico ppa:owner/name."
                ),
            )

        return _PpaSelection(
            target=" ".join(original for original, _normalized in target_pairs).strip(),
            source_coordinate=coordinate_original,
            hint_found=True,
        )

    return _PpaSelection()


def _extract_flatpak_selection(action) -> _FlatpakSelection:
    pairs = extract_target_token_pairs(action)
    for index in range(1, len(pairs)):
        if pairs[index - 1][1] not in _SOURCE_PREPOSITIONS or pairs[index][1] not in _FLATPAK_HINT_TOKENS:
            continue

        target_pairs = pairs[: index - 1]
        remote_pairs = pairs[index + 1 :]
        hint_original, hint_normalized = pairs[index]
        if not target_pairs:
            return _FlatpakSelection(
                hint_found=True,
                hint_token=hint_normalized,
                reason="faltou o alvo do software do usuario marcado via flatpak.",
            )

        if hint_normalized == "flathub":
            if remote_pairs:
                return _FlatpakSelection(
                    target=" ".join(original for original, _normalized in target_pairs).strip(),
                    hint_found=True,
                    hint_token=hint_normalized,
                    reason=(
                        "o remote Flatpak explicito desta rodada precisa ser um nome unico e conservador, "
                        "sem argumentos extras apos o hint."
                    ),
                    source_coordinate_required=True,
                )
            return _FlatpakSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                source_coordinate=hint_original,
                hint_found=True,
                hint_token=hint_normalized,
            )

        if not remote_pairs:
            return _FlatpakSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                hint_found=True,
                hint_token=hint_normalized,
            )
        if len(remote_pairs) != 1:
            return _FlatpakSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                hint_found=True,
                hint_token=hint_normalized,
                reason=(
                    "o remote Flatpak explicito desta rodada precisa ser um nome unico e conservador, "
                    "sem parsing amplo de argumentos."
                ),
                source_coordinate_required=True,
            )

        remote_original, remote_normalized = remote_pairs[0]
        if not flatpak_remote_name_is_explicit(remote_normalized):
            return _FlatpakSelection(
                target=" ".join(original for original, _normalized in target_pairs).strip(),
                hint_found=True,
                hint_token=hint_normalized,
                reason=(
                    "o remote Flatpak explicito precisa ser um nome unico, conservador e ja observavel "
                    "no host, sem URL nem coordenada ampla."
                ),
                source_coordinate_required=True,
            )

        return _FlatpakSelection(
            target=" ".join(original for original, _normalized in target_pairs).strip(),
            source_coordinate=remote_original,
            hint_found=True,
            hint_token=hint_normalized,
        )

    return _FlatpakSelection()


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
        source_coordinate_required = False
        flatpak_selection = _extract_flatpak_selection(action)
        if flatpak_selection.hint_found:
            target = flatpak_selection.target
            source_coordinate = flatpak_selection.source_coordinate
            source_coordinate_required = flatpak_selection.source_coordinate_required
            observations = tuple(
                item
                for item in (
                    "domain_selection:explicit_user_software",
                    f"source_hint:{flatpak_selection.hint_token or 'flatpak'}",
                    (
                        f"flatpak_requested_remote:{source_coordinate}"
                        if source_coordinate
                        else "flatpak_requested_remote:-"
                    ),
                )
                if item
            )
            domain_kind = "user_software"
            requested_source = "flatpak"
            missing_target_reason = (
                flatpak_selection.reason or "faltou o alvo do software do usuario marcado via flatpak."
            )
            consistent_reason = (
                (
                    "pedido explicitamente marcado como 'flatpak', com remote explicito, "
                    "entao foi enquadrado em user_software."
                )
                if source_coordinate
                else (
                    f"pedido explicitamente marcado como '{flatpak_selection.hint_token or 'flatpak'}', "
                    "entao foi enquadrado em user_software."
                )
            )
        else:
            ppa_selection = _extract_ppa_selection(action)
            if ppa_selection.hint_found:
                target = ppa_selection.target
                source_coordinate = ppa_selection.source_coordinate
                observations = (
                    "domain_selection:explicit_host_package_source",
                    "source_hint:ppa",
                    f"ppa_coordinate:{source_coordinate}" if source_coordinate else "ppa_coordinate:-",
                )
                domain_kind = "host_package"
                requested_source = "ppa"
                missing_target_reason = ppa_selection.reason or "faltou o alvo do pacote do host marcado via ppa."
                consistent_reason = (
                    "pedido explicitamente marcado como 'ppa', entao foi enquadrado em host_package "
                    "com fonte separada PPA e coordenada explicita."
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
        if requested_source == "flatpak" and source_coordinate_required and not source_coordinate:
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
        if requested_source in {"copr", "ppa"} and not source_coordinate:
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

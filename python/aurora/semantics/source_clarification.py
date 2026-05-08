from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aurora.semantics.normalize import normalize_token, preprocess_text


class SourceClarificationKind(Enum):
    EXPLAIN_SOURCES = "explain_sources"
    EXPLAIN_SURFACES = "explain_surfaces"
    EXPLAIN_FLATPAK_REMOTE = "explain_flatpak_remote"
    CHOOSE_SOURCE = "choose_source"
    CHOOSE_FLATPAK_REMOTE = "choose_flatpak_remote"
    WHERE_INSTALL = "where_install"
    INSTALL_FLATPAK = "install_flatpak"
    INSTALL_FLATPAK_REMOTE = "install_flatpak_remote"
    SEARCH_FLATPAK_REMOTE = "search_flatpak_remote"
    INSTALL_AUR = "install_aur"
    INSTALL_TOOLBOX = "install_toolbox"
    INSTALL_DISTROBOX = "install_distrobox"
    INSTALL_RPM_OSTREE = "install_rpm_ostree"
    COMPARE_HOST_FLATPAK = "compare_host_flatpak"
    COMPARE_AUR_HOST = "compare_aur_host"
    BLOCK_AUTOMATIC_SOURCE_CHOICE = "block_automatic_source_choice"
    BLOCK_FLATPAK_REMOTE_CHOICE = "block_flatpak_remote_choice"
    BLOCK_FLATPAK_REMOTE_ADD = "block_flatpak_remote_add"
    BLOCK_FLATPAK_REMOTE_ALL = "block_flatpak_remote_all"


@dataclass(frozen=True)
class SourceClarificationRequest:
    kind: SourceClarificationKind
    target: str = ""
    environment: str = ""
    remote: str = ""
    blocking: bool = False


def _normalized_parts(text: str) -> list[tuple[str, str]]:
    return [
        (part.strip().strip(",.;:!?"), normalize_token(part))
        for part in preprocess_text(text).split()
        if part.strip()
    ]


def _normalized_text(parts: list[tuple[str, str]]) -> str:
    return " ".join(normalized for _original, normalized in parts).strip()


def _target_text(parts: list[tuple[str, str]]) -> str:
    return " ".join(original for original, _normalized in parts).strip()


def _match_marked_install(
    parts: list[tuple[str, str]],
) -> SourceClarificationRequest | None:
    if len(parts) < 5 or [normalized for _original, normalized in parts[:2]] != ["como", "instalar"]:
        return None

    normalized = [normalized for _original, normalized in parts]
    trailing_markers: tuple[tuple[list[str], SourceClarificationKind], ...] = (
        (["no", "flatpak"], SourceClarificationKind.INSTALL_FLATPAK),
        (["no", "aur"], SourceClarificationKind.INSTALL_AUR),
        (["no", "rpm-ostree"], SourceClarificationKind.INSTALL_RPM_OSTREE),
    )
    for marker, kind in trailing_markers:
        if normalized[-len(marker) :] == marker:
            target = _target_text(parts[2 : -len(marker)])
            if target:
                return SourceClarificationRequest(kind=kind, target=target)

    if len(parts) >= 6 and normalized[-3:-1] == ["na", "toolbox"] and normalized[-1]:
        target = _target_text(parts[2:-3])
        if target:
            return SourceClarificationRequest(
                kind=SourceClarificationKind.INSTALL_TOOLBOX,
                target=target,
                environment=parts[-1][0],
            )

    if len(parts) >= 6 and normalized[-3:-1] == ["na", "distrobox"] and normalized[-1]:
        target = _target_text(parts[2:-3])
        if target:
            return SourceClarificationRequest(
                kind=SourceClarificationKind.INSTALL_DISTROBOX,
                target=target,
                environment=parts[-1][0],
            )

    return None


def _match_flatpak_remote_action(
    parts: list[tuple[str, str]],
) -> SourceClarificationRequest | None:
    if len(parts) < 6 or parts[0][1] != "como":
        return None

    action = parts[1][1]
    kind_by_action = {
        "instalar": SourceClarificationKind.INSTALL_FLATPAK_REMOTE,
        "procurar": SourceClarificationKind.SEARCH_FLATPAK_REMOTE,
    }
    kind = kind_by_action.get(action)
    if kind is None:
        return None

    normalized = [normalized for _original, normalized in parts]
    if len(parts) >= 6 and normalized[-3:-1] == ["no", "flatpak"]:
        target = _target_text(parts[2:-3])
        remote = parts[-1][0]
        if target and remote:
            return SourceClarificationRequest(kind=kind, target=target, remote=remote)

    if len(parts) >= 5 and normalized[-2] == "no" and normalized[-1] == "flathub":
        target = _target_text(parts[2:-2])
        if target:
            return SourceClarificationRequest(kind=kind, target=target, remote=parts[-1][0])

    return None


def _target_after_token(parts: list[tuple[str, str]], token: str) -> str:
    for index, (_original, normalized) in enumerate(parts):
        if normalized == token:
            return _target_text(parts[index + 1 :])
    return ""


def _target_before_token(parts: list[tuple[str, str]], token: str, *, start: int = 0) -> str:
    for index, (_original, normalized) in enumerate(parts[start:], start=start):
        if normalized == token:
            return _target_text(parts[start:index])
    return _target_text(parts[start:])


def _match_flatpak_remote_guidance(
    parts: list[tuple[str, str]],
) -> SourceClarificationRequest | None:
    normalized = [normalized for _original, normalized in parts]
    normalized_text = _normalized_text(parts)

    exact_explain = {
        "explicar remote flatpak",
        "explicar remotes flatpak",
        "onde entra o flathub",
        "flatpak usa flathub",
    }
    if normalized_text in exact_explain:
        return SourceClarificationRequest(kind=SourceClarificationKind.EXPLAIN_FLATPAK_REMOTE)

    if {"flatpak", "remote"}.issubset(normalized) and "melhor" in normalized:
        return SourceClarificationRequest(
            kind=SourceClarificationKind.BLOCK_FLATPAK_REMOTE_CHOICE,
            target=_target_after_token(parts, "para"),
            blocking=True,
        )

    if "flatpak" in normalized and (
        normalized[:2] == ["adicionar", "remote"] or "remote-add" in normalized
    ):
        return SourceClarificationRequest(
            kind=SourceClarificationKind.BLOCK_FLATPAK_REMOTE_ADD,
            remote=parts[-1][0] if len(parts) >= 3 else "",
            blocking=True,
        )

    if "flatpak" in normalized and "procurar" in normalized and "todos" in normalized:
        remote_words = {"remote", "remotes"}
        if any(word in normalized for word in remote_words):
            return SourceClarificationRequest(
                kind=SourceClarificationKind.BLOCK_FLATPAK_REMOTE_ALL,
                target=_target_before_token(parts, "em", start=1),
                blocking=True,
            )

    if normalized_text == "como escolher remote flatpak":
        return SourceClarificationRequest(kind=SourceClarificationKind.CHOOSE_FLATPAK_REMOTE)

    if len(parts) >= 5 and normalized[:4] == ["como", "escolher", "remote", "flatpak"]:
        return SourceClarificationRequest(
            kind=SourceClarificationKind.CHOOSE_FLATPAK_REMOTE,
            target=_target_after_token(parts, "para"),
        )

    if len(parts) >= 6 and normalized[:4] == ["qual", "remote", "flatpak", "usar"]:
        return SourceClarificationRequest(
            kind=SourceClarificationKind.CHOOSE_FLATPAK_REMOTE,
            target=_target_after_token(parts, "para"),
        )

    return None


def _match_automatic_choice_block(
    parts: list[tuple[str, str]],
) -> SourceClarificationRequest | None:
    if len(parts) < 5 or parts[0][1] != "instalar":
        return None

    normalized = [normalized for _original, normalized in parts]
    blocked_suffixes = (
        ["onde", "for", "melhor"],
        ["na", "melhor", "fonte"],
        ["na", "melhor", "superficie"],
    )
    for suffix in blocked_suffixes:
        if normalized[-len(suffix) :] == suffix:
            target = _target_text(parts[1 : -len(suffix)])
            if target:
                return SourceClarificationRequest(
                    kind=SourceClarificationKind.BLOCK_AUTOMATIC_SOURCE_CHOICE,
                    target=target,
                    blocking=True,
                )

    return None


def parse_source_clarification(text: str) -> SourceClarificationRequest | None:
    parts = _normalized_parts(text)
    normalized = _normalized_text(parts)

    exact_matches = {
        "explicar fontes": SourceClarificationKind.EXPLAIN_SOURCES,
        "explicar superficies": SourceClarificationKind.EXPLAIN_SURFACES,
        "diferenca entre host e flatpak": SourceClarificationKind.COMPARE_HOST_FLATPAK,
        "diferenca entre aur e pacote do host": SourceClarificationKind.COMPARE_AUR_HOST,
    }
    exact = exact_matches.get(normalized)
    if exact is not None:
        return SourceClarificationRequest(kind=exact)

    flatpak_remote_guidance = _match_flatpak_remote_guidance(parts)
    if flatpak_remote_guidance is not None:
        return flatpak_remote_guidance

    blocked = _match_automatic_choice_block(parts)
    if blocked is not None:
        return blocked

    flatpak_remote_action = _match_flatpak_remote_action(parts)
    if flatpak_remote_action is not None:
        return flatpak_remote_action

    marked_install = _match_marked_install(parts)
    if marked_install is not None:
        return marked_install

    normalized_parts = [normalized_part for _original, normalized_part in parts]
    if len(parts) >= 5 and normalized_parts[:4] == ["como", "escolher", "fonte", "para"]:
        target = _target_text(parts[4:])
        if target:
            return SourceClarificationRequest(kind=SourceClarificationKind.CHOOSE_SOURCE, target=target)

    if len(parts) >= 5 and normalized_parts[:4] == ["qual", "fonte", "usar", "para"]:
        target = _target_text(parts[4:])
        if target:
            return SourceClarificationRequest(kind=SourceClarificationKind.CHOOSE_SOURCE, target=target)

    if len(parts) >= 3 and normalized_parts[:2] == ["onde", "instalar"]:
        target = _target_text(parts[2:])
        if target:
            return SourceClarificationRequest(kind=SourceClarificationKind.WHERE_INSTALL, target=target)

    return None

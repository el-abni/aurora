from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aurora.semantics.normalize import normalize_token, preprocess_text


class SourceClarificationKind(Enum):
    EXPLAIN_SOURCES = "explain_sources"
    EXPLAIN_SURFACES = "explain_surfaces"
    CHOOSE_SOURCE = "choose_source"
    WHERE_INSTALL = "where_install"
    INSTALL_FLATPAK = "install_flatpak"
    INSTALL_AUR = "install_aur"
    INSTALL_TOOLBOX = "install_toolbox"
    INSTALL_DISTROBOX = "install_distrobox"
    INSTALL_RPM_OSTREE = "install_rpm_ostree"
    COMPARE_HOST_FLATPAK = "compare_host_flatpak"
    COMPARE_AUR_HOST = "compare_aur_host"
    BLOCK_AUTOMATIC_SOURCE_CHOICE = "block_automatic_source_choice"


@dataclass(frozen=True)
class SourceClarificationRequest:
    kind: SourceClarificationKind
    target: str = ""
    environment: str = ""
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

    blocked = _match_automatic_choice_block(parts)
    if blocked is not None:
        return blocked

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

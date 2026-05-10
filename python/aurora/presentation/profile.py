from __future__ import annotations

from enum import Enum
from typing import Iterable


class PresentationProfile(str, Enum):
    DIRECT = "direct"
    EXPLANATORY = "explanatory"
    BEGINNER = "beginner"


ProfileInput = PresentationProfile | str | None

DEFAULT_PRESENTATION_PROFILE = PresentationProfile.EXPLANATORY


def normalize_profile(profile: ProfileInput = None) -> PresentationProfile:
    if profile is None:
        return DEFAULT_PRESENTATION_PROFILE
    if isinstance(profile, PresentationProfile):
        return profile
    try:
        return PresentationProfile(profile.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in PresentationProfile)
        raise ValueError(f"perfil de apresentação inválido: {profile!r}; use {allowed}") from exc


def _clean_items(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(item.strip().rstrip(".") for item in items if item.strip())


def _bullet_list(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item};" for item in items)


def render_profiled_response(
    summary: str,
    *,
    steps: Iterable[str] = (),
    limits: Iterable[str] = (),
    note: str = "",
    profile: ProfileInput = None,
) -> str:
    selected = normalize_profile(profile)
    clean_steps = _clean_items(steps)
    clean_limits = _clean_items(limits)
    sections = [summary.strip()]

    if clean_steps:
        if selected is PresentationProfile.DIRECT:
            sections.append("Use: " + " | ".join(clean_steps) + ".")
        elif selected is PresentationProfile.BEGINNER:
            sections.append("Caminho seguro:\n" + _bullet_list(clean_steps))
        else:
            sections.append("Como pedir:\n" + _bullet_list(clean_steps))

    if clean_limits:
        if selected is PresentationProfile.DIRECT:
            sections.append("Limites: " + "; ".join(clean_limits) + ".")
        elif selected is PresentationProfile.BEGINNER:
            sections.append("O que a Aurora não faz nesta resposta:\n" + _bullet_list(clean_limits))
        else:
            sections.append("Limites preservados: " + "; ".join(clean_limits) + ".")

    if note.strip():
        sections.append(note.strip())

    return "\n".join(sections)

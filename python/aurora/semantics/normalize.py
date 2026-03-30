from __future__ import annotations

import re
import unicodedata

_CORRECTIONS = {
    "vc": "voce",
    "vcs": "voces",
    "ce": "voce",
    "c": "voce",
    "q": "que",
    "ta": "esta",
    "tb": "tambem",
    "tbm": "tambem",
    "mosta": "mostrar",
    "mosra": "mostrar",
    "ve": "ver",
    "vee": "ver",
    "instalaa": "instalar",
}


def strip_accents(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn"
    )


def normalize_token(token: str) -> str:
    lowered = strip_accents(token.strip().strip(",.;:!?")).lower()
    return _CORRECTIONS.get(lowered, lowered)


def preprocess_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    cleaned = re.sub(r"^(aurora|auro)\s*,\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def tokenize(text: str) -> list[str]:
    prepared = preprocess_text(text)
    return [normalize_token(part) for part in prepared.split() if part.strip()]


def normalized_text(text: str) -> str:
    return " ".join(tokenize(text))

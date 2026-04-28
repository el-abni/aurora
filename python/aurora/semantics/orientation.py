from __future__ import annotations

from dataclasses import dataclass

from aurora.semantics.normalize import normalize_token, preprocess_text


TOPIC_EXAMPLES = "exemplos"
TOPIC_LIMITS = "limites"
TOPIC_COMMANDS = "comandos"
TOPIC_SOURCES = "fontes"
TOPIC_LOCAL_MODEL = "modelo_local"
TOPIC_DECISION_RECORD = "decision_record"
TOPIC_PRODUCT = "o_que_voce_faz"
TOPIC_USAGE = "como_eu_uso"

QUESTION_INSTALL = "como_instalar"
QUESTION_SEARCH = "como_procurar"
QUESTION_REMOVE = "como_remover"
QUESTION_UPDATE_SYSTEM = "como_atualizar_sistema"

_TOPICS_BY_NORMALIZED_TEXT = {
    "exemplos": TOPIC_EXAMPLES,
    "limites": TOPIC_LIMITS,
    "comandos": TOPIC_COMMANDS,
    "fontes": TOPIC_SOURCES,
    "modelo local": TOPIC_LOCAL_MODEL,
    "decision record": TOPIC_DECISION_RECORD,
    "o que voce faz": TOPIC_PRODUCT,
    "como eu uso": TOPIC_USAGE,
}

_QUESTION_ACTIONS = {
    "instalar": QUESTION_INSTALL,
    "procurar": QUESTION_SEARCH,
    "remover": QUESTION_REMOVE,
}


@dataclass(frozen=True)
class OrientationRequest:
    topic: str
    target: str = ""


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


def parse_orientation(text: str) -> OrientationRequest | None:
    parts = _normalized_parts(text)
    normalized = _normalized_text(parts)
    topic = _TOPICS_BY_NORMALIZED_TEXT.get(normalized)
    if topic is not None:
        return OrientationRequest(topic=topic)

    if not parts or parts[0][1] != "como":
        return None

    if len(parts) == 3 and parts[1][1] == "atualizar" and parts[2][1] == "sistema":
        return OrientationRequest(topic=QUESTION_UPDATE_SYSTEM, target=parts[2][0])

    if len(parts) < 3:
        return None

    question_topic = _QUESTION_ACTIONS.get(parts[1][1])
    if question_topic is None:
        return None

    target = _target_text(parts[2:])
    if not target:
        return None
    return OrientationRequest(topic=question_topic, target=target)

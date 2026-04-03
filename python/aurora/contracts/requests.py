from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProtectedToken:
    placeholder: str
    value: str
    token_type: str


@dataclass
class InputPhrase:
    original_tokens: list[str] = field(default_factory=list)
    protected_tokens: list[ProtectedToken] = field(default_factory=list)
    corrected_tokens: list[str] = field(default_factory=list)
    normalized_tokens: list[str] = field(default_factory=list)
    normalized_display_tokens: list[str] = field(default_factory=list)

    @property
    def original_text(self) -> str:
        return " ".join(self.original_tokens).strip()

    @property
    def normalized_text(self) -> str:
        return " ".join(self.normalized_display_tokens).strip()


@dataclass
class PreparedAction:
    index: int
    original_tokens: list[str] = field(default_factory=list)
    corrected_tokens: list[str] = field(default_factory=list)
    normalized_tokens: list[str] = field(default_factory=list)
    normalized_display_tokens: list[str] = field(default_factory=list)

    @property
    def original_action(self) -> str:
        return " ".join(self.original_tokens).strip()

    @property
    def normalized_action(self) -> str:
        return " ".join(self.normalized_display_tokens).strip()


@dataclass(frozen=True)
class SemanticRequest:
    original_text: str
    normalized_text: str
    intent: str
    domain_kind: str
    requested_source: str = ""
    source_coordinate: str = ""
    target: str = ""
    status: str = "OUT_OF_SCOPE"
    reason: str = ""
    observations: tuple[str, ...] = ()
    action_count: int = 1

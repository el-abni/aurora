from __future__ import annotations

__all__ = ["build_input_phrase", "prepare_text"]


def __getattr__(name: str):
    if name in __all__:
        from .pipeline import build_input_phrase, prepare_text

        values = {
            "build_input_phrase": build_input_phrase,
            "prepare_text": prepare_text,
        }
        return values[name]
    raise AttributeError(f"module 'aurora.semantics' has no attribute {name!r}")

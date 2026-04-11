#!/usr/bin/env python3
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.lower().split())


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def assert_workflow_doc() -> None:
    path = "docs/WORKFLOW_DE_TESTES_E_RELEASE.md"
    text = read(path)
    normalized = normalize(text)
    ensure(VERSION in text, f"{path} precisa refletir a release atual")
    for term in (
        "teste automatico",
        "revisao e teste manual",
        "terminal local",
        "tests/release_gate_iteracao.sh",
        "tests/release_gate_pre_push.sh",
        "tests/release_gate_pre_release.sh",
        "tests/release_gate_canonic_line.sh",
        "tests/release_gate_v0_6_2.sh",
        "tests/REVIEW_CHECKLIST.md",
        "commit",
        "push",
        "tag",
        "release",
        "aurora --version",
        "aurora --help",
        "aurora dev",
    ):
        ensure(term in text or term in normalized, f"{path} precisa citar {term}")
    ok(f"{path} alinhado")


def assert_review_checklist() -> None:
    path = "tests/REVIEW_CHECKLIST.md"
    text = read(path)
    normalized = normalize(text)
    for term in (
        VERSION,
        "VERSION",
        "README.md",
        "CHANGELOG.md",
        "resources/help.txt",
        "docs/ARCHITECTURE.md",
        "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
        "tests/README.md",
        "aurora --version",
        "aurora --help",
        "aurora dev",
        "caso feliz",
        "caso ruim",
        "terminal real",
        "release_gate_pre_push.sh",
        "release_gate_pre_release.sh",
    ):
        ensure(term in text or term in normalized, f"{path} precisa citar {term}")
    ok(f"{path} alinhado")


def assert_gate(path: str, terms: tuple[str, ...], ok_marker: str) -> None:
    text = read(path)
    normalized = normalize(text)
    ensure("fish" not in normalized, f"{path} nao pode depender de Fish")
    ensure("stage publica" not in normalized and "staging" not in normalized, f"{path} nao pode depender de stage publica")
    for term in terms:
        ensure(term in text, f"{path} precisa citar {term}")
    ensure(ok_marker in text, f"{path} precisa imprimir {ok_marker}")
    ok(f"{path} alinhado")


def main() -> int:
    ensure(re.fullmatch(r"v\d+\.\d+\.\d+", VERSION) is not None, "VERSION precisa estar em formato de release")
    assert_workflow_doc()
    assert_review_checklist()
    assert_gate(
        "tests/release_gate_iteracao.sh",
        (
            "git diff --check",
            "tests/audit_decision_record_contract.py",
            "tests/audit_factual_hotspots.py",
            "tests/audit_factual_baseline.py",
            "tests/audit_observability_canonical_facts.py",
            "tests/audit_local_model_eval_baseline.py",
            "test_bootstrap_smoke.py",
            "test_installer_release.py",
            "test_decision_record.py",
        ),
        "release_gate_iteracao: ok",
    )
    assert_gate(
        "tests/release_gate_pre_push.sh",
        (
            "git diff --check",
            "tests/release_gate_canonic_line.sh",
        ),
        "release_gate_pre_push: ok",
    )
    assert_gate(
        "tests/release_gate_pre_release.sh",
        (
            "git diff --check",
            "tests/release_gate_pre_push.sh",
            "tests/release_gate_v0_6_2.sh",
            "test_bootstrap_smoke.py",
            "test_installer_release.py",
            "tests/REVIEW_CHECKLIST.md",
        ),
        "release_gate_pre_release: ok",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

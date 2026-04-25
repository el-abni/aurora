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


def ensure_any(text: str, options: tuple[str, ...], message: str) -> None:
    if not any(option in text for option in options):
        fail(message)


def current_changelog_section(changelog: str) -> str:
    marker = f"## 🌌 Aurora {VERSION}"
    ensure(marker in changelog, f"CHANGELOG.md precisa abrir a release publica {VERSION}")
    return changelog.partition(marker)[2].partition("\n## ")[0]


def assert_invariants_state() -> None:
    path = "docs/AURORA_INVARIANTS.md"
    text = read(path)
    normalized = normalize(text)
    ensure(VERSION in text, f"{path} precisa refletir a release publica atual")
    ensure("contrato pequeno" in normalized and "auditavel" in normalized, f"{path} precisa registrar contrato pequeno e auditavel")
    ensure("superficie explicita" in normalized and "fallback magico" in normalized, f"{path} precisa registrar superficie explicita contra fallback magico")
    ensure("ferramenta observada" in normalized and "nao vira suporte" in normalized, f"{path} precisa registrar que ferramenta observada nao vira suporte")
    ensure("trust_signals" in normalized and "parsing reverso" in normalized, f"{path} precisa registrar que parsing reverso de trust_signals nao pode ficar implicito")
    ensure("modelo local" in normalized and "kernel deterministico" in normalized, f"{path} precisa registrar o limite de autoridade do modelo local")
    ensure("revisao humana" in normalized and "terminal real" in normalized, f"{path} precisa registrar revisao humana e terminal real")
    ensure("100% python" in normalized and "fish" in normalized and "stage publica" in normalized, f"{path} precisa preservar o centro 100% Python da Aurora")
    ok(f"{path} alinhado")


def assert_tests_readme_state() -> None:
    path = "tests/README.md"
    text = read(path)
    normalized = normalize(text)
    for term in (
        "tests/release_gate_canonic_line.sh",
        "tests/release_gate_v0_6_2.sh",
        "tests/release_gate_iteracao.sh",
        "tests/release_gate_pre_push.sh",
        "tests/release_gate_pre_release.sh",
        "tests/audit_public_release.py",
        "tests/audit_canonic_line.py",
        "tests/audit_decision_record_contract.py",
        "tests/audit_factual_hotspots.py",
        "tests/audit_factual_baseline.py",
        "tests/audit_observability_canonical_facts.py",
        "tests/audit_local_model_eval_baseline.py",
        "tests/audit_workflow_release.py",
        "tests/REVIEW_CHECKLIST.md",
        "schema",
        "stable_ids",
        "facts",
        "presentation",
        "terminal real",
    ):
        ensure(term in text or term in normalized, f"{path} precisa citar {term}")
    ensure("gate canonico da linha" in normalized, f"{path} precisa explicitar o gate canonico da linha")
    ensure("gate historico de release" in normalized, f"{path} precisa explicitar o gate historico de release")
    ok(f"{path} alinhado")


def assert_gate_state() -> None:
    path = "tests/release_gate_canonic_line.sh"
    text = read(path)
    normalized = normalize(text)
    for term in (
        "git ls-files 'tests/test_*.py'",
        "python3 -m unittest",
        "tests/audit_public_release.py",
        "tests/audit_canonic_line.py",
        "tests/audit_decision_record_contract.py",
        "tests/audit_factual_hotspots.py",
        "tests/audit_factual_baseline.py",
        "tests/audit_observability_canonical_facts.py",
        "tests/audit_local_model_eval_baseline.py",
        "tests/audit_workflow_release.py",
        "release_gate_canonic_line: ok",
    ):
        ensure(term in text, f"{path} precisa citar {term}")
    ensure("fish" not in normalized, f"{path} nao pode depender de Fish")
    ensure("stage publica" not in normalized and "staging" not in normalized, f"{path} nao pode depender de stage publica")
    ok(f"{path} alinhado")


def assert_readme_spine() -> None:
    path = "README.md"
    text = read(path)
    normalized = normalize(text)
    for term in (
        "tests/release_gate_canonic_line.sh",
        "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
        "tests/REVIEW_CHECKLIST.md",
        "tests/release_gate_iteracao.sh",
        "tests/release_gate_pre_push.sh",
        "tests/release_gate_pre_release.sh",
        "tests/README.md",
        "docs/AURORA_INVARIANTS.md",
        "docs/DECISION_RECORD_SCHEMA.md",
        "docs/FACTS_VS_RENDERING.md",
        "docs/AURY_TO_AURORA_DOSSIER.md",
        "aurora.decision_record.v1",
        "stable_ids",
        "facts",
        "presentation",
    ):
        ensure(term in text or term in normalized, f"{path} precisa citar {term}")
    ensure_any(normalized, ("espinha canonica", "workflow operacional", "disciplina operacional"), f"{path} precisa registrar a espinha e o workflow da linha")
    ok(f"{path} alinhado")


def assert_architecture_spine() -> None:
    path = "docs/ARCHITECTURE.md"
    text = read(path)
    normalized = normalize(text)
    for term in (
        "tests/release_gate_canonic_line.sh",
        "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
        "tests/REVIEW_CHECKLIST.md",
        "tests/release_gate_iteracao.sh",
        "tests/release_gate_pre_push.sh",
        "tests/release_gate_pre_release.sh",
        "tests/README.md",
        "docs/AURORA_INVARIANTS.md",
        "docs/DECISION_RECORD_SCHEMA.md",
        "docs/FACTS_VS_RENDERING.md",
        "docs/AURY_TO_AURORA_DOSSIER.md",
        "tests/audit_decision_record_contract.py",
        "tests/audit_factual_hotspots.py",
        "tests/audit_factual_baseline.py",
        "tests/audit_observability_canonical_facts.py",
        "tests/audit_local_model_eval_baseline.py",
        "aurora.decision_record.v1",
        "stable_ids",
        "facts",
        "presentation",
    ):
        ensure(term in text or term in normalized, f"{path} precisa citar {term}")
    for term in ("local_model", "model_off", "model_on", "fallback deterministico"):
        ensure(term in text or term in normalized, f"{path} precisa citar {term}")
    ensure_any(normalized, ("espinha canonica", "regua corrente da linha", "disciplina operacional"), f"{path} precisa registrar a espinha da linha na {VERSION}")
    ok(f"{path} alinhado")


def assert_changelog_spine() -> None:
    section = normalize(current_changelog_section(read("CHANGELOG.md")))
    for term in (
        "release_gate_canonic_line.sh",
        "workflow_de_testes_e_release.md",
        "review_checklist.md",
        "release_gate_iteracao.sh",
        "release_gate_pre_push.sh",
        "release_gate_pre_release.sh",
        "audit_workflow_release.py",
        "stable_ids",
        "presentation",
    ):
        ensure(term in section, f"CHANGELOG.md precisa citar {term} na release atual")
    ensure_any(section, ("workflow", "disciplina operacional", "disciplina de subida"), f"CHANGELOG.md precisa tratar a {VERSION} como workflow disciplinado")
    ok("CHANGELOG.md alinhado a espinha da linha")


def main() -> int:
    ensure(re.fullmatch(r"v\d+\.\d+\.\d+", VERSION) is not None, "VERSION precisa estar em formato de release")
    assert_invariants_state()
    assert_tests_readme_state()
    assert_gate_state()
    assert_readme_spine()
    assert_architecture_spine()
    assert_changelog_spine()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
PUBLIC_FILES = (
    "README.md",
    "CHANGELOG.md",
    "docs/ARCHITECTURE.md",
    "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
    "docs/COMPATIBILITY_LINUX.md",
    "docs/INSTALLATION_POLICY.md",
    "docs/AURY_HERITAGE_MAP.md",
    "docs/AURORA_INVARIANTS.md",
    "docs/DECISION_RECORD_SCHEMA.md",
    "docs/FACTS_VS_RENDERING.md",
    "docs/AURY_TO_AURORA_DOSSIER.md",
    "resources/help.txt",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def git_ls_files() -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        text=True,
        capture_output=True,
        check=False,
    )
    ensure(proc.returncode == 0, "git ls-files precisa funcionar para a auditoria publica")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def assert_terms(path: str, *terms: str) -> None:
    text = read(path)
    normalized = normalize(text)
    for term in terms:
        ensure(term in text or term in normalized, f"{path} precisa citar {term}")


def public_surface_sensitive_markers() -> tuple[str, ...]:
    private_suffix = "-private"
    return (
        "." + "aurora" + private_suffix,
        "." + "aury" + private_suffix,
        "/" + "/".join(("home", "abni")),
        ".".join(("AGENTS", "md")),
        "Chat" + "y",
        "Cod" + "dy",
        "Auro" + "boros",
        "Bor" + "eal",
        "brain" + "storms",
        "person" + "as",
    )


def main() -> int:
    ensure(VERSION == "v1.3.0", "VERSION precisa estar promovido para v1.3.0 no fechamento desta release")
    ensure(re.fullmatch(r"v\d+\.\d+\.\d+", VERSION) is not None, "VERSION precisa estar em formato de release")
    ok("VERSION promovido para v1.3.0")

    changelog = read("CHANGELOG.md")
    changelog_normalized = normalize(changelog)
    ensure(f"## 🌌 Aurora {VERSION}" in changelog, f"CHANGELOG.md precisa abrir a release publica {VERSION}")
    for preserved in ("v0.7.0", "v0.6.5", "v0.6.4", "v0.6.3", "v0.6.2", "v0.6.1", "v0.6.0", "v0.5.1", "v0.5.0"):
        ensure(f"## 🌌 Aurora {preserved}" in changelog, f"CHANGELOG.md precisa preservar a release publica {preserved}")
    for term in (
        "resources/help.txt",
        "README.md",
        "docs/COMPATIBILITY_LINUX.md",
        "docs/INSTALLATION_POLICY.md",
        "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
        "tests/release_gate_canonic_line.sh",
        "tests/release_gate_iteracao.sh",
        "tests/release_gate_pre_push.sh",
        "tests/release_gate_pre_release.sh",
        "tests/REVIEW_CHECKLIST.md",
        "tests/test_source_clarification.py",
        "tests/test_conversation_mediation.py",
        "tests/audit_workflow_release.py",
        "clarificacao controlada",
        "source_clarification",
        "source_discovery",
        "aurora explicar fontes",
        "aurora onde instalar firefox?",
        "aurora instalar firefox onde for melhor",
        "conversação/mediação",
        "orientação determinística",
        "aurora versão",
        "aurora exemplos",
        "aurora como instalar firefox?",
        "local_model",
        "model_off",
        "model_on",
        "ollama",
        "qwen2.5:3b-instruct",
        "provider real",
        "fallback deterministico",
        "autoridade limitada",
        "stable_ids",
        "presentation",
        "v0.7.0",
        "v1.0.0",
        "host_maintenance.atualizar",
        "aurora atualizar sistema --confirm",
        "sudo + pacman",
        "sem `paru`",
        "AUR implícita",
        "preparação da linha",
    ):
        ensure(term in changelog or term.lower() in changelog_normalized, f"CHANGELOG.md precisa citar {term}")
    ensure_any(changelog_normalized, ("provider real", "ollama", "fallback deterministico"), "CHANGELOG.md precisa preservar a v1.0.0 como base publica honesta da seam local_model")
    ensure_any(changelog_normalized, ("absorcao funcional i", "host_maintenance.atualizar", "aurora atualizar sistema --confirm"), "CHANGELOG.md precisa tratar a v1.1.0 como fechamento formal de host_maintenance.atualizar")
    ensure_any(changelog_normalized, ("conversacao/mediacao", "orientacao deterministica", "perguntas fechadas"), "CHANGELOG.md precisa tratar a v1.2.0 como conversacao/mediacao estreita")
    ensure_any(changelog_normalized, ("clarificacao controlada", "source_clarification", "source_discovery"), "CHANGELOG.md precisa tratar a v1.3.0 como clarificacao controlada de fonte/superficie")
    ok("CHANGELOG.md alinhado")

    readme = read("README.md")
    readme_normalized = normalize(readme)
    ensure(VERSION in readme, "README.md precisa citar a versao publica atual")
    for term in (
        "100% python",
        "Linux",
        "aurora ajuda",
        "auro ajuda",
        "aurora --version",
        "aurora versão",
        "aurora exemplos",
        "aurora como instalar firefox?",
        "aurora explicar fontes",
        "aurora onde instalar firefox?",
        "aurora instalar firefox onde for melhor",
        'aurora dev "procurar firefox"',
        "host_package",
        "host_maintenance.atualizar",
        "aurora atualizar sistema --confirm",
        "sudo + pacman",
        "sem `paru`",
        "AUR implícita",
        "AUR",
        "COPR",
        "PPA",
        "Flatpak",
        "user_software",
        "toolbox",
        "distrobox",
        "rpm-ostree",
        "--confirm",
        "release_gate_canonic_line.sh",
        "WORKFLOW_DE_TESTES_E_RELEASE.md",
        "REVIEW_CHECKLIST.md",
        "tests/README.md",
        "AURORA_INVARIANTS.md",
        "DECISION_RECORD_SCHEMA.md",
        "FACTS_VS_RENDERING.md",
        "AURY_TO_AURORA_DOSSIER.md",
        "aurora.decision_record.v1",
        "stable_ids",
        "facts",
        "presentation",
        "local_model",
        "model_off",
        "model_on",
        "ollama",
        "qwen2.5:3b-instruct",
        "AURORA_MODEL_MODE",
        "AURORA_LOCAL_MODEL_PROVIDER",
        "fallback deterministico",
        "clarificacao controlada",
        "source_discovery",
        "conversação/mediação",
        "orientação determinística",
    ):
        ensure(term in readme or term in readme_normalized, f"README.md precisa citar {term}")
    for term in (
        "contrato pequeno",
        "superficie publica continua pequena",
        "nao promete entender qualquer frase",
        "limites honestos",
        "nao decide policy",
        "aurora --help",
    ):
        ensure(term in readme or term in readme_normalized, f"README.md precisa citar {term}")
    readme_casefold = readme.casefold()
    for marker in public_surface_sensitive_markers():
        ensure(marker.casefold() not in readme_casefold, "README.md nao pode expor marcador publico sensivel")
    ensure_any(
        readme_normalized,
        ("contrato pequeno", "kernel deterministico", "decision_record"),
        "README.md precisa funcionar como home publica curta e preservar a seam local_model herdada",
    )
    ensure_any(readme_normalized, ("absorcao funcional i", "host_maintenance.atualizar", "sudo + pacman"), "README.md precisa tratar a v1.1.0 como fechamento formal de host_maintenance.atualizar")
    ensure_any(readme_normalized, ("clarificacao controlada", "source_discovery", "melhor fonte"), "README.md precisa tratar a v1.3.0 como clarificacao controlada sem discovery")
    ok("README.md alinhado")

    architecture = read("docs/ARCHITECTURE.md")
    architecture_normalized = normalize(architecture)
    for term in (
        "100% python",
        "fish",
        "tests/release_gate_canonic_line.sh",
        "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
        "tests/REVIEW_CHECKLIST.md",
        "tests/release_gate_iteracao.sh",
        "tests/release_gate_pre_push.sh",
        "tests/release_gate_pre_release.sh",
        "tests/README.md",
        "AURORA_INVARIANTS.md",
        "DECISION_RECORD_SCHEMA.md",
        "FACTS_VS_RENDERING.md",
        "AURY_TO_AURORA_DOSSIER.md",
        "tests/audit_decision_record_contract.py",
        "source_clarification.py",
        "source_discovery",
        "local_model/",
        "model_off",
        "model_on",
        "ollama",
        "qwen2.5:3b-instruct",
        "aurora dev",
        "fallback deterministico",
        "autoridade limitada",
        "aurora.decision_record.v1",
        "stable_ids",
        "facts",
        "presentation",
        "host_package.procurar",
        "host_package.search",
        "host_maintenance.atualizar",
        "sudo + pacman",
        "toolbox.procurar",
        "distrobox.procurar",
        "rpm_ostree.instalar",
        "rpm_ostree.remover",
    ):
        ensure(term in architecture or term in architecture_normalized, f"docs/ARCHITECTURE.md precisa citar {term}")
    ensure_any(architecture_normalized, ("workflow", "disciplina operacional", "ollama"), "ARCHITECTURE precisa preservar a seam assistiva real herdada sem abrir frente lateral")
    ensure_any(architecture_normalized, ("host_maintenance.atualizar", "absorcao funcional i", "sudo + pacman"), "ARCHITECTURE precisa tratar a v1.1.0 como fechamento formal de host_maintenance.atualizar")
    ensure_any(architecture_normalized, ("source_clarification", "clarificacao controlada", "source_discovery"), "ARCHITECTURE precisa registrar a clarificacao controlada da v1.3.0")
    ok("docs/ARCHITECTURE.md alinhado")

    assert_terms(
        "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
        VERSION,
        "teste automatico",
        "revisao",
        "terminal local",
        "release_gate_canonic_line.sh",
        "release_gate_v0_6_2.sh",
        "release_gate_iteracao.sh",
        "release_gate_pre_push.sh",
        "release_gate_pre_release.sh",
        "REVIEW_CHECKLIST.md",
        "aurora --version",
        "aurora --help",
        "aurora dev",
        "push",
        "tag",
        "release",
    )
    ok("docs/WORKFLOW_DE_TESTES_E_RELEASE.md alinhado")

    assert_terms(
        "docs/COMPATIBILITY_LINUX.md",
        VERSION,
        "toolbox",
        "distrobox",
        "rpm-ostree",
        "flatpak",
        "AUR",
        "COPR",
        "PPA",
        "pending deployment",
        "status --json",
        "clarificacao controlada",
        "host_maintenance",
        "atualizar sistema",
        "sudo + pacman",
    )
    ok("docs/COMPATIBILITY_LINUX.md alinhado")

    assert_terms(
        "docs/INSTALLATION_POLICY.md",
        VERSION,
        "domain_kind",
        "source_type",
        "execution_surface",
        "policy_outcome",
        "requires_confirmation",
        "immutable_selected_surface",
        "rpm_ostree_status",
        "flatpak_effective_remote",
        "toolbox_requested_environment",
        "distrobox_requested_environment",
        "host_maintenance",
        "requires_confirmation",
        "source_discovery",
        "melhor fonte",
    )
    ok("docs/INSTALLATION_POLICY.md alinhado")

    assert_terms(
        "docs/AURY_HERITAGE_MAP.md",
        VERSION,
        "aury",
        "herdado",
        "host_package",
        "user_software",
        "AURY_TO_AURORA_DOSSIER.md",
    )
    ok("docs/AURY_HERITAGE_MAP.md alinhado")

    assert_terms(
        "docs/AURORA_INVARIANTS.md",
        VERSION,
        "contrato pequeno",
        "auditavel",
        "superficie explicita",
        "ferramenta observada",
        "revisao humana",
        "terminal real",
        "100% python",
        "fish",
        "stage publica",
        "source_discovery",
        "melhor fonte",
    )
    ok("docs/AURORA_INVARIANTS.md alinhado")

    schema_doc = read("docs/DECISION_RECORD_SCHEMA.md")
    schema_normalized = normalize(schema_doc)
    for term in (
        VERSION,
        "aurora.decision_record.v1",
        "stable_ids.action_id",
        "stable_ids.route_id",
        "stable_ids.event_id",
        "facts",
        "presentation",
        "provider_name",
        "fallback_reason",
        "output_text",
        "disabled",
        "completed",
        "fallback_deterministic",
        "host_package.procurar",
        "host_package.search",
        "host_maintenance.atualizar",
        "atualizar",
        "payload antigo",
        "source_clarification",
    ):
        ensure(term in schema_doc or term in schema_normalized, f"docs/DECISION_RECORD_SCHEMA.md precisa citar {term}")
    ok("docs/DECISION_RECORD_SCHEMA.md alinhado")

    facts_doc = read("docs/FACTS_VS_RENDERING.md")
    facts_normalized = normalize(facts_doc)
    for term in (
        VERSION,
        "messages.py",
        "text_polish.py",
        "facts",
        "presentation",
        "fallback_reason",
        "output_text",
        "Local model seam",
        "policy",
        "bloqueio",
        "confirmacao",
        "resultado",
        "refactor ornamental",
        "terminal real",
        "host_maintenance.atualizar",
        "source_clarification.py",
        "source_discovery",
    ):
        ensure(term in facts_doc or term in facts_normalized, f"docs/FACTS_VS_RENDERING.md precisa citar {term}")
    ok("docs/FACTS_VS_RENDERING.md alinhado")

    dossier = read("docs/AURY_TO_AURORA_DOSSIER.md")
    dossier_normalized = normalize(dossier)
    for term in (
        VERSION,
        "aury",
        "aurora",
        "raiz operacional",
        "decisao e mediacao",
        "modelo local",
        "nao deve migrar",
        "frontend da aurora",
        "fish",
        "gate final",
    ):
        ensure(term in dossier or term in dossier_normalized, f"docs/AURY_TO_AURORA_DOSSIER.md precisa citar {term}")
    ok("docs/AURY_TO_AURORA_DOSSIER.md alinhado")

    help_text = read("resources/help.txt")
    help_normalized = normalize(help_text)
    ensure(help_text.startswith("🌌 Aurora {version}"), "resources/help.txt precisa abrir com o cabecalho final da release")
    ensure(len(help_text.splitlines()) <= 55, "resources/help.txt precisa permanecer curto o bastante para ser help de uso")
    for term in (
        "Uso rápido:",
        "Orientação:",
        "Fontes explícitas:",
        "Ambientes e host imutável:",
        "Leitura correta:",
        "Confirmação:",
        "Mais detalhes:",
        "aurora exemplos",
        "aurora limites",
        "aurora comandos",
        "aurora versão",
        "auro versão",
        "aurora como instalar firefox?",
        "aurora.decision_record.v1",
        "README.md",
        "docs/COMPATIBILITY_LINUX.md",
        "docs/INSTALLATION_POLICY.md",
        "docs/WORKFLOW_DE_TESTES_E_RELEASE.md",
        "ppa:owner/name",
        "owner>/<project>",
        "na toolbox <ambiente>",
        "na distrobox <ambiente>",
        "rpm-ostree",
        "aurora explicar fontes",
        "aurora onde instalar firefox?",
        "aurora instalar firefox onde for melhor",
        "--confirm",
        "--yes",
    ):
        ensure(term in help_text or term in help_normalized, f"resources/help.txt precisa citar {term}")
    ensure("Compatibilidade:" not in help_text, "resources/help.txt nao pode voltar a carregar secao longa de compatibilidade")
    ensure("Fora da" not in help_text, "resources/help.txt nao pode voltar a carregar secao longa de limites fora da release")
    ensure("Contrato público da" not in help_text, "resources/help.txt nao pode embutir o contrato publico inteiro")
    ok("resources/help.txt alinhado")

    gitignore = read(".gitignore")
    ensure("__pycache__/" in gitignore, ".gitignore precisa ignorar __pycache__/")
    ensure("*.pyc" in gitignore, ".gitignore precisa ignorar *.pyc")
    ensure(".codex" in gitignore, ".gitignore precisa ignorar .codex")
    ok(".gitignore alinhado")

    tracked_files = git_ls_files()
    dirty_python_artifacts = [path for path in tracked_files if "__pycache__/" in path or path.endswith(".pyc")]
    ensure(not dirty_python_artifacts, "artefatos Python compilados nao podem permanecer rastreados no repositorio")
    ok("artefatos Python compilados fora do rastreamento")

    install_text = read("install.sh")
    uninstall_text = read("uninstall.sh")
    ensure("fish" not in normalize(install_text), "install.sh nao pode depender de Fish")
    ensure("fish" not in normalize(uninstall_text), "uninstall.sh nao pode depender de Fish")
    ok("instalador sem dependencia de Fish")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

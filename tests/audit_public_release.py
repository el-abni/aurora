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
    "docs/COMPATIBILITY_LINUX.md",
    "docs/INSTALLATION_POLICY.md",
    "docs/AURY_HERITAGE_MAP.md",
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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_no_auroboros(path: str, text: str) -> None:
    ensure("auroboros" not in normalize(text), f"{path} nao pode mencionar Auroboros em material publico")


def git_ls_files() -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        text=True,
        capture_output=True,
        check=False,
    )
    ensure(proc.returncode == 0, "git ls-files precisa funcionar para a auditoria publica")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def main() -> int:
    ensure(VERSION == "v0.3.0", "VERSION precisa estar promovido para v0.3.0 no fechamento desta release")
    ensure(re.fullmatch(r"v\d+\.\d+\.\d+", VERSION) is not None, "VERSION precisa estar em formato de release")
    ok("VERSION promovido para v0.3.0")

    changelog = read("CHANGELOG.md")
    changelog_normalized = normalize(changelog)
    ensure("## 🌌 Aurora v0.3.0" in changelog, "CHANGELOG.md precisa abrir a release publica v0.3.0")
    ensure("em progresso" not in changelog_normalized, "CHANGELOG.md nao pode manter a v0.3.0 como em progresso")
    ensure("## 🌌 Aurora v0.2.0" in changelog, "CHANGELOG.md precisa preservar a release publica v0.2.0")
    ensure("aur.procurar" in changelog, "CHANGELOG.md precisa citar a rota aur.procurar")
    ensure("user_software" in changelog, "CHANGELOG.md precisa citar user_software")
    ensure("flatpak" in changelog_normalized, "CHANGELOG.md precisa citar flatpak")
    ensure("aur" in changelog_normalized, "CHANGELOG.md precisa citar a frente AUR")
    assert_no_auroboros("CHANGELOG.md", changelog)
    ok("CHANGELOG.md alinhado ao estado atual da linha")

    readme = read("README.md")
    readme_normalized = normalize(readme)
    ensure(VERSION in readme, "README.md precisa citar a versao publica atual")
    ensure("v0.2.0" not in readme, "README.md nao pode continuar apresentando v0.2.0 como release publica atual")
    ensure("100% python" in readme_normalized, "README.md precisa deixar Aurora como produto 100% Python")
    ensure("aurora" in readme_normalized and "auro" in readme_normalized, "README.md precisa citar os launchers")
    ensure("host_package" in readme, "README.md precisa citar host_package explicitamente")
    ensure("user_software" in readme, "README.md precisa citar user_software explicitamente")
    ensure("aur" in readme_normalized, "README.md precisa explicar a frente AUR explicita")
    ensure("flatpak" in readme_normalized, "README.md precisa explicar o recorte flatpak")
    ensure("--confirm" in readme, "README.md precisa mencionar --confirm")
    ensure("--yes" in readme, "README.md precisa mencionar --yes como alias de confirmacao")
    ensure("no aur" in readme_normalized, "README.md precisa mostrar a sintaxe explicita de AUR")
    ensure("interativo" in readme_normalized, "README.md precisa explicar o fluxo interativo do helper AUR")
    assert_no_auroboros("README.md", readme)
    ok("README.md alinhado ao release")

    architecture = read("docs/ARCHITECTURE.md")
    architecture_normalized = normalize(architecture)
    ensure("100% python" in architecture_normalized, "ARCHITECTURE precisa afirmar 100% Python")
    ensure("fish" in architecture_normalized, "ARCHITECTURE precisa explicitar a saida de Fish do centro")
    for route_name in (
        "host_package.search",
        "host_package.instalar",
        "host_package.remover",
        "aur.procurar",
        "aur.instalar",
        "aur.remover",
        "flatpak.procurar",
        "flatpak.instalar",
        "flatpak.remover",
    ):
        ensure(route_name in architecture, f"ARCHITECTURE precisa listar a rota {route_name}")
    ensure("interativo" in architecture_normalized, "ARCHITECTURE precisa registrar o handoff interativo do helper")
    assert_no_auroboros("docs/ARCHITECTURE.md", architecture)
    ok("docs/ARCHITECTURE.md alinhado")

    compatibility = read("docs/COMPATIBILITY_LINUX.md")
    compatibility_normalized = normalize(compatibility)
    for term in ("arch", "debian", "fedora", "opensuse", "atomic", "flatpak", "user_software", "aur", "paru"):
        ensure(term in compatibility_normalized, f"COMPATIBILITY precisa citar {term}")
    ensure("interativo" in compatibility_normalized, "COMPATIBILITY precisa citar o fluxo interativo de aur.instalar")
    assert_no_auroboros("docs/COMPATIBILITY_LINUX.md", compatibility)
    ok("docs/COMPATIBILITY_LINUX.md alinhado")

    policy = read("docs/INSTALLATION_POLICY.md")
    policy_normalized = normalize(policy)
    for term in (
        "domain_kind",
        "source_type",
        "trust_level",
        "software_criticality",
        "policy_outcome",
        "requires_confirmation",
        "reversal_level",
        "host_package_manager",
        "aur_repository",
        "flatpak_remote",
        "distribution_managed",
        "third_party_build",
        "guarded",
        "flathub",
    ):
        ensure(term in policy, f"INSTALLATION_POLICY precisa citar {term}")
    ensure("user_software" in policy, "INSTALLATION_POLICY precisa citar user_software")
    ensure("aur" in policy_normalized, "INSTALLATION_POLICY precisa citar AUR")
    ensure("flatpak" in policy_normalized, "INSTALLATION_POLICY precisa citar flatpak")
    ensure("--yes" in policy, "INSTALLATION_POLICY precisa citar --yes como alias de confirmacao")
    ensure("interativo" in policy_normalized, "INSTALLATION_POLICY precisa explicar o fluxo interativo de aur.instalar")
    assert_no_auroboros("docs/INSTALLATION_POLICY.md", policy)
    ok("docs/INSTALLATION_POLICY.md alinhado")

    heritage = read("docs/AURY_HERITAGE_MAP.md")
    heritage_normalized = normalize(heritage)
    ensure(VERSION in heritage, "AURY_HERITAGE_MAP precisa refletir a release publica atual")
    ensure("aury" in heritage_normalized, "AURY_HERITAGE_MAP precisa citar a Aury")
    ensure("herdado" in heritage_normalized or "herdada" in heritage_normalized, "AURY_HERITAGE_MAP precisa marcar heranca")
    ensure("nao entrou" in heritage_normalized or "nao migrou" in heritage_normalized, "AURY_HERITAGE_MAP precisa registrar o que nao migrou")
    ensure("user_software" in heritage, "AURY_HERITAGE_MAP precisa citar a extensao da v0.2.0")
    ensure("aur" in heritage_normalized, "AURY_HERITAGE_MAP precisa citar a frente AUR da v0.3.0")
    assert_no_auroboros("docs/AURY_HERITAGE_MAP.md", heritage)
    ok("docs/AURY_HERITAGE_MAP.md alinhado")

    help_text = read("resources/help.txt")
    help_normalized = normalize(help_text)
    ensure(help_text.startswith("🌌 Aurora {version}"), "resources/help.txt precisa abrir com o cabecalho final da release")
    ensure("{version}" in help_text, "resources/help.txt precisa manter placeholder de versao")
    ensure("host_package" in help_text, "resources/help.txt precisa citar host_package")
    ensure("user_software" in help_text, "resources/help.txt precisa citar user_software")
    ensure("host_package.search/instalar/remover" in help_text, "resources/help.txt precisa listar as rotas reais de host_package")
    ensure("aur" in help_normalized, "resources/help.txt precisa citar AUR como rota real")
    ensure("flatpak" in help_normalized, "resources/help.txt precisa citar flatpak como rota real")
    ensure("--confirm" in help_text, "resources/help.txt precisa citar --confirm")
    ensure("--yes" in help_text, "resources/help.txt precisa citar --yes")
    ensure("interativo" in help_normalized, "resources/help.txt precisa citar o fluxo interativo de aur.instalar")
    ensure("aurora instalar <pacote> --confirm" in help_text, "resources/help.txt precisa mostrar a sintaxe publica correta para instalacao sensivel")
    ensure(
        "aurora instalar <pacote> no aur --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica correta para instalacao AUR com confirmacao",
    )
    ensure(
        "aurora remover <software> no flatpak --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica correta para remocao flatpak com confirmacao",
    )
    assert_no_auroboros("resources/help.txt", help_text)
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

    for path in PUBLIC_FILES:
        assert_no_auroboros(path, read(path))

    install_text = read("install.sh")
    uninstall_text = read("uninstall.sh")
    ensure("fish" not in normalize(install_text), "install.sh nao pode depender de Fish")
    ensure("fish" not in normalize(uninstall_text), "uninstall.sh nao pode depender de Fish")
    ok("instalador sem dependencia de Fish")

    release_gate = read("tests/release_gate_v0_3.sh")
    ensure("PYTHONPATH=python" in release_gate, "release_gate_v0_3 precisa executar com PYTHONPATH=python")
    ensure("audit_public_release.py" in release_gate, "release_gate_v0_3 precisa rodar a auditoria publica")
    ok("release_gate_v0_3 alinhado")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

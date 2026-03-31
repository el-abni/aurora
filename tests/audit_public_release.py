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
    ensure(VERSION == "v0.2.0", "VERSION precisa estar promovido para v0.2.0 no fechamento desta release")
    ensure(re.fullmatch(r"v\d+\.\d+\.\d+", VERSION) is not None, "VERSION precisa estar em formato de release")
    ok("VERSION promovido para v0.2.0")

    changelog = read("CHANGELOG.md")
    changelog_normalized = normalize(changelog)
    ensure("## 🌌 Aurora v0.2.0" in changelog, "CHANGELOG.md precisa abrir a release v0.2.0")
    ensure("user_software" in changelog, "CHANGELOG.md precisa citar user_software")
    ensure("flatpak" in changelog_normalized, "CHANGELOG.md precisa citar flatpak")
    ensure("gate final" in changelog_normalized, "CHANGELOG.md precisa registrar o gate final")
    assert_no_auroboros("CHANGELOG.md", changelog)
    ok("CHANGELOG.md alinhado ao fechamento da v0.2.0")

    readme = read("README.md")
    readme_normalized = normalize(readme)
    ensure(VERSION in readme, "README.md precisa citar a versao publica atual")
    ensure("100% python" in readme_normalized, "README.md precisa deixar Aurora como produto 100% Python")
    ensure("aurora" in readme_normalized and "auro" in readme_normalized, "README.md precisa citar os launchers")
    ensure("host_package" in readme, "README.md precisa citar host_package explicitamente")
    ensure("user_software" in readme, "README.md precisa citar user_software explicitamente")
    ensure("flatpak" in readme_normalized, "README.md precisa explicar o recorte flatpak")
    ensure("--confirm" in readme, "README.md precisa mencionar --confirm")
    ensure("corte inicial" not in readme_normalized, "README.md nao pode vender a v0.2.0 como corte inicial")
    assert_no_auroboros("README.md", readme)
    ok("README.md alinhado ao release")

    architecture = read("docs/ARCHITECTURE.md")
    architecture_normalized = normalize(architecture)
    ensure("100% python" in architecture_normalized, "ARCHITECTURE precisa afirmar 100% Python")
    ensure("fish" in architecture_normalized, "ARCHITECTURE precisa explicitar a saida de Fish do centro")
    for route_name in (
        "host_package.search",
        "host_package.install",
        "host_package.remove",
        "flatpak.procurar",
        "flatpak.instalar",
        "flatpak.remover",
    ):
        ensure(route_name in architecture, f"ARCHITECTURE precisa listar a rota {route_name}")
    assert_no_auroboros("docs/ARCHITECTURE.md", architecture)
    ok("docs/ARCHITECTURE.md alinhado")

    compatibility = read("docs/COMPATIBILITY_LINUX.md")
    compatibility_normalized = normalize(compatibility)
    for term in ("arch", "debian", "fedora", "opensuse", "atomic", "flatpak", "user_software"):
        ensure(term in compatibility_normalized, f"COMPATIBILITY precisa citar {term}")
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
        "flatpak_remote",
        "distribution_managed",
        "guarded",
        "flathub",
    ):
        ensure(term in policy, f"INSTALLATION_POLICY precisa citar {term}")
    ensure("user_software" in policy, "INSTALLATION_POLICY precisa citar user_software")
    ensure("flatpak" in policy_normalized, "INSTALLATION_POLICY precisa citar flatpak")
    assert_no_auroboros("docs/INSTALLATION_POLICY.md", policy)
    ok("docs/INSTALLATION_POLICY.md alinhado")

    heritage = read("docs/AURY_HERITAGE_MAP.md")
    heritage_normalized = normalize(heritage)
    ensure("aury" in heritage_normalized, "AURY_HERITAGE_MAP precisa citar a Aury")
    ensure("herdado" in heritage_normalized or "herdada" in heritage_normalized, "AURY_HERITAGE_MAP precisa marcar heranca")
    ensure("nao entrou" in heritage_normalized or "nao migrou" in heritage_normalized, "AURY_HERITAGE_MAP precisa registrar o que nao migrou")
    ensure("user_software" in heritage, "AURY_HERITAGE_MAP precisa citar a extensao da v0.2.0")
    assert_no_auroboros("docs/AURY_HERITAGE_MAP.md", heritage)
    ok("docs/AURY_HERITAGE_MAP.md alinhado")

    help_text = read("resources/help.txt")
    help_normalized = normalize(help_text)
    ensure(help_text.startswith("🌌 Aurora {version}"), "resources/help.txt precisa abrir com o cabecalho final da release")
    ensure("{version}" in help_text, "resources/help.txt precisa manter placeholder de versao")
    ensure("host_package" in help_text, "resources/help.txt precisa citar host_package")
    ensure("user_software" in help_text, "resources/help.txt precisa citar user_software")
    ensure("flatpak" in help_normalized, "resources/help.txt precisa citar flatpak como rota real")
    ensure("--confirm" in help_text, "resources/help.txt precisa citar --confirm")
    ensure("aurora instalar <pacote> --confirm" in help_text, "resources/help.txt precisa mostrar a sintaxe publica correta para instalacao sensivel")
    ensure(
        "aurora remover <software> no flatpak --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica correta para remocao flatpak com confirmacao",
    )
    assert_no_auroboros("resources/help.txt", help_text)
    ok("resources/help.txt alinhado")

    gitignore = read(".gitignore")
    ensure("__pycache__/" in gitignore, ".gitignore precisa ignorar __pycache__/")
    ensure("*.pyc" in gitignore, ".gitignore precisa ignorar *.pyc")
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

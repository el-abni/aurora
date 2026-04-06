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
    ensure(VERSION == "v0.6.2", "VERSION precisa estar promovido para v0.6.2 no fechamento desta release")
    ensure(re.fullmatch(r"v\d+\.\d+\.\d+", VERSION) is not None, "VERSION precisa estar em formato de release")
    ok("VERSION promovido para v0.6.2")

    changelog = read("CHANGELOG.md")
    changelog_normalized = normalize(changelog)
    ensure("## 🌌 Aurora v0.6.2" in changelog, "CHANGELOG.md precisa abrir a release publica v0.6.2")
    ensure("## 🌌 Aurora v0.6.1" in changelog, "CHANGELOG.md precisa preservar a release publica v0.6.1")
    ensure("## 🌌 Aurora v0.6.0" in changelog, "CHANGELOG.md precisa preservar a release publica v0.6.0")
    ensure("## 🌌 Aurora v0.5.1" in changelog, "CHANGELOG.md precisa preservar a release publica v0.5.1")
    ensure("## 🌌 Aurora v0.5.0" in changelog, "CHANGELOG.md precisa preservar a release publica v0.5.0")
    for term in (
        "toolbox",
        "distrobox",
        "rpm-ostree",
        "rpm_ostree.instalar",
        "rpm_ostree.remover",
        "rpm_ostree.procurar",
        "immutable_selected_surface",
        "pending deployment",
        "status --json",
        "execution_surface",
        "environment_target",
        "toolbox.procurar",
        "toolbox.instalar",
        "toolbox.remover",
        "distrobox.procurar",
        "distrobox.instalar",
        "distrobox.remover",
        "fallback",
        "nome exato",
        "ppa.instalar",
        "ppa:owner/name",
    ):
        ensure(term in changelog_normalized or term in changelog, f"CHANGELOG.md precisa citar {term}")
    ensure("copr" in changelog_normalized, "CHANGELOG.md precisa preservar a frente COPR")
    ensure("aur" in changelog_normalized, "CHANGELOG.md precisa preservar a frente AUR")
    ensure("flatpak" in changelog_normalized, "CHANGELOG.md precisa preservar flatpak")
    assert_no_auroboros("CHANGELOG.md", changelog)
    ok("CHANGELOG.md alinhado ao estado atual da linha")

    readme = read("README.md")
    readme_normalized = normalize(readme)
    ensure(VERSION in readme, "README.md precisa citar a versao publica atual")
    ensure("100% python" in readme_normalized, "README.md precisa deixar Aurora como produto 100% Python")
    ensure("aurora" in readme_normalized and "auro" in readme_normalized, "README.md precisa citar os launchers")
    for term in (
        "host_package",
        "user_software",
        "execution_surface",
        "environment_target",
        "aur",
        "copr",
        "flatpak",
        "ppa",
        "toolbox",
        "distrobox",
        "rpm-ostree",
        "rpm_ostree",
        "rpm_ostree.instalar",
        "rpm_ostree.remover",
        "rpm_ostree.procurar",
        "rpm_ostree_layering",
        "immutable_selected_surface",
        "immutable_observed_surfaces",
        "pending deployment",
        "status --json",
        "toolbox.procurar",
        "toolbox.instalar",
        "toolbox.remover",
        "distrobox.procurar",
        "distrobox.instalar",
        "distrobox.remover",
        "toolbox_host_package_manager",
        "distrobox_host_package_manager",
        "mediated_environment",
        "na toolbox <ambiente>",
        "na distrobox <ambiente>",
        "nome exato",
        "fallback",
        "ppa.instalar",
        "ppa.remover",
        "ppa:owner/name",
        "ppa_repository",
        "add-apt-repository",
        "ubuntu mutavel",
        "flatpak remotes",
        "remote-ls",
        "flathub",
        "host imutável",
        "--confirm",
        "--yes",
    ):
        ensure(term in readme_normalized or term in readme, f"README.md precisa citar {term}")
    ensure("owner/project" in readme, "README.md precisa continuar citando owner/project")
    ensure("from_repo" in readme, "README.md precisa continuar citando from_repo")
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
        "copr.procurar",
        "copr.instalar",
        "copr.remover",
        "ppa.instalar",
        "flatpak.procurar",
        "flatpak.instalar",
        "flatpak.remover",
        "toolbox.procurar",
        "toolbox.instalar",
        "toolbox.remover",
        "distrobox.procurar",
        "distrobox.instalar",
        "distrobox.remover",
        "rpm_ostree.instalar",
        "rpm_ostree.remover",
    ):
        ensure(route_name in architecture, f"ARCHITECTURE precisa listar a rota {route_name}")
    for term in (
        "toolbox",
        "distrobox",
        "rpm-ostree",
        "rpm_ostree_status",
        "immutable_selected_surface",
        "immutable_observed_surfaces",
        "pending deployment",
        "status --json",
        "execution_surface",
        "environment_resolution",
        "toolbox_profile",
        "distrobox_profile",
        "nome exato",
        "fallback",
        "ppa:owner/name",
        "ubuntu",
        "add-apt-repository",
        "ppa.remover",
        "flatpak remotes",
        "remote-ls",
        "flathub",
        "origin",
    ):
        ensure(term in architecture_normalized or term in architecture, f"ARCHITECTURE precisa citar {term}")
    assert_no_auroboros("docs/ARCHITECTURE.md", architecture)
    ok("docs/ARCHITECTURE.md alinhado")

    compatibility = read("docs/COMPATIBILITY_LINUX.md")
    compatibility_normalized = normalize(compatibility)
    for term in (
        "arch",
        "debian",
        "fedora",
        "opensuse",
        "atomic",
        "flatpak",
        "user_software",
        "aur",
        "paru",
        "yay",
        "copr",
        "owner/project",
        "from_repo",
        "ppa",
        "ppa:owner/name",
        "ubuntu",
        "add-apt-repository",
        "apt-get",
        "dpkg",
        "ppa.remover",
        "toolbox",
        "distrobox",
        "rpm-ostree",
        "rpm_ostree.instalar",
        "rpm_ostree.remover",
        "rpm_ostree.procurar",
        "immutable_selected_surface",
        "pending deployment",
        "status --json",
        "sudo",
        "nome exato",
        "fallback",
        "flatpak remotes",
        "remote-ls",
        "flathub",
        "origin",
    ):
        ensure(term in compatibility_normalized or term in compatibility, f"COMPATIBILITY precisa citar {term}")
    assert_no_auroboros("docs/COMPATIBILITY_LINUX.md", compatibility)
    ok("docs/COMPATIBILITY_LINUX.md alinhado")

    policy = read("docs/INSTALLATION_POLICY.md")
    policy_normalized = normalize(policy)
    for term in (
        "domain_kind",
        "source_type",
        "execution_surface",
        "trust_level",
        "software_criticality",
        "policy_outcome",
        "requires_confirmation",
        "reversal_level",
        "host_package_manager",
        "aur_repository",
        "copr_repository",
        "ppa_repository",
        "flatpak_remote",
        "toolbox_host_package_manager",
        "distrobox_host_package_manager",
        "rpm_ostree_layering",
        "distribution_managed",
        "third_party_build",
        "third_party_repository",
        "guarded",
        "mediated_environment",
        "immutable_host_surface",
        "immutable_selected_surface",
        "immutable_observed_surfaces",
        "rpm_ostree_status",
        "pending deployment",
        "status --json",
        "toolbox_requested_environment",
        "toolbox_resolved_environment",
        "toolbox_package_backends",
        "toolbox_sudo_observed",
        "distrobox_requested_environment",
        "distrobox_resolved_environment",
        "distrobox_package_backends",
        "distrobox_sudo_observed",
        "na toolbox",
        "na distrobox",
        "nome exato",
        "flathub",
        "flatpak_effective_remote",
        "flatpak_remote_origin",
        "flatpak_observed_remotes",
        "flatpak remotes",
        "remote-ls",
        "ppa:owner/name",
        "add-apt-repository",
        "ubuntu",
        "ppa.remover",
    ):
        ensure(term in policy_normalized or term in policy, f"INSTALLATION_POLICY precisa citar {term}")
    ensure("owner/project" in policy, "INSTALLATION_POLICY precisa continuar citando owner/project")
    ensure("from_repo" in policy, "INSTALLATION_POLICY precisa continuar citando from_repo")
    assert_no_auroboros("docs/INSTALLATION_POLICY.md", policy)
    ok("docs/INSTALLATION_POLICY.md alinhado")

    heritage = read("docs/AURY_HERITAGE_MAP.md")
    heritage_normalized = normalize(heritage)
    ensure(VERSION in heritage, "AURY_HERITAGE_MAP precisa refletir a release publica atual")
    for term in (
        "aury",
        "herdado",
        "host_package",
        "user_software",
        "aur",
        "copr",
        "ppa",
        "flatpak",
        "toolbox",
        "distrobox",
        "rpm-ostree",
    ):
        ensure(term in heritage_normalized or term in heritage, f"AURY_HERITAGE_MAP precisa citar {term}")
    assert_no_auroboros("docs/AURY_HERITAGE_MAP.md", heritage)
    ok("docs/AURY_HERITAGE_MAP.md alinhado")

    help_text = read("resources/help.txt")
    help_normalized = normalize(help_text)
    ensure(help_text.startswith("🌌 Aurora {version}"), "resources/help.txt precisa abrir com o cabecalho final da release")
    ensure("{version}" in help_text, "resources/help.txt precisa manter placeholder de versao")
    for term in (
        "host_package",
        "user_software",
        "aur",
        "copr",
        "ppa",
        "flatpak",
        "toolbox",
        "distrobox",
        "rpm-ostree",
        "rpm_ostree",
        "rpm_ostree.instalar",
        "rpm_ostree.remover",
        "rpm_ostree_layering",
        "immutable_selected_surface",
        "pending deployment",
        "status --json",
        "ppa_repository",
        "ppa.instalar",
        "ppa.remover",
        "ppa:owner/name",
        "ubuntu",
        "add-apt-repository",
        "toolbox.instalar",
        "toolbox.remover",
        "toolbox_host_package_manager",
        "distrobox.instalar",
        "distrobox.remover",
        "distrobox_host_package_manager",
        "na toolbox <ambiente>",
        "na distrobox <ambiente>",
        "nome exato",
        "flatpak remotes",
        "remote-ls",
        "flathub",
        "--confirm",
        "--yes",
    ):
        ensure(term in help_normalized or term in help_text, f"resources/help.txt precisa citar {term}")
    ensure(
        "aurora instalar <pacote> do ppa <ppa:owner/name> --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica correta para instalacao PPA com confirmacao",
    )
    ensure(
        "aurora remover <pacote> do ppa <ppa:owner/name>" in help_text,
        "resources/help.txt precisa mostrar a sintaxe observavel para o bloqueio de remocao PPA",
    )
    ensure(
        "aurora procurar <software> no flatpak <remote>" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de remote explicito no flatpak",
    )
    ensure(
        "aurora remover <software> no flatpak <remote> --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de remocao flatpak com remote explicito",
    )
    ensure(
        "aurora procurar <pacote> na toolbox <ambiente>" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de busca em toolbox explicita",
    )
    ensure(
        "aurora remover <pacote> na toolbox <ambiente> --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de remocao em toolbox explicita",
    )
    ensure(
        "aurora procurar <pacote> na distrobox <ambiente>" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de busca em distrobox explicita",
    )
    ensure(
        "aurora remover <pacote> na distrobox <ambiente> --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de remocao em distrobox explicita",
    )
    ensure(
        "aurora instalar <pacote> no rpm-ostree" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de instalacao rpm-ostree explicita",
    )
    ensure(
        "aurora remover <pacote> no rpm-ostree --confirm" in help_text,
        "resources/help.txt precisa mostrar a sintaxe publica de remocao rpm-ostree explicita",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

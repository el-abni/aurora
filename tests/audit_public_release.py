#!/usr/bin/env python3
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
PUBLIC_FILES = (
    "README.md",
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


def main() -> int:
    ensure(re.fullmatch(r"v\d+\.\d+\.\d+", VERSION) is not None, "VERSION precisa estar em formato de release")
    ok("VERSION esta em formato de release")

    readme = read("README.md")
    readme_normalized = normalize(readme)
    ensure(VERSION in readme, "README.md precisa citar a versao publica atual")
    ensure("100% python" in readme_normalized, "README.md precisa deixar Aurora como produto 100% Python")
    ensure("aurora" in readme_normalized and "auro" in readme_normalized, "README.md precisa citar os launchers")
    ensure("host_package" in readme, "README.md precisa citar host_package explicitamente")
    ensure("procurar" in readme_normalized and "instalar" in readme_normalized and "remover" in readme_normalized, "README.md precisa listar as acoes reais")
    ensure("--confirm" in readme, "README.md precisa mencionar --confirm")
    ensure("flatpak" in readme_normalized, "README.md precisa enquadrar flatpak fora do escopo")
    assert_no_auroboros("README.md", readme)
    ok("README.md alinhado ao release")

    architecture = read("docs/ARCHITECTURE.md")
    architecture_normalized = normalize(architecture)
    ensure("100% python" in architecture_normalized, "ARCHITECTURE precisa afirmar 100% Python")
    ensure("fish" in architecture_normalized, "ARCHITECTURE precisa explicitar a saida de Fish do centro")
    ensure("host_package.search" in architecture and "host_package.install" in architecture and "host_package.remove" in architecture, "ARCHITECTURE precisa listar as rotas abertas")
    assert_no_auroboros("docs/ARCHITECTURE.md", architecture)
    ok("docs/ARCHITECTURE.md alinhado")

    compatibility = read("docs/COMPATIBILITY_LINUX.md")
    compatibility_normalized = normalize(compatibility)
    ensure("arch" in compatibility_normalized, "COMPATIBILITY precisa citar Arch")
    ensure("debian" in compatibility_normalized or "ubuntu" in compatibility_normalized, "COMPATIBILITY precisa citar Debian/Ubuntu")
    ensure("fedora" in compatibility_normalized, "COMPATIBILITY precisa citar Fedora")
    ensure("opensuse" in compatibility_normalized, "COMPATIBILITY precisa citar OpenSUSE")
    ensure("atomic" in compatibility_normalized or "imutaveis" in compatibility_normalized, "COMPATIBILITY precisa citar Atomic/imutaveis")
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
    ):
        ensure(term in policy, f"INSTALLATION_POLICY precisa citar {term}")
    ensure("flatpak" in policy_normalized, "INSTALLATION_POLICY precisa enquadrar flatpak fora da v0.1")
    assert_no_auroboros("docs/INSTALLATION_POLICY.md", policy)
    ok("docs/INSTALLATION_POLICY.md alinhado")

    heritage = read("docs/AURY_HERITAGE_MAP.md")
    heritage_normalized = normalize(heritage)
    ensure("aury" in heritage_normalized, "AURY_HERITAGE_MAP precisa citar a Aury")
    ensure("herdado" in heritage_normalized or "herdada" in heritage_normalized, "AURY_HERITAGE_MAP precisa marcar heranca")
    ensure("nao migrou" in heritage_normalized or "nao entrou" in heritage_normalized, "AURY_HERITAGE_MAP precisa registrar o que nao migrou")
    assert_no_auroboros("docs/AURY_HERITAGE_MAP.md", heritage)
    ok("docs/AURY_HERITAGE_MAP.md alinhado")

    help_text = read("resources/help.txt")
    help_normalized = normalize(help_text)
    ensure(help_text.startswith("🌌 Aurora {version}"), "resources/help.txt precisa abrir com o cabecalho final da release")
    ensure("{version}" in help_text, "resources/help.txt precisa manter placeholder de versao")
    ensure("host_package" in help_text, "resources/help.txt precisa citar host_package")
    ensure("--confirm" in help_text, "resources/help.txt precisa citar --confirm")
    ensure("aurora instalar <pacote> --confirm" in help_text, "resources/help.txt precisa mostrar a sintaxe publica correta para instalar com confirmacao")
    ensure("aurora remover <pacote> --confirm" in help_text, "resources/help.txt precisa mostrar a sintaxe publica correta para remover com confirmacao")
    ensure("flatpak" in help_normalized, "resources/help.txt precisa enquadrar flatpak fora do contrato")
    assert_no_auroboros("resources/help.txt", help_text)
    ok("resources/help.txt alinhado")

    for path in PUBLIC_FILES:
        text = read(path)
        assert_no_auroboros(path, text)

    install_text = read("install.sh")
    uninstall_text = read("uninstall.sh")
    ensure("fish" not in normalize(install_text), "install.sh nao pode depender de Fish")
    ensure("fish" not in normalize(uninstall_text), "uninstall.sh nao pode depender de Fish")
    ok("instalador sem dependencia de Fish")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

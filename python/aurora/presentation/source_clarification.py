from __future__ import annotations

from aurora.presentation.text_polish import apply_speech_indicator
from aurora.semantics.source_clarification import (
    SourceClarificationKind,
    SourceClarificationRequest,
)


def _info(text: str) -> str:
    return apply_speech_indicator(f"ℹ️ {text}")


def _failure(text: str) -> str:
    return apply_speech_indicator(f"❌ {text}")


def _syntax_block() -> str:
    return (
        "Sintaxe explícita:\n"
        "- pedido nu continua no pacote do host;\n"
        "- AUR exige 'no aur'; COPR exige 'do copr owner/project'; PPA exige 'do ppa ppa:owner/name';\n"
        "- Flatpak exige 'no flatpak' e pode exigir remote observado;\n"
        "- toolbox exige 'na toolbox <ambiente>'; distrobox exige 'na distrobox <ambiente>';\n"
        "- rpm-ostree exige 'no rpm-ostree'."
    )


def _no_discovery_clause() -> str:
    return (
        "Esta orientação não executa backend, não busca em tudo, não escolhe a melhor fonte, "
        "não cria ambiente, não adiciona remote e não faz fallback entre superfícies."
    )


def _inspect_clause(target: str) -> str:
    if not target:
        return "Use aurora dev \"<frase>\" para inspecionar uma frase operacional antes de executar."
    return f"Use aurora dev \"instalar {target}\" para inspecionar a leitura operacional antes de executar."


def _explain_sources() -> str:
    return _info(f"Fontes e superfícies precisam estar marcadas.\n{_syntax_block()}\n{_no_discovery_clause()}")


def _explain_surfaces() -> str:
    return _info(
        "Superfície é onde a ação acontece: host, Flatpak, toolbox, distrobox ou rpm-ostree.\n"
        "Fonte é de onde vem o pacote ou software: gerenciador do host, AUR, COPR, PPA, remote Flatpak ou backend do ambiente.\n"
        f"{_syntax_block()}\n{_no_discovery_clause()}"
    )


def _choose_source(target: str) -> str:
    return _info(
        f"Para escolher como pedir '{target}', marque a fonte ou superfície na frase.\n"
        f"{_syntax_block()}\n"
        f"{_inspect_clause(target)}\n"
        f"{_no_discovery_clause()}"
    )


def _where_install(target: str) -> str:
    return _info(
        f"Para decidir onde instalar '{target}', escreva a superfície explicitamente.\n"
        f"{_syntax_block()}\n"
        f"{_inspect_clause(target)}\n"
        f"{_no_discovery_clause()}"
    )


def _install_flatpak(target: str) -> str:
    return _info(
        f"Para orientar instalação Flatpak de '{target}', use marcador explícito:\n"
        f"- aurora dev \"instalar {target} no flatpak\"\n"
        f"- aurora instalar {target} no flatpak\n"
        "Flatpak usa remote observado; a Aurora não adiciona remote automaticamente.\n"
        f"{_no_discovery_clause()}"
    )


def _install_aur(target: str) -> str:
    return _info(
        f"Para orientar instalação AUR de '{target}', use marcador explícito:\n"
        f"- aurora dev \"instalar {target} no aur\"\n"
        f"- aurora instalar {target} no aur --confirm\n"
        "AUR é fonte terceira explícita; helper observado não vira AUR implícita.\n"
        f"{_no_discovery_clause()}"
    )


def _install_toolbox(target: str, environment: str) -> str:
    return _info(
        f"Para orientar instalação de '{target}' na toolbox '{environment}', nomeie o ambiente:\n"
        f"- aurora dev \"instalar {target} na toolbox {environment}\"\n"
        f"- aurora instalar {target} na toolbox {environment}\n"
        "A Aurora não cria toolbox, não escolhe ambiente default e não faz fallback para o host.\n"
        f"{_no_discovery_clause()}"
    )


def _install_distrobox(target: str, environment: str) -> str:
    return _info(
        f"Para orientar instalação de '{target}' na distrobox '{environment}', nomeie o ambiente:\n"
        f"- aurora dev \"instalar {target} na distrobox {environment}\"\n"
        f"- aurora instalar {target} na distrobox {environment}\n"
        "A Aurora não cria distrobox, não escolhe ambiente default e não faz fallback para o host.\n"
        f"{_no_discovery_clause()}"
    )


def _install_rpm_ostree(target: str) -> str:
    return _info(
        f"Para orientar instalação rpm-ostree de '{target}', use marcador explícito:\n"
        f"- aurora dev \"instalar {target} no rpm-ostree\"\n"
        f"- aurora instalar {target} no rpm-ostree\n"
        "rpm-ostree é superfície explícita de host imutável; busca rpm-ostree não está aberta neste recorte.\n"
        f"{_no_discovery_clause()}"
    )


def _compare_host_flatpak() -> str:
    return _info(
        "Host instala pacote do sistema via gerenciador da distribuição. Flatpak instala software de usuário via remote observado.\n"
        "Pedido nu continua no pacote do host; Flatpak exige 'no flatpak'.\n"
        f"{_no_discovery_clause()}"
    )


def _compare_aur_host() -> str:
    return _info(
        "Pacote do host é gerenciado pela distribuição. AUR é fonte terceira explícita e exige 'no aur'.\n"
        "Helper AUR observado não transforma pedido nu em AUR.\n"
        f"{_no_discovery_clause()}"
    )


def _block_automatic_source_choice(target: str) -> str:
    return _failure(
        f"Não escolho fonte ou superfície automaticamente para '{target}'. "
        "Refaça com marcador explícito: 'no aur', 'no flatpak', 'do copr owner/project', "
        "'do ppa ppa:owner/name', 'na toolbox <ambiente>', 'na distrobox <ambiente>' ou 'no rpm-ostree'. "
        "Pedido nu continua no pacote do host. Esta mensagem não executou backend nem gerou decision record."
    )


def render_source_clarification(request: SourceClarificationRequest) -> str:
    if request.kind == SourceClarificationKind.EXPLAIN_SOURCES:
        return _explain_sources()
    if request.kind == SourceClarificationKind.EXPLAIN_SURFACES:
        return _explain_surfaces()
    if request.kind == SourceClarificationKind.CHOOSE_SOURCE:
        return _choose_source(request.target)
    if request.kind == SourceClarificationKind.WHERE_INSTALL:
        return _where_install(request.target)
    if request.kind == SourceClarificationKind.INSTALL_FLATPAK:
        return _install_flatpak(request.target)
    if request.kind == SourceClarificationKind.INSTALL_AUR:
        return _install_aur(request.target)
    if request.kind == SourceClarificationKind.INSTALL_TOOLBOX:
        return _install_toolbox(request.target, request.environment)
    if request.kind == SourceClarificationKind.INSTALL_DISTROBOX:
        return _install_distrobox(request.target, request.environment)
    if request.kind == SourceClarificationKind.INSTALL_RPM_OSTREE:
        return _install_rpm_ostree(request.target)
    if request.kind == SourceClarificationKind.COMPARE_HOST_FLATPAK:
        return _compare_host_flatpak()
    if request.kind == SourceClarificationKind.COMPARE_AUR_HOST:
        return _compare_aur_host()
    if request.kind == SourceClarificationKind.BLOCK_AUTOMATIC_SOURCE_CHOICE:
        return _block_automatic_source_choice(request.target)
    raise ValueError(f"Unsupported source clarification kind: {request.kind.value}")

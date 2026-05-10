from __future__ import annotations

from aurora.presentation.profile import ProfileInput, render_profiled_response
from aurora.presentation.text_polish import apply_speech_indicator
from aurora.semantics.orientation import (
    QUESTION_INSTALL,
    QUESTION_REMOVE,
    QUESTION_SEARCH,
    QUESTION_UPDATE_SYSTEM,
    TOPIC_COMMANDS,
    TOPIC_DECISION_RECORD,
    TOPIC_EXAMPLES,
    TOPIC_LIMITS,
    TOPIC_LOCAL_MODEL,
    TOPIC_PRODUCT,
    TOPIC_SOURCES,
    TOPIC_USAGE,
    OrientationRequest,
)


def _info(text: str) -> str:
    return apply_speech_indicator(f"ℹ️ {text}")


def _topic_examples() -> str:
    return _info(
        "Exemplos seguros da Aurora:\n"
        "- aurora dev \"instalar firefox\"\n"
        "- aurora procurar firefox\n"
        "- aurora instalar firefox\n"
        "- aurora remover firefox --confirm\n"
        "- aurora atualizar sistema --confirm\n"
        "- aurora procurar firefox no flatpak\n"
        "- aurora procurar google chrome no aur\n"
        "- aurora procurar ripgrep na toolbox devbox\n"
        "Esses exemplos não escolhem fonte automaticamente; fontes e superfícies precisam estar explícitas."
    )


def _topic_limits() -> str:
    return _info(
        "Limites atuais:\n"
        "- conversa aqui é orientação determinística, não chat genérico;\n"
        "- perguntas do tipo 'como ...?' explicam próximos passos e não executam;\n"
        "- AUR, COPR, PPA, Flatpak, toolbox, distrobox e rpm-ostree não entram por fallback;\n"
        "- mutação real continua passando pelo kernel, pela policy e por confirmação quando exigida;\n"
        "- modelo local, quando ligado, segue assistivo e não decide rota, suporte ou execução."
    )


def _topic_commands() -> str:
    return _info(
        "Comandos sustentados nesta linha:\n"
        "- aurora ajuda | aurora --help\n"
        "- aurora versão | aurora --version\n"
        "- aurora dev <frase>\n"
        "- aurora procurar <pacote>\n"
        "- aurora instalar <pacote>\n"
        "- aurora remover <pacote> --confirm\n"
        "- aurora atualizar sistema --confirm\n"
        "Use marcadores explícitos para AUR, COPR, PPA, Flatpak, toolbox, distrobox e rpm-ostree."
    )


def _topic_sources() -> str:
    return _info(
        "Fontes e superfícies são explícitas:\n"
        "- pedido nu fica em host_package no host;\n"
        "- AUR exige 'no aur'; COPR exige 'do copr owner/project'; PPA exige 'do ppa ppa:owner/name';\n"
        "- Flatpak exige 'no flatpak' e pode receber remote explícito observado;\n"
        "- toolbox e distrobox exigem ambiente nomeado;\n"
        "- rpm-ostree exige marcador próprio.\n"
        "A Aurora não faz busca transversal nem escolhe a melhor fonte por conta própria."
    )


def _topic_local_model() -> str:
    return _info(
        "Modelo local:\n"
        "- model_off é o default e basta para a inspeção técnica;\n"
        "- model_on só entra por opt-in de ambiente;\n"
        "- a seam pode explicar, resumir, clarificar ou desambiguar candidatos já estruturados;\n"
        "- fallback determinístico preserva a verdade operacional se o provider faltar, falhar ou expirar;\n"
        "- modelo local não decide policy, suporte, bloqueio, confirmação, rota, execução ou resultado."
    )


def _topic_decision_record() -> str:
    return _info(
        "Decision record:\n"
        "- use aurora dev <frase> para ver a decisão antes de executar;\n"
        "- o schema público continua aurora.decision_record.v1;\n"
        "- stable_ids, facts e presentation são a espinha parseável;\n"
        "- texto de ajuda e conversa orientam, mas não viram contrato operacional."
    )


def _topic_product() -> str:
    return _info(
        "A Aurora recebe pedidos curtos de Linux, enquadra o domínio, aplica policy e executa, bloqueia ou mostra a leitura técnica. "
        "Nesta release, ela também responde tópicos de orientação em PT-BR para explicar uso, limites, fontes, modelo local e decision record, sem executar backend."
    )


def _topic_usage() -> str:
    return _info(
        "Uso recomendado:\n"
        "- comece por aurora ajuda, aurora exemplos ou aurora limites;\n"
        "- rode aurora dev \"<frase>\" quando quiser ler a decisão antes;\n"
        "- use comandos operacionais explícitos para executar;\n"
        "- adicione --confirm só quando você realmente quiser autorizar uma mutação exigida pela policy."
    )


def _question_install(target: str, *, profile: ProfileInput = None) -> str:
    return _info(
        render_profiled_response(
            f"Para instalar '{target}', primeiro inspecione a decisão.",
            steps=(
                f"aurora dev \"instalar {target}\"",
                f"aurora instalar {target}",
            ),
            limits=("não executei backend", "não escolhi fonte", "não alterei o sistema"),
            profile=profile,
        )
    )


def _question_search(target: str, *, profile: ProfileInput = None) -> str:
    return _info(
        render_profiled_response(
            f"Para procurar '{target}', use o comando operacional explícito.",
            steps=(
                f"aurora procurar {target}",
                f"aurora dev \"procurar {target}\"",
            ),
            limits=(
                "não fiz busca real nesta resposta",
                "não escolhi fonte",
                "marque AUR, COPR, PPA, Flatpak, toolbox, distrobox ou rpm-ostree explicitamente",
            ),
            profile=profile,
        )
    )


def _question_remove(target: str, *, profile: ProfileInput = None) -> str:
    return _info(
        render_profiled_response(
            f"Para remover '{target}', primeiro inspecione a decisão.",
            steps=(
                f"aurora dev \"remover {target}\"",
                f"aurora remover {target} --confirm",
            ),
            limits=("não removi nada", "não executei backend", "mutação real exige confirmação explícita"),
            profile=profile,
        )
    )


def _question_update_system(*, profile: ProfileInput = None) -> str:
    return _info(
        render_profiled_response(
            "Para atualizar o sistema no recorte atual, primeiro inspecione a decisão.",
            steps=(
                "aurora dev \"atualizar sistema\"",
                "aurora atualizar sistema --confirm",
            ),
            limits=(
                "não atualizei o sistema",
                "rota real exige confirmação explícita",
                "suporte aberto só no host Arch mutável com pacman observado e backend sudo + pacman",
            ),
            profile=profile,
        )
    )


def render_orientation(request: OrientationRequest, *, profile: ProfileInput = None) -> str:
    renderers = {
        TOPIC_EXAMPLES: _topic_examples,
        TOPIC_LIMITS: _topic_limits,
        TOPIC_COMMANDS: _topic_commands,
        TOPIC_SOURCES: _topic_sources,
        TOPIC_LOCAL_MODEL: _topic_local_model,
        TOPIC_DECISION_RECORD: _topic_decision_record,
        TOPIC_PRODUCT: _topic_product,
        TOPIC_USAGE: _topic_usage,
    }
    if request.topic == QUESTION_INSTALL:
        return _question_install(request.target, profile=profile)
    if request.topic == QUESTION_SEARCH:
        return _question_search(request.target, profile=profile)
    if request.topic == QUESTION_REMOVE:
        return _question_remove(request.target, profile=profile)
    if request.topic == QUESTION_UPDATE_SYSTEM:
        return _question_update_system(profile=profile)
    return renderers[request.topic]()

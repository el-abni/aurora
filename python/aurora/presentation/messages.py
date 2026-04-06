from __future__ import annotations

from aurora.presentation.text_polish import polish_public_text


def invalid_command_message() -> str:
    return "❌ comando inválido"


def backend_missing_message(name: str) -> str:
    return f"❌ backend '{name}' não está disponível"


def backend_failed_message(name: str, *, exit_code: int | None = None, detail: str = "") -> str:
    base = f"❌ backend '{name}' retornou erro operacional"
    if exit_code is not None:
        base += f" (exit code {exit_code})"
    if detail:
        return f"{base}. Motivo informado pelo backend: {detail}"
    return base


def interactive_handoff_start_message(name: str) -> str:
    return (
        f"ℹ️ vou entregar o terminal ao helper interativo '{name}'. "
        "A partir daqui, leia e responda aos prompts do helper; ele pode pedir Enter, seleção, revisão de build ou senha. "
        "Quando ele devolver o terminal, a Aurora valida o estado final."
    )


def interactive_handoff_return_message(name: str, exit_code: int) -> str:
    if exit_code == 0:
        return (
            f"ℹ️ o helper interativo '{name}' devolveu o terminal. "
            "Agora vou validar se o estado final realmente fechou."
        )
    return (
        f"ℹ️ o helper interativo '{name}' devolveu o terminal com exit code {exit_code}. "
        "Vou encerrar a rota com o status reportado pelo backend."
    )


def no_results_message(target: str, backend_name: str) -> str:
    return f"ℹ️ não encontrei resultados para '{target}' no backend '{backend_name}'."


def search_results_message(target: str, backend_name: str, details: str) -> str:
    if not details.strip():
        return f"✅ encontrei resultados para '{target}' no backend '{backend_name}'."
    return f"✅ encontrei resultados para '{target}' no backend '{backend_name}':\n{details.rstrip()}"


def package_not_found_message(
    intent: str,
    target: str,
    backend_name: str,
    *,
    target_label: str = "pacote",
) -> str:
    if intent == "instalar":
        return f"❌ não encontrei o {target_label} '{target}' no backend '{backend_name}'."
    return f"❌ não consegui localizar o {target_label} '{target}' no backend '{backend_name}' para remover."


def noop_message(
    intent: str,
    target: str,
    *,
    target_label: str = "pacote",
    location_label: str = "neste host",
) -> str:
    if intent == "instalar":
        return f"ℹ️ o {target_label} '{target}' já está instalado {location_label}. Nada foi feito."
    return f"ℹ️ o {target_label} '{target}' já não está instalado {location_label}. Nada foi feito."


def mutation_success_message(
    intent: str,
    target: str,
    *,
    target_label: str = "pacote",
) -> str:
    if intent == "instalar":
        return f"✅ pronto, o {target_label} '{target}' está instalado."
    return f"✅ pronto, o {target_label} '{target}' foi removido."


def rpm_ostree_noop_message(intent: str, target: str) -> str:
    if intent == "instalar":
        return (
            f"ℹ️ o pacote '{target}' já aparece no deployment atual ou no próximo deployment rpm-ostree. "
            "Nada foi feito."
        )
    return (
        f"ℹ️ o pacote '{target}' já não aparece como camada solicitada no deployment efetivo rpm-ostree. "
        "Nada foi feito."
    )


def rpm_ostree_mutation_success_message(intent: str, target: str) -> str:
    if intent == "instalar":
        return (
            f"✅ pronto, o pacote '{target}' foi adicionado ao próximo deployment rpm-ostree. "
            "Reinicie para aplicar."
        )
    return (
        f"✅ pronto, o pacote '{target}' foi removido do próximo deployment rpm-ostree. "
        "Reinicie para aplicar."
    )


def state_probe_missing_message(backend_name: str, probe_label: str) -> str:
    return (
        f"❌ a confirmação de estado para o backend '{backend_name}' depende da ferramenta "
        f"auxiliar '{probe_label}', que não está disponível."
    )


def state_confirmation_failed_message(
    intent: str,
    target: str,
    backend_name: str,
    *,
    detail: str = "",
) -> str:
    if intent == "instalar":
        base = f"❌ o backend '{backend_name}' terminou sem eu conseguir confirmar a instalação de '{target}'."
    else:
        base = f"❌ o backend '{backend_name}' terminou sem eu conseguir confirmar a remoção de '{target}'."
    if detail:
        return f"{base} Estado observado depois da execução: {detail}"
    return base


def blocked_message(reason: str) -> str:
    return f"❌ bloqueado por política: {polish_public_text(reason)}"


def target_resolution_blocked_message(reason: str) -> str:
    return f"❌ bloqueado por resolução de alvo: {polish_public_text(reason)}"


def confirmation_required_message(
    target: str,
    software_criticality: str,
    reversal_level: str,
    *,
    target_label: str = "pacote",
) -> str:
    return (
        f"❌ a mutação do {target_label} '{target}' exige confirmação explícita nesta rodada "
        f"(criticidade {software_criticality}; reversão {reversal_level}). Use --confirm para prosseguir."
    )


def out_of_scope_message(reason: str) -> str:
    return f"❌ fora do recorte atual: {polish_public_text(reason)}"


def not_implemented_message(intent: str, domain_kind: str) -> str:
    return (
        f"❌ '{intent}' em '{domain_kind}' já foi classificado e planejado, "
        "mas a execução real ainda não foi aberta nesta rodada."
    )

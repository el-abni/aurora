from __future__ import annotations

from aurora.presentation.text_polish import apply_speech_indicator, polish_public_text


def _voice(text: str) -> str:
    return apply_speech_indicator(text)


def _failure(text: str) -> str:
    return _voice(f"❌ {text}")


def _success(text: str) -> str:
    return _voice(f"✅ {text}")


def _info(text: str) -> str:
    return _voice(f"ℹ️ {text}")


def invalid_command_message() -> str:
    return _voice("❌ Comando inválido.")


def missing_dev_phrase_message() -> str:
    return _voice("❌ Informe uma frase para inspeção.")


def backend_missing_message(name: str) -> str:
    return _failure(f"Não consegui usar o backend '{name}' porque ele não está disponível.")


def backend_failed_message(name: str, *, exit_code: int | None = None, detail: str = "") -> str:
    base = f"Não consegui concluir a operação no backend '{name}'"
    if exit_code is not None:
        base += f" (exit code {exit_code})"
    if detail:
        return _failure(f"{base}. Detalhe informado pelo backend: {detail}")
    return _failure(f"{base}.")


def interactive_handoff_start_message(name: str) -> str:
    return _info(
        f"Agora o terminal está com o helper interativo '{name}'. "
        "Leia e responda aos prompts do helper; ele pode pedir Enter, seleção, revisão de build ou senha. "
        "Também pode haver uma pausa silenciosa durante o build e, em alguns terminais, um Enter extra ao final. "
        "Quando o helper devolver o controle, a Aurora valida o estado final."
    )


def interactive_handoff_return_message(name: str, exit_code: int) -> str:
    if exit_code == 0:
        return _info(
            f"O helper interativo '{name}' devolveu o controle do terminal. "
            "Agora a Aurora vai validar se o estado final realmente fechou."
        )
    return _info(
        f"O helper interativo '{name}' devolveu o controle do terminal com exit code {exit_code}. "
        "A Aurora vai encerrar a rota com o status reportado pelo backend."
    )


def mediated_execution_start_message(
    execution_surface: str,
    environment_name: str,
    backend_name: str,
) -> str:
    environment_label = (
        f"na {execution_surface} '{environment_name}'"
        if environment_name
        else f"na {execution_surface} selecionada"
    )
    return _info(
        f"Vou iniciar a execução mediada {environment_label} com o backend '{backend_name}'. "
        "A partir daqui, pode haver espera silenciosa enquanto o backend interno trabalha; ele também pode pedir senha e, em alguns terminais, exigir um Enter extra ao final. "
        "Quando o comando devolver o controle, a Aurora valida o estado final."
    )


def mediated_execution_return_message(
    execution_surface: str,
    environment_name: str,
    exit_code: int,
) -> str:
    environment_label = (
        f"na {execution_surface} '{environment_name}'"
        if environment_name
        else f"na {execution_surface} selecionada"
    )
    if exit_code == 0:
        return _info(
            f"A execução mediada {environment_label} devolveu o controle. "
            "Agora a Aurora vai validar se o estado final realmente fechou."
        )
    return _info(
        f"A execução mediada {environment_label} devolveu o controle com exit code {exit_code}. "
        "A Aurora vai encerrar a rota com o status reportado pelo backend."
    )


def no_results_message(target: str, backend_name: str) -> str:
    return _info(f"Não encontrei resultados para '{target}' no backend '{backend_name}'.")


def search_results_message(target: str, backend_name: str, details: str) -> str:
    if not details.strip():
        return _success(f"Encontrei resultados para '{target}' no backend '{backend_name}'.")
    return _success(f"Encontrei resultados para '{target}' no backend '{backend_name}':\n{details.rstrip()}")


def package_not_found_message(
    intent: str,
    target: str,
    backend_name: str,
    *,
    target_label: str = "pacote",
) -> str:
    if intent == "instalar":
        return _failure(f"Não encontrei o {target_label} '{target}' no backend '{backend_name}'.")
    return _failure(f"Não consegui localizar o {target_label} '{target}' no backend '{backend_name}' para remover.")


def noop_message(
    intent: str,
    target: str,
    *,
    target_label: str = "pacote",
    location_label: str = "neste host",
) -> str:
    if intent == "instalar":
        return _info(f"O {target_label} '{target}' já está instalado {location_label}. Nenhuma ação foi necessária.")
    return _info(f"O {target_label} '{target}' já não está instalado {location_label}. Nenhuma ação foi necessária.")


def mutation_success_message(
    intent: str,
    target: str,
    *,
    target_label: str = "pacote",
) -> str:
    if intent == "instalar":
        return _success(f"Pronto, eu confirmei que o {target_label} '{target}' está instalado.")
    return _success(f"Pronto, eu confirmei que o {target_label} '{target}' foi removido.")


def rpm_ostree_noop_message(intent: str, target: str) -> str:
    if intent == "instalar":
        return _info(
            f"O pacote '{target}' já aparece no deployment atual ou no próximo deployment rpm-ostree. "
            "Nenhuma ação foi necessária."
        )
    return _info(
        f"O pacote '{target}' já não aparece como camada solicitada no deployment efetivo rpm-ostree. "
        "Nenhuma ação foi necessária."
    )


def rpm_ostree_mutation_success_message(intent: str, target: str) -> str:
    if intent == "instalar":
        return _success(
            f"Pronto, eu confirmei que o pacote '{target}' foi adicionado ao próximo deployment rpm-ostree. "
            "Reinicie para aplicar."
        )
    return _success(
        f"Pronto, eu confirmei que o pacote '{target}' foi removido do próximo deployment rpm-ostree. "
        "Reinicie para aplicar."
    )


def state_probe_missing_message(backend_name: str, probe_label: str) -> str:
    return _failure(
        f"A confirmação de estado para o backend '{backend_name}' depende da ferramenta "
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
        base = f"Não consegui confirmar a instalação de '{target}' depois que o backend '{backend_name}' terminou."
    else:
        base = f"Não consegui confirmar a remoção de '{target}' depois que o backend '{backend_name}' terminou."
    if detail:
        return _failure(f"{base} Estado observado depois da execução: {detail}")
    return _failure(base)


def blocked_message(reason: str) -> str:
    return _voice(f"❌ Bloqueado por política: {polish_public_text(reason)}")


def target_resolution_blocked_message(reason: str) -> str:
    return _voice(f"❌ Bloqueado por resolução de alvo: {polish_public_text(reason)}")


def confirmation_required_message(
    target: str,
    software_criticality: str,
    reversal_level: str,
    *,
    target_label: str = "pacote",
) -> str:
    return _voice(
        f"❌ Bloqueado por política: a mutação do {target_label} '{target}' exige confirmação explícita nesta rodada "
        f"(criticidade {software_criticality}; reversão {reversal_level}). Use --confirm para prosseguir."
    )


def out_of_scope_message(reason: str) -> str:
    return _voice(f"❌ Fora do recorte atual: {polish_public_text(reason)}")


def not_implemented_message(intent: str, domain_kind: str) -> str:
    return _voice(
        f"❌ '{intent}' em '{domain_kind}' já foi classificado e planejado, "
        "mas a execução real ainda não foi aberta nesta rodada."
    )

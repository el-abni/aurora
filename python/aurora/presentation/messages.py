from __future__ import annotations


def invalid_command_message() -> str:
    return "❌ comando inválido"


def backend_missing_message(name: str) -> str:
    return f"❌ backend '{name}' não está disponível"


def backend_failed_message(name: str) -> str:
    return f"❌ backend '{name}' retornou erro operacional"


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


def state_probe_missing_message(backend_name: str, probe_label: str) -> str:
    return (
        f"❌ a confirmação de estado para o backend '{backend_name}' depende da ferramenta "
        f"auxiliar '{probe_label}', que não está disponível."
    )


def state_confirmation_failed_message(intent: str, target: str, backend_name: str) -> str:
    if intent == "instalar":
        return f"❌ o backend '{backend_name}' terminou sem eu conseguir confirmar a instalação de '{target}'."
    return f"❌ o backend '{backend_name}' terminou sem eu conseguir confirmar a remoção de '{target}'."


def blocked_message(reason: str) -> str:
    return f"❌ bloqueado por política: {reason}"


def target_resolution_blocked_message(reason: str) -> str:
    return f"❌ bloqueado por resolução de alvo: {reason}"


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
    return f"❌ fora do recorte atual: {reason}"


def not_implemented_message(intent: str, domain_kind: str) -> str:
    return (
        f"❌ '{intent}' em '{domain_kind}' ja foi classificado e planejado, "
        "mas a execucao real ainda nao foi aberta nesta rodada."
    )

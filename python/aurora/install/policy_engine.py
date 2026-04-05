from __future__ import annotations

import os
import shutil

from aurora.contracts.decisions import EnvironmentResolution
from aurora.contracts.host import HostProfile
from aurora.contracts.policy import PolicyAssessment
from aurora.contracts.requests import SemanticRequest
from aurora.install.sources.aur import (
    observed_out_of_contract_aur_helpers,
    supported_aur_helper,
    supported_aur_helpers,
)
from aurora.install.sources.copr import (
    observe_copr_capability,
    observe_copr_package_origin,
    observe_copr_repository_state,
)
from aurora.install.sources.flatpak import (
    flatpak_effective_remote,
    flatpak_remote_origin,
    flatpak_requested_remote,
    observe_flatpak_remotes,
)
from aurora.install.sources.ppa import observe_ppa_capability, supported_ppa_distro_ids
from aurora.linux.immutable_policy import host_package_block_reason
from aurora.linux.toolbox import ToolboxProfileProbe

_CRITICAL_PACKAGE_NAMES = {
    "apt",
    "apt-get",
    "bash",
    "coreutils",
    "dnf",
    "dpkg",
    "glibc",
    "grub",
    "linux",
    "networkmanager",
    "openssh",
    "pacman",
    "rpm",
    "sudo",
    "systemd",
    "util-linux",
    "zypper",
}
_CRITICAL_PACKAGE_PREFIXES = (
    "glibc",
    "grub",
    "kernel",
    "linux",
    "networkmanager",
    "openssh",
    "systemd",
)


def _host_package_software_criticality(request: SemanticRequest) -> str:
    if request.intent == "procurar":
        return "low"

    target = request.target.strip().lower()
    is_critical = target in _CRITICAL_PACKAGE_NAMES or any(
        target == prefix or target.startswith(f"{prefix}-") for prefix in _CRITICAL_PACKAGE_PREFIXES
    )
    if not is_critical:
        return "medium"
    if request.intent == "remover":
        return "sensitive"
    return "high"


def _host_package_reversal_level(intent: str, software_criticality: str) -> str:
    if intent == "procurar":
        return "informational"
    if intent == "instalar":
        return "host_change_sensitive" if software_criticality in {"high", "sensitive"} else "host_change"
    if software_criticality == "sensitive":
        return "hard_to_reverse"
    return "reinstall_required"


def _assess_host_package_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    confirmation_supplied: bool = False,
) -> PolicyAssessment | None:
    software_criticality = _host_package_software_criticality(request)
    reversal_level = _host_package_reversal_level(request.intent, software_criticality)
    requires_confirmation = (
        request.intent in {"instalar", "remover"} and software_criticality in {"high", "sensitive"}
    )

    if profile is None:
        return PolicyAssessment(
            domain_kind="host_package",
            source_type="host_package_manager",
            trust_level="distribution_managed",
            software_criticality=software_criticality,
            trust_signals=(),
            trust_gaps=("host_profile_unavailable",),
            policy_outcome="block",
            requires_confirmation=requires_confirmation,
            confirmation_supplied=confirmation_supplied,
            reversal_level=reversal_level,
            reason="o host profile nao esta disponivel.",
        )

    trust_signals = [
        f"linux_family:{profile.linux_family}",
        f"mutability:{profile.mutability}",
        f"support_tier:{profile.support_tier}",
        f"software_criticality:{software_criticality}",
    ]
    if profile.package_backends:
        trust_signals.append(f"observed_backends:{','.join(profile.package_backends)}")
    if profile.linux_family == "arch":
        trust_signals.append("arch_host_package_contract:pacman")
    if profile.observed_third_party_package_tools:
        observed_tools = ",".join(profile.observed_third_party_package_tools)
        trust_signals.append(f"observed_third_party_package_tools:{observed_tools}")
    if confirmation_supplied:
        trust_signals.append("confirmation:explicit")

    trust_gaps: list[str] = []
    outcome = "allow"
    reason = "host_package no host mutavel suportado por familia/host."

    if request.status != "CONSISTENT":
        outcome = "block"
        trust_gaps.append("request_not_consistent")
        reason = request.reason
    elif profile.mutability == "atomic":
        outcome = "block"
        trust_gaps.append("host_mutation_blocked_on_atomic")
        reason, _message = host_package_block_reason(profile)
    elif profile.support_tier == "out_of_scope":
        outcome = "block"
        trust_gaps.append("linux_family_out_of_scope")
        reason = "a familia Linux deste host ficou fora do recorte atual de host_package."
    elif profile.support_tier == "tier_2":
        trust_gaps.append("opensuse_support_is_contained")
        reason = "host_package permitido em OpenSUSE mutavel contido nesta rodada."

    if profile.linux_family == "arch" and profile.observed_third_party_package_tools:
        trust_gaps.append("arch_aur_helpers_observed_out_of_contract")

    if outcome == "allow" and profile.linux_family == "arch" and "pacman" not in profile.package_backends:
        outcome = "block"
        trust_gaps.append("arch_host_package_backend_not_observed")
        if profile.observed_third_party_package_tools:
            reason = (
                "o contrato de host_package em Arch continua ancorado em pacman; "
                "helper AUR observado nao substitui backend oficial nesta rodada."
            )
        else:
            reason = "o backend oficial pacman nao foi observado neste host Arch."

    if not profile.package_backends:
        trust_gaps.append("no_host_package_backend_observed")

    if outcome == "allow" and requires_confirmation and not confirmation_supplied:
        outcome = "require_confirmation"
        trust_gaps.append("confirmation_missing_for_sensitive_mutation")
        reason = (
            "esta mutacao toca um pacote de criticidade elevada e exige confirmacao explicita nesta rodada."
        )

    return PolicyAssessment(
        domain_kind="host_package",
        source_type="host_package_manager",
        trust_level="distribution_managed",
        software_criticality=software_criticality,
        trust_signals=tuple(trust_signals),
        trust_gaps=tuple(trust_gaps),
        policy_outcome=outcome,
        requires_confirmation=requires_confirmation,
        confirmation_supplied=confirmation_supplied,
        reversal_level=reversal_level,
        reason=reason,
    )


def _toolbox_software_criticality(request: SemanticRequest) -> str:
    if request.intent == "procurar":
        return "low"
    return "medium"


def _toolbox_reversal_level(intent: str) -> str:
    if intent == "procurar":
        return "informational"
    if intent == "instalar":
        return "mediated_environment_change"
    return "mediated_environment_removal"


def _toolbox_environment_gap(status: str) -> str:
    if status == "missing":
        return "toolbox_environment_target_missing"
    if status == "not_found":
        return "toolbox_environment_not_observed"
    if status == "ambiguous":
        return "toolbox_environment_ambiguous"
    return "toolbox_environment_not_resolved"


def _assess_toolbox_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    environment_resolution: EnvironmentResolution | None = None,
    toolbox_profile: HostProfile | None = None,
    toolbox_profile_probe: ToolboxProfileProbe | None = None,
    confirmation_supplied: bool = False,
) -> PolicyAssessment | None:
    software_criticality = _toolbox_software_criticality(request)
    reversal_level = _toolbox_reversal_level(request.intent)
    requires_confirmation = request.intent == "remover"

    if profile is None:
        return PolicyAssessment(
            domain_kind="host_package",
            source_type="toolbox_host_package_manager",
            trust_level="mediated_environment",
            software_criticality=software_criticality,
            trust_signals=(),
            trust_gaps=("host_profile_unavailable",),
            policy_outcome="block",
            requires_confirmation=requires_confirmation,
            confirmation_supplied=confirmation_supplied,
            reversal_level=reversal_level,
            reason="o host profile nao esta disponivel para abrir a superficie toolbox.",
            execution_surface="toolbox",
        )

    trust_signals = [
        "execution_surface:toolbox",
        "domain:host_package",
        "source_type:toolbox_host_package_manager",
        f"host_mutability:{profile.mutability}",
        f"software_criticality:{software_criticality}",
        (
            f"toolbox_requested_environment:{request.environment_target}"
            if request.environment_target
            else "toolbox_requested_environment:-"
        ),
    ]
    if profile.observed_environment_tools:
        trust_signals.append(f"observed_environment_tools:{','.join(profile.observed_environment_tools)}")
    if profile.observed_toolbox_environments:
        trust_signals.append(
            f"observed_toolbox_environments:{','.join(profile.observed_toolbox_environments)}"
        )
    if environment_resolution is not None:
        trust_signals.append(f"toolbox_environment_status:{environment_resolution.status}")
        if environment_resolution.resolved_environment:
            trust_signals.append(
                f"toolbox_resolved_environment:{environment_resolution.resolved_environment}"
            )
    if toolbox_profile is not None:
        trust_signals.extend(
            (
                f"toolbox_linux_family:{toolbox_profile.linux_family}",
                f"toolbox_support_tier:{toolbox_profile.support_tier}",
                (
                    f"toolbox_package_backends:{','.join(toolbox_profile.package_backends)}"
                    if toolbox_profile.package_backends
                    else "toolbox_package_backends:-"
                ),
            )
        )
    if toolbox_profile_probe is not None and toolbox_profile_probe.observed_commands:
        trust_signals.append(
            f"toolbox_observed_commands:{','.join(toolbox_profile_probe.observed_commands)}"
        )
        trust_signals.append(
            f"toolbox_sudo_observed:{'true' if toolbox_profile_probe.sudo_observed else 'false'}"
        )
    if confirmation_supplied:
        trust_signals.append("confirmation:explicit")

    trust_gaps = [
        "toolbox_default_selection_not_opened",
        "toolbox_create_not_opened",
        "toolbox_lifecycle_not_opened",
        "toolbox_host_fallback_not_opened",
    ]
    if request.intent in {"instalar", "remover"}:
        trust_gaps.append("toolbox_mutation_requires_exact_package_name")

    outcome = "allow"
    reason = "toolbox explicita foi aceita como superficie mediada distinta do host nesta release."

    if request.status != "CONSISTENT":
        outcome = "block"
        trust_gaps.append("request_not_consistent")
        reason = request.reason
    elif request.domain_kind != "host_package" or request.requested_source:
        outcome = "block"
        trust_gaps.append("toolbox_scope_not_supported")
        reason = (
            "toolbox explicita nesta rodada cobre apenas pacotes distro-managed dentro da toolbox, "
            "sem misturar AUR, COPR, PPA ou flatpak."
        )
    elif "toolbox" not in profile.observed_environment_tools:
        outcome = "block"
        trust_gaps.append("toolbox_command_not_observed")
        reason = (
            "o comando 'toolbox' nao foi observado neste host. "
            "esta release nao cria ambiente automaticamente nem usa toolbox como fallback implicito."
        )
    elif environment_resolution is None or environment_resolution.status != "resolved":
        outcome = "block"
        if environment_resolution is not None:
            trust_gaps.append(_toolbox_environment_gap(environment_resolution.status))
            reason = environment_resolution.reason
        else:
            trust_gaps.append("toolbox_environment_not_resolved")
            reason = "nao consegui resolver o ambiente toolbox explicitamente pedido."
    elif toolbox_profile_probe is not None and not toolbox_profile_probe.observed:
        outcome = "block"
        trust_gaps.append(toolbox_profile_probe.gap or "toolbox_profile_not_observed")
        reason = toolbox_profile_probe.reason
    elif toolbox_profile is None:
        outcome = "block"
        trust_gaps.append("toolbox_profile_not_observed")
        reason = "nao consegui observar a familia Linux e o backend de pacote dentro da toolbox selecionada."
    elif toolbox_profile.support_tier == "out_of_scope":
        outcome = "block"
        trust_gaps.append("toolbox_linux_family_out_of_scope")
        reason = (
            "a familia Linux observada dentro da toolbox ficou fora do recorte atual. "
            "esta release so cobre backends distro-managed conhecidos."
        )
    elif not toolbox_profile.package_backends:
        outcome = "block"
        trust_gaps.append("toolbox_backend_not_observed")
        reason = (
            "nao observei um backend distro-managed suportado dentro da toolbox selecionada. "
            "esta release nao abre mutacao cega nem heuristica ampla de ambiente."
        )
    elif request.intent in {"instalar", "remover"} and (
        toolbox_profile_probe is None or not toolbox_profile_probe.sudo_observed
    ):
        outcome = "block"
        trust_gaps.append("toolbox_sudo_not_observed")
        reason = (
            "nao observei 'sudo' dentro da toolbox selecionada. "
            "esta release nao tenta mutar o ambiente mediado sem capacidade minima explicitamente observada."
        )
    elif request.intent == "procurar":
        reason = (
            f"toolbox.procurar foi aceito dentro da toolbox '{environment_resolution.resolved_environment}', "
            "mantendo clara a fronteira entre host e ambiente mediado."
        )
    elif request.intent == "instalar":
        reason = (
            f"toolbox.instalar foi aceito dentro da toolbox '{environment_resolution.resolved_environment}', "
            "sem criar ambiente automaticamente e sem tocar o host."
        )
    elif request.intent == "remover":
        reason = (
            f"toolbox.remover foi aceito dentro da toolbox '{environment_resolution.resolved_environment}', "
            "com confirmacao explicita para deixar visivel a mutacao mediada."
        )

    if outcome == "allow" and requires_confirmation and not confirmation_supplied:
        outcome = "require_confirmation"
        trust_gaps.append("confirmation_missing_for_toolbox_removal")
        reason = "a remocao dentro da toolbox exige confirmacao explicita nesta rodada."

    return PolicyAssessment(
        domain_kind="host_package",
        source_type="toolbox_host_package_manager",
        trust_level="mediated_environment",
        software_criticality=software_criticality,
        trust_signals=tuple(trust_signals),
        trust_gaps=tuple(trust_gaps),
        policy_outcome=outcome,
        requires_confirmation=requires_confirmation,
        confirmation_supplied=confirmation_supplied,
        reversal_level=reversal_level,
        reason=reason,
        execution_surface="toolbox",
    )


def _user_software_software_criticality(request: SemanticRequest) -> str:
    if request.intent == "procurar":
        return "low"
    return "medium"


def _user_software_reversal_level(intent: str) -> str:
    if intent == "procurar":
        return "informational"
    if intent == "instalar":
        return "user_scope_change"
    return "user_scope_removal"


def _assess_user_software_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    confirmation_supplied: bool = False,
    environ: dict[str, str] | None = None,
) -> PolicyAssessment | None:
    software_criticality = _user_software_software_criticality(request)
    reversal_level = _user_software_reversal_level(request.intent)
    requires_confirmation = request.intent == "remover"

    if profile is None:
        return PolicyAssessment(
            domain_kind="user_software",
            source_type="flatpak_remote",
            trust_level="guarded",
            software_criticality=software_criticality,
            trust_signals=(),
            trust_gaps=("host_profile_unavailable",),
            policy_outcome="block",
            requires_confirmation=requires_confirmation,
            confirmation_supplied=confirmation_supplied,
            reversal_level=reversal_level,
            reason="o host profile nao esta disponivel.",
        )

    source_hint = next(
        (item.split(":", 1)[1] for item in request.observations if item.startswith("source_hint:")),
        "flatpak",
    )
    requested_remote = flatpak_requested_remote(request)
    effective_remote = flatpak_effective_remote(request)
    remote_origin = flatpak_remote_origin(request)
    observed_remotes = observe_flatpak_remotes(profile, environ=environ)
    trust_signals = [
        "domain:user_software",
        "source_type:flatpak_remote",
        f"source_hint:{source_hint}",
        f"mutability:{profile.mutability}",
        f"software_criticality:{software_criticality}",
        f"flatpak_remote_origin:{remote_origin}",
    ]
    if requested_remote:
        trust_signals.append(f"flatpak_requested_remote:{requested_remote}")
    if effective_remote:
        trust_signals.append(f"flatpak_effective_remote:{effective_remote}")
    if observed_remotes:
        trust_signals.append(f"flatpak_observed_remotes:{','.join(observed_remotes)}")
    trust_gaps: list[str] = []
    if request.intent in {"instalar", "remover"}:
        trust_signals.append("installation_scope:user")
    if remote_origin == "default" and effective_remote:
        trust_signals.append(f"flatpak_remote_default:{effective_remote}")
    if request.intent == "remover" and requested_remote:
        trust_signals.append("flatpak_remove_origin_constraint:enabled")
    trust_gaps.append("flatpak_remote_management_not_opened")
    if request.intent == "procurar":
        trust_gaps.append("flatpak_search_within_selected_remote_only")
    elif request.intent == "instalar":
        trust_gaps.append("flatpak_remote_auto_add_not_supported")
    elif request.intent == "remover" and requested_remote:
        trust_gaps.append("flatpak_remove_uses_remote_only_as_origin_constraint")
    if "flatpak" in profile.observed_package_tools:
        trust_signals.append("backend:flatpak_observed")
    if confirmation_supplied:
        trust_signals.append("confirmation:explicit")

    outcome = "allow"
    reason = "user_software via flatpak foi aceito como rota explicita nesta release."

    if request.status != "CONSISTENT":
        outcome = "block"
        trust_gaps.append("request_not_consistent")
        reason = request.reason
    elif "flatpak" not in profile.observed_package_tools:
        outcome = "block"
        trust_gaps.append("flatpak_backend_not_observed")
        reason = "o backend flatpak nao foi observado neste host."
    elif effective_remote and not observed_remotes:
        outcome = "block"
        trust_gaps.append("flatpak_remotes_not_observed")
        reason = (
            "nao consegui observar remotes Flatpak neste host. "
            "esta release so aceita search/install em remote explicitamente observavel."
        )
    elif effective_remote and effective_remote not in observed_remotes:
        outcome = "block"
        trust_gaps.append("flatpak_selected_remote_not_observed")
        if requested_remote:
            reason = (
                f"o remote Flatpak explicitamente pedido '{effective_remote}' nao foi observado neste host. "
                "esta release nao faz add automatico nem descoberta ampla de remotes."
            )
        else:
            reason = (
                f"o remote default '{effective_remote}' nao foi observado neste host. "
                "esta release nao faz add automatico de remotes."
            )
    elif request.intent == "procurar" and effective_remote:
        reason = (
            f"flatpak.procurar foi aceito no remote "
            f"{'explicito' if requested_remote else 'default'} '{effective_remote}' ja observado neste host."
        )
    elif request.intent == "instalar":
        if requested_remote:
            reason = (
                f"flatpak.instalar usa installation scope explicito de usuario no remote "
                f"explicito '{effective_remote}', ja observado neste host."
            )
        else:
            reason = (
                f"flatpak.instalar usa installation scope explicito de usuario e assume o remote default "
                f"'{effective_remote}', ja observado neste host."
            )
    elif request.intent == "remover":
        if requested_remote:
            reason = (
                f"flatpak.remover usa installation scope explicito de usuario e respeita o remote "
                f"explicito '{requested_remote}' apenas como restricao de origin nesta rodada."
            )
        else:
            reason = "flatpak.remover usa installation scope explicito de usuario nesta rodada."

    if outcome == "allow" and requires_confirmation and not confirmation_supplied:
        outcome = "require_confirmation"
        trust_gaps.append("confirmation_missing_for_user_software_removal")
        reason = (
            "a remocao de software do usuario via flatpak exige confirmacao explicita nesta rodada."
        )

    return PolicyAssessment(
        domain_kind="user_software",
        source_type="flatpak_remote",
        trust_level="guarded",
        software_criticality=software_criticality,
        trust_signals=tuple(trust_signals),
        trust_gaps=tuple(trust_gaps),
        policy_outcome=outcome,
        requires_confirmation=requires_confirmation,
        confirmation_supplied=confirmation_supplied,
        reversal_level=reversal_level,
        reason=reason,
    )


def _aur_software_criticality(request: SemanticRequest) -> str:
    if request.intent == "procurar":
        return "low"
    return "medium"


def _aur_reversal_level(intent: str) -> str:
    if intent == "procurar":
        return "informational"
    if intent == "instalar":
        return "third_party_host_change"
    return "third_party_host_removal"


def _assess_aur_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    confirmation_supplied: bool = False,
) -> PolicyAssessment | None:
    software_criticality = _aur_software_criticality(request)
    reversal_level = _aur_reversal_level(request.intent)
    requires_confirmation = request.intent in {"instalar", "remover"}
    supported_helpers = supported_aur_helpers()
    supported_helpers_label = ", ".join(supported_helpers)

    if profile is None:
        return PolicyAssessment(
            domain_kind="host_package",
            source_type="aur_repository",
            trust_level="third_party_build",
            software_criticality=software_criticality,
            trust_signals=("source_request:aur",),
            trust_gaps=("host_profile_unavailable", "aur_third_party_source_requires_human_review"),
            policy_outcome="block",
            requires_confirmation=requires_confirmation,
            confirmation_supplied=confirmation_supplied,
            reversal_level=reversal_level,
            reason="o host profile nao esta disponivel para validar a rota AUR.",
        )

    source_hint = next(
        (item.split(":", 1)[1] for item in request.observations if item.startswith("source_hint:")),
        "aur",
    )
    helper = supported_aur_helper(profile)
    observed_helpers = profile.observed_third_party_package_tools
    out_of_contract_helpers = observed_out_of_contract_aur_helpers(profile)
    trust_signals = [
        "domain:host_package",
        "source_type:aur_repository",
        "source_request:aur",
        f"source_hint:{source_hint}",
        f"linux_family:{profile.linux_family}",
        f"mutability:{profile.mutability}",
        f"software_criticality:{software_criticality}",
        f"aur_helpers_supported:{supported_helpers_label}",
    ]
    if profile.package_backends:
        trust_signals.append(f"observed_backends:{','.join(profile.package_backends)}")
    if observed_helpers:
        trust_signals.append(
            f"observed_third_party_package_tools:{','.join(observed_helpers)}"
        )
        supported_observed_helpers = tuple(
            helper_name for helper_name in supported_helpers if helper_name in observed_helpers
        )
        if supported_observed_helpers:
            trust_signals.append(
                f"aur_supported_helpers_observed:{','.join(supported_observed_helpers)}"
            )
    if helper is not None:
        trust_signals.append(f"aur_helper_selected:{helper}")
    if out_of_contract_helpers:
        trust_signals.append(f"observed_out_of_contract_aur_helpers:{','.join(out_of_contract_helpers)}")
    if confirmation_supplied:
        trust_signals.append("confirmation:explicit")

    trust_gaps = ["aur_third_party_source_requires_human_review"]
    if out_of_contract_helpers:
        trust_gaps.append("aur_helper_out_of_contract_observed")

    outcome = "allow"
    reason = "AUR explicito foi aceito como fonte de terceiro pequena e observavel nesta rodada."

    if request.status != "CONSISTENT":
        outcome = "block"
        trust_gaps.append("request_not_consistent")
        reason = request.reason
    elif profile.linux_family != "arch":
        outcome = "block"
        trust_gaps.append("aur_linux_family_not_supported")
        reason = "AUR explicito nesta rodada so abre em hosts da familia Arch."
    elif profile.mutability == "atomic":
        outcome = "block"
        trust_gaps.append("aur_blocked_on_atomic_host")
        reason = "AUR explicito continua bloqueado em hosts Atomic/imutaveis nesta rodada."
    elif "pacman" not in profile.package_backends:
        outcome = "block"
        trust_gaps.append("aur_pacman_backend_not_observed")
        reason = "AUR explicito depende de pacman observado para probe e separacao entre native e foreign."
    elif helper is None:
        outcome = "block"
        if observed_helpers:
            trust_gaps.append("aur_supported_helper_not_observed")
            observed_helpers_label = ", ".join(observed_helpers)
            reason = (
                f"observei helper(s) AUR no host ({observed_helpers_label}), mas a frente explicita aceita "
                f"apenas {supported_helpers_label} nesta rodada."
            )
        else:
            trust_gaps.append("aur_helper_not_observed")
            reason = f"nenhum helper AUR suportado nesta rodada ({supported_helpers_label}) foi observado no host."
    elif request.intent == "procurar":
        reason = f"aur.procurar foi aceito como leitura explicita do AUR via {helper} nesta rodada."
    else:
        reason = (
            "mutacoes AUR exigem confirmacao explicita e continuam sinalizadas como fonte terceira "
            f"nesta rodada. helper selecionado: {helper}."
        )

    if outcome == "allow" and requires_confirmation and not confirmation_supplied:
        outcome = "require_confirmation"
        trust_gaps.append("confirmation_missing_for_aur_mutation")
        reason = "a mutacao explicitamente marcada como AUR exige confirmacao explicita nesta rodada."

    return PolicyAssessment(
        domain_kind="host_package",
        source_type="aur_repository",
        trust_level="third_party_build",
        software_criticality=software_criticality,
        trust_signals=tuple(trust_signals),
        trust_gaps=tuple(trust_gaps),
        policy_outcome=outcome,
        requires_confirmation=requires_confirmation,
        confirmation_supplied=confirmation_supplied,
        reversal_level=reversal_level,
        reason=reason,
    )


def _copr_software_criticality(request: SemanticRequest) -> str:
    if request.intent == "procurar":
        return "low"
    return "medium"


def _copr_reversal_level(intent: str) -> str:
    if intent == "procurar":
        return "informational"
    if intent == "instalar":
        return "third_party_host_change"
    return "third_party_host_removal"


def _ppa_software_criticality(_request: SemanticRequest) -> str:
    return "medium"


def _ppa_reversal_level(intent: str) -> str:
    if intent == "instalar":
        return "third_party_host_change"
    return "third_party_host_removal"


def _assess_ppa_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    confirmation_supplied: bool = False,
    environ: dict[str, str] | None = None,
) -> PolicyAssessment | None:
    software_criticality = _ppa_software_criticality(request)
    reversal_level = _ppa_reversal_level(request.intent)
    requires_confirmation = request.intent == "instalar"
    repository = request.source_coordinate.strip()
    supported_distros = supported_ppa_distro_ids()
    supported_distros_label = ",".join(supported_distros)

    if profile is None:
        return PolicyAssessment(
            domain_kind="host_package",
            source_type="ppa_repository",
            trust_level="third_party_repository",
            software_criticality=software_criticality,
            trust_signals=tuple(
                signal
                for signal in (
                    "source_request:ppa",
                    f"ppa_coordinate:{repository}" if repository else "",
                    f"ppa_supported_distros:{supported_distros_label}",
                )
                if signal
            ),
            trust_gaps=("host_profile_unavailable", "ppa_third_party_source_requires_human_review"),
            policy_outcome="block",
            requires_confirmation=requires_confirmation,
            confirmation_supplied=confirmation_supplied,
            reversal_level=reversal_level,
            reason="o host profile nao esta disponivel para validar a rota PPA.",
        )

    source_hint = next(
        (item.split(":", 1)[1] for item in request.observations if item.startswith("source_hint:")),
        "ppa",
    )
    capability = observe_ppa_capability(profile, environ=environ)
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    dpkg_observed = shutil.which("dpkg", path=path) is not None

    trust_signals = [
        "domain:host_package",
        "source_type:ppa_repository",
        "source_request:ppa",
        f"source_hint:{source_hint}",
        f"linux_family:{profile.linux_family}",
        f"distro_id:{profile.distro_id}",
        f"mutability:{profile.mutability}",
        f"software_criticality:{software_criticality}",
        f"ppa_supported_distros:{supported_distros_label}",
    ]
    if repository:
        trust_signals.append(f"ppa_coordinate:{repository}")
    if profile.package_backends:
        trust_signals.append(f"observed_backends:{','.join(profile.package_backends)}")
    if "apt-get" in profile.package_backends:
        trust_signals.append("ppa_backend:apt_get_observed")
    if capability.observed:
        trust_signals.append("ppa_capability:add_apt_repository_observed")
    if dpkg_observed:
        trust_signals.append("ppa_state_probe:dpkg_observed")
    if request.intent == "instalar":
        trust_signals.append("ppa_install_preparation:add_repository,apt_get_update")
    if confirmation_supplied:
        trust_signals.append("confirmation:explicit")

    trust_gaps = ["ppa_third_party_source_requires_human_review"]
    if request.intent == "instalar":
        trust_gaps.append("ppa_repository_state_not_observed_by_design")

    outcome = "allow"
    reason = "PPA explicito foi aceito como fonte contida de terceiro em Ubuntu mutavel nesta rodada."

    if request.status != "CONSISTENT":
        outcome = "block"
        trust_gaps.append("request_not_consistent")
        reason = request.reason
    elif profile.linux_family != "debian":
        outcome = "block"
        trust_gaps.append("ppa_linux_family_not_supported")
        reason = "PPA explicito nesta rodada so abre em Ubuntu mutavel dentro da familia Debian."
    elif profile.distro_id not in supported_distros:
        outcome = "block"
        trust_gaps.append("ppa_distro_not_supported")
        reason = (
            "PPA explicito nesta rodada ficou contido a Ubuntu mutavel com coordenada canonica "
            "e capacidades observaveis; outros Debian-like continuam bloqueados por honestidade."
        )
    elif profile.mutability == "atomic":
        outcome = "block"
        trust_gaps.append("ppa_blocked_on_atomic_host")
        reason = "PPA explicito continua bloqueado em hosts Atomic/imutaveis nesta rodada."
    elif "apt-get" not in profile.package_backends:
        outcome = "block"
        trust_gaps.append("ppa_apt_get_not_observed")
        reason = "a frente PPA depende de apt-get observado neste host Ubuntu."
    elif not repository:
        outcome = "block"
        trust_gaps.append("ppa_coordinate_missing")
        reason = "faltou a coordenada explicita do PPA no formato canonico ppa:owner/name."
    elif not capability.observed:
        outcome = "block"
        trust_gaps.append(capability.gap or "ppa_add_repository_not_observed")
        reason = capability.reason
    elif not dpkg_observed:
        outcome = "block"
        trust_gaps.append("ppa_dpkg_not_observed")
        reason = "a confirmacao de estado para PPA depende de dpkg observado neste host."
    elif request.intent == "instalar":
        reason = (
            "ppa.instalar planeja add-apt-repository e apt-get update como passos preparatorios "
            "explicitos antes do apt-get install, sem observar lifecycle amplo do PPA."
        )
    elif request.intent == "remover":
        outcome = "block"
        trust_gaps.extend(("ppa_removal_not_opened", "ppa_package_origin_not_verifiable"))
        reason = (
            "ppa.remover continua bloqueado nesta rodada: a Aurora ainda nao demonstra proveniencia "
            "APT suficiente por PPA e nao abre cleanup/lifecycle amplo do repositorio."
        )

    if outcome == "allow" and requires_confirmation and not confirmation_supplied:
        outcome = "require_confirmation"
        trust_gaps.append("confirmation_missing_for_ppa_install")
        reason = "a mutacao explicitamente marcada como PPA exige confirmacao explicita nesta rodada."

    return PolicyAssessment(
        domain_kind="host_package",
        source_type="ppa_repository",
        trust_level="third_party_repository",
        software_criticality=software_criticality,
        trust_signals=tuple(trust_signals),
        trust_gaps=tuple(trust_gaps),
        policy_outcome=outcome,
        requires_confirmation=requires_confirmation,
        confirmation_supplied=confirmation_supplied,
        reversal_level=reversal_level,
        reason=reason,
    )


def _assess_copr_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    confirmation_supplied: bool = False,
    environ: dict[str, str] | None = None,
) -> PolicyAssessment | None:
    software_criticality = _copr_software_criticality(request)
    reversal_level = _copr_reversal_level(request.intent)
    requires_confirmation = request.intent in {"instalar", "remover"}
    repository = request.source_coordinate.strip()

    if profile is None:
        return PolicyAssessment(
            domain_kind="host_package",
            source_type="copr_repository",
            trust_level="third_party_repository",
            software_criticality=software_criticality,
            trust_signals=tuple(
                signal
                for signal in (
                    "source_request:copr",
                    f"copr_repo:{repository}" if repository else "",
                )
                if signal
            ),
            trust_gaps=("host_profile_unavailable", "copr_third_party_source_requires_human_review"),
            policy_outcome="block",
            requires_confirmation=requires_confirmation,
            confirmation_supplied=confirmation_supplied,
            reversal_level=reversal_level,
            reason="o host profile nao esta disponivel para validar a rota COPR.",
        )

    source_hint = next(
        (item.split(":", 1)[1] for item in request.observations if item.startswith("source_hint:")),
        "copr",
    )
    capability = observe_copr_capability(profile, environ=environ)
    repository_state = (
        observe_copr_repository_state(profile, repository, environ=environ)
        if request.intent in {"instalar", "remover"}
        else None
    )
    provenance = (
        observe_copr_package_origin(profile, repository, request.target.strip(), environ=environ)
        if request.intent == "remover" and request.target.strip()
        else None
    )
    trust_signals = [
        "domain:host_package",
        "source_type:copr_repository",
        "source_request:copr",
        f"source_hint:{source_hint}",
        f"linux_family:{profile.linux_family}",
        f"mutability:{profile.mutability}",
        f"software_criticality:{software_criticality}",
    ]
    if repository:
        trust_signals.append(f"copr_repo:{repository}")
    if profile.package_backends:
        trust_signals.append(f"observed_backends:{','.join(profile.package_backends)}")
    if capability.observed:
        trust_signals.append("copr_capability:dnf_copr_observed")
    if repository_state is not None and repository_state.observed:
        trust_signals.append(f"copr_repository_state:{repository_state.status}")
    if request.intent == "instalar":
        if repository_state is not None and repository_state.observed and repository_state.enabled is True:
            trust_signals.append("copr_repository_enable_action:not_needed")
        else:
            trust_signals.append("copr_repository_enable_action:explicit_enable")
    if request.intent == "procurar":
        trust_signals.append("copr_search_scope:explicit_repository_only")
    if provenance is not None:
        trust_signals.append(f"copr_package_origin:{provenance.status}")
        if provenance.from_repo:
            trust_signals.append(f"copr_package_from_repo:{provenance.from_repo}")
    if confirmation_supplied:
        trust_signals.append("confirmation:explicit")

    trust_gaps = ["copr_third_party_source_requires_human_review"]

    outcome = "allow"
    reason = "COPR explicito foi aceito como fonte contida de terceiro em Fedora mutavel nesta rodada."

    if request.status != "CONSISTENT":
        outcome = "block"
        trust_gaps.append("request_not_consistent")
        reason = request.reason
    elif profile.linux_family != "fedora":
        outcome = "block"
        trust_gaps.append("copr_linux_family_not_supported")
        reason = "COPR explicito nesta rodada so abre em hosts Fedora mutaveis suportados."
    elif profile.mutability == "atomic":
        outcome = "block"
        trust_gaps.append("copr_blocked_on_atomic_host")
        reason = "COPR explicito continua bloqueado em hosts Atomic/imutaveis nesta rodada."
    elif "dnf" not in profile.package_backends:
        outcome = "block"
        trust_gaps.append("copr_dnf_backend_not_observed")
        reason = "a frente COPR depende de dnf observado neste host Fedora."
    elif not repository:
        outcome = "block"
        trust_gaps.append("copr_repository_coordinate_missing")
        reason = "faltou a coordenada explicita do repositorio COPR no formato owner/project."
    elif not capability.observed:
        outcome = "block"
        trust_gaps.append(capability.gap or "copr_dnf_plugin_not_observed")
        reason = capability.reason
    elif request.intent == "procurar":
        reason = (
            "copr.procurar consulta apenas o repositorio explicitamente pedido e nao faz "
            "descoberta automatica nem busca global de repositorios nesta rodada."
        )
    elif request.intent == "instalar":
        if repository_state is not None and repository_state.observed and repository_state.enabled is True:
            reason = (
                "copr.instalar observou que o repositorio explicito ja estava habilitado e segue "
                "sem novo enable, mantendo a mutacao idempotente e explicavel."
            )
        elif repository_state is not None and repository_state.observed and repository_state.enabled is False:
            reason = (
                "copr.instalar observou o repositorio explicito como desabilitado e planeja apenas "
                "o enable minimo antes da instalacao, sem abrir cleanup ou lifecycle amplo."
            )
        else:
            trust_gaps.append(
                repository_state.gap if repository_state is not None and repository_state.gap else "copr_repository_state_not_observed"
            )
            reason = (
                "copr.instalar depende do repositorio explicito e manteve apenas o enable minimo "
                "como guarda idempotente, porque o estado previo do repo nao foi observado com confianca."
            )
    elif request.intent == "remover":
        if repository_state is not None and repository_state.observed:
            trust_signals.append(f"copr_repository_state_on_remove:{repository_state.status}")
        elif repository_state is not None and repository_state.gap:
            trust_gaps.append(repository_state.gap)

        if provenance is None:
            trust_gaps.append("copr_package_origin_not_verified")
            outcome = "block"
            reason = (
                "copr.remover exige verificacao de origem RPM nesta rodada, mas nao consegui montar "
                "o probe de proveniencia do pacote."
            )
        elif provenance.status == "verified":
            reason = (
                "copr.remover verificou a origem RPM do pacote instalado contra o repo explicito "
                "antes de permitir a mutacao."
            )
        elif provenance.status == "not_installed":
            reason = (
                "copr.remover observou que o pacote ja nao esta instalado; a verificacao de origem "
                "RPM nao foi necessaria antes do no-op."
            )
        else:
            outcome = "block"
            trust_gaps.append(provenance.gap or "copr_package_origin_not_verified")
            reason = provenance.reason

    if outcome == "allow" and requires_confirmation and not confirmation_supplied:
        outcome = "require_confirmation"
        trust_gaps.append("confirmation_missing_for_copr_mutation")
        reason = "a mutacao explicitamente marcada como COPR exige confirmacao explicita nesta rodada."

    return PolicyAssessment(
        domain_kind="host_package",
        source_type="copr_repository",
        trust_level="third_party_repository",
        software_criticality=software_criticality,
        trust_signals=tuple(trust_signals),
        trust_gaps=tuple(trust_gaps),
        policy_outcome=outcome,
        requires_confirmation=requires_confirmation,
        confirmation_supplied=confirmation_supplied,
        reversal_level=reversal_level,
        reason=reason,
    )


def assess_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    confirmation_supplied: bool = False,
    environ: dict[str, str] | None = None,
    environment_resolution: EnvironmentResolution | None = None,
    toolbox_profile: HostProfile | None = None,
    toolbox_profile_probe: ToolboxProfileProbe | None = None,
) -> PolicyAssessment | None:
    if request.execution_surface == "toolbox":
        return _assess_toolbox_policy(
            request,
            profile,
            environment_resolution=environment_resolution,
            toolbox_profile=toolbox_profile,
            toolbox_profile_probe=toolbox_profile_probe,
            confirmation_supplied=confirmation_supplied,
        )
    if request.domain_kind == "host_package" and request.requested_source == "ppa":
        return _assess_ppa_policy(
            request,
            profile,
            confirmation_supplied=confirmation_supplied,
            environ=environ,
        )
    if request.domain_kind == "host_package" and request.requested_source == "copr":
        return _assess_copr_policy(
            request,
            profile,
            confirmation_supplied=confirmation_supplied,
            environ=environ,
        )
    if request.domain_kind == "host_package" and request.requested_source == "aur":
        return _assess_aur_policy(
            request,
            profile,
            confirmation_supplied=confirmation_supplied,
        )
    if request.domain_kind == "host_package":
        return _assess_host_package_policy(
            request,
            profile,
            confirmation_supplied=confirmation_supplied,
        )
    if request.domain_kind == "user_software":
        return _assess_user_software_policy(
            request,
            profile,
            confirmation_supplied=confirmation_supplied,
            environ=environ,
        )
    return None

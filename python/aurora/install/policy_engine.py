from __future__ import annotations

from aurora.contracts.host import HostProfile
from aurora.contracts.policy import PolicyAssessment
from aurora.contracts.requests import SemanticRequest
from aurora.install.sources.aur import observed_out_of_contract_aur_helpers, supported_aur_helper
from aurora.linux.immutable_policy import host_package_block_reason

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
    trust_signals = [
        "domain:user_software",
        "source_type:flatpak_remote",
        f"source_hint:{source_hint}",
        f"mutability:{profile.mutability}",
        f"software_criticality:{software_criticality}",
    ]
    trust_gaps: list[str] = []
    if request.intent == "procurar":
        trust_gaps.append("flatpak_search_scope_not_generalized")
    else:
        trust_signals.extend(("installation_scope:user", "remote_default:flathub"))
        trust_gaps.append("flatpak_remote_selection_not_generalized")
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
    elif request.intent == "instalar":
        reason = (
            "flatpak.instalar usa installation scope explicito de usuario e remote default flathub "
            "nesta rodada."
        )
    elif request.intent == "remover":
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
    out_of_contract_helpers = observed_out_of_contract_aur_helpers(profile)
    trust_signals = [
        "domain:host_package",
        "source_type:aur_repository",
        "source_request:aur",
        f"source_hint:{source_hint}",
        f"linux_family:{profile.linux_family}",
        f"mutability:{profile.mutability}",
        f"software_criticality:{software_criticality}",
    ]
    if profile.package_backends:
        trust_signals.append(f"observed_backends:{','.join(profile.package_backends)}")
    if profile.observed_third_party_package_tools:
        trust_signals.append(
            f"observed_third_party_package_tools:{','.join(profile.observed_third_party_package_tools)}"
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
        if profile.observed_third_party_package_tools:
            trust_gaps.append("aur_supported_helper_not_observed")
            reason = (
                "observei helper(s) AUR fora do contrato desta rodada, mas a frente explicita aceita "
                "apenas paru neste primeiro corte."
            )
        else:
            trust_gaps.append("aur_helper_not_observed")
            reason = "nenhum helper AUR aceito nesta rodada foi observado no host."
    elif request.intent == "procurar":
        reason = "aur.procurar foi aceito como leitura explicita do AUR via paru nesta rodada."
    else:
        reason = (
            "mutacoes AUR exigem confirmacao explicita e continuam sinalizadas como fonte terceira "
            "nesta rodada."
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


def assess_policy(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    confirmation_supplied: bool = False,
) -> PolicyAssessment | None:
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
        )
    return None

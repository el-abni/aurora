from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImmutableHostFacts:
    host_is_immutable: bool = False
    observed_surfaces: tuple[str, ...] = ()
    selected_surface: str = ""
    toolbox_environments: tuple[str, ...] = ()
    distrobox_environments: tuple[str, ...] = ()


@dataclass(frozen=True)
class MediatedEnvironmentFacts:
    requested_environment: str = ""
    environment_status: str = ""
    resolved_environment: str = ""
    observed_environment_tools: tuple[str, ...] = ()
    observed_environments: tuple[str, ...] = ()
    linux_family: str = ""
    support_tier: str = ""
    package_backends: tuple[str, ...] = ()
    observed_commands: tuple[str, ...] = ()
    sudo_observed: bool | None = None


@dataclass(frozen=True)
class FlatpakPolicyFacts:
    requested_remote: str = ""
    effective_remote: str = ""
    remote_origin: str = ""
    observed_remotes: tuple[str, ...] = ()
    remove_origin_constraint: bool = False


@dataclass(frozen=True)
class PpaPolicyFacts:
    supported_distros: tuple[str, ...] = ()
    capability: str = ""
    state_probe: str = ""
    install_preparation: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoprPolicyFacts:
    repository_state: str = ""
    repository_enable_action: str = ""
    package_origin: str = ""
    package_from_repo: str = ""


@dataclass(frozen=True)
class RpmOstreePolicyFacts:
    status: str = ""
    booted_requested_packages: tuple[str, ...] = ()
    booted_packages: tuple[str, ...] = ()
    pending_deployment: bool | None = None
    pending_requested_packages: tuple[str, ...] = ()
    pending_packages: tuple[str, ...] = ()
    transaction_active: bool | None = None


@dataclass(frozen=True)
class PolicyAssessment:
    domain_kind: str
    source_type: str
    trust_level: str
    software_criticality: str
    trust_signals: tuple[str, ...]
    trust_gaps: tuple[str, ...]
    policy_outcome: str
    requires_confirmation: bool
    confirmation_supplied: bool
    reversal_level: str
    reason: str
    execution_surface: str = "host"
    immutable_host_facts: ImmutableHostFacts | None = None
    toolbox_facts: MediatedEnvironmentFacts | None = None
    distrobox_facts: MediatedEnvironmentFacts | None = None
    flatpak_facts: FlatpakPolicyFacts | None = None
    ppa_facts: PpaPolicyFacts | None = None
    copr_facts: CoprPolicyFacts | None = None
    rpm_ostree_facts: RpmOstreePolicyFacts | None = None

from __future__ import annotations

from aurora.contracts.decisions import DecisionRecord
from aurora.install.sources.aur import (
    observed_out_of_contract_aur_helpers,
    supported_aur_helper,
    supported_aur_helpers,
)
from aurora.presentation.formatting import field


def _signal_value(signals: tuple[str, ...], prefix: str) -> str | None:
    for signal in signals:
        if signal.startswith(prefix):
            return signal.split(":", 1)[1]
    return None


def _scope_label(record: DecisionRecord) -> str:
    if record.request.execution_surface == "toolbox" and record.request.domain_kind == "host_package":
        return "pacote do host dentro da toolbox"
    if record.request.domain_kind == "user_software":
        return "software do usuario"
    if record.request.domain_kind == "host_package" and record.request.requested_source == "ppa":
        return "pacote do host via PPA"
    if record.request.domain_kind == "host_package" and record.request.requested_source == "copr":
        return "pacote do host via COPR"
    if record.request.domain_kind == "host_package" and record.request.requested_source == "aur":
        return "pacote AUR no host"
    if record.request.domain_kind == "host_package":
        return "pacote do host"
    return "indefinido"


def _compact_diagnostic(value: str) -> str:
    compact = " | ".join(line.strip() for line in value.splitlines() if line.strip())
    if not compact:
        return "-"
    if len(compact) <= 200:
        return compact
    return compact[:197].rstrip() + "..."


def render_decision_record(record: DecisionRecord) -> str:
    lines = [
        "Aurora decision record",
        field("outcome", record.outcome),
        field("summary", record.summary),
        "",
        "Request",
        field("original_text", record.request.original_text),
        field("normalized_text", record.request.normalized_text),
        field("intent", record.request.intent),
        field("domain_kind", record.request.domain_kind),
        field("execution_surface", record.request.execution_surface),
        field("requested_source", record.request.requested_source or "-"),
        field("source_coordinate", record.request.source_coordinate or "-"),
        field("environment_target", record.request.environment_target or "-"),
        field("scope_label", _scope_label(record)),
        field("target", record.request.target or "-"),
        field("status", record.request.status),
        field("reason", record.request.reason),
        field("observations", ", ".join(record.request.observations) or "-"),
        field("action_count", str(record.request.action_count)),
    ]

    if record.host_profile is not None:
        lines.extend(
            [
                "",
                "Host profile",
                field("linux_family", record.host_profile.linux_family_label),
                field("distro_id", record.host_profile.distro_id or "-"),
                field("distro_like", ", ".join(record.host_profile.distro_like) or "-"),
                field("mutability", record.host_profile.mutability_label),
                field("support_tier", record.host_profile.support_tier_label),
                field("compatibility", record.host_profile.compatibility_frontier_label),
                field("package_backends", record.host_profile.package_backends_label),
                field("observed_tools", record.host_profile.observed_package_tools_label),
                field(
                    "observed_third_party_tools",
                    record.host_profile.observed_third_party_package_tools_label,
                ),
                field(
                    "observed_environment_tools",
                    record.host_profile.observed_environment_tools_label,
                ),
                field(
                    "observed_toolbox_environments",
                    record.host_profile.observed_toolbox_environments_label,
                ),
            ]
        )

    if record.policy is not None:
        lines.extend(
            [
                "",
                "Policy",
                field("domain_kind", record.policy.domain_kind),
                field("source_type", record.policy.source_type),
                field("execution_surface", record.policy.execution_surface),
                field("trust_level", record.policy.trust_level),
                field("software_criticality", record.policy.software_criticality),
                field("policy_outcome", record.policy.policy_outcome),
                field("requires_confirmation", str(record.policy.requires_confirmation).lower()),
                field("confirmation_supplied", str(record.policy.confirmation_supplied).lower()),
                field("reversal_level", record.policy.reversal_level),
                field("trust_signals", ", ".join(record.policy.trust_signals) or "-"),
                field("trust_gaps", ", ".join(record.policy.trust_gaps) or "-"),
                field("policy_reason", record.policy.reason),
            ]
        )
        if record.request.requested_source == "aur":
            observed_helpers = (
                ", ".join(record.host_profile.observed_third_party_package_tools)
                if record.host_profile is not None and record.host_profile.observed_third_party_package_tools
                else "-"
            )
            out_of_contract = ", ".join(observed_out_of_contract_aur_helpers(record.host_profile)) or "-"
            selected_helper = supported_aur_helper(record.host_profile) or "-"
            lines.extend(
                [
                    field("observed_aur_helpers", observed_helpers),
                    field("supported_aur_helpers", ", ".join(supported_aur_helpers())),
                    field("selected_aur_helper", selected_helper),
                    field("out_of_contract_aur_helpers", out_of_contract),
                ]
            )
        if record.request.requested_source == "copr":
            lines.extend(
                [
                    field(
                        "copr_repository_state",
                        _signal_value(record.policy.trust_signals, "copr_repository_state:") or "-",
                    ),
                    field(
                        "copr_repository_enable_action",
                        _signal_value(record.policy.trust_signals, "copr_repository_enable_action:")
                        or "-",
                    ),
                    field(
                        "copr_package_origin",
                        _signal_value(record.policy.trust_signals, "copr_package_origin:") or "-",
                    ),
                    field(
                        "copr_package_from_repo",
                        _signal_value(record.policy.trust_signals, "copr_package_from_repo:") or "-",
                    ),
                ]
            )
        if record.request.requested_source == "ppa":
            lines.extend(
                [
                    field(
                        "ppa_supported_distros",
                        _signal_value(record.policy.trust_signals, "ppa_supported_distros:") or "-",
                    ),
                    field(
                        "ppa_capability",
                        _signal_value(record.policy.trust_signals, "ppa_capability:") or "-",
                    ),
                    field(
                        "ppa_state_probe",
                        _signal_value(record.policy.trust_signals, "ppa_state_probe:") or "-",
                    ),
                    field(
                        "ppa_install_preparation",
                        _signal_value(record.policy.trust_signals, "ppa_install_preparation:") or "-",
                    ),
                ]
            )
        if record.request.domain_kind == "user_software":
            lines.extend(
                [
                    field(
                        "flatpak_effective_remote",
                        _signal_value(record.policy.trust_signals, "flatpak_effective_remote:") or "-",
                    ),
                    field(
                        "flatpak_remote_origin",
                        _signal_value(record.policy.trust_signals, "flatpak_remote_origin:") or "-",
                    ),
                    field(
                        "flatpak_observed_remotes",
                        _signal_value(record.policy.trust_signals, "flatpak_observed_remotes:") or "-",
                    ),
                    field(
                        "flatpak_remove_origin_constraint",
                        _signal_value(record.policy.trust_signals, "flatpak_remove_origin_constraint:")
                        or "-",
                    ),
                ]
            )
        if record.request.execution_surface == "toolbox":
            lines.extend(
                [
                    field(
                        "toolbox_requested_environment",
                        _signal_value(record.policy.trust_signals, "toolbox_requested_environment:") or "-",
                    ),
                    field(
                        "toolbox_environment_status",
                        _signal_value(record.policy.trust_signals, "toolbox_environment_status:") or "-",
                    ),
                    field(
                        "toolbox_resolved_environment",
                        _signal_value(record.policy.trust_signals, "toolbox_resolved_environment:") or "-",
                    ),
                    field(
                        "toolbox_linux_family",
                        _signal_value(record.policy.trust_signals, "toolbox_linux_family:") or "-",
                    ),
                    field(
                        "toolbox_support_tier",
                        _signal_value(record.policy.trust_signals, "toolbox_support_tier:") or "-",
                    ),
                    field(
                        "toolbox_package_backends",
                        _signal_value(record.policy.trust_signals, "toolbox_package_backends:") or "-",
                    ),
                    field(
                        "toolbox_observed_commands",
                        _signal_value(record.policy.trust_signals, "toolbox_observed_commands:") or "-",
                    ),
                    field(
                        "toolbox_sudo_observed",
                        _signal_value(record.policy.trust_signals, "toolbox_sudo_observed:") or "-",
                    ),
                ]
            )

    if record.environment_resolution is not None:
        lines.extend(
            [
                "",
                "Environment resolution",
                field("execution_surface", record.environment_resolution.execution_surface),
                field("original_environment", record.environment_resolution.original_environment or "-"),
                field("resolved_environment", record.environment_resolution.resolved_environment or "-"),
                field(
                    "observed_environments",
                    ", ".join(record.environment_resolution.observed_environments) or "-",
                ),
                field("status", record.environment_resolution.status),
                field("source", record.environment_resolution.source or "-"),
                field("reason", record.environment_resolution.reason),
            ]
        )
        if (
            record.environment_resolution.diagnostic_command
            or record.environment_resolution.diagnostic_exit_code is not None
            or record.environment_resolution.diagnostic_stdout
            or record.environment_resolution.diagnostic_stderr
        ):
            lines.extend(
                [
                    field(
                        "diagnostic_command",
                        " ".join(record.environment_resolution.diagnostic_command) or "-",
                    ),
                    field(
                        "diagnostic_exit_code",
                        (
                            str(record.environment_resolution.diagnostic_exit_code)
                            if record.environment_resolution.diagnostic_exit_code is not None
                            else "-"
                        ),
                    ),
                    field("diagnostic_stdout", _compact_diagnostic(record.environment_resolution.diagnostic_stdout)),
                    field("diagnostic_stderr", _compact_diagnostic(record.environment_resolution.diagnostic_stderr)),
                ]
            )

    if record.target_resolution is not None:
        lines.extend(
            [
                "",
                "Target resolution",
                field("original_target", record.target_resolution.original_target or "-"),
                field("consulted_target", record.target_resolution.consulted_target or "-"),
                field("consulted_targets", ", ".join(record.target_resolution.consulted_targets) or "-"),
                field("resolved_target", record.target_resolution.resolved_target or "-"),
                field("status", record.target_resolution.status),
                field("source", record.target_resolution.source or "-"),
                field("canonicalized", str(record.target_resolution.canonicalized).lower()),
                field("candidates", ", ".join(record.target_resolution.candidates) or "-"),
                field("resolution_reason", record.target_resolution.reason),
            ]
        )
        if (
            record.target_resolution.diagnostic_command
            or record.target_resolution.diagnostic_exit_code is not None
            or record.target_resolution.diagnostic_stdout
            or record.target_resolution.diagnostic_stderr
        ):
            lines.extend(
                [
                    field(
                        "diagnostic_command",
                        " ".join(record.target_resolution.diagnostic_command) or "-",
                    ),
                    field(
                        "diagnostic_exit_code",
                        (
                            str(record.target_resolution.diagnostic_exit_code)
                            if record.target_resolution.diagnostic_exit_code is not None
                            else "-"
                        ),
                    ),
                    field("diagnostic_stdout", _compact_diagnostic(record.target_resolution.diagnostic_stdout)),
                    field("diagnostic_stderr", _compact_diagnostic(record.target_resolution.diagnostic_stderr)),
                ]
            )

    if record.execution_route is not None:
        lines.extend(
            [
                "",
                "Execution route",
                field("route_name", record.execution_route.route_name),
                field("action_name", record.execution_route.action_name),
                field("backend_name", record.execution_route.backend_name),
                field("execution_surface", record.execution_route.execution_surface),
                field("environment_target", record.execution_route.environment_target or "-"),
                field("scope_label", _scope_label(record)),
                field("implemented", str(record.execution_route.implemented).lower()),
                field(
                    "requires_privilege_escalation",
                    str(record.execution_route.requires_privilege_escalation).lower(),
                ),
                field(
                    "interactive_passthrough",
                    str(record.execution_route.interactive_passthrough).lower(),
                ),
                field(
                    "pre_commands",
                    " | ".join(" ".join(command) for command in record.execution_route.pre_commands) or "-",
                ),
                field("command", " ".join(record.execution_route.command) or "-"),
                field("state_probe", " ".join(record.execution_route.state_probe_command) or "-"),
                field("notes", "; ".join(record.execution_route.notes) or "-"),
            ]
        )
        if record.execution_route.route_name.startswith("aur."):
            lines.append(field("selected_aur_helper", record.execution_route.backend_name or "-"))
        if record.execution_route.route_name.startswith("copr."):
            lines.extend(
                [
                    field(
                        "copr_enable_planned",
                        str(bool(record.execution_route.pre_commands)).lower(),
                    ),
                    field(
                        "copr_repository_state",
                        (
                            _signal_value(record.policy.trust_signals, "copr_repository_state:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "copr_package_origin",
                        (
                            _signal_value(record.policy.trust_signals, "copr_package_origin:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "copr_package_from_repo",
                        (
                            _signal_value(record.policy.trust_signals, "copr_package_from_repo:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                ]
            )
        if record.execution_route.route_name.startswith("ppa."):
            lines.extend(
                [
                    field(
                        "ppa_preparation_planned",
                        str(bool(record.execution_route.pre_commands)).lower(),
                    ),
                    field(
                        "ppa_supported_distros",
                        (
                            _signal_value(record.policy.trust_signals, "ppa_supported_distros:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "ppa_capability",
                        (
                            _signal_value(record.policy.trust_signals, "ppa_capability:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "ppa_install_preparation",
                        (
                            _signal_value(record.policy.trust_signals, "ppa_install_preparation:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                ]
            )
        if record.execution_route.route_name.startswith("flatpak."):
            lines.extend(
                [
                    field(
                        "flatpak_effective_remote",
                        (
                            _signal_value(record.policy.trust_signals, "flatpak_effective_remote:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "flatpak_remote_origin",
                        (
                            _signal_value(record.policy.trust_signals, "flatpak_remote_origin:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "flatpak_observed_remotes",
                        (
                            _signal_value(record.policy.trust_signals, "flatpak_observed_remotes:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "flatpak_remove_origin_constraint",
                        (
                            _signal_value(
                                record.policy.trust_signals,
                                "flatpak_remove_origin_constraint:",
                            )
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                ]
            )
        if record.execution_route.route_name.startswith("toolbox."):
            lines.extend(
                [
                    field(
                        "toolbox_environment_status",
                        (
                            _signal_value(record.policy.trust_signals, "toolbox_environment_status:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "toolbox_resolved_environment",
                        (
                            _signal_value(record.policy.trust_signals, "toolbox_resolved_environment:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "toolbox_linux_family",
                        (
                            _signal_value(record.policy.trust_signals, "toolbox_linux_family:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "toolbox_package_backends",
                        (
                            _signal_value(record.policy.trust_signals, "toolbox_package_backends:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                    field(
                        "toolbox_sudo_observed",
                        (
                            _signal_value(record.policy.trust_signals, "toolbox_sudo_observed:")
                            if record.policy is not None
                            else "-"
                        )
                        or "-",
                    ),
                ]
            )

    if record.toolbox_profile is not None:
        lines.extend(
            [
                "",
                "Toolbox profile",
                field("linux_family", record.toolbox_profile.linux_family_label),
                field("distro_id", record.toolbox_profile.distro_id or "-"),
                field("distro_like", ", ".join(record.toolbox_profile.distro_like) or "-"),
                field("mutability", record.toolbox_profile.mutability_label),
                field("support_tier", record.toolbox_profile.support_tier_label),
                field("compatibility", record.toolbox_profile.compatibility_frontier_label),
                field("package_backends", record.toolbox_profile.package_backends_label),
                field("observed_tools", record.toolbox_profile.observed_package_tools_label),
                field(
                    "observed_third_party_tools",
                    record.toolbox_profile.observed_third_party_package_tools_label,
                ),
            ]
        )

    if record.execution is not None:
        lines.extend(
            [
                "",
                "Execution",
                field("status", record.execution.status),
                field("attempted", str(record.execution.attempted).lower()),
                field("confirmation_supplied", str(record.execution.confirmation_supplied).lower()),
                field("interactive_passthrough", str(record.execution.interactive_passthrough).lower()),
                field("exit_code", str(record.execution.exit_code) if record.execution.exit_code is not None else "-"),
                field("summary", record.execution.summary),
                field(
                    "pre_probe",
                    record.execution.pre_probe.summary if record.execution.pre_probe is not None else "-",
                ),
                field(
                    "post_probe",
                    record.execution.post_probe.summary if record.execution.post_probe is not None else "-",
                ),
            ]
        )

    return "\n".join(lines)

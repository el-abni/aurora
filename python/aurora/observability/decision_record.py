from __future__ import annotations

from aurora.contracts.decisions import DecisionRecord
from aurora.install.sources.aur import (
    observed_out_of_contract_aur_helpers,
    supported_aur_helper,
    supported_aur_helpers,
)


def _signal_value(signals: tuple[str, ...], prefix: str) -> str | None:
    for signal in signals:
        if signal.startswith(prefix):
            return signal.split(":", 1)[1]
    return None


def decision_record_to_dict(record: DecisionRecord) -> dict[str, object]:
    payload: dict[str, object] = {
        "request": {
            "original_text": record.request.original_text,
            "normalized_text": record.request.normalized_text,
            "intent": record.request.intent,
            "domain_kind": record.request.domain_kind,
            "requested_source": record.request.requested_source,
            "source_coordinate": record.request.source_coordinate,
            "target": record.request.target,
            "status": record.request.status,
            "reason": record.request.reason,
            "observations": list(record.request.observations),
            "action_count": record.request.action_count,
        },
        "outcome": record.outcome,
        "summary": record.summary,
    }

    if record.host_profile is not None:
        payload["host_profile"] = {
            "linux_family": record.host_profile.linux_family,
            "distro_id": record.host_profile.distro_id,
            "distro_like": list(record.host_profile.distro_like),
            "variant_id": record.host_profile.variant_id,
            "mutability": record.host_profile.mutability,
            "package_backends": list(record.host_profile.package_backends),
            "observed_package_tools": list(record.host_profile.observed_package_tools),
            "observed_third_party_package_tools": list(record.host_profile.observed_third_party_package_tools),
            "support_tier": record.host_profile.support_tier,
        }

    if record.policy is not None:
        payload["policy"] = {
            "domain_kind": record.policy.domain_kind,
            "source_type": record.policy.source_type,
            "trust_level": record.policy.trust_level,
            "software_criticality": record.policy.software_criticality,
            "trust_signals": list(record.policy.trust_signals),
            "trust_gaps": list(record.policy.trust_gaps),
            "policy_outcome": record.policy.policy_outcome,
            "requires_confirmation": record.policy.requires_confirmation,
            "confirmation_supplied": record.policy.confirmation_supplied,
            "reversal_level": record.policy.reversal_level,
            "reason": record.policy.reason,
        }
        if record.request.requested_source == "aur":
            payload["policy"]["observed_aur_helpers"] = (
                list(record.host_profile.observed_third_party_package_tools)
                if record.host_profile is not None
                else []
            )
            payload["policy"]["supported_aur_helpers"] = list(supported_aur_helpers())
            payload["policy"]["selected_aur_helper"] = (
                supported_aur_helper(record.host_profile) if record.host_profile is not None else None
            )
            payload["policy"]["out_of_contract_aur_helpers"] = (
                list(observed_out_of_contract_aur_helpers(record.host_profile))
                if record.host_profile is not None
                else []
            )
        if record.request.requested_source == "copr":
            payload["policy"]["copr_repository_state"] = _signal_value(
                record.policy.trust_signals,
                "copr_repository_state:",
            )
            payload["policy"]["copr_repository_enable_action"] = _signal_value(
                record.policy.trust_signals,
                "copr_repository_enable_action:",
            )
            payload["policy"]["copr_package_origin"] = _signal_value(
                record.policy.trust_signals,
                "copr_package_origin:",
            )
            payload["policy"]["copr_package_from_repo"] = _signal_value(
                record.policy.trust_signals,
                "copr_package_from_repo:",
            )
        if record.request.requested_source == "ppa":
            payload["policy"]["ppa_supported_distros"] = _signal_value(
                record.policy.trust_signals,
                "ppa_supported_distros:",
            )
            payload["policy"]["ppa_capability"] = _signal_value(
                record.policy.trust_signals,
                "ppa_capability:",
            )
            payload["policy"]["ppa_state_probe"] = _signal_value(
                record.policy.trust_signals,
                "ppa_state_probe:",
            )
            payload["policy"]["ppa_install_preparation"] = _signal_value(
                record.policy.trust_signals,
                "ppa_install_preparation:",
            )
        if record.request.domain_kind == "user_software":
            payload["policy"]["flatpak_effective_remote"] = _signal_value(
                record.policy.trust_signals,
                "flatpak_effective_remote:",
            )
            payload["policy"]["flatpak_remote_origin"] = _signal_value(
                record.policy.trust_signals,
                "flatpak_remote_origin:",
            )
            payload["policy"]["flatpak_observed_remotes"] = _signal_value(
                record.policy.trust_signals,
                "flatpak_observed_remotes:",
            )
            payload["policy"]["flatpak_remove_origin_constraint"] = _signal_value(
                record.policy.trust_signals,
                "flatpak_remove_origin_constraint:",
            )

    if record.target_resolution is not None:
        payload["target_resolution"] = {
            "original_target": record.target_resolution.original_target,
            "consulted_target": record.target_resolution.consulted_target,
            "consulted_targets": list(record.target_resolution.consulted_targets),
            "resolved_target": record.target_resolution.resolved_target,
            "status": record.target_resolution.status,
            "source": record.target_resolution.source,
            "canonicalized": record.target_resolution.canonicalized,
            "candidates": list(record.target_resolution.candidates),
            "reason": record.target_resolution.reason,
            "diagnostic_command": list(record.target_resolution.diagnostic_command),
            "diagnostic_exit_code": record.target_resolution.diagnostic_exit_code,
            "diagnostic_stdout": record.target_resolution.diagnostic_stdout,
            "diagnostic_stderr": record.target_resolution.diagnostic_stderr,
        }

    if record.execution_route is not None:
        payload["execution_route"] = {
            "route_name": record.execution_route.route_name,
            "action_name": record.execution_route.action_name,
            "backend_name": record.execution_route.backend_name,
            "pre_commands": [list(command) for command in record.execution_route.pre_commands],
            "pre_command_required_commands": [
                list(commands) for commands in record.execution_route.pre_command_required_commands
            ],
            "command": list(record.execution_route.command),
            "required_commands": list(record.execution_route.required_commands),
            "state_probe_command": list(record.execution_route.state_probe_command),
            "state_probe_required_commands": list(record.execution_route.state_probe_required_commands),
            "implemented": record.execution_route.implemented,
            "requires_privilege_escalation": record.execution_route.requires_privilege_escalation,
            "interactive_passthrough": record.execution_route.interactive_passthrough,
            "notes": list(record.execution_route.notes),
        }
        if record.execution_route.route_name.startswith("aur."):
            payload["execution_route"]["selected_aur_helper"] = record.execution_route.backend_name
        if record.execution_route.route_name.startswith("copr."):
            payload["execution_route"]["copr_enable_planned"] = bool(record.execution_route.pre_commands)
            if record.policy is not None:
                payload["execution_route"]["copr_repository_state"] = _signal_value(
                    record.policy.trust_signals,
                    "copr_repository_state:",
                )
                payload["execution_route"]["copr_repository_enable_action"] = _signal_value(
                    record.policy.trust_signals,
                    "copr_repository_enable_action:",
                )
                payload["execution_route"]["copr_package_origin"] = _signal_value(
                    record.policy.trust_signals,
                    "copr_package_origin:",
                )
                payload["execution_route"]["copr_package_from_repo"] = _signal_value(
                    record.policy.trust_signals,
                    "copr_package_from_repo:",
                )
        if record.execution_route.route_name.startswith("ppa."):
            payload["execution_route"]["ppa_preparation_planned"] = bool(record.execution_route.pre_commands)
            if record.policy is not None:
                payload["execution_route"]["ppa_supported_distros"] = _signal_value(
                    record.policy.trust_signals,
                    "ppa_supported_distros:",
                )
                payload["execution_route"]["ppa_capability"] = _signal_value(
                    record.policy.trust_signals,
                    "ppa_capability:",
                )
                payload["execution_route"]["ppa_state_probe"] = _signal_value(
                    record.policy.trust_signals,
                    "ppa_state_probe:",
                )
                payload["execution_route"]["ppa_install_preparation"] = _signal_value(
                    record.policy.trust_signals,
                    "ppa_install_preparation:",
                )
        if record.execution_route.route_name.startswith("flatpak."):
            if record.policy is not None:
                payload["execution_route"]["flatpak_effective_remote"] = _signal_value(
                    record.policy.trust_signals,
                    "flatpak_effective_remote:",
                )
                payload["execution_route"]["flatpak_remote_origin"] = _signal_value(
                    record.policy.trust_signals,
                    "flatpak_remote_origin:",
                )
                payload["execution_route"]["flatpak_observed_remotes"] = _signal_value(
                    record.policy.trust_signals,
                    "flatpak_observed_remotes:",
                )
                payload["execution_route"]["flatpak_remove_origin_constraint"] = _signal_value(
                    record.policy.trust_signals,
                    "flatpak_remove_origin_constraint:",
                )

    if record.execution is not None:
        payload["execution"] = {
            "status": record.execution.status,
            "attempted": record.execution.attempted,
            "confirmation_supplied": record.execution.confirmation_supplied,
            "command": list(record.execution.command),
            "exit_code": record.execution.exit_code,
            "interactive_passthrough": record.execution.interactive_passthrough,
            "summary": record.execution.summary,
            "pre_probe": (
                {
                    "status": record.execution.pre_probe.status,
                    "command": list(record.execution.pre_probe.command),
                    "required_commands": list(record.execution.pre_probe.required_commands),
                    "exit_code": record.execution.pre_probe.exit_code,
                    "package_present": record.execution.pre_probe.package_present,
                    "summary": record.execution.pre_probe.summary,
                }
                if record.execution.pre_probe is not None
                else None
            ),
            "post_probe": (
                {
                    "status": record.execution.post_probe.status,
                    "command": list(record.execution.post_probe.command),
                    "required_commands": list(record.execution.post_probe.required_commands),
                    "exit_code": record.execution.post_probe.exit_code,
                    "package_present": record.execution.post_probe.package_present,
                    "summary": record.execution.post_probe.summary,
                }
                if record.execution.post_probe is not None
                else None
            ),
        }

    return payload

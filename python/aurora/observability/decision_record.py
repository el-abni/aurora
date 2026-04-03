from __future__ import annotations

from aurora.contracts.decisions import DecisionRecord


def decision_record_to_dict(record: DecisionRecord) -> dict[str, object]:
    payload: dict[str, object] = {
        "request": {
            "original_text": record.request.original_text,
            "normalized_text": record.request.normalized_text,
            "intent": record.request.intent,
            "domain_kind": record.request.domain_kind,
            "requested_source": record.request.requested_source,
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
            "command": list(record.execution_route.command),
            "required_commands": list(record.execution_route.required_commands),
            "state_probe_command": list(record.execution_route.state_probe_command),
            "state_probe_required_commands": list(record.execution_route.state_probe_required_commands),
            "implemented": record.execution_route.implemented,
            "requires_privilege_escalation": record.execution_route.requires_privilege_escalation,
            "interactive_passthrough": record.execution_route.interactive_passthrough,
            "notes": list(record.execution_route.notes),
        }

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

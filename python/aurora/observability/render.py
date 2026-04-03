from __future__ import annotations

from aurora.contracts.decisions import DecisionRecord
from aurora.presentation.formatting import field


def _scope_label(record: DecisionRecord) -> str:
    if record.request.domain_kind == "user_software":
        return "software do usuario"
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
        field("requested_source", record.request.requested_source or "-"),
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
                field("mutability", record.host_profile.mutability_label),
                field("support_tier", record.host_profile.support_tier_label),
                field("compatibility", record.host_profile.compatibility_frontier_label),
                field("package_backends", record.host_profile.package_backends_label),
                field("observed_tools", record.host_profile.observed_package_tools_label),
                field(
                    "observed_third_party_tools",
                    record.host_profile.observed_third_party_package_tools_label,
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
                field("command", " ".join(record.execution_route.command) or "-"),
                field("state_probe", " ".join(record.execution_route.state_probe_command) or "-"),
                field("notes", "; ".join(record.execution_route.notes) or "-"),
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

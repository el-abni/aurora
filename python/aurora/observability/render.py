from __future__ import annotations

from aurora.contracts.decisions import DecisionRecord
from aurora.presentation.formatting import field


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
        field("target", record.request.target or "-"),
        field("status", record.request.status),
        field("reason", record.request.reason),
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
            ]
        )

    if record.policy is not None:
        lines.extend(
            [
                "",
                "Policy",
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

    if record.execution_route is not None:
        lines.extend(
            [
                "",
                "Execution route",
                field("route_name", record.execution_route.route_name),
                field("backend_name", record.execution_route.backend_name),
                field("implemented", str(record.execution_route.implemented).lower()),
                field(
                    "requires_privilege_escalation",
                    str(record.execution_route.requires_privilege_escalation).lower(),
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

from __future__ import annotations

from collections.abc import Mapping

from aurora.install.sources.aur import (
    observed_out_of_contract_aur_helpers,
    supported_aur_helper,
    supported_aur_helpers,
)
from aurora.local_model.contracts import (
    LOCAL_MODEL_ALLOWED_CAPABILITIES,
    LOCAL_MODEL_AUTHORITY_PROFILE,
    LOCAL_MODEL_FORBIDDEN_AUTHORITIES,
    LOCAL_MODEL_INPUT_SCHEMA_ID,
    MODEL_MODES,
)
from aurora.version import read_version

from .decisions import DecisionRecord
from .stable_ids import ACTION_IDS, EVENT_IDS, ROUTE_IDS, decision_record_stable_ids

DECISION_RECORD_SCHEMA_NAME = "aurora.decision_record"
DECISION_RECORD_SCHEMA_VERSION = "v1"
DECISION_RECORD_SCHEMA_ID = f"{DECISION_RECORD_SCHEMA_NAME}.{DECISION_RECORD_SCHEMA_VERSION}"
CANONICAL_SECTIONS = ("stable_ids", "facts")
PRESENTATION_SECTIONS = ("presentation",)


def _string_or_none(value: str) -> str | None:
    return value or None


def _csv_or_none(items: tuple[str, ...]) -> str | None:
    return ",".join(items) if items else None


def _bool_string_or_none(value: bool | None) -> str | None:
    if value is None:
        return None
    return "true" if value else "false"


def _host_profile_to_dict(profile) -> dict[str, object]:
    return {
        "linux_family": profile.linux_family,
        "distro_id": profile.distro_id,
        "distro_like": list(profile.distro_like),
        "variant_id": profile.variant_id,
        "mutability": profile.mutability,
        "package_backends": list(profile.package_backends),
        "observed_package_tools": list(profile.observed_package_tools),
        "observed_third_party_package_tools": list(profile.observed_third_party_package_tools),
        "support_tier": profile.support_tier,
        "observed_environment_tools": list(profile.observed_environment_tools),
        "observed_toolbox_environments": list(profile.observed_toolbox_environments),
        "observed_distrobox_environments": list(profile.observed_distrobox_environments),
        "observed_immutable_surfaces": list(profile.observed_immutable_surfaces),
    }


def _immutable_host_context_to_dict(facts) -> dict[str, object]:
    return {
        "host_is_immutable": facts.host_is_immutable,
        "observed_surfaces": list(facts.observed_surfaces),
        "selected_surface": facts.selected_surface,
        "toolbox_environments": list(facts.toolbox_environments),
        "distrobox_environments": list(facts.distrobox_environments),
    }


def _mediated_environment_context_to_dict(facts) -> dict[str, object]:
    return {
        "requested_environment": facts.requested_environment,
        "environment_status": facts.environment_status,
        "resolved_environment": facts.resolved_environment,
        "observed_environment_tools": list(facts.observed_environment_tools),
        "observed_environments": list(facts.observed_environments),
        "linux_family": facts.linux_family,
        "support_tier": facts.support_tier,
        "package_backends": list(facts.package_backends),
        "observed_commands": list(facts.observed_commands),
        "sudo_observed": facts.sudo_observed,
    }


def _flatpak_context_to_dict(facts) -> dict[str, object]:
    return {
        "requested_remote": facts.requested_remote,
        "effective_remote": facts.effective_remote,
        "remote_origin": facts.remote_origin,
        "observed_remotes": list(facts.observed_remotes),
        "remove_origin_constraint": facts.remove_origin_constraint,
    }


def _ppa_context_to_dict(facts) -> dict[str, object]:
    return {
        "supported_distros": list(facts.supported_distros),
        "capability": facts.capability,
        "state_probe": facts.state_probe,
        "install_preparation": list(facts.install_preparation),
    }


def _copr_context_to_dict(facts) -> dict[str, object]:
    return {
        "repository_state": facts.repository_state,
        "repository_enable_action": facts.repository_enable_action,
        "package_origin": facts.package_origin,
        "package_from_repo": facts.package_from_repo,
    }


def _rpm_ostree_context_to_dict(facts) -> dict[str, object]:
    return {
        "status": facts.status,
        "booted_requested_packages": list(facts.booted_requested_packages),
        "booted_packages": list(facts.booted_packages),
        "pending_deployment": facts.pending_deployment,
        "pending_requested_packages": list(facts.pending_requested_packages),
        "pending_packages": list(facts.pending_packages),
        "transaction_active": facts.transaction_active,
    }


def _append_immutable_policy_fields(policy_payload: dict[str, object], facts) -> None:
    policy_payload["immutable_host_context"] = _immutable_host_context_to_dict(facts)
    policy_payload["immutable_host"] = "true" if facts.host_is_immutable else None
    policy_payload["immutable_observed_surfaces"] = _csv_or_none(facts.observed_surfaces)
    policy_payload["immutable_selected_surface"] = _string_or_none(facts.selected_surface)
    policy_payload["immutable_toolbox_environments"] = _csv_or_none(facts.toolbox_environments)
    policy_payload["immutable_distrobox_environments"] = _csv_or_none(facts.distrobox_environments)


def _append_mediated_policy_fields(policy_payload: dict[str, object], surface: str, facts) -> None:
    policy_payload[surface] = _mediated_environment_context_to_dict(facts)
    policy_payload["observed_environment_tools"] = _csv_or_none(facts.observed_environment_tools)
    policy_payload[f"{surface}_requested_environment"] = _string_or_none(facts.requested_environment)
    policy_payload[f"{surface}_environment_status"] = _string_or_none(facts.environment_status)
    policy_payload[f"{surface}_resolved_environment"] = _string_or_none(facts.resolved_environment)
    policy_payload[f"observed_{surface}_environments"] = _csv_or_none(facts.observed_environments)
    policy_payload[f"{surface}_linux_family"] = _string_or_none(facts.linux_family)
    policy_payload[f"{surface}_support_tier"] = _string_or_none(facts.support_tier)
    policy_payload[f"{surface}_package_backends"] = _csv_or_none(facts.package_backends)
    policy_payload[f"{surface}_observed_commands"] = _csv_or_none(facts.observed_commands)
    policy_payload[f"{surface}_sudo_observed"] = _bool_string_or_none(facts.sudo_observed)


def _append_flatpak_policy_fields(policy_payload: dict[str, object], facts) -> None:
    policy_payload["flatpak"] = _flatpak_context_to_dict(facts)
    policy_payload["flatpak_effective_remote"] = _string_or_none(facts.effective_remote)
    policy_payload["flatpak_remote_origin"] = _string_or_none(facts.remote_origin)
    policy_payload["flatpak_observed_remotes"] = _csv_or_none(facts.observed_remotes)
    policy_payload["flatpak_remove_origin_constraint"] = (
        "enabled" if facts.remove_origin_constraint else None
    )


def _append_ppa_policy_fields(policy_payload: dict[str, object], facts) -> None:
    policy_payload["ppa"] = _ppa_context_to_dict(facts)
    policy_payload["ppa_supported_distros"] = _csv_or_none(facts.supported_distros)
    policy_payload["ppa_capability"] = _string_or_none(facts.capability)
    policy_payload["ppa_state_probe"] = _string_or_none(facts.state_probe)
    policy_payload["ppa_install_preparation"] = _csv_or_none(facts.install_preparation)


def _append_copr_policy_fields(policy_payload: dict[str, object], facts) -> None:
    policy_payload["copr"] = _copr_context_to_dict(facts)
    policy_payload["copr_repository_state"] = _string_or_none(facts.repository_state)
    policy_payload["copr_repository_enable_action"] = _string_or_none(facts.repository_enable_action)
    policy_payload["copr_package_origin"] = _string_or_none(facts.package_origin)
    policy_payload["copr_package_from_repo"] = _string_or_none(facts.package_from_repo)


def _append_rpm_ostree_policy_fields(policy_payload: dict[str, object], facts) -> None:
    policy_payload["rpm_ostree"] = _rpm_ostree_context_to_dict(facts)
    policy_payload["rpm_ostree_status"] = _string_or_none(facts.status)
    policy_payload["rpm_ostree_booted_requested_packages"] = _csv_or_none(
        facts.booted_requested_packages
    )
    policy_payload["rpm_ostree_booted_packages"] = _csv_or_none(facts.booted_packages)
    policy_payload["rpm_ostree_pending_deployment"] = _bool_string_or_none(
        facts.pending_deployment
    )
    policy_payload["rpm_ostree_pending_requested_packages"] = _csv_or_none(
        facts.pending_requested_packages
    )
    policy_payload["rpm_ostree_pending_packages"] = _csv_or_none(facts.pending_packages)
    policy_payload["rpm_ostree_transaction_active"] = _bool_string_or_none(
        facts.transaction_active
    )


def _execution_probe_to_dict(probe) -> dict[str, object]:
    return {
        "status": probe.status,
        "command": list(probe.command),
        "required_commands": list(probe.required_commands),
        "exit_code": probe.exit_code,
        "package_present": probe.package_present,
    }


def decision_record_schema_metadata() -> dict[str, object]:
    return {
        "schema_id": DECISION_RECORD_SCHEMA_ID,
        "schema_name": DECISION_RECORD_SCHEMA_NAME,
        "schema_version": DECISION_RECORD_SCHEMA_VERSION,
        "public_version": read_version(),
        "canonical_sections": list(CANONICAL_SECTIONS),
        "presentation_sections": list(PRESENTATION_SECTIONS),
        "legacy_top_level_mirrors": True,
    }


def decision_record_facts(record: DecisionRecord) -> dict[str, object]:
    stable_ids = decision_record_stable_ids(record)
    facts: dict[str, object] = {
        "request": {
            "original_text": record.request.original_text,
            "normalized_text": record.request.normalized_text,
            "intent": record.request.intent,
            "action_id": stable_ids["action_id"],
            "domain_kind": record.request.domain_kind,
            "execution_surface": record.request.execution_surface,
            "requested_source": record.request.requested_source,
            "source_coordinate": record.request.source_coordinate,
            "environment_target": record.request.environment_target,
            "target": record.request.target,
            "status": record.request.status,
            "reason": record.request.reason,
            "observations": list(record.request.observations),
            "action_count": record.request.action_count,
        },
        "outcome": record.outcome,
    }

    if record.host_profile is not None:
        facts["host_profile"] = _host_profile_to_dict(record.host_profile)

    if record.policy is not None:
        policy_payload: dict[str, object] = {
            "domain_kind": record.policy.domain_kind,
            "source_type": record.policy.source_type,
            "execution_surface": record.policy.execution_surface,
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
        facts["policy"] = policy_payload
        if record.request.requested_source == "aur":
            policy_payload["observed_aur_helpers"] = (
                list(record.host_profile.observed_third_party_package_tools)
                if record.host_profile is not None
                else []
            )
            policy_payload["supported_aur_helpers"] = list(supported_aur_helpers())
            policy_payload["selected_aur_helper"] = (
                supported_aur_helper(record.host_profile) if record.host_profile is not None else None
            )
            policy_payload["out_of_contract_aur_helpers"] = (
                list(observed_out_of_contract_aur_helpers(record.host_profile))
                if record.host_profile is not None
                else []
            )
        if record.policy.immutable_host_facts is not None:
            _append_immutable_policy_fields(policy_payload, record.policy.immutable_host_facts)
        if record.request.requested_source == "copr" and record.policy.copr_facts is not None:
            _append_copr_policy_fields(policy_payload, record.policy.copr_facts)
        if record.request.requested_source == "ppa" and record.policy.ppa_facts is not None:
            _append_ppa_policy_fields(policy_payload, record.policy.ppa_facts)
        if record.request.domain_kind == "user_software" and record.policy.flatpak_facts is not None:
            _append_flatpak_policy_fields(policy_payload, record.policy.flatpak_facts)
        if record.request.execution_surface == "toolbox" and record.policy.toolbox_facts is not None:
            _append_mediated_policy_fields(policy_payload, "toolbox", record.policy.toolbox_facts)
        if record.request.execution_surface == "distrobox" and record.policy.distrobox_facts is not None:
            _append_mediated_policy_fields(policy_payload, "distrobox", record.policy.distrobox_facts)
        if record.request.execution_surface == "rpm_ostree" and record.policy.rpm_ostree_facts is not None:
            _append_rpm_ostree_policy_fields(policy_payload, record.policy.rpm_ostree_facts)

    if record.environment_resolution is not None:
        facts["environment_resolution"] = {
            "execution_surface": record.environment_resolution.execution_surface,
            "original_environment": record.environment_resolution.original_environment,
            "resolved_environment": record.environment_resolution.resolved_environment,
            "observed_environments": list(record.environment_resolution.observed_environments),
            "status": record.environment_resolution.status,
            "source": record.environment_resolution.source,
            "reason": record.environment_resolution.reason,
            "diagnostic_command": list(record.environment_resolution.diagnostic_command),
            "diagnostic_exit_code": record.environment_resolution.diagnostic_exit_code,
            "diagnostic_stdout": record.environment_resolution.diagnostic_stdout,
            "diagnostic_stderr": record.environment_resolution.diagnostic_stderr,
        }

    if record.target_resolution is not None:
        facts["target_resolution"] = {
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
        route_payload = {
            "route_name": record.execution_route.route_name,
            "route_id": stable_ids["route_id"],
            "action_name": record.execution_route.action_name,
            "backend_name": record.execution_route.backend_name,
            "execution_surface": record.execution_route.execution_surface,
            "environment_target": record.execution_route.environment_target,
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
        if stable_ids["route_id"] != record.execution_route.route_name:
            route_payload["legacy_route_name"] = record.execution_route.route_name
        if record.execution_route.route_name.startswith("aur."):
            route_payload["selected_aur_helper"] = record.execution_route.backend_name
        if record.execution_route.route_name.startswith("copr."):
            route_payload["copr_enable_planned"] = bool(record.execution_route.pre_commands)
            if record.policy is not None and record.policy.copr_facts is not None:
                route_payload["copr_repository_state"] = _string_or_none(
                    record.policy.copr_facts.repository_state
                )
                route_payload["copr_package_origin"] = _string_or_none(
                    record.policy.copr_facts.package_origin
                )
                route_payload["copr_package_from_repo"] = _string_or_none(
                    record.policy.copr_facts.package_from_repo
                )
        if record.execution_route.route_name.startswith("ppa."):
            route_payload["ppa_preparation_planned"] = bool(record.execution_route.pre_commands)
            if record.policy is not None and record.policy.ppa_facts is not None:
                route_payload["ppa_supported_distros"] = _csv_or_none(
                    record.policy.ppa_facts.supported_distros
                )
                route_payload["ppa_capability"] = _string_or_none(record.policy.ppa_facts.capability)
                route_payload["ppa_install_preparation"] = _csv_or_none(
                    record.policy.ppa_facts.install_preparation
                )
        if record.execution_route.route_name.startswith("flatpak.") and record.policy is not None:
            if record.policy.flatpak_facts is not None:
                route_payload["flatpak_effective_remote"] = _string_or_none(
                    record.policy.flatpak_facts.effective_remote
                )
                route_payload["flatpak_remote_origin"] = _string_or_none(
                    record.policy.flatpak_facts.remote_origin
                )
                route_payload["flatpak_observed_remotes"] = _csv_or_none(
                    record.policy.flatpak_facts.observed_remotes
                )
                route_payload["flatpak_remove_origin_constraint"] = (
                    "enabled" if record.policy.flatpak_facts.remove_origin_constraint else None
                )
        if record.execution_route.route_name.startswith("rpm_ostree.") and record.policy is not None:
            if record.policy.immutable_host_facts is not None:
                route_payload["immutable_observed_surfaces"] = _csv_or_none(
                    record.policy.immutable_host_facts.observed_surfaces
                )
                route_payload["immutable_selected_surface"] = _string_or_none(
                    record.policy.immutable_host_facts.selected_surface
                )
            if record.policy.rpm_ostree_facts is not None:
                route_payload["rpm_ostree_status"] = _string_or_none(
                    record.policy.rpm_ostree_facts.status
                )
                route_payload["rpm_ostree_pending_deployment"] = _bool_string_or_none(
                    record.policy.rpm_ostree_facts.pending_deployment
                )
                route_payload["rpm_ostree_pending_requested_packages"] = _csv_or_none(
                    record.policy.rpm_ostree_facts.pending_requested_packages
                )
        facts["execution_route"] = route_payload

    if record.toolbox_profile is not None:
        facts["toolbox_profile"] = _host_profile_to_dict(record.toolbox_profile)

    if record.distrobox_profile is not None:
        facts["distrobox_profile"] = _host_profile_to_dict(record.distrobox_profile)

    if record.rpm_ostree_status is not None:
        facts["rpm_ostree_status"] = {
            "observed": record.rpm_ostree_status.observed,
            "status": record.rpm_ostree_status.status,
            "source": record.rpm_ostree_status.source,
            "reason": record.rpm_ostree_status.reason,
            "transaction_active": record.rpm_ostree_status.transaction_active,
            "booted_requested_packages": list(record.rpm_ostree_status.booted_requested_packages),
            "booted_packages": list(record.rpm_ostree_status.booted_packages),
            "booted_base_removals": list(record.rpm_ostree_status.booted_base_removals),
            "pending_deployment": record.rpm_ostree_status.pending_deployment,
            "pending_requested_packages": list(record.rpm_ostree_status.pending_requested_packages),
            "pending_packages": list(record.rpm_ostree_status.pending_packages),
            "pending_base_removals": list(record.rpm_ostree_status.pending_base_removals),
            "diagnostic_command": list(record.rpm_ostree_status.diagnostic_command),
            "diagnostic_exit_code": record.rpm_ostree_status.diagnostic_exit_code,
            "diagnostic_stdout": record.rpm_ostree_status.diagnostic_stdout,
            "diagnostic_stderr": record.rpm_ostree_status.diagnostic_stderr,
        }

    if record.execution is not None:
        execution_payload = {
            "status": record.execution.status,
            "event_id": stable_ids["event_id"],
            "attempted": record.execution.attempted,
            "confirmation_supplied": record.execution.confirmation_supplied,
            "command": list(record.execution.command),
            "exit_code": record.execution.exit_code,
            "pre_probe": None,
            "post_probe": None,
            "interactive_passthrough": record.execution.interactive_passthrough,
            "diagnostic_stdout": record.execution.diagnostic_stdout,
            "diagnostic_stderr": record.execution.diagnostic_stderr,
        }
        if record.execution.pre_probe is not None:
            execution_payload["pre_probe"] = _execution_probe_to_dict(record.execution.pre_probe)
        if record.execution.post_probe is not None:
            execution_payload["post_probe"] = _execution_probe_to_dict(record.execution.post_probe)
        facts["execution"] = execution_payload

    return facts


def decision_record_presentation(record: DecisionRecord) -> dict[str, object]:
    presentation: dict[str, object] = {"summary": record.summary}
    if record.execution is not None:
        execution_payload: dict[str, object] = {"summary": record.execution.summary}
        if record.execution.pre_probe is not None:
            execution_payload["pre_probe_summary"] = record.execution.pre_probe.summary
        if record.execution.post_probe is not None:
            execution_payload["post_probe_summary"] = record.execution.post_probe.summary
        presentation["execution"] = execution_payload
    return presentation


def validate_decision_record_payload(payload: Mapping[str, object]) -> tuple[str, ...]:
    errors: list[str] = []

    schema = payload.get("schema")
    if not isinstance(schema, Mapping):
        errors.append("schema ausente")
    else:
        if schema.get("schema_id") != DECISION_RECORD_SCHEMA_ID:
            errors.append("schema_id incorreto")
        if schema.get("schema_version") != DECISION_RECORD_SCHEMA_VERSION:
            errors.append("schema_version incorreto")
        if schema.get("public_version") != read_version():
            errors.append("public_version divergente")

    stable_ids = payload.get("stable_ids")
    if not isinstance(stable_ids, Mapping):
        errors.append("stable_ids ausente")
    else:
        action_id = stable_ids.get("action_id")
        route_id = stable_ids.get("route_id")
        event_id = stable_ids.get("event_id")
        if action_id is not None and action_id not in ACTION_IDS:
            errors.append("action_id fora do contrato")
        if route_id is not None and route_id not in ROUTE_IDS:
            errors.append("route_id fora do contrato")
        if event_id not in EVENT_IDS:
            errors.append("event_id fora do contrato")

    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        errors.append("facts ausente")
    else:
        if "summary" in facts:
            errors.append("facts nao pode carregar summary")
        request = facts.get("request")
        if not isinstance(request, Mapping):
            errors.append("facts.request ausente")
        else:
            request_action_id = request.get("action_id")
            if request_action_id is not None and request_action_id not in ACTION_IDS:
                errors.append("facts.request.action_id fora do contrato")

        execution_route = facts.get("execution_route")
        if isinstance(execution_route, Mapping):
            if execution_route.get("route_id") not in ROUTE_IDS:
                errors.append("facts.execution_route.route_id fora do contrato")

        execution = facts.get("execution")
        if isinstance(execution, Mapping):
            if "summary" in execution:
                errors.append("facts.execution nao pode carregar summary")
            if execution.get("event_id") not in EVENT_IDS:
                errors.append("facts.execution.event_id fora do contrato")
            for probe_name in ("pre_probe", "post_probe"):
                probe = execution.get(probe_name)
                if isinstance(probe, Mapping) and "summary" in probe:
                    errors.append(f"facts.execution.{probe_name} nao pode carregar summary")

        local_model = facts.get("local_model")
        if isinstance(local_model, Mapping):
            if local_model.get("mode") not in MODEL_MODES:
                errors.append("facts.local_model.mode fora do contrato")
            if local_model.get("authority_profile") != LOCAL_MODEL_AUTHORITY_PROFILE:
                errors.append("facts.local_model.authority_profile incorreto")
            if local_model.get("input_schema_id") != LOCAL_MODEL_INPUT_SCHEMA_ID:
                errors.append("facts.local_model.input_schema_id incorreto")
            requested_capability = local_model.get("requested_capability")
            if requested_capability not in (*LOCAL_MODEL_ALLOWED_CAPABILITIES, "none"):
                errors.append("facts.local_model.requested_capability fora do contrato")
            if local_model.get("allowed_capabilities") != list(LOCAL_MODEL_ALLOWED_CAPABILITIES):
                errors.append("facts.local_model.allowed_capabilities divergente")
            if local_model.get("forbidden_authorities") != list(LOCAL_MODEL_FORBIDDEN_AUTHORITIES):
                errors.append("facts.local_model.forbidden_authorities divergente")

    presentation = payload.get("presentation")
    if not isinstance(presentation, Mapping):
        errors.append("presentation ausente")
    else:
        if not isinstance(presentation.get("summary"), str):
            errors.append("presentation.summary ausente")

    return tuple(errors)

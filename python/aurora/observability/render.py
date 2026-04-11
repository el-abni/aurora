from __future__ import annotations

from collections.abc import Mapping

from aurora.contracts.decisions import DecisionRecord
from aurora.local_model.contracts import LocalModelProvider
from aurora.observability.decision_record import decision_record_to_dict
from aurora.presentation.formatting import field
from aurora.presentation.text_polish import polish_public_text


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _present(value: object) -> bool:
    return value is not None and value != "" and value != []


def _string_or_dash(value: object) -> str:
    if not _present(value):
        return "-"
    return str(value)


def _bool_or_dash(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _list_or_dash(value: object, *, separator: str) -> str:
    if isinstance(value, (list, tuple)):
        return separator.join(str(item) for item in value) or "-"
    if value is None:
        return "-"
    text = str(value)
    return text or "-"


def _compact_diagnostic(value: str) -> str:
    compact = " | ".join(line.strip() for line in value.splitlines() if line.strip())
    if not compact:
        return "-"
    if len(compact) <= 200:
        return compact
    return compact[:197].rstrip() + "..."


def _scope_label(request: Mapping[str, object]) -> str:
    execution_surface = request.get("execution_surface")
    domain_kind = request.get("domain_kind")
    requested_source = request.get("requested_source")
    if execution_surface == "rpm_ostree" and domain_kind == "host_package":
        return "pacote do host via rpm-ostree"
    if execution_surface == "distrobox" and domain_kind == "host_package":
        return "pacote do host dentro da distrobox"
    if execution_surface == "toolbox" and domain_kind == "host_package":
        return "pacote do host dentro da toolbox"
    if domain_kind == "user_software":
        return "software do usuário"
    if domain_kind == "host_package" and requested_source == "ppa":
        return "pacote do host via PPA"
    if domain_kind == "host_package" and requested_source == "copr":
        return "pacote do host via COPR"
    if domain_kind == "host_package" and requested_source == "aur":
        return "pacote do host pela rota AUR"
    if domain_kind == "host_package":
        return "pacote do host"
    return "indefinido"


def _append_environment_profile_lines(lines: list[str], profile, title: str) -> None:
    lines.extend(
        [
            "",
            title,
            field("linux_family", profile.linux_family_label),
            field("distro_id", profile.distro_id or "-"),
            field("distro_like", ", ".join(profile.distro_like) or "-"),
            field("mutability", profile.mutability_label),
            field("support_tier", profile.support_tier_label),
            field("compatibility", profile.compatibility_frontier_label),
            field("package_backends", profile.package_backends_label),
            field("observed_tools", profile.observed_package_tools_label),
            field(
                "observed_third_party_tools",
                profile.observed_third_party_package_tools_label,
            ),
        ]
    )


def _policy_section(policy: Mapping[str, object], section_name: str) -> Mapping[str, object] | None:
    return _mapping(policy.get(section_name))


def _policy_section_value(
    policy: Mapping[str, object],
    section_name: str,
    key: str,
    legacy_key: str | None = None,
) -> object:
    section = _policy_section(policy, section_name)
    if section is not None:
        value = section.get(key)
        if _present(value) or value is False:
            return value
    if legacy_key is None:
        return None
    return policy.get(legacy_key)


def _route_or_policy_value(
    route: Mapping[str, object],
    route_key: str,
    policy: Mapping[str, object] | None = None,
    *,
    policy_section: str | None = None,
    policy_key: str | None = None,
    policy_legacy_key: str | None = None,
) -> object:
    value = route.get(route_key)
    if _present(value) or value is False:
        return value
    if policy is None or policy_section is None or policy_key is None:
        return None
    return _policy_section_value(policy, policy_section, policy_key, policy_legacy_key)


def _append_surface_policy_lines(lines: list[str], policy: Mapping[str, object], surface: str) -> None:
    lines.extend(
        [
            field(
                f"{surface}_requested_environment",
                _string_or_dash(
                    _policy_section_value(
                        policy,
                        surface,
                        "requested_environment",
                        f"{surface}_requested_environment",
                    )
                ),
            ),
            field(
                f"{surface}_environment_status",
                _string_or_dash(
                    _policy_section_value(
                        policy,
                        surface,
                        "environment_status",
                        f"{surface}_environment_status",
                    )
                ),
            ),
            field(
                f"{surface}_resolved_environment",
                _string_or_dash(
                    _policy_section_value(
                        policy,
                        surface,
                        "resolved_environment",
                        f"{surface}_resolved_environment",
                    )
                ),
            ),
            field(
                f"{surface}_linux_family",
                _string_or_dash(
                    _policy_section_value(policy, surface, "linux_family", f"{surface}_linux_family")
                ),
            ),
            field(
                f"{surface}_support_tier",
                _string_or_dash(
                    _policy_section_value(policy, surface, "support_tier", f"{surface}_support_tier")
                ),
            ),
            field(
                f"{surface}_package_backends",
                _list_or_dash(
                    _policy_section_value(
                        policy,
                        surface,
                        "package_backends",
                        f"{surface}_package_backends",
                    ),
                    separator=",",
                ),
            ),
            field(
                f"{surface}_observed_commands",
                _list_or_dash(
                    _policy_section_value(
                        policy,
                        surface,
                        "observed_commands",
                        f"{surface}_observed_commands",
                    ),
                    separator=",",
                ),
            ),
            field(
                f"{surface}_sudo_observed",
                _bool_or_dash(
                    _policy_section_value(
                        policy,
                        surface,
                        "sudo_observed",
                        f"{surface}_sudo_observed",
                    )
                ),
            ),
        ]
    )


def _append_surface_route_lines(
    lines: list[str],
    route: Mapping[str, object],
    policy: Mapping[str, object] | None,
    surface: str,
) -> None:
    lines.extend(
        [
            field(
                f"{surface}_environment_status",
                _string_or_dash(
                    _route_or_policy_value(
                        route,
                        f"{surface}_environment_status",
                        policy,
                        policy_section=surface,
                        policy_key="environment_status",
                        policy_legacy_key=f"{surface}_environment_status",
                    )
                ),
            ),
            field(
                f"{surface}_resolved_environment",
                _string_or_dash(
                    _route_or_policy_value(
                        route,
                        f"{surface}_resolved_environment",
                        policy,
                        policy_section=surface,
                        policy_key="resolved_environment",
                        policy_legacy_key=f"{surface}_resolved_environment",
                    )
                ),
            ),
            field(
                f"{surface}_linux_family",
                _string_or_dash(
                    _route_or_policy_value(
                        route,
                        f"{surface}_linux_family",
                        policy,
                        policy_section=surface,
                        policy_key="linux_family",
                        policy_legacy_key=f"{surface}_linux_family",
                    )
                ),
            ),
            field(
                f"{surface}_package_backends",
                _list_or_dash(
                    _route_or_policy_value(
                        route,
                        f"{surface}_package_backends",
                        policy,
                        policy_section=surface,
                        policy_key="package_backends",
                        policy_legacy_key=f"{surface}_package_backends",
                    ),
                    separator=",",
                ),
            ),
            field(
                f"{surface}_sudo_observed",
                _bool_or_dash(
                    _route_or_policy_value(
                        route,
                        f"{surface}_sudo_observed",
                        policy,
                        policy_section=surface,
                        policy_key="sudo_observed",
                        policy_legacy_key=f"{surface}_sudo_observed",
                    )
                ),
            ),
        ]
    )


def render_decision_record(
    record: DecisionRecord,
    *,
    model_mode: str | None = None,
    model_provider: LocalModelProvider | None = None,
    environ: dict[str, str] | None = None,
) -> str:
    payload = decision_record_to_dict(
        record,
        model_mode=model_mode,
        model_provider=model_provider,
        environ=environ,
    )
    schema = _mapping(payload.get("schema")) or {}
    stable_ids = _mapping(payload.get("stable_ids")) or {}
    presentation = _mapping(payload.get("presentation")) or {}
    facts = _mapping(payload.get("facts")) or {}
    local_model = _mapping(facts.get("local_model"))
    request = _mapping(facts.get("request")) or {}
    policy = _mapping(facts.get("policy"))
    environment_resolution = _mapping(facts.get("environment_resolution"))
    target_resolution = _mapping(facts.get("target_resolution"))
    route = _mapping(facts.get("execution_route"))
    execution = _mapping(facts.get("execution"))
    rpm_ostree_status = _mapping(facts.get("rpm_ostree_status"))

    lines = [
        "Aurora decision record",
        field("schema_version", _string_or_dash(schema.get("schema_version"))),
        field("action_id", _string_or_dash(stable_ids.get("action_id"))),
        field("route_id", _string_or_dash(stable_ids.get("route_id"))),
        field("event_id", _string_or_dash(stable_ids.get("event_id"))),
        field("outcome", _string_or_dash(facts.get("outcome"))),
        field("summary", polish_public_text(_string_or_dash(presentation.get("summary")))),
    ]

    if local_model is not None:
        lines.extend(
            [
                "",
                "Local model seam",
                field("mode", _string_or_dash(local_model.get("mode"))),
                field("status", _string_or_dash(local_model.get("status"))),
                field(
                    "requested_capability",
                    _string_or_dash(local_model.get("requested_capability")),
                ),
                field(
                    "authority_profile",
                    _string_or_dash(local_model.get("authority_profile")),
                ),
                field("advisory_only", _bool_or_dash(local_model.get("advisory_only"))),
                field("provider_name", _string_or_dash(local_model.get("provider_name"))),
                field(
                    "allowed_capabilities",
                    _list_or_dash(local_model.get("allowed_capabilities"), separator=", "),
                ),
                field(
                    "forbidden_authorities",
                    _list_or_dash(local_model.get("forbidden_authorities"), separator=", "),
                ),
                field(
                    "consumed_sections",
                    _list_or_dash(local_model.get("consumed_sections"), separator=", "),
                ),
                field("input_schema_id", _string_or_dash(local_model.get("input_schema_id"))),
                field(
                    "fallback_reason",
                    polish_public_text(_string_or_dash(local_model.get("fallback_reason"))),
                ),
                field("output_text", polish_public_text(_string_or_dash(local_model.get("output_text")))),
            ]
        )

    lines.extend(
        [
            "",
            "Request",
            field("original_text", _string_or_dash(request.get("original_text"))),
            field("normalized_text", _string_or_dash(request.get("normalized_text"))),
            field("intent", _string_or_dash(request.get("intent"))),
            field("domain_kind", _string_or_dash(request.get("domain_kind"))),
            field("execution_surface", _string_or_dash(request.get("execution_surface"))),
            field("requested_source", _string_or_dash(request.get("requested_source"))),
            field("source_coordinate", _string_or_dash(request.get("source_coordinate"))),
            field("environment_target", _string_or_dash(request.get("environment_target"))),
            field("scope_label", _scope_label(request)),
            field("target", _string_or_dash(request.get("target"))),
            field("status", _string_or_dash(request.get("status"))),
            field("reason", polish_public_text(_string_or_dash(request.get("reason")))),
            field("observations", _list_or_dash(request.get("observations"), separator=", ")),
            field("action_count", _string_or_dash(request.get("action_count"))),
        ]
    )

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
                field(
                    "observed_distrobox_environments",
                    record.host_profile.observed_distrobox_environments_label,
                ),
                field(
                    "observed_immutable_surfaces",
                    record.host_profile.observed_immutable_surfaces_label,
                ),
            ]
        )

    if policy is not None:
        lines.extend(
            [
                "",
                "Policy",
                field("domain_kind", _string_or_dash(policy.get("domain_kind"))),
                field("source_type", _string_or_dash(policy.get("source_type"))),
                field("execution_surface", _string_or_dash(policy.get("execution_surface"))),
                field("trust_level", _string_or_dash(policy.get("trust_level"))),
                field("software_criticality", _string_or_dash(policy.get("software_criticality"))),
                field("policy_outcome", _string_or_dash(policy.get("policy_outcome"))),
                field("requires_confirmation", _bool_or_dash(policy.get("requires_confirmation"))),
                field("confirmation_supplied", _bool_or_dash(policy.get("confirmation_supplied"))),
                field("reversal_level", _string_or_dash(policy.get("reversal_level"))),
                field("trust_signals", _list_or_dash(policy.get("trust_signals"), separator=", ")),
                field("trust_gaps", _list_or_dash(policy.get("trust_gaps"), separator=", ")),
                field("policy_reason", polish_public_text(_string_or_dash(policy.get("reason")))),
            ]
        )
        if request.get("requested_source") == "aur":
            lines.extend(
                [
                    field("observed_aur_helpers", _list_or_dash(policy.get("observed_aur_helpers"), separator=", ")),
                    field("supported_aur_helpers", _list_or_dash(policy.get("supported_aur_helpers"), separator=", ")),
                    field("selected_aur_helper", _string_or_dash(policy.get("selected_aur_helper"))),
                    field(
                        "out_of_contract_aur_helpers",
                        _list_or_dash(policy.get("out_of_contract_aur_helpers"), separator=", "),
                    ),
                ]
            )
        if request.get("requested_source") == "copr":
            lines.extend(
                [
                    field(
                        "copr_repository_state",
                        _string_or_dash(
                            _policy_section_value(policy, "copr", "repository_state", "copr_repository_state")
                        ),
                    ),
                    field(
                        "copr_repository_enable_action",
                        _string_or_dash(
                            _policy_section_value(
                                policy,
                                "copr",
                                "repository_enable_action",
                                "copr_repository_enable_action",
                            )
                        ),
                    ),
                    field(
                        "copr_package_origin",
                        _string_or_dash(
                            _policy_section_value(policy, "copr", "package_origin", "copr_package_origin")
                        ),
                    ),
                    field(
                        "copr_package_from_repo",
                        _string_or_dash(
                            _policy_section_value(policy, "copr", "package_from_repo", "copr_package_from_repo")
                        ),
                    ),
                ]
            )
        if request.get("requested_source") == "ppa":
            lines.extend(
                [
                    field(
                        "ppa_supported_distros",
                        _list_or_dash(
                            _policy_section_value(policy, "ppa", "supported_distros", "ppa_supported_distros"),
                            separator=",",
                        ),
                    ),
                    field(
                        "ppa_capability",
                        _string_or_dash(
                            _policy_section_value(policy, "ppa", "capability", "ppa_capability")
                        ),
                    ),
                    field(
                        "ppa_state_probe",
                        _string_or_dash(
                            _policy_section_value(policy, "ppa", "state_probe", "ppa_state_probe")
                        ),
                    ),
                    field(
                        "ppa_install_preparation",
                        _list_or_dash(
                            _policy_section_value(
                                policy,
                                "ppa",
                                "install_preparation",
                                "ppa_install_preparation",
                            ),
                            separator=",",
                        ),
                    ),
                ]
            )
        if request.get("domain_kind") == "user_software":
            flatpak_remove_constraint = _policy_section_value(
                policy,
                "flatpak",
                "remove_origin_constraint",
                "flatpak_remove_origin_constraint",
            )
            lines.extend(
                [
                    field(
                        "flatpak_effective_remote",
                        _string_or_dash(
                            _policy_section_value(
                                policy,
                                "flatpak",
                                "effective_remote",
                                "flatpak_effective_remote",
                            )
                        ),
                    ),
                    field(
                        "flatpak_remote_origin",
                        _string_or_dash(
                            _policy_section_value(policy, "flatpak", "remote_origin", "flatpak_remote_origin")
                        ),
                    ),
                    field(
                        "flatpak_observed_remotes",
                        _list_or_dash(
                            _policy_section_value(
                                policy,
                                "flatpak",
                                "observed_remotes",
                                "flatpak_observed_remotes",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "flatpak_remove_origin_constraint",
                        "enabled"
                        if flatpak_remove_constraint in {True, "enabled"}
                        else _string_or_dash(
                            flatpak_remove_constraint if flatpak_remove_constraint not in {False, ""} else None
                        ),
                    ),
                ]
            )
        immutable_context = _policy_section(policy, "immutable_host_context")
        if immutable_context is not None and any(
            _present(immutable_context.get(key)) or immutable_context.get(key) is True
            for key in (
                "host_is_immutable",
                "observed_surfaces",
                "selected_surface",
                "toolbox_environments",
                "distrobox_environments",
            )
        ):
            lines.extend(
                [
                    field(
                        "immutable_host",
                        _bool_or_dash(
                            immutable_context.get("host_is_immutable", policy.get("immutable_host"))
                        ),
                    ),
                    field(
                        "immutable_observed_surfaces",
                        _list_or_dash(
                            immutable_context.get(
                                "observed_surfaces",
                                policy.get("immutable_observed_surfaces"),
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "immutable_selected_surface",
                        _string_or_dash(
                            immutable_context.get(
                                "selected_surface",
                                policy.get("immutable_selected_surface"),
                            )
                        ),
                    ),
                    field(
                        "immutable_toolbox_environments",
                        _list_or_dash(
                            immutable_context.get(
                                "toolbox_environments",
                                policy.get("immutable_toolbox_environments"),
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "immutable_distrobox_environments",
                        _list_or_dash(
                            immutable_context.get(
                                "distrobox_environments",
                                policy.get("immutable_distrobox_environments"),
                            ),
                            separator=",",
                        ),
                    ),
                ]
            )
        if request.get("execution_surface") in {"toolbox", "distrobox"}:
            _append_surface_policy_lines(lines, policy, str(request.get("execution_surface")))
        if request.get("execution_surface") == "rpm_ostree":
            lines.extend(
                [
                    field(
                        "rpm_ostree_status",
                        _string_or_dash(
                            _policy_section_value(policy, "rpm_ostree", "status", "rpm_ostree_status")
                        ),
                    ),
                    field(
                        "rpm_ostree_booted_requested_packages",
                        _list_or_dash(
                            _policy_section_value(
                                policy,
                                "rpm_ostree",
                                "booted_requested_packages",
                                "rpm_ostree_booted_requested_packages",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "rpm_ostree_booted_packages",
                        _list_or_dash(
                            _policy_section_value(
                                policy,
                                "rpm_ostree",
                                "booted_packages",
                                "rpm_ostree_booted_packages",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "rpm_ostree_pending_deployment",
                        _bool_or_dash(
                            _policy_section_value(
                                policy,
                                "rpm_ostree",
                                "pending_deployment",
                                "rpm_ostree_pending_deployment",
                            )
                        ),
                    ),
                    field(
                        "rpm_ostree_pending_requested_packages",
                        _list_or_dash(
                            _policy_section_value(
                                policy,
                                "rpm_ostree",
                                "pending_requested_packages",
                                "rpm_ostree_pending_requested_packages",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "rpm_ostree_pending_packages",
                        _list_or_dash(
                            _policy_section_value(
                                policy,
                                "rpm_ostree",
                                "pending_packages",
                                "rpm_ostree_pending_packages",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "rpm_ostree_transaction_active",
                        _bool_or_dash(
                            _policy_section_value(
                                policy,
                                "rpm_ostree",
                                "transaction_active",
                                "rpm_ostree_transaction_active",
                            )
                        ),
                    ),
                ]
            )

    if environment_resolution is not None:
        lines.extend(
            [
                "",
                "Environment resolution",
                field("execution_surface", _string_or_dash(environment_resolution.get("execution_surface"))),
                field("original_environment", _string_or_dash(environment_resolution.get("original_environment"))),
                field("resolved_environment", _string_or_dash(environment_resolution.get("resolved_environment"))),
                field(
                    "observed_environments",
                    _list_or_dash(environment_resolution.get("observed_environments"), separator=", "),
                ),
                field("status", _string_or_dash(environment_resolution.get("status"))),
                field("source", _string_or_dash(environment_resolution.get("source"))),
                field("reason", polish_public_text(_string_or_dash(environment_resolution.get("reason")))),
            ]
        )
        if (
            environment_resolution.get("diagnostic_command")
            or environment_resolution.get("diagnostic_exit_code") is not None
            or environment_resolution.get("diagnostic_stdout")
            or environment_resolution.get("diagnostic_stderr")
        ):
            lines.extend(
                [
                    field(
                        "diagnostic_command",
                        _list_or_dash(environment_resolution.get("diagnostic_command"), separator=" "),
                    ),
                    field(
                        "diagnostic_exit_code",
                        _string_or_dash(environment_resolution.get("diagnostic_exit_code")),
                    ),
                    field(
                        "diagnostic_stdout",
                        _compact_diagnostic(str(environment_resolution.get("diagnostic_stdout") or "")),
                    ),
                    field(
                        "diagnostic_stderr",
                        _compact_diagnostic(str(environment_resolution.get("diagnostic_stderr") or "")),
                    ),
                ]
            )

    if target_resolution is not None:
        lines.extend(
            [
                "",
                "Target resolution",
                field("original_target", _string_or_dash(target_resolution.get("original_target"))),
                field("consulted_target", _string_or_dash(target_resolution.get("consulted_target"))),
                field(
                    "consulted_targets",
                    _list_or_dash(target_resolution.get("consulted_targets"), separator=", "),
                ),
                field("resolved_target", _string_or_dash(target_resolution.get("resolved_target"))),
                field("status", _string_or_dash(target_resolution.get("status"))),
                field("source", _string_or_dash(target_resolution.get("source"))),
                field("canonicalized", _bool_or_dash(target_resolution.get("canonicalized"))),
                field("candidates", _list_or_dash(target_resolution.get("candidates"), separator=", ")),
                field(
                    "resolution_reason",
                    polish_public_text(_string_or_dash(target_resolution.get("reason"))),
                ),
            ]
        )
        if (
            target_resolution.get("diagnostic_command")
            or target_resolution.get("diagnostic_exit_code") is not None
            or target_resolution.get("diagnostic_stdout")
            or target_resolution.get("diagnostic_stderr")
        ):
            lines.extend(
                [
                    field(
                        "diagnostic_command",
                        _list_or_dash(target_resolution.get("diagnostic_command"), separator=" "),
                    ),
                    field(
                        "diagnostic_exit_code",
                        _string_or_dash(target_resolution.get("diagnostic_exit_code")),
                    ),
                    field(
                        "diagnostic_stdout",
                        _compact_diagnostic(str(target_resolution.get("diagnostic_stdout") or "")),
                    ),
                    field(
                        "diagnostic_stderr",
                        _compact_diagnostic(str(target_resolution.get("diagnostic_stderr") or "")),
                    ),
                ]
            )

    if route is not None:
        lines.extend(
            [
                "",
                "Execution route",
                field("route_name", _string_or_dash(route.get("route_name"))),
                field("action_name", _string_or_dash(route.get("action_name"))),
                field("backend_name", _string_or_dash(route.get("backend_name"))),
                field("execution_surface", _string_or_dash(route.get("execution_surface"))),
                field("environment_target", _string_or_dash(route.get("environment_target"))),
                field("scope_label", _scope_label(request)),
                field("implemented", _bool_or_dash(route.get("implemented"))),
                field(
                    "requires_privilege_escalation",
                    _bool_or_dash(route.get("requires_privilege_escalation")),
                ),
                field("interactive_passthrough", _bool_or_dash(route.get("interactive_passthrough"))),
                field(
                    "pre_commands",
                    (
                        " | ".join(" ".join(str(part) for part in command) for command in route.get("pre_commands", []))
                        or "-"
                    ),
                ),
                field("command", _list_or_dash(route.get("command"), separator=" ")),
                field("state_probe", _list_or_dash(route.get("state_probe_command"), separator=" ")),
                field("notes", polish_public_text(_list_or_dash(route.get("notes"), separator="; "))),
            ]
        )
        route_name = str(route.get("route_name") or "")
        if route_name.startswith("aur."):
            lines.append(field("selected_aur_helper", _string_or_dash(route.get("backend_name"))))
        if route_name.startswith("copr."):
            lines.extend(
                [
                    field("copr_enable_planned", _bool_or_dash(route.get("copr_enable_planned"))),
                    field(
                        "copr_repository_state",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "copr_repository_state",
                                policy,
                                policy_section="copr",
                                policy_key="repository_state",
                                policy_legacy_key="copr_repository_state",
                            )
                        ),
                    ),
                    field(
                        "copr_package_origin",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "copr_package_origin",
                                policy,
                                policy_section="copr",
                                policy_key="package_origin",
                                policy_legacy_key="copr_package_origin",
                            )
                        ),
                    ),
                    field(
                        "copr_package_from_repo",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "copr_package_from_repo",
                                policy,
                                policy_section="copr",
                                policy_key="package_from_repo",
                                policy_legacy_key="copr_package_from_repo",
                            )
                        ),
                    ),
                ]
            )
        if route_name.startswith("ppa."):
            lines.extend(
                [
                    field("ppa_preparation_planned", _bool_or_dash(route.get("ppa_preparation_planned"))),
                    field(
                        "ppa_supported_distros",
                        _list_or_dash(
                            _route_or_policy_value(
                                route,
                                "ppa_supported_distros",
                                policy,
                                policy_section="ppa",
                                policy_key="supported_distros",
                                policy_legacy_key="ppa_supported_distros",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "ppa_capability",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "ppa_capability",
                                policy,
                                policy_section="ppa",
                                policy_key="capability",
                                policy_legacy_key="ppa_capability",
                            )
                        ),
                    ),
                    field(
                        "ppa_install_preparation",
                        _list_or_dash(
                            _route_or_policy_value(
                                route,
                                "ppa_install_preparation",
                                policy,
                                policy_section="ppa",
                                policy_key="install_preparation",
                                policy_legacy_key="ppa_install_preparation",
                            ),
                            separator=",",
                        ),
                    ),
                ]
            )
        if route_name.startswith("flatpak."):
            flatpak_remove_constraint = _route_or_policy_value(
                route,
                "flatpak_remove_origin_constraint",
                policy,
                policy_section="flatpak",
                policy_key="remove_origin_constraint",
                policy_legacy_key="flatpak_remove_origin_constraint",
            )
            lines.extend(
                [
                    field(
                        "flatpak_effective_remote",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "flatpak_effective_remote",
                                policy,
                                policy_section="flatpak",
                                policy_key="effective_remote",
                                policy_legacy_key="flatpak_effective_remote",
                            )
                        ),
                    ),
                    field(
                        "flatpak_remote_origin",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "flatpak_remote_origin",
                                policy,
                                policy_section="flatpak",
                                policy_key="remote_origin",
                                policy_legacy_key="flatpak_remote_origin",
                            )
                        ),
                    ),
                    field(
                        "flatpak_observed_remotes",
                        _list_or_dash(
                            _route_or_policy_value(
                                route,
                                "flatpak_observed_remotes",
                                policy,
                                policy_section="flatpak",
                                policy_key="observed_remotes",
                                policy_legacy_key="flatpak_observed_remotes",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "flatpak_remove_origin_constraint",
                        "enabled"
                        if flatpak_remove_constraint in {True, "enabled"}
                        else _string_or_dash(
                            flatpak_remove_constraint if flatpak_remove_constraint not in {False, ""} else None
                        ),
                    ),
                ]
            )
        if route_name.startswith("rpm_ostree."):
            lines.extend(
                [
                    field(
                        "immutable_observed_surfaces",
                        _list_or_dash(
                            _route_or_policy_value(
                                route,
                                "immutable_observed_surfaces",
                                policy,
                                policy_section="immutable_host_context",
                                policy_key="observed_surfaces",
                                policy_legacy_key="immutable_observed_surfaces",
                            ),
                            separator=",",
                        ),
                    ),
                    field(
                        "immutable_selected_surface",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "immutable_selected_surface",
                                policy,
                                policy_section="immutable_host_context",
                                policy_key="selected_surface",
                                policy_legacy_key="immutable_selected_surface",
                            )
                        ),
                    ),
                    field(
                        "rpm_ostree_status",
                        _string_or_dash(
                            _route_or_policy_value(
                                route,
                                "rpm_ostree_status",
                                policy,
                                policy_section="rpm_ostree",
                                policy_key="status",
                                policy_legacy_key="rpm_ostree_status",
                            )
                        ),
                    ),
                    field(
                        "rpm_ostree_pending_deployment",
                        _bool_or_dash(
                            _route_or_policy_value(
                                route,
                                "rpm_ostree_pending_deployment",
                                policy,
                                policy_section="rpm_ostree",
                                policy_key="pending_deployment",
                                policy_legacy_key="rpm_ostree_pending_deployment",
                            )
                        ),
                    ),
                    field(
                        "rpm_ostree_pending_requested_packages",
                        _list_or_dash(
                            _route_or_policy_value(
                                route,
                                "rpm_ostree_pending_requested_packages",
                                policy,
                                policy_section="rpm_ostree",
                                policy_key="pending_requested_packages",
                                policy_legacy_key="rpm_ostree_pending_requested_packages",
                            ),
                            separator=",",
                        ),
                    ),
                ]
            )
        if route_name.startswith("toolbox."):
            _append_surface_route_lines(lines, route, policy, "toolbox")
        if route_name.startswith("distrobox."):
            _append_surface_route_lines(lines, route, policy, "distrobox")

    if record.toolbox_profile is not None:
        _append_environment_profile_lines(lines, record.toolbox_profile, "Toolbox profile")

    if record.distrobox_profile is not None:
        _append_environment_profile_lines(lines, record.distrobox_profile, "Distrobox profile")

    if rpm_ostree_status is not None:
        lines.extend(
            [
                "",
                "rpm-ostree status",
                field("observed", _bool_or_dash(rpm_ostree_status.get("observed"))),
                field("status", _string_or_dash(rpm_ostree_status.get("status"))),
                field("source", _string_or_dash(rpm_ostree_status.get("source"))),
                field("reason", polish_public_text(_string_or_dash(rpm_ostree_status.get("reason")))),
                field("transaction_active", _bool_or_dash(rpm_ostree_status.get("transaction_active"))),
                field(
                    "booted_requested_packages",
                    _list_or_dash(rpm_ostree_status.get("booted_requested_packages"), separator=", "),
                ),
                field(
                    "booted_packages",
                    _list_or_dash(rpm_ostree_status.get("booted_packages"), separator=", "),
                ),
                field(
                    "booted_base_removals",
                    _list_or_dash(rpm_ostree_status.get("booted_base_removals"), separator=", "),
                ),
                field("pending_deployment", _bool_or_dash(rpm_ostree_status.get("pending_deployment"))),
                field(
                    "pending_requested_packages",
                    _list_or_dash(rpm_ostree_status.get("pending_requested_packages"), separator=", "),
                ),
                field(
                    "pending_packages",
                    _list_or_dash(rpm_ostree_status.get("pending_packages"), separator=", "),
                ),
                field(
                    "pending_base_removals",
                    _list_or_dash(rpm_ostree_status.get("pending_base_removals"), separator=", "),
                ),
                field(
                    "diagnostic_command",
                    _list_or_dash(rpm_ostree_status.get("diagnostic_command"), separator=" "),
                ),
                field(
                    "diagnostic_exit_code",
                    _string_or_dash(rpm_ostree_status.get("diagnostic_exit_code")),
                ),
                field(
                    "diagnostic_stdout",
                    _compact_diagnostic(str(rpm_ostree_status.get("diagnostic_stdout") or "")),
                ),
                field(
                    "diagnostic_stderr",
                    _compact_diagnostic(str(rpm_ostree_status.get("diagnostic_stderr") or "")),
                ),
            ]
        )

    if execution is not None:
        execution_presentation = _mapping(presentation.get("execution")) or {}
        lines.extend(
            [
                "",
                "Execution",
                field("status", _string_or_dash(execution.get("status"))),
                field("attempted", _bool_or_dash(execution.get("attempted"))),
                field("confirmation_supplied", _bool_or_dash(execution.get("confirmation_supplied"))),
                field("interactive_passthrough", _bool_or_dash(execution.get("interactive_passthrough"))),
                field("exit_code", _string_or_dash(execution.get("exit_code"))),
                field(
                    "summary",
                    polish_public_text(_string_or_dash(execution_presentation.get("summary"))),
                ),
                field(
                    "pre_probe",
                    polish_public_text(
                        _string_or_dash(execution_presentation.get("pre_probe_summary"))
                    ),
                ),
                field(
                    "post_probe",
                    polish_public_text(
                        _string_or_dash(execution_presentation.get("post_probe_summary"))
                    ),
                ),
            ]
        )
        if execution.get("diagnostic_stdout") or execution.get("diagnostic_stderr"):
            lines.extend(
                [
                    field(
                        "diagnostic_stdout",
                        _compact_diagnostic(str(execution.get("diagnostic_stdout") or "")),
                    ),
                    field(
                        "diagnostic_stderr",
                        _compact_diagnostic(str(execution.get("diagnostic_stderr") or "")),
                    ),
                ]
            )
    return "\n".join(lines)

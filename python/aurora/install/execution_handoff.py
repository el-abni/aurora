from __future__ import annotations

from dataclasses import replace
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence

from aurora.contracts.decisions import DecisionRecord
from aurora.contracts.execution import ExecutionProbe, ExecutionResult
from aurora.install.sources.aur import (
    aur_mutation_reports_no_matching_package,
    aur_search_has_no_results,
    aur_search_has_parseable_candidates,
)
from aurora.install.sources.flatpak import (
    flatpak_mutation_reports_no_matching_ref,
    flatpak_search_has_no_results,
)
from aurora.linux.host_package import mutation_reports_no_matching_package, search_has_no_results
from aurora.presentation.messages import (
    backend_failed_message,
    backend_missing_message,
    blocked_message,
    confirmation_required_message,
    interactive_handoff_return_message,
    interactive_handoff_start_message,
    mutation_success_message,
    no_results_message,
    package_not_found_message,
    noop_message,
    not_implemented_message,
    out_of_scope_message,
    search_results_message,
    state_confirmation_failed_message,
    state_probe_missing_message,
    target_resolution_blocked_message,
)

UNSUPPORTED_EXIT = 120
Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
Announcer = Callable[[str], None]


def _run_command(
    args: Sequence[str],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False, env=environ)


def _run_interactive_command(
    args: Sequence[str],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, check=False, env=environ)
    return subprocess.CompletedProcess(args, proc.returncode, "", "")


def _required_backend_available(
    route: tuple[str, ...],
    required_commands: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    command_names = required_commands or route[:1]
    return all(shutil.which(name, path=path) is not None for name in command_names)


def _probe_state(
    record: DecisionRecord,
    *,
    run: Runner,
    environ: dict[str, str] | None = None,
) -> ExecutionProbe:
    route = record.execution_route
    if route is None or not route.state_probe_command:
        return ExecutionProbe(status="not_required", summary="esta rota nao exige state probe.")

    if not _required_backend_available(
        route.state_probe_command,
        route.state_probe_required_commands,
        environ=environ,
    ):
        probe_label = route.state_probe_command[0]
        return ExecutionProbe(
            status="probe_missing",
            command=route.state_probe_command,
            required_commands=route.state_probe_required_commands,
            summary=state_probe_missing_message(route.backend_name, probe_label),
        )

    proc = run(route.state_probe_command)
    package_present = proc.returncode == 0
    summary = _probe_summary(record, package_present)
    return ExecutionProbe(
        status="completed",
        command=route.state_probe_command,
        required_commands=route.state_probe_required_commands,
        exit_code=proc.returncode,
        package_present=package_present,
        summary=summary,
    )


def _result(
    record: DecisionRecord,
    *,
    exit_code: int,
    outcome: str,
    message: str,
    execution: ExecutionResult,
) -> tuple[int, DecisionRecord, str]:
    return exit_code, replace(record, outcome=outcome, summary=message, execution=execution), message


def _is_user_software(record: DecisionRecord) -> bool:
    return record.request.domain_kind == "user_software"


def _is_copr_source(record: DecisionRecord) -> bool:
    return record.request.domain_kind == "host_package" and record.request.requested_source == "copr"


def _is_aur_source(record: DecisionRecord) -> bool:
    return record.request.domain_kind == "host_package" and record.request.requested_source == "aur"


def _target_label(record: DecisionRecord) -> str:
    if _is_copr_source(record):
        return "pacote do COPR"
    if _is_aur_source(record):
        return "pacote AUR"
    return "software" if _is_user_software(record) else "pacote"


def _location_label(record: DecisionRecord) -> str:
    if _is_copr_source(record):
        return "neste host via COPR"
    if _is_aur_source(record):
        return "como pacote AUR neste host"
    return "na instalação do usuário" if _is_user_software(record) else "neste host"


def _probe_summary(record: DecisionRecord, package_present: bool) -> str:
    if _is_copr_source(record):
        if package_present:
            return "pacote presente no host para a rota COPR."
        return "pacote ausente no host para a rota COPR."
    if _is_user_software(record):
        if package_present:
            return "software presente na instalação do usuário."
        return "software ausente na instalação do usuário."
    if _is_aur_source(record):
        if package_present:
            return "pacote AUR presente como foreign no host."
        return "pacote AUR ausente como foreign no host."
    if package_present:
        return "pacote presente no host."
    return "pacote ausente no host."


def _target_resolution_block_reason(record: DecisionRecord) -> str | None:
    resolution = record.target_resolution
    if resolution is None:
        return None
    if resolution.status in {"ambiguous", "not_found", "unresolved", "source_mismatch"}:
        return resolution.reason
    return None


def _search_reports_no_results(
    record: DecisionRecord,
    *,
    stdout: str,
    stderr: str,
    returncode: int,
) -> bool:
    route = record.execution_route
    if route is not None and route.route_name.startswith("aur."):
        return aur_search_has_no_results(stdout, stderr, returncode)
    if route is not None and route.backend_name == "flatpak":
        return flatpak_search_has_no_results(stdout, stderr, returncode)
    return search_has_no_results(stdout, stderr, returncode)


def _mutation_reports_not_found(record: DecisionRecord, stdout: str, stderr: str) -> bool:
    route = record.execution_route
    if route is not None and route.route_name.startswith("aur."):
        return aur_mutation_reports_no_matching_package(stdout, stderr)
    if route is not None and route.backend_name == "flatpak":
        return flatpak_mutation_reports_no_matching_ref(stdout, stderr)
    return mutation_reports_no_matching_package(stdout, stderr)


def _pre_commands_with_requirements(route) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    prepared: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for index, command in enumerate(route.pre_commands):
        required_commands = (
            route.pre_command_required_commands[index]
            if index < len(route.pre_command_required_commands)
            else ()
        )
        prepared.append((command, required_commands))
    return tuple(prepared)


def _execute_search(
    record: DecisionRecord,
    *,
    run: Runner,
    environ: dict[str, str] | None = None,
) -> tuple[int, DecisionRecord, str]:
    route = record.execution_route
    assert route is not None

    if not _required_backend_available(route.command, route.required_commands, environ=environ):
        message = backend_missing_message(route.backend_name)
        return _result(
            record,
            exit_code=1,
            outcome="operational_error",
            message=message,
            execution=ExecutionResult(
                status="backend_missing",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    proc = run(route.command)
    if _search_reports_no_results(
        record,
        stdout=proc.stdout,
        stderr=proc.stderr,
        returncode=proc.returncode,
    ):
        message = no_results_message(record.request.target, route.backend_name)
        return _result(
            record,
            exit_code=0,
            outcome="executed",
            message=message,
            execution=ExecutionResult(
                status="no_results",
                attempted=True,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                exit_code=proc.returncode,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    if proc.returncode != 0:
        if route.route_name.startswith("aur.") and aur_search_has_parseable_candidates(proc.stdout):
            output = proc.stdout.rstrip()
            message = search_results_message(record.request.target, route.backend_name, output)
            return _result(
                record,
                exit_code=0,
                outcome="executed",
                message=message,
                execution=ExecutionResult(
                    status="executed_with_backend_warning",
                    attempted=True,
                    confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                    command=route.command,
                    exit_code=proc.returncode,
                    interactive_passthrough=route.interactive_passthrough,
                    summary=message,
                ),
            )
        message = backend_failed_message(route.backend_name)
        return _result(
            record,
            exit_code=1,
            outcome="operational_error",
            message=message,
            execution=ExecutionResult(
                status="operational_error",
                attempted=True,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                exit_code=proc.returncode,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    output = proc.stdout.rstrip()
    message = search_results_message(record.request.target, route.backend_name, output)
    return _result(
        record,
        exit_code=0,
        outcome="executed",
        message=message,
        execution=ExecutionResult(
            status="executed",
            attempted=True,
            confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
            command=route.command,
            exit_code=proc.returncode,
            interactive_passthrough=route.interactive_passthrough,
            summary=message,
        ),
    )


def _execute_mutation(
    record: DecisionRecord,
    *,
    run: Runner,
    run_interactive: Runner,
    announce: Announcer | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[int, DecisionRecord, str]:
    route = record.execution_route
    assert route is not None

    pre_probe = _probe_state(record, run=run, environ=environ)
    if pre_probe.status == "probe_missing":
        return _result(
            record,
            exit_code=1,
            outcome="operational_error",
            message=pre_probe.summary,
            execution=ExecutionResult(
                status="probe_missing",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                pre_probe=pre_probe,
                interactive_passthrough=route.interactive_passthrough,
                summary=pre_probe.summary,
            ),
        )

    should_noop = (
        route.action_name == "instalar" and pre_probe.package_present is True
    ) or (
        route.action_name == "remover" and pre_probe.package_present is False
    )
    if should_noop:
        message = noop_message(
            route.action_name,
            record.request.target,
            target_label=_target_label(record),
            location_label=_location_label(record),
        )
        return _result(
            record,
            exit_code=0,
            outcome="noop",
            message=message,
            execution=ExecutionResult(
                status="noop",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                pre_probe=pre_probe,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    if record.policy is not None and record.policy.policy_outcome == "require_confirmation":
        message = confirmation_required_message(
            record.request.target,
            record.policy.software_criticality,
            record.policy.reversal_level,
            target_label=_target_label(record),
        )
        return _result(
            record,
            exit_code=1,
            outcome="blocked",
            message=message,
            execution=ExecutionResult(
                status="confirmation_required",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied,
                command=route.command,
                pre_probe=pre_probe,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    if not _required_backend_available(route.command, route.required_commands, environ=environ):
        message = backend_missing_message(route.backend_name)
        return _result(
            record,
            exit_code=1,
            outcome="operational_error",
            message=message,
            execution=ExecutionResult(
                status="backend_missing",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                pre_probe=pre_probe,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    for command, required_commands in _pre_commands_with_requirements(route):
        if not _required_backend_available(command, required_commands, environ=environ):
            message = backend_missing_message(route.backend_name)
            return _result(
                record,
                exit_code=1,
                outcome="operational_error",
                message=message,
                execution=ExecutionResult(
                    status="backend_missing",
                    attempted=False,
                    confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                    command=command,
                    pre_probe=pre_probe,
                    interactive_passthrough=False,
                    summary=message,
                ),
            )

        proc = run(command)
        if proc.returncode != 0:
            message = backend_failed_message(route.backend_name)
            return _result(
                record,
                exit_code=1,
                outcome="operational_error",
                message=message,
                execution=ExecutionResult(
                    status="operational_error",
                    attempted=True,
                    confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                    command=command,
                    exit_code=proc.returncode,
                    pre_probe=pre_probe,
                    interactive_passthrough=False,
                    summary=message,
                ),
            )

    if route.interactive_passthrough and announce is not None:
        announce(interactive_handoff_start_message(route.backend_name))

    command_runner = run_interactive if route.interactive_passthrough else run
    proc = command_runner(route.command)
    if route.interactive_passthrough and announce is not None:
        announce(interactive_handoff_return_message(route.backend_name, proc.returncode))
    if proc.returncode != 0:
        if _mutation_reports_not_found(record, proc.stdout, proc.stderr):
            message = package_not_found_message(
                route.action_name,
                record.request.target,
                route.backend_name,
                target_label=_target_label(record),
            )
            return _result(
                record,
                exit_code=1,
                outcome="operational_error",
                message=message,
                execution=ExecutionResult(
                    status="package_not_found",
                    attempted=True,
                    confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                    command=route.command,
                    exit_code=proc.returncode,
                    pre_probe=pre_probe,
                    interactive_passthrough=route.interactive_passthrough,
                    summary=message,
                ),
            )

        message = backend_failed_message(route.backend_name)
        return _result(
            record,
            exit_code=1,
            outcome="operational_error",
            message=message,
            execution=ExecutionResult(
                status="operational_error",
                attempted=True,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                exit_code=proc.returncode,
                pre_probe=pre_probe,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    post_probe = _probe_state(record, run=run, environ=environ)
    if post_probe.status == "probe_missing":
        return _result(
            record,
            exit_code=1,
            outcome="operational_error",
            message=post_probe.summary,
            execution=ExecutionResult(
                status="probe_missing",
                attempted=True,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                exit_code=proc.returncode,
                pre_probe=pre_probe,
                post_probe=post_probe,
                interactive_passthrough=route.interactive_passthrough,
                summary=post_probe.summary,
            ),
        )

    confirmed_state = (
        route.action_name == "instalar" and post_probe.package_present is True
    ) or (
        route.action_name == "remover" and post_probe.package_present is False
    )
    if not confirmed_state:
        message = state_confirmation_failed_message(route.action_name, record.request.target, route.backend_name)
        return _result(
            record,
            exit_code=1,
            outcome="operational_error",
            message=message,
            execution=ExecutionResult(
                status="state_confirmation_failed",
                attempted=True,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                command=route.command,
                exit_code=proc.returncode,
                pre_probe=pre_probe,
                post_probe=post_probe,
                interactive_passthrough=route.interactive_passthrough,
                summary=message,
            ),
        )

    message = mutation_success_message(
        route.action_name,
        record.request.target,
        target_label=_target_label(record),
    )
    return _result(
        record,
        exit_code=0,
        outcome="executed",
        message=message,
        execution=ExecutionResult(
            status="executed",
            attempted=True,
            confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
            command=route.command,
            exit_code=proc.returncode,
            pre_probe=pre_probe,
            post_probe=post_probe,
            interactive_passthrough=route.interactive_passthrough,
            summary=message,
        ),
    )


def perform_execution(
    record: DecisionRecord,
    runner: Runner | None = None,
    *,
    interactive_runner: Runner | None = None,
    announce: Announcer | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[int, DecisionRecord, str]:
    def run(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if runner is not None:
            return runner(args)
        return _run_command(args, environ=environ)

    def run_interactive(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if interactive_runner is not None:
            return interactive_runner(args)
        if runner is not None:
            return runner(args)
        return _run_interactive_command(args, environ=environ)

    if record.outcome == "out_of_scope":
        message = out_of_scope_message(record.request.reason)
        return _result(
            record,
            exit_code=1,
            outcome="blocked",
            message=message,
            execution=ExecutionResult(status="blocked", summary=message),
        )

    resolution_reason = _target_resolution_block_reason(record)
    if resolution_reason is not None:
        message = target_resolution_blocked_message(resolution_reason)
        return _result(
            record,
            exit_code=1,
            outcome="blocked",
            message=message,
            execution=ExecutionResult(
                status="blocked",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                summary=message,
            ),
        )

    if record.policy is not None and record.policy.policy_outcome == "require_confirmation":
        route = record.execution_route
        if route is not None and route.action_name in {"instalar", "remover"}:
            return _execute_mutation(
                record,
                run=run,
                run_interactive=run_interactive,
                announce=announce,
                environ=environ,
            )
        message = confirmation_required_message(
            record.request.target,
            record.policy.software_criticality,
            record.policy.reversal_level,
            target_label=_target_label(record),
        )
        return _result(
            record,
            exit_code=1,
            outcome="blocked",
            message=message,
            execution=ExecutionResult(
                status="confirmation_required",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied,
                summary=message,
            ),
        )

    if record.outcome == "blocked":
        reason = record.policy.reason if record.policy is not None else record.request.reason
        message = blocked_message(reason)
        return _result(
            record,
            exit_code=1,
            outcome="blocked",
            message=message,
            execution=ExecutionResult(
                status="blocked",
                attempted=False,
                confirmation_supplied=record.policy.confirmation_supplied if record.policy else False,
                summary=message,
            ),
        )

    if record.execution_route is None:
        message = out_of_scope_message("nao encontrei rota executavel para este pedido.")
        return _result(
            record,
            exit_code=1,
            outcome="blocked",
            message=message,
            execution=ExecutionResult(status="blocked", summary=message),
        )

    if not record.execution_route.can_execute_now:
        message = not_implemented_message(record.request.intent, record.request.domain_kind)
        return _result(
            record,
            exit_code=UNSUPPORTED_EXIT,
            outcome="planned",
            message=message,
            execution=ExecutionResult(status="not_implemented", summary=message),
        )

    if record.execution_route.action_name == "procurar":
        return _execute_search(record, run=run, environ=environ)

    return _execute_mutation(
        record,
        run=run,
        run_interactive=run_interactive,
        announce=announce,
        environ=environ,
    )


def execute_decision(
    record: DecisionRecord,
    runner: Runner | None = None,
    *,
    interactive_runner: Runner | None = None,
    environ: dict[str, str] | None = None,
) -> int:
    exit_code, _updated_record, message = perform_execution(
        record,
        runner,
        interactive_runner=interactive_runner,
        announce=print,
        environ=environ,
    )
    if message:
        print(message)
    return exit_code

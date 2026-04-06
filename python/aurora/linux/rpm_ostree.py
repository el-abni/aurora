from __future__ import annotations

from dataclasses import dataclass
import json
import os
import shutil
import subprocess

from aurora.contracts.decisions import RpmOstreeStatusObservation, TargetResolution
from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest

from .mediated_host_package import environment_package_name_is_explicit

_STATUS_COMMAND = ("rpm-ostree", "status", "--json")


@dataclass(frozen=True)
class _DeploymentState:
    requested_packages: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()
    base_removals: tuple[str, ...] = ()


def rpm_ostree_package_name_is_explicit(value: str) -> bool:
    return environment_package_name_is_explicit(value)


def _rpm_ostree_available(environ: dict[str, str] | None = None) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    return shutil.which("rpm-ostree", path=path) is not None


def _run_command(
    command: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False, env=environ)


def _tuple_from_value(value) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        if normalized and normalized not in result:
            result.append(normalized)
    return tuple(result)


def _deployment_list_value(deployment: dict[str, object], key: str) -> tuple[str, ...]:
    for candidate in (key, key.replace("-", "_")):
        if candidate in deployment:
            return _tuple_from_value(deployment.get(candidate))
    return ()


def _deployment_state(deployment: dict[str, object] | None) -> _DeploymentState:
    if deployment is None:
        return _DeploymentState()
    return _DeploymentState(
        requested_packages=_deployment_list_value(deployment, "requested-packages"),
        packages=_deployment_list_value(deployment, "packages"),
        base_removals=_deployment_list_value(deployment, "base-removals"),
    )


def _status_observation_from_payload(
    payload: dict[str, object],
    *,
    diagnostic_exit_code: int | None,
    diagnostic_stdout: str,
    diagnostic_stderr: str,
) -> RpmOstreeStatusObservation:
    deployments = payload.get("deployments")
    deployment_list = deployments if isinstance(deployments, list) else []
    booted = next(
        (
            deployment
            for deployment in deployment_list
            if isinstance(deployment, dict) and bool(deployment.get("booted"))
        ),
        None,
    )
    default = deployment_list[0] if deployment_list and isinstance(deployment_list[0], dict) else None
    pending = default if default is not None and not bool(default.get("booted")) else None
    booted_state = _deployment_state(booted if isinstance(booted, dict) else None)
    pending_state = _deployment_state(pending if isinstance(pending, dict) else None)

    return RpmOstreeStatusObservation(
        observed=True,
        status="observed",
        source="rpm_ostree_status_json",
        reason="o estado do host rpm-ostree foi observado via 'rpm-ostree status --json'.",
        transaction_active=bool(payload.get("transaction")),
        booted_requested_packages=booted_state.requested_packages,
        booted_packages=booted_state.packages,
        booted_base_removals=booted_state.base_removals,
        pending_deployment=pending is not None,
        pending_requested_packages=pending_state.requested_packages,
        pending_packages=pending_state.packages,
        pending_base_removals=pending_state.base_removals,
        diagnostic_command=_STATUS_COMMAND,
        diagnostic_exit_code=diagnostic_exit_code,
        diagnostic_stdout=diagnostic_stdout,
        diagnostic_stderr=diagnostic_stderr,
    )


def observe_rpm_ostree_status(
    *,
    environ: dict[str, str] | None = None,
    runner=None,
) -> RpmOstreeStatusObservation:
    if runner is None and not _rpm_ostree_available(environ):
        return RpmOstreeStatusObservation(
            observed=False,
            status="missing",
            source="host_observation",
            reason=(
                "o comando 'rpm-ostree' nao foi observado neste host. "
                "esta release nao inventa superficie imutavel quando o backend nao existe."
            ),
            diagnostic_command=_STATUS_COMMAND,
        )

    proc = runner(_STATUS_COMMAND) if runner is not None else _run_command(_STATUS_COMMAND, environ=environ)
    if proc.returncode != 0:
        return RpmOstreeStatusObservation(
            observed=False,
            status="error",
            source="rpm_ostree_status_json",
            reason=(
                "nao consegui observar o estado do host imutavel via 'rpm-ostree status --json'. "
                "esta release exige esse probe para planejar mutacoes auditaveis."
            ),
            diagnostic_command=_STATUS_COMMAND,
            diagnostic_exit_code=proc.returncode,
            diagnostic_stdout=proc.stdout,
            diagnostic_stderr=proc.stderr,
        )

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return RpmOstreeStatusObservation(
            observed=False,
            status="parse_error",
            source="rpm_ostree_status_json",
            reason=(
                "o retorno de 'rpm-ostree status --json' nao foi parseavel. "
                "esta release nao segue com mutacao sem status estruturado do deployment."
            ),
            diagnostic_command=_STATUS_COMMAND,
            diagnostic_exit_code=proc.returncode,
            diagnostic_stdout=proc.stdout,
            diagnostic_stderr=proc.stderr,
        )

    if not isinstance(payload, dict):
        return RpmOstreeStatusObservation(
            observed=False,
            status="parse_error",
            source="rpm_ostree_status_json",
            reason=(
                "o payload de 'rpm-ostree status --json' veio em formato inesperado. "
                "esta release nao segue com mutacao sem status estruturado do deployment."
            ),
            diagnostic_command=_STATUS_COMMAND,
            diagnostic_exit_code=proc.returncode,
            diagnostic_stdout=proc.stdout,
            diagnostic_stderr=proc.stderr,
        )

    return _status_observation_from_payload(
        payload,
        diagnostic_exit_code=proc.returncode,
        diagnostic_stdout=proc.stdout,
        diagnostic_stderr=proc.stderr,
    )


def rpm_ostree_target_present(target: str, status: RpmOstreeStatusObservation) -> bool:
    relevant_requested = (
        status.pending_requested_packages
        if status.pending_deployment
        else status.booted_requested_packages
    )
    relevant_packages = status.pending_packages if status.pending_deployment else status.booted_packages
    return target in relevant_requested or target in relevant_packages


def resolve_rpm_ostree_target(
    request: SemanticRequest,
    _profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    del environ
    if request.execution_surface != "rpm_ostree":
        return None
    if request.domain_kind != "host_package" or request.intent not in {"instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    if rpm_ostree_package_name_is_explicit(target):
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_package_name",
            canonicalized=False,
            reason=(
                "rpm-ostree.instalar e rpm-ostree.remover exigem nome de pacote explicito nesta release; "
                "o alvo fornecido foi usado diretamente."
            ),
        )

    return TargetResolution(
        original_target=target,
        status="unresolved",
        source="rpm_ostree_user_input",
        reason=(
            "rpm-ostree.instalar e rpm-ostree.remover exigem o nome real do pacote nesta release. "
            "rpm-ostree.procurar ainda nao foi aberta."
        ),
    )


def rpm_ostree_target_resolution_blocks(resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    return resolution.status in {"ambiguous", "not_found", "unresolved"}


def build_rpm_ostree_candidate(
    request: SemanticRequest,
    profile: HostProfile,
    *,
    target: str | None = None,
    status_observation: RpmOstreeStatusObservation | None = None,
) -> ExecutionRoute | None:
    if request.execution_surface != "rpm_ostree":
        return None
    if request.domain_kind != "host_package" or request.requested_source:
        return None

    resolved_target = target.strip() if target is not None and target.strip() else request.target.strip()
    notes = (
        "rpm-ostree entra como superficie explicita de host imutavel nesta release.",
        "a semantica desta rota nao e host_package mutavel comum: a mudanca gera deployment pendente no host.",
        (
            "rpm-ostree status --json foi observado antes do planejamento."
            if status_observation is not None and status_observation.observed
            else "rpm-ostree status --json ainda nao foi observado."
        ),
        "a Aurora nao abre apply-live, override remove, reboot automatico nem manutencao ampla do host nesta release.",
        "a fronteira permanece explicita: flatpak atua no escopo do usuario, toolbox e distrobox atuam em ambientes mediados, rpm-ostree atua no host imutavel.",
    )

    if request.intent == "procurar":
        return ExecutionRoute(
            route_name="rpm_ostree.procurar",
            action_name="procurar",
            backend_name="rpm-ostree",
            required_commands=("rpm-ostree",),
            implemented=False,
            notes=notes + ("rpm-ostree.procurar ainda nao foi aberta nesta release.",),
            execution_surface="rpm_ostree",
        )

    if request.intent not in {"instalar", "remover"} or not resolved_target:
        return None

    subcommand = "install" if request.intent == "instalar" else "uninstall"
    return ExecutionRoute(
        route_name=f"rpm_ostree.{request.intent}",
        action_name=request.intent,
        backend_name="rpm-ostree",
        command=("sudo", "rpm-ostree", subcommand, resolved_target),
        required_commands=("sudo", "rpm-ostree"),
        state_probe_command=_STATUS_COMMAND,
        state_probe_required_commands=("rpm-ostree",),
        implemented=True,
        requires_privilege_escalation=True,
        notes=notes
        + (
            "a confirmacao de sucesso observa o deployment default/pending via rpm-ostree status --json.",
            "uma mutacao bem-sucedida pode exigir reboot para aplicar o novo deployment.",
        ),
        execution_surface="rpm_ostree",
    )


def rpm_ostree_mutation_reports_no_matching_package(stdout: str, stderr: str) -> bool:
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if not combined_output:
        return False
    markers = (
        "packages not found",
        "package not found",
        "not currently requested",
        "not installed",
    )
    return any(marker in combined_output for marker in markers)

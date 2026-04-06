from __future__ import annotations

from dataclasses import dataclass
import os
import re
import shutil
import subprocess

from aurora.contracts.decisions import EnvironmentResolution, TargetResolution
from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest

from .mediated_host_package import (
    MediatedProfileProbe,
    build_mediated_candidate,
    command_probe_script,
    environment_name_is_explicit,
    environment_package_name_is_explicit,
    mediated_target_resolution_blocks,
    observe_environment_profile,
    resolve_mediated_target,
)

_TOOLBOX_LIST_COMMAND = ("toolbox", "list", "--containers")
_TOOLBOX_COMMAND_PROBE_SCRIPT = command_probe_script()
_HEX_ID_RE = re.compile(r"^[0-9a-f]{6,}$")


@dataclass(frozen=True)
class ToolboxCapabilityProbe:
    observed: bool
    observed_environments: tuple[str, ...] = ()
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = _TOOLBOX_LIST_COMMAND
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


ToolboxProfileProbe = MediatedProfileProbe


def toolbox_name_is_explicit(value: str) -> bool:
    return environment_name_is_explicit(value)


def toolbox_package_name_is_explicit(value: str) -> bool:
    return environment_package_name_is_explicit(value)


def _toolbox_available(environ: dict[str, str] | None = None) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    return shutil.which("toolbox", path=path) is not None


def _run_command(
    command: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False, env=environ)


def _toolbox_run_prefix(environment_name: str) -> tuple[str, ...]:
    return ("toolbox", "run", "--container", environment_name, "--")


def _toolbox_os_release_command(environment_name: str) -> tuple[str, ...]:
    return _toolbox_run_prefix(environment_name) + ("cat", "/etc/os-release")


def _toolbox_command_probe_command(environment_name: str) -> tuple[str, ...]:
    return _toolbox_run_prefix(environment_name) + ("sh", "-c", _TOOLBOX_COMMAND_PROBE_SCRIPT)


def _parse_toolbox_names(output: str) -> tuple[str, ...]:
    names: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = " ".join(line.lower().split())
        if normalized.startswith("container id ") or normalized.startswith("container name "):
            continue
        parts = [part.strip() for part in re.split(r"\s{2,}", line) if part.strip()]
        candidate = ""
        if len(parts) >= 2 and _HEX_ID_RE.fullmatch(parts[0].lower()) is not None:
            candidate = parts[1]
        elif parts:
            candidate = parts[0]
        if candidate and toolbox_name_is_explicit(candidate) and candidate not in names:
            names.append(candidate)
    return tuple(names)


def observe_toolbox_capability(environ: dict[str, str] | None = None) -> ToolboxCapabilityProbe:
    if not _toolbox_available(environ):
        return ToolboxCapabilityProbe(
            observed=False,
            gap="toolbox_command_not_observed",
            reason=(
                "O comando 'toolbox' não foi observado neste host. "
                "Esta release não cria ambientes automaticamente nem usa toolbox como fallback implícito."
            ),
        )

    proc = _run_command(_TOOLBOX_LIST_COMMAND, environ=environ)
    if proc.returncode != 0:
        return ToolboxCapabilityProbe(
            observed=False,
            gap="toolbox_list_not_observed",
            reason=(
                "Não consegui observar as toolboxes existentes via 'toolbox list --containers'. "
                "Esta release exige observação explícita do ambiente mediado."
            ),
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    return ToolboxCapabilityProbe(
        observed=True,
        observed_environments=_parse_toolbox_names(proc.stdout),
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def observe_toolbox_environments(environ: dict[str, str] | None = None) -> tuple[str, ...]:
    capability = observe_toolbox_capability(environ=environ)
    if not capability.observed:
        return ()
    return capability.observed_environments


def resolve_toolbox_environment(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> EnvironmentResolution | None:
    if request.execution_surface != "toolbox":
        return None

    observed_environments = profile.observed_toolbox_environments if profile is not None else ()
    environment_name = request.environment_target.strip()
    if not environment_name:
        return EnvironmentResolution(
            execution_surface="toolbox",
            observed_environments=observed_environments,
            status="missing",
            source="user_input",
            reason=(
                "Toolbox explícita nesta rodada exige o nome do ambiente. "
                "Não existe default implícito, descoberta mágica nem autosseleção."
            ),
        )

    if not toolbox_name_is_explicit(environment_name):
        return EnvironmentResolution(
            execution_surface="toolbox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="unresolved",
            source="user_input",
            reason=(
                "O nome da toolbox precisa ser um identificador simples e conservador nesta rodada, "
                "sem parsing amplo de argumentos."
            ),
        )

    if profile is None:
        return EnvironmentResolution(
            execution_surface="toolbox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="unresolved",
            source="host_profile",
            reason="O host profile não está disponível para abrir a superfície toolbox.",
        )

    if "toolbox" not in profile.observed_environment_tools:
        return EnvironmentResolution(
            execution_surface="toolbox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="unresolved",
            source="host_observation",
            reason=(
                "O comando 'toolbox' não foi observado neste host. "
                "Esta release não cria ambientes automaticamente nem usa toolbox como fallback implícito."
            ),
        )

    probe_command = _toolbox_os_release_command(environment_name)
    proc = _run_command(probe_command, environ=environ)
    if proc.returncode != 0:
        return EnvironmentResolution(
            execution_surface="toolbox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="not_found",
            source="toolbox_run_probe",
            reason=(
                f"A toolbox explícita '{environment_name}' não foi resolvida por probe controlado. "
                "Esta release não cria ambiente automaticamente nem assume nomes aproximados."
            ),
            diagnostic_command=probe_command,
            diagnostic_exit_code=proc.returncode,
            diagnostic_stdout=proc.stdout,
            diagnostic_stderr=proc.stderr,
        )

    return EnvironmentResolution(
        execution_surface="toolbox",
        original_environment=environment_name,
        resolved_environment=environment_name,
        observed_environments=observed_environments,
        status="resolved",
        source="toolbox_run_probe",
        reason=(
            f"A toolbox explícita '{environment_name}' foi observada por probe controlado "
            "antes do planejamento da rota."
        ),
        diagnostic_command=probe_command,
        diagnostic_exit_code=proc.returncode,
        diagnostic_stdout=proc.stdout,
        diagnostic_stderr=proc.stderr,
    )


def observe_toolbox_profile(
    environment_name: str,
    *,
    environ: dict[str, str] | None = None,
) -> ToolboxProfileProbe:
    return observe_environment_profile(
        "toolbox",
        environment_name,
        run_command=_run_command,
        os_release_command=_toolbox_os_release_command(environment_name),
        command_probe_command=_toolbox_command_probe_command(environment_name),
        environ=environ,
    )


def resolve_toolbox_target(
    request: SemanticRequest,
    _profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    del environ
    return resolve_mediated_target(request, "toolbox")


def toolbox_target_resolution_blocks(resolution: TargetResolution | None) -> bool:
    return mediated_target_resolution_blocks(resolution)


def build_toolbox_candidate(
    request: SemanticRequest,
    host_profile: HostProfile,
    *,
    toolbox_profile: HostProfile | None,
    environment_resolution: EnvironmentResolution | None,
    target: str | None = None,
) -> ExecutionRoute | None:
    notes = (
        "Toolbox entra como superfície operacional mediada explícita nesta rodada.",
        "Toolbox e distrobox compartilham apenas o miolo de pacote distro-managed dentro do ambiente; a observação e a semântica de superfície continuam distintas.",
        (
            f"Ambiente toolbox selecionado explicitamente: {environment_resolution.resolved_environment}."
            if environment_resolution is not None and environment_resolution.resolved_environment
            else "Ambiente toolbox ainda não resolvido."
        ),
        "A fronteira host vs toolbox permanece visível: a mutação acontece dentro do ambiente mediado, não no host.",
        "Esta frente não cria toolbox automaticamente, não administra lifecycle amplo e não vira fallback implícito do host.",
        "Esta frente cobre apenas pacote do host dentro da toolbox, sem misturar AUR, COPR, PPA ou flatpak.",
    )
    del host_profile
    return build_mediated_candidate(
        request,
        "toolbox",
        environment_profile=toolbox_profile,
        environment_resolution=environment_resolution,
        run_prefix=_toolbox_run_prefix,
        target=target,
        notes=notes,
    )

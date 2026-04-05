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

_DISTROBOX_LIST_COMMAND = ("distrobox", "list", "--no-color")
_DISTROBOX_COMMAND_PROBE_SCRIPT = command_probe_script()
_DISTROBOX_HEADER_TOKENS = {"container name", "name", "id", "status", "image"}
_HEX_ID_RE = re.compile(r"^[0-9a-f]{6,}$")


@dataclass(frozen=True)
class DistroboxCapabilityProbe:
    observed: bool
    observed_environments: tuple[str, ...] = ()
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = _DISTROBOX_LIST_COMMAND
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


DistroboxProfileProbe = MediatedProfileProbe


def distrobox_name_is_explicit(value: str) -> bool:
    return environment_name_is_explicit(value)


def distrobox_package_name_is_explicit(value: str) -> bool:
    return environment_package_name_is_explicit(value)


def _distrobox_available(environ: dict[str, str] | None = None) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    return shutil.which("distrobox", path=path) is not None


def _run_command(
    command: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False, env=environ)


def _distrobox_run_prefix(environment_name: str) -> tuple[str, ...]:
    return ("distrobox", "enter", "--name", environment_name, "--no-tty", "--")


def _distrobox_os_release_command(environment_name: str) -> tuple[str, ...]:
    return _distrobox_run_prefix(environment_name) + ("cat", "/etc/os-release")


def _distrobox_command_probe_command(environment_name: str) -> tuple[str, ...]:
    return _distrobox_run_prefix(environment_name) + ("sh", "-c", _DISTROBOX_COMMAND_PROBE_SCRIPT)


def _parse_distrobox_names(output: str) -> tuple[str, ...]:
    names: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = " ".join(line.lower().replace("|", " ").split())
        if normalized in _DISTROBOX_HEADER_TOKENS:
            continue
        if normalized.startswith("id ") or normalized.startswith("name ") or normalized.startswith("container name "):
            continue

        parts = [
            part.strip()
            for part in re.split(r"\s{2,}|\t+|\s*\|\s*", line)
            if part.strip()
        ]
        candidates: list[str] = []
        if len(parts) >= 2 and _HEX_ID_RE.fullmatch(parts[0].lower()) is not None:
            candidates.append(parts[1])
        if parts:
            candidates.append(parts[0])

        for candidate in candidates:
            if candidate.lower() in {"id", "name", "status", "image"}:
                continue
            if distrobox_name_is_explicit(candidate) and candidate not in names:
                names.append(candidate)
                break
    return tuple(names)


def observe_distrobox_capability(environ: dict[str, str] | None = None) -> DistroboxCapabilityProbe:
    if not _distrobox_available(environ):
        return DistroboxCapabilityProbe(
            observed=False,
            gap="distrobox_command_not_observed",
            reason=(
                "o comando 'distrobox' nao foi observado neste host. "
                "esta release nao cria ambientes automaticamente nem usa distrobox como fallback implicito."
            ),
        )

    proc = _run_command(_DISTROBOX_LIST_COMMAND, environ=environ)
    if proc.returncode != 0:
        return DistroboxCapabilityProbe(
            observed=False,
            gap="distrobox_list_not_observed",
            reason=(
                "nao consegui observar as distroboxes existentes via 'distrobox list --no-color'. "
                "esta release exige observacao explicita do ambiente mediado."
            ),
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    return DistroboxCapabilityProbe(
        observed=True,
        observed_environments=_parse_distrobox_names(proc.stdout),
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def observe_distrobox_environments(environ: dict[str, str] | None = None) -> tuple[str, ...]:
    capability = observe_distrobox_capability(environ=environ)
    if not capability.observed:
        return ()
    return capability.observed_environments


def resolve_distrobox_environment(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> EnvironmentResolution | None:
    if request.execution_surface != "distrobox":
        return None

    observed_environments = profile.observed_distrobox_environments if profile is not None else ()
    environment_name = request.environment_target.strip()
    if not environment_name:
        return EnvironmentResolution(
            execution_surface="distrobox",
            observed_environments=observed_environments,
            status="missing",
            source="user_input",
            reason=(
                "distrobox explicita nesta rodada exige o nome do ambiente. "
                "nao existe default implicito, descoberta magica nem autoselecao."
            ),
        )

    if not distrobox_name_is_explicit(environment_name):
        return EnvironmentResolution(
            execution_surface="distrobox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="unresolved",
            source="user_input",
            reason=(
                "o nome da distrobox precisa ser um identificador simples e conservador nesta rodada, "
                "sem parsing amplo de argumentos."
            ),
        )

    if profile is None:
        return EnvironmentResolution(
            execution_surface="distrobox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="unresolved",
            source="host_profile",
            reason="o host profile nao esta disponivel para abrir a superficie distrobox.",
        )

    if "distrobox" not in profile.observed_environment_tools:
        return EnvironmentResolution(
            execution_surface="distrobox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="unresolved",
            source="host_observation",
            reason=(
                "o comando 'distrobox' nao foi observado neste host. "
                "esta release nao cria ambientes automaticamente nem usa distrobox como fallback implicito."
            ),
        )

    probe_command = _distrobox_os_release_command(environment_name)
    proc = _run_command(probe_command, environ=environ)
    if proc.returncode != 0:
        return EnvironmentResolution(
            execution_surface="distrobox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="not_found",
            source="distrobox_enter_probe",
            reason=(
                f"a distrobox explicita '{environment_name}' nao foi resolvida por probe controlado. "
                "esta release nao cria ambiente automaticamente nem assume nomes aproximados."
            ),
            diagnostic_command=probe_command,
            diagnostic_exit_code=proc.returncode,
            diagnostic_stdout=proc.stdout,
            diagnostic_stderr=proc.stderr,
        )

    return EnvironmentResolution(
        execution_surface="distrobox",
        original_environment=environment_name,
        resolved_environment=environment_name,
        observed_environments=observed_environments,
        status="resolved",
        source="distrobox_enter_probe",
        reason=(
            f"a distrobox explicita '{environment_name}' foi observada por probe controlado "
            "antes do planejamento da rota."
        ),
        diagnostic_command=probe_command,
        diagnostic_exit_code=proc.returncode,
        diagnostic_stdout=proc.stdout,
        diagnostic_stderr=proc.stderr,
    )


def observe_distrobox_profile(
    environment_name: str,
    *,
    environ: dict[str, str] | None = None,
) -> DistroboxProfileProbe:
    return observe_environment_profile(
        "distrobox",
        environment_name,
        run_command=_run_command,
        os_release_command=_distrobox_os_release_command(environment_name),
        command_probe_command=_distrobox_command_probe_command(environment_name),
        environ=environ,
    )


def resolve_distrobox_target(
    request: SemanticRequest,
    _profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    del environ
    return resolve_mediated_target(request, "distrobox")


def distrobox_target_resolution_blocks(resolution: TargetResolution | None) -> bool:
    return mediated_target_resolution_blocks(resolution)


def build_distrobox_candidate(
    request: SemanticRequest,
    host_profile: HostProfile,
    *,
    distrobox_profile: HostProfile | None,
    environment_resolution: EnvironmentResolution | None,
    target: str | None = None,
) -> ExecutionRoute | None:
    notes = (
        "distrobox entra como superficie operacional mediada explicita nesta rodada.",
        "toolbox e distrobox compartilham apenas o miolo de pacote distro-managed dentro do ambiente; a observacao e a semantica de superficie continuam distintas.",
        (
            f"ambiente distrobox selecionado explicitamente: {environment_resolution.resolved_environment}."
            if environment_resolution is not None and environment_resolution.resolved_environment
            else "ambiente distrobox ainda nao resolvido."
        ),
        "a fronteira host vs distrobox permanece visivel: a mutacao acontece dentro do ambiente mediado, nao no host.",
        "esta frente nao cria distrobox automaticamente, nao administra lifecycle amplo e nao vira fallback implicito do host.",
        "esta frente cobre apenas pacote do host dentro da distrobox, sem misturar AUR, COPR, PPA ou flatpak.",
    )
    del host_profile
    return build_mediated_candidate(
        request,
        "distrobox",
        environment_profile=distrobox_profile,
        environment_resolution=environment_resolution,
        run_prefix=_distrobox_run_prefix,
        target=target,
        notes=notes,
    )

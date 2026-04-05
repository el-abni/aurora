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

from .profile_facts import HOST_PACKAGE_BACKENDS, detect_linux_family, support_tier_for_profile
from .probes import parse_os_release_text, split_like

_TOOLBOX_LIST_COMMAND = ("toolbox", "list", "--containers")
_TOOLBOX_PROFILE_COMMAND_NAMES = (*HOST_PACKAGE_BACKENDS, "sudo")
_TOOLBOX_COMMAND_PROBE_SCRIPT = (
    "for name in pacman apt-cache apt-get dnf zypper sudo; do "
    "command -v \"$name\" >/dev/null 2>&1 && printf '%s\\n' \"$name\"; "
    "done; exit 0"
)
_TOOLBOX_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_TOOLBOX_PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
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


@dataclass(frozen=True)
class ToolboxProfileProbe:
    observed: bool
    profile: HostProfile | None = None
    observed_commands: tuple[str, ...] = ()
    sudo_observed: bool = False
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = ()
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


def toolbox_name_is_explicit(value: str) -> bool:
    return _TOOLBOX_NAME_RE.fullmatch(value.strip()) is not None


def toolbox_package_name_is_explicit(value: str) -> bool:
    return _TOOLBOX_PACKAGE_RE.fullmatch(value.strip()) is not None


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
                "o comando 'toolbox' nao foi observado neste host. "
                "esta release nao cria ambientes automaticamente nem usa toolbox como fallback implicito."
            ),
        )

    proc = _run_command(_TOOLBOX_LIST_COMMAND, environ=environ)
    if proc.returncode != 0:
        return ToolboxCapabilityProbe(
            observed=False,
            gap="toolbox_list_not_observed",
            reason=(
                "nao consegui observar as toolboxes existentes via 'toolbox list --containers'. "
                "esta release exige observacao explicita do ambiente mediado."
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
                "toolbox explicita nesta rodada exige o nome do ambiente. "
                "nao existe default implicito, descoberta magica nem autoselecao."
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
                "o nome da toolbox precisa ser um identificador simples e conservador nesta rodada, "
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
            reason="o host profile nao esta disponivel para abrir a superficie toolbox.",
        )

    if "toolbox" not in profile.observed_environment_tools:
        return EnvironmentResolution(
            execution_surface="toolbox",
            original_environment=environment_name,
            observed_environments=observed_environments,
            status="unresolved",
            source="host_observation",
            reason=(
                "o comando 'toolbox' nao foi observado neste host. "
                "esta release nao cria ambientes automaticamente nem usa toolbox como fallback implicito."
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
                f"a toolbox explicita '{environment_name}' nao foi resolvida por probe controlado. "
                "esta release nao cria ambiente automaticamente nem assume nomes aproximados."
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
            f"a toolbox explicita '{environment_name}' foi observada por probe controlado "
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
    if not environment_name.strip():
        return ToolboxProfileProbe(
            observed=False,
            gap="toolbox_environment_missing",
            reason="faltou o nome do ambiente toolbox para observar o backend interno.",
        )

    os_release_command = _toolbox_os_release_command(environment_name)
    os_release_proc = _run_command(os_release_command, environ=environ)
    if os_release_proc.returncode != 0:
        return ToolboxProfileProbe(
            observed=False,
            gap="toolbox_profile_not_observed",
            reason=(
                f"nao consegui ler /etc/os-release dentro da toolbox '{environment_name}' "
                "para determinar a familia Linux mediada."
            ),
            command=os_release_command,
            exit_code=os_release_proc.returncode,
            stdout=os_release_proc.stdout,
            stderr=os_release_proc.stderr,
        )

    os_release = parse_os_release_text(os_release_proc.stdout)
    distro_id = os_release.get("ID", "").strip().lower()
    distro_like = split_like(os_release.get("ID_LIKE", ""))
    variant_id = os_release.get("VARIANT_ID", "").strip().lower()
    linux_family = detect_linux_family(distro_id, distro_like)

    probe_command = _toolbox_command_probe_command(environment_name)
    commands_proc = _run_command(probe_command, environ=environ)
    if commands_proc.returncode != 0:
        return ToolboxProfileProbe(
            observed=False,
            gap="toolbox_commands_not_observed",
            reason=(
                f"nao consegui observar os comandos basicos dentro da toolbox '{environment_name}' "
                "para montar uma rota mediada auditavel."
            ),
            command=probe_command,
            exit_code=commands_proc.returncode,
            stdout=commands_proc.stdout,
            stderr=commands_proc.stderr,
        )

    observed_commands = tuple(
        command
        for command in commands_proc.stdout.splitlines()
        if command.strip() in _TOOLBOX_PROFILE_COMMAND_NAMES
    )
    package_backends = tuple(
        command for command in observed_commands if command in HOST_PACKAGE_BACKENDS
    )
    profile = HostProfile(
        linux_family=linux_family,
        distro_id=distro_id,
        distro_like=distro_like,
        variant_id=variant_id,
        mutability="mutable",
        package_backends=package_backends,
        observed_package_tools=(),
        observed_third_party_package_tools=(),
        support_tier=support_tier_for_profile(linux_family, "mutable"),
    )
    return ToolboxProfileProbe(
        observed=True,
        profile=profile,
        observed_commands=observed_commands,
        sudo_observed="sudo" in observed_commands,
        command=probe_command,
        exit_code=commands_proc.returncode,
        stdout=commands_proc.stdout,
        stderr=commands_proc.stderr,
    )


def resolve_toolbox_target(
    request: SemanticRequest,
    _profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    del environ

    if request.execution_surface != "toolbox":
        return None
    if request.domain_kind != "host_package" or request.intent not in {"instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    if toolbox_package_name_is_explicit(target):
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_package_name",
            canonicalized=False,
            reason=(
                "a mutacao dentro da toolbox recebeu um nome de pacote explicito e conservador, "
                "entao o alvo foi usado diretamente."
            ),
        )

    return TargetResolution(
        original_target=target,
        status="unresolved",
        source="toolbox_user_input",
        reason=(
            "toolbox.instalar e toolbox.remover exigem o nome real do pacote nesta release. "
            "Use toolbox.procurar para descobrir o nome exato antes da mutacao."
        ),
    )


def toolbox_target_resolution_blocks(resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    return resolution.status in {"ambiguous", "not_found", "unresolved"}


def _search_command(target: str, profile: HostProfile) -> tuple[str, ...]:
    if profile.linux_family == "arch":
        return ("pacman", "-Ss", "--", target)
    if profile.linux_family == "debian":
        return ("apt-cache", "search", target)
    if profile.linux_family == "opensuse":
        return ("zypper", "search", "--", target)
    return ("dnf", "search", target)


def _mutation_command(intent: str, target: str, profile: HostProfile) -> tuple[str, ...]:
    if profile.linux_family == "arch":
        if intent == "instalar":
            return ("sudo", "pacman", "-S", "--needed", "--", target)
        return ("sudo", "pacman", "-Rns", "--", target)
    if profile.linux_family == "debian":
        if intent == "instalar":
            return ("sudo", "apt-get", "install", "-y", target)
        return ("sudo", "apt-get", "remove", "-y", target)
    if profile.linux_family == "opensuse":
        if intent == "instalar":
            return ("sudo", "zypper", "--non-interactive", "install", "--", target)
        return ("sudo", "zypper", "--non-interactive", "remove", "--", target)
    if intent == "instalar":
        return ("sudo", "dnf", "install", "-y", target)
    return ("sudo", "dnf", "remove", "-y", target)


def _state_probe_command(target: str, profile: HostProfile) -> tuple[str, ...]:
    if profile.linux_family == "arch":
        return ("pacman", "-Q", "--", target)
    if profile.linux_family == "debian":
        return ("dpkg", "-s", target)
    return ("rpm", "-q", target)


def _backend_label(intent: str, profile: HostProfile) -> str:
    if profile.linux_family == "arch":
        inner = "pacman" if intent == "procurar" else "sudo + pacman"
    elif profile.linux_family == "debian":
        inner = "apt-cache" if intent == "procurar" else "sudo + apt-get"
    elif profile.linux_family == "opensuse":
        inner = "zypper" if intent == "procurar" else "sudo + zypper"
    else:
        inner = "dnf" if intent == "procurar" else "sudo + dnf"
    return f"toolbox + {inner}"


def build_toolbox_candidate(
    request: SemanticRequest,
    _host_profile: HostProfile,
    *,
    toolbox_profile: HostProfile | None,
    environment_resolution: EnvironmentResolution | None,
    target: str | None = None,
) -> ExecutionRoute | None:
    if request.execution_surface != "toolbox":
        return None
    if request.domain_kind != "host_package" or request.requested_source:
        return None
    if toolbox_profile is None or environment_resolution is None:
        return None
    if environment_resolution.status != "resolved" or not environment_resolution.resolved_environment:
        return None

    environment_name = environment_resolution.resolved_environment
    resolved_target = target.strip() if target is not None and target.strip() else request.target.strip()
    if not resolved_target:
        return None

    prefix = _toolbox_run_prefix(environment_name)
    notes = (
        "toolbox entra como superficie operacional mediada explicita nesta rodada.",
        f"ambiente toolbox selecionado explicitamente: {environment_name}.",
        "a fronteira host vs toolbox permanece visivel: a mutacao acontece dentro do ambiente mediado, nao no host.",
        "esta frente nao cria toolbox automaticamente, nao administra lifecycle amplo e nao vira fallback implicito do host.",
        "esta frente cobre apenas pacote do host dentro da toolbox, sem misturar AUR, COPR, PPA ou flatpak.",
    )

    if request.intent == "procurar":
        return ExecutionRoute(
            route_name="toolbox.procurar",
            action_name="procurar",
            backend_name=_backend_label("procurar", toolbox_profile),
            command=prefix + _search_command(resolved_target, toolbox_profile),
            required_commands=("toolbox",),
            implemented=True,
            notes=notes,
            execution_surface="toolbox",
            environment_target=environment_name,
        )

    return ExecutionRoute(
        route_name=f"toolbox.{request.intent}",
        action_name=request.intent,
        backend_name=_backend_label(request.intent, toolbox_profile),
        command=prefix + _mutation_command(request.intent, resolved_target, toolbox_profile),
        required_commands=("toolbox",),
        state_probe_command=prefix + _state_probe_command(resolved_target, toolbox_profile),
        state_probe_required_commands=("toolbox",),
        implemented=True,
        requires_privilege_escalation=True,
        notes=notes + ("mutacao mediada usa probe antes e depois da execucao dentro da toolbox.",),
        execution_surface="toolbox",
        environment_target=environment_name,
    )

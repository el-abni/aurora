from __future__ import annotations

from dataclasses import dataclass
import re

from aurora.contracts.decisions import EnvironmentResolution, TargetResolution
from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest

from .profile_facts import HOST_PACKAGE_BACKENDS, detect_linux_family, support_tier_for_profile
from .probes import parse_os_release_text, split_like

_ENVIRONMENT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_PROFILE_COMMAND_NAMES = (*HOST_PACKAGE_BACKENDS, "sudo")
_COMMAND_PROBE_SCRIPT = (
    "for name in pacman apt-cache apt-get dnf zypper sudo; do "
    "command -v \"$name\" >/dev/null 2>&1 && printf '%s\\n' \"$name\"; "
    "done; exit 0"
)


@dataclass(frozen=True)
class MediatedProfileProbe:
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


def environment_name_is_explicit(value: str) -> bool:
    return _ENVIRONMENT_NAME_RE.fullmatch(value.strip()) is not None


def environment_package_name_is_explicit(value: str) -> bool:
    return _PACKAGE_NAME_RE.fullmatch(value.strip()) is not None


def command_probe_script() -> str:
    return _COMMAND_PROBE_SCRIPT


def observe_environment_profile(
    execution_surface: str,
    environment_name: str,
    *,
    run_command,
    os_release_command: tuple[str, ...],
    command_probe_command: tuple[str, ...],
    environ: dict[str, str] | None = None,
) -> MediatedProfileProbe:
    if not environment_name.strip():
        return MediatedProfileProbe(
            observed=False,
            gap=f"{execution_surface}_environment_missing",
            reason=(
                f"faltou o nome do ambiente {execution_surface} para observar o backend interno."
            ),
        )

    os_release_proc = run_command(os_release_command, environ=environ)
    if os_release_proc.returncode != 0:
        return MediatedProfileProbe(
            observed=False,
            gap=f"{execution_surface}_profile_not_observed",
            reason=(
                f"nao consegui ler /etc/os-release dentro da {execution_surface} '{environment_name}' "
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

    commands_proc = run_command(command_probe_command, environ=environ)
    if commands_proc.returncode != 0:
        return MediatedProfileProbe(
            observed=False,
            gap=f"{execution_surface}_commands_not_observed",
            reason=(
                f"nao consegui observar os comandos basicos dentro da {execution_surface} '{environment_name}' "
                "para montar uma rota mediada auditavel."
            ),
            command=command_probe_command,
            exit_code=commands_proc.returncode,
            stdout=commands_proc.stdout,
            stderr=commands_proc.stderr,
        )

    observed_commands = tuple(
        command
        for command in commands_proc.stdout.splitlines()
        if command.strip() in _PROFILE_COMMAND_NAMES
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
    return MediatedProfileProbe(
        observed=True,
        profile=profile,
        observed_commands=observed_commands,
        sudo_observed="sudo" in observed_commands,
        command=command_probe_command,
        exit_code=commands_proc.returncode,
        stdout=commands_proc.stdout,
        stderr=commands_proc.stderr,
    )


def resolve_mediated_target(
    request: SemanticRequest,
    execution_surface: str,
) -> TargetResolution | None:
    if request.execution_surface != execution_surface:
        return None
    if request.domain_kind != "host_package" or request.intent not in {"instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    if environment_package_name_is_explicit(target):
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_package_name",
            canonicalized=False,
            reason=(
                f"a mutacao dentro da {execution_surface} recebeu um nome de pacote explicito e conservador, "
                "entao o alvo foi usado diretamente."
            ),
        )

    return TargetResolution(
        original_target=target,
        status="unresolved",
        source=f"{execution_surface}_user_input",
        reason=(
            f"{execution_surface}.instalar e {execution_surface}.remover exigem o nome real do pacote nesta release. "
            f"Use {execution_surface}.procurar para descobrir o nome exato antes da mutacao."
        ),
    )


def mediated_target_resolution_blocks(resolution: TargetResolution | None) -> bool:
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


def _backend_label(execution_surface: str, intent: str, profile: HostProfile) -> str:
    if profile.linux_family == "arch":
        inner = "pacman" if intent == "procurar" else "sudo + pacman"
    elif profile.linux_family == "debian":
        inner = "apt-cache" if intent == "procurar" else "sudo + apt-get"
    elif profile.linux_family == "opensuse":
        inner = "zypper" if intent == "procurar" else "sudo + zypper"
    else:
        inner = "dnf" if intent == "procurar" else "sudo + dnf"
    return f"{execution_surface} + {inner}"


def build_mediated_candidate(
    request: SemanticRequest,
    execution_surface: str,
    *,
    environment_profile: HostProfile | None,
    environment_resolution: EnvironmentResolution | None,
    run_prefix,
    target: str | None = None,
    notes: tuple[str, ...] = (),
) -> ExecutionRoute | None:
    if request.execution_surface != execution_surface:
        return None
    if request.domain_kind != "host_package" or request.requested_source:
        return None
    if environment_profile is None or environment_resolution is None:
        return None
    if environment_resolution.status != "resolved" or not environment_resolution.resolved_environment:
        return None

    environment_name = environment_resolution.resolved_environment
    resolved_target = target.strip() if target is not None and target.strip() else request.target.strip()
    if not resolved_target:
        return None

    prefix = run_prefix(environment_name)
    if request.intent == "procurar":
        return ExecutionRoute(
            route_name=f"{execution_surface}.procurar",
            action_name="procurar",
            backend_name=_backend_label(execution_surface, "procurar", environment_profile),
            command=prefix + _search_command(resolved_target, environment_profile),
            required_commands=(execution_surface,),
            implemented=True,
            notes=notes,
            execution_surface=execution_surface,
            environment_target=environment_name,
        )

    return ExecutionRoute(
        route_name=f"{execution_surface}.{request.intent}",
        action_name=request.intent,
        backend_name=_backend_label(execution_surface, request.intent, environment_profile),
        command=prefix + _mutation_command(request.intent, resolved_target, environment_profile),
        required_commands=(execution_surface,),
        state_probe_command=prefix + _state_probe_command(resolved_target, environment_profile),
        state_probe_required_commands=(execution_surface,),
        implemented=True,
        requires_privilege_escalation=True,
        notes=notes + (
            f"mutacao mediada usa probe antes e depois da execucao dentro da {execution_surface}.",
        ),
        execution_surface=execution_surface,
        environment_target=environment_name,
    )

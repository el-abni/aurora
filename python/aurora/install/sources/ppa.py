from __future__ import annotations

from dataclasses import dataclass
import os
import re
import shutil
import subprocess

from aurora.contracts.decisions import TargetResolution
from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest

_PPA_COORDINATE_RE = re.compile(r"^ppa:[A-Za-z0-9][A-Za-z0-9._+-]*/[A-Za-z0-9][A-Za-z0-9._+-]*$")
_PPA_PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_SUPPORTED_PPA_DISTRO_IDS = ("ubuntu",)


@dataclass(frozen=True)
class PpaCapabilityProbe:
    observed: bool
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = ("add-apt-repository", "--help")
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


def supported_ppa_distro_ids() -> tuple[str, ...]:
    return _SUPPORTED_PPA_DISTRO_IDS


def ppa_coordinate_is_explicit(value: str) -> bool:
    return _PPA_COORDINATE_RE.fullmatch(value.strip()) is not None


def observe_ppa_capability(
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> PpaCapabilityProbe:
    command = ("add-apt-repository", "--help")

    if profile is None:
        return PpaCapabilityProbe(
            observed=False,
            gap="host_profile_unavailable",
            reason="o host profile nao esta disponivel para observar a capacidade minima de PPA.",
            command=command,
        )

    if profile.linux_family != "debian":
        return PpaCapabilityProbe(
            observed=False,
            gap="ppa_linux_family_not_supported",
            reason="a capacidade minima de PPA so faz sentido em hosts Ubuntu mutaveis nesta rodada.",
            command=command,
        )

    if profile.distro_id not in _SUPPORTED_PPA_DISTRO_IDS:
        return PpaCapabilityProbe(
            observed=False,
            gap="ppa_distro_not_supported",
            reason="a frente PPA foi contida a Ubuntu mutavel nesta rodada.",
            command=command,
        )

    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    if shutil.which("add-apt-repository", path=path) is None:
        return PpaCapabilityProbe(
            observed=False,
            gap="ppa_add_repository_not_observed",
            reason=(
                "nao observei o comando 'add-apt-repository', necessario para abrir um PPA explicito "
                "nesta rodada."
            ),
            command=command,
        )

    proc = subprocess.run(command, text=True, capture_output=True, check=False, env=environ)
    combined_output = "\n".join(part.strip().lower() for part in (proc.stdout, proc.stderr) if part.strip())
    if proc.returncode == 0 or ("usage" in combined_output and "add-apt-repository" in combined_output):
        return PpaCapabilityProbe(
            observed=True,
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    return PpaCapabilityProbe(
        observed=False,
        gap="ppa_capability_probe_failed",
        reason=(
            "nao consegui observar com confianca a capacidade minima de PPA via "
            "'add-apt-repository --help'."
        ),
        command=command,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def _requested_ppa(request: SemanticRequest) -> str:
    return request.source_coordinate.strip()


def _state_probe_for_mutation(target: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return ("dpkg", "-s", target), ("dpkg",)


def resolve_ppa_target(
    request: SemanticRequest,
    _profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    del environ

    if request.domain_kind != "host_package" or request.requested_source != "ppa":
        return None
    if request.intent not in {"instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    if _PPA_PACKAGE_RE.fullmatch(target) is not None:
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_package_name",
            canonicalized=False,
            reason="o alvo ja parecia um nome de pacote utilizavel e foi usado diretamente para a frente PPA.",
        )

    return TargetResolution(
        original_target=target,
        status="unresolved",
        source="ppa_user_input",
        reason=(
            "PPA explicito nesta rodada exige o nome real do pacote, sem busca ou canonicalizacao "
            "automatica. Use o nome do pacote exatamente como ele existe no PPA pedido."
        ),
    )


def resolved_ppa_target(request: SemanticRequest, resolution: TargetResolution | None) -> str:
    if resolution is not None and resolution.resolved_target:
        return resolution.resolved_target
    return request.target


def ppa_target_resolution_blocks(_request: SemanticRequest, resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    return resolution.status in {"ambiguous", "not_found", "unresolved"}


def build_ppa_candidate(
    request: SemanticRequest,
    _profile: HostProfile,
    *,
    target: str | None = None,
) -> ExecutionRoute | None:
    if request.domain_kind != "host_package" or request.requested_source != "ppa":
        return None
    if request.intent != "instalar":
        return None

    repository = _requested_ppa(request)
    if not repository:
        return None

    mutation_target = target.strip() if target is not None and target.strip() else request.target
    state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
    return ExecutionRoute(
        route_name="ppa.instalar",
        action_name="instalar",
        backend_name="ppa",
        pre_commands=(
            ("sudo", "add-apt-repository", "-y", "-n", repository),
            ("sudo", "apt-get", "update"),
        ),
        pre_command_required_commands=(
            ("sudo", "add-apt-repository"),
            ("sudo", "apt-get"),
        ),
        command=("sudo", "apt-get", "install", "-y", mutation_target),
        required_commands=("sudo", "apt-get"),
        state_probe_command=state_probe_command,
        state_probe_required_commands=state_probe_required_commands,
        implemented=True,
        requires_privilege_escalation=True,
        notes=(
            "PPA entra como fonte explicita de terceiro nesta rodada.",
            f"coordenada PPA pedida: {repository}.",
            "esta frente so abre em Ubuntu mutavel com add-apt-repository, apt-get e dpkg observados.",
            "os passos preparatorios sao explicitos: add do PPA sem update implicito, depois apt-get update.",
            "esta frente nao faz descoberta automatica de PPA, busca global em PPA nem trata apt repo generico como PPA.",
            "nao ha cleanup automatico, remove-apt-repository nem lifecycle amplo do PPA nesta rodada.",
        ),
    )

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

_COPR_PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_COPR_MISSING_MARKERS = (
    "no such command",
    "unknown command",
    "no command named",
    "unknown argument: copr",
)


@dataclass(frozen=True)
class CoprCapabilityProbe:
    observed: bool
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = ("dnf", "copr", "--help")
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


def observe_copr_capability(
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> CoprCapabilityProbe:
    if profile is None:
        return CoprCapabilityProbe(
            observed=False,
            gap="host_profile_unavailable",
            reason="o host profile nao esta disponivel para observar a capacidade COPR.",
        )

    if profile.linux_family != "fedora":
        return CoprCapabilityProbe(
            observed=False,
            gap="copr_linux_family_not_supported",
            reason="a observacao de capacidade COPR so faz sentido em hosts Fedora nesta rodada.",
        )

    if "dnf" not in profile.package_backends:
        return CoprCapabilityProbe(
            observed=False,
            gap="copr_dnf_backend_not_observed",
            reason="a frente COPR depende de dnf observado neste host Fedora.",
        )

    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    if shutil.which("dnf", path=path) is None:
        return CoprCapabilityProbe(
            observed=False,
            gap="copr_dnf_backend_not_observed",
            reason="o backend dnf nao esta disponivel para observar a capacidade COPR.",
        )

    command = ("dnf", "copr", "--help")
    proc = subprocess.run(command, text=True, capture_output=True, check=False, env=environ)
    combined_output = "\n".join(part.strip().lower() for part in (proc.stdout, proc.stderr) if part.strip())
    if any(marker in combined_output for marker in _COPR_MISSING_MARKERS):
        return CoprCapabilityProbe(
            observed=False,
            gap="copr_dnf_plugin_not_observed",
            reason=(
                "o backend dnf foi observado, mas nao consegui confirmar o subcomando 'dnf copr' "
                "necessario para esta frente."
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    if proc.returncode == 0 or ("copr" in combined_output and "usage" in combined_output):
        return CoprCapabilityProbe(
            observed=True,
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    return CoprCapabilityProbe(
        observed=False,
        gap="copr_capability_probe_failed",
        reason=(
            "nao consegui observar com confianca a capacidade minima de COPR via 'dnf copr --help'."
        ),
        command=command,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def _requested_repository(request: SemanticRequest) -> str:
    return request.source_coordinate.strip()


def _state_probe_for_mutation(target: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return ("rpm", "-q", target), ("rpm",)


def resolve_copr_target(
    request: SemanticRequest,
    _profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    del environ

    if request.domain_kind != "host_package" or request.requested_source != "copr":
        return None
    if request.intent not in {"instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    if _COPR_PACKAGE_RE.fullmatch(target) is not None:
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_package_name",
            canonicalized=False,
            reason=(
                "o alvo ja parecia um nome de pacote utilizavel e foi usado diretamente para a frente COPR."
            ),
        )

    return TargetResolution(
        original_target=target,
        status="unresolved",
        source="copr_user_input",
        reason=(
            "COPR explicito nesta rodada exige o nome real do pacote, sem busca ou canonicalizacao "
            "automatica. Use o nome do pacote exatamente como ele existe no repositorio pedido."
        ),
    )


def resolved_copr_target(request: SemanticRequest, resolution: TargetResolution | None) -> str:
    if resolution is not None and resolution.resolved_target:
        return resolution.resolved_target
    return request.target


def copr_target_resolution_blocks(request: SemanticRequest, resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    if request.intent in {"instalar", "remover"}:
        return resolution.status in {"ambiguous", "not_found", "unresolved"}
    return False


def build_copr_candidate(
    request: SemanticRequest,
    _profile: HostProfile,
    *,
    target: str | None = None,
) -> ExecutionRoute | None:
    if request.domain_kind != "host_package" or request.requested_source != "copr":
        return None
    if request.intent not in {"instalar", "remover"}:
        return None

    repository = _requested_repository(request)
    if not repository:
        return None

    mutation_target = target.strip() if target is not None and target.strip() else request.target
    notes = (
        "COPR entra como fonte explicita de terceiro nesta rodada.",
        f"repositorio COPR pedido: {repository}.",
        "esta frente nao faz descoberta automatica de repositório nem busca global de pacote.",
        "state probe via rpm -q para confirmar o estado final do pacote do host.",
        "o lifecycle do repositorio COPR nao e gerenciado automaticamente nesta rodada.",
    )

    if request.intent == "instalar":
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
        return ExecutionRoute(
            route_name="copr.instalar",
            action_name="instalar",
            backend_name="dnf",
            pre_commands=(("sudo", "dnf", "-y", "copr", "enable", repository),),
            pre_command_required_commands=(("sudo", "dnf"),),
            command=("sudo", "dnf", "install", "-y", mutation_target),
            required_commands=("sudo", "dnf"),
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=True,
            notes=notes
            + (
                "a instalacao habilita explicitamente o repositorio pedido antes de instalar o pacote.",
            ),
        )

    state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
    return ExecutionRoute(
        route_name="copr.remover",
        action_name="remover",
        backend_name="dnf",
        command=("sudo", "dnf", "remove", "-y", mutation_target),
        required_commands=("sudo", "dnf"),
        state_probe_command=state_probe_command,
        state_probe_required_commands=state_probe_required_commands,
        implemented=True,
        requires_privilege_escalation=True,
        notes=notes
        + (
            "a remocao atua no pacote instalado e nao desabilita o repositorio COPR nesta rodada.",
        ),
    )

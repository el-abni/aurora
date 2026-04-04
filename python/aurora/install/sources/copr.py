from __future__ import annotations

from dataclasses import dataclass
import os
import re
import shutil
import subprocess
import tempfile
from urllib import error as urllib_error
from urllib import request as urllib_request

from aurora.contracts.decisions import TargetResolution
from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest
from aurora.linux.probes import read_os_release

_COPR_PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_COPR_MISSING_MARKERS = (
    "no such command",
    "unknown command",
    "no command named",
    "unknown argument: copr",
)
_COPR_NO_RESULTS_MARKERS = (
    "no matches found",
    "no match for argument",
    "nenhum pacote encontrado",
    "nenhuma correspondencia encontrada",
)
_COPR_BASE_URL_ENV = "AURORA_COPR_BASE_URL"


@dataclass(frozen=True)
class CoprCapabilityProbe:
    observed: bool
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = ("dnf", "copr", "--help")
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


def _human_search_query(target: str) -> str:
    normalized = re.sub(r"[-_]+", " ", target.strip())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _package_search_query(target: str) -> str:
    normalized = re.sub(r"[\s_]+", "-", target.strip())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def _preferred_search_query(target: str) -> str:
    stripped = target.strip()
    if not stripped:
        return ""
    package_query = _package_search_query(target)
    if " " in stripped and package_query and package_query != stripped:
        return package_query
    return stripped


def _search_queries_for_target(target: str) -> tuple[str, ...]:
    queries: list[str] = []
    for query in (_preferred_search_query(target), target.strip(), _human_search_query(target)):
        if query and query not in queries:
            queries.append(query)
    return tuple(queries)


def _requested_releasever(environ: dict[str, str] | None = None) -> str:
    resolved_environ = os.environ if environ is None else environ
    os_release = read_os_release(resolved_environ)
    return os_release.get("VERSION_ID", "").strip().lower()


def _repository_slug(repository: str) -> str:
    return "-".join(part.strip() for part in repository.split("/", 1) if part.strip())


def _repository_segments(repository: str) -> tuple[str, str]:
    owner, project = repository.split("/", 1)
    return owner.strip(), project.strip()


def _copr_base_url(environ: dict[str, str] | None = None) -> str:
    resolved_environ = os.environ if environ is None else environ
    return resolved_environ.get(_COPR_BASE_URL_ENV, "https://copr.fedorainfracloud.org").rstrip("/")


def _repo_file_url(
    repository: str,
    releasever: str,
    *,
    environ: dict[str, str] | None = None,
) -> str:
    owner, project = _repository_segments(repository)
    slug = _repository_slug(repository)
    base_url = _copr_base_url(environ)
    return (
        f"{base_url}/coprs/{owner}/{project}/repo/fedora-{releasever}/"
        f"{slug}-fedora-{releasever}.repo"
    )


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


def run_copr_search(
    repository: str,
    query: str,
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    releasever = _requested_releasever(environ)
    command = ("dnf", "--disablerepo=*", "--setopt=reposdir=<copr_repo_tempdir>", "search", query)
    if not releasever:
        return subprocess.CompletedProcess(
            command,
            66,
            "",
            "nao consegui determinar o VERSION_ID do host para consultar o repositório COPR pedido.",
        )

    repo_file_url = _repo_file_url(repository, releasever, environ=environ)
    try:
        with tempfile.TemporaryDirectory(prefix="aurora-copr-search-") as repo_dir:
            repo_file_name = f"{_repository_slug(repository)}-fedora-{releasever}.repo"
            repo_file_path = os.path.join(repo_dir, repo_file_name)
            with urllib_request.urlopen(repo_file_url, timeout=15) as response:
                repo_file_contents = response.read()
            with open(repo_file_path, "wb") as handle:
                handle.write(repo_file_contents)
            runtime_command = (
                "dnf",
                "--disablerepo=*",
                f"--setopt=reposdir={repo_dir}",
                "search",
                query,
            )
            return subprocess.run(
                runtime_command,
                text=True,
                capture_output=True,
                check=False,
                env=environ,
            )
    except (OSError, TimeoutError, urllib_error.URLError) as exc:
        return subprocess.CompletedProcess(
            command,
            69,
            "",
            (
                f"nao consegui preparar a consulta COPR restrita ao repositorio '{repository}' "
                f"para Fedora {releasever}. repo file: {repo_file_url}. detalhe: {exc}"
            ),
        )


def copr_search_has_no_results(stdout: str, stderr: str, returncode: int) -> bool:
    if returncode not in {0, 1, 104}:
        return False
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if not combined_output:
        return True
    return any(marker in combined_output for marker in _COPR_NO_RESULTS_MARKERS)


def resolve_copr_target(
    request: SemanticRequest,
    _profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    del environ

    if request.domain_kind != "host_package" or request.requested_source != "copr":
        return None
    if request.intent not in {"procurar", "instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    if request.intent == "procurar":
        repository = _requested_repository(request)
        consulted_target = _preferred_search_query(target)
        consulted_targets = _search_queries_for_target(target)
        canonicalized = consulted_target != target
        if canonicalized:
            return TargetResolution(
                original_target=target,
                consulted_target=consulted_target,
                consulted_targets=consulted_targets,
                status="query_refined",
                source="copr_repo_search_query_normalized",
                canonicalized=True,
                reason=(
                    f"o alvo humano '{target}' foi refinado para a consulta COPR '{consulted_target}' "
                    f"dentro do repositório explícito '{repository}' para reduzir ruído de busca, "
                    "sem promover isso a resolução automática de pacote."
                ),
            )
        return TargetResolution(
            original_target=target,
            consulted_target=consulted_target,
            consulted_targets=consulted_targets,
            status="query_direct",
            source="copr_repo_search_query_direct",
            canonicalized=False,
            reason=(
                f"o alvo de busca COPR '{target}' foi consultado diretamente dentro do repositório "
                f"explícito '{repository}'."
            ),
        )

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
    if request.intent == "procurar" and resolution is not None and resolution.consulted_target:
        return resolution.consulted_target
    return request.target


def copr_target_resolution_blocks(request: SemanticRequest, resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    if request.intent == "procurar":
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
    if request.intent not in {"procurar", "instalar", "remover"}:
        return None

    repository = _requested_repository(request)
    if not repository:
        return None

    mutation_target = target.strip() if target is not None and target.strip() else request.target
    notes = (
        "COPR entra como fonte explicita de terceiro nesta rodada.",
        f"repositorio COPR pedido: {repository}.",
        "esta frente nao faz descoberta automatica de repositório nem busca global de pacote.",
        "qualquer consulta fica restrita ao repositório explicitamente informado.",
        "o lifecycle do repositorio COPR nao e gerenciado automaticamente nesta rodada.",
    )

    if request.intent == "procurar":
        return ExecutionRoute(
            route_name="copr.procurar",
            action_name="procurar",
            backend_name="copr",
            command=("dnf", "--disablerepo=*", "--setopt=reposdir=<copr_repo_tempdir>", "search", mutation_target),
            required_commands=("dnf",),
            implemented=True,
            requires_privilege_escalation=False,
            notes=notes
            + (
                "a consulta usa apenas o repo file do repositório pedido para o Fedora atual, sem habilitar o repositório no host.",
            ),
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
                "state probe via rpm -q para confirmar o estado final do pacote do host.",
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
            "state probe via rpm -q para confirmar o estado final do pacote do host.",
            "a remocao atua no pacote instalado e nao desabilita o repositorio COPR nesta rodada.",
        ),
    )

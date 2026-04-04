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
_COPR_NOT_INSTALLED_MARKERS = (
    "no package matched",
    "no packages matched",
    "is not installed",
    "not installed",
)
_COPR_BASE_URL_ENV = "AURORA_COPR_BASE_URL"
_COPR_REPO_SECTION_RE = re.compile(r"^\[(?P<repoid>[^\]]+)\]\s*$")


@dataclass(frozen=True)
class CoprCapabilityProbe:
    observed: bool
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = ("dnf", "copr", "--help")
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class CoprRepositoryStateProbe:
    observed: bool
    status: str = "not_checked"
    enabled: bool | None = None
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = ("dnf", "copr", "list", "--enabled")
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class CoprPackageOriginProbe:
    observed: bool
    status: str = "not_checked"
    package_present: bool | None = None
    verified: bool | None = None
    from_repo: str = ""
    expected_repoids: tuple[str, ...] = ()
    gap: str = ""
    reason: str = ""
    command: tuple[str, ...] = ()
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


def _fetch_repo_file_contents(
    repository: str,
    *,
    environ: dict[str, str] | None = None,
) -> tuple[str, str, bytes]:
    releasever = _requested_releasever(environ)
    if not releasever:
        raise OSError(
            "nao consegui determinar o VERSION_ID do host para consultar o repositorio COPR pedido."
        )
    repo_file_url = _repo_file_url(repository, releasever, environ=environ)
    with urllib_request.urlopen(repo_file_url, timeout=15) as response:
        return releasever, repo_file_url, response.read()


def _repoids_from_repo_file_contents(contents: str) -> tuple[str, ...]:
    repoids: list[str] = []
    for raw_line in contents.splitlines():
        match = _COPR_REPO_SECTION_RE.match(raw_line.strip())
        if match is None:
            continue
        repoid = match.group("repoid").strip()
        if repoid and repoid not in repoids:
            repoids.append(repoid)
    return tuple(repoids)


def _output_mentions_repository(output: str, repository: str) -> bool:
    normalized_repository = repository.strip().lower()
    if not normalized_repository:
        return False
    for raw_line in output.splitlines():
        line = raw_line.strip().lower()
        if not line:
            continue
        if normalized_repository == line:
            return True
        if normalized_repository in line:
            return True
    return False


def _origin_probe_command(target: str) -> tuple[str, ...]:
    return (
        "dnf",
        "repoquery",
        "--installed",
        "--queryformat",
        "%{name}\t%{from_repo}",
        target,
    )


def observe_copr_repository_state(
    profile: HostProfile | None,
    repository: str,
    *,
    environ: dict[str, str] | None = None,
) -> CoprRepositoryStateProbe:
    if not repository.strip():
        return CoprRepositoryStateProbe(
            observed=False,
            status="repository_missing",
            gap="copr_repository_coordinate_missing",
            reason="faltou a coordenada explicita do repositorio COPR no formato owner/project.",
        )

    if profile is None:
        return CoprRepositoryStateProbe(
            observed=False,
            status="profile_unavailable",
            gap="host_profile_unavailable",
            reason="o host profile nao esta disponivel para observar o estado do repositorio COPR.",
        )

    if profile.linux_family != "fedora":
        return CoprRepositoryStateProbe(
            observed=False,
            status="linux_family_not_supported",
            gap="copr_linux_family_not_supported",
            reason="a observacao de estado do repositorio COPR so faz sentido em hosts Fedora nesta rodada.",
        )

    if "dnf" not in profile.package_backends:
        return CoprRepositoryStateProbe(
            observed=False,
            status="dnf_not_observed",
            gap="copr_dnf_backend_not_observed",
            reason="a observacao de estado do repositorio COPR depende de dnf observado neste host.",
        )

    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    if shutil.which("dnf", path=path) is None:
        return CoprRepositoryStateProbe(
            observed=False,
            status="dnf_not_observed",
            gap="copr_dnf_backend_not_observed",
            reason="o backend dnf nao esta disponivel para observar o estado do repositorio COPR.",
        )

    command = ("dnf", "copr", "list", "--enabled")
    proc = subprocess.run(command, text=True, capture_output=True, check=False, env=environ)
    if proc.returncode != 0:
        return CoprRepositoryStateProbe(
            observed=False,
            status="probe_failed",
            gap="copr_repository_state_not_observed",
            reason=(
                f"nao consegui observar se o repositorio COPR '{repository}' ja estava habilitado "
                "via 'dnf copr list --enabled'."
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    enabled = _output_mentions_repository("\n".join((proc.stdout, proc.stderr)), repository)
    if enabled:
        return CoprRepositoryStateProbe(
            observed=True,
            status="enabled",
            enabled=True,
            reason=(
                f"o repositorio COPR '{repository}' ja aparece em 'dnf copr list --enabled'."
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    return CoprRepositoryStateProbe(
        observed=True,
        status="disabled",
        enabled=False,
        reason=(
            f"o repositorio COPR '{repository}' nao aparece em 'dnf copr list --enabled' "
            "e sera tratado como desabilitado nesta rodada."
        ),
        command=command,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def observe_copr_package_origin(
    profile: HostProfile | None,
    repository: str,
    target: str,
    *,
    environ: dict[str, str] | None = None,
) -> CoprPackageOriginProbe:
    command = _origin_probe_command(target)
    if not repository.strip():
        return CoprPackageOriginProbe(
            observed=False,
            status="repository_missing",
            gap="copr_repository_coordinate_missing",
            reason="faltou a coordenada explicita do repositorio COPR no formato owner/project.",
            command=command,
        )

    if profile is None:
        return CoprPackageOriginProbe(
            observed=False,
            status="profile_unavailable",
            gap="host_profile_unavailable",
            reason="o host profile nao esta disponivel para verificar a origem RPM do pacote.",
            command=command,
        )

    if profile.linux_family != "fedora":
        return CoprPackageOriginProbe(
            observed=False,
            status="linux_family_not_supported",
            gap="copr_linux_family_not_supported",
            reason="a verificacao de origem RPM para COPR so faz sentido em hosts Fedora nesta rodada.",
            command=command,
        )

    if "dnf" not in profile.package_backends:
        return CoprPackageOriginProbe(
            observed=False,
            status="dnf_not_observed",
            gap="copr_dnf_backend_not_observed",
            reason="a verificacao de origem RPM para COPR depende de dnf observado neste host.",
            command=command,
        )

    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    if shutil.which("dnf", path=path) is None:
        return CoprPackageOriginProbe(
            observed=False,
            status="dnf_not_observed",
            gap="copr_dnf_backend_not_observed",
            reason="o backend dnf nao esta disponivel para verificar a origem RPM do pacote.",
            command=command,
        )

    proc = subprocess.run(command, text=True, capture_output=True, check=False, env=environ)
    combined_output = "\n".join(part.strip().lower() for part in (proc.stdout, proc.stderr) if part.strip())
    if proc.returncode != 0:
        if any(marker in combined_output for marker in _COPR_NOT_INSTALLED_MARKERS):
            return CoprPackageOriginProbe(
                observed=True,
                status="not_installed",
                package_present=False,
                verified=None,
                reason=(
                    f"o pacote '{target}' nao aparece como instalado; a verificacao de origem RPM "
                    "nao foi necessaria."
                ),
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        return CoprPackageOriginProbe(
            observed=False,
            status="probe_failed",
            package_present=None,
            verified=None,
            gap="copr_package_origin_probe_failed",
            reason=(
                f"nao consegui verificar a origem RPM do pacote '{target}' via "
                "'dnf repoquery --installed'."
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    from_repo = ""
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        columns = line.split("\t", 1)
        from_repo = columns[1].strip() if len(columns) == 2 else ""
        if from_repo:
            break

    if not from_repo:
        return CoprPackageOriginProbe(
            observed=True,
            status="origin_missing",
            package_present=True,
            verified=False,
            gap="copr_package_origin_not_reported",
            reason=(
                f"o pacote '{target}' esta instalado, mas 'dnf repoquery --installed' nao expos "
                "um campo from_repo confiavel para comparar com o repositorio COPR pedido."
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    try:
        _releasever, repo_file_url, repo_file_bytes = _fetch_repo_file_contents(repository, environ=environ)
        expected_repoids = _repoids_from_repo_file_contents(repo_file_bytes.decode("utf-8"))
    except (OSError, TimeoutError, UnicodeDecodeError, urllib_error.URLError) as exc:
        return CoprPackageOriginProbe(
            observed=False,
            status="repo_file_unavailable",
            package_present=True,
            verified=False,
            from_repo=from_repo,
            gap="copr_package_origin_reference_not_observed",
            reason=(
                f"o pacote '{target}' reportou from_repo '{from_repo}', mas nao consegui obter o "
                f"repo file de referencia do repositorio COPR '{repository}' para comparar. detalhe: {exc}"
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=repo_file_url if 'repo_file_url' in locals() else proc.stderr,
        )

    if not expected_repoids:
        return CoprPackageOriginProbe(
            observed=False,
            status="repo_ids_missing",
            package_present=True,
            verified=False,
            from_repo=from_repo,
            gap="copr_package_origin_reference_not_observed",
            reason=(
                f"o repo file do repositorio COPR '{repository}' nao expos repoid suficiente para "
                f"comparar com o from_repo '{from_repo}'."
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    if from_repo in expected_repoids:
        return CoprPackageOriginProbe(
            observed=True,
            status="verified",
            package_present=True,
            verified=True,
            from_repo=from_repo,
            expected_repoids=expected_repoids,
            reason=(
                f"o pacote '{target}' reportou from_repo '{from_repo}', compativel com o repo file "
                f"do repositorio COPR explicito '{repository}'."
            ),
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    return CoprPackageOriginProbe(
        observed=True,
        status="mismatch",
        package_present=True,
        verified=False,
        from_repo=from_repo,
        expected_repoids=expected_repoids,
        gap="copr_package_origin_mismatch",
        reason=(
            f"o pacote '{target}' reportou from_repo '{from_repo}', que nao corresponde aos repoids "
            f"observados para o repositorio COPR explicito '{repository}'."
        ),
        command=command,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
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
    command = ("dnf", "--disablerepo=*", "--setopt=reposdir=<copr_repo_tempdir>", "search", query)
    try:
        releasever, repo_file_url, repo_file_contents = _fetch_repo_file_contents(repository, environ=environ)
        with tempfile.TemporaryDirectory(prefix="aurora-copr-search-") as repo_dir:
            repo_file_name = f"{_repository_slug(repository)}-fedora-{releasever}.repo"
            repo_file_path = os.path.join(repo_dir, repo_file_name)
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
                    f"dentro do repositorio explicito '{repository}' para reduzir ruido de busca, "
                    "sem promover isso a resolucao automatica de pacote."
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
                f"o alvo de busca COPR '{target}' foi consultado diretamente dentro do repositorio "
                f"explicito '{repository}'."
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
    profile: HostProfile,
    *,
    target: str | None = None,
    environ: dict[str, str] | None = None,
) -> ExecutionRoute | None:
    if request.domain_kind != "host_package" or request.requested_source != "copr":
        return None
    if request.intent not in {"procurar", "instalar", "remover"}:
        return None

    repository = _requested_repository(request)
    if not repository:
        return None

    mutation_target = target.strip() if target is not None and target.strip() else request.target
    repository_state = (
        observe_copr_repository_state(profile, repository, environ=environ)
        if request.intent in {"instalar", "remover"}
        else None
    )
    notes = (
        "COPR entra como fonte explicita de terceiro nesta rodada.",
        f"repositorio COPR pedido: {repository}.",
        "esta frente nao faz descoberta automatica de repositorio nem busca global de pacote.",
        "qualquer consulta fica restrita ao repositorio explicitamente informado.",
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
                "a consulta usa apenas o repo file do repositorio pedido para o Fedora atual, sem habilitar o repositorio no host.",
                "o lifecycle do repositorio fica fora da rota de busca; nao ha enable, disable nem cleanup automatico.",
            ),
        )

    if request.intent == "instalar":
        pre_commands: tuple[tuple[str, ...], ...] = ()
        pre_command_required_commands: tuple[tuple[str, ...], ...] = ()
        install_notes: tuple[str, ...]
        if repository_state is not None and repository_state.observed and repository_state.enabled is True:
            install_notes = (
                repository_state.reason,
                "nenhum pre-command de enable foi planejado porque o repositorio ja estava habilitado.",
            )
        else:
            pre_commands = (("sudo", "dnf", "-y", "copr", "enable", repository),)
            pre_command_required_commands = (("sudo", "dnf"),)
            if repository_state is not None and repository_state.observed and repository_state.enabled is False:
                install_notes = (
                    repository_state.reason,
                    "enable explicito planejado como passo preparatorio minimo e idempotente.",
                )
            else:
                install_notes = (
                    (
                        repository_state.reason
                        if repository_state is not None
                        else ""
                    )
                    or (
                        f"o estado do repositorio COPR '{repository}' nao pode ser observado com "
                        "confianca antes da mutacao."
                    ),
                    "enable explicito mantido como guarda idempotente porque o estado previo do repositorio nao foi observado.",
                )
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
        return ExecutionRoute(
            route_name="copr.instalar",
            action_name="instalar",
            backend_name="dnf",
            pre_commands=pre_commands,
            pre_command_required_commands=pre_command_required_commands,
            command=("sudo", "dnf", "install", "-y", mutation_target),
            required_commands=("sudo", "dnf"),
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=True,
            notes=notes
            + (
                "state probe via rpm -q para confirmar o estado final do pacote do host.",
            )
            + install_notes
            + (
                "nao ha disable automatico, cleanup heuristico nem garbage collection de repositorio nesta rodada.",
            ),
        )

    provenance = observe_copr_package_origin(profile, repository, mutation_target, environ=environ)
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
            (
                repository_state.reason
                if repository_state is not None and repository_state.reason
                else f"o estado habilitado do repositorio COPR '{repository}' nao foi observado com confianca."
            ),
            provenance.reason,
            "a remocao atua apenas no pacote instalado e nao faz disable automatico do repositorio COPR nesta rodada.",
        ),
    )

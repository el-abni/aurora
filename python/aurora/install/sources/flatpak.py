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

_FLATPAK_DEFAULT_REMOTE = "flathub"
_FLATPAK_SEARCH_COLUMNS = "application,name,version,branch,origin"
_FLATPAK_REMOTE_RESOLUTION_COLUMNS = "application,name,origin"
_FLATPAK_LIST_RESOLUTION_COLUMNS = "application,name,origin"
_FLATPAK_NO_RESULTS_MARKERS = (
    "no matches found",
    "no results found",
    "nenhum resultado encontrado",
)
_FLATPAK_NOT_FOUND_MARKERS = (
    "no installed refs found",
    "not installed",
    "no remote refs found",
    "nothing matches",
)
_FLATPAK_REMOTE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class _FlatpakResolutionCandidate:
    app_id: str
    name: str
    origin: str = ""


def flatpak_remote_name_is_explicit(value: str) -> bool:
    return _FLATPAK_REMOTE_NAME_RE.fullmatch(value.strip()) is not None


def flatpak_requested_remote(request: SemanticRequest) -> str:
    return request.source_coordinate.strip()


def flatpak_effective_remote(request: SemanticRequest) -> str:
    requested_remote = flatpak_requested_remote(request)
    if requested_remote:
        return requested_remote
    if request.intent in {"procurar", "instalar"}:
        return _FLATPAK_DEFAULT_REMOTE
    return ""


def flatpak_remote_origin(request: SemanticRequest) -> str:
    if flatpak_requested_remote(request):
        return "explicit"
    if request.intent in {"procurar", "instalar"}:
        return "default"
    return "not_applicable"


def _state_probe_for_mutation(target: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return ("flatpak", "info", "--user", "--show-ref", target), ("flatpak",)


def _mutation_target(request: SemanticRequest, target: str | None) -> str:
    if target is not None and target.strip():
        return target.strip()
    return request.target


def _looks_like_flatpak_app_id(target: str) -> bool:
    stripped = target.strip()
    if not stripped or " " in stripped:
        return False
    return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*(\.[A-Za-z0-9][A-Za-z0-9._-]*){2,}", stripped) is not None


def _normalized_resolution_key(value: str) -> str:
    return "".join(re.findall(r"[a-z0-9]+", value.lower()))


def _candidate_label(candidate: _FlatpakResolutionCandidate) -> str:
    if candidate.name and candidate.name != candidate.app_id:
        return f"{candidate.app_id} ({candidate.name})"
    return candidate.app_id


def _candidate_matches_target(candidate: _FlatpakResolutionCandidate, target_key: str) -> bool:
    if _normalized_resolution_key(candidate.app_id) == target_key:
        return True
    return bool(candidate.name) and _normalized_resolution_key(candidate.name) == target_key


def _candidate_matches_search(candidate: _FlatpakResolutionCandidate, query_key: str) -> bool:
    if not query_key:
        return False
    if query_key in _normalized_resolution_key(candidate.app_id):
        return True
    return bool(candidate.name) and query_key in _normalized_resolution_key(candidate.name)


def _parse_tabular_parts(raw_line: str) -> tuple[str, ...]:
    line = raw_line.strip()
    if not line:
        return ()
    if "\t" in line:
        return tuple(part.strip() for part in line.split("\t") if part.strip())
    return tuple(part.strip() for part in re.split(r"\s{2,}", line) if part.strip())


def _parse_resolution_candidates(output: str) -> tuple[_FlatpakResolutionCandidate, ...]:
    candidates: list[_FlatpakResolutionCandidate] = []
    seen_app_ids: set[str] = set()
    for raw_line in output.splitlines():
        parts = _parse_tabular_parts(raw_line)
        if not parts:
            continue
        app_id = parts[0]
        if not app_id or app_id in seen_app_ids:
            continue
        name = parts[1] if len(parts) >= 2 else ""
        origin = parts[2] if len(parts) >= 3 else ""
        candidates.append(_FlatpakResolutionCandidate(app_id=app_id, name=name, origin=origin))
        seen_app_ids.add(app_id)
    return tuple(candidates)


def _parse_remote_names(output: str) -> tuple[str, ...]:
    remotes: list[str] = []
    for raw_line in output.splitlines():
        parts = _parse_tabular_parts(raw_line)
        if not parts:
            continue
        remote = parts[0]
        if remote and remote not in remotes:
            remotes.append(remote)
    return tuple(remotes)


def _flatpak_command_available(environ: dict[str, str] | None = None) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    return shutil.which("flatpak", path=path) is not None


def _run_flatpak_query(
    args: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False, env=environ)


def _run_flatpak_remote_listing(
    remote: str,
    *,
    columns: str,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    commands = (
        ("flatpak", "remote-ls", "--app", f"--columns={columns}", remote),
        ("flatpak", "remote-ls", "--user", "--app", f"--columns={columns}", remote),
    )

    successful_proc: subprocess.CompletedProcess[str] | None = None
    failed_proc: subprocess.CompletedProcess[str] | None = None
    for command in commands:
        proc = _run_flatpak_query(command, environ=environ)
        if proc.returncode == 0:
            if proc.stdout.strip():
                return proc
            if successful_proc is None:
                successful_proc = proc
            continue
        if failed_proc is None:
            failed_proc = proc

    if successful_proc is not None:
        return successful_proc
    if failed_proc is not None:
        return failed_proc
    return subprocess.CompletedProcess(commands[0], 1, "", "")


def observe_flatpak_remotes(
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> tuple[str, ...]:
    if profile is None or "flatpak" not in profile.observed_package_tools:
        return ()
    if not _flatpak_command_available(environ):
        return ()

    remotes: list[str] = []
    commands = (
        ("flatpak", "remotes", "--columns=name"),
        ("flatpak", "remotes", "--user", "--columns=name"),
    )
    for command in commands:
        proc = _run_flatpak_query(command, environ=environ)
        if proc.returncode != 0:
            continue
        for remote in _parse_remote_names(proc.stdout):
            if remote not in remotes:
                remotes.append(remote)
    return tuple(remotes)


def run_flatpak_search(
    remote: str,
    query: str,
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = _run_flatpak_remote_listing(
        remote,
        columns=_FLATPAK_SEARCH_COLUMNS,
        environ=environ,
    )
    if proc.returncode != 0:
        return proc

    query_key = _normalized_resolution_key(query)
    filtered_lines: list[str] = []
    for raw_line in proc.stdout.splitlines():
        parts = _parse_tabular_parts(raw_line)
        if not parts:
            continue
        candidate = _FlatpakResolutionCandidate(
            app_id=parts[0],
            name=parts[1] if len(parts) >= 2 else "",
            origin=parts[4] if len(parts) >= 5 else (parts[2] if len(parts) >= 3 else ""),
        )
        if _candidate_matches_search(candidate, query_key):
            filtered_lines.append(raw_line.rstrip())

    filtered_stdout = "\n".join(filtered_lines)
    if filtered_stdout:
        filtered_stdout += "\n"
    return subprocess.CompletedProcess(proc.args, 0, filtered_stdout, "")


def _resolution_from_candidates(
    target: str,
    candidates: tuple[_FlatpakResolutionCandidate, ...],
    *,
    source: str,
    no_match_status: str,
    no_match_reason: str,
    resolved_reason: str,
) -> TargetResolution:
    target_key = _normalized_resolution_key(target)
    matches = tuple(candidate for candidate in candidates if _candidate_matches_target(candidate, target_key))

    if not matches:
        return TargetResolution(
            original_target=target,
            status=no_match_status,
            source=source,
            reason=no_match_reason,
        )

    if len(matches) > 1:
        labels = tuple(_candidate_label(candidate) for candidate in matches)
        return TargetResolution(
            original_target=target,
            status="ambiguous",
            source=source,
            candidates=labels,
            reason=(
                f"encontrei multiplos candidatos Flatpak igualmente fortes para '{target}': "
                f"{', '.join(labels)}. Use o app ID real para prosseguir."
            ),
        )

    match = matches[0]
    return TargetResolution(
        original_target=target,
        resolved_target=match.app_id,
        status="resolved",
        source=source,
        canonicalized=match.app_id != target,
        candidates=(_candidate_label(match),),
        reason=resolved_reason.format(app_id=match.app_id, target=target),
    )


def _resolve_install_from_remote_catalog(
    target: str,
    *,
    remote: str,
    environ: dict[str, str] | None = None,
) -> TargetResolution:
    proc = _run_flatpak_remote_listing(
        remote,
        columns=_FLATPAK_REMOTE_RESOLUTION_COLUMNS,
        environ=environ,
    )
    if proc.returncode != 0:
        return TargetResolution(
            original_target=target,
            status="unresolved",
            source="flatpak_remote_ls",
            reason=(
                f"nao consegui resolver o alvo Flatpak '{target}' porque a leitura controlada do remote "
                f"'{remote}' falhou operacionalmente."
            ),
            diagnostic_command=tuple(str(part) for part in proc.args),
            diagnostic_exit_code=proc.returncode,
            diagnostic_stdout=proc.stdout,
            diagnostic_stderr=proc.stderr,
        )

    return _resolution_from_candidates(
        target,
        _parse_resolution_candidates(proc.stdout),
        source="flatpak_remote_ls",
        no_match_status="not_found",
        no_match_reason=(
            f"nao encontrei um app Flatpak com correspondencia exata e confiavel para '{target}' "
            f"no remote '{remote}'. Use o app ID real ou refine o nome."
        ),
        resolved_reason=(
            "o alvo humano '{target}' foi resolvido por leitura controlada do remote "
            f"'{remote}' para o app ID '{{app_id}}'."
        ),
    )


def _resolve_remove_from_user_installation(
    target: str,
    *,
    requested_remote: str,
    environ: dict[str, str] | None = None,
) -> TargetResolution:
    proc = _run_flatpak_query(
        ("flatpak", "list", "--user", "--app", f"--columns={_FLATPAK_LIST_RESOLUTION_COLUMNS}"),
        environ=environ,
    )
    if proc.returncode != 0:
        return TargetResolution(
            original_target=target,
            status="unresolved",
            source="flatpak_list_user",
            reason=(
                f"nao consegui resolver o alvo Flatpak '{target}' porque a leitura dos apps instalados "
                "do usuario falhou operacionalmente."
            ),
        )

    candidates = _parse_resolution_candidates(proc.stdout)
    resolution = _resolution_from_candidates(
        target,
        candidates,
        source="flatpak_list_user",
        no_match_status="absent",
        no_match_reason=(
            f"nao encontrei um app instalado na instalacao do usuario com correspondencia exata e "
            f"confiavel para '{target}'."
        ),
        resolved_reason=(
            "o alvo humano '{target}' foi resolvido na instalacao do usuario para o app ID '{app_id}'."
        ),
    )
    if resolution.status != "resolved" or not requested_remote:
        return resolution

    matched_candidate = next(
        (candidate for candidate in candidates if candidate.app_id == resolution.resolved_target),
        None,
    )
    if matched_candidate is None:
        return resolution
    if not matched_candidate.origin:
        return TargetResolution(
            original_target=target,
            resolved_target=resolution.resolved_target,
            status="unresolved",
            source="flatpak_list_user_origin",
            canonicalized=resolution.canonicalized,
            candidates=resolution.candidates,
            reason=(
                f"nao consegui observar o origin do app instalado '{resolution.resolved_target}' "
                "para validar a restricao de remote desta rodada."
            ),
        )
    if matched_candidate.origin != requested_remote:
        return TargetResolution(
            original_target=target,
            resolved_target=resolution.resolved_target,
            status="source_mismatch",
            source="flatpak_list_user_origin",
            canonicalized=resolution.canonicalized,
            candidates=resolution.candidates,
            reason=(
                f"o app instalado '{resolution.resolved_target}' pertence ao remote "
                f"'{matched_candidate.origin}', nao ao remote explicitamente pedido '{requested_remote}'."
            ),
        )
    return TargetResolution(
        original_target=resolution.original_target,
        resolved_target=resolution.resolved_target,
        status=resolution.status,
        source="flatpak_list_user_origin",
        canonicalized=resolution.canonicalized,
        candidates=resolution.candidates,
        reason=(
            f"o alvo humano '{target}' foi resolvido na instalacao do usuario para o app ID "
            f"'{resolution.resolved_target}', com origin confirmado no remote '{requested_remote}'."
        ),
    )


def resolve_flatpak_target(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    if request.domain_kind != "user_software" or request.intent not in {"instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    requested_remote = flatpak_requested_remote(request)
    effective_remote = flatpak_effective_remote(request)

    if request.intent == "instalar" and _looks_like_flatpak_app_id(target):
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_app_id",
            canonicalized=False,
            reason=(
                "o alvo ja parecia um app ID Flatpak e foi usado diretamente."
                if not effective_remote
                else f"o alvo ja parecia um app ID Flatpak e foi usado diretamente no remote '{effective_remote}'."
            ),
        )

    if profile is None or "flatpak" not in profile.observed_package_tools:
        return None

    if not _flatpak_command_available(environ):
        return None

    if request.intent == "instalar":
        return _resolve_install_from_remote_catalog(
            target,
            remote=effective_remote,
            environ=environ,
        )

    if _looks_like_flatpak_app_id(target) and not requested_remote:
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_app_id",
            canonicalized=False,
            reason="o alvo ja parecia um app ID Flatpak e foi usado diretamente.",
        )

    return _resolve_remove_from_user_installation(
        target,
        requested_remote=requested_remote,
        environ=environ,
    )


def flatpak_target_resolution_blocks(request: SemanticRequest, resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    if request.intent == "instalar":
        return resolution.status in {"ambiguous", "not_found", "unresolved"}
    if request.intent == "remover":
        return resolution.status in {"ambiguous", "unresolved", "source_mismatch"}
    return False


def resolved_flatpak_target(request: SemanticRequest, resolution: TargetResolution | None) -> str:
    if resolution is not None and resolution.resolved_target:
        return resolution.resolved_target
    return request.target


def build_flatpak_candidate(
    request: SemanticRequest,
    _profile: HostProfile,
    *,
    target: str | None = None,
) -> ExecutionRoute | None:
    if request.domain_kind != "user_software":
        return None

    mutation_target = _mutation_target(request, target)
    effective_remote = flatpak_effective_remote(request)
    remote_origin = flatpak_remote_origin(request)

    if request.intent == "procurar":
        remote_note = (
            f"remote default assumido: {effective_remote}."
            if remote_origin == "default"
            else f"remote explicito pedido: {effective_remote}."
        )
        return ExecutionRoute(
            route_name="flatpak.procurar",
            action_name="procurar",
            backend_name="flatpak",
            command=(
                "flatpak",
                "remote-ls",
                "--app",
                f"--columns={_FLATPAK_SEARCH_COLUMNS}",
                effective_remote,
            ),
            required_commands=("flatpak",),
            implemented=True,
            requires_privilege_escalation=False,
            notes=(
                "primeiro corte contido de remote explicito na familia flatpak.",
                remote_note,
                "flatpak.procurar usa flatpak remote-ls filtrado localmente para respeitar o remote selecionado.",
            ),
        )

    if request.intent == "instalar":
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
        remote_note = (
            f"remote default assumido: {effective_remote}."
            if remote_origin == "default"
            else f"remote explicito pedido: {effective_remote}."
        )
        return ExecutionRoute(
            route_name="flatpak.instalar",
            action_name="instalar",
            backend_name="flatpak",
            command=(
                "flatpak",
                "install",
                "--user",
                "--noninteractive",
                "-y",
                "--app",
                effective_remote,
                mutation_target,
            ),
            required_commands=("flatpak",),
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=False,
            notes=(
                "mutacao de user_software usa installation scope explicito de usuario.",
                remote_note,
                "nao ha add automatico de remote nesta rodada; o remote precisa estar previamente observavel.",
                "state probe via flatpak info --user --show-ref.",
                "instalacao usa app ID resolvido quando a canonicalizacao fecha de forma confiavel.",
            ),
        )

    if request.intent == "remover":
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
        remote_notes = (
            (
                "remote nao e assumido por default em flatpak.remover nesta rodada.",
            )
            if not effective_remote
            else (
                f"remote explicito pedido: {effective_remote}.",
                "o remote explicito atua apenas como restricao honesta de origin da ref instalada.",
            )
        )
        return ExecutionRoute(
            route_name="flatpak.remover",
            action_name="remover",
            backend_name="flatpak",
            command=(
                "flatpak",
                "uninstall",
                "--user",
                "--noninteractive",
                "-y",
                "--app",
                mutation_target,
            ),
            required_commands=("flatpak",),
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=False,
            notes=(
                "mutacao de user_software usa installation scope explicito de usuario.",
                *remote_notes,
                "state probe via flatpak info --user --show-ref.",
                "remocao nao usa --delete-data nesta rodada.",
                "remocao usa app ID resolvido quando a canonicalizacao fecha de forma confiavel.",
            ),
        )

    return ExecutionRoute(
        route_name=f"flatpak.{request.intent}",
        action_name=request.intent,
        backend_name="flatpak",
        required_commands=("flatpak",),
        implemented=False,
        requires_privilege_escalation=False,
        notes=("acao ainda nao aberta para a rota flatpak nesta release.",),
    )


def flatpak_search_has_no_results(stdout: str, stderr: str, returncode: int) -> bool:
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if any(marker in combined_output for marker in _FLATPAK_NO_RESULTS_MARKERS):
        return True
    return returncode == 0 and not stdout.strip()


def flatpak_mutation_reports_no_matching_ref(stdout: str, stderr: str) -> bool:
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if not combined_output:
        return False
    return any(marker in combined_output for marker in _FLATPAK_NOT_FOUND_MARKERS)

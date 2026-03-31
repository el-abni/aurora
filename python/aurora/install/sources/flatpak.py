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
_FLATPAK_SEARCH_COLUMNS = "application,name,version,branch,remotes"
_FLATPAK_RESOLUTION_COLUMNS = "application,name"
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


@dataclass(frozen=True)
class _FlatpakResolutionCandidate:
    app_id: str
    name: str


@dataclass(frozen=True)
class _FlatpakSearchResolution:
    candidates: tuple[_FlatpakResolutionCandidate, ...]
    source: str
    reason_suffix: str = ""
    queries_used: tuple[str, ...] = ()


def _default_remote(_request: SemanticRequest) -> str:
    return _FLATPAK_DEFAULT_REMOTE


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


def _normalized_human_search_query(target: str) -> str:
    normalized = re.sub(r"[-_]+", " ", target.strip())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _search_queries_for_target(target: str) -> tuple[str, ...]:
    queries: list[str] = []
    for query in (target.strip(), _normalized_human_search_query(target)):
        if query and query not in queries:
            queries.append(query)
    return tuple(queries)


def _parse_resolution_candidates(output: str) -> tuple[_FlatpakResolutionCandidate, ...]:
    candidates: list[_FlatpakResolutionCandidate] = []
    seen_app_ids: set[str] = set()
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("\t") if part.strip()]
        if len(parts) < 2:
            parts = [part.strip() for part in re.split(r"\s{2,}", line, maxsplit=1) if part.strip()]
        if not parts:
            continue
        app_id = parts[0]
        if not app_id or app_id in seen_app_ids:
            continue
        name = parts[1] if len(parts) >= 2 else ""
        candidates.append(_FlatpakResolutionCandidate(app_id=app_id, name=name))
        seen_app_ids.add(app_id)
    return tuple(candidates)


def _merge_resolution_candidates(
    candidates: tuple[_FlatpakResolutionCandidate, ...],
    new_candidates: tuple[_FlatpakResolutionCandidate, ...],
) -> tuple[_FlatpakResolutionCandidate, ...]:
    merged = {candidate.app_id: candidate for candidate in candidates}
    for candidate in new_candidates:
        merged[candidate.app_id] = candidate
    return tuple(merged.values())


def _flatpak_command_available(environ: dict[str, str] | None = None) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    return shutil.which("flatpak", path=path) is not None


def _run_flatpak_query(
    args: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False, env=environ)


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


def _search_resolution_candidates(
    target: str,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | _FlatpakSearchResolution:
    candidates: tuple[_FlatpakResolutionCandidate, ...] = ()
    original_query = target.strip()
    successful_queries: list[str] = []

    for query in _search_queries_for_target(target):
        proc = _run_flatpak_query(
            ("flatpak", "search", f"--columns={_FLATPAK_RESOLUTION_COLUMNS}", query),
            environ=environ,
        )
        if flatpak_search_has_no_results(proc.stdout, proc.stderr, proc.returncode):
            continue
        if proc.returncode != 0:
            return TargetResolution(
                original_target=target,
                status="unresolved",
                source="flatpak_search",
                reason=(
                    f"nao consegui resolver o alvo Flatpak '{target}' porque a busca de canonicalizacao "
                    "falhou operacionalmente."
                ),
            )

        parsed_candidates = _parse_resolution_candidates(proc.stdout)
        candidates = _merge_resolution_candidates(candidates, parsed_candidates)
        successful_queries.append(query)

    if successful_queries:
        normalized_queries = tuple(query for query in successful_queries if query != original_query)
        if normalized_queries:
            normalized_label = "', '".join(normalized_queries)
            source = "flatpak_search_normalized_query"
            reason_suffix = f" usando a consulta humana normalizada '{normalized_label}'"
        else:
            source = "flatpak_search"
            reason_suffix = ""
        return _FlatpakSearchResolution(
            candidates=candidates,
            source=source,
            reason_suffix=reason_suffix,
            queries_used=tuple(successful_queries),
        )

    return TargetResolution(
        original_target=target,
        status="not_found",
        source="flatpak_search",
        reason=(
            f"nao encontrei um app Flatpak com correspondencia exata e confiavel para '{target}'. "
            "Use o app ID real ou refine o nome."
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

    if _looks_like_flatpak_app_id(target):
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_app_id",
            canonicalized=False,
            reason="o alvo ja parecia um app ID Flatpak e foi usado diretamente.",
        )

    if profile is None or "flatpak" not in profile.observed_package_tools:
        return None

    if not _flatpak_command_available(environ):
        return None

    if request.intent == "instalar":
        search_resolution = _search_resolution_candidates(target, environ=environ)
        if isinstance(search_resolution, TargetResolution):
            return search_resolution
        return _resolution_from_candidates(
            target,
            search_resolution.candidates,
            source=search_resolution.source,
            no_match_status="not_found",
            no_match_reason=(
                f"nao encontrei um app Flatpak com correspondencia exata e confiavel para '{target}'. "
                "Use o app ID real ou refine o nome."
            ),
            resolved_reason=(
                "o alvo humano '{target}' foi resolvido por busca controlada do Flatpak"
                f"{search_resolution.reason_suffix} para o app ID "
                "'{app_id}'."
            ),
        )

    proc = _run_flatpak_query(
        ("flatpak", "list", "--user", "--app", f"--columns={_FLATPAK_RESOLUTION_COLUMNS}"),
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
    return _resolution_from_candidates(
        target,
        _parse_resolution_candidates(proc.stdout),
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


def flatpak_target_resolution_blocks(request: SemanticRequest, resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    if request.intent == "instalar":
        return resolution.status in {"ambiguous", "not_found", "unresolved"}
    if request.intent == "remover":
        return resolution.status in {"ambiguous", "unresolved"}
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

    if request.intent == "procurar":
        return ExecutionRoute(
            route_name="flatpak.procurar",
            action_name="procurar",
            backend_name="flatpak",
            command=("flatpak", "search", f"--columns={_FLATPAK_SEARCH_COLUMNS}", request.target),
            required_commands=("flatpak",),
            implemented=True,
            requires_privilege_escalation=False,
            notes=(
                "primeiro corte do dominio user_software.",
                "a busca usa o installation scope padrao do flatpak nesta rodada.",
            ),
        )

    if request.intent == "instalar":
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
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
                _default_remote(request),
                mutation_target,
            ),
            required_commands=("flatpak",),
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=False,
            notes=(
                "mutacao de user_software usa installation scope explicito de usuario.",
                "remote default: flathub nesta rodada.",
                "state probe via flatpak info --user --show-ref.",
                "instalacao usa app ID resolvido quando a canonicalizacao fecha de forma confiavel.",
            ),
        )

    if request.intent == "remover":
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
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

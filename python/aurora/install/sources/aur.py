from __future__ import annotations

from dataclasses import dataclass, replace
import os
import re
import shlex
import shutil
import subprocess

from aurora.contracts.decisions import TargetResolution
from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile
from aurora.contracts.requests import SemanticRequest

_SUPPORTED_AUR_HELPERS = ("paru", "yay")
_AUR_NO_RESULTS_MARKERS = (
    "no packages found",
    "no matches found",
    "no results found",
    "nenhum pacote encontrado",
    "nenhuma correspondencia encontrada",
)
_AUR_NOT_FOUND_MARKERS = (
    "target not found",
    "package not found",
    "could not find all required packages",
)


@dataclass(frozen=True)
class _AurResolutionCandidate:
    package_name: str


@dataclass(frozen=True)
class _AurSearchResolution:
    candidates: tuple[_AurResolutionCandidate, ...]
    source: str
    reason_suffix: str = ""
    queries_used: tuple[str, ...] = ()
    consulted_targets: tuple[str, ...] = ()
    consulted_target: str = ""
    diagnostic_command: tuple[str, ...] = ()
    diagnostic_exit_code: int | None = None
    diagnostic_stdout: str = ""
    diagnostic_stderr: str = ""


def supported_aur_helper(profile: HostProfile | None) -> str | None:
    if profile is None:
        return None
    for helper in _SUPPORTED_AUR_HELPERS:
        if helper in profile.observed_third_party_package_tools:
            return helper
    return None


def supported_aur_helpers() -> tuple[str, ...]:
    return _SUPPORTED_AUR_HELPERS


def observed_out_of_contract_aur_helpers(profile: HostProfile | None) -> tuple[str, ...]:
    if profile is None:
        return ()
    return tuple(
        tool for tool in profile.observed_third_party_package_tools if tool not in _SUPPORTED_AUR_HELPERS
    )


def _normalized_resolution_key(value: str) -> str:
    return "".join(re.findall(r"[a-z0-9]+", value.lower()))


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


def _mutation_consulted_target(target: str) -> tuple[str, tuple[str, ...]]:
    original_target = target.strip()
    consulted_target = _preferred_search_query(original_target)
    consulted_targets: list[str] = []
    for candidate in (consulted_target, original_target):
        if candidate and candidate not in consulted_targets:
            consulted_targets.append(candidate)
    return consulted_target, tuple(consulted_targets)


def _search_queries_for_target(target: str) -> tuple[str, ...]:
    queries: list[str] = []
    for query in (_preferred_search_query(target), target.strip(), _human_search_query(target)):
        if query and query not in queries:
            queries.append(query)
    return tuple(queries)


def _command_available(name: str, environ: dict[str, str] | None = None) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    return shutil.which(name, path=path) is not None


def _run_command(
    args: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False, env=environ)


def _compact_output_excerpt(text: str, *, limit: int = 240) -> str:
    compact = " | ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _search_failure_reason(
    target: str,
    command: tuple[str, ...],
    proc: subprocess.CompletedProcess[str],
) -> str:
    reason = (
        f"nao consegui resolver o alvo AUR '{target}' porque o comando "
        f"'{shlex.join(command)}' retornou exit code {proc.returncode} durante a busca controlada."
    )
    stderr_excerpt = _compact_output_excerpt(proc.stderr)
    stdout_excerpt = _compact_output_excerpt(proc.stdout)
    if stderr_excerpt:
        return f"{reason} stderr: {stderr_excerpt}"
    if stdout_excerpt:
        return f"{reason} stdout: {stdout_excerpt}"
    return reason


def _aur_package_name_from_search_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or line[:1].isspace():
        return ""

    token = stripped.split()[0]
    if "/" in token:
        return token.split("/", 1)[1]
    return token


def _package_name_from_installed_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    return stripped.split()[0]


def _parse_search_candidates(output: str) -> tuple[_AurResolutionCandidate, ...]:
    candidates: list[_AurResolutionCandidate] = []
    seen: set[str] = set()
    for raw_line in output.splitlines():
        package_name = _aur_package_name_from_search_line(raw_line)
        if not package_name or package_name in seen:
            continue
        candidates.append(_AurResolutionCandidate(package_name=package_name))
        seen.add(package_name)
    return tuple(candidates)


def aur_search_has_parseable_candidates(stdout: str) -> bool:
    return bool(_parse_search_candidates(stdout))


def _parse_installed_candidates(output: str) -> tuple[_AurResolutionCandidate, ...]:
    candidates: list[_AurResolutionCandidate] = []
    seen: set[str] = set()
    for raw_line in output.splitlines():
        package_name = _package_name_from_installed_line(raw_line)
        if not package_name or package_name in seen:
            continue
        candidates.append(_AurResolutionCandidate(package_name=package_name))
        seen.add(package_name)
    return tuple(candidates)


def _merge_resolution_candidates(
    candidates: tuple[_AurResolutionCandidate, ...],
    new_candidates: tuple[_AurResolutionCandidate, ...],
) -> tuple[_AurResolutionCandidate, ...]:
    merged = {candidate.package_name: candidate for candidate in candidates}
    for candidate in new_candidates:
        merged[candidate.package_name] = candidate
    return tuple(merged.values())


def _candidate_matches_target(candidate: _AurResolutionCandidate, target_key: str) -> bool:
    return _normalized_resolution_key(candidate.package_name) == target_key


def _candidate_label(candidate: _AurResolutionCandidate) -> str:
    return candidate.package_name


def _resolution_from_candidates(
    target: str,
    candidates: tuple[_AurResolutionCandidate, ...],
    *,
    consulted_target: str = "",
    consulted_targets: tuple[str, ...] = (),
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
            consulted_target=consulted_target,
            consulted_targets=consulted_targets,
            status=no_match_status,
            source=source,
            reason=no_match_reason,
        )

    if len(matches) > 1:
        labels = tuple(_candidate_label(candidate) for candidate in matches)
        return TargetResolution(
            original_target=target,
            consulted_target=consulted_target,
            consulted_targets=consulted_targets,
            status="ambiguous",
            source=source,
            candidates=labels,
            reason=(
                f"encontrei multiplos pacotes AUR igualmente fortes para '{target}': "
                f"{', '.join(labels)}. Use o nome real do pacote AUR para prosseguir."
            ),
        )

    match = matches[0]
    return TargetResolution(
        original_target=target,
        consulted_target=consulted_target,
        consulted_targets=consulted_targets,
        resolved_target=match.package_name,
        status="resolved",
        source=source,
        canonicalized=match.package_name != target,
        candidates=(_candidate_label(match),),
        reason=resolved_reason.format(target=target, package_name=match.package_name),
    )


def _search_resolution_candidates(
    target: str,
    helper: str,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | _AurSearchResolution:
    candidates: tuple[_AurResolutionCandidate, ...] = ()
    original_query = target.strip()
    search_queries = _search_queries_for_target(target)
    attempted_queries: list[str] = []
    successful_queries: list[str] = []
    observed_search_output = False
    matched_query = ""
    target_key = _normalized_resolution_key(target)
    preferred_query = _preferred_search_query(target)
    diagnostic_command: tuple[str, ...] = ()
    diagnostic_exit_code: int | None = None
    diagnostic_stdout = ""
    diagnostic_stderr = ""

    if not _command_available(helper, environ):
        return TargetResolution(
            original_target=target,
            consulted_target=preferred_query,
            consulted_targets=search_queries,
            status="unresolved",
            source="aur_search",
            reason=f"o helper AUR '{helper}' nao esta disponivel para resolver este alvo.",
        )

    for query in search_queries:
        command = (helper, "-Ss", "--aur", "--", query)
        attempted_queries.append(query)
        proc = _run_command(command, environ=environ)
        if aur_search_has_no_results(proc.stdout, proc.stderr, proc.returncode):
            continue
        parsed_candidates = _parse_search_candidates(proc.stdout)
        if proc.returncode != 0 and not parsed_candidates:
            if matched_query:
                diagnostic_command = command
                diagnostic_exit_code = proc.returncode
                diagnostic_stdout = proc.stdout
                diagnostic_stderr = proc.stderr
                continue
            return TargetResolution(
                original_target=target,
                consulted_target=preferred_query,
                consulted_targets=tuple(attempted_queries),
                status="unresolved",
                source="aur_search",
                reason=_search_failure_reason(target, command, proc),
                diagnostic_command=command,
                diagnostic_exit_code=proc.returncode,
                diagnostic_stdout=proc.stdout,
                diagnostic_stderr=proc.stderr,
            )

        if proc.stdout.strip():
            observed_search_output = True

        if proc.returncode != 0 and parsed_candidates:
            diagnostic_command = command
            diagnostic_exit_code = proc.returncode
            diagnostic_stdout = proc.stdout
            diagnostic_stderr = proc.stderr

        candidates = _merge_resolution_candidates(candidates, parsed_candidates)
        successful_queries.append(query)
        if not matched_query and any(_candidate_matches_target(candidate, target_key) for candidate in parsed_candidates):
            matched_query = query

    if observed_search_output and not candidates:
        return TargetResolution(
            original_target=target,
            consulted_target=preferred_query,
            consulted_targets=tuple(successful_queries) or search_queries,
            status="unresolved",
            source="aur_search",
            reason=(
                f"nao consegui interpretar candidatos confiaveis para '{target}' a partir da busca "
                f"controlada do helper '{helper}'."
            ),
            diagnostic_command=diagnostic_command,
            diagnostic_exit_code=diagnostic_exit_code,
            diagnostic_stdout=diagnostic_stdout,
            diagnostic_stderr=diagnostic_stderr,
        )

    if successful_queries:
        normalized_queries = tuple(query for query in successful_queries if query != original_query)
        if normalized_queries:
            normalized_label = "', '".join(normalized_queries)
            source = "aur_search_normalized_query"
            reason_suffix = f" usando a consulta humana normalizada '{normalized_label}'"
        else:
            source = "aur_search"
            reason_suffix = ""
        return _AurSearchResolution(
            candidates=candidates,
            source=source,
            reason_suffix=reason_suffix,
            queries_used=tuple(successful_queries),
            consulted_targets=search_queries,
            consulted_target=matched_query or preferred_query or successful_queries[0],
            diagnostic_command=diagnostic_command,
            diagnostic_exit_code=diagnostic_exit_code,
            diagnostic_stdout=diagnostic_stdout,
            diagnostic_stderr=diagnostic_stderr,
        )

    return TargetResolution(
        original_target=target,
        consulted_target=preferred_query,
        consulted_targets=search_queries,
        status="not_found",
        source="aur_search",
        reason=(
            f"nao encontrei um pacote AUR com correspondencia exata e confiavel para '{target}'. "
            "Use o nome real do pacote AUR ou refine o pedido."
        ),
    )


def _installed_resolution(
    target: str,
    *,
    query_flag: str,
    source: str,
    no_match_status: str,
    no_match_reason: str,
    resolved_reason: str,
    environ: dict[str, str] | None = None,
) -> TargetResolution:
    consulted_target, consulted_targets = _mutation_consulted_target(target)
    if not _command_available("pacman", environ):
        return TargetResolution(
            original_target=target,
            consulted_target=consulted_target,
            consulted_targets=consulted_targets,
            status="unresolved",
            source=source,
            reason="o backend oficial pacman nao esta disponivel para inspecionar o estado do host.",
        )

    proc = _run_command(("pacman", query_flag), environ=environ)
    if proc.returncode != 0:
        return TargetResolution(
            original_target=target,
            consulted_target=consulted_target,
            consulted_targets=consulted_targets,
            status="unresolved",
            source=source,
            reason="nao consegui ler o estado instalado do host para resolver este alvo AUR.",
            diagnostic_command=("pacman", query_flag),
            diagnostic_exit_code=proc.returncode,
            diagnostic_stdout=proc.stdout,
            diagnostic_stderr=proc.stderr,
        )
    return _resolution_from_candidates(
        target,
        _parse_installed_candidates(proc.stdout),
        consulted_target=consulted_target,
        consulted_targets=consulted_targets,
        source=source,
        no_match_status=no_match_status,
        no_match_reason=no_match_reason,
        resolved_reason=resolved_reason,
    )


def _native_source_mismatch(
    target: str,
    *,
    lookup_target: str | None = None,
    consulted_target: str = "",
    consulted_targets: tuple[str, ...] = (),
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    if not consulted_target:
        consulted_target, consulted_targets = _mutation_consulted_target(target)
    native_resolution = _installed_resolution(
        lookup_target or target,
        query_flag="-Qn",
        source="pacman_native_list",
        no_match_status="not_found",
        no_match_reason="",
        resolved_reason="",
        environ=environ,
    )
    if native_resolution.status != "resolved":
        return None

    return TargetResolution(
        original_target=target,
        consulted_target=consulted_target,
        consulted_targets=consulted_targets,
        resolved_target=native_resolution.resolved_target,
        status="source_mismatch",
        source="pacman_native_list",
        canonicalized=native_resolution.canonicalized,
        candidates=native_resolution.candidates,
        reason=(
            f"o pacote '{native_resolution.resolved_target}' esta instalado como pacote oficial do host via "
            "pacman; o pedido foi marcado explicitamente como AUR e nao foi promovido por fallback."
        ),
    )


def resolve_aur_target(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    if request.domain_kind != "host_package" or request.requested_source != "aur":
        return None
    if request.intent not in {"procurar", "instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    helper = supported_aur_helper(profile)
    if helper is None:
        return None

    if request.intent == "procurar":
        consulted_target = _preferred_search_query(target)
        consulted_targets = _search_queries_for_target(target)
        canonicalized = consulted_target != target
        if canonicalized:
            reason = (
                f"o alvo humano '{target}' foi refinado para a consulta AUR '{consulted_target}' "
                "para reduzir ruido de busca, sem promover isso a resolucao final de pacote."
            )
            source = "aur_search_query_normalized"
            status = "query_refined"
        else:
            reason = f"o alvo de busca AUR '{target}' foi consultado diretamente."
            source = "user_input_search_query"
            status = "query_direct"
        return TargetResolution(
            original_target=target,
            consulted_target=consulted_target,
            consulted_targets=consulted_targets,
            status=status,
            source=source,
            canonicalized=canonicalized,
            reason=reason,
        )

    if request.intent == "instalar":
        search_resolution = _search_resolution_candidates(target, helper, environ=environ)
        if isinstance(search_resolution, TargetResolution):
            if search_resolution.status == "not_found":
                source_mismatch = _native_source_mismatch(
                    target,
                    consulted_target=search_resolution.consulted_target,
                    consulted_targets=search_resolution.consulted_targets,
                    environ=environ,
                )
                if source_mismatch is not None:
                    return source_mismatch
            return search_resolution

        resolution = _resolution_from_candidates(
            target,
            search_resolution.candidates,
            consulted_target=search_resolution.consulted_target,
            consulted_targets=search_resolution.consulted_targets,
            source=search_resolution.source,
            no_match_status="not_found",
            no_match_reason=(
                f"nao encontrei um pacote AUR com correspondencia exata e confiavel para '{target}'. "
                "Use o nome real do pacote AUR ou refine o pedido."
            ),
            resolved_reason=(
                "o alvo humano '{target}' foi resolvido por busca controlada no AUR"
                f"{search_resolution.reason_suffix} para o pacote "
                "'{package_name}'."
            ),
        )
        if search_resolution.diagnostic_command:
            resolution = replace(
                resolution,
                diagnostic_command=search_resolution.diagnostic_command,
                diagnostic_exit_code=search_resolution.diagnostic_exit_code,
                diagnostic_stdout=search_resolution.diagnostic_stdout,
                diagnostic_stderr=search_resolution.diagnostic_stderr,
            )
        if resolution.status == "resolved":
            source_mismatch = _native_source_mismatch(
                target,
                lookup_target=resolution.resolved_target,
                consulted_target=resolution.consulted_target,
                consulted_targets=resolution.consulted_targets,
                environ=environ,
            )
            if source_mismatch is not None:
                return source_mismatch
        elif resolution.status == "not_found":
            source_mismatch = _native_source_mismatch(
                target,
                consulted_target=resolution.consulted_target,
                consulted_targets=resolution.consulted_targets,
                environ=environ,
            )
            if source_mismatch is not None:
                return source_mismatch
        return resolution

    foreign_resolution = _installed_resolution(
        target,
        query_flag="-Qm",
        source="pacman_foreign_list",
        no_match_status="absent",
        no_match_reason=(
            f"nao encontrei um pacote AUR instalado com correspondencia exata e confiavel para '{target}'."
        ),
        resolved_reason="o alvo humano '{target}' foi resolvido entre os pacotes foreign para '{package_name}'.",
        environ=environ,
    )
    if foreign_resolution.status == "absent":
        source_mismatch = _native_source_mismatch(
            target,
            consulted_target=foreign_resolution.consulted_target,
            consulted_targets=foreign_resolution.consulted_targets,
            environ=environ,
        )
        if source_mismatch is not None:
            return source_mismatch
    return foreign_resolution


def resolved_aur_target(request: SemanticRequest, resolution: TargetResolution | None) -> str:
    if resolution is not None and resolution.resolved_target:
        return resolution.resolved_target
    if request.intent == "procurar" and resolution is not None and resolution.consulted_target:
        return resolution.consulted_target
    if request.intent == "remover" and resolution is not None and resolution.consulted_target:
        return resolution.consulted_target
    return request.target


def aur_target_resolution_blocks(request: SemanticRequest, resolution: TargetResolution | None) -> bool:
    if resolution is None:
        return False
    if request.intent == "instalar":
        return resolution.status in {"ambiguous", "not_found", "unresolved", "source_mismatch"}
    if request.intent == "remover":
        return resolution.status in {"ambiguous", "unresolved", "source_mismatch"}
    return False


def _state_probe_for_mutation(target: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return ("pacman", "-Qm", target), ("pacman",)


def _mutation_target(request: SemanticRequest, target: str | None) -> str:
    if target is not None and target.strip():
        return target.strip()
    return request.target


def _route_notes(
    helper: str,
    *,
    observed_helpers: tuple[str, ...],
    out_of_contract_helpers: tuple[str, ...],
) -> tuple[str, ...]:
    supported_helpers = ", ".join(_SUPPORTED_AUR_HELPERS)
    notes = [
        "AUR entra como fonte explicita de terceiro nesta rodada.",
        f"helpers aceitos nesta rodada: {supported_helpers}.",
        f"helper escolhido para esta rota: {helper} (primeiro helper suportado observado na ordem do contrato).",
        "busca pode refinar a consulta para a forma package-like quando isso reduz ruido sem resolver o pacote automaticamente.",
        "mutacao usa resolved_target apenas quando a correspondencia exata fecha de forma confiavel.",
        "state probe via pacman -Qm para confirmar pacote foreign.",
        "o pedido explicito de AUR nao sofre fallback para host_package oficial.",
    ]
    if observed_helpers:
        notes.append(f"helpers AUR observados no host: {', '.join(observed_helpers)}.")
    if out_of_contract_helpers:
        notes.append(f"helpers AUR observados fora do contrato: {', '.join(out_of_contract_helpers)}.")
    return tuple(notes)


def build_aur_candidate(
    request: SemanticRequest,
    profile: HostProfile,
    *,
    target: str | None = None,
) -> ExecutionRoute | None:
    if request.domain_kind != "host_package" or request.requested_source != "aur":
        return None

    helper = supported_aur_helper(profile)
    if helper is None:
        return None

    mutation_target = _mutation_target(request, target)
    notes = _route_notes(
        helper,
        observed_helpers=profile.observed_third_party_package_tools,
        out_of_contract_helpers=observed_out_of_contract_aur_helpers(profile),
    )

    if request.intent == "procurar":
        return ExecutionRoute(
            route_name="aur.procurar",
            action_name="procurar",
            backend_name=helper,
            command=(helper, "-Ss", "--aur", "--", mutation_target),
            required_commands=(helper,),
            implemented=True,
            requires_privilege_escalation=False,
            notes=notes,
        )

    if request.intent == "instalar":
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
        return ExecutionRoute(
            route_name="aur.instalar",
            action_name="instalar",
            backend_name=helper,
            command=(helper, "-S", "--aur", "--needed", "--noconfirm", "--", mutation_target),
            required_commands=(helper,),
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=True,
            interactive_passthrough=True,
            notes=notes
            + (
                "instalacao real via AUR entrega stdin/stdout/stderr ao helper para revisao e build interativos.",
            ),
        )

    if request.intent == "remover":
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(mutation_target)
        return ExecutionRoute(
            route_name="aur.remover",
            action_name="remover",
            backend_name=helper,
            command=(helper, "-Rns", "--noconfirm", "--", mutation_target),
            required_commands=(helper,),
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=True,
            notes=notes,
        )

    return ExecutionRoute(
        route_name=f"aur.{request.intent}",
        action_name=request.intent,
        backend_name=helper,
        required_commands=(helper,),
        implemented=False,
        requires_privilege_escalation=False,
        notes=("acao ainda nao aberta para a rota AUR nesta release.",),
    )


def aur_search_has_no_results(stdout: str, stderr: str, returncode: int) -> bool:
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if any(marker in combined_output for marker in _AUR_NO_RESULTS_MARKERS):
        return True
    return returncode == 0 and not stdout.strip()


def aur_mutation_reports_no_matching_package(stdout: str, stderr: str) -> bool:
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if not combined_output:
        return False
    return any(marker in combined_output for marker in _AUR_NOT_FOUND_MARKERS)

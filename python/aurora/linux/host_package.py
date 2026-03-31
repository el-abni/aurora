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

from .backends import (
    build_arch_search_route,
    build_debian_search_route,
    build_fedora_search_route,
    build_opensuse_search_route,
)

NO_RESULTS_MARKERS = (
    "no packages found",
    "no matches found",
    "no matching items found",
    "nenhum pacote encontrado",
    "nenhuma correspondencia encontrada",
    "nenhum item correspondente encontrado",
)
_DNF_ARCH_SUFFIXES = {"aarch64", "i686", "noarch", "ppc64le", "s390x", "x86_64"}


@dataclass(frozen=True)
class _HostPackageResolutionCandidate:
    package_name: str


@dataclass(frozen=True)
class _HostPackageSearchResolution:
    candidates: tuple[_HostPackageResolutionCandidate, ...]
    source: str
    reason_suffix: str = ""


def _planned_backend_label(intent: str, profile: HostProfile) -> str:
    backends = set(profile.package_backends)
    if profile.linux_family == "arch":
        if intent == "procurar":
            if "pacman" in backends:
                return "pacman"
            if "paru" in backends:
                return "paru"
            return "pacman"
        return "paru + pacman" if "paru" in backends else "sudo + pacman"
    if profile.linux_family == "debian":
        return "apt-cache" if intent == "procurar" else "sudo + apt-get"
    if profile.linux_family == "opensuse":
        return "zypper" if intent == "procurar" else "sudo + zypper"
    return "dnf" if intent == "procurar" else "sudo + dnf"


def _planned_mutation_command(intent: str, target: str, profile: HostProfile) -> tuple[str, ...]:
    if profile.linux_family == "arch":
        if intent == "instalar":
            if "paru" in set(profile.package_backends):
                return ("paru", "-S", "--needed", "--", target)
            return ("sudo", "pacman", "-S", "--needed", "--", target)
        if "paru" in set(profile.package_backends):
            return ("paru", "-Rns", "--", target)
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


def _state_probe_for_mutation(target: str, profile: HostProfile) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if profile.linux_family == "arch":
        return ("pacman", "-Q", "--", target), ("pacman",)
    if profile.linux_family == "debian":
        return ("dpkg", "-s", target), ("dpkg",)
    return ("rpm", "-q", target), ("rpm",)


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


def _search_queries_for_target(target: str) -> tuple[str, ...]:
    queries: list[str] = []
    for query in (target.strip(), _package_search_query(target), _human_search_query(target)):
        if query and query not in queries:
            queries.append(query)
    return tuple(queries)


def _candidate_label(candidate: _HostPackageResolutionCandidate) -> str:
    return candidate.package_name


def _candidate_matches_target(candidate: _HostPackageResolutionCandidate, target_key: str) -> bool:
    return _normalized_resolution_key(candidate.package_name) == target_key


def _required_search_backend_available(
    required_commands: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> bool:
    path = None if environ is None else environ.get("PATH", os.environ.get("PATH"))
    return all(shutil.which(name, path=path) is not None for name in required_commands)


def _run_search_command(
    command: tuple[str, ...],
    *,
    environ: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False, env=environ)


def _strip_dnf_arch_suffix(package_name: str) -> str:
    base, separator, suffix = package_name.rpartition(".")
    if separator and suffix in _DNF_ARCH_SUFFIXES:
        return base
    return package_name


def _package_name_from_search_line(line: str, backend_name: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""

    if backend_name in {"pacman", "paru"}:
        if line[:1].isspace():
            return ""
        token = stripped.split()[0]
        if "/" in token:
            return token.split("/", 1)[1]
        return token

    if backend_name == "apt-cache":
        if " - " not in stripped:
            return ""
        return stripped.split(" - ", 1)[0].strip()

    if backend_name == "dnf":
        if " : " not in stripped:
            return ""
        token = stripped.split(" : ", 1)[0].strip().split()[0]
        return _strip_dnf_arch_suffix(token)

    if backend_name == "zypper":
        if "|" not in stripped:
            return ""
        parts = [part.strip() for part in stripped.split("|")]
        if len(parts) < 3:
            return ""
        package_name = parts[1].strip()
        if package_name.lower() in {"name", "package"}:
            return ""
        return package_name

    return ""


def _parse_resolution_candidates(
    output: str,
    backend_name: str,
) -> tuple[_HostPackageResolutionCandidate, ...]:
    candidates: list[_HostPackageResolutionCandidate] = []
    seen: set[str] = set()
    for raw_line in output.splitlines():
        package_name = _package_name_from_search_line(raw_line, backend_name)
        if not package_name or package_name in seen:
            continue
        candidates.append(_HostPackageResolutionCandidate(package_name=package_name))
        seen.add(package_name)
    return tuple(candidates)


def _merge_resolution_candidates(
    candidates: tuple[_HostPackageResolutionCandidate, ...],
    new_candidates: tuple[_HostPackageResolutionCandidate, ...],
) -> tuple[_HostPackageResolutionCandidate, ...]:
    merged = {candidate.package_name: candidate for candidate in candidates}
    for candidate in new_candidates:
        merged[candidate.package_name] = candidate
    return tuple(merged.values())


def _search_resolution_candidates(
    target: str,
    profile: HostProfile,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | _HostPackageSearchResolution:
    candidates: tuple[_HostPackageResolutionCandidate, ...] = ()
    original_query = target.strip()
    successful_queries: list[str] = []
    observed_search_output = False
    backend_name = ""

    for query in _search_queries_for_target(target):
        search_route = build_host_package_route("procurar", query, profile)
        if search_route is None:
            return TargetResolution(
                original_target=target,
                status="unresolved",
                source="host_package_search",
                reason="nao encontrei rota de busca adequada para resolver este pacote do host.",
            )
        backend_name = search_route.backend_name
        if not _required_search_backend_available(search_route.required_commands, environ=environ):
            return TargetResolution(
                original_target=target,
                status="unresolved",
                source="host_package_search",
                reason=(
                    f"nao consegui resolver o alvo do host '{target}' porque o backend de busca "
                    f"'{search_route.backend_name}' nao esta disponivel."
                ),
            )

        proc = _run_search_command(search_route.command, environ=environ)
        if search_has_no_results(proc.stdout, proc.stderr, proc.returncode):
            continue
        if proc.returncode != 0:
            return TargetResolution(
                original_target=target,
                status="unresolved",
                source="host_package_search",
                reason=(
                    f"nao consegui resolver o alvo do host '{target}' porque a busca controlada "
                    f"no backend '{search_route.backend_name}' falhou operacionalmente."
                ),
            )

        if proc.stdout.strip():
            observed_search_output = True

        parsed_candidates = _parse_resolution_candidates(proc.stdout, search_route.backend_name)
        candidates = _merge_resolution_candidates(candidates, parsed_candidates)
        successful_queries.append(query)

    if observed_search_output and not candidates:
        return TargetResolution(
            original_target=target,
            status="unresolved",
            source="host_package_search",
            reason=(
                f"nao consegui interpretar candidatos confiaveis para '{target}' a partir da busca "
                f"do backend '{backend_name or 'host_package'}'."
            ),
        )

    if successful_queries:
        normalized_queries = tuple(query for query in successful_queries if query != original_query)
        if normalized_queries:
            normalized_label = "', '".join(normalized_queries)
            source = "host_package_search_normalized_query"
            reason_suffix = f" usando a consulta humana normalizada '{normalized_label}'"
        else:
            source = "host_package_search"
            reason_suffix = ""
        return _HostPackageSearchResolution(
            candidates=candidates,
            source=source,
            reason_suffix=reason_suffix,
        )

    return TargetResolution(
        original_target=target,
        status="not_found",
        source="host_package_search",
        reason=(
            f"nao encontrei um pacote do host com correspondencia exata e confiavel para '{target}'. "
            "Use o nome real do pacote ou refine o pedido."
        ),
    )


def _resolution_from_candidates(
    target: str,
    candidates: tuple[_HostPackageResolutionCandidate, ...],
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
                f"encontrei multiplos pacotes do host igualmente fortes para '{target}': "
                f"{', '.join(labels)}. Use o nome real do pacote para prosseguir."
            ),
        )

    match = matches[0]
    return TargetResolution(
        original_target=target,
        resolved_target=match.package_name,
        status="resolved",
        source=source,
        canonicalized=match.package_name != target,
        candidates=(_candidate_label(match),),
        reason=resolved_reason.format(target=target, package_name=match.package_name),
    )


def resolve_host_package_target(
    request: SemanticRequest,
    profile: HostProfile | None,
    *,
    environ: dict[str, str] | None = None,
) -> TargetResolution | None:
    if request.domain_kind != "host_package" or request.intent not in {"instalar", "remover"}:
        return None

    target = request.target.strip()
    if not target:
        return None

    if " " not in target:
        return TargetResolution(
            original_target=target,
            resolved_target=target,
            status="direct",
            source="user_input_package_name",
            canonicalized=False,
            reason="o alvo ja parecia um nome de pacote utilizavel e foi usado diretamente.",
        )

    if profile is None or profile.linux_family not in {"arch", "debian", "fedora", "opensuse"}:
        return None

    search_resolution = _search_resolution_candidates(target, profile, environ=environ)
    if isinstance(search_resolution, TargetResolution):
        return search_resolution

    return _resolution_from_candidates(
        target,
        search_resolution.candidates,
        source=search_resolution.source,
        no_match_status="not_found",
        no_match_reason=(
            f"nao encontrei um pacote do host com correspondencia exata e confiavel para '{target}'. "
            "Use o nome real do pacote ou refine o pedido."
        ),
        resolved_reason=(
            "o alvo humano '{target}' foi resolvido por busca controlada do host"
            f"{search_resolution.reason_suffix} para o pacote "
            "'{package_name}'."
        ),
    )


def build_host_package_route(intent: str, target: str, profile: HostProfile) -> ExecutionRoute | None:
    if profile.linux_family == "arch" and intent == "procurar":
        return build_arch_search_route(target, profile)
    if profile.linux_family == "debian" and intent == "procurar":
        return build_debian_search_route(target, profile)
    if profile.linux_family == "fedora" and intent == "procurar":
        return build_fedora_search_route(target, profile)
    if profile.linux_family == "opensuse" and intent == "procurar":
        return build_opensuse_search_route(target, profile)
    if profile.linux_family not in {"arch", "debian", "fedora", "opensuse"}:
        return None

    if intent in {"instalar", "remover"}:
        state_probe_command, state_probe_required_commands = _state_probe_for_mutation(target, profile)
        backends = set(profile.package_backends)
        if profile.linux_family == "arch":
            required_commands = ("paru", "pacman") if "paru" in backends else ("sudo", "pacman")
        elif profile.linux_family == "debian":
            required_commands = ("sudo", "apt-get")
        elif profile.linux_family == "opensuse":
            required_commands = ("sudo", "zypper")
        else:
            required_commands = ("sudo", "dnf")
        return ExecutionRoute(
            route_name=f"host_package.{intent}",
            action_name=intent,
            backend_name=_planned_backend_label(intent, profile),
            command=_planned_mutation_command(intent, target, profile),
            required_commands=required_commands,
            state_probe_command=state_probe_command,
            state_probe_required_commands=state_probe_required_commands,
            implemented=True,
            requires_privilege_escalation=True,
            notes=("mutacao do host exige probe antes e depois da execucao",),
        )

    return None


def search_has_no_results(stdout: str, stderr: str, returncode: int) -> bool:
    if returncode not in {0, 1, 104}:
        return False
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if not combined_output:
        return True
    return any(marker in combined_output for marker in NO_RESULTS_MARKERS)


def mutation_reports_no_matching_package(stdout: str, stderr: str) -> bool:
    combined_output = "\n".join(part.strip().lower() for part in (stdout, stderr) if part.strip())
    if not combined_output:
        return False
    markers = (
        "unable to locate package",
        "no match for argument",
        "no matching items found",
        "package not found",
        "nenhum pacote encontrado",
        "nenhuma correspondencia encontrada",
        "no packages found",
    )
    return any(marker in combined_output for marker in markers)

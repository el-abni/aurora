from __future__ import annotations

from aurora.contracts.execution import ExecutionRoute
from aurora.contracts.host import HostProfile

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

from __future__ import annotations

import os

from aurora.contracts.host import HostProfile

from .mutability import detect_mutability
from .probes import detect_available_commands, read_os_release, split_like

HOST_PACKAGE_BACKENDS = ("pacman", "apt-cache", "apt-get", "dnf", "zypper")
OBSERVED_PACKAGE_TOOLS = ("flatpak", "rpm-ostree")
OBSERVED_THIRD_PARTY_PACKAGE_TOOLS = ("paru", "yay", "pikaur")
ARCH_FAMILY_IDS = {"arch", "archlinux", "artix", "cachyos", "endeavouros", "manjaro"}
DEBIAN_FAMILY_IDS = {"debian", "ubuntu", "linuxmint", "pop", "neon", "raspbian", "elementary"}
FEDORA_FAMILY_IDS = {"fedora", "rhel", "centos", "rocky", "almalinux", "nobara", "bazzite", "bluefin", "aurora"}
OPENSUSE_FAMILY_IDS = {"opensuse", "opensuse-leap", "opensuse-tumbleweed", "opensuse-microos", "sles", "sled", "microos", "suse"}


def _detect_linux_family(distro_id: str, distro_like: tuple[str, ...]) -> str:
    tokens = {distro_id, *distro_like}
    if tokens & ARCH_FAMILY_IDS:
        return "arch"
    if tokens & DEBIAN_FAMILY_IDS:
        return "debian"
    if tokens & FEDORA_FAMILY_IDS:
        return "fedora"
    if tokens & OPENSUSE_FAMILY_IDS:
        return "opensuse"
    return "unknown"


def detect_host_profile(environ: dict[str, str] | None = None) -> HostProfile:
    resolved_environ = os.environ if environ is None else environ
    os_release = read_os_release(resolved_environ)
    distro_id = os_release.get("ID", "").strip().lower()
    distro_like = split_like(os_release.get("ID_LIKE", ""))
    variant_id = os_release.get("VARIANT_ID", "").strip().lower()
    name = os_release.get("NAME", "").strip().lower()
    pretty_name = os_release.get("PRETTY_NAME", "").strip().lower()
    linux_family = _detect_linux_family(distro_id, distro_like)
    mutability = detect_mutability(distro_id, variant_id, name, pretty_name, resolved_environ)
    package_backends = detect_available_commands(HOST_PACKAGE_BACKENDS, resolved_environ)
    observed_package_tools = detect_available_commands(OBSERVED_PACKAGE_TOOLS, resolved_environ)
    observed_third_party_package_tools = detect_available_commands(
        OBSERVED_THIRD_PARTY_PACKAGE_TOOLS,
        resolved_environ,
    )

    if mutability == "atomic":
        support_tier = "limited"
    elif linux_family in {"arch", "debian", "fedora"}:
        support_tier = "tier_1"
    elif linux_family == "opensuse":
        support_tier = "tier_2"
    else:
        support_tier = "out_of_scope"

    return HostProfile(
        linux_family=linux_family,
        distro_id=distro_id,
        distro_like=distro_like,
        variant_id=variant_id,
        mutability=mutability,
        package_backends=package_backends,
        observed_package_tools=observed_package_tools,
        observed_third_party_package_tools=observed_third_party_package_tools,
        support_tier=support_tier,
    )

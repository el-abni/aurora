from __future__ import annotations

HOST_PACKAGE_BACKENDS = ("pacman", "apt-cache", "apt-get", "dnf", "zypper")
OBSERVED_PACKAGE_TOOLS = ("flatpak", "rpm-ostree")
OBSERVED_THIRD_PARTY_PACKAGE_TOOLS = ("paru", "yay", "pikaur")
OBSERVED_ENVIRONMENT_TOOLS = ("toolbox",)

ARCH_FAMILY_IDS = {"arch", "archlinux", "artix", "cachyos", "endeavouros", "manjaro"}
DEBIAN_FAMILY_IDS = {"debian", "ubuntu", "linuxmint", "pop", "neon", "raspbian", "elementary"}
FEDORA_FAMILY_IDS = {
    "fedora",
    "rhel",
    "centos",
    "rocky",
    "almalinux",
    "nobara",
    "bazzite",
    "bluefin",
    "aurora",
}
OPENSUSE_FAMILY_IDS = {
    "opensuse",
    "opensuse-leap",
    "opensuse-tumbleweed",
    "opensuse-microos",
    "sles",
    "sled",
    "microos",
    "suse",
}


def detect_linux_family(distro_id: str, distro_like: tuple[str, ...]) -> str:
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


def support_tier_for_profile(linux_family: str, mutability: str) -> str:
    if mutability == "atomic":
        return "limited"
    if linux_family in {"arch", "debian", "fedora"}:
        return "tier_1"
    if linux_family == "opensuse":
        return "tier_2"
    return "out_of_scope"

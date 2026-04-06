from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HostProfile:
    linux_family: str
    distro_id: str
    distro_like: tuple[str, ...]
    variant_id: str
    mutability: str
    package_backends: tuple[str, ...]
    observed_package_tools: tuple[str, ...]
    observed_third_party_package_tools: tuple[str, ...]
    support_tier: str
    observed_environment_tools: tuple[str, ...] = ()
    observed_toolbox_environments: tuple[str, ...] = ()
    observed_distrobox_environments: tuple[str, ...] = ()

    @property
    def observed_immutable_surfaces(self) -> tuple[str, ...]:
        if self.mutability != "atomic":
            return ()

        surfaces: list[str] = []
        if "flatpak" in self.observed_package_tools:
            surfaces.append("flatpak")
        if "rpm-ostree" in self.observed_package_tools:
            surfaces.append("rpm-ostree")
        if self.observed_toolbox_environments:
            surfaces.append(f"toolbox[{','.join(self.observed_toolbox_environments)}]")
        elif "toolbox" in self.observed_environment_tools:
            surfaces.append("toolbox")
        if self.observed_distrobox_environments:
            surfaces.append(f"distrobox[{','.join(self.observed_distrobox_environments)}]")
        elif "distrobox" in self.observed_environment_tools:
            surfaces.append("distrobox")
        return tuple(surfaces)

    @property
    def linux_family_label(self) -> str:
        return "desconhecida" if self.linux_family == "unknown" else self.linux_family

    @property
    def mutability_label(self) -> str:
        return "Atomic" if self.mutability == "atomic" else "mutavel"

    @property
    def support_tier_label(self) -> str:
        if self.support_tier == "tier_1":
            return "Tier 1 canonico"
        if self.support_tier == "tier_2":
            return "Tier 2 util contido"
        if self.support_tier == "limited":
            return "suporte limitado"
        return "fora do recorte"

    @property
    def compatibility_frontier_label(self) -> str:
        if self.mutability == "atomic":
            if "rpm-ostree" in self.observed_package_tools:
                return "imutavel com rpm-ostree explicito"
            if self.observed_immutable_surfaces:
                return "imutavel com superficies explicitas limitadas"
            return "imutavel sem superficie adequada observada"
        if self.support_tier == "tier_1":
            return "suportado agora"
        if self.support_tier == "tier_2":
            return "suportado contido"
        return "fora do recorte"

    @property
    def package_backends_label(self) -> str:
        return ", ".join(self.package_backends) if self.package_backends else "-"

    @property
    def observed_package_tools_label(self) -> str:
        if not self.observed_package_tools:
            return "-"
        return ", ".join(self.observed_package_tools)

    @property
    def observed_third_party_package_tools_label(self) -> str:
        if not self.observed_third_party_package_tools:
            return "-"
        return ", ".join(self.observed_third_party_package_tools)

    @property
    def observed_environment_tools_label(self) -> str:
        if not self.observed_environment_tools:
            return "-"
        return ", ".join(self.observed_environment_tools)

    @property
    def observed_toolbox_environments_label(self) -> str:
        if not self.observed_toolbox_environments:
            return "-"
        return ", ".join(self.observed_toolbox_environments)

    @property
    def observed_distrobox_environments_label(self) -> str:
        if not self.observed_distrobox_environments:
            return "-"
        return ", ".join(self.observed_distrobox_environments)

    @property
    def observed_immutable_surfaces_label(self) -> str:
        if not self.observed_immutable_surfaces:
            return "-"
        return ", ".join(self.observed_immutable_surfaces)

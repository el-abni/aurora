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
    support_tier: str

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
            return "bloqueado por politica"
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

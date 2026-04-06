from __future__ import annotations

from aurora.contracts.host import HostProfile


def observed_immutable_surface_signals(profile: HostProfile | None) -> tuple[str, ...]:
    if profile is None or profile.mutability != "atomic":
        return ()

    surfaces = profile.observed_immutable_surfaces
    signals = [
        "immutable_host:true",
        (
            f"immutable_observed_surfaces:{','.join(surfaces)}"
            if surfaces
            else "immutable_observed_surfaces:-"
        ),
        (
            f"immutable_toolbox_environments:{','.join(profile.observed_toolbox_environments)}"
            if profile.observed_toolbox_environments
            else "immutable_toolbox_environments:-"
        ),
        (
            f"immutable_distrobox_environments:{','.join(profile.observed_distrobox_environments)}"
            if profile.observed_distrobox_environments
            else "immutable_distrobox_environments:-"
        ),
        (
            "immutable_rpm_ostree_observed:true"
            if "rpm-ostree" in profile.observed_package_tools
            else "immutable_rpm_ostree_observed:false"
        ),
        (
            "immutable_flatpak_observed:true"
            if "flatpak" in profile.observed_package_tools
            else "immutable_flatpak_observed:false"
        ),
    ]
    return tuple(signals)


def immutable_surface_selection_reason(profile: HostProfile) -> str:
    surfaces = profile.observed_immutable_surfaces
    if not surfaces:
        return (
            "o host foi detectado como imutavel, mas nao observei uma superficie operacional adequada "
            "entre flatpak, toolbox, distrobox ou rpm-ostree."
        )
    return (
        "o host foi detectado como imutavel; as superficies atualmente observadas foram "
        f"{', '.join(surfaces)}."
    )


def host_package_block_reason(profile: HostProfile) -> tuple[str, str]:
    if profile.mutability == "atomic":
        base_reason = immutable_surface_selection_reason(profile)
        reason = (
            f"{base_reason} Um pedido nu de host_package nao permite inferir com honestidade entre "
            "flatpak, toolbox, distrobox, rpm-ostree ou bloqueio; peça a superficie explicitamente."
        )
        message = f"❌ {reason}"
        return reason, message

    reason = "a familia Linux deste host ficou fora do recorte atual de host_package."
    message = "❌ a familia Linux deste host ficou fora do recorte atual de host_package."
    return reason, message

from __future__ import annotations

import os

from aurora.contracts.host import HostProfile

from .mutability import detect_mutability
from .distrobox import observe_distrobox_environments
from .probes import detect_available_commands, read_os_release, split_like
from .profile_facts import (
    HOST_PACKAGE_BACKENDS,
    OBSERVED_ENVIRONMENT_TOOLS,
    OBSERVED_PACKAGE_TOOLS,
    OBSERVED_THIRD_PARTY_PACKAGE_TOOLS,
    detect_linux_family,
    support_tier_for_profile,
)
from .toolbox import observe_toolbox_environments


def detect_host_profile(environ: dict[str, str] | None = None) -> HostProfile:
    resolved_environ = os.environ if environ is None else environ
    os_release = read_os_release(resolved_environ)
    distro_id = os_release.get("ID", "").strip().lower()
    distro_like = split_like(os_release.get("ID_LIKE", ""))
    variant_id = os_release.get("VARIANT_ID", "").strip().lower()
    name = os_release.get("NAME", "").strip().lower()
    pretty_name = os_release.get("PRETTY_NAME", "").strip().lower()
    linux_family = detect_linux_family(distro_id, distro_like)
    mutability = detect_mutability(distro_id, variant_id, name, pretty_name, resolved_environ)
    package_backends = detect_available_commands(HOST_PACKAGE_BACKENDS, resolved_environ)
    observed_package_tools = detect_available_commands(OBSERVED_PACKAGE_TOOLS, resolved_environ)
    observed_environment_tools = detect_available_commands(OBSERVED_ENVIRONMENT_TOOLS, resolved_environ)
    observed_third_party_package_tools = detect_available_commands(
        OBSERVED_THIRD_PARTY_PACKAGE_TOOLS,
        resolved_environ,
    )
    observed_toolbox_environments = observe_toolbox_environments(resolved_environ)
    observed_distrobox_environments = observe_distrobox_environments(resolved_environ)
    support_tier = support_tier_for_profile(linux_family, mutability)

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
        observed_environment_tools=observed_environment_tools,
        observed_toolbox_environments=observed_toolbox_environments,
        observed_distrobox_environments=observed_distrobox_environments,
    )

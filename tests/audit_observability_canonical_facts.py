#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.render import render_decision_record
from support import (
    setup_copr_testbed,
    setup_flatpak_testbed,
    setup_ppa_testbed,
    setup_rpm_ostree_testbed,
    setup_toolbox_testbed,
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def build_flatpak_install_ubuntu(root: Path) -> dict[str, str]:
    env, _state_file = setup_flatpak_testbed(
        root,
        distro_id="ubuntu",
        distro_like="debian",
        repo_apps=("com.obsproject.Studio|OBS Studio",),
        name="Ubuntu",
    )
    return env


def build_toolbox_search_atomic(root: Path) -> dict[str, str]:
    env, _state_files = setup_toolbox_testbed(
        root,
        host_distro_id="bazzite",
        host_distro_like="fedora",
        host_name="Bazzite",
        toolboxes=(
            {
                "name": "devbox",
                "family": "fedora",
                "distro_id": "fedora",
                "distro_like": "fedora",
                "display_name": "Fedora Toolbox",
                "repo_packages": ("ripgrep|ripgrep",),
            },
        ),
    )
    return env


def build_rpm_ostree_install_atomic(root: Path) -> dict[str, str]:
    env, _state_files = setup_rpm_ostree_testbed(
        root,
        host_distro_id="bazzite",
        host_distro_like="fedora",
        repo_packages=("htop|htop",),
        include_flatpak=True,
        toolbox_environments=("devbox",),
        distrobox_environments=("workbox",),
        host_name="Bazzite",
    )
    return env


def build_copr_install_fedora(root: Path) -> dict[str, str]:
    env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
        root,
        copr_repo="atim/obs-studio",
        repo_packages=("obs-studio|OBS Studio",),
    )
    return env


def build_ppa_install_ubuntu(root: Path) -> dict[str, str]:
    env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
        root,
        ppa_coordinate="ppa:obsproject/obs-studio",
        repo_packages=("obs-studio|OBS Studio",),
    )
    return env


def lookup_path(payload: object, dotted_path: str) -> object:
    current = payload
    for part in dotted_path.split("."):
        if isinstance(current, list):
            current = current[int(part)]
            continue
        if not isinstance(current, dict):
            raise KeyError(dotted_path)
        current = current[part]
    return current


def stripped_record(text: str, env: dict[str, str]):
    record = plan_text(text, environ=env)
    ensure(record.policy is not None, "cenario factual precisa produzir policy")
    stripped_policy = replace(record.policy, trust_signals=())
    return replace(record, policy=stripped_policy)


def assert_scenario(
    scenario_id: str,
    builder,
    phrase: str,
    payload_path: str,
    expected_value,
    render_snippet: str,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env = builder(root)
        record = stripped_record(phrase, env)
        payload = decision_record_to_dict(record)
        rendered = render_decision_record(record)
        ensure(payload["policy"]["trust_signals"] == [], f"{scenario_id} precisa esvaziar trust_signals no espelho legado")
        ensure(
            lookup_path(payload, payload_path) == expected_value,
            f"{scenario_id} divergiu no payload canonico {payload_path}",
        )
        ensure(render_snippet in rendered, f"{scenario_id} divergiu no render canonico")
        ok(f"observability canonica {scenario_id} alinhada")


def main() -> int:
    assert_scenario(
        "flatpak",
        build_flatpak_install_ubuntu,
        "instalar obs studio no flatpak",
        "facts.policy.flatpak.effective_remote",
        "flathub",
        "flatpak_effective_remote: flathub",
    )
    assert_scenario(
        "toolbox",
        build_toolbox_search_atomic,
        "procurar ripgrep na toolbox devbox",
        "facts.policy.toolbox.resolved_environment",
        "devbox",
        "toolbox_resolved_environment: devbox",
    )
    assert_scenario(
        "rpm_ostree",
        build_rpm_ostree_install_atomic,
        "instalar htop no rpm-ostree",
        "facts.policy.rpm_ostree.status",
        "observed",
        "rpm_ostree_status:       observed",
    )
    assert_scenario(
        "copr",
        build_copr_install_fedora,
        "instalar obs-studio do copr atim/obs-studio",
        "facts.policy.copr.repository_state",
        "disabled",
        "copr_repository_state:   disabled",
    )
    assert_scenario(
        "ppa",
        build_ppa_install_ubuntu,
        "instalar obs-studio do ppa ppa:obsproject/obs-studio",
        "facts.policy.ppa.capability",
        "add_apt_repository_observed",
        "ppa_capability:          add_apt_repository_observed",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import (
    setup_copr_testbed,
    setup_flatpak_testbed,
    setup_host_package_testbed,
    setup_ppa_testbed,
    setup_rpm_ostree_testbed,
    setup_toolbox_testbed,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "factual_baseline_v0_7_0_cut3.json"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def build_host_package_search_debian(root: Path) -> dict[str, str]:
    env, _state_file = setup_host_package_testbed(
        root,
        family="debian",
        distro_id="ubuntu",
        distro_like="debian",
        repo_packages=("firefox|Firefox",),
    )
    return env


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


BUILDERS = {
    "host_package_search_debian": build_host_package_search_debian,
    "flatpak_install_ubuntu": build_flatpak_install_ubuntu,
    "toolbox_search_atomic": build_toolbox_search_atomic,
    "rpm_ostree_install_atomic": build_rpm_ostree_install_atomic,
    "copr_install_fedora": build_copr_install_fedora,
    "ppa_install_ubuntu": build_ppa_install_ubuntu,
}


def run_scenario(builder_name: str, phrase: str) -> tuple[dict[str, object], str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env = BUILDERS[builder_name](root)
        payload = decision_record_to_dict(plan_text(phrase, environ=env))
        rendered = render_dev_report(phrase, environ=env)
    return payload, rendered


def assert_scenario(scenario: dict[str, object]) -> None:
    builder_name = str(scenario["builder"])
    phrase = str(scenario["phrase"])
    payload, rendered = run_scenario(builder_name, phrase)

    for path, expected in dict(scenario["payload_expect"]).items():
        actual = lookup_path(payload, path)
        ensure(
            actual == expected,
            f"baseline factual divergiu em {scenario['id']} -> {path}: esperado={expected!r} atual={actual!r}",
        )
    for snippet in list(scenario["render_expect"]):
        ensure(
            str(snippet) in rendered,
            f"baseline render divergiu em {scenario['id']}: faltou trecho {snippet!r}",
        )
    ok(f"baseline factual {scenario['id']} alinhado")


def main() -> int:
    fixture = read_json(FIXTURE_PATH)
    scenarios = list(fixture["scenarios"])
    ensure(scenarios, "fixture factual precisa listar cenarios")
    for scenario in scenarios:
        assert_scenario(scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

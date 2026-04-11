#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from aurora.install.planner import plan_text
from aurora.local_model.contracts import LocalModelRequest, LocalModelResponse
from aurora.observability.decision_record import decision_record_to_dict
from support import setup_host_package_testbed, setup_rpm_ostree_testbed

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "local_model_eval_baseline_v0_7_0_cut4.json"


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


def build_sensitive_remove_arch(root: Path) -> dict[str, str]:
    env, _state_file = setup_host_package_testbed(
        root,
        family="arch",
        distro_id="cachyos",
        distro_like="arch",
        repo_packages=("sudo|sudo",),
        installed_packages=("sudo",),
    )
    return env


def build_atomic_surface_clarify(root: Path) -> dict[str, str]:
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


def build_ambiguous_host_package(root: Path) -> dict[str, str]:
    env, _state_file = setup_host_package_testbed(
        root,
        family="debian",
        distro_id="ubuntu",
        distro_like="debian",
        repo_packages=("obs-studio|OBS Studio", "obs_studio|OBS Studio underscore"),
    )
    return env


BUILDERS = {
    "host_package_search_debian": build_host_package_search_debian,
    "sensitive_remove_arch": build_sensitive_remove_arch,
    "atomic_surface_clarify": build_atomic_surface_clarify,
    "ambiguous_host_package": build_ambiguous_host_package,
}


class FixtureLocalModelProvider:
    provider_name = "fixture_local_model"

    def __init__(self, responses: dict[tuple[str, str], str]) -> None:
        self._responses = responses

    def assist(self, request: LocalModelRequest) -> LocalModelResponse:
        phrase = str(request.facts["request"]["original_text"])
        capability = request.capability
        text = self._responses[(phrase, capability)]
        return LocalModelResponse(capability=capability, text=text)


def run_scenario(
    builder_name: str,
    phrase: str,
    provider: FixtureLocalModelProvider,
) -> tuple[dict[str, object], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env = BUILDERS[builder_name](root)
        record = plan_text(phrase, environ=env)
        payload_off = decision_record_to_dict(record, model_mode="model_off", environ=env)
        payload_on = decision_record_to_dict(
            record,
            model_mode="model_on",
            model_provider=provider,
            environ=env,
        )
    return payload_off, payload_on


def assert_scenario(
    scenario: dict[str, object],
    provider: FixtureLocalModelProvider,
) -> None:
    builder_name = str(scenario["builder"])
    phrase = str(scenario["phrase"])
    payload_off, payload_on = run_scenario(builder_name, phrase, provider)

    for path, expected in dict(scenario["kernel_expect"]).items():
        actual_off = lookup_path(payload_off, path)
        actual_on = lookup_path(payload_on, path)
        ensure(
            actual_off == expected,
            f"kernel model_off divergiu em {scenario['id']} -> {path}: esperado={expected!r} atual={actual_off!r}",
        )
        ensure(
            actual_on == expected,
            f"kernel model_on divergiu em {scenario['id']} -> {path}: esperado={expected!r} atual={actual_on!r}",
        )

    ensure(
        lookup_path(payload_off, "facts.local_model.mode") == "model_off",
        f"{scenario['id']} precisa manter model_off explicito",
    )
    ensure(
        lookup_path(payload_off, "facts.local_model.status") == "disabled",
        f"{scenario['id']} precisa manter model_off desabilitado",
    )
    ensure(
        lookup_path(payload_on, "facts.local_model.mode") == "model_on",
        f"{scenario['id']} precisa expor model_on",
    )
    ensure(
        lookup_path(payload_on, "facts.local_model.status") == "completed",
        f"{scenario['id']} precisa completar model_on com provider fixture",
    )
    ensure(
        lookup_path(payload_off, "facts.local_model.requested_capability")
        == scenario["requested_capability"],
        f"{scenario['id']} precisa selecionar a capacidade canonica em model_off",
    )
    ensure(
        lookup_path(payload_on, "facts.local_model.requested_capability")
        == scenario["requested_capability"],
        f"{scenario['id']} precisa selecionar a capacidade canonica em model_on",
    )
    ensure(
        lookup_path(payload_off, "facts.local_model.output_text") == "",
        f"{scenario['id']} precisa manter model_off sem texto produzido",
    )
    ensure(
        str(scenario["model_on_contains"]) in lookup_path(payload_on, "facts.local_model.output_text"),
        f"{scenario['id']} divergiu no texto produzido pelo provider fixture",
    )
    ok(f"baseline local_model {scenario['id']} alinhado")


def main() -> int:
    fixture = read_json(FIXTURE_PATH)
    scenarios = list(fixture["scenarios"])
    ensure(scenarios, "fixture local_model precisa listar cenarios")
    provider = FixtureLocalModelProvider(
        {
            (str(scenario["phrase"]), str(scenario["requested_capability"])): str(
                scenario["model_on_contains"]
            )
            for scenario in scenarios
        }
    )
    for scenario in scenarios:
        assert_scenario(scenario, provider)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

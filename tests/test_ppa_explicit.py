from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.domain_classifier import classify_text
from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import setup_host_package_testbed, setup_ppa_testbed


class PpaExplicitTests(unittest.TestCase):
    def test_classifier_routes_explicit_ppa_install_with_canonical_coordinate(self) -> None:
        request = classify_text("instalar obs-studio do ppa ppa:obsproject/obs-studio")
        self.assertEqual(request.intent, "instalar")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.requested_source, "ppa")
        self.assertEqual(request.source_coordinate, "ppa:obsproject/obs-studio")
        self.assertEqual(request.target, "obs-studio")
        self.assertEqual(request.status, "CONSISTENT")
        self.assertIn("source_hint:ppa", request.observations)
        self.assertIn("ppa_coordinate:ppa:obsproject/obs-studio", request.observations)

    def test_classifier_blocks_explicit_ppa_without_coordinate(self) -> None:
        request = classify_text("instalar obs-studio do ppa")
        self.assertEqual(request.requested_source, "ppa")
        self.assertEqual(request.status, "BLOCKED")
        self.assertIn("ppa:owner/name", request.reason)

    def test_classifier_blocks_non_canonical_ppa_coordinate(self) -> None:
        request = classify_text("instalar obs-studio do ppa obsproject/obs-studio")
        self.assertEqual(request.requested_source, "ppa")
        self.assertEqual(request.target, "obs-studio")
        self.assertEqual(request.status, "BLOCKED")
        self.assertIn("ppa:owner/name", request.reason)

    def test_ppa_install_requires_confirmation_and_plans_explicit_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs-studio do ppa ppa:obsproject/obs-studio", environ=env)
            )
            self.assertEqual(payload["policy"]["source_type"], "ppa_repository")
            self.assertEqual(payload["policy"]["trust_level"], "third_party_repository")
            self.assertEqual(payload["policy"]["policy_outcome"], "require_confirmation")
            self.assertEqual(payload["policy"]["ppa_supported_distros"], "ubuntu")
            self.assertEqual(payload["policy"]["ppa_capability"], "add_apt_repository_observed")
            self.assertEqual(payload["policy"]["ppa_state_probe"], "dpkg_observed")
            self.assertEqual(payload["policy"]["ppa_install_preparation"], "add_repository,apt_get_update")
            self.assertEqual(payload["request"]["source_coordinate"], "ppa:obsproject/obs-studio")
            self.assertEqual(payload["execution_route"]["route_name"], "ppa.instalar")
            self.assertEqual(
                payload["execution_route"]["pre_commands"],
                [
                    ["sudo", "add-apt-repository", "-y", "-n", "ppa:obsproject/obs-studio"],
                    ["sudo", "apt-get", "update"],
                ],
            )
            self.assertEqual(payload["execution_route"]["command"], ["sudo", "apt-get", "install", "-y", "obs-studio"])
            self.assertTrue(payload["execution_route"]["ppa_preparation_planned"])

    def test_ppa_install_executes_add_update_then_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file, enabled_ppa_file, commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
            )
            exit_code, record, _message = perform_execution(
                plan_text("instalar obs-studio do ppa ppa:obsproject/obs-studio", environ=env, confirmed=True),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution_route"]["route_name"], "ppa.instalar")
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], False)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], True)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "obs-studio")
            self.assertEqual(enabled_ppa_file.read_text(encoding="utf-8").strip(), "ppa:obsproject/obs-studio")
            self.assertEqual(
                commands_file.read_text(encoding="utf-8").splitlines(),
                [
                    "--help",
                    "-y -n ppa:obsproject/obs-studio",
                    "update",
                    "install -y obs-studio",
                ],
            )

    def test_ppa_blocks_on_debian_even_with_apt_stack_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
                distro_id="debian",
                distro_like="debian",
                name="Debian GNU/Linux",
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs-studio do ppa ppa:obsproject/obs-studio", environ=env)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("ppa_distro_not_supported", payload["policy"]["trust_gaps"])

    def test_ppa_blocks_on_non_ubuntu_derivative_even_with_apt_stack_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
                distro_id="linuxmint",
                distro_like="ubuntu debian",
                name="Linux Mint",
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs-studio do ppa ppa:obsproject/obs-studio", environ=env)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("ppa_distro_not_supported", payload["policy"]["trust_gaps"])

    def test_ppa_blocks_when_add_apt_repository_capability_is_not_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
                add_apt_repository_available=False,
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs-studio do ppa ppa:obsproject/obs-studio", environ=env)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("ppa_capability_probe_failed", payload["policy"]["trust_gaps"])

    def test_ppa_remove_is_blocked_by_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
                installed_packages=("obs-studio",),
            )
            payload = decision_record_to_dict(
                plan_text("remover obs-studio do ppa ppa:obsproject/obs-studio", environ=env, confirmed=True)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("ppa_removal_not_opened", payload["policy"]["trust_gaps"])
            self.assertIn("ppa_package_origin_not_verifiable", payload["policy"]["trust_gaps"])
            self.assertIsNone(payload.get("execution_route"))

    def test_ppa_install_requires_exact_package_name_and_does_not_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs studio do ppa ppa:obsproject/obs-studio", environ=env, confirmed=True)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "unresolved")
            self.assertIn("sem busca ou canonicalizacao automatica", payload["target_resolution"]["reason"])

    def test_dev_report_exposes_requested_source_coordinate_and_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_ppa_file, _commands_file = setup_ppa_testbed(
                root,
                ppa_coordinate="ppa:obsproject/obs-studio",
                repo_packages=("obs-studio",),
            )
            rendered = render_dev_report(
                "instalar obs-studio do ppa ppa:obsproject/obs-studio",
                environ=env,
            )
            self.assertIn("requested_source:        ppa", rendered)
            self.assertIn("source_coordinate:       ppa:obsproject/obs-studio", rendered)
            self.assertIn("source_type:             ppa_repository", rendered)
            self.assertIn("scope_label:             pacote do host via PPA", rendered)
            self.assertIn("distro_id:               ubuntu", rendered)
            self.assertIn("ppa_capability:          add_apt_repository_observed", rendered)
            self.assertIn("ppa_install_preparation: add_repository,apt_get_update", rendered)
            self.assertIn("route_name:              ppa.instalar", rendered)
            self.assertIn("ppa_preparation_planned: true", rendered)

    def test_explicit_ppa_request_does_not_change_default_host_package_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("obs-studio",),
            )
            request = classify_text("instalar obs-studio")
            self.assertEqual(request.requested_source, "")
            payload = decision_record_to_dict(plan_text("instalar obs-studio", environ=env))
            self.assertEqual(payload["policy"]["source_type"], "host_package_manager")


if __name__ == "__main__":
    unittest.main()

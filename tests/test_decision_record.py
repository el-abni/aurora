from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import setup_flatpak_testbed, setup_host_package_testbed, write_os_release, write_stub


class DecisionRecordTests(unittest.TestCase):
    def test_install_request_generates_typed_policy_and_state_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox",),
            )
            record = plan_text("instalar firefox", environ=env)
            payload = decision_record_to_dict(record)

            self.assertEqual(payload["outcome"], "planned")
            self.assertEqual(payload["policy"]["source_type"], "host_package_manager")
            self.assertEqual(payload["policy"]["trust_level"], "distribution_managed")
            self.assertEqual(payload["policy"]["policy_outcome"], "allow")
            self.assertEqual(payload["policy"]["software_criticality"], "medium")
            self.assertEqual(payload["policy"]["requires_confirmation"], False)
            self.assertEqual(payload["execution_route"]["implemented"], True)
            self.assertEqual(payload["execution_route"]["requires_privilege_escalation"], True)
            self.assertEqual(payload["execution_route"]["state_probe_command"], ["dpkg", "-s", "firefox"])
            self.assertEqual(payload["target_resolution"]["status"], "direct")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "firefox")

    def test_atomic_block_records_trust_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "dnf", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="bazzite", distro_like="fedora", name="Bazzite")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}
            payload = decision_record_to_dict(plan_text("procurar firefox", environ=env))
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("host_mutation_blocked_on_atomic", payload["policy"]["trust_gaps"])

    def test_sensitive_remove_requires_confirmation_until_explicitly_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("sudo",),
                installed_packages=("sudo",),
            )
            without_confirm = decision_record_to_dict(plan_text("remover sudo", environ=env))
            self.assertEqual(without_confirm["policy"]["software_criticality"], "sensitive")
            self.assertEqual(without_confirm["policy"]["policy_outcome"], "require_confirmation")
            self.assertEqual(without_confirm["policy"]["requires_confirmation"], True)
            self.assertEqual(without_confirm["policy"]["reversal_level"], "hard_to_reverse")

            with_confirm = decision_record_to_dict(plan_text("remover sudo", environ=env, confirmed=True))
            self.assertEqual(with_confirm["policy"]["policy_outcome"], "allow")
            self.assertEqual(with_confirm["policy"]["confirmation_supplied"], True)

    def test_execution_record_captures_probes_and_final_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox",),
            )
            exit_code, executed_record, _message = perform_execution(
                plan_text("instalar firefox", environ=env),
                environ=env,
            )
            self.assertEqual(exit_code, 0)
            payload = decision_record_to_dict(executed_record)
            self.assertEqual(payload["outcome"], "executed")
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], False)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], True)

    def test_dev_render_exposes_core_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "zypper", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="opensuse-tumbleweed", distro_like="opensuse suse", name="openSUSE")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}
            rendered = render_dev_report("procurar steam", environ=env)
            self.assertIn("Policy", rendered)
            self.assertIn("source_type:", rendered)
            self.assertIn("trust_gaps:", rendered)
            self.assertIn("Execution route", rendered)

    def test_dev_render_labels_user_scope_for_flatpak_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("obs-studio|OBS Studio",),
                name="Ubuntu",
            )
            rendered = render_dev_report("procurar obs-studio no flatpak", environ=env)
            self.assertIn("scope_label:             software do usuario", rendered)

    def test_dev_render_exposes_flatpak_target_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            rendered = render_dev_report("instalar obs studio no flatpak", environ=env)
            self.assertIn("Target resolution", rendered)
            self.assertIn("resolved_target:         com.obsproject.Studio", rendered)
            self.assertIn("canonicalized:           true", rendered)

    def test_decision_record_marks_normalized_query_resolution_for_hyphenated_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            payload = decision_record_to_dict(plan_text("instalar obs-studio no flatpak", environ=env))
            self.assertEqual(payload["target_resolution"]["source"], "flatpak_search_normalized_query")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "com.obsproject.Studio")

    def test_decision_record_exposes_host_package_target_resolution_for_compound_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("obs-studio|OBS Studio",),
            )
            payload = decision_record_to_dict(plan_text("instalar obs studio", environ=env))
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["source"], "host_package_search_normalized_query")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")


if __name__ == "__main__":
    unittest.main()

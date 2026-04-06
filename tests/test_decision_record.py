from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import (
    setup_aur_testbed,
    setup_flatpak_testbed,
    setup_host_package_testbed,
    write_os_release,
    write_stub,
)


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

    def test_inline_confirmation_marker_is_promoted_to_global_confirmation(self) -> None:
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
            with_confirm = decision_record_to_dict(plan_text("remover sudo --confirm", environ=env))
            with_yes = decision_record_to_dict(plan_text("remover sudo --yes", environ=env))
            self.assertEqual(with_confirm["policy"]["policy_outcome"], "allow")
            self.assertTrue(with_confirm["policy"]["confirmation_supplied"])
            self.assertEqual(with_yes["policy"]["policy_outcome"], "allow")
            self.assertTrue(with_yes["policy"]["confirmation_supplied"])

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

    def test_aur_install_execution_record_captures_foreign_probes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
            )
            def fake_interactive_runner(args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
                with aur_state_file.open("a", encoding="utf-8") as handle:
                    handle.write("google-chrome\n")
                return subprocess.CompletedProcess(args, 0, "", "")

            exit_code, executed_record, _message = perform_execution(
                plan_text("instalar google chrome no aur", environ=env, confirmed=True),
                interactive_runner=fake_interactive_runner,
                environ=env,
            )
            self.assertEqual(exit_code, 0)
            payload = decision_record_to_dict(executed_record)
            self.assertEqual(payload["policy"]["source_type"], "aur_repository")
            self.assertEqual(payload["policy"]["trust_level"], "third_party_build")
            self.assertEqual(payload["execution_route"]["route_name"], "aur.instalar")
            self.assertEqual(payload["execution_route"]["state_probe_command"], ["pacman", "-Q", "--", "google-chrome"])
            self.assertTrue(payload["execution_route"]["interactive_passthrough"])
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertTrue(payload["execution"]["interactive_passthrough"])
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], False)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], True)
            self.assertIn("google-chrome", aur_state_file.read_text(encoding="utf-8"))

    def test_aur_remove_execution_record_captures_foreign_probes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
                aur_installed_packages=("google-chrome",),
            )
            exit_code, executed_record, _message = perform_execution(
                plan_text("remover google chrome no aur", environ=env, confirmed=True),
                environ=env,
            )
            self.assertEqual(exit_code, 0)
            payload = decision_record_to_dict(executed_record)
            self.assertEqual(payload["policy"]["source_type"], "aur_repository")
            self.assertEqual(payload["policy"]["trust_level"], "third_party_build")
            self.assertEqual(payload["execution_route"]["route_name"], "aur.remover")
            self.assertEqual(payload["execution_route"]["state_probe_command"], ["pacman", "-Q", "--", "google-chrome"])
            self.assertFalse(payload["execution_route"]["interactive_passthrough"])
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertFalse(payload["execution"]["interactive_passthrough"])
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], True)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], False)
            self.assertEqual(aur_state_file.read_text(encoding="utf-8").strip(), "")

    def test_arch_record_surfaces_observed_aur_helper_outside_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("firefox",),
                prefer_paru=True,
            )
            payload = decision_record_to_dict(plan_text("instalar firefox", environ=env))
            self.assertEqual(payload["host_profile"]["package_backends"], ["pacman"])
            self.assertEqual(payload["host_profile"]["observed_third_party_package_tools"], ["paru"])
            self.assertIn(
                "observed_third_party_package_tools:paru",
                payload["policy"]["trust_signals"],
            )
            self.assertIn("arch_aur_helpers_observed_out_of_contract", payload["policy"]["trust_gaps"])
            self.assertIn(
                "helpers de fonte terceira observados (paru) nao ampliam o contrato de host_package nesta rodada.",
                payload["execution_route"]["notes"],
            )

            rendered = render_dev_report("instalar firefox", environ=env)
            self.assertIn("observed_third_party_tools: paru", rendered)

    def test_arch_blocks_when_only_aur_helper_is_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "paru", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="cachyos", distro_like="arch", name="CachyOS")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}

            payload = decision_record_to_dict(plan_text("procurar firefox", environ=env))
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertEqual(payload["host_profile"]["package_backends"], [])
            self.assertEqual(payload["host_profile"]["observed_third_party_package_tools"], ["paru"])
            self.assertIn("arch_host_package_backend_not_observed", payload["policy"]["trust_gaps"])
            self.assertIn("arch_aur_helpers_observed_out_of_contract", payload["policy"]["trust_gaps"])
            self.assertIn("helper AUR observado nao substitui backend oficial", payload["policy"]["reason"])

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
            self.assertIn("scope_label:             software do usuário", rendered)

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
            self.assertIn("flatpak_effective_remote: flathub", rendered)
            self.assertIn("flatpak_remote_origin:   default", rendered)

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
            self.assertEqual(payload["target_resolution"]["source"], "flatpak_remote_ls")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "com.obsproject.Studio")
            self.assertEqual(payload["policy"]["flatpak_effective_remote"], "flathub")

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

    def test_dev_render_keeps_inline_aur_markers_out_of_target_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio|OBS Studio",),
            )
            rendered = render_dev_report("instalar obs-studio no aur --confirm", environ=env)
            self.assertIn("target:                  obs-studio", rendered)
            self.assertIn("original_target:         obs-studio", rendered)
            self.assertIn("consulted_target:        obs-studio", rendered)
            self.assertIn("resolved_target:         obs-studio", rendered)
            self.assertIn("confirmation_supplied:   true", rendered)
            self.assertIn("interactive_passthrough: true", rendered)
            self.assertNotIn("target:                  obs-studio no aur --confirm", rendered)
            self.assertNotIn("original_target:         obs-studio no aur --confirm", rendered)

    def test_dev_render_exposes_aur_resolution_diagnostics_for_operational_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio-git|OBS Studio Git",),
            )
            bin_dir = root / "bin"
            write_stub(
                bin_dir,
                "paru",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    -Ss|--aur|--)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "-Ss" ] && [ "$target" = "obs-studio-git" ]; then
  echo "error: aur rpc unavailable" >&2
  exit 7
fi
echo "no packages found" >&2
exit 1
""",
            )
            rendered = render_dev_report("instalar obs-studio-git no aur", environ=env, confirmed=True)
            self.assertIn("diagnostic_command:      paru -Ss --aur -- obs-studio-git", rendered)
            self.assertIn("diagnostic_exit_code:    7", rendered)
            self.assertIn("diagnostic_stderr:       error: aur rpc unavailable", rendered)


if __name__ == "__main__":
    unittest.main()

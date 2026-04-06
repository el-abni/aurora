from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from support import run_module, setup_host_package_testbed, write_os_release, write_stub


class HostPackageMutationTests(unittest.TestCase):
    def test_install_resolves_compound_human_name_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("obs-studio|OBS Studio",),
            )
            exit_code, record, message = perform_execution(plan_text("instalar obs studio", environ=env), environ=env)
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")
            self.assertIn("está instalado", message)
            self.assertIn("obs-studio", state_file.read_text(encoding="utf-8"))

    def test_install_supports_explicit_hyphenated_package_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("obs-studio|OBS Studio",),
            )
            payload = decision_record_to_dict(plan_text("instalar obs-studio", environ=env))
            self.assertEqual(payload["target_resolution"]["status"], "direct")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")

            proc = run_module("instalar", "obs-studio", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("está instalado", proc.stdout)
            self.assertIn("obs-studio", state_file.read_text(encoding="utf-8"))

    def test_arch_mutation_stays_anchored_in_pacman_when_paru_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("firefox",),
                prefer_paru=True,
            )
            write_stub(root / "bin", "paru", "#!/bin/sh\necho paru-should-not-run >&2\nexit 7\n")

            payload = decision_record_to_dict(plan_text("instalar firefox", environ=env))
            self.assertEqual(payload["host_profile"]["package_backends"], ["pacman"])
            self.assertEqual(payload["host_profile"]["observed_third_party_package_tools"], ["paru"])
            self.assertEqual(payload["execution_route"]["backend_name"], "sudo + pacman")
            self.assertEqual(payload["execution_route"]["command"][:2], ["sudo", "pacman"])

            proc = run_module("instalar", "firefox", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("está instalado", proc.stdout)
            self.assertIn("firefox", state_file.read_text(encoding="utf-8"))

    def test_remove_resolves_compound_human_name_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("obs-studio|OBS Studio",),
                installed_packages=("obs-studio",),
            )
            exit_code, record, message = perform_execution(plan_text("remover obs studio", environ=env), environ=env)
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")
            self.assertIn("foi removido", message)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_compound_human_name_blocks_when_resolution_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("obs-studio|OBS Studio", "obs_studio|OBS Studio Legacy"),
            )
            exit_code, record, message = perform_execution(plan_text("instalar obs studio", environ=env), environ=env)
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "ambiguous")
            self.assertEqual(set(payload["target_resolution"]["candidates"]), {"obs-studio", "obs_studio"})
            self.assertNotIn("execution_route", payload)
            self.assertIn("bloqueado por resolução de alvo", message)

    def test_compound_human_name_blocks_when_no_exact_package_match_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("obs-studio-browser|OBS Studio Browser",),
            )
            exit_code, record, message = perform_execution(plan_text("instalar obs studio", environ=env), environ=env)
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "not_found")
            self.assertNotIn("execution_route", payload)
            self.assertIn("bloqueado por resolução de alvo", message)

    def test_install_executes_across_supported_families(self) -> None:
        cases = [
            ("arch", "cachyos", "arch"),
            ("debian", "ubuntu", "debian"),
            ("fedora", "fedora", "fedora"),
            ("opensuse", "opensuse-tumbleweed", "opensuse suse"),
        ]
        for family, distro_id, distro_like in cases:
            with self.subTest(family=family):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    env, state_file = setup_host_package_testbed(
                        root,
                        family=family,
                        distro_id=distro_id,
                        distro_like=distro_like,
                        repo_packages=("firefox",),
                    )
                    proc = run_module("instalar", "firefox", env=env)
                    self.assertEqual(proc.returncode, 0)
                    self.assertIn("está instalado", proc.stdout)
                    self.assertIn("firefox", state_file.read_text(encoding="utf-8"))

    def test_remove_executes_across_supported_families(self) -> None:
        cases = [
            ("arch", "cachyos", "arch"),
            ("debian", "ubuntu", "debian"),
            ("fedora", "fedora", "fedora"),
            ("opensuse", "opensuse-tumbleweed", "opensuse suse"),
        ]
        for family, distro_id, distro_like in cases:
            with self.subTest(family=family):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    env, state_file = setup_host_package_testbed(
                        root,
                        family=family,
                        distro_id=distro_id,
                        distro_like=distro_like,
                        repo_packages=("firefox",),
                        installed_packages=("firefox",),
                    )
                    proc = run_module("remover", "firefox", env=env)
                    self.assertEqual(proc.returncode, 0)
                    self.assertIn("foi removido", proc.stdout)
                    self.assertNotIn("firefox", state_file.read_text(encoding="utf-8"))

    def test_install_noop_when_package_is_already_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox",),
                installed_packages=("firefox",),
            )
            proc = run_module("instalar", "firefox", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("já está instalado", proc.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "firefox")

    def test_remove_noop_when_package_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="fedora",
                distro_id="fedora",
                distro_like="fedora",
                repo_packages=("firefox",),
            )
            proc = run_module("remover", "firefox", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("já não está instalado", proc.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_atomic_host_blocks_mutation_by_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")
            write_stub(bin_dir, "dnf", "#!/bin/sh\nexit 0\n")
            write_stub(bin_dir, "rpm", "#!/bin/sh\nexit 0\n")
            write_os_release(root, distro_id="bazzite", distro_like="fedora", name="Bazzite")
            env = {"PATH": f"{bin_dir}:{Path('/usr/bin')}", "AURORA_OS_RELEASE_PATH": str(root / 'os-release')}
            proc = run_module("instalar", "firefox", env=env)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("bloqueado por política", proc.stdout)

    def test_sensitive_remove_requires_confirmation_and_respects_confirm_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("sudo",),
                installed_packages=("sudo",),
            )
            blocked = run_module("remover", "sudo", env=env)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("exige confirmação explícita", blocked.stdout)
            self.assertIn("sudo", state_file.read_text(encoding="utf-8"))

            confirmed = run_module("remover", "sudo", "--confirm", env=env)
            self.assertEqual(confirmed.returncode, 0)
            self.assertIn("foi removido", confirmed.stdout)
            self.assertNotIn("sudo", state_file.read_text(encoding="utf-8"))

    def test_sensitive_remove_accepts_inline_confirmation_when_phrase_is_single_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("sudo",),
                installed_packages=("sudo",),
            )
            confirmed = run_module("remover sudo --confirm", env=env)
            self.assertEqual(confirmed.returncode, 0)
            self.assertIn("foi removido", confirmed.stdout)
            self.assertNotIn("sudo", state_file.read_text(encoding="utf-8"))

    def test_sensitive_remove_accepts_inline_yes_when_phrase_is_single_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("sudo",),
                installed_packages=("sudo",),
            )
            confirmed = run_module("remover sudo --yes", env=env)
            self.assertEqual(confirmed.returncode, 0)
            self.assertIn("foi removido", confirmed.stdout)
            self.assertNotIn("sudo", state_file.read_text(encoding="utf-8"))

    def test_sensitive_remove_noops_when_package_is_already_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("sudo",),
            )
            proc = run_module("remover", "sudo", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("já não está instalado", proc.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_missing_state_probe_is_reported_as_operational_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")
            write_stub(bin_dir, "apt-get", "#!/bin/sh\nexit 0\n")
            write_os_release(root, distro_id="ubuntu", distro_like="debian", name="Ubuntu")
            env = {"PATH": f"{bin_dir}:{Path('/usr/bin')}", "AURORA_OS_RELEASE_PATH": str(root / 'os-release')}
            exit_code, record, message = perform_execution(plan_text("instalar firefox", environ=env), environ=env)
            self.assertEqual(exit_code, 1)
            self.assertEqual(record.outcome, "operational_error")
            self.assertEqual(record.execution.status, "probe_missing")
            self.assertIn("confirmação de estado", message)

    def test_backend_failure_exposes_useful_operational_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("jq",),
                installed_packages=("jq",),
            )

            def fake_runner(args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
                command = tuple(args)
                if command == ("pacman", "-Q", "--", "jq"):
                    return subprocess.CompletedProcess(args, 0, "jq 1.0-1\n", "")
                if command == ("sudo", "pacman", "-Rns", "--", "jq"):
                    return subprocess.CompletedProcess(
                        args,
                        1,
                        "",
                        (
                            "error: failed to prepare transaction (could not satisfy dependencies)\n"
                            ":: removing jq breaks dependency 'jq' required by 'scx-scheds'\n"
                        ),
                    )
                self.fail(f"comando inesperado: {command!r}")

            exit_code, record, message = perform_execution(
                plan_text("remover jq --confirm", environ=env),
                runner=fake_runner,
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 1)
            self.assertEqual(record.outcome, "operational_error")
            self.assertEqual(record.execution.status, "operational_error")
            self.assertIn("exit code 1", message)
            self.assertIn("scx-scheds", message)
            self.assertIn("scx-scheds", payload["execution"]["diagnostic_stderr"])


if __name__ == "__main__":
    unittest.main()

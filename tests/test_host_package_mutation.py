from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from support import run_module, setup_host_package_testbed, write_os_release, write_stub


class HostPackageMutationTests(unittest.TestCase):
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
                    self.assertIn("esta instalado", proc.stdout)
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


if __name__ == "__main__":
    unittest.main()

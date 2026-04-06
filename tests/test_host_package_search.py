from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.planner import plan_text
from support import run_module, setup_host_package_testbed, write_os_release, write_stub


class HostPackageSearchTests(unittest.TestCase):
    def test_arch_search_executes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("firefox",),
            )
            proc = run_module("procurar", "firefox", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("Encontrei resultados", proc.stdout)
            self.assertIn("extra/firefox 1.0", proc.stdout)

    def test_arch_search_stays_anchored_in_pacman_when_paru_is_present(self) -> None:
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
            write_stub(root / "bin", "paru", "#!/bin/sh\necho paru-should-not-run >&2\nexit 7\n")

            record = plan_text("procurar firefox", environ=env)
            self.assertIsNotNone(record.execution_route)
            self.assertEqual(record.execution_route.backend_name, "pacman")
            self.assertEqual(record.execution_route.command, ("pacman", "-Ss", "--", "firefox"))

            proc = run_module("procurar", "firefox", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("extra/firefox 1.0", proc.stdout)

    def test_search_handles_no_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
            )
            proc = run_module("procurar", "firefox", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("Não encontrei resultados", proc.stdout)

    def test_planner_maps_family_specific_search_routes(self) -> None:
        cases = [
            ("ubuntu", "debian", "apt-cache", ("apt-cache", "search", "firefox")),
            ("fedora", "fedora", "dnf", ("dnf", "search", "firefox")),
            ("opensuse-tumbleweed", "opensuse suse", "zypper", ("zypper", "search", "--", "firefox")),
        ]
        for distro_id, distro_like, backend_name, command in cases:
            with self.subTest(distro_id=distro_id):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    bin_dir = root / "bin"
                    bin_dir.mkdir()
                    write_stub(bin_dir, backend_name, "#!/usr/bin/env bash\nexit 0\n")
                    write_os_release(root, distro_id=distro_id, distro_like=distro_like, name=distro_id)
                    env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}
                    record = plan_text("procurar firefox", environ=env)
                    self.assertIsNotNone(record.execution_route)
                    self.assertEqual(record.execution_route.command, command)
                    self.assertEqual(record.outcome, "planned")

    def test_atomic_host_blocks_search_by_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "dnf", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="bazzite", distro_like="fedora", name="Bazzite")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}
            proc = run_module("procurar", "firefox", env=env)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("Bloqueado por política", proc.stdout)


if __name__ == "__main__":
    unittest.main()

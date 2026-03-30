from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from support import ROOT, run_module, run_script, write_os_release, write_stub

CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class BootstrapSmokeTests(unittest.TestCase):
    def test_help_via_module(self) -> None:
        proc = run_module("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn(f"🌌 Aurora {CURRENT_VERSION}", proc.stdout)
        self.assertIn("host_package", proc.stdout)

    def test_version_via_launchers(self) -> None:
        for script_name in ("aurora", "auro"):
            proc = run_script(script_name, "--version")
            self.assertEqual(proc.returncode, 0)
            self.assertIn(f"Aurora {CURRENT_VERSION}", proc.stdout)

    def test_dev_boots_with_decision_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            write_stub(bin_dir, "apt-cache", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="ubuntu", distro_like="debian", name="Ubuntu")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}
            proc = run_module("dev", "procurar", "firefox", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("Aurora decision record", proc.stdout)
            self.assertIn("source_type:", proc.stdout)
            self.assertIn("route_name:", proc.stdout)


if __name__ == "__main__":
    unittest.main()

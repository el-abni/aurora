from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from support import ROOT

CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class InstallerReleaseTests(unittest.TestCase):
    def test_install_and_uninstall_scripts_manage_local_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            share_dir = root / "share" / "aurora"
            bin_dir = root / "bin"
            env = os.environ.copy()
            env["AURORA_SHARE_DIR"] = str(share_dir)
            env["AURORA_BIN_DIR"] = str(bin_dir)

            install_proc = subprocess.run(
                ["bash", "install.sh"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(install_proc.returncode, 0)
            self.assertIn(f"Aurora {CURRENT_VERSION} instalada", install_proc.stdout)
            self.assertTrue((share_dir / "python" / "aurora" / "__main__.py").exists())
            self.assertTrue((bin_dir / "aurora").exists())
            self.assertTrue((bin_dir / "auro").exists())

            run_env = env.copy()
            run_env["PATH"] = f"{bin_dir}:{os.environ['PATH']}"
            version_proc = subprocess.run(
                [str(bin_dir / "aurora"), "--version"],
                cwd=ROOT,
                env=run_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(version_proc.returncode, 0)
            self.assertIn(f"Aurora {CURRENT_VERSION}", version_proc.stdout)

            uninstall_proc = subprocess.run(
                ["bash", "uninstall.sh"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(uninstall_proc.returncode, 0)
            self.assertIn("Aurora removida", uninstall_proc.stdout)
            self.assertFalse(share_dir.exists())
            self.assertFalse((bin_dir / "aurora").exists())
            self.assertFalse((bin_dir / "auro").exists())


if __name__ == "__main__":
    unittest.main()

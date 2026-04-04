from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.linux.host_profile import detect_host_profile
from support import write_os_release, write_stub


class HostProfileTests(unittest.TestCase):
    def _env(self, root: Path) -> dict[str, str]:
        return {
            "PATH": str(root / "bin"),
            "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
        }

    def test_arch_mutable_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "pacman", "#!/usr/bin/env bash\nexit 0\n")
            write_stub(bin_dir, "paru", "#!/usr/bin/env bash\nexit 0\n")
            write_stub(bin_dir, "flatpak", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="cachyos", distro_like="arch", name="CachyOS")
            profile = detect_host_profile(self._env(root))
            self.assertEqual(profile.linux_family, "arch")
            self.assertEqual(profile.mutability, "mutable")
            self.assertEqual(profile.support_tier, "tier_1")
            self.assertEqual(profile.package_backends, ("pacman",))
            self.assertEqual(profile.observed_package_tools, ("flatpak",))
            self.assertEqual(profile.observed_third_party_package_tools, ("paru",))

    def test_arch_profile_observes_supported_and_out_of_contract_aur_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "pacman", "#!/usr/bin/env bash\nexit 0\n")
            write_stub(bin_dir, "yay", "#!/usr/bin/env bash\nexit 0\n")
            write_stub(bin_dir, "pikaur", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="cachyos", distro_like="arch", name="CachyOS")
            profile = detect_host_profile(self._env(root))
            self.assertEqual(profile.observed_third_party_package_tools, ("yay", "pikaur"))

    def test_debian_mutable_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "apt-cache", "#!/usr/bin/env bash\nexit 0\n")
            write_stub(bin_dir, "apt-get", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="ubuntu", distro_like="debian", name="Ubuntu")
            profile = detect_host_profile(self._env(root))
            self.assertEqual(profile.linux_family, "debian")
            self.assertEqual(profile.support_tier, "tier_1")

    def test_fedora_mutable_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "dnf", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="fedora", distro_like="fedora", name="Fedora Linux")
            profile = detect_host_profile(self._env(root))
            self.assertEqual(profile.linux_family, "fedora")
            self.assertEqual(profile.support_tier, "tier_1")

    def test_opensuse_contained_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "zypper", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(
                root,
                distro_id="opensuse-tumbleweed",
                distro_like="opensuse suse",
                name="openSUSE Tumbleweed",
            )
            profile = detect_host_profile(self._env(root))
            self.assertEqual(profile.linux_family, "opensuse")
            self.assertEqual(profile.support_tier, "tier_2")

    def test_atomic_profile_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_stub(bin_dir, "dnf", "#!/usr/bin/env bash\nexit 0\n")
            write_os_release(root, distro_id="bazzite", distro_like="fedora", name="Bazzite")
            profile = detect_host_profile(self._env(root))
            self.assertEqual(profile.linux_family, "fedora")
            self.assertEqual(profile.mutability, "atomic")
            self.assertEqual(profile.support_tier, "limited")


if __name__ == "__main__":
    unittest.main()

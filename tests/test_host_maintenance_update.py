from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.domain_classifier import classify_text
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import run_module, write_os_release, write_stub


def _arch_env(
    root: Path,
    *,
    with_paru: bool = False,
    pacman_exit_code: int = 0,
) -> tuple[dict[str, str], Path, Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    update_log = root / "pacman-update.log"
    paru_log = root / "paru.log"
    write_os_release(root, distro_id="cachyos", distro_like="arch", name="CachyOS")
    write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")
    write_stub(
        bin_dir,
        "pacman",
        (
            "#!/bin/sh\n"
            f"log_file=\"{update_log}\"\n"
            "case \"$1\" in\n"
            "  -Syu)\n"
            "    echo \"$*\" >> \"$log_file\"\n"
            f"    exit {pacman_exit_code}\n"
            "    ;;\n"
            "  -Q)\n"
            "    exit 1\n"
            "    ;;\n"
            "esac\n"
            "exit 2\n"
        ),
    )
    if with_paru:
        write_stub(
            bin_dir,
            "paru",
            (
                "#!/bin/sh\n"
                f"log_file=\"{paru_log}\"\n"
                "echo \"$*\" >> \"$log_file\"\n"
                "exit 7\n"
            ),
        )
    env = {
        "PATH": f"{bin_dir}:{Path('/usr/bin')}",
        "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
    }
    return env, update_log, paru_log


def _debian_env(root: Path) -> dict[str, str]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    write_os_release(root, distro_id="ubuntu", distro_like="debian", name="Ubuntu")
    return {
        "PATH": f"{bin_dir}:{Path('/usr/bin')}",
        "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
    }


def _atomic_env(root: Path) -> dict[str, str]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    write_os_release(root, distro_id="bazzite", distro_like="fedora", name="Bazzite")
    write_stub(bin_dir, "rpm-ostree", "#!/bin/sh\nexit 0\n")
    return {
        "PATH": f"{bin_dir}:{Path('/usr/bin')}",
        "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
    }


class HostMaintenanceUpdateTests(unittest.TestCase):
    def test_classifier_opens_system_update_only(self) -> None:
        request = classify_text("atualizar sistema")
        self.assertEqual(request.intent, "atualizar")
        self.assertEqual(request.domain_kind, "host_maintenance")
        self.assertEqual(request.target, "sistema")
        self.assertEqual(request.status, "CONSISTENT")

        out_of_scope = classify_text("atualizar firefox")
        self.assertEqual(out_of_scope.domain_kind, "host_maintenance")
        self.assertEqual(out_of_scope.status, "OUT_OF_SCOPE")
        self.assertIn("apenas para 'sistema'", out_of_scope.reason)

    def test_public_out_of_scope_update_uses_polished_host_maintenance_terms(self) -> None:
        proc = run_module("atualizar", "firefox")

        self.assertEqual(proc.returncode, 1)
        self.assertIn("manutenção do host", proc.stdout)
        self.assertNotIn("manutencao", proc.stdout)

    def test_arch_plan_requires_confirmation_and_keeps_arch_route_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _update_log, _paru_log = _arch_env(Path(tmp), with_paru=True)
            payload = decision_record_to_dict(plan_text("atualizar sistema", environ=env))

            self.assertEqual(payload["stable_ids"]["action_id"], "atualizar")
            self.assertEqual(payload["stable_ids"]["route_id"], "host_maintenance.atualizar")
            self.assertEqual(payload["request"]["domain_kind"], "host_maintenance")
            self.assertEqual(payload["policy"]["policy_outcome"], "require_confirmation")
            self.assertTrue(payload["policy"]["requires_confirmation"])
            self.assertEqual(payload["execution_route"]["backend_name"], "sudo + pacman")
            self.assertEqual(payload["execution_route"]["command"], ["sudo", "pacman", "-Syu"])
            self.assertTrue(payload["execution_route"]["interactive_passthrough"])
            self.assertIn(
                "arch_aur_helpers_observed_out_of_contract",
                payload["policy"]["trust_gaps"],
            )
            self.assertIn(
                "nao abre AUR implicita",
                " ".join(payload["execution_route"]["notes"]),
            )

            rendered = render_dev_report("atualizar sistema", environ=env)
            self.assertIn("scope_label:             manutenção do host", rendered)
            self.assertIn("route_id:                host_maintenance.atualizar", rendered)

    def test_public_update_requires_confirmation_and_does_not_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, update_log, _paru_log = _arch_env(Path(tmp))
            proc = run_module("atualizar", "sistema", env=env)

            self.assertEqual(proc.returncode, 1)
            self.assertIn("exige confirmação explícita", proc.stdout)
            self.assertFalse(update_log.exists())

    def test_confirmed_update_executes_with_pacman_and_never_calls_paru(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, update_log, paru_log = _arch_env(Path(tmp), with_paru=True)
            proc = run_module("atualizar", "sistema", "--confirm", env=env)

            self.assertEqual(proc.returncode, 0)
            self.assertIn("sudo + pacman", proc.stdout)
            self.assertIn("concluí a atualização do sistema do host suportado", proc.stdout)
            self.assertIn("-Syu", update_log.read_text(encoding="utf-8"))
            self.assertTrue(not paru_log.exists() or not paru_log.read_text(encoding="utf-8").strip())

    def test_debian_update_stays_honestly_out_of_scope_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _debian_env(Path(tmp))
            payload = decision_record_to_dict(plan_text("atualizar sistema", environ=env))
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("fora do recorte equivalente", payload["policy"]["reason"])
            self.assertNotIn("execution_route", payload)

            proc = run_module("atualizar", "sistema", env=env)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("fora do recorte equivalente", proc.stdout)
            self.assertNotIn("backend", proc.stdout.lower())

    def test_atomic_update_blocks_with_immutable_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _atomic_env(Path(tmp))
            payload = decision_record_to_dict(plan_text("atualizar sistema", environ=env))

            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("host imutavel", payload["policy"]["reason"])
            self.assertEqual(payload["policy"]["immutable_selected_surface"], "block")
            self.assertTrue(payload["policy"]["immutable_host_context"]["host_is_immutable"])
            self.assertNotIn("execution_route", payload)

    def test_help_and_docs_expose_the_minimal_surface_honestly(self) -> None:
        root = Path(__file__).resolve().parents[1]
        help_text = (root / "resources" / "help.txt").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        architecture = (root / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
        compatibility = (root / "docs" / "COMPATIBILITY_LINUX.md").read_text(encoding="utf-8")
        policy = (root / "docs" / "INSTALLATION_POLICY.md").read_text(encoding="utf-8")

        self.assertIn("aurora atualizar sistema --confirm", help_text)
        self.assertIn("host_maintenance.atualizar", readme)
        self.assertIn("sem `paru`", readme)
        self.assertIn("host_maintenance.atualizar", architecture)
        self.assertIn("misturar AUR", architecture)
        self.assertIn("atualizar sistema", compatibility)
        self.assertIn("host_maintenance", policy)


if __name__ == "__main__":
    unittest.main()

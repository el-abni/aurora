from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.domain_classifier import classify_text
from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import run_module, setup_distrobox_testbed


class DistroboxExplicitTests(unittest.TestCase):
    def _single_distrobox_env(
        self,
        root: Path,
        *,
        include_sudo: bool = True,
        installed: tuple[str, ...] = (),
    ) -> tuple[dict[str, str], dict[str, Path]]:
        return setup_distrobox_testbed(
            root,
            host_distro_id="bazzite",
            host_distro_like="fedora",
            distroboxes=(
                {
                    "name": "devbox",
                    "family": "fedora",
                    "distro_id": "fedora",
                    "distro_like": "fedora",
                    "display_name": "Fedora Distrobox",
                    "repo_packages": ("ripgrep|ripgrep", "obs-studio|OBS Studio"),
                    "installed_packages": installed,
                    "include_sudo": include_sudo,
                },
            ),
        )

    def test_classifier_routes_explicit_distrobox_request_to_mediated_host_package(self) -> None:
        request = classify_text("instalar ripgrep na distrobox devbox")

        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.execution_surface, "distrobox")
        self.assertEqual(request.environment_target, "devbox")
        self.assertEqual(request.requested_source, "")
        self.assertEqual(request.target, "ripgrep")
        self.assertIn("surface_hint:distrobox", request.observations)

    def test_naked_request_does_not_fallback_to_distrobox(self) -> None:
        request = classify_text("instalar ripgrep")

        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.execution_surface, "host")
        self.assertEqual(request.environment_target, "")

    def test_distrobox_plan_accepts_explicit_environment_on_atomic_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_distrobox_env(Path(tmp))
            payload = decision_record_to_dict(plan_text("instalar ripgrep na distrobox devbox", environ=env))

            self.assertEqual(payload["host_profile"]["mutability"], "atomic")
            self.assertEqual(payload["host_profile"]["observed_environment_tools"], ["distrobox"])
            self.assertEqual(payload["host_profile"]["observed_distrobox_environments"], ["devbox"])
            self.assertEqual(payload["environment_resolution"]["status"], "resolved")
            self.assertEqual(payload["environment_resolution"]["resolved_environment"], "devbox")
            self.assertEqual(payload["policy"]["source_type"], "distrobox_host_package_manager")
            self.assertEqual(payload["policy"]["execution_surface"], "distrobox")
            self.assertEqual(payload["policy"]["trust_level"], "mediated_environment")
            self.assertEqual(payload["policy"]["policy_outcome"], "allow")
            self.assertEqual(payload["distrobox_profile"]["linux_family"], "fedora")
            self.assertEqual(payload["distrobox_profile"]["package_backends"], ["dnf"])
            self.assertEqual(payload["execution_route"]["route_name"], "distrobox.instalar")
            self.assertEqual(payload["execution_route"]["execution_surface"], "distrobox")
            self.assertEqual(payload["execution_route"]["environment_target"], "devbox")

    def test_distrobox_search_executes_inside_selected_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_distrobox_env(Path(tmp))
            proc = run_module("procurar", "ripgrep", "na", "distrobox", "devbox", env=env)

            self.assertEqual(proc.returncode, 0)
            self.assertIn("backend 'distrobox + dnf'", proc.stdout)
            self.assertIn("ripgrep.x86_64", proc.stdout)

    def test_distrobox_install_executes_with_state_probe_inside_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, state_files = self._single_distrobox_env(Path(tmp))
            exit_code, executed_record, _message = perform_execution(
                plan_text("instalar ripgrep na distrobox devbox", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(executed_record)

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], False)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], True)
            self.assertEqual(
                payload["execution_route"]["state_probe_command"][:6],
                ["distrobox", "enter", "--name", "devbox", "--no-tty", "--"],
            )
            self.assertIn("ripgrep", state_files["devbox"].read_text(encoding="utf-8"))

    def test_distrobox_remove_requires_confirmation_and_executes_when_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, state_files = self._single_distrobox_env(Path(tmp), installed=("ripgrep",))
            blocked = decision_record_to_dict(plan_text("remover ripgrep na distrobox devbox", environ=env))
            self.assertEqual(blocked["policy"]["policy_outcome"], "require_confirmation")

            exit_code, executed_record, _message = perform_execution(
                plan_text("remover ripgrep na distrobox devbox", environ=env, confirmed=True),
                environ=env,
            )
            payload = decision_record_to_dict(executed_record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], True)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], False)
            self.assertEqual(state_files["devbox"].read_text(encoding="utf-8").strip(), "")

    def test_distrobox_blocks_when_environment_name_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_distrobox_env(Path(tmp))
            payload = decision_record_to_dict(plan_text("instalar ripgrep na distrobox", environ=env))

            self.assertEqual(payload["environment_resolution"]["status"], "missing")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertNotIn("execution_route", payload)

    def test_distrobox_blocks_when_requested_environment_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_distrobox_env(Path(tmp))
            payload = decision_record_to_dict(plan_text("instalar ripgrep na distrobox qa-box", environ=env))

            self.assertEqual(payload["environment_resolution"]["status"], "not_found")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertNotIn("execution_route", payload)

    def test_distrobox_blocks_mutation_without_exact_package_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_distrobox_env(Path(tmp))
            payload = decision_record_to_dict(plan_text("instalar rip grep na distrobox devbox", environ=env))

            self.assertEqual(payload["target_resolution"]["status"], "unresolved")
            self.assertEqual(payload["policy"]["policy_outcome"], "allow")
            self.assertNotIn("execution_route", payload)

    def test_distrobox_blocks_mutation_when_sudo_is_missing_inside_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_distrobox_env(Path(tmp), include_sudo=False)
            payload = decision_record_to_dict(plan_text("instalar ripgrep na distrobox devbox", environ=env))

            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("distrobox_sudo_not_observed", payload["policy"]["trust_gaps"])
            self.assertEqual(payload["execution_route"]["route_name"], "distrobox.instalar")

    def test_distrobox_blocks_mixed_surface_phrase(self) -> None:
        request = classify_text("instalar google chrome no aur na distrobox devbox")

        self.assertEqual(request.execution_surface, "distrobox")
        self.assertEqual(request.status, "BLOCKED")
        self.assertIn("escolha uma unica superficie", request.reason)

    def test_dev_report_exposes_distrobox_boundary_and_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_distrobox_env(Path(tmp))
            rendered = render_dev_report("procurar ripgrep na distrobox devbox", environ=env)

            self.assertIn("execution_surface:       distrobox", rendered)
            self.assertIn("observed_environment_tools: distrobox", rendered)
            self.assertIn("observed_distrobox_environments: devbox", rendered)
            self.assertIn("Environment resolution", rendered)
            self.assertIn("Distrobox profile", rendered)
            self.assertIn("route_name:              distrobox.procurar", rendered)


if __name__ == "__main__":
    unittest.main()

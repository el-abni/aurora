from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.domain_classifier import classify_text
from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import setup_rpm_ostree_testbed


class RpmOstreeExplicitTests(unittest.TestCase):
    def _single_atomic_host(
        self,
        root: Path,
        *,
        repo_packages: tuple[str, ...] = ("htop|htop",),
        booted_requested_packages: tuple[str, ...] = (),
        booted_packages: tuple[str, ...] = (),
        pending_requested_packages: tuple[str, ...] = (),
        pending_packages: tuple[str, ...] = (),
        transaction_active: bool = False,
    ) -> tuple[dict[str, str], dict[str, Path]]:
        return setup_rpm_ostree_testbed(
            root,
            host_distro_id="bazzite",
            host_distro_like="fedora",
            repo_packages=repo_packages,
            booted_requested_packages=booted_requested_packages,
            booted_packages=booted_packages,
            pending_requested_packages=pending_requested_packages,
            pending_packages=pending_packages,
            transaction_active=transaction_active,
            include_flatpak=True,
            toolbox_environments=("devbox",),
            distrobox_environments=("workbox",),
            host_name="Bazzite",
        )

    def test_classifier_routes_explicit_rpm_ostree_request_to_immutable_host_surface(self) -> None:
        request = classify_text("instalar htop no rpm-ostree")

        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.execution_surface, "rpm_ostree")
        self.assertEqual(request.requested_source, "")
        self.assertEqual(request.target, "htop")
        self.assertIn("surface_hint:rpm-ostree", request.observations)

    def test_naked_request_does_not_fallback_to_rpm_ostree(self) -> None:
        request = classify_text("instalar htop")

        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.execution_surface, "host")
        self.assertEqual(request.environment_target, "")

    def test_rpm_ostree_plan_accepts_explicit_install_on_atomic_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_atomic_host(Path(tmp))
            payload = decision_record_to_dict(plan_text("instalar htop no rpm-ostree", environ=env))

            self.assertEqual(payload["host_profile"]["mutability"], "atomic")
            self.assertEqual(
                payload["host_profile"]["observed_immutable_surfaces"],
                ["flatpak", "rpm-ostree", "toolbox[devbox]", "distrobox[workbox]"],
            )
            self.assertEqual(payload["policy"]["source_type"], "rpm_ostree_layering")
            self.assertEqual(payload["policy"]["execution_surface"], "rpm_ostree")
            self.assertEqual(payload["policy"]["trust_level"], "immutable_host_surface")
            self.assertEqual(payload["policy"]["immutable_selected_surface"], "rpm_ostree")
            self.assertEqual(payload["policy"]["policy_outcome"], "allow")
            self.assertEqual(payload["rpm_ostree_status"]["status"], "observed")
            self.assertFalse(payload["rpm_ostree_status"]["pending_deployment"])
            self.assertEqual(payload["execution_route"]["route_name"], "rpm_ostree.instalar")
            self.assertEqual(payload["execution_route"]["execution_surface"], "rpm_ostree")

    def test_rpm_ostree_install_executes_and_stages_pending_deployment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, state_files = self._single_atomic_host(Path(tmp))
            exit_code, executed_record, message = perform_execution(
                plan_text("instalar htop no rpm-ostree", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(executed_record)

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertFalse(payload["execution"]["pre_probe"]["package_present"])
            self.assertTrue(payload["execution"]["post_probe"]["package_present"])
            self.assertEqual(
                payload["execution_route"]["state_probe_command"],
                ["rpm-ostree", "status", "--json"],
            )
            self.assertIn("htop", state_files["pending_requested"].read_text(encoding="utf-8"))
            self.assertIn("Reinicie para aplicar", message)

    def test_rpm_ostree_remove_requires_confirmation_and_executes_when_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, state_files = self._single_atomic_host(
                Path(tmp),
                booted_requested_packages=("htop",),
                booted_packages=("htop",),
            )
            blocked = decision_record_to_dict(plan_text("remover htop no rpm-ostree", environ=env))
            self.assertEqual(blocked["policy"]["policy_outcome"], "require_confirmation")

            exit_code, executed_record, _message = perform_execution(
                plan_text("remover htop no rpm-ostree", environ=env, confirmed=True),
                environ=env,
            )
            payload = decision_record_to_dict(executed_record)
            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["execution"]["pre_probe"]["package_present"])
            self.assertFalse(payload["execution"]["post_probe"]["package_present"])
            self.assertEqual(state_files["pending_requested"].read_text(encoding="utf-8").strip(), "")

    def test_rpm_ostree_blocks_search_in_first_cut(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_atomic_host(Path(tmp))
            payload = decision_record_to_dict(plan_text("procurar htop no rpm-ostree", environ=env))

            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertEqual(payload["execution_route"]["route_name"], "rpm_ostree.procurar")
            self.assertFalse(payload["execution_route"]["implemented"])

    def test_rpm_ostree_blocks_when_pending_deployment_is_already_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_atomic_host(
                Path(tmp),
                repo_packages=("htop|htop", "vim|vim"),
                pending_requested_packages=("vim",),
                pending_packages=("vim",),
            )
            payload = decision_record_to_dict(plan_text("instalar htop no rpm-ostree", environ=env))

            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("rpm_ostree_pending_deployment_present", payload["policy"]["trust_gaps"])
            self.assertEqual(payload["rpm_ostree_status"]["pending_requested_packages"], ["vim"])

    def test_rpm_ostree_blocks_mutation_without_exact_package_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_atomic_host(Path(tmp), repo_packages=("obs-studio|OBS Studio",))
            payload = decision_record_to_dict(plan_text("instalar obs studio no rpm-ostree", environ=env))

            self.assertEqual(payload["target_resolution"]["status"], "unresolved")
            self.assertEqual(payload["policy"]["policy_outcome"], "allow")
            self.assertNotIn("execution_route", payload)

    def test_atomic_default_request_blocks_with_surface_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_atomic_host(Path(tmp))
            payload = decision_record_to_dict(plan_text("instalar htop", environ=env))

            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertEqual(payload["policy"]["immutable_selected_surface"], "block")
            self.assertIn("flatpak, rpm-ostree, toolbox[devbox], distrobox[workbox]", payload["policy"]["reason"])

    def test_dev_report_exposes_immutable_boundary_and_rpm_ostree_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state_files = self._single_atomic_host(Path(tmp))
            rendered = render_dev_report("instalar htop no rpm-ostree", environ=env)

            self.assertIn("execution_surface:       rpm_ostree", rendered)
            self.assertIn("observed_immutable_surfaces: flatpak, rpm-ostree, toolbox[devbox], distrobox[workbox]", rendered)
            self.assertIn("immutable_selected_surface: rpm_ostree", rendered)
            self.assertIn("rpm-ostree status", rendered)
            self.assertIn("route_name:              rpm_ostree.instalar", rendered)


if __name__ == "__main__":
    unittest.main()

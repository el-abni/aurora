from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.domain_classifier import classify_text
from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import run_module, setup_copr_testbed, setup_host_package_testbed


class CoprExplicitTests(unittest.TestCase):
    def test_classifier_routes_explicit_copr_search_with_repository_coordinate(self) -> None:
        request = classify_text("procurar obs-studio do copr atim/obs-studio")
        self.assertEqual(request.intent, "procurar")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.requested_source, "copr")
        self.assertEqual(request.source_coordinate, "atim/obs-studio")
        self.assertEqual(request.target, "obs-studio")
        self.assertEqual(request.status, "CONSISTENT")

    def test_classifier_routes_explicit_copr_request_with_repository_coordinate(self) -> None:
        request = classify_text("instalar yt-dlp do copr atim/ytdlp --confirm")
        self.assertEqual(request.intent, "instalar")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.requested_source, "copr")
        self.assertEqual(request.source_coordinate, "atim/ytdlp")
        self.assertEqual(request.target, "yt-dlp")
        self.assertEqual(request.status, "CONSISTENT")
        self.assertIn("source_hint:copr", request.observations)
        self.assertIn("copr_repo:atim/ytdlp", request.observations)

    def test_classifier_blocks_explicit_copr_without_repository_coordinate(self) -> None:
        request = classify_text("instalar yt-dlp do copr")
        self.assertEqual(request.requested_source, "copr")
        self.assertEqual(request.status, "BLOCKED")
        self.assertIn("owner/project", request.reason)

    def test_classifier_blocks_explicit_copr_search_without_repository_coordinate(self) -> None:
        request = classify_text("procurar yt-dlp do copr")
        self.assertEqual(request.requested_source, "copr")
        self.assertEqual(request.status, "BLOCKED")
        self.assertIn("owner/project", request.reason)

    def test_classifier_rejects_path_like_value_as_copr_repository_coordinate(self) -> None:
        request = classify_text("instalar yt-dlp do copr /tmp/repo")
        self.assertEqual(request.requested_source, "copr")
        self.assertEqual(request.status, "BLOCKED")
        self.assertEqual(request.target, "yt-dlp")
        self.assertIn("owner/project", request.reason)

    def test_copr_install_requires_confirmation_and_exposes_repository_in_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs-studio do copr atim/obs-studio", environ=env)
            )
            self.assertEqual(payload["policy"]["source_type"], "copr_repository")
            self.assertEqual(payload["policy"]["trust_level"], "third_party_repository")
            self.assertEqual(payload["policy"]["policy_outcome"], "require_confirmation")
            self.assertIn("copr_repo:atim/obs-studio", payload["policy"]["trust_signals"])
            self.assertEqual(payload["request"]["source_coordinate"], "atim/obs-studio")
            self.assertEqual(
                payload["execution_route"]["pre_commands"],
                [["sudo", "dnf", "-y", "copr", "enable", "atim/obs-studio"]],
            )
            self.assertEqual(payload["execution_route"]["command"], ["sudo", "dnf", "install", "-y", "obs-studio"])

    def test_copr_blocks_when_dnf_copr_capability_is_not_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
                copr_available=False,
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs-studio do copr atim/obs-studio", environ=env)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("copr_dnf_plugin_not_observed", payload["policy"]["trust_gaps"])

    def test_copr_blocks_outside_fedora(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("yt-dlp",),
            )
            payload = decision_record_to_dict(
                plan_text("instalar yt-dlp do copr atim/ytdlp", environ=env)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertIn("copr_linux_family_not_supported", payload["policy"]["trust_gaps"])

    def test_copr_install_requires_exact_package_name_and_does_not_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
            )
            payload = decision_record_to_dict(
                plan_text("instalar obs studio do copr atim/obs-studio", environ=env, confirmed=True)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "unresolved")
            self.assertIn("sem busca ou canonicalizacao automatica", payload["target_resolution"]["reason"])

    def test_copr_search_executes_only_inside_explicit_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio|OBS Studio", "obs-tools|OBS Tools",),
            )
            proc = run_module("procurar", "obs", "studio", "do", "copr", "atim/obs-studio", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("backend 'copr'", proc.stdout)
            self.assertIn("obs-studio.x86_64", proc.stdout)
            self.assertNotIn("bloqueado por política", proc.stdout)
            commands = commands_file.read_text(encoding="utf-8").splitlines()
            self.assertEqual(commands[0], "copr --help")
            self.assertIn("--setopt=reposdir=", commands[1])
            self.assertTrue(commands[1].endswith("search obs-studio"))

    def test_copr_search_refines_spaced_target_inside_explicit_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio|OBS Studio",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar obs studio do copr atim/obs-studio", environ=env)
            )
            self.assertEqual(payload["policy"]["policy_outcome"], "allow")
            self.assertEqual(payload["target_resolution"]["status"], "query_refined")
            self.assertEqual(payload["target_resolution"]["source"], "copr_repo_search_query_normalized")
            self.assertEqual(payload["target_resolution"]["consulted_target"], "obs-studio")
            self.assertEqual(payload["target_resolution"]["consulted_targets"], ["obs-studio", "obs studio"])
            self.assertEqual(payload["execution_route"]["route_name"], "copr.procurar")
            self.assertEqual(
                payload["execution_route"]["command"],
                ["dnf", "--disablerepo=*", "--setopt=reposdir=<copr_repo_tempdir>", "search", "obs-studio"],
            )
            self.assertIn(
                "copr_search_scope:explicit_repository_only",
                payload["policy"]["trust_signals"],
            )

    def test_copr_search_reports_no_results_only_inside_requested_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio|OBS Studio",),
            )
            proc = run_module("procurar", "yt-dlp", "do", "copr", "atim/obs-studio", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("não encontrei resultados", proc.stdout)
            self.assertIn("backend 'copr'", proc.stdout)

    def test_copr_search_blocks_when_dnf_copr_capability_is_not_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
                copr_available=False,
            )
            payload = decision_record_to_dict(
                plan_text("procurar obs-studio do copr atim/obs-studio", environ=env)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("copr_dnf_plugin_not_observed", payload["policy"]["trust_gaps"])

    def test_copr_search_blocks_outside_fedora(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("yt-dlp",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar yt-dlp do copr atim/ytdlp", environ=env)
            )
            self.assertEqual(payload["outcome"], "blocked")
            self.assertIn("copr_linux_family_not_supported", payload["policy"]["trust_gaps"])

    def test_copr_install_executes_enable_then_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file, enabled_repo_file, commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
            )
            exit_code, record, _message = perform_execution(
                plan_text("instalar obs-studio do copr atim/obs-studio", environ=env, confirmed=True),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution_route"]["route_name"], "copr.instalar")
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], False)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], True)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "obs-studio")
            self.assertEqual(enabled_repo_file.read_text(encoding="utf-8").strip(), "atim/obs-studio")
            self.assertEqual(
                commands_file.read_text(encoding="utf-8").splitlines(),
                ["copr --help", "-y copr enable atim/obs-studio", "install -y obs-studio"],
            )

    def test_copr_remove_executes_and_keeps_repository_observable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file, enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
                installed_packages=("obs-studio",),
            )
            enabled_repo_file.write_text("atim/obs-studio\n", encoding="utf-8")
            exit_code, record, _message = perform_execution(
                plan_text("remover obs-studio do copr atim/obs-studio", environ=env, confirmed=True),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution_route"]["route_name"], "copr.remover")
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], True)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], False)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")
            self.assertEqual(enabled_repo_file.read_text(encoding="utf-8").strip(), "atim/obs-studio")

    def test_dev_record_exposes_repository_coordinate_and_pre_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
            )
            rendered = render_dev_report(
                "instalar obs-studio do copr atim/obs-studio --confirm",
                environ=env,
            )
            self.assertIn("requested_source:        copr", rendered)
            self.assertIn("source_coordinate:       atim/obs-studio", rendered)
            self.assertIn("source_type:             copr_repository", rendered)
            self.assertIn("scope_label:             pacote do host via COPR", rendered)
            self.assertIn("pre_commands:            sudo dnf -y copr enable atim/obs-studio", rendered)

    def test_dev_record_exposes_repository_restriction_for_copr_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file, _enabled_repo_file, _commands_file = setup_copr_testbed(
                root,
                copr_repo="atim/obs-studio",
                repo_packages=("obs-studio",),
            )
            rendered = render_dev_report(
                "procurar obs-studio do copr atim/obs-studio",
                environ=env,
            )
            self.assertIn("requested_source:        copr", rendered)
            self.assertIn("source_coordinate:       atim/obs-studio", rendered)
            self.assertIn("route_name:              copr.procurar", rendered)
            self.assertIn("consulted_target:        obs-studio", rendered)
            self.assertIn("copr_search_scope:explicit_repository_only", rendered)
            self.assertIn("restrita ao repositório explicitamente informado", rendered)


if __name__ == "__main__":
    unittest.main()

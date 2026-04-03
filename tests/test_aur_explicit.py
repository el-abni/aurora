from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from aurora.install.domain_classifier import classify_text
from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import run_module, setup_aur_testbed, write_os_release, write_stub


class AurExplicitTests(unittest.TestCase):
    def test_classifier_routes_explicit_aur_search_to_host_package_with_separate_source(self) -> None:
        request = classify_text("procurar google chrome no aur")
        self.assertEqual(request.intent, "procurar")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.requested_source, "aur")
        self.assertEqual(request.target, "google chrome")
        self.assertEqual(request.status, "CONSISTENT")
        self.assertIn("source_hint:aur", request.observations)

    def test_classifier_strips_inline_confirm_from_explicit_aur_target(self) -> None:
        request = classify_text("instalar obs-studio no aur --confirm")
        self.assertEqual(request.intent, "instalar")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.requested_source, "aur")
        self.assertEqual(request.target, "obs-studio")

    def test_naked_request_stays_out_of_aur(self) -> None:
        request = classify_text("procurar google chrome")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.requested_source, "")
        self.assertIn("domain_selection:default_host_package", request.observations)

    def test_aur_search_executes_when_paru_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
            )
            proc = run_module("procurar", "google", "chrome", "no", "aur", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("backend 'paru'", proc.stdout)
            self.assertIn("google-chrome", proc.stdout)

    def test_aur_search_refines_spaced_target_to_package_like_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio|OBS Studio",),
            )
            payload = decision_record_to_dict(plan_text("procurar obs studio no aur", environ=env))
            self.assertEqual(payload["target_resolution"]["status"], "query_refined")
            self.assertEqual(payload["target_resolution"]["source"], "aur_search_query_normalized")
            self.assertEqual(payload["target_resolution"]["consulted_target"], "obs-studio")
            self.assertEqual(payload["target_resolution"]["consulted_targets"], ["obs-studio", "obs studio"])
            self.assertTrue(payload["target_resolution"]["canonicalized"])
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")

    def test_aur_search_keeps_hyphenated_target_as_direct_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio|OBS Studio",),
            )
            payload = decision_record_to_dict(plan_text("procurar obs-studio no aur", environ=env))
            self.assertEqual(payload["target_resolution"]["status"], "query_direct")
            self.assertEqual(payload["target_resolution"]["source"], "user_input_search_query")
            self.assertEqual(payload["target_resolution"]["consulted_target"], "obs-studio")
            self.assertEqual(payload["target_resolution"]["consulted_targets"], ["obs-studio", "obs studio"])
            self.assertFalse(payload["target_resolution"]["canonicalized"])
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")

    def test_aur_search_uses_refined_query_to_avoid_spaced_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            write_stub(bin_dir, "pacman", "#!/bin/sh\nexit 0\n")
            write_stub(
                bin_dir,
                "paru",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    -Ss|--aur|--)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "-Ss" ]; then
  if [ "$target" = "obs studio" ]; then
    printf "aur/obs-bridge 1.0-1\\n    OBS Studio Bridge\\n"
    printf "aur/studio-tools 1.0-1\\n    Studio Tools for OBS workflows\\n"
    exit 0
  fi
  if [ "$target" = "obs-studio" ]; then
    printf "aur/obs-studio 1.0-1\\n    OBS Studio\\n"
    exit 0
  fi
fi
exit 1
""",
            )
            write_os_release(root, distro_id="cachyos", distro_like="arch", name="CachyOS")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}

            proc = run_module("procurar", "obs", "studio", "no", "aur", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("obs-studio", proc.stdout)
            self.assertNotIn("obs-bridge", proc.stdout)
            self.assertNotIn("studio-tools", proc.stdout)

    def test_aur_search_accepts_parseable_results_even_when_helper_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio-git|OBS Studio Git",),
            )
            bin_dir = root / "bin"
            write_stub(
                bin_dir,
                "paru",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    -Ss|--aur|--)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "-Ss" ] && [ "$target" = "obs-studio-git" ]; then
  printf "aur/obs-studio-git 1.0-1\\n    OBS Studio Git\\n"
  echo "warning: aur rpc returned an auxiliary warning" >&2
  exit 1
fi
exit 1
""",
            )
            proc = run_module("procurar", "obs-studio-git", "no", "aur", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("obs-studio-git", proc.stdout)
            self.assertNotIn("erro operacional", proc.stdout)

    def test_explicit_aur_request_blocks_when_helper_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(root, helpers=())
            payload = decision_record_to_dict(plan_text("procurar google chrome no aur", environ=env))
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("aur_helper_not_observed", payload["policy"]["trust_gaps"])
            self.assertEqual(payload["request"]["requested_source"], "aur")

    def test_explicit_aur_request_blocks_when_only_yay_is_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(root, helpers=("yay",))
            payload = decision_record_to_dict(plan_text("procurar yay no aur", environ=env))
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("aur_supported_helper_not_observed", payload["policy"]["trust_gaps"])
            self.assertIn("aur_helper_out_of_contract_observed", payload["policy"]["trust_gaps"])
            self.assertEqual(payload["host_profile"]["observed_third_party_package_tools"], ["yay"])

    def test_aur_install_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
            )
            payload = decision_record_to_dict(plan_text("instalar google chrome no aur", environ=env))
            self.assertEqual(payload["policy"]["source_type"], "aur_repository")
            self.assertEqual(payload["policy"]["trust_level"], "third_party_build")
            self.assertEqual(payload["policy"]["policy_outcome"], "require_confirmation")
            self.assertEqual(payload["execution_route"]["route_name"], "aur.instalar")
            self.assertTrue(payload["execution_route"]["interactive_passthrough"])
            self.assertEqual(payload["target_resolution"]["resolved_target"], "google-chrome")

    def test_aur_install_exposes_consulted_query_for_spaced_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio|OBS Studio",),
            )
            payload = decision_record_to_dict(plan_text("instalar obs studio no aur", environ=env))
            self.assertEqual(payload["target_resolution"]["source"], "aur_search_normalized_query")
            self.assertEqual(payload["target_resolution"]["consulted_target"], "obs-studio")
            self.assertEqual(payload["target_resolution"]["consulted_targets"], ["obs-studio", "obs studio"])
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")

    def test_aur_install_records_all_consulted_queries_when_only_package_like_search_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio|OBS Studio",),
            )
            bin_dir = root / "bin"
            write_stub(
                bin_dir,
                "paru",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    -Ss|--aur|--)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "-Ss" ]; then
  if [ "$target" = "obs-studio" ]; then
    printf "aur/obs-studio 1.0-1\\n    OBS Studio\\n"
    exit 0
  fi
  echo "no packages found" >&2
  exit 1
fi
exit 1
""",
            )
            payload = decision_record_to_dict(plan_text("instalar obs studio no aur", environ=env))
            self.assertEqual(payload["target_resolution"]["consulted_target"], "obs-studio")
            self.assertEqual(payload["target_resolution"]["consulted_targets"], ["obs-studio", "obs studio"])
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio")

    def test_aur_install_resolves_exact_package_like_target_even_with_nonzero_search_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio-git|OBS Studio Git",),
            )
            bin_dir = root / "bin"
            write_stub(
                bin_dir,
                "paru",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    -Ss|--aur|--)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "-Ss" ] && [ "$target" = "obs-studio-git" ]; then
  printf "aur/obs-studio-git 1.0-1\\n    OBS Studio Git\\n"
  echo "warning: aur rpc returned an auxiliary warning" >&2
  exit 1
fi
echo "no packages found" >&2
exit 1
""",
            )
            payload = decision_record_to_dict(plan_text("instalar obs-studio-git no aur", environ=env, confirmed=True))
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio-git")
            self.assertEqual(payload["target_resolution"]["diagnostic_command"], ["paru", "-Ss", "--aur", "--", "obs-studio-git"])
            self.assertEqual(payload["target_resolution"]["diagnostic_exit_code"], 1)
            self.assertIn("auxiliary warning", payload["target_resolution"]["diagnostic_stderr"])
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio-git")

    def test_aur_install_keeps_exact_resolution_when_auxiliary_query_fails_after_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio-git|OBS Studio Git",),
            )
            bin_dir = root / "bin"
            write_stub(
                bin_dir,
                "paru",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    -Ss|--aur|--)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "-Ss" ] && [ "$target" = "obs-studio-git" ]; then
  printf "aur/obs-studio-git 1.0-1\\n    OBS Studio Git\\n"
  exit 0
fi
if [ "$action" = "-Ss" ] && [ "$target" = "obs studio git" ]; then
  exit 1
fi
echo "no packages found" >&2
exit 1
""",
            )
            payload = decision_record_to_dict(plan_text("instalar obs-studio-git no aur", environ=env, confirmed=True))
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "obs-studio-git")
            self.assertEqual(payload["target_resolution"]["diagnostic_command"], ["paru", "-Ss", "--aur", "--", "obs studio git"])
            self.assertEqual(payload["target_resolution"]["diagnostic_exit_code"], 1)
            self.assertEqual(payload["execution_route"]["command"][-1], "obs-studio-git")

    def test_aur_install_reports_precise_search_command_on_operational_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio-git|OBS Studio Git",),
            )
            bin_dir = root / "bin"
            write_stub(
                bin_dir,
                "paru",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    -Ss|--aur|--)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "-Ss" ] && [ "$target" = "obs-studio-git" ]; then
  echo "error: aur rpc unavailable" >&2
  exit 7
fi
echo "no packages found" >&2
exit 1
""",
            )
            payload = decision_record_to_dict(plan_text("instalar obs-studio-git no aur", environ=env, confirmed=True))
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "unresolved")
            self.assertIn("paru -Ss --aur -- obs-studio-git", payload["target_resolution"]["reason"])
            self.assertIn("exit code 7", payload["target_resolution"]["reason"])
            self.assertEqual(payload["target_resolution"]["diagnostic_command"], ["paru", "-Ss", "--aur", "--", "obs-studio-git"])
            self.assertEqual(payload["target_resolution"]["diagnostic_exit_code"], 7)
            self.assertEqual(payload["target_resolution"]["diagnostic_stdout"], "")
            self.assertIn("aur rpc unavailable", payload["target_resolution"]["diagnostic_stderr"])

    def test_aur_install_executes_with_confirmation_and_canonicalized_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
            )
            observed_commands: list[tuple[str, ...]] = []

            def fake_interactive_runner(args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
                observed_commands.append(tuple(args))
                with aur_state_file.open("a", encoding="utf-8") as handle:
                    handle.write("google-chrome\n")
                return subprocess.CompletedProcess(args, 0, "", "")

            exit_code, record, _message = perform_execution(
                plan_text("instalar google chrome no aur", environ=env, confirmed=True),
                interactive_runner=fake_interactive_runner,
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                observed_commands,
                [("paru", "-S", "--aur", "--needed", "--noconfirm", "--", "google-chrome")],
            )
            self.assertEqual(payload["target_resolution"]["resolved_target"], "google-chrome")
            self.assertEqual(payload["execution_route"]["command"][-1], "google-chrome")
            self.assertTrue(payload["execution_route"]["interactive_passthrough"])
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertTrue(payload["execution"]["interactive_passthrough"])
            self.assertIn("google-chrome", aur_state_file.read_text(encoding="utf-8"))

    def test_aur_install_cli_announces_interactive_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
            )
            proc = run_module("instalar", "google", "chrome", "no", "aur", "--confirm", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("entregando o terminal ao helper interativo 'paru'", proc.stdout)
            self.assertIn("Quando ele terminar, vou validar o estado final", proc.stdout)
            self.assertIn("installed google-chrome", proc.stdout)
            self.assertIn("o helper interativo 'paru' terminou. Validando o estado final.", proc.stdout)
            self.assertIn("pronto, o pacote AUR 'google chrome' está instalado", proc.stdout)
            self.assertIn("google-chrome", aur_state_file.read_text(encoding="utf-8"))

    def test_aur_mutation_strips_source_and_control_markers_before_resolution(self) -> None:
        cases = (
            ("instalar obs-studio no aur --confirm", "obs-studio", "obs-studio"),
            ("remover obs-studio no aur --confirm", "obs-studio", "obs-studio"),
            ("instalar obs studio no aur --confirm", "obs studio", "obs-studio"),
            ("remover obs studio no aur --confirm", "obs studio", "obs-studio"),
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("obs-studio|OBS Studio",),
                aur_installed_packages=("obs-studio",),
            )

            for text, expected_target, expected_resolved in cases:
                with self.subTest(text=text):
                    payload = decision_record_to_dict(plan_text(text, environ=env, confirmed=True))
                    self.assertEqual(payload["request"]["target"], expected_target)
                    self.assertEqual(payload["target_resolution"]["consulted_target"], "obs-studio")
                    self.assertEqual(payload["target_resolution"]["resolved_target"], expected_resolved)
                    self.assertEqual(payload["execution_route"]["command"][-1], expected_resolved)

    def test_aur_install_noops_when_foreign_package_is_already_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
                aur_installed_packages=("google-chrome",),
            )
            exit_code, record, message = perform_execution(
                plan_text("instalar google chrome no aur", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution"]["status"], "noop")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], True)
            self.assertIsNone(payload["execution"]["post_probe"])
            self.assertIn("já está instalado como pacote AUR neste host", message)
            self.assertIn("google-chrome", aur_state_file.read_text(encoding="utf-8"))

    def test_aur_install_blocks_on_native_source_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, native_state_file = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
                native_installed_packages=("google-chrome",),
            )
            payload = decision_record_to_dict(plan_text("instalar google chrome no aur", environ=env, confirmed=True))
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "source_mismatch")
            self.assertIn("pacote oficial do host", payload["target_resolution"]["reason"])
            self.assertIn("google-chrome", native_state_file.read_text(encoding="utf-8"))

    def test_aur_install_blocks_on_ambiguous_exact_match_before_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=(
                    "google-chrome|Google Chrome Stable",
                    "googlechrome|Google Chrome Mirror",
                ),
            )
            exit_code, record, message = perform_execution(
                plan_text("instalar google chrome no aur", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "ambiguous")
            self.assertNotIn("execution_route", payload)
            self.assertEqual(payload["execution"]["status"], "blocked")
            self.assertIn("bloqueado por resolução de alvo", message)

    def test_aur_install_blocks_on_missing_reliable_match_before_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome-beta|Google Chrome Beta",),
            )
            exit_code, record, message = perform_execution(
                plan_text("instalar google chrome no aur", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "not_found")
            self.assertEqual(payload["target_resolution"]["consulted_targets"], ["google-chrome", "google chrome"])
            self.assertNotIn("execution_route", payload)
            self.assertEqual(payload["execution"]["status"], "blocked")
            self.assertIn("bloqueado por resolução de alvo", message)

    def test_aur_remove_resolves_foreign_package_from_human_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
                aur_installed_packages=("google-chrome",),
            )
            payload = decision_record_to_dict(plan_text("remover google chrome no aur", environ=env, confirmed=True))
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["source"], "pacman_foreign_list")
            self.assertEqual(payload["execution_route"]["command"][-1], "google-chrome")

            exit_code, record, _message = perform_execution(
                plan_text("remover google chrome no aur", environ=env, confirmed=True),
                environ=env,
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(decision_record_to_dict(record)["execution"]["status"], "executed")
            self.assertEqual(aur_state_file.read_text(encoding="utf-8").strip(), "")

    def test_aur_remove_noops_when_foreign_package_is_already_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
            )
            exit_code, record, message = perform_execution(
                plan_text("remover google chrome no aur", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["target_resolution"]["status"], "absent")
            self.assertEqual(payload["execution_route"]["command"][-1], "google-chrome")
            self.assertEqual(payload["execution"]["status"], "noop")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], False)
            self.assertIsNone(payload["execution"]["post_probe"])
            self.assertIn("já não está instalado como pacote AUR neste host", message)
            self.assertEqual(aur_state_file.read_text(encoding="utf-8"), "")

    def test_aur_remove_requires_confirmation_when_foreign_package_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, aur_state_file, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
                aur_installed_packages=("google-chrome",),
            )
            blocked = run_module("remover", "google", "chrome", "no", "aur", env=env)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("exige confirmação explícita", blocked.stdout)
            self.assertIn("google-chrome", aur_state_file.read_text(encoding="utf-8"))

            confirmed = run_module("remover", "google", "chrome", "no", "aur", "--confirm", env=env)
            self.assertEqual(confirmed.returncode, 0)
            self.assertIn("foi removido", confirmed.stdout)
            self.assertEqual(aur_state_file.read_text(encoding="utf-8").strip(), "")

    def test_aur_remove_blocks_when_target_is_native_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, native_state_file = setup_aur_testbed(
                root,
                native_installed_packages=("google-chrome",),
            )
            payload = decision_record_to_dict(plan_text("remover google chrome no aur", environ=env, confirmed=True))
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "source_mismatch")
            self.assertEqual(payload["target_resolution"]["source"], "pacman_native_list")
            self.assertIn("google-chrome", native_state_file.read_text(encoding="utf-8"))

    def test_dev_record_exposes_requested_source_and_aur_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _aur_state, _native_state = setup_aur_testbed(
                root,
                repo_packages=("google-chrome|Google Chrome",),
            )
            rendered = render_dev_report("procurar google chrome no aur", environ=env)
            self.assertIn("requested_source:        aur", rendered)
            self.assertIn("source_type:             aur_repository", rendered)
            self.assertIn("route_name:              aur.procurar", rendered)
            self.assertIn("scope_label:             pacote AUR no host", rendered)
            self.assertIn("consulted_target:", rendered)


if __name__ == "__main__":
    unittest.main()

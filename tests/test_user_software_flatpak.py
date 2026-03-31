from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.domain_classifier import classify_text
from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import run_module, setup_flatpak_testbed, write_os_release, write_stub


class UserSoftwareFlatpakTests(unittest.TestCase):
    def test_classifier_routes_explicit_flatpak_search_to_user_software(self) -> None:
        request = classify_text("procurar firefox no flatpak")
        self.assertEqual(request.intent, "procurar")
        self.assertEqual(request.domain_kind, "user_software")
        self.assertEqual(request.target, "firefox")
        self.assertEqual(request.status, "CONSISTENT")
        self.assertIn("source_hint:flatpak", request.observations)

    def test_classifier_keeps_compound_flatpak_target_without_quotes(self) -> None:
        request = classify_text("instalar obs studio no flatpak")
        self.assertEqual(request.intent, "instalar")
        self.assertEqual(request.domain_kind, "user_software")
        self.assertEqual(request.target, "obs studio")
        self.assertEqual(request.status, "CONSISTENT")

    def test_naked_search_stays_in_host_package_by_default(self) -> None:
        request = classify_text("procurar firefox")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.target, "firefox")
        self.assertIn("domain_selection:default_host_package", request.observations)

    def test_flatpak_search_executes_when_requested_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("firefox",),
                name="Ubuntu",
            )
            proc = run_module("procurar", "firefox", "no", "flatpak", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("encontrei resultados", proc.stdout)
            self.assertIn("flathub", proc.stdout)

    def test_atomic_host_keeps_naked_search_on_host_package_but_allows_explicit_flatpak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            write_stub(bin_dir, "dnf", "#!/bin/sh\nexit 0\n")
            write_stub(
                bin_dir,
                "flatpak",
                "#!/bin/sh\nif [ \"$1\" = \"search\" ]; then echo \"firefox\tfirefox app\t1.0\tstable\tflathub\"; exit 0; fi\nexit 1\n",
            )
            write_os_release(root, distro_id="bazzite", distro_like="fedora", name="Bazzite")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}

            naked = run_module("procurar", "firefox", env=env)
            explicit = run_module("procurar", "firefox", "no", "flatpak", env=env)

            self.assertEqual(naked.returncode, 1)
            self.assertIn("bloqueado por política", naked.stdout)
            self.assertEqual(explicit.returncode, 0)
            self.assertIn("backend 'flatpak'", explicit.stdout)

    def test_dev_record_exposes_user_software_policy_and_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("obs-studio",),
                name="Ubuntu",
            )
            rendered = render_dev_report("procurar obs-studio no flatpak", environ=env)
            self.assertIn("domain_kind:             user_software", rendered)
            self.assertIn("source_type:             flatpak_remote", rendered)
            self.assertIn("route_name:              flatpak.procurar", rendered)
            self.assertIn("observations:", rendered)

    def test_flatpak_install_resolves_hyphenated_human_target_to_app_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            payload = decision_record_to_dict(plan_text("instalar obs-studio no flatpak", environ=env))
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "com.obsproject.Studio")
            self.assertEqual(payload["target_resolution"]["source"], "flatpak_search_normalized_query")
            self.assertTrue(payload["target_resolution"]["canonicalized"])
            self.assertEqual(payload["execution_route"]["command"][-1], "com.obsproject.Studio")

    def test_flatpak_install_keeps_hyphen_space_equivalence_when_literal_search_returns_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            write_stub(
                bin_dir,
                "flatpak",
                """#!/bin/sh
action="$1"
target=""
for arg in "$@"; do
  case "$arg" in
    search|--columns=*|--show-ref|--user|--system|--noninteractive|-y|--app|flathub)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
if [ "$action" = "search" ]; then
  if [ "$target" = "obs-studio" ]; then
    printf "org.example.Noise\\tNoise App\\n"
    exit 0
  fi
  if [ "$target" = "obs studio" ]; then
    printf "org.example.Noise\\tNoise App\\ncom.obsproject.Studio\\tOBS Studio\\n"
    exit 0
  fi
fi
exit 0
""",
            )
            write_os_release(root, distro_id="ubuntu", distro_like="debian", name="Ubuntu")
            env = {"PATH": str(bin_dir), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}

            payload = decision_record_to_dict(plan_text("instalar obs-studio no flatpak", environ=env))
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["source"], "flatpak_search_normalized_query")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "com.obsproject.Studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "com.obsproject.Studio")

    def test_flatpak_install_resolves_spaced_human_target_in_real_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            exit_code, record, _message = perform_execution(
                plan_text("instalar obs studio no flatpak", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["target_resolution"]["resolved_target"], "com.obsproject.Studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "com.obsproject.Studio")
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertIn("com.obsproject.Studio", state_file.read_text(encoding="utf-8"))

    def test_flatpak_install_executes_via_cli_for_compound_name_without_quotes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            proc = run_module("instalar", "obs", "studio", "no", "flatpak", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("está instalado", proc.stdout)
            self.assertIn("com.obsproject.Studio", state_file.read_text(encoding="utf-8"))

    def test_flatpak_install_executes_via_cli_for_hyphenated_human_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            proc = run_module("instalar", "obs-studio", "no", "flatpak", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("está instalado", proc.stdout)
            self.assertIn("com.obsproject.Studio", state_file.read_text(encoding="utf-8"))

    def test_flatpak_install_uses_direct_app_id_when_target_is_already_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            payload = decision_record_to_dict(plan_text("instalar com.obsproject.Studio no flatpak", environ=env))
            self.assertEqual(payload["target_resolution"]["status"], "direct")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "com.obsproject.Studio")
            self.assertEqual(payload["target_resolution"]["source"], "user_input_app_id")
            self.assertFalse(payload["target_resolution"]["canonicalized"])
            self.assertEqual(payload["execution_route"]["command"][-1], "com.obsproject.Studio")

    def test_flatpak_install_executes_with_pre_and_post_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("firefox",),
                name="Ubuntu",
            )
            exit_code, record, _message = perform_execution(
                plan_text("instalar firefox no flatpak", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["execution_route"]["route_name"], "flatpak.instalar")
            self.assertEqual(payload["execution"]["status"], "executed")
            self.assertEqual(payload["execution"]["pre_probe"]["package_present"], False)
            self.assertEqual(payload["execution"]["post_probe"]["package_present"], True)
            self.assertIn("firefox", state_file.read_text(encoding="utf-8"))

    def test_flatpak_install_noops_when_app_is_already_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("firefox",),
                installed_apps=("firefox",),
                name="Ubuntu",
            )
            proc = run_module("instalar", "firefox", "no", "flatpak", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("já está instalado na instalação do usuário", proc.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "firefox")

    def test_flatpak_install_reports_app_not_found_for_direct_app_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                name="Ubuntu",
            )
            proc = run_module("instalar", "com.obsproject.Studio", "no", "flatpak", env=env)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("não encontrei o software 'com.obsproject.Studio'", proc.stdout)

    def test_flatpak_install_blocks_when_target_resolution_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=(
                    "com.obsproject.Studio|OBS Studio",
                    "io.test.OBSStudio|OBS Studio",
                ),
                name="Ubuntu",
            )
            exit_code, record, message = perform_execution(
                plan_text("instalar obs studio no flatpak", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["outcome"], "blocked")
            self.assertEqual(payload["target_resolution"]["status"], "ambiguous")
            self.assertEqual(len(payload["target_resolution"]["candidates"]), 2)
            self.assertNotIn("execution_route", payload)
            self.assertIn("bloqueado por resolução de alvo", message)

    def test_flatpak_install_blocks_when_target_resolution_finds_no_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            exit_code, record, message = perform_execution(
                plan_text("instalar obs no flatpak", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["target_resolution"]["status"], "not_found")
            self.assertNotIn("execution_route", payload)
            self.assertIn("bloqueado por resolução de alvo", message)

    def test_flatpak_remove_noops_when_app_is_already_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("firefox",),
                name="Ubuntu",
            )
            proc = run_module("remover", "firefox", "no", "flatpak", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("já não está instalado na instalação do usuário", proc.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_flatpak_remove_resolves_human_target_from_user_installation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                installed_apps=("com.obsproject.Studio",),
                name="Ubuntu",
            )
            exit_code, record, _message = perform_execution(
                plan_text("remover obs studio no flatpak", environ=env, confirmed=True),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["target_resolution"]["status"], "resolved")
            self.assertEqual(payload["target_resolution"]["source"], "flatpak_list_user")
            self.assertEqual(payload["target_resolution"]["resolved_target"], "com.obsproject.Studio")
            self.assertEqual(payload["execution_route"]["command"][-1], "com.obsproject.Studio")
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_flatpak_remove_executes_via_cli_for_compound_name_without_quotes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                installed_apps=("com.obsproject.Studio",),
                name="Ubuntu",
            )
            proc = run_module("remover", "obs", "studio", "no", "flatpak", "--confirm", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("foi removido", proc.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_flatpak_remove_executes_via_cli_for_hyphenated_human_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                installed_apps=("com.obsproject.Studio",),
                name="Ubuntu",
            )
            proc = run_module("remover", "obs-studio", "no", "flatpak", "--confirm", env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("foi removido", proc.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_flatpak_remove_human_target_noops_when_matching_install_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("com.obsproject.Studio|OBS Studio",),
                name="Ubuntu",
            )
            exit_code, record, message = perform_execution(
                plan_text("remover obs studio no flatpak", environ=env),
                environ=env,
            )
            payload = decision_record_to_dict(record)
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["target_resolution"]["status"], "absent")
            self.assertEqual(payload["execution"]["status"], "noop")
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")
            self.assertIn("já não está instalado na instalação do usuário", message)

    def test_flatpak_remove_requires_confirmation_when_app_is_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_file = setup_flatpak_testbed(
                root,
                distro_id="ubuntu",
                distro_like="debian",
                repo_apps=("firefox",),
                installed_apps=("firefox",),
                name="Ubuntu",
            )
            blocked = run_module("remover", "firefox", "no", "flatpak", env=env)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("exige confirmação explícita", blocked.stdout)
            self.assertIn("firefox", state_file.read_text(encoding="utf-8"))

            confirmed = run_module("remover", "firefox", "no", "flatpak", "--confirm", env=env)
            self.assertEqual(confirmed.returncode, 0)
            self.assertIn("foi removido", confirmed.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8"), "")

    def test_explicit_flatpak_request_blocks_when_backend_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_os_release(root, distro_id="ubuntu", distro_like="debian", name="Ubuntu")
            env = {"PATH": str(root / "bin"), "AURORA_OS_RELEASE_PATH": str(root / "os-release")}
            payload = decision_record_to_dict(plan_text("procurar firefox no flatpak", environ=env))
            self.assertEqual(payload["policy"]["policy_outcome"], "block")
            self.assertIn("flatpak_backend_not_observed", payload["policy"]["trust_gaps"])


if __name__ == "__main__":
    unittest.main()

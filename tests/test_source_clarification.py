from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from aurora import cli
from aurora.install.domain_classifier import classify_text
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from support import run_module, setup_aur_testbed, setup_flatpak_testbed, setup_host_package_testbed


class SourceClarificationTests(unittest.TestCase):
    def test_source_clarification_orients_without_executor(self) -> None:
        cases = (
            (["explicar", "fontes"], ("Fontes e superfícies", "pedido nu continua")),
            (["explicar", "superfícies"], ("Superfície é onde", "não executa backend")),
            (["como", "escolher", "fonte", "para", "firefox?"], ("marque a fonte", "instalar firefox")),
            (["qual", "fonte", "usar", "para", "firefox?"], ("marque a fonte", "não busca em tudo")),
            (["onde", "instalar", "firefox?"], ("onde instalar", "no flatpak")),
            (["como", "instalar", "firefox", "no", "flatpak?"], ("instalação Flatpak", "remote observado")),
            (["como", "instalar", "firefox", "no", "aur?"], ("instalação AUR", "no aur --confirm")),
            (
                ["como", "instalar", "pacote", "na", "toolbox", "devbox?"],
                ("toolbox 'devbox'", "não cria toolbox"),
            ),
            (
                ["como", "instalar", "pacote", "na", "distrobox", "devbox?"],
                ("distrobox 'devbox'", "não cria distrobox"),
            ),
            (
                ["como", "instalar", "pacote", "no", "rpm-ostree?"],
                ("rpm-ostree", "busca rpm-ostree não está aberta"),
            ),
            (["diferença", "entre", "host", "e", "flatpak"], ("Host instala", "Flatpak exige")),
            (
                ["diferença", "entre", "aur", "e", "pacote", "do", "host"],
                ("Pacote do host", "AUR é fonte terceira"),
            ),
        )
        for args, expected_fragments in cases:
            with self.subTest(args=args):
                stdout = io.StringIO()
                with mock.patch("aurora.cli.execute_text") as execute_text:
                    with redirect_stdout(stdout):
                        exit_code = cli.main(args)
                rendered = stdout.getvalue()
                self.assertEqual(exit_code, 0)
                execute_text.assert_not_called()
                for expected in expected_fragments:
                    self.assertIn(expected, rendered)
                self.assertIn("não", rendered)

    def test_automatic_source_choice_blocks_before_executor(self) -> None:
        cases = (
            ["instalar", "firefox", "onde", "for", "melhor"],
            ["instalar", "firefox", "na", "melhor", "fonte"],
            ["instalar", "firefox", "na", "melhor", "superfície"],
        )
        for args in cases:
            with self.subTest(args=args):
                stdout = io.StringIO()
                with mock.patch("aurora.cli.execute_text") as execute_text:
                    with redirect_stdout(stdout):
                        exit_code = cli.main(args)
                rendered = stdout.getvalue()
                self.assertEqual(exit_code, 1)
                execute_text.assert_not_called()
                self.assertIn("Não escolho fonte ou superfície automaticamente", rendered)
                self.assertIn("no flatpak", rendered)
                self.assertIn("não executou backend", rendered)

    def test_existing_sources_topic_is_preserved(self) -> None:
        proc = run_module("fontes")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Fontes e superfícies são explícitas", proc.stdout)
        self.assertIn("host_package", proc.stdout)

    def test_operational_commands_still_fall_through_to_kernel(self) -> None:
        cases = (
            ["instalar", "firefox"],
            ["instalar", "firefox", "no", "flatpak"],
            ["instalar", "firefox", "no", "aur"],
            ["instalar", "firefox", "na", "toolbox", "devbox"],
            ["instalar", "firefox", "na", "distrobox", "devbox"],
        )
        for args in cases:
            with self.subTest(args=args):
                with mock.patch("aurora.cli.execute_text", return_value=0) as execute_text:
                    exit_code = cli.main(args)
                self.assertEqual(exit_code, 0)
                execute_text.assert_called_once_with(" ".join(args), confirmed=False)

    def test_operational_classification_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state = setup_host_package_testbed(
                Path(tmp),
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("firefox|Mozilla Firefox",),
            )
            payload = decision_record_to_dict(plan_text("instalar firefox", environ=env))

        self.assertEqual(payload["schema"]["schema_id"], "aurora.decision_record.v1")
        self.assertEqual(payload["request"]["domain_kind"], "host_package")
        self.assertEqual(payload["request"]["execution_surface"], "host")
        self.assertEqual(payload["policy"]["source_type"], "host_package_manager")
        self.assertEqual(payload["facts"]["local_model"]["mode"], "model_off")
        self.assertEqual(payload["facts"]["local_model"]["status"], "disabled")

    def test_explicit_flatpak_and_aur_stay_in_kernel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state = setup_flatpak_testbed(
                Path(tmp),
                distro_id="cachyos",
                distro_like="arch",
                repo_apps=("org.mozilla.firefox|Firefox|flathub",),
            )
            flatpak_payload = decision_record_to_dict(plan_text("instalar firefox no flatpak", environ=env))

        self.assertEqual(flatpak_payload["request"]["domain_kind"], "user_software")
        self.assertEqual(flatpak_payload["request"]["requested_source"], "flatpak")
        self.assertEqual(flatpak_payload["policy"]["source_type"], "flatpak_remote")

        with tempfile.TemporaryDirectory() as tmp:
            env, _aur_state, _native_state = setup_aur_testbed(
                Path(tmp),
                repo_packages=("google-chrome|Google Chrome",),
            )
            aur_payload = decision_record_to_dict(plan_text("instalar google chrome no aur", environ=env))

        self.assertEqual(aur_payload["request"]["requested_source"], "aur")
        self.assertEqual(aur_payload["policy"]["source_type"], "aur_repository")

    def test_explicit_toolbox_and_distrobox_stay_in_kernel_classification(self) -> None:
        toolbox = classify_text("instalar firefox na toolbox devbox")
        self.assertEqual(toolbox.execution_surface, "toolbox")
        self.assertEqual(toolbox.environment_target, "devbox")

        distrobox = classify_text("instalar firefox na distrobox devbox")
        self.assertEqual(distrobox.execution_surface, "distrobox")
        self.assertEqual(distrobox.environment_target, "devbox")

    def test_broad_language_and_discovery_stay_out_of_scope(self) -> None:
        cases = (
            ("quero", "instalar", "firefox"),
            ("me", "recomenda", "uma", "fonte", "para", "firefox"),
            ("busca", "em", "tudo", "e", "instala", "firefox"),
        )
        for args in cases:
            with self.subTest(args=args):
                proc = run_module(*args)
                self.assertEqual(proc.returncode, 1)
                self.assertIn("Fora do recorte atual", proc.stdout)


if __name__ == "__main__":
    unittest.main()

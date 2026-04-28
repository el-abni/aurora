from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from aurora import cli
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from support import ROOT, run_module, run_script, setup_host_package_testbed

CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class ConversationMediationTests(unittest.TestCase):
    def test_version_aliases_match_public_version(self) -> None:
        for script_name in ("aurora", "auro"):
            for token in ("versão", "versao"):
                with self.subTest(script=script_name, token=token):
                    proc = run_script(script_name, token)
                    self.assertEqual(proc.returncode, 0)
                    self.assertEqual(proc.stdout.strip(), f"Aurora {CURRENT_VERSION}")

    def test_orientation_topics_return_zero(self) -> None:
        cases = (
            (("exemplos",), "Exemplos seguros"),
            (("limites",), "Limites atuais"),
            (("comandos",), "Comandos sustentados"),
            (("fontes",), "Fontes e superfícies"),
            (("modelo", "local"), "Modelo local"),
            (("decision", "record"), "aurora.decision_record.v1"),
            (("o", "que", "você", "faz"), "orientação em PT-BR"),
            (("como", "eu", "uso"), "Uso recomendado"),
        )
        for args, expected in cases:
            with self.subTest(args=args):
                proc = run_module(*args)
                self.assertEqual(proc.returncode, 0)
                self.assertIn(expected, proc.stdout)
                self.assertNotIn("Fora do recorte atual", proc.stdout)

    def test_closed_questions_orient_without_executor(self) -> None:
        cases = (
            (["como", "instalar", "firefox?"], "aurora instalar firefox"),
            (["como", "procurar", "firefox?"], "aurora procurar firefox"),
            (["como", "remover", "firefox?"], "aurora remover firefox --confirm"),
            (["como", "atualizar", "sistema?"], "aurora atualizar sistema --confirm"),
        )
        for args, expected in cases:
            with self.subTest(args=args):
                stdout = io.StringIO()
                with mock.patch("aurora.cli.execute_text") as execute_text:
                    with redirect_stdout(stdout):
                        exit_code = cli.main(args)
                self.assertEqual(exit_code, 0)
                execute_text.assert_not_called()
                self.assertIn(expected, stdout.getvalue())
                self.assertIn("não", stdout.getvalue())

    def test_broad_natural_language_stays_out_of_scope(self) -> None:
        proc = run_module("quero", "instalar", "firefox")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Fora do recorte atual", proc.stdout)

    def test_existing_operational_search_still_uses_kernel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state = setup_host_package_testbed(
                Path(tmp),
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("firefox|Mozilla Firefox",),
            )
            proc = run_module("procurar", "firefox", env=env)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("backend 'pacman'", proc.stdout)
        self.assertIn("Mozilla Firefox", proc.stdout)

    def test_decision_record_schema_and_model_off_remain_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _state = setup_host_package_testbed(
                Path(tmp),
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("firefox|Mozilla Firefox",),
            )
            payload = decision_record_to_dict(plan_text("procurar firefox", environ=env))

        self.assertEqual(payload["schema"]["schema_id"], "aurora.decision_record.v1")
        self.assertEqual(payload["schema"]["schema_version"], "v1")
        self.assertEqual(payload["facts"]["local_model"]["mode"], "model_off")
        self.assertEqual(payload["facts"]["local_model"]["status"], "disabled")


if __name__ == "__main__":
    unittest.main()

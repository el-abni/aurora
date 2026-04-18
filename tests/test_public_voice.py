from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.observability.dev_command import render_dev_report
from aurora.presentation.messages import (
    blocked_message,
    interactive_handoff_start_message,
    invalid_command_message,
    mediated_execution_start_message,
    mutation_success_message,
    search_results_message,
)
from support import setup_host_package_testbed


class PublicVoiceTests(unittest.TestCase):
    def test_primary_public_messages_gain_single_discrete_indicator(self) -> None:
        invalid = invalid_command_message()
        blocked = blocked_message("falta confirmacao explicita nesta rodada.")
        success = mutation_success_message("instalar", "ripgrep")
        info = interactive_handoff_start_message("paru")

        self.assertTrue(invalid.startswith("❌ | 🌌 "))
        self.assertTrue(blocked.startswith("❌ | 🌌 "))
        self.assertTrue(success.startswith("✅ | 🌌 "))
        self.assertTrue(info.startswith("ℹ️ | 🌌 "))
        self.assertEqual(invalid.count("🌌"), 1)
        self.assertEqual(blocked.count("🌌"), 1)
        self.assertEqual(success.count("🌌"), 1)
        self.assertEqual(info.count("🌌"), 1)

    def test_multiline_search_message_marks_only_the_first_line(self) -> None:
        message = search_results_message(
            "firefox",
            "pacman",
            "firefox browser\nfirefox-beta browser beta",
        )

        lines = message.splitlines()
        self.assertTrue(lines[0].startswith("✅ | 🌌 "))
        self.assertTrue(all("🌌" not in line for line in lines[1:]))

    def test_mediated_execution_messages_follow_info_visual_pattern(self) -> None:
        message = mediated_execution_start_message("toolbox", "devbox", "pacman")

        self.assertTrue(message.startswith("ℹ️ | 🌌 "))
        self.assertIn("Vou iniciar a execução mediada na toolbox 'devbox'", message)

    def test_dev_report_stays_technical_without_speech_indicator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox",),
            )
            rendered = render_dev_report("procurar firefox", environ=env)
            self.assertIn("Aurora decision record", rendered)
            self.assertIn("summary:                 Vou procurar o pacote do host 'firefox'.", rendered)
            self.assertNotIn("🌌 ", rendered)


if __name__ == "__main__":
    unittest.main()

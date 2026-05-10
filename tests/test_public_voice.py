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
from aurora.presentation.profile import PresentationProfile, normalize_profile
from aurora.presentation.orientation import render_orientation
from aurora.presentation.source_clarification import render_source_clarification
from aurora.semantics.orientation import QUESTION_INSTALL, OrientationRequest
from aurora.semantics.source_clarification import SourceClarificationKind, SourceClarificationRequest
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

    def test_presentation_profiles_are_rendering_only_for_public_guidance(self) -> None:
        request = SourceClarificationRequest(
            kind=SourceClarificationKind.BLOCK_FLATPAK_REMOTE_CHOICE,
            target="firefox",
            blocking=True,
        )

        direct = render_source_clarification(request, profile=PresentationProfile.DIRECT)
        explanatory = render_source_clarification(request)
        beginner = render_source_clarification(request, profile=PresentationProfile.BEGINNER)

        for rendered in (direct, explanatory, beginner):
            self.assertIn("Não escolho o melhor remote Flatpak para 'firefox'", rendered)
            self.assertIn("não escolhe o melhor remote", rendered)
            self.assertIn("não faz fallback entre remotes", rendered)
            self.assertIn("não executou backend", rendered)
            self.assertIn("decision record", rendered)

        self.assertIn("Limites:", direct)
        self.assertIn("Limites preservados:", explanatory)
        self.assertIn("Caminho seguro:", beginner)
        self.assertIn("O que a Aurora não faz nesta resposta:", beginner)

    def test_invalid_presentation_profile_is_explicit_error(self) -> None:
        with self.assertRaises(ValueError):
            normalize_profile("operacional")

    def test_orientation_profile_keeps_guidance_and_limits_visible(self) -> None:
        request = OrientationRequest(topic=QUESTION_INSTALL, target="firefox")

        rendered = render_orientation(request, profile=PresentationProfile.BEGINNER)

        self.assertIn("Para instalar 'firefox'", rendered)
        self.assertIn("Caminho seguro:", rendered)
        self.assertIn("aurora dev \"instalar firefox\"", rendered)
        self.assertIn("aurora instalar firefox", rendered)
        self.assertIn("não executei backend", rendered)
        self.assertIn("não alterei o sistema", rendered)


if __name__ == "__main__":
    unittest.main()

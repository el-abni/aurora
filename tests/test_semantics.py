from __future__ import annotations

import unittest

from aurora.install.domain_classifier import classify_text
from aurora.semantics.pipeline import prepare_text
from aurora.semantics.sensitive_tokens import protect_sensitive_tokens, restore_sensitive_tokens


class SemanticsTests(unittest.TestCase):
    def test_sensitive_tokens_are_protected_and_restored(self) -> None:
        protected, mapping = protect_sensitive_tokens(["instalar", "~/Downloads/pkg.tar.gz"])
        self.assertEqual(protected[0], "instalar")
        self.assertTrue(protected[1].startswith("__AURORA_"))
        self.assertIn(mapping[0].token_type, {"path", "file"})
        restored = restore_sensitive_tokens(protected, mapping)
        self.assertEqual(restored, ["instalar", "~/Downloads/pkg.tar.gz"])

    def test_split_actions_is_available_but_sequence_is_not_open(self) -> None:
        _phrase, actions = prepare_text("procurar firefox e depois remover vlc")
        self.assertEqual(len(actions), 2)
        request = classify_text("procurar firefox e depois remover vlc")
        self.assertEqual(request.status, "OUT_OF_SCOPE")
        self.assertEqual(request.action_count, 2)

    def test_classifier_understands_host_package_search(self) -> None:
        request = classify_text("Aurora, procure o pacote firefox")
        self.assertEqual(request.intent, "procurar")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.target, "firefox")
        self.assertEqual(request.status, "CONSISTENT")

    def test_classifier_blocks_missing_package_target(self) -> None:
        request = classify_text("instalar pacote")
        self.assertEqual(request.intent, "instalar")
        self.assertEqual(request.domain_kind, "host_package")
        self.assertEqual(request.status, "BLOCKED")
        self.assertIn("faltou o alvo", request.reason)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from aurora.presentation.messages import search_results_message


class PublicSearchRenderingTests(unittest.TestCase):
    def test_dnf_distrobox_metadata_output_is_summarized_by_result_rows(self) -> None:
        details = "\n".join(
            (
                "Campos correspondentes: name",
                "",
                "----------",
                " git.x86_64\tFast Version Control System",
                "Matched fields: name, summary",
                " git-core.x86_64\tGit core tools",
                *(
                    f" git-addon-{index:02d}.x86_64\tGit addon {index:02d}"
                    for index in range(1, 13)
                ),
            )
        )

        rendered = search_results_message("git", "distrobox + dnf", details)

        self.assertIn("Encontrei muitos resultados para 'git' no backend 'distrobox + dnf'", rendered)
        self.assertIn("Mostrando os primeiros 10", rendered)
        self.assertIn("1. git.x86_64 — Fast Version Control System", rendered)
        self.assertIn("2. git-core.x86_64 — Git core tools", rendered)
        self.assertIn("10. git-addon-08.x86_64", rendered)
        self.assertIn("Há mais resultados", rendered)
        self.assertNotIn("1. Campos", rendered)
        self.assertNotIn("Campos correspondentes:", rendered)
        self.assertNotIn("Matched fields", rendered)
        self.assertNotIn("----------", rendered)
        self.assertNotIn("git-addon-09", rendered)
        self.assertNotIn("melhor", rendered.lower())
        self.assertNotIn("recomendado", rendered.lower())


if __name__ == "__main__":
    unittest.main()

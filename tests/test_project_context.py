from pathlib import Path
import re
import tomllib
import unittest


class ProjectContextTests(unittest.TestCase):
    def test_project_state_uses_the_locked_upstream_pins(self) -> None:
        project = Path(__file__).resolve().parents[1]
        with (project / "upstream.lock").open("rb") as stream:
            upstream = tomllib.load(stream)["upstream"]
        project_state = (project / "docs/PROJECT_STATE.md").read_text(encoding="utf-8")

        self.assertIn(upstream["batocera.linux"], project_state)
        self.assertIn(upstream["batocera-emulationstation"], project_state)
        self.assertIn(upstream["architecture"], project_state)

    def test_handoff_documents_reference_existing_core_documents(self) -> None:
        project = Path(__file__).resolve().parents[1]
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        project_state = (project / "docs/PROJECT_STATE.md").read_text(encoding="utf-8")
        references = {
            "AGENTS.md": agents,
            "docs/PROJECT_STATE.md": agents,
            "docs/COMPATIBILITY_0_1.md": agents,
            "COMPATIBILITY_0_1.md": project_state,
        }

        for relative, document in references.items():
            self.assertIn(relative, document)
            target = project / relative
            if not target.exists():
                target = project / "docs" / relative
            self.assertTrue(target.is_file(), relative)

        read_first = re.search(r"## Read first\n(?P<body>.*?)(?:\n## |\Z)", agents, re.S)
        self.assertIsNotNone(read_first)
        self.assertIn("git status --short", read_first.group("body"))
        self.assertIn("git log --oneline -15", read_first.group("body"))


if __name__ == "__main__":
    unittest.main()

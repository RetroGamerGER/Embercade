from pathlib import Path
import unittest


class DevelopmentHarnessTests(unittest.TestCase):
    def test_frontend_sees_dynamic_input_directory_instead_of_one_startup_event_node(self) -> None:
        project = Path(__file__).resolve().parents[1]
        script = (project / "scripts/dev-run").read_text(encoding="utf-8")

        self.assertIn("--dev-bind /dev/input /dev/input", script)
        self.assertIn("EMBERCADE_HOST_PROVIDER_RUNNER", script)
        self.assertNotIn("--dev-bind /dev/fuse /dev/fuse", script)
        self.assertNotIn("controller-info --device-path-only", script)
        self.assertNotIn('controller_mounts', script)


if __name__ == "__main__":
    unittest.main()

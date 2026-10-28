from pathlib import Path
import tomllib
import unittest


class UpstreamLockTests(unittest.TestCase):
    def test_required_upstream_pins(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with (project_root / "upstream.lock").open("rb") as stream:
            upstream = tomllib.load(stream)["upstream"]

        self.assertEqual(
            upstream["batocera.linux"],
            "9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48",
        )
        self.assertEqual(
            upstream["batocera-emulationstation"],
            "1750dded8c0fdff70630026f756a69fcad0bb995",
        )
        self.assertEqual(upstream["architecture"], "batocera-launch-44")


if __name__ == "__main__":
    unittest.main()

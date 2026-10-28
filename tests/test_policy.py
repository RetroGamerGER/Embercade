from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.policy import CapabilityStatus, DesktopPolicy


class DesktopPolicyTests(unittest.TestCase):
    def test_project_policy_covers_all_four_states_and_hides_power_actions(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        policy = DesktopPolicy.load(
            project_root / "resources/policy/desktop-capabilities.conf"
        )
        self.assertEqual(set(policy.capabilities.values()), set(CapabilityStatus))
        self.assertEqual(policy.status("themes"), CapabilityStatus.DESKTOP_MANAGED)
        self.assertEqual(policy.status("reboot"), CapabilityStatus.HIDDEN)
        self.assertEqual(
            policy.frontend_environment(),
            {
                "EMBERCADE_DESKTOP_POLICY": "1",
                "EMBERCADE_HIDE_SYSTEM_SETTINGS": "1",
                "EMBERCADE_EXIT_ONLY": "1",
            },
        )

    def test_invalid_status_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "policy.conf"
            path.write_text("reboot=maybe\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported status"):
                DesktopPolicy.load(path)

    def test_desktop_exit_action_uses_embercade_product_branding(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        patch = (
            project_root / "patches/emulationstation/0001-embercade-desktop-policy.patch"
        ).read_text(encoding="utf-8")
        policy_branch = patch.split(
            '+\tif (embercadePolicyEnabled("EMBERCADE_EXIT_ONLY"))', 1
        )[1].split("+\telse", 1)[0]

        self.assertIn('_("QUIT EMBERCADE")', policy_branch)
        self.assertNotIn('_("QUIT EMULATIONSTATION")', policy_branch)
        self.assertIn("Utils::Platform::QuitMode::QUIT", policy_branch)


if __name__ == "__main__":
    unittest.main()

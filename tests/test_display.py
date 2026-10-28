import json
import subprocess
import unittest
from unittest.mock import patch

from embercade.display import (
    DisplayResolution,
    DisplayResolutionError,
    DisplaySession,
    current_resolution,
)


class DisplaySessionTests(unittest.TestCase):
    def test_wayland_is_preferred(self) -> None:
        session = DisplaySession.current({"WAYLAND_DISPLAY": "wayland-1", "DISPLAY": ":0"})
        self.assertEqual(session.protocol, "wayland")
        self.assertFalse(session.supports_mode_switch)

    def test_headless(self) -> None:
        self.assertEqual(DisplaySession.current({}).protocol, "headless")

    def test_explicit_desktop_resolution_is_used_without_query(self) -> None:
        resolution = current_resolution(
            {
                "EMBERCADE_DISPLAY_WIDTH": "2560",
                "EMBERCADE_DISPLAY_HEIGHT": "1440",
            }
        )
        self.assertEqual(resolution, DisplayResolution(2560, 1440))

    def test_hyprland_focused_monitor_pixel_size(self) -> None:
        class Completed:
            returncode = 0
            stdout = (
                '[{"width": 1920, "height": 1080, "focused": false},'
                '{"width": 2560, "height": 1440, "focused": true}]'
            )

        with patch("embercade.display.shutil.which", return_value="/fixture/hyprctl"):
            resolution = current_resolution(
                {"PATH": "/usr/bin", "HYPRLAND_INSTANCE_SIGNATURE": "test"},
                runner=lambda *args, **kwargs: Completed(),
            )
        self.assertEqual(resolution, DisplayResolution(2560, 1440))

    def test_kde_uses_physical_mode_and_active_output_without_mode_switch(self):
        outputs = [dict(name="DP-1", connected=True, enabled=True, priority=1,
                        currentModeId="a", modes=[dict(id="a", size=dict(width=1920, height=1080))]),
                   dict(name="HDMI-1", connected=True, enabled=True, priority=2, rotation=1,
                        size=dict(width=1280, height=720), currentModeId="b",
                        modes=[dict(id="b", size=dict(width=2560, height=1440))])]
        calls = []
        def run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, "HDMI-1\n" if "activeOutputName" in argv[-1]
                                               else json.dumps(dict(outputs=outputs)), "")
        with patch("embercade.display.shutil.which", side_effect=lambda name, **_: name):
            size = current_resolution(dict(WAYLAND_DISPLAY="w", XDG_CURRENT_DESKTOP="KDE"), runner=run)
        self.assertEqual(size, DisplayResolution(2560, 1440))
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], ["kscreen-doctor", "-j"])

    def test_gamescope_uses_its_logical_output_before_inherited_desktop(self):
        def run(argv, **kwargs):
            self.assertEqual(argv, ["xrandr", "--current"])
            return subprocess.CompletedProcess(argv, 0, "XWAYLAND0 connected primary 1280x800+0+0\n", "")
        with patch("embercade.display.shutil.which", side_effect=lambda name, **_: name):
            size = current_resolution(dict(DISPLAY=":2", WAYLAND_DISPLAY="w", XDG_CURRENT_DESKTOP="KDE",
                                           GAMESCOPE_WAYLAND_DISPLAY="gamescope"), runner=run)
        self.assertEqual(size, DisplayResolution(1280, 800))

    def test_invalid_kde_output_does_not_silently_generate_wrong_viewports(self):
        with patch("embercade.display.shutil.which", return_value="kscreen-doctor"):
            with self.assertRaises(DisplayResolutionError):
                current_resolution(dict(WAYLAND_DISPLAY="w", XDG_CURRENT_DESKTOP="KDE"),
                                   runner=lambda *a, **k: subprocess.CompletedProcess([], 0, '{"outputs":[]}', ""))

    def test_partial_or_invalid_explicit_resolution_is_rejected(self) -> None:
        with self.assertRaises(DisplayResolutionError):
            current_resolution({"EMBERCADE_DISPLAY_WIDTH": "2560"})
        with self.assertRaises(DisplayResolutionError):
            current_resolution(
                {
                    "EMBERCADE_DISPLAY_WIDTH": "0",
                    "EMBERCADE_DISPLAY_HEIGHT": "1440",
                }
            )


if __name__ == "__main__":
    unittest.main()

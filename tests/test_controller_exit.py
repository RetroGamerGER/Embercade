from pathlib import Path
from unittest.mock import Mock, call, patch
import unittest

from embercade.controller_exit import (
    _emit_alt_f4,
    _evdev_exit_button_codes,
    _exit_chord_pressed,
    _steam_virtual_gamepad_paths,
    load_host_evdev,
)
from embercade.exit_hotkey import EXIT_HOTKEYS


class ControllerExitTests(unittest.TestCase):
    def test_steam_session_adds_only_valves_forwarded_xbox_gamepad(self) -> None:
        physical = Mock(info=Mock(vendor=0x3537, product=0x109C))
        virtual = Mock(info=Mock(vendor=0x28DE, product=0x11FF))
        evdev = Mock()
        evdev.list_devices.return_value = ("/dev/input/event13", "/dev/input/event25")
        evdev.InputDevice.side_effect = (physical, virtual)

        self.assertEqual(
            _steam_virtual_gamepad_paths(
                evdev,
                {"SteamAppId": "4059814080"},
            ),
            (Path("/dev/input/event25"),),
        )
        physical.close.assert_called_once_with()
        virtual.close.assert_called_once_with()

    def test_non_steam_session_does_not_scan_virtual_gamepads(self) -> None:
        evdev = Mock()
        self.assertEqual(_steam_virtual_gamepad_paths(evdev, {}), ())
        evdev.list_devices.assert_not_called()

    def test_evdev_exit_buttons_follow_configured_select_or_guide_preset(self) -> None:
        ecodes = Mock(BTN_SELECT=314, BTN_MODE=316, BTN_START=315)
        self.assertEqual(
            _evdev_exit_button_codes(ecodes, EXIT_HOTKEYS["back-start"]),
            (314, 315),
        )
        self.assertEqual(
            _evdev_exit_button_codes(ecodes, EXIT_HOTKEYS["guide-start"]),
            (316, 315),
        )

    def test_controller_state_is_refreshed_before_select_start_read(self) -> None:
        sdl = Mock()
        sdl.SDL_GameControllerGetButton.side_effect = [1, 1]

        self.assertTrue(_exit_chord_pressed(sdl, "handle"))
        self.assertEqual(
            sdl.method_calls,
            [
                call.SDL_GameControllerUpdate(),
                call.SDL_GameControllerGetButton("handle", 4),
                call.SDL_GameControllerGetButton("handle", 6),
            ],
        )

    def test_guide_start_uses_sdl_guide_button(self) -> None:
        sdl = Mock()
        sdl.SDL_GameControllerGetButton.side_effect = [1, 1]
        self.assertTrue(_exit_chord_pressed(sdl, "handle", 5))
        self.assertEqual(sdl.method_calls[-2:], [
            call.SDL_GameControllerGetButton("handle", 5),
            call.SDL_GameControllerGetButton("handle", 6),
        ])

    def test_alt_f4_is_emitted_as_a_normal_keyboard_chord(self) -> None:
        keyboard = Mock()
        ecodes = Mock(EV_KEY=1, KEY_LEFTALT=56, KEY_F4=62)
        _emit_alt_f4(keyboard, ecodes)

        self.assertEqual(
            keyboard.method_calls,
            [
                call.write(1, 56, 1),
                call.write(1, 62, 1),
                call.syn(),
                call.write(1, 62, 0),
                call.write(1, 56, 0),
                call.syn(),
            ],
        )

    def test_host_evdev_fallback_is_scoped_to_one_import(self) -> None:
        fake_evdev = Mock(__file__="/usr/lib/python3.14/site-packages/evdev/__init__.py")
        with (
            patch("embercade.controller_exit.import_module", side_effect=[ImportError(), fake_evdev]),
            patch("embercade.controller_exit.Path.is_dir", return_value=True),
        ):
            before = list(__import__("sys").path)
            result = load_host_evdev()
            after = list(__import__("sys").path)
        self.assertIs(result, fake_evdev)
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import unittest
import xml.etree.ElementTree as ET

from embercade.controller import (
    ControllerDevice,
    ControllerUnavailable,
    enumerate_sdl_game_controllers,
    guid_without_crc,
    require_player_one_controller,
    resolve_player_controllers,
    write_es_input_override,
    write_es_input_overrides,
)


LIVE_GUID = "030081b85e0400008e02000010010000"
NORMALIZED_GUID = "030000005e0400008e02000010010000"


def controller(*, device_path: Path = Path("/dev/input/event23")) -> ControllerDevice:
    return ControllerDevice(
        index=0,
        guid=LIVE_GUID,
        name="Xbox 360 Controller",
        device_path=device_path,
        buttons=11,
        hats=1,
        axes=6,
        mapping="live SDL mapping",
        real_name="Microsoft X-Box 360 pad",
        usb_vendor="045e",
        usb_product="028e",
        kernel_driver="xpad",
    )


class ControllerTests(unittest.TestCase):
    def test_discovery_disables_steam_virtual_gamepad_and_restores_environment(self) -> None:
        allow = "SDL_GAMECONTROLLER_ALLOW_STEAM_VIRTUAL_GAMEPAD"
        ignored = "SDL_GAMECONTROLLER_IGNORE_DEVICES"
        ignored_except = "SDL_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT"
        wii_hidapi = "SDL_JOYSTICK_HIDAPI_WII"
        inherited = {
            allow: "1",
            ignored: "0x3537/0x109c",
            ignored_except: "0x28de/0x11ff",
            wii_hidapi: "1",
        }
        with patch.dict(os.environ, inherited, clear=False):
            observed: list[dict[str, str | None]] = []

            def discover() -> tuple[ControllerDevice, ...]:
                observed.append(
                    {
                        allow: os.environ.get(allow),
                        ignored: os.environ.get(ignored),
                        ignored_except: os.environ.get(ignored_except),
                        wii_hidapi: os.environ.get(wii_hidapi),
                    }
                )
                return (controller(),)

            with patch(
                "embercade.controller._enumerate_sdl_game_controllers",
                side_effect=discover,
            ):
                devices = enumerate_sdl_game_controllers()

            self.assertEqual(devices, (controller(),))
            self.assertEqual(
                observed,
                [{allow: "0", ignored: None, ignored_except: None, wii_hidapi: "0"}],
            )
            self.assertEqual(
                {name: os.environ.get(name) for name in inherited},
                inherited,
            )

    def test_player_one_arguments_are_separate_argv_entries(self) -> None:
        device = controller(device_path=Path("/dev/input/event path"))

        self.assertEqual(
            device.player_one_arguments(),
            (
                "-p1index",
                "0",
                "-p1guid",
                LIVE_GUID,
                "-p1name",
                "Microsoft X-Box 360 pad",
                "-p1devicepath",
                "/dev/input/event path",
                "-p1nbbuttons",
                "11",
                "-p1nbhats",
                "1",
                "-p1nbaxes",
                "6",
            ),
        )

    def test_player_one_arguments_can_use_live_sdl_name(self) -> None:
        arguments = controller().player_one_arguments(device_name="Xbox 360 Controller")

        self.assertEqual(arguments[arguments.index("-p1name") + 1], "Xbox 360 Controller")

    def test_one_or_more_gamepads_including_bluetooth_are_supported(self) -> None:
        device = controller()
        self.assertIs(require_player_one_controller((device,)), device)

        with self.assertRaisesRegex(ControllerUnavailable, "No connected"):
            require_player_one_controller(())
        with self.assertRaisesRegex(ControllerUnavailable, "Duplicate SDL"):
            require_player_one_controller((device, device))

        non_usb = ControllerDevice(
            index=0,
            guid=LIVE_GUID,
            name="Xbox 360 Controller",
            device_path=Path("/dev/input/event23"),
            buttons=11,
            hats=1,
            axes=6,
            mapping="live SDL mapping",
        )
        self.assertIs(require_player_one_controller((non_usb,)), non_usb)
        self.assertEqual(resolve_player_controllers(()), ())

    def test_es_order_preferences_duplicate_guids_and_reconnect(self) -> None:
        first = controller(device_path=Path("/dev/input/event23"))
        second = replace(first, index=1, device_path=Path("/dev/input/event31"))
        with TemporaryDirectory() as directory:
            settings = Path(directory) / "es_settings.cfg"
            settings.write_text('''<config><string name="INPUT P1PATH" value="/physical/second" />
<string name="INPUT P2PATH" value="/physical/first" /></config>''', encoding="utf-8")
            with patch("embercade.controller._es_sort_device_path", side_effect=lambda device:
                       "/physical/second" if device.device_path.name in {"event31", "event39"}
                       else "/physical/first"):
                self.assertEqual(resolve_player_controllers((first, second), es_settings=settings),
                                 (second, first))
                reconnected = replace(second, index=3, device_path=Path("/dev/input/event39"))
                self.assertEqual(resolve_player_controllers((first, reconnected), es_settings=settings),
                                 (reconnected, first))

    def test_two_players_have_distinct_batocera_arguments(self) -> None:
        first = controller()
        second = replace(first, index=2, device_path=Path("/dev/input/event32"))
        self.assertIn("-p2index", second.player_arguments(2))
        self.assertEqual(second.player_arguments(2)[1], "2")
        self.assertIn("/dev/input/event32", second.player_arguments(2))
        self.assertNotIn(str(first.device_path), second.player_arguments(2))
        with self.assertRaises(ValueError):
            first.player_arguments(9)

    def test_default_player_one_selection_uses_sdl_enumeration(self) -> None:
        device = controller()
        with patch(
            "embercade.controller.enumerate_sdl_game_controllers",
            return_value=(device,),
        ) as enumerate_mock:
            self.assertIs(require_player_one_controller(), device)
        enumerate_mock.assert_called_once_with()

    def test_reconnect_reenumerates_index_and_device_path_instead_of_reusing_snapshot(self) -> None:
        before = controller(device_path=Path("/dev/input/event23"))
        after = replace(before, index=3, device_path=Path("/dev/input/event31"))
        with patch(
            "embercade.controller.enumerate_sdl_game_controllers",
            side_effect=((before,), (after,)),
        ) as enumerate_mock:
            first = require_player_one_controller()
            second = require_player_one_controller()

        self.assertEqual(enumerate_mock.call_count, 2)
        self.assertEqual(first.index, 0)
        self.assertEqual(first.device_path, Path("/dev/input/event23"))
        self.assertEqual(second.index, 3)
        self.assertEqual(second.device_path, Path("/dev/input/event31"))
        self.assertIn("3", second.player_one_arguments())
        self.assertIn("/dev/input/event31", second.player_one_arguments())
        self.assertNotIn("/dev/input/event23", second.player_one_arguments())

    def test_guid_crc_normalization_matches_batocera_database_form(self) -> None:
        self.assertEqual(guid_without_crc(LIVE_GUID), NORMALIZED_GUID)
        with self.assertRaisesRegex(ControllerUnavailable, "Invalid SDL2 controller GUID"):
            guid_without_crc("short")

    def test_exact_live_es_override_is_derived_from_batocera_mapping(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "database.xml"
            destination = root / "isolated" / "es_input.cfg"
            database.write_text(
                f'''<?xml version="1.0"?>
<inputList>
  <inputConfig type="joystick" deviceName="Microsoft X-Box 360 pad" deviceGUID="{NORMALIZED_GUID}">
    <input name="a" type="button" id="0" value="1" />
    <input name="b" type="button" id="1" value="1" />
    <input name="up" type="hat" id="0" value="1" />
    <input name="down" type="hat" id="0" value="4" />
    <input name="left" type="hat" id="0" value="8" />
    <input name="right" type="hat" id="0" value="2" />
    <input name="start" type="button" id="7" value="1" />
    <input name="hotkey" type="button" id="8" value="1" />
  </inputConfig>
</inputList>
''',
                encoding="utf-8",
            )

            source = write_es_input_override(controller(), database, destination)
            generated = ET.parse(destination).getroot().find("./inputConfig")

            self.assertIsNotNone(generated)
            assert generated is not None
            self.assertEqual(source.guid, NORMALIZED_GUID)
            self.assertEqual(source.name, "Microsoft X-Box 360 pad")
            self.assertEqual(generated.get("deviceGUID"), LIVE_GUID)
            self.assertEqual(generated.get("deviceName"), "Xbox 360 Controller")
            inputs = {item.get("name"): item.get("id") for item in generated.findall("./input")}
            self.assertEqual(inputs["hotkey"], "8")
            self.assertEqual(inputs["start"], "7")
            self.assertTrue(destination.is_relative_to(root))

    def test_duplicate_guid_shares_one_es_mapping_but_not_one_player_slot(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "database.xml"
            database.write_text('''<inputList><inputConfig type="joystick"
deviceName="Xbox 360 Controller" deviceGUID="030081b85e0400008e02000010010000">
<input name="a" type="button" id="0" value="1" />
<input name="b" type="button" id="1" value="1" />
<input name="up" type="hat" id="0" value="1" />
<input name="down" type="hat" id="0" value="4" />
<input name="left" type="hat" id="0" value="8" />
<input name="right" type="hat" id="0" value="2" />
<input name="start" type="button" id="7" value="1" />
<input name="hotkey" type="button" id="8" value="1" />
</inputConfig></inputList>''', encoding="utf-8")
            first = controller()
            second = replace(first, index=1, device_path=Path("/dev/input/event33"))
            sources = write_es_input_overrides((first, second), database, root / "es_input.cfg")
            generated = ET.parse(root / "es_input.cfg").getroot()
            self.assertEqual(len(sources), 1)
            self.assertEqual(len(generated.findall("./inputConfig")), 1)
            self.assertEqual(len(resolve_player_controllers((first, second))), 2)

    def test_existing_es_mapping_survives_launch_and_new_pad_is_added(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "database.xml"
            database.write_text("<inputList/>", encoding="utf-8")
            destination = root / "es_input.cfg"
            destination.write_text(
                f'<inputList><inputConfig type="joystick" deviceName="Xbox 360 Controller" '
                f'deviceGUID="{LIVE_GUID}"><input name="a" type="button" id="7" '
                'value="1" /></inputConfig></inputList>', encoding="utf-8",
            )
            original = destination.read_bytes()
            source = write_es_input_overrides((controller(),), database, destination)
            self.assertEqual(source[0].name, "EmulationStation user mapping")
            self.assertEqual(destination.read_bytes(), original)
            bluetooth = ControllerDevice(
                1, "050018dc5e040000130b000017050000", "Xbox Series X Controller",
                Path("/dev/input/event19"), 16, 1, 6,
                "050018dc5e040000130b000017050000,Xbox Series X Controller,"
                "a:b0,b:b1,guide:b12,start:b11,dpup:h0.1,dpdown:h0.4,"
                "dpleft:h0.8,dpright:h0.2,platform:Linux,",
            )
            write_es_input_overrides((controller(), bluetooth), database, destination)
            saved = ET.parse(destination).getroot().findall("./inputConfig")
            self.assertEqual(len(saved), 2)
            self.assertEqual(saved[0].find("./input").get("id"), "7")

    def test_live_sdl_mapping_fills_gap_in_pinned_database(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "database.xml"
            database.write_text("<inputList/>", encoding="utf-8")
            bluetooth = ControllerDevice(
                0, "050018dc5e040000130b000017050000", "Xbox Series X Controller",
                Path("/dev/input/event19"), 16, 1, 6,
                "050018dc5e040000130b000017050000,Xbox Series X Controller,"
                "a:b0,b:b1,guide:b12,start:b11,dpup:h0.1,dpdown:h0.4,"
                "dpleft:h0.8,dpright:h0.2,platform:Linux,",
            )
            sources = write_es_input_overrides((bluetooth,), database, root / "es_input.cfg")
            self.assertEqual(sources[0].name, "live SDL mapping")
            generated = ET.parse(root / "es_input.cfg").getroot().find("./inputConfig")
            self.assertIsNotNone(generated)
            assert generated is not None
            inputs = {item.get("name"): item.get("id") for item in generated.findall("./input")}
            self.assertEqual(inputs["hotkey"], "12")
            self.assertEqual(inputs["start"], "11")
            self.assertEqual(inputs["a"], "1")
            self.assertEqual(inputs["b"], "0")

    def test_only_exact_legacy_sdl_fallback_is_migrated(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "database.xml"
            database.write_text("<inputList/>", encoding="utf-8")
            destination = root / "es_input.cfg"
            bluetooth = ControllerDevice(
                0, "050018dc5e040000130b000017050000", "Xbox Series X Controller",
                Path("/dev/input/event19"), 16, 1, 6,
                "050018dc5e040000130b000017050000,Xbox Wireless Controller,"
                "a:b0,b:b1,x:b3,y:b4,guide:b12,start:b11,"
                "dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,platform:Linux,",
            )
            write_es_input_overrides((bluetooth,), database, destination)
            tree = ET.parse(destination)
            entry = tree.getroot().find("./inputConfig")
            assert entry is not None
            for item in entry.findall("./input"):
                item.set("name", {"a": "b", "b": "a", "x": "y", "y": "x"}.get(
                    item.get("name", ""), item.get("name", "")))
            tree.write(destination, encoding="utf-8", xml_declaration=True)

            source = write_es_input_overrides((bluetooth,), database, destination)
            self.assertEqual(source[0].name, "corrected SDL mapping")
            tree = ET.parse(destination)
            entry = tree.getroot().find("./inputConfig")
            assert entry is not None
            faces = {item.get("name"): item.get("id") for item in entry.findall("./input")}
            self.assertEqual({name: faces[name] for name in ("a", "b", "x", "y")},
                             {"a": "1", "b": "0", "x": "4", "y": "3"})

            next(item for item in entry.findall("./input") if item.get("name") == "a").set("id", "9")
            tree.write(destination, encoding="utf-8", xml_declaration=True)
            customized = destination.read_bytes()
            source = write_es_input_overrides((bluetooth,), database, destination)
            self.assertEqual(source[0].name, "EmulationStation user mapping")
            self.assertEqual(destination.read_bytes(), customized)


if __name__ == "__main__":
    unittest.main()

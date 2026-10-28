"""Pinned-generator fixture checks; these do not establish hardware READY."""

import asyncio
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import sys
import unittest


class _Config(dict):
    core = "nestopia"
    system = "nes"
    use_guns = False
    use_wheels = False


class _Settings:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def save(self, key: str, value: str) -> None:
        self.values[key] = value


class _Wheel:
    def __init__(self) -> None:
        self.device_path = "/dev/input/event42"
        self.real_name = "Fixture wheel"
        self.index = 1
        self.player_number = 1
        self.physical_device_path = None
        self.inputs = {
            name: SimpleNamespace(id=str(index), type="axis", value="1", name=name)
            for index, name in enumerate(("joystick1left", "l2", "r2"))
        }

    def replace(self, *, player_number: int) -> "_Wheel":
        self.player_number = player_number
        return self


class PinnedSpecialControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        site_packages = tuple((root / ".work/runtime/venv/lib").glob("python*/site-packages"))
        if not site_packages:
            raise unittest.SkipTest("Prepare the pinned runtime before generator checks")
        sys.path.insert(0, str(site_packages[0]))
        from batocera_launch.devices import wheels
        from batocera_launch_pcsx2.emulator import _input_to_wheel
        from configgen.generators.libretro import libretroControllers, libretroOptions

        cls.wheels = wheels
        cls.input_to_wheel = staticmethod(_input_to_wheel)
        cls.libretro_controllers = libretroControllers
        cls.libretro_options = libretroOptions

    def test_lightgun_core_and_slots_keep_normal_pointer_separate(self) -> None:
        settings = _Settings()
        config = _Config()
        system = SimpleNamespace(name="nes", config=config)
        self.libretro_options._nestopia_options(settings, system, None, [], {})
        self.assertEqual(settings.values["nestopia_zapper_device"], '"mouse"')
        config.use_guns = True
        self.libretro_options._nestopia_options(
            settings, system, None, [SimpleNamespace(needs_cross=False)], {}
        )
        self.assertEqual(settings.values["nestopia_zapper_device"], '"lightgun"')

        controller = SimpleNamespace(
            player_number=2, type="joystick",
            inputs={"a": SimpleNamespace(type="button", id="0", value="1")},
        )
        ordinary = self.libretro_controllers.generateControllerConfig(controller, system, False, "3")
        gun = self.libretro_controllers.generateControllerConfig(controller, system, True, "3")
        self.assertEqual(ordinary["input_player2_mouse_index"], "3")
        self.assertNotIn("input_player2_mouse_index", gun)
        self.assertIn("input_player2_gun_aux_a_btn", gun)
        self.assertNotIn("input_player1_gun_aux_a_btn", gun)

    def test_relative_pointer_path_does_not_become_a_gun_or_gamepad(self) -> None:
        config = _Config()
        system = SimpleNamespace(name="nes", config=config)
        pointer = SimpleNamespace(player_number=1, type="mouse", inputs={})
        with patch.dict(os.environ, {"EMBERCADE_DESKTOP": "1"}):
            result = self.libretro_controllers.generateControllerConfig(pointer, system, False, "1")
        self.assertEqual(result, {"input_player1_mouse_index": "1"})

    def test_pcsx2_wheel_steering_and_pedals_use_upstream_axis_mapping(self) -> None:
        wheel = _Wheel()
        self.assertEqual(self.input_to_wheel(wheel.inputs["joystick1left"]), "-Axis6")
        self.assertEqual(self.input_to_wheel(wheel.inputs["joystick1left"], reversed_axis=True), "+Axis6")
        self.assertEqual(self.input_to_wheel(wheel.inputs["l2"], reversed_axis=None), "FullAxis7~")
        self.assertEqual(self.input_to_wheel(wheel.inputs["r2"], reversed_axis=None), "FullAxis8~")

    def test_desktop_wheel_preserves_raw_axes_without_host_calibration(self) -> None:
        wheel = _Wheel()
        config = _Config()
        config.use_wheels = True
        device = SimpleNamespace(
            is_wheel=True, wheel_rotation=900, sysfs_path="/sys/fixture", event_id=42,
            is_joystick=True,
        )

        async def check() -> None:
            with (
                patch.dict(os.environ, {"EMBERCADE_DESKTOP": "1"}),
                patch.object(self.wheels, "get_device_info", return_value={wheel.device_path: device}),
                patch.object(self.wheels, "_find_range_path", side_effect=AssertionError("host sysfs write")),
                patch.object(self.wheels, "_reconfigure_angle_rotation", new_callable=AsyncMock,
                             side_effect=AssertionError("host calibration")),
            ):
                async with self.wheels.configure_wheels(config, [wheel], {"wheel_rotation": "270"}) as result:
                    self.assertEqual(result[0], [wheel])
                    self.assertEqual(result[1], {wheel.device_path: device})
                    self.assertEqual(wheel.player_number, 1)
                    self.assertEqual(set(wheel.inputs), {"joystick1left", "l2", "r2"})

        asyncio.run(check())

    def test_wheel_enabled_without_hardware_keeps_ordinary_player(self) -> None:
        pad = _Wheel()
        config = _Config()
        config.use_wheels = True

        async def check() -> None:
            with patch.object(self.wheels, "get_device_info", return_value={}):
                async with self.wheels.configure_wheels(config, [pad], {}) as result:
                    self.assertEqual(result, ([pad], {}))
                    self.assertEqual(pad.player_number, 1)

        asyncio.run(check())

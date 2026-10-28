from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.controller import ControllerDevice
from embercade.dolphin_dry_run import build_report, execute_dry_run
from embercade.launcher import LaunchPlan
from embercade.paths import EmbercadePaths


class DolphinDryRunTests(unittest.TestCase):
    def test_wii_command_controller_and_all_writable_paths_are_isolated(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom_root = root / "read only ROMs"
            rom = rom_root / "wii/Test Game.rvz"
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b"read-only rvz")
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root / "home"),
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                },
                config={"paths": {"roms": str(rom_root)}},
            )
            config_root = paths.emulator_configs / "dolphin-emu"
            config_root.mkdir(parents=True)
            (config_root / "Dolphin.ini").write_text(
                "[General]\n"
                f"ISOPath0 = {rom_root / 'wii'}\n"
                f"ISOPath1 = {rom_root / 'gamecube'}\n"
                "[Core]\nGFXBackend = OGL\nWiimoteContinuousScanning = True\n"
                "[DSP]\nBackend = Cubeb\n",
                encoding="utf-8",
            )
            for name in ("GFX.ini", "Qt.ini", "Hotkeys.ini"):
                (config_root / name).write_text("[Settings]\nValue = 1\n", encoding="utf-8")
            (config_root / "WiimoteNew.ini").write_text(
                "[Wiimote1]\n"
                "Device = evdev/0/Microsoft X-Box 360 pad\n"
                "Main Stick/Dead Zone = 5.0\n"
                "Main Stick/Dead Zone = 5.0\n",
                encoding="utf-8-sig",
            )
            dolphin = root / "host bin/dolphin-emu"
            dolphin.parent.mkdir()
            dolphin.write_text("binary\n", encoding="utf-8")
            dolphin.chmod(0o755)
            launcher = root / "fake-launcher"
            final = [str(dolphin), "-b", "-e", str(rom)]
            launcher.write_text(
                "#!/usr/bin/env python3\n"
                "import shlex\n"
                f"print('EMBERCADE_FINAL_COMMAND=' + shlex.join({final!r}))\n",
                encoding="utf-8",
            )
            launcher.chmod(0o755)
            controller = ControllerDevice(
                0,
                "guid",
                "Xbox 360 Controller",
                Path("/dev/input/event23"),
                11,
                1,
                6,
                "mapping",
                real_name="Microsoft X-Box 360 pad",
            )
            command = (str(launcher), "-system", "wii", "-rom", str(rom)) + (
                controller.player_one_arguments()
            )
            plan = LaunchPlan(
                command,
                {
                    "XDG_CONFIG_HOME": str(paths.config),
                    "XDG_DATA_HOME": str(paths.data),
                    "XDG_CACHE_HOME": str(paths.cache),
                },
                dolphin,
                None,
                rom,
                controller,
                system="wii",
                dry_run=True,
                emulator="dolphin",
                core_name=None,
            )

            row = execute_dry_run(plan, paths)

            self.assertEqual(row["final_command"], final)
            self.assertEqual(row["renderer"], "OGL")
            self.assertEqual(row["audio_backend"], "Cubeb")
            self.assertEqual(row["nand_root"], str(paths.saves / "dolphin-emu/Wii"))
            self.assertEqual(row["special_controller_validation"], "PENDING")
            report = build_report(row, host_profiles_unchanged=True)
            self.assertTrue(report["host_profiles_unchanged"])


if __name__ == "__main__":
    unittest.main()

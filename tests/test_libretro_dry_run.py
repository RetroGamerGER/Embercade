from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.controller import ControllerDevice
from embercade.launcher import LaunchPlan
from embercade.libretro_dry_run import (
    LibretroDryRunError,
    build_report,
    execute_dry_run,
    expected_system_directory,
    required_system_resources,
    snapshot_metadata,
)
from embercade.paths import EmbercadePaths


class LibretroDryRunTests(unittest.TestCase):
    @staticmethod
    def _controller() -> ControllerDevice:
        return ControllerDevice(
            0,
            "guid",
            "Xbox Controller",
            Path("/dev/input/event23"),
            11,
            1,
            6,
            "mapping",
            real_name="Microsoft X-Box 360 pad",
        )

    def test_verifies_core_rom_bios_controller_shader_overlay_and_isolation(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root),
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                },
                config={"paths": {"bios": str(root / "read only BIOS")}},
            )
            config = paths.emulator_configs / "retroarch/retroarchcustom.cfg"
            config.parent.mkdir(parents=True)
            overlay = paths.overlays / "overlay.cfg"
            overlay.parent.mkdir(parents=True)
            overlay.write_text("overlay0_full_screen = true\n", encoding="utf-8")
            config.write_text(
                f'system_directory = "{paths.bios_root}"\n'
                f'savefile_directory = "{paths.saves / "megadrive"}"\n'
                f'savestate_directory = "{paths.saves / "megadrive"}"\n'
                f'cache_directory = "{paths.emulator_configs / "retroarch/cache"}"\n'
                'input_overlay_enable = "true"\n'
                f'input_overlay = "{overlay}"\n',
                encoding="utf-8",
            )
            core = root / "host cores/genesis_plus_gx_libretro.so"
            core.parent.mkdir()
            core.write_bytes(b"\x7fELFcore")
            retroarch = root / "bin/retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("binary", encoding="utf-8")
            retroarch.chmod(0o755)
            rom = root / "ROM files/Game Name (Europe).md"
            rom.parent.mkdir()
            rom.write_bytes(b"rom")
            shader = root / "resources/shader preset.slangp"
            shader.parent.mkdir()
            shader.write_text("shader", encoding="utf-8")
            launcher = root / "fake-launcher"
            final = [
                str(retroarch),
                "-L",
                str(core),
                "--config",
                str(config),
                "--set-shader",
                str(shader),
                "--verbose",
                str(rom),
            ]
            launcher.write_text(
                "#!/usr/bin/env python3\n"
                "import shlex\n"
                f"print('EMBERCADE_FINAL_COMMAND=' + shlex.join({final!r}))\n",
                encoding="utf-8",
            )
            launcher.chmod(0o755)
            controller = self._controller()
            command = (str(launcher),) + controller.player_one_arguments()
            plan = LaunchPlan(
                command,
                {},
                retroarch,
                core,
                rom,
                controller,
                system="megadrive",
                dry_run=True,
                emulator="libretro",
                core_name="genesisplusgx",
            )

            row = execute_dry_run(plan, paths)

            self.assertEqual(row["core"], "genesisplusgx")
            self.assertEqual(row["rom"], str(rom))
            self.assertTrue(row["controller_arguments_complete"])
            self.assertTrue(row["overlay_enabled"])
            self.assertEqual(row["shader"], str(shader))
            self.assertEqual(row["memory_card_directory"], str(paths.saves / "megadrive"))
            self.assertEqual(row["savestate_directory"], str(paths.saves / "megadrive"))
            report = build_report([row], host_profile_unchanged=True)
            self.assertEqual(report["summary"], {"systems": 1, "successful": 1})

    def test_rejects_incomplete_controller_arguments(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.sfc"
            rom.write_bytes(b"rom")
            plan = LaunchPlan(
                ("launcher",),
                {},
                root / "retroarch",
                root / "core.so",
                rom,
                self._controller(),
                system="snes",
                dry_run=True,
                emulator="libretro",
                core_name="snes9x",
            )
            with self.assertRaisesRegex(LibretroDryRunError, "controller"):
                execute_dry_run(plan, EmbercadePaths.from_environment({"HOME": str(root)}))

    def test_metadata_snapshot_detects_changes_without_reading_contents(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "retroarch.cfg"
            file.write_text("first", encoding="utf-8")
            before = snapshot_metadata(root)
            file.write_text("changed and longer", encoding="utf-8")
            self.assertNotEqual(before, snapshot_metadata(root))

    def test_amiga_systems_use_read_only_bios_subdirectory(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment(
                {"HOME": str(root)},
                config={"paths": {"bios": str(root / "Complete BIOS")}},
            )
            self.assertEqual(
                expected_system_directory("amigacd32", paths),
                paths.bios_root / "amiga",
            )
            self.assertEqual(
                expected_system_directory("amiga1200", paths),
                paths.bios_root / "amiga",
            )
            self.assertEqual(expected_system_directory("saturn", paths), paths.bios_root)

    def test_psp_requires_complete_read_only_ppsspp_assets(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bios = root / "Complete BIOS"
            paths = EmbercadePaths.from_environment(
                {"HOME": str(root)}, config={"paths": {"bios": str(bios)}}
            )
            with self.assertRaisesRegex(LibretroDryRunError, "ppge_atlas.zim"):
                required_system_resources("psp", paths)

            ppsspp = paths.isolated_bios / "psp/PPSSPP"
            (ppsspp / "lang").mkdir(parents=True)
            (ppsspp / "flash0").mkdir()
            (ppsspp / "ppge_atlas.zim").write_bytes(b"read-only core data")

            self.assertEqual(
                required_system_resources("psp", paths),
                (
                    ppsspp / "ppge_atlas.zim",
                    ppsspp / "lang",
                    ppsspp / "flash0",
                ),
            )
            self.assertEqual(required_system_resources("3ds", paths), ())


if __name__ == "__main__":
    unittest.main()

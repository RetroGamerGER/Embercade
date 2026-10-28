from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from contextlib import contextmanager
import os
import signal
import socket
import subprocess
import unittest

from embercade.controller import ControllerDevice
from embercade.batocera_config import BatoceraSystemChoice
from embercade.launcher import (
    LaunchError,
    create_launch_plan,
    prepare_launch_layout,
    run_launch,
)
from embercade.paths import EmbercadePaths
from embercade.runtime import ProjectRuntime
from embercade.rpcs3 import prepare_rpcs3_firmware
from embercade.xemu import isolated_xemu_files


class LauncherTests(unittest.TestCase):
    @staticmethod
    def _choice(system: str, core: str) -> BatoceraSystemChoice:
        return BatoceraSystemChoice(system, "libretro", core, False, False)

    @staticmethod
    def _resources(project: Path) -> None:
        share = project / ".work/ui/share/batocera"
        (share / "shaders/configs").mkdir(parents=True)
        (share / "shaders/configs/rendering-defaults.yml").write_text(
            "default: {}\n", encoding="utf-8"
        )
        (share / "datainit/decorations").mkdir(parents=True)

    @staticmethod
    def _controller(device_path: Path) -> ControllerDevice:
        return ControllerDevice(
            index=0,
            guid="030081b85e0400008e02000010010000",
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

    def test_nes_plan_has_no_controller_arguments(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)

            retroarch = root / "bin" / "retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("#!/bin/sh\n", encoding="utf-8")
            retroarch.chmod(0o755)

            cores = root / "cores"
            cores.mkdir()
            (cores / "nestopia_libretro.so").write_bytes(b"core")
            rom = root / "game with spaces.nes"
            rom.write_bytes(b"rom")

            env = {
                "HOME": str(root),
                "PATH": str(retroarch.parent),
                "EMBERCADE_DISPLAY_WIDTH": "2560",
                "EMBERCADE_DISPLAY_HEIGHT": "1440",
            }
            paths = EmbercadePaths.from_environment(env)
            plan = create_launch_plan(
                system="nes",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=env,
                dry_run=True,
                batocera_choice=self._choice("nes", "nestopia"),
            )

            self.assertEqual(
                plan.command,
                (
                    str(runtime.launcher),
                    "-system",
                    "nes",
                    "-rom",
                    str(rom),
                    "-emulator",
                    "libretro",
                    "-core",
                    "nestopia",
                ),
            )
            self.assertFalse(any(argument.startswith("-p1") for argument in plan.command))
            self.assertEqual(plan.core, cores / "nestopia_libretro.so")
            self.assertEqual(
                plan.environment["EMBERCADE_LIBRETRO_CORE"],
                str(cores / "nestopia_libretro.so"),
            )
            self.assertEqual(plan.environment["EMBERCADE_LIBRETRO_CORE_NAME"], "nestopia")
            self.assertEqual(plan.environment["EMBERCADE_DRY_RUN"], "1")
            self.assertEqual(plan.environment["EMBERCADE_CONFIGS"], str(paths.emulator_configs))
            self.assertEqual(
                plan.environment["EMBERCADE_BATOCERA_SHADERS"],
                str(project / ".work/ui/share/batocera/shaders"),
            )

    def test_two_player_nes_plan_passes_distinct_batocera_slots(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            retroarch = root / "bin/retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("#!/bin/sh\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "cores"
            cores.mkdir()
            (cores / "nestopia_libretro.so").write_bytes(b"core")
            rom = root / "game.nes"
            rom.write_bytes(b"rom")
            env = {"HOME": str(root), "PATH": str(retroarch.parent),
                   "EMBERCADE_DISPLAY_WIDTH": "1920", "EMBERCADE_DISPLAY_HEIGHT": "1080"}
            first = self._controller(Path("/dev/input/event21"))
            second = ControllerDevice(1, first.guid, first.name, Path("/dev/input/event25"),
                                      first.buttons, first.hats, first.axes, first.mapping,
                                      real_name=first.real_name)
            plan = create_launch_plan(
                system="nes", rom=rom, paths=EmbercadePaths.from_environment(env),
                runtime=runtime, config={"libretro": {"cores": str(cores)}},
                environment=env, dry_run=True, batocera_choice=self._choice("nes", "nestopia"),
                controllers=(first, second),
            )
            self.assertEqual(plan.controller, first)
            self.assertEqual(plan.controllers, (first, second))
            self.assertEqual(plan.command[plan.command.index("-p1devicepath") + 1],
                             "/dev/input/event21")
            self.assertEqual(plan.command[plan.command.index("-p2devicepath") + 1],
                             "/dev/input/event25")
            self.assertEqual(plan.command[plan.command.index("-p2index") + 1], "1")

    def test_preparation_never_creates_configured_read_only_collection_roots(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            (project / "resources/defaults").mkdir(parents=True)
            (project / "resources/defaults/batocera.conf").write_text("", encoding="utf-8")
            (project / "resources/defaults/es_settings.cfg").write_text("", encoding="utf-8")
            external_roms = root / "external ROM root"
            external_bios = root / "external BIOS root"
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root / "home"),
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                },
                config={
                    "paths": {"roms": str(external_roms), "bios": str(external_bios)}
                },
            )

            prepare_launch_layout(paths, project)

            self.assertFalse(external_roms.exists())
            self.assertFalse(external_bios.exists())
            self.assertTrue(paths.isolated_bios.is_dir())

    def test_gamecube_plan_resolves_host_dolphin_and_preserves_iso_argument(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)

            dolphin = root / "bin" / "dolphin-emu"
            dolphin.parent.mkdir()
            dolphin.write_text("#!/bin/sh\n", encoding="utf-8")
            dolphin.chmod(0o755)
            rom = root / "Test Game.iso"
            rom.write_bytes(b"iso")
            env = {"HOME": str(root), "PATH": str(dolphin.parent),
                   "EMBERCADE_WII_REAL_CONNECTED": "1", "SDL_JOYSTICK_HIDAPI_WII": "1"}
            paths = EmbercadePaths.from_environment(env)

            plan = create_launch_plan(
                system="gamecube",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=env,
                dry_run=True,
                controller=self._controller(Path("/dev/input/event23")),
            )

            self.assertEqual(plan.executable, dolphin)
            self.assertIsNone(plan.core)
            self.assertEqual(plan.command[4], str(rom))
            self.assertEqual(plan.environment["EMBERCADE_DOLPHIN_BIN"], str(dolphin))
            self.assertEqual(plan.environment["EMBERCADE_DRY_RUN"], "1")
            self.assertNotIn("EMBERCADE_WII_REAL_CONNECTED", plan.environment)
            self.assertEqual(plan.environment['SDL_JOYSTICK_HIDAPI_WII'], '0')
            self.assertIn("Microsoft X-Box 360 pad", plan.command)
            self.assertNotIn(str(Path.home() / ".config" / "dolphin-emu"), plan.environment.values())
            self.assertEqual(
                plan.environment["EMBERCADE_SYSTEM_DECORATIONS"],
                str(project / ".work/ui/share/batocera/datainit/decorations"),
            )
            self.assertFalse(
                any(
                    value.startswith("/userdata")
                    for value in plan.environment.values()
                )
            )

    def test_controller_and_rom_are_passed_as_separate_argv_entries(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            retroarch = root / "bin" / "retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("#!/bin/sh\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "cores"
            cores.mkdir()
            (cores / "nestopia_libretro.so").write_bytes(b"core")
            rom = root / "Test Game.nes"
            rom.write_bytes(b"rom")
            device_path = Path("/dev/input/event path")
            env = {
                "HOME": str(root),
                "PATH": str(retroarch.parent),
                "EMBERCADE_DISPLAY_WIDTH": "2560",
                "EMBERCADE_DISPLAY_HEIGHT": "1440",
            }
            paths = EmbercadePaths.from_environment(env)

            plan = create_launch_plan(
                system="nes",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=env,
                dry_run=True,
                controller=self._controller(device_path),
                batocera_choice=self._choice("nes", "nestopia"),
            )

            self.assertEqual(plan.command[4], str(rom))
            self.assertIn("Microsoft X-Box 360 pad", plan.command)
            self.assertIn(str(device_path), plan.command)
            self.assertEqual(plan.command[-2:], ("-p1nbaxes", "6"))
            self.assertNotIn(str(Path.home() / ".config" / "retroarch"), plan.environment.values())

    def test_generic_libretro_systems_use_batocera_choice_aliases_and_central_bios(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            retroarch = root / "bin/retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("#!/bin/sh\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "host cores"
            cores.mkdir()
            expected = {
                # Atari 5200 is one of the BIOS-requiring systems in the
                # pinned Batocera inventory, so this also covers BIOS_ROOT.
                "3ds": ("azahar", "azahar_libretro.so"),
                "atari5200": ("atari800", "atari800_libretro.so"),
                "c64": ("vice_x64", "vice_x64_libretro.so"),
                "snes": ("snes9x", "snes9x_libretro.so"),
                "megadrive": ("genesisplusgx", "genesis_plus_gx_libretro.so"),
                "pcengine": ("pce", "mednafen_pce_libretro.so"),
                "gba": ("mgba", "mgba_libretro.so"),
                "jaguar": ("virtualjaguar", "virtualjaguar_libretro.so"),
                "n64": ("mupen64plus-next", "mupen64plus_next_libretro.so"),
                "psx": ("pcsx_rearmed", "pcsx_rearmed_libretro.so"),
                "amigacd32": ("puae", "puae_libretro.so"),
                "amiga1200": ("puae", "puae_libretro.so"),
                "dos": ("dosbox_pure", "dosbox_pure_libretro.so"),
                "mame": ("mame078plus", "mame2003_plus_libretro.so"),
                "nds": ("melondsds", "melondsds_libretro.so"),
                "psp": ("ppsspp", "ppsspp_libretro.so"),
                "dreamcast": ("flycast", "flycast_libretro.so"),
                "megacd": ("genesisplusgx", "genesis_plus_gx_libretro.so"),
                "neogeocd": ("neocd", "neocd_libretro.so"),
                "pcenginecd": ("pce", "mednafen_pce_libretro.so"),
                "saturn": ("beetle-saturn", "mednafen_saturn_libretro.so"),
            }
            for _, filename in expected.values():
                (cores / filename).write_bytes(b"\x7fELFcore")
            bios = root / "read only BIOS"
            bios.mkdir()
            ppsspp_assets = root / "official PPSSPP assets"
            (ppsspp_assets / "lang").mkdir(parents=True)
            (ppsspp_assets / "flash0").mkdir()
            (ppsspp_assets / "ppge_atlas.zim").write_bytes(b"read-only assets")
            bios.chmod(0o555)
            env = {
                "HOME": str(root),
                "PATH": str(retroarch.parent),
                "EMBERCADE_DISPLAY_WIDTH": "2560",
                "EMBERCADE_DISPLAY_HEIGHT": "1440",
            }
            paths = EmbercadePaths.from_environment(
                env,
                config={"paths": {"bios": str(bios)}},
            )
            controller = self._controller(Path("/dev/input/event23"))
            optical_extensions = {
                "amiga1200": ".lha",
                "amigacd32": ".chd",
                "dreamcast": ".cdi",
                "megacd": ".chd",
                "neogeocd": ".cue",
                "pcenginecd": ".cue",
                "psx": ".chd",
                "saturn": ".chd",
                "dos": ".zip",
                "mame": ".zip",
                "jaguar": ".j64",
                "n64": ".n64",
                "psp": ".iso",
                "3ds": ".3ds",
            }

            for system, (core_name, filename) in expected.items():
                with self.subTest(system=system):
                    extension = optical_extensions.get(system, ".rom")
                    rom = root / f"ROM files/{system}/Game Name ({system}){extension}"
                    rom.parent.mkdir(parents=True)
                    rom.write_bytes(b"rom")
                    before = (rom.read_bytes(), rom.stat().st_mtime_ns)
                    plan = create_launch_plan(
                        system=system,
                        rom=rom,
                        paths=paths,
                        runtime=runtime,
                        config={
                            "libretro": {
                                "cores": str(cores),
                                "ppsspp_assets": str(ppsspp_assets),
                            }
                        },
                        environment=env,
                        dry_run=True,
                        controller=controller,
                        batocera_choice=self._choice(system, core_name),
                    )

                    self.assertEqual(plan.emulator, "libretro")
                    self.assertEqual(plan.core_name, core_name)
                    self.assertEqual(plan.core, cores / filename)
                    self.assertEqual(plan.command[4], str(rom))
                    self.assertEqual(plan.command[5:9], ("-emulator", "libretro", "-core", core_name))
                    self.assertIn("-p1devicepath", plan.command)
                    if system == "psp":
                        psp_system = paths.isolated_bios / "psp"
                        self.assertEqual(plan.environment["EMBERCADE_BIOS"], str(psp_system))
                        self.assertTrue((psp_system / "PPSSPP").is_symlink())
                        self.assertEqual(
                            (psp_system / "PPSSPP").resolve(), ppsspp_assets.resolve()
                        )
                    else:
                        self.assertEqual(plan.environment["EMBERCADE_BIOS"], str(bios))
                    self.assertEqual(plan.environment["EMBERCADE_LIBRETRO_CORE"], str(cores / filename))
                    self.assertEqual(plan.environment["EMBERCADE_LIBRETRO_CORE_NAME"], core_name)
                    self.assertEqual(plan.environment["EMBERCADE_RETROARCH_BIN"], str(retroarch))
                    self.assertEqual(plan.environment["EMBERCADE_DISPLAY_WIDTH"], "2560")
                    self.assertEqual(plan.environment["EMBERCADE_DISPLAY_HEIGHT"], "1440")
                    self.assertEqual(before, (rom.read_bytes(), rom.stat().st_mtime_ns))

            bios.chmod(0o755)

    def test_wii_plan_reuses_dolphin_with_live_controller_and_isolated_paths(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            dolphin = root / "bin/dolphin-emu"
            dolphin.parent.mkdir()
            dolphin.write_text("#!/bin/sh\n", encoding="utf-8")
            dolphin.chmod(0o755)
            rom = root / "ROM root/wii/Test Game.rvz"
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b"read-only rvz")
            env = {"HOME": str(root), "PATH": str(dolphin.parent)}
            paths = EmbercadePaths.from_environment(
                env,
                config={"paths": {"roms": str(root / "ROM root")}},
            )

            plan = create_launch_plan(
                system="wii",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=env,
                dry_run=True,
                controller=self._controller(Path("/dev/input/event23")),
            )

            self.assertEqual(plan.emulator, "dolphin")
            self.assertEqual(plan.executable, dolphin)
            self.assertEqual(plan.environment["EMBERCADE_DOLPHIN_BIN"], str(dolphin))
            self.assertEqual(plan.environment["EMBERCADE_ROMS"], str(root / "ROM root"))
            self.assertEqual(plan.command[4], str(rom))
            self.assertIn("Microsoft X-Box 360 pad", plan.command)

            with patch('embercade.wii.real_wiimote_connected', side_effect=[True, False]) as probe:
                for expected in ('1', '0'):
                    live = create_launch_plan(
                        system="wii", rom=rom, paths=paths, runtime=runtime,
                        config={}, environment=env, dry_run=False,
                        controller=self._controller(Path("/dev/input/event23")),
                    )
                    self.assertEqual(live.environment['EMBERCADE_WII_REAL_CONNECTED'], expected)
                self.assertEqual(probe.call_count, 2)
            with patch('embercade.wii.real_wiimote_connected') as probe:
                structural = create_launch_plan(
                    system="wii", rom=rom, paths=paths, runtime=runtime,
                    config={}, environment=env, dry_run=True,
                    controller=self._controller(Path("/dev/input/event23")),
                )
                self.assertEqual(structural.environment['EMBERCADE_WII_REAL_CONNECTED'], '0')
                probe.assert_not_called()

    def test_wiiu_plan_uses_cemu_libretro_core_not_cemu_appimage(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            retroarch = root / "bin/retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("#!/bin/sh\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "host cores"
            cores.mkdir()
            cemu = cores / "cemu_libretro.so"
            cemu.write_bytes(b"\x7fELFcore")
            rom = root / "Test Game/code/game.rpx"
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b"read-only rpx")
            env = {"HOME": str(root), "PATH": str(retroarch.parent)}
            paths = EmbercadePaths.from_environment(env)

            plan = create_launch_plan(
                system="wiiu",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=env,
                dry_run=True,
                controller=self._controller(Path("/dev/input/event23")),
                batocera_choice=self._choice("wiiu", "cemu"),
            )

            self.assertEqual(plan.executable, retroarch)
            self.assertEqual(plan.core, cemu)
            self.assertEqual(plan.emulator, "libretro")
            self.assertEqual(plan.core_name, "cemu")
            self.assertEqual(plan.command[4], str(rom))
            self.assertEqual(plan.command[5:9], ("-emulator", "libretro", "-core", "cemu"))
            self.assertEqual(plan.environment["EMBERCADE_LIBRETRO_CORE"], str(cemu))
            self.assertNotIn("EMBERCADE_CEMU_BIN", plan.environment)

    def test_xbox360_plan_uses_external_appimage_and_isolated_working_directory(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            appimage = root / "providers/Xenia Edge.AppImage"
            appimage.parent.mkdir()
            appimage.write_text("#!/bin/sh\n", encoding="utf-8")
            appimage.chmod(0o755)
            rom = root / "Test Game.iso"
            rom.write_bytes(b"read-only iso")
            env = {"HOME": str(root), "PATH": ""}
            paths = EmbercadePaths.from_environment(env)

            plan = create_launch_plan(
                system="xbox360",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={
                    "emulators": {
                        "xenia-edge": {
                            "provider": "appimage",
                            "executable": str(appimage),
                        }
                    }
                },
                environment=env,
                dry_run=True,
                controller=self._controller(Path("/dev/input/event23")),
            )

            self.assertEqual(plan.executable, appimage)
            self.assertEqual(plan.environment["EMBERCADE_XENIA_EDGE_BIN"], str(appimage))
            self.assertEqual(
                plan.environment["EMBERCADE_XENIA_EDGE_LOG"],
                str(paths.logs / "xenia-edge.log"),
            )
            self.assertEqual(plan.working_directory, paths.emulator_configs / "Xenia")
            self.assertEqual(plan.command[4], str(rom))
            self.assertIn("-p1devicepath", plan.command)
            self.assertFalse(any(value.startswith("/userdata") for value in plan.environment.values()))

    def test_xbox360_can_delegate_appimage_outside_frontend_mount_namespace(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            runner = project / "scripts/run-external-provider"
            runner.parent.mkdir()
            runner.write_text("#!/bin/sh\n", encoding="utf-8")
            runner.chmod(0o755)
            appimage = root / "providers/Xenia Edge.AppImage"
            appimage.parent.mkdir()
            appimage.write_text("#!/bin/sh\n", encoding="utf-8")
            appimage.chmod(0o755)
            rom = root / "Test Game.iso"
            rom.write_bytes(b"read-only iso")
            env = {
                "HOME": str(root),
                "PATH": "",
                "EMBERCADE_HOST_PROVIDER_RUNNER": str(runner),
                "EMBERCADE_HOST_CONFIG_ROOT": str(root / "host config"),
                "EMBERCADE_HOST_DATA_ROOT": str(root / "host data"),
                "EMBERCADE_HOST_CACHE_ROOT": str(root / "host cache"),
            }
            paths = EmbercadePaths.from_environment(env)

            plan = create_launch_plan(
                system="xbox360",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={
                    "emulators": {
                        "xenia-edge": {
                            "provider": "appimage",
                            "executable": str(appimage),
                        }
                    }
                },
                environment=env,
                dry_run=False,
                controller=self._controller(Path("/dev/input/event23")),
            )

            self.assertEqual(plan.executable, appimage)
            self.assertEqual(plan.environment["EMBERCADE_XENIA_EDGE_BIN"], str(runner))
            self.assertEqual(
                plan.environment["EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE"], str(appimage)
            )
            self.assertEqual(
                plan.environment["EMBERCADE_EXTERNAL_PROVIDER_UNIT"],
                "embercade-xenia",
            )
            self.assertEqual(
                plan.environment["EMBERCADE_EXTERNAL_PROVIDER_HOME"],
                str(paths.data / "system"),
            )
            self.assertEqual(
                plan.environment["EMBERCADE_XENIA_EDGE_LOG"],
                str(paths.logs / "xenia-edge.log"),
            )
            self.assertEqual(
                plan.environment["EMBERCADE_XENIA_EDGE_STORAGE_ROOT"],
                str(root / "host config/emulators/Xenia"),
            )
            self.assertEqual(
                plan.environment["EMBERCADE_XENIA_EDGE_CONTENT_ROOT"],
                str(root / "host data/saves/xbox360"),
            )
            self.assertEqual(
                plan.environment["EMBERCADE_XENIA_EDGE_CACHE_ROOT"],
                str(root / "host cache/xenia-edge"),
            )

    def test_generic_libretro_missing_core_is_a_clear_prelaunch_error(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            retroarch = root / "bin/retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("#!/bin/sh\n", encoding="utf-8")
            retroarch.chmod(0o755)
            empty_cores = root / "empty cores"
            empty_cores.mkdir()
            rom = root / "Game.sfc"
            rom.write_bytes(b"rom")
            env = {"HOME": str(root), "PATH": str(retroarch.parent)}

            with self.assertRaisesRegex(LaunchError, "snes9x_libretro.so"):
                create_launch_plan(
                    system="snes",
                    rom=rom,
                    paths=EmbercadePaths.from_environment(env),
                    runtime=runtime,
                    config={"libretro": {"cores": str(empty_cores)}},
                    environment=env,
                    dry_run=True,
                    batocera_choice=self._choice("snes", "snes9x"),
                )

    def test_xbox_plan_uses_builtin_xemu_with_isolated_files(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            xemu = root / "bin" / "xemu"
            xemu.parent.mkdir()
            xemu.write_text("#!/bin/sh\n", encoding="utf-8")
            xemu.chmod(0o755)
            rom = root / "Test Game.iso"
            rom.write_bytes(b"iso")
            env = {"HOME": str(root), "PATH": str(xemu.parent)}
            paths = EmbercadePaths.from_environment(env)
            files = isolated_xemu_files(paths)
            for path in (files.flashrom, files.bootrom, files.eeprom, files.hdd):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"prepared")

            plan = create_launch_plan(
                system="xbox",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=env,
                dry_run=True,
                controller=self._controller(Path("/dev/input/event23")),
            )

            self.assertEqual(plan.executable, xemu)
            self.assertIsNone(plan.core)
            self.assertEqual(plan.command[4], str(rom))
            self.assertEqual(plan.environment["EMBERCADE_XEMU_BIN"], str(xemu))
            self.assertEqual(plan.environment["EMBERCADE_XEMU_FLASHROM"], str(files.flashrom))
            self.assertEqual(plan.environment["EMBERCADE_XEMU_BOOTROM"], str(files.bootrom))
            self.assertEqual(plan.environment["EMBERCADE_XEMU_EEPROM"], str(files.eeprom))
            self.assertEqual(plan.environment["EMBERCADE_XEMU_HDD"], str(files.hdd))
            self.assertFalse(any(value.startswith("/userdata") for value in plan.environment.values()))
            self.assertNotIn(str(Path.home() / ".local/share/xemu"), plan.environment.values())

    def test_ps2_plan_resolves_host_binary_and_private_bios_workspace(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            pcsx2 = root / "bin" / "pcsx2-qt"
            pcsx2.parent.mkdir()
            pcsx2.write_text("#!/bin/sh\n", encoding="utf-8")
            pcsx2.chmod(0o755)
            host_resources = root / "host/share/pcsx2/resources"
            host_resources.mkdir(parents=True)
            (host_resources / "GameIndex.yaml").write_text("games: {}\n", encoding="utf-8")
            (host_resources / "patches.zip").write_bytes(b"patches")
            bios = root / "existing PS2 BIOS"
            bios.mkdir()
            (bios / "ps2-0230a-20080220.bin").write_bytes(b"bios")
            rom = root / "Test Game.iso"
            rom.write_bytes(b"iso")
            env = {
                "HOME": str(root),
                "PATH": str(pcsx2.parent),
                "ENABLE_GAMESCOPE_WSI": "1",
                "EMBERCADE_PCSX2_BIOS_SOURCE": str(bios),
                "EMBERCADE_PCSX2_RESOURCES_SOURCE": str(host_resources),
            }
            paths = EmbercadePaths.from_environment(env)

            plan = create_launch_plan(
                system="ps2",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=env,
                dry_run=True,
                controller=self._controller(Path("/dev/input/event23")),
            )

            self.assertEqual(plan.executable, pcsx2)
            self.assertEqual(plan.environment["ENABLE_GAMESCOPE_WSI"], "1")
            self.assertEqual(plan.command[4], str(rom))
            self.assertEqual(plan.environment["EMBERCADE_PCSX2_BIN"], str(pcsx2))
            private_bios = paths.isolated_bios / "ps2"
            self.assertEqual(
                plan.environment["EMBERCADE_PCSX2_BIOS_DIR"], str(private_bios)
            )
            self.assertTrue(
                (private_bios / "ps2-0230a-20080220.bin").is_symlink()
            )
            self.assertEqual(
                plan.environment["EMBERCADE_PCSX2_RESOURCES"], str(host_resources)
            )
            self.assertIn("Microsoft X-Box 360 pad", plan.command)
            self.assertFalse(any(value.startswith("/userdata") for value in plan.environment.values()))
            self.assertNotIn(str(Path.home() / ".config/PCSX2"), plan.environment.values())

    def test_ps3_plan_resolves_plugin_binary_and_preserves_directory_argument(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            rpcs3 = root / "bin" / "rpcs3"
            rpcs3.parent.mkdir()
            rpcs3.write_text("#!/bin/sh\n", encoding="utf-8")
            rpcs3.chmod(0o755)
            firmware = root / "host-rpcs3"
            (firmware / "dev_flash/vsh/etc").mkdir(parents=True)
            (firmware / "dev_flash/vsh/etc/version.txt").write_text(
                "release:04.9300:build:test\n", encoding="utf-8"
            )
            (firmware / "dev_flash2").mkdir()
            (firmware / "dev_flash3").mkdir()
            rom = root / "God_of_War_III_EUR.ps3"
            (rom / "PS3_GAME/USRDIR").mkdir(parents=True)
            (rom / "PS3_GAME/USRDIR/EBOOT.BIN").write_bytes(b"eboot")
            env = {
                "HOME": str(root),
                "PATH": str(rpcs3.parent),
                "ENABLE_GAMESCOPE_WSI": "1",
                "EMBERCADE_RPCS3_FIRMWARE_SOURCE": str(firmware),
            }
            paths = EmbercadePaths.from_environment(env)
            prepare_rpcs3_firmware(paths, {}, env)

            plan = create_launch_plan(
                system="ps3",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=env,
                dry_run=True,
                controller=self._controller(Path("/dev/input/event23")),
            )

            self.assertEqual(plan.executable, rpcs3)
            self.assertEqual(plan.environment["ENABLE_GAMESCOPE_WSI"], "0")
            self.assertEqual(plan.command[4], str(rom))
            self.assertEqual(plan.environment["EMBERCADE_RPCS3_BIN"], str(rpcs3))
            self.assertEqual(
                plan.environment["EMBERCADE_RPCS3_FIRMWARE_SOURCE"], str(firmware)
            )
            self.assertIn("Xbox 360 Controller", plan.command)
            self.assertNotIn("Microsoft X-Box 360 pad", plan.command)
            self.assertFalse(any(value.startswith("/userdata") for value in plan.environment.values()))
            self.assertNotIn(str(Path.home() / ".config/rpcs3"), plan.environment.values())

    def test_desktop_sockets_are_made_explicit_before_xdg_isolation(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            self._resources(project)
            runtime = ProjectRuntime(project)
            runtime.launcher.parent.mkdir(parents=True)
            runtime.launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.launcher.chmod(0o755)
            retroarch = root / "bin" / "retroarch"
            retroarch.parent.mkdir()
            retroarch.write_text("#!/bin/sh\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "cores"
            cores.mkdir()
            (cores / "nestopia_libretro.so").write_bytes(b"core")
            rom = root / "game.nes"
            rom.write_bytes(b"rom")
            host_runtime = root / "host-runtime"
            pulse_socket = host_runtime / "pulse" / "native"
            pulse_socket.parent.mkdir(parents=True)
            listener = socket.socket(socket.AF_UNIX)
            self.addCleanup(listener.close)
            listener.bind(str(pulse_socket))
            wayland_socket = host_runtime / "wayland-1"
            wayland_listener = socket.socket(socket.AF_UNIX)
            self.addCleanup(wayland_listener.close)
            wayland_listener.bind(str(wayland_socket))
            env = {
                "HOME": str(root),
                "PATH": str(retroarch.parent),
                "XDG_RUNTIME_DIR": str(host_runtime),
                "WAYLAND_DISPLAY": "wayland-1",
            }

            plan = create_launch_plan(
                system="nes",
                rom=rom,
                paths=EmbercadePaths.from_environment(env),
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=env,
                dry_run=True,
                batocera_choice=self._choice("nes", "nestopia"),
            )

            self.assertEqual(plan.environment["PULSE_SERVER"], f"unix:{pulse_socket}")
            self.assertEqual(plan.environment["WAYLAND_DISPLAY"], str(wayland_socket))
            self.assertNotEqual(
                plan.environment["XDG_RUNTIME_DIR"],
                str(host_runtime),
            )
            self.assertEqual(
                plan.environment["EMBERCADE_HOST_SESSION_RUNTIME_ROOT"],
                str(host_runtime),
            )
            explicit_environment = {
                **env,
                "EMBERCADE_HOST_SESSION_RUNTIME_ROOT": str(root / "original-host-runtime"),
            }
            explicit_plan = create_launch_plan(
                system="nes",
                rom=rom,
                paths=EmbercadePaths.from_environment(env),
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=explicit_environment,
                dry_run=True,
                batocera_choice=self._choice("nes", "nestopia"),
            )
            self.assertEqual(
                explicit_plan.environment["EMBERCADE_HOST_SESSION_RUNTIME_ROOT"],
                explicit_environment["EMBERCADE_HOST_SESSION_RUNTIME_ROOT"],
            )

    def test_prepare_layout_writes_only_under_embercade_roots(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            defaults = project / "resources" / "defaults"
            defaults.mkdir(parents=True)
            (defaults / "batocera.conf").write_text("nes.core=nestopia\n", encoding="utf-8")
            (defaults / "es_settings.cfg").write_text("<config />\n", encoding="utf-8")
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root),
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                }
            )

            prepare_launch_layout(paths, project)

            self.assertTrue(paths.batocera_conf.is_file())
            self.assertTrue((paths.emulationstation_config / "es_settings.cfg").is_file())
            self.assertTrue(
                (paths.emulator_configs / "retroarch" / "retroarchcustom.cfg").is_file()
            )
            self.assertTrue(
                (
                    paths.emulator_configs
                    / "retroarch"
                    / "cores"
                    / "retroarch-core-options.cfg"
                ).is_file()
            )
            self.assertTrue((paths.saves / "gamecube").is_dir())
            self.assertTrue((paths.saves / "wii").is_dir())
            self.assertTrue((paths.saves / "snes").is_dir())
            self.assertTrue((paths.saves / "atari2600").is_dir())
            for resolved in paths.as_dict().values():
                self.assertTrue(str(resolved).startswith(str(root)))

    def test_run_launch_is_synchronous_subprocess_call(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.nes"
            core = root / "nestopia_libretro.so"
            executable = root / "retroarch"
            from embercade.launcher import LaunchPlan

            plan = LaunchPlan(("launcher", "-rom", str(rom)), {"A": "B"}, executable, core, rom)
            with patch("embercade.launcher.subprocess.run") as mocked:
                mocked.return_value.returncode = 7
                result = run_launch(plan)

            self.assertEqual(result, 7)
            mocked.assert_called_once_with(plan.command, env=dict(plan.environment), check=False)

    def test_real_azahar_launch_syncs_private_system_language_before_and_after(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.3ds"
            from embercade.launcher import LaunchPlan

            plan = LaunchPlan(
                ("launcher", "-rom", str(rom)),
                {
                    "EMBERCADE_BATOCERA_CONF": str(root / "batocera.conf"),
                    "EMBERCADE_SAVES": str(root / "saves"),
                },
                root / "retroarch",
                root / "azahar_libretro.so",
                rom,
                system="3ds",
                emulator="libretro",
                core_name="azahar",
            )
            with patch("embercade.launcher.sync_azahar_system_language") as sync, patch(
                "embercade.launcher.subprocess.run"
            ) as mocked:
                mocked.return_value.returncode = 0
                result = run_launch(plan)

            self.assertEqual(result, 0)
            self.assertEqual(sync.call_count, 2)
            sync.assert_called_with(
                batocera_conf=root / "batocera.conf",
                saves_root=root / "saves",
            )

    def test_real_xbox_launch_scopes_controller_exit_bridge_to_subprocess(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.iso"
            controller = self._controller(Path("/dev/input/event23"))
            player_two = ControllerDevice(
                1, controller.guid, controller.name, Path("/dev/input/event24"),
                controller.buttons, controller.hats, controller.axes, controller.mapping,
                real_name=controller.real_name,
            )
            from embercade.launcher import LaunchPlan

            events = []

            @contextmanager
            def bridge(_controller, *, emulator, on_exit):
                self.assertIs(_controller, controller)
                self.assertEqual(emulator, "xbox")
                events.append("bridge-enter")
                on_exit()
                try:
                    yield
                finally:
                    events.append("bridge-exit")

            plan = LaunchPlan(
                ("launcher", "-rom", str(rom)),
                {"A": "B"},
                root / "xemu",
                None,
                rom,
                controller,
                (controller, player_two),
                system="xbox",
                dry_run=False,
            )
            process = Mock()
            process.poll.return_value = None
            process.wait.side_effect = lambda: events.append("subprocess") or 0
            with patch("embercade.launcher.controller_exit_bridge", bridge), patch(
                "embercade.launcher.subprocess.Popen", return_value=process
            ) as popen:
                result = run_launch(plan)

            self.assertEqual(result, 0)
            self.assertEqual(events, ["bridge-enter", "subprocess", "bridge-exit"])
            process.send_signal.assert_called_once_with(signal.SIGINT)

    def test_real_ps3_launch_scopes_controller_exit_bridge_to_subprocess(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.ps3"
            controller = self._controller(Path("/dev/input/event23"))
            from embercade.launcher import LaunchPlan

            events = []

            @contextmanager
            def bridge(_controller, *, emulator, on_exit):
                events.append(f"bridge-enter-{emulator}")
                on_exit()
                try:
                    yield
                finally:
                    events.append("bridge-exit")

            plan = LaunchPlan(
                ("launcher", "-rom", str(rom)),
                {"A": "B"},
                root / "rpcs3",
                None,
                rom,
                controller,
                system="ps3",
                dry_run=False,
            )
            process = Mock()
            process.poll.return_value = None
            process.wait.side_effect = lambda: events.append("subprocess") or 0
            with patch("embercade.launcher.controller_exit_bridge", bridge), patch(
                "embercade.launcher.subprocess.Popen", return_value=process
            ) as popen:
                result = run_launch(plan)

            self.assertEqual(result, 0)
            self.assertEqual(events, ["bridge-enter-ps3", "subprocess", "bridge-exit"])
            process.send_signal.assert_called_once_with(signal.SIGINT)
            popen.assert_called_once_with(
                plan.command,
                env=dict(plan.environment),
            )

    def test_xenia_exit_stops_only_its_named_provider_service(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.iso"
            controller = self._controller(Path("/dev/input/event23"))
            from embercade.launcher import LaunchPlan

            @contextmanager
            def bridge(_controller, *, emulator, on_exit):
                self.assertEqual(emulator, "xbox360")
                on_exit()
                yield

            plan = LaunchPlan(
                ("launcher", "-rom", str(rom)),
                {
                    "PATH": "/usr/bin",
                    "EMBERCADE_EXTERNAL_PROVIDER_UNIT": "embercade-xenia",
                    "XDG_RUNTIME_DIR": "/userdata/system/xdg/runtime/embercade",
                    "EMBERCADE_HOST_SESSION_RUNTIME_ROOT": "/run/user/1000",
                    "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
                },
                root / "xenia.AppImage",
                None,
                rom,
                controller,
                system="xbox360",
                dry_run=False,
            )
            process = Mock()
            process.poll.return_value = None
            process.wait.return_value = 0
            stopped = subprocess.CompletedProcess((), 0)
            with (
                patch("embercade.launcher.controller_exit_bridge", bridge),
                patch("embercade.launcher.subprocess.Popen", return_value=process),
                patch("embercade.launcher.subprocess.run", return_value=stopped) as run,
                patch("embercade.launcher.shutil.which", return_value="/usr/bin/systemctl"),
            ):
                self.assertEqual(run_launch(plan), 0)

            run.assert_called_once_with(
                (
                    "/usr/bin/systemctl",
                    "--user",
                    "stop",
                    "embercade-xenia.service",
                ),
                env={**plan.environment, "XDG_RUNTIME_DIR": "/run/user/1000"},
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            process.send_signal.assert_not_called()
            self.assertEqual(
                plan.environment["XDG_RUNTIME_DIR"], "/userdata/system/xdg/runtime/embercade"
            )

    def test_xbox_dry_run_does_not_start_exit_bridge(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.iso"
            from embercade.launcher import LaunchPlan

            plan = LaunchPlan(
                ("launcher", "-rom", str(rom)),
                {},
                root / "xemu",
                None,
                rom,
                self._controller(Path("/dev/input/event23")),
                system="xbox",
                dry_run=True,
            )
            with patch("embercade.launcher.controller_exit_bridge") as bridge, patch(
                "embercade.launcher.subprocess.run"
            ) as mocked:
                mocked.return_value.returncode = 0
                self.assertEqual(run_launch(plan), 0)
            bridge.assert_not_called()

    def test_ps2_uses_native_exit_without_external_bridge(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "game.iso"
            from embercade.launcher import LaunchPlan

            plan = LaunchPlan(
                ("launcher", "-rom", str(rom)),
                {},
                root / "pcsx2-qt",
                None,
                rom,
                self._controller(Path("/dev/input/event23")),
                system="ps2",
                dry_run=False,
            )
            with patch("embercade.launcher.controller_exit_bridge") as bridge, patch(
                "embercade.launcher.subprocess.run"
            ) as mocked:
                mocked.return_value.returncode = 0
                self.assertEqual(run_launch(plan), 0)
            bridge.assert_not_called()

    def test_missing_rom_is_rejected_before_launch(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(LaunchError, "ROM is not a readable file"):
                create_launch_plan(
                    system="nes",
                    rom=root / "missing.nes",
                    paths=EmbercadePaths.from_environment({"HOME": str(root)}),
                    runtime=ProjectRuntime(root),
                    config={},
                    environment={"HOME": str(root), "PATH": os.environ.get("PATH", "")},
                )


if __name__ == "__main__":
    unittest.main()

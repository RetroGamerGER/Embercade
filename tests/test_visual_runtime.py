from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import os
import shlex
import subprocess
import unittest

from PIL import Image

from embercade.batocera_config import BatoceraSystemChoice
from embercade.controller import ControllerDevice, write_es_input_override
from embercade.dolphin_dry_run import execute_dry_run as execute_dolphin_dry_run
from embercade.launcher import create_launch_plan, prepare_launch_layout
from embercade.paths import EmbercadePaths
from embercade.runtime import ProjectRuntime
from embercade.rpcs3 import prepare_rpcs3_firmware
from embercade.xemu import prepare_xemu_files
from graphics_helpers import with_graphics_probe


class VisualRuntimeTests(unittest.TestCase):
    def test_fresh_defaults_have_no_shader_and_clear_stale_enabled_effect(self):
        project = Path(__file__).resolve().parents[1]
        defaults = (project / 'resources/defaults/batocera.conf').read_text()
        shader_settings = [line.strip() for line in defaults.splitlines()
                           if '.shaderset=' in line and not line.lstrip().startswith('#')]
        self.assertEqual(shader_settings, ['global.shaderset=none'])
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            executable = bin_dir / 'retroarch'
            executable.write_text('#!/bin/sh\nexit 99\n')
            executable.chmod(0o755)
            cores = root / 'cores'
            cores.mkdir()
            (cores / 'gambatte_libretro.so').write_bytes(b'\x7fELFfixture')
            rom = root / 'roms/gb/Test.gb'
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b'synthetic; dry run only')
            bios = root / 'bios'
            bios.mkdir()
            environment = dict(os.environ, HOME=str(root / 'home'),
                               PATH=f'{bin_dir}:{os.environ.get("PATH", "")}',
                               EMBERCADE_CONFIG_HOME=str(root / 'config'),
                               EMBERCADE_DATA_HOME=str(root / 'data'),
                               EMBERCADE_STATE_HOME=str(root / 'state'),
                               EMBERCADE_CACHE_HOME=str(root / 'cache'),
                               EMBERCADE_RUNTIME_HOME=str(root / 'runtime'),
                               EMBERCADE_DISPLAY_WIDTH='1280', EMBERCADE_DISPLAY_HEIGHT='720')
            environment.pop('XDG_RUNTIME_DIR', None)
            environment.pop('WAYLAND_DISPLAY', None)
            environment.pop('DISPLAY', None)
            config = {'paths': {'bios': str(bios)}, 'libretro': {'cores': str(cores)}}
            paths = EmbercadePaths.from_environment(environment, config=config)
            prepare_launch_layout(paths, project)
            self.assertEqual(paths.batocera_conf.read_text(), defaults)
            settings = paths.emulator_configs / 'retroarch/retroarchcustom.cfg'
            for stale in ('', 'video_shader_enable = "true"\nvideo_shader = "old.slangp"\n'):
                with self.subTest(stale=bool(stale)):
                    settings.write_text(stale)
                    plan = create_launch_plan(system='gb', rom=rom, paths=paths,
                        runtime=ProjectRuntime(project), config=config, environment=environment,
                        dry_run=True, batocera_choice=BatoceraSystemChoice('gb','libretro','gambatte',False,False))
                    plan = with_graphics_probe(plan)
                    completed = subprocess.run(plan.command, env=dict(plan.environment),
                                               capture_output=True, text=True, timeout=30)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    final = next(line for line in completed.stdout.splitlines()
                                 if line.startswith('EMBERCADE_FINAL_COMMAND='))
                    self.assertNotIn('--set-shader', shlex.split(final.partition('=')[2]))
                    self.assertIn('video_shader_enable = false', settings.read_text())
                    self.assertEqual(paths.batocera_conf.read_text(), defaults)

    def test_libretro_launch_replaces_legacy_qt_autostart_but_keeps_user_overrides(self) -> None:
        project = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "host bin"
            fake_bin.mkdir()
            retroarch = fake_bin / "retroarch"
            retroarch.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "host cores"
            cores.mkdir()
            (cores / "gambatte_libretro.so").write_bytes(b"\x7fELFcore")
            rom = root / "read only ROMs/gb/Game with spaces.gb"
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b"read-only content")
            bios = root / "read only BIOS"
            bios.mkdir()
            environment = dict(os.environ)
            environment.update({
                "HOME": str(root / "home"),
                "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                "EMBERCADE_STATE_HOME": str(root / "isolated/state"),
                "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                "EMBERCADE_DISPLAY_WIDTH": "2560",
                "EMBERCADE_DISPLAY_HEIGHT": "1440",
            })
            config = {"paths": {"bios": str(bios)}, "libretro": {"cores": str(cores)}}
            paths = EmbercadePaths.from_environment(environment, config=config)
            prepare_launch_layout(paths, project)
            settings = paths.emulator_configs / "retroarch/retroarchcustom.cfg"
            companion = ("desktop_menu_enable", "ui_companion_start_on_boot", "ui_companion_toggle")
            save = paths.saves / "gb/keep.srm"
            save.write_bytes(b"preserved save")
            for explicit in (False, True):
                with self.subTest(explicit_override=explicit):
                    settings.write_text(
                        'menu_driver = "rgui"\n'
                        + "".join(f'{key} = "true"\n' for key in companion),
                        encoding="utf-8",
                    )
                    extra = "".join(f"gb.retroarch.{key}=true\n" for key in companion) if explicit else ""
                    paths.batocera_conf.write_text(
                        (project / "resources/defaults/batocera.conf").read_text() + extra,
                        encoding="utf-8",
                    )
                    plan = create_launch_plan(
                        system="gb", rom=rom, paths=paths, runtime=ProjectRuntime(project),
                        config=config, environment=environment, dry_run=True,
                        batocera_choice=BatoceraSystemChoice("gb", "libretro", "gambatte", False, False),
                    )
                    completed = subprocess.run(
                        plan.command, capture_output=True, text=True,
                        env=dict(plan.environment), check=False, timeout=60,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    generated = settings.read_text(encoding="utf-8")
                    values = {
                        key.strip(): value.strip().strip('"')
                        for line in generated.splitlines()
                        for key, separator, value in (line.partition("="),) if separator
                    }
                    for key in companion:
                        self.assertEqual(values[key], "true" if explicit else "false")
                    self.assertEqual(values["menu_driver"], "rgui")
                    self.assertEqual(save.read_bytes(), b"preserved save")
                    self.assertEqual(rom.read_bytes(), b"read-only content")
                    command = next(
                        line.removeprefix("EMBERCADE_FINAL_COMMAND=")
                        for line in completed.stdout.splitlines()
                        if line.startswith("EMBERCADE_FINAL_COMMAND=")
                    )
                    self.assertEqual(shlex.split(command)[0], str(retroarch))

    def test_new_libretro_systems_generate_batocera_options_and_isolated_writes(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        cases = {
            "3ds": (
                "azahar",
                "azahar_libretro.so",
                ".3ds",
                ('citra_layout_option = "default"', 'citra_resolution_factor = "1"'),
            ),
            "amiga1200": (
                "puae",
                "puae_libretro.so",
                ".lha",
                ('puae_model = "A1200"', 'puae_use_whdload_prefs = "config"'),
            ),
            "dos": (
                "dosbox_pure",
                "dosbox_pure_libretro.so",
                ".zip",
                ('dosbox_pure_conf = "inside"', 'dosbox_pure_auto_mapping = "true"'),
            ),
            "jaguar": (
                "virtualjaguar",
                "virtualjaguar_libretro.so",
                ".j64",
                (
                    'virtualjaguar_usefastblitter = "enabled"',
                    'virtualjaguar_bios = "enabled"',
                    'virtualjaguar_doom_res_hack = "disabled"',
                ),
            ),
            "mame": (
                "mame078plus",
                "mame2003_plus_libretro.so",
                ".zip",
                ('mame2003-plus_input_interface = "retropad"', 'mame2003-plus_skip_warnings = "enabled"'),
            ),
            "c64": (
                "vice_x64",
                "vice_x64_libretro.so",
                ".t64",
                ('vice_c64_model = "C64 PAL auto"', "vice_mapper_select = TOGGLE_VKBD"),
            ),
            "nds": (
                "melondsds",
                "melondsds_libretro.so",
                ".nds",
                ('melonds_screen_layout1 = "top-bottom"', 'melonds_touch_mode = "joystick"'),
            ),
            "n64": (
                "mupen64plus-next",
                "mupen64plus_next_libretro.so",
                ".n64",
                (
                    'mupen64plus-rdp-plugin = "gliden64"',
                    'mupen64plus-rsp-plugin = "hle"',
                    'mupen64plus-pak1 = "memory"',
                ),
            ),
            "psp": (
                "ppsspp",
                "ppsspp_libretro.so",
                ".iso",
                ('ppsspp_internal_resolution = "960x544"',),
            ),
        }
        for system, (core_name, binary_name, suffix, option_fragments) in cases.items():
            with self.subTest(system=system), TemporaryDirectory() as directory:
                root = Path(directory)
                fake_bin = root / "host bin"
                fake_bin.mkdir()
                retroarch = fake_bin / "retroarch"
                retroarch.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
                retroarch.chmod(0o755)
                cores = root / "host cores"
                cores.mkdir()
                core = cores / binary_name
                core.write_bytes(b"\x7fELFcore")
                rom = root / f"read only ROMs/{system}/Game with spaces{suffix}"
                rom.parent.mkdir(parents=True)
                rom.write_bytes(b"read-only content")
                bios = root / "read only BIOS"
                (bios / "amiga").mkdir(parents=True)
                (bios / "amiga/kick40068.A1200").write_bytes(b"read-only kickstart")
                ppsspp_assets = root / "official PPSSPP assets"
                (ppsspp_assets / "lang").mkdir(parents=True)
                (ppsspp_assets / "flash0").mkdir()
                (ppsspp_assets / "ppge_atlas.zim").write_bytes(b"read-only assets")
                before = hashlib.sha256(rom.read_bytes()).hexdigest(), rom.stat().st_mtime_ns
                environment = dict(os.environ)
                environment.update(
                    {
                        "HOME": str(root / "home"),
                        "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                        "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                        "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                        "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                        "EMBERCADE_STATE_HOME": str(root / "isolated/state"),
                        "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                        "EMBERCADE_DISPLAY_WIDTH": "2560",
                        "EMBERCADE_DISPLAY_HEIGHT": "1440",
                    }
                )
                paths = EmbercadePaths.from_environment(
                    environment,
                    config={
                        "paths": {"roms": str(root / "read only ROMs"), "bios": str(bios)},
                        "libretro": {
                            "cores": str(cores),
                            "ppsspp_assets": str(ppsspp_assets),
                        },
                    },
                )
                prepare_launch_layout(paths, project)
                if system == "amiga1200":
                    stale_options = (
                        paths.emulator_configs / "retroarch/config/PUAE/PUAE.opt"
                    )
                    stale_options.parent.mkdir(parents=True, exist_ok=True)
                    stale_options.write_text(
                        'puae_mapper_select = "---"\n'
                        'puae_model = "CD32FR"\n',
                        encoding="utf-8",
                    )
                controller = ControllerDevice(
                    0,
                    "030081b85e0400008e02000010010000",
                    "Xbox 360 Controller",
                    Path("/dev/input/event23"),
                    11,
                    1,
                    6,
                    "test mapping",
                    real_name="Microsoft X-Box 360 pad",
                )
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
                    environment=environment,
                    dry_run=True,
                    controller=controller,
                    batocera_choice=BatoceraSystemChoice(
                        system, "libretro", core_name, False, False
                    ),
                )
                completed = subprocess.run(
                    plan.command,
                    check=False,
                    capture_output=True,
                    env=dict(plan.environment),
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                output = completed.stdout + completed.stderr
                generated = (
                    paths.emulator_configs / "retroarch/retroarchcustom.cfg"
                ).read_text(encoding="utf-8")
                options = (
                    paths.emulator_configs / "retroarch/cores/retroarch-core-options.cfg"
                ).read_text(encoding="utf-8")
                command_line = next(
                    line.removeprefix("EMBERCADE_FINAL_COMMAND=")
                    for line in output.splitlines()
                    if line.startswith("EMBERCADE_FINAL_COMMAND=")
                )
                final_command = shlex.split(command_line)
                self.assertEqual(final_command[0:3], [str(retroarch), "-L", str(core)])
                self.assertEqual(final_command[-1], str(rom))
                self.assertIn(f'savefile_directory = "{paths.saves / system}"', generated)
                self.assertIn(f'savestate_directory = "{paths.saves / system}"', generated)
                self.assertIn("input_overlay_enable = true", generated)
                for fragment in option_fragments:
                    self.assertIn(fragment, options)
                if system == "amiga1200":
                    self.assertIn(f'system_directory = "{bios / "amiga"}"', generated)
                    self.assertIn("input_libretro_device_p1 = 1", generated)
                    self.assertIn('global_core_options = "true"', generated)
                    self.assertIn('game_specific_options = "false"', generated)
                    self.assertIn("puae_mapper_select = TOGGLE_VKBD", options)
                if system == "n64":
                    self.assertIn('video_driver = "glcore"', generated)
                self.assertNotIn("/userdata", generated + options + output)
                self.assertEqual(
                    before,
                    (hashlib.sha256(rom.read_bytes()).hexdigest(), rom.stat().st_mtime_ns),
                )

    def test_wii_dolphin_dry_run_refreshes_roots_and_isolates_nand(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "host bin"
            fake_bin.mkdir()
            dolphin = fake_bin / "dolphin-emu"
            dolphin.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            dolphin.chmod(0o755)
            rom_root = root / "read only ROMs"
            rom = rom_root / "wii/Test Game.rvz"
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b"read-only rvz")
            environment = dict(os.environ)
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                    "EMBERCADE_DISPLAY_WIDTH": "2560",
                    "EMBERCADE_DISPLAY_HEIGHT": "1440",
                }
            )
            paths = EmbercadePaths.from_environment(
                environment,
                config={"paths": {"roms": str(rom_root)}},
            )
            prepare_launch_layout(paths, project)
            dolphin_ini = paths.emulator_configs / "dolphin-emu/Dolphin.ini"
            dolphin_ini.parent.mkdir(parents=True)
            dolphin_ini.write_text(
                "[General]\nISOPath0 = /stale/wii\nISOPath1 = /stale/gamecube\nISOPaths = 2\n",
                encoding="utf-8",
            )
            with paths.batocera_conf.open("a", encoding="utf-8") as stream:
                stream.write("\nwii.emulatedwiimotes=true\n")
            controller = ControllerDevice(
                0,
                "030081b85e0400008e02000010010000",
                "Xbox 360 Controller",
                Path("/dev/input/event23"),
                11,
                1,
                6,
                "test mapping",
                real_name="Microsoft X-Box 360 pad",
            )
            plan = create_launch_plan(
                system="wii",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=environment,
                dry_run=True,
                controller=controller,
            )

            original_config = paths.batocera_conf.read_text()
            for available, override, expected in ((True, None, "Vulkan"), (False, None, "OGL"),
                                                   (True, "OGL", "OGL"), (False, "Vulkan", "OGL")):
                with self.subTest(vulkan=available, override=override):
                    paths.batocera_conf.write_text(original_config + (f"\nwii.gfxbackend={override}\n" if override else ""))
                    execute_dolphin_dry_run(with_graphics_probe(plan, available), paths)
                    self.assertIn(f"GFXBackend = {expected}", dolphin_ini.read_text())
            paths.batocera_conf.write_text(original_config)
            row = execute_dolphin_dry_run(with_graphics_probe(plan, True), paths)

            generated = dolphin_ini.read_text(encoding="utf-8")
            self.assertIn(f"ISOPath0 = {rom_root / 'wii'}", generated)
            self.assertIn(f"ISOPath1 = {rom_root / 'gamecube'}", generated)
            self.assertNotIn("/stale/", generated)
            self.assertEqual(row["final_command"], [str(dolphin), "-b", "-e", str(rom)])
            self.assertEqual(row["nand_root"], str(paths.saves / "dolphin-emu/Wii"))
            self.assertEqual(row["special_controller_validation"], "PENDING")
            self.assertFalse((root / "home/.config/dolphin-emu").exists())

    def test_cd32_disc_dry_run_uses_amiga_bios_and_isolated_writes(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.launcher.is_file())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "host bin"
            fake_bin.mkdir()
            retroarch = fake_bin / "retroarch"
            retroarch.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "host cores"
            cores.mkdir()
            core = cores / "puae_libretro.so"
            core.write_bytes(b"\x7fELFcore")
            rom = root / "ROM files/Naughty Ones (Europe).chd"
            rom.parent.mkdir()
            rom.write_bytes(b"read-only chd")
            bios = root / "read only BIOS"
            (bios / "amiga").mkdir(parents=True)
            firmware = bios / "amiga/kick40060.CD32"
            firmware.write_bytes(b"read-only firmware")
            inputs = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (rom, firmware)
            }

            environment = dict(os.environ)
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated tree/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated tree/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated tree/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated tree/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated tree/runtime"),
                    "EMBERCADE_DISPLAY_WIDTH": "2560",
                    "EMBERCADE_DISPLAY_HEIGHT": "1440",
                }
            )
            paths = EmbercadePaths.from_environment(
                environment,
                config={"paths": {"bios": str(bios)}, "libretro": {"cores": str(cores)}},
            )
            prepare_launch_layout(paths, project)
            controller = ControllerDevice(
                index=0,
                guid="030081b85e0400008e02000010010000",
                name="Xbox 360 Controller",
                device_path=Path("/dev/input/event23"),
                buttons=11,
                hats=1,
                axes=6,
                mapping="test mapping",
                real_name="Microsoft X-Box 360 pad",
                usb_vendor="045e",
                usb_product="028e",
                kernel_driver="xpad",
            )
            plan = create_launch_plan(
                system="amigacd32",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=environment,
                dry_run=True,
                controller=controller,
                batocera_choice=BatoceraSystemChoice(
                    "amigacd32", "libretro", "puae", False, False
                ),
            )
            completed = subprocess.run(
                plan.command,
                check=False,
                capture_output=True,
                env=dict(plan.environment),
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = completed.stdout + completed.stderr
            generated = (
                paths.emulator_configs / "retroarch/retroarchcustom.cfg"
            ).read_text(encoding="utf-8")
            options = (
                paths.emulator_configs / "retroarch/cores/retroarch-core-options.cfg"
            ).read_text(encoding="utf-8")

            command_line = next(
                line.removeprefix("EMBERCADE_FINAL_COMMAND=")
                for line in output.splitlines()
                if line.startswith("EMBERCADE_FINAL_COMMAND=")
            )
            final_command = shlex.split(command_line)
            self.assertEqual(final_command[0:3], [str(retroarch), "-L", str(core)])
            self.assertEqual(final_command[-1], str(rom))
            self.assertIn(f'system_directory = "{bios / "amiga"}"', generated)
            self.assertIn(f'savefile_directory = "{paths.saves / "amigacd32"}"', generated)
            self.assertIn(f'savestate_directory = "{paths.saves / "amigacd32"}"', generated)
            self.assertIn("input_libretro_device_p1 = 517", generated)
            self.assertIn("input_overlay_enable = true", generated)
            self.assertIn('puae_model = "CD32FR"', options)
            self.assertNotIn("/userdata", generated + options + output)
            self.assertFalse((root / "home/.config/retroarch").exists())
            self.assertEqual(
                inputs,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (rom, firmware)
                },
            )

    def test_pcenginecd_cue_bin_dry_run_needs_no_firmware_file(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.launcher.is_file())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "host bin"
            fake_bin.mkdir()
            retroarch = fake_bin / "retroarch"
            retroarch.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "host cores"
            cores.mkdir()
            core = cores / "mednafen_pce_libretro.so"
            core.write_bytes(b"\x7fELFcore")
            rom = root / "ROM files/1552 Tenka Tairan (Japan).cue"
            track = rom.with_name("1552 Tenka Tairan (Japan) (Track 01).bin")
            rom.parent.mkdir()
            rom.write_text(f'FILE "{track.name}" BINARY\n', encoding="utf-8")
            track.write_bytes(b"read-only track")
            bios = root / "empty read only BIOS"
            bios.mkdir()
            inputs = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (rom, track)
            }

            environment = dict(os.environ)
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated tree/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated tree/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated tree/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated tree/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated tree/runtime"),
                    "EMBERCADE_DISPLAY_WIDTH": "2560",
                    "EMBERCADE_DISPLAY_HEIGHT": "1440",
                }
            )
            paths = EmbercadePaths.from_environment(
                environment,
                config={"paths": {"bios": str(bios)}, "libretro": {"cores": str(cores)}},
            )
            prepare_launch_layout(paths, project)
            controller = ControllerDevice(
                index=0,
                guid="030081b85e0400008e02000010010000",
                name="Xbox 360 Controller",
                device_path=Path("/dev/input/event23"),
                buttons=11,
                hats=1,
                axes=6,
                mapping="test mapping",
                real_name="Microsoft X-Box 360 pad",
                usb_vendor="045e",
                usb_product="028e",
                kernel_driver="xpad",
            )
            plan = create_launch_plan(
                system="pcenginecd",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=environment,
                dry_run=True,
                controller=controller,
                batocera_choice=BatoceraSystemChoice(
                    "pcenginecd", "libretro", "pce", False, False
                ),
            )
            completed = subprocess.run(
                plan.command,
                check=False,
                capture_output=True,
                env=dict(plan.environment),
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = completed.stdout + completed.stderr
            generated = (
                paths.emulator_configs / "retroarch/retroarchcustom.cfg"
            ).read_text(encoding="utf-8")
            command_line = next(
                line.removeprefix("EMBERCADE_FINAL_COMMAND=")
                for line in output.splitlines()
                if line.startswith("EMBERCADE_FINAL_COMMAND=")
            )
            final_command = shlex.split(command_line)

            self.assertEqual(final_command[0:3], [str(retroarch), "-L", str(core)])
            self.assertEqual(final_command[-1], str(rom))
            self.assertIn(f'system_directory = "{bios}"', generated)
            self.assertIn(f'savefile_directory = "{paths.saves / "pcenginecd"}"', generated)
            self.assertIn(f'savestate_directory = "{paths.saves / "pcenginecd"}"', generated)
            self.assertIn("input_overlay_enable = true", generated)
            self.assertNotIn("/userdata", generated + output)
            self.assertFalse((root / "home/.config/retroarch").exists())
            self.assertEqual(
                inputs,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (rom, track)
                },
            )

    def test_libretro_config_quotes_all_desktop_paths_with_spaces(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.launcher.is_file())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "host bin"
            fake_bin.mkdir()
            retroarch = fake_bin / "retroarch"
            retroarch.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cores = root / "host cores"
            cores.mkdir()
            core = cores / "swanstation_libretro.so"
            core.write_bytes(b"\x7fELFcore")
            rom = root / "ROM files/007 - The World Is Not Enough (Europe).chd"
            rom.parent.mkdir()
            rom.write_bytes(b"read-only chd")
            bios = root / "read only BIOS"
            bios.mkdir()

            environment = dict(os.environ)
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated tree/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated tree/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated tree/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated tree/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated tree/runtime"),
                    "EMBERCADE_DISPLAY_WIDTH": "2560",
                    "EMBERCADE_DISPLAY_HEIGHT": "1440",
                }
            )
            paths = EmbercadePaths.from_environment(
                environment,
                config={"paths": {"bios": str(bios)}},
            )
            prepare_launch_layout(paths, project)
            controller = ControllerDevice(
                index=0,
                guid="030081b85e0400008e02000010010000",
                name="Xbox 360 Controller",
                device_path=Path("/dev/input/event23"),
                buttons=11,
                hats=1,
                axes=6,
                mapping="test mapping",
                real_name="Microsoft X-Box 360 pad",
                usb_vendor="045e",
                usb_product="028e",
                kernel_driver="xpad",
            )
            plan = create_launch_plan(
                system="psx",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={"libretro": {"cores": str(cores)}},
                environment=environment,
                dry_run=True,
                controller=controller,
                batocera_choice=BatoceraSystemChoice(
                    "psx", "libretro", "swanstation", False, True
                ),
            )
            completed = subprocess.run(
                plan.command,
                check=False,
                capture_output=True,
                env=dict(plan.environment),
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            generated = (
                paths.emulator_configs / "retroarch/retroarchcustom.cfg"
            ).read_text(encoding="utf-8")

            for setting, expected in (
                ("assets_directory", runtime.share / "libretro/assets"),
                ("cache_directory", paths.emulator_configs / "retroarch/cache"),
                ("libretro_directory", cores),
                ("libretro_info_path", runtime.share / "libretro/info"),
                ("savefile_directory", paths.saves / "psx"),
                ("savestate_directory", paths.saves / "psx"),
            ):
                self.assertIn(f'{setting} = "{expected}"', generated)

    def test_rpcs3_plugin_generates_isolated_config_without_network_or_sysctl(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.launcher.is_file())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            rpcs3 = fake_bin / "rpcs3"
            rpcs3.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            rpcs3.chmod(0o755)
            rom = root / "God_of_War_III_EUR.ps3"
            (rom / "PS3_GAME/USRDIR").mkdir(parents=True)
            eboot = rom / "PS3_GAME/USRDIR/EBOOT.BIN"
            eboot.write_bytes(b"read-only eboot")

            firmware = root / "host-rpcs3"
            (firmware / "dev_flash/vsh/etc").mkdir(parents=True)
            version = firmware / "dev_flash/vsh/etc/version.txt"
            version.write_text("release:04.9300:build:test\n", encoding="utf-8")
            (firmware / "dev_flash2").mkdir()
            (firmware / "dev_flash3").mkdir()
            icons = root / "host-icons"
            icons.mkdir()
            (icons / "test.png").write_bytes(b"icon")
            before = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (eboot, version, icons / "test.png")
            }

            static = root / "static"
            shaders = static / "shaders/configs"
            decorations = static / "decorations"
            shaders.mkdir(parents=True)
            decorations.mkdir(parents=True)
            (shaders / "rendering-defaults.yml").write_text("default: {}\n", encoding="utf-8")

            environment = dict(os.environ)
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                    "EMBERCADE_RPCS3_FIRMWARE_SOURCE": str(firmware),
                    "EMBERCADE_RPCS3_ICONS_SOURCE": str(icons),
                    "EMBERCADE_SHADER_RESOURCES": str(static / "shaders"),
                    "EMBERCADE_DECORATION_RESOURCES": str(decorations),
                }
            )
            paths = EmbercadePaths.from_environment(environment)
            prepare_launch_layout(paths, project)
            prepare_rpcs3_firmware(paths, {}, environment)
            controller = ControllerDevice(
                index=0,
                guid="030081b85e0400008e02000010010000",
                name="Xbox 360 Controller",
                device_path=Path("/dev/input/event23"),
                buttons=11,
                hats=1,
                axes=6,
                mapping="test mapping",
                real_name="Microsoft X-Box 360 pad",
                usb_vendor="045e",
                usb_product="028e",
                kernel_driver="xpad",
            )
            write_es_input_override(
                controller,
                runtime.share / "emulationstation/es_input.cfg",
                paths.emulationstation_config / "es_input.cfg",
            )
            plan = create_launch_plan(
                system="ps3",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=environment,
                dry_run=True,
                controller=controller,
            )
            completed = subprocess.run(
                plan.command,
                check=False,
                capture_output=True,
                env=dict(plan.environment),
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = completed.stdout + completed.stderr
            config_dir = paths.emulator_configs / "rpcs3"
            config = (config_dir / "config.yml").read_text(encoding="utf-8")
            vfs = (config_dir / "vfs.yml").read_text(encoding="utf-8")
            pads = (config_dir / "input_configs/global/Default.yml").read_text(
                encoding="utf-8"
            )

            self.assertIn(f"EMBERCADE_FINAL_COMMAND={rpcs3}", output)
            self.assertIn(str(eboot), output)
            self.assertIn("--no-gui", output)
            self.assertIn("Renderer:", config)
            self.assertIn("Renderer: Cubeb", config)
            self.assertIn(str(paths.saves / "ps3/rpcs3/dev_hdd0"), vfs)
            self.assertIn("$(EmulatorDir)dev_flash/", vfs)
            self.assertIn("Handler: SDL", pads)
            self.assertIn("Device: Xbox 360 Controller 1", pads)
            self.assertIn("PS Button: Guide", pads)
            self.assertFalse((config_dir / "GuiConfigs/config_database.dat").exists())
            self.assertNotIn("/userdata", config + vfs + pads + output)
            self.assertNotIn("/var/run", vfs + output)
            self.assertNotIn("rpcs3-exit", output)
            self.assertNotIn("vm.overcommit_memory", output)
            self.assertNotIn("mangohud", output.lower())
            self.assertEqual(plan.environment["XDG_STATE_HOME"], str(paths.state))
            self.assertFalse((root / "home/.config/rpcs3").exists())
            self.assertEqual(
                before,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (eboot, version, icons / "test.png")
                },
            )

    def test_pcsx2_plugin_generates_an_isolated_desktop_launch(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.launcher.is_file())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            pcsx2 = fake_bin / "pcsx2-qt"
            pcsx2.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            pcsx2.chmod(0o755)
            rom = root / "Test Game.iso"
            rom.write_bytes(b"read-only iso")
            bios = root / "existing bios"
            bios.mkdir()
            bios_image = bios / "ps2-0230a-20080220.bin"
            bios_image.write_bytes(b"read-only bios")
            resources = root / "host/share/pcsx2/resources"
            resources.mkdir(parents=True)
            (resources / "GameIndex.yaml").write_text("games: {}\n", encoding="utf-8")
            (resources / "patches.zip").write_bytes(b"host patches")
            input_hashes = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (rom, bios_image, resources / "patches.zip")
            }

            environment = dict(os.environ)
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                    "EMBERCADE_PCSX2_BIOS_SOURCE": str(bios),
                    "EMBERCADE_PCSX2_RESOURCES_SOURCE": str(resources),
                }
            )
            paths = EmbercadePaths.from_environment(environment)
            prepare_launch_layout(paths, project)
            controller = ControllerDevice(
                index=0,
                guid="030081b85e0400008e02000010010000",
                name="Xbox 360 Controller",
                device_path=Path("/dev/input/event23"),
                buttons=11,
                hats=1,
                axes=6,
                mapping="test mapping",
                real_name="Microsoft X-Box 360 pad",
                usb_vendor="045e",
                usb_product="028e",
                kernel_driver="xpad",
            )
            plan = create_launch_plan(
                system="ps2",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=environment,
                dry_run=True,
                controller=controller,
            )
            original_config = paths.batocera_conf.read_text()
            for available, override, expected in ((True, None, "14"), (False, None, "-1"), (True, "12", "12"), (False, "12", "12"), (True, "-1", "-1")):
                with self.subTest(vulkan=available, override=override):
                    paths.batocera_conf.write_text(original_config + (f"\nps2.pcsx2_gfxbackend={override}\n" if override else ""))
                    injected = with_graphics_probe(plan, available)
                    completed = subprocess.run(injected.command, check=False, capture_output=True, env=dict(injected.environment), text=True)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    generated = (paths.emulator_configs / "PCSX2/inis/PCSX2.ini").read_text()
                    self.assertIn(f"Renderer = {expected}", generated)
            paths.batocera_conf.write_text(original_config)
            injected = with_graphics_probe(plan, True)
            completed = subprocess.run(injected.command, check=False, capture_output=True, env=dict(injected.environment), text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = completed.stdout + completed.stderr
            config_dir = paths.emulator_configs / "PCSX2"
            generated = (config_dir / "inis/PCSX2.ini").read_text(encoding="utf-8")
            registry = (config_dir / "PCSX2-reg.ini").read_text(encoding="utf-8")

            self.assertIn(f"EMBERCADE_FINAL_COMMAND={pcsx2} -nogui", output)
            self.assertIn(str(rom), output)
            self.assertIn(f"Bios = {paths.isolated_bios / 'ps2'}", generated)
            self.assertTrue((paths.isolated_bios / "ps2" / bios_image.name).is_symlink())
            self.assertEqual(
                (paths.isolated_bios / "ps2" / bios_image.name).resolve(),
                bios_image.resolve(),
            )
            self.assertIn(f"Snapshots = {paths.screenshots}", generated)
            self.assertIn(f"Savestates = {paths.saves / 'ps2/pcsx2/sstates'}", generated)
            self.assertIn(f"MemoryCards = {paths.saves / 'ps2/pcsx2/memcards'}", generated)
            self.assertIn(f"Logs = {paths.logs / 'pcsx2'}", generated)
            self.assertIn(f"Cache = {paths.cache / 'ps2'}", generated)
            self.assertIn(f"Patches = {config_dir / 'patches'}", generated)
            self.assertIn(f"UserResources = {config_dir / 'resources'}", generated)
            self.assertIn("Backend = Cubeb", generated)
            self.assertIn("ShutdownVM = SDL-0/Back & SDL-0/Start", generated)
            self.assertIn("Cross = SDL-0/FaceSouth", generated)
            self.assertIn(f"CustomDocumentsFolder={config_dir}", registry)
            self.assertIn(f"Install_Dir={resources.parent}", registry)
            self.assertNotIn("/userdata", generated + registry + output)
            self.assertNotIn(str(root / "home/.config/PCSX2"), generated + registry)
            self.assertNotIn("mangohud", output.lower())
            self.assertNotIn("batocera-resolution", output)
            self.assertNotIn("nvidia", output.lower())
            self.assertFalse((bios / "patches.zip").exists())
            self.assertFalse((root / "home/.config/PCSX2").exists())
            self.assertEqual(
                input_hashes,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (rom, bios_image, resources / "patches.zip")
                },
            )

    def test_xemu_generator_writes_only_isolated_desktop_configuration(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.launcher.is_file())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            xemu = fake_bin / "xemu"
            xemu.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            xemu.chmod(0o755)
            rom = root / "Test Game.iso"
            rom.write_bytes(b"read-only iso")

            static = root / "static"
            shaders = static / "shaders/configs"
            decorations = static / "decorations"
            shaders.mkdir(parents=True)
            decorations.mkdir(parents=True)
            (shaders / "rendering-defaults.yml").write_text("default: {}\n", encoding="utf-8")

            sources = root / "sources"
            sources.mkdir()
            source_paths = {
                "FLASHROM": sources / "Complex_4627.bin",
                "BOOTROM": sources / "mcpx_1.0.bin",
                "HDD": sources / "xbox_hdd.qcow2",
            }
            for label, path in source_paths.items():
                path.write_bytes(label.encode("ascii"))
            source_hashes = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in source_paths.values()
            }

            environment = dict(os.environ)
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}:{environment.get('PATH', '')}",
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "isolated/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "isolated/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                    "EMBERCADE_SHADER_RESOURCES": str(static / "shaders"),
                    "EMBERCADE_DECORATION_RESOURCES": str(decorations),
                    **{
                        f"EMBERCADE_XEMU_{label}_SOURCE": str(path)
                        for label, path in source_paths.items()
                    },
                }
            )
            paths = EmbercadePaths.from_environment(environment)
            prepare_launch_layout(paths, project)
            prepared = prepare_xemu_files(paths, environment)
            self.assertFalse(prepared.eeprom.exists())
            controller = ControllerDevice(
                index=0,
                guid="030081b85e0400008e02000010010000",
                name="Xbox 360 Controller",
                device_path=Path("/dev/input/event23"),
                buttons=11,
                hats=1,
                axes=6,
                mapping="test mapping",
                real_name="Microsoft X-Box 360 pad",
                usb_vendor="045e",
                usb_product="028e",
                kernel_driver="xpad",
            )
            plan = create_launch_plan(
                system="xbox",
                rom=rom,
                paths=paths,
                runtime=runtime,
                config={},
                environment=environment,
                dry_run=True,
                controller=controller,
            )
            completed = subprocess.run(
                plan.command,
                check=False,
                capture_output=True,
                env=dict(plan.environment),
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = completed.stdout + completed.stderr
            config = paths.emulator_configs / "xemu/xemu.toml"
            generated = config.read_text(encoding="utf-8")

            self.assertIn(f"EMBERCADE_FINAL_COMMAND={xemu} -config_path", output)
            self.assertIn(f'flashrom_path = "{prepared.flashrom}"', generated)
            self.assertIn(f'bootrom_path = "{prepared.bootrom}"', generated)
            self.assertIn(f'eeprom_path = "{prepared.eeprom}"', generated)
            self.assertFalse(prepared.eeprom.exists())  # generator never fabricates state
            self.assertIn(f'hdd_path = "{prepared.hdd}"', generated)
            self.assertIn(f'dvd_path = "{rom}"', generated)
            self.assertIn(f'screenshot_dir = "{paths.screenshots}"', generated)
            self.assertIn(f'port1 = "{controller.guid}"', generated)
            self.assertNotIn("/userdata", generated)
            self.assertNotIn("/usr/share/xemu", generated)
            self.assertNotIn(str(Path.home() / ".local/share/xemu"), generated)
            self.assertNotIn("mangohud", output.lower())
            self.assertNotIn("batocera-resolution", output)
            self.assertNotIn("batocera-bezel-overlay", output)
            self.assertEqual(
                source_hashes,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in source_paths.values()
                },
            )

    def test_configgen_writes_overlay_for_read_only_system_bezel(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.python.is_file())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            decorations = root / "static/decorations"
            png = decorations / "consoles/systems/nes.png"
            info = png.with_suffix(".info")
            png.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 9), (0, 0, 0, 0)).save(png, format="PNG")
            info.write_text(
                json.dumps(
                    {
                        "width": 1920,
                        "height": 1080,
                        "top": 24,
                        "left": 273,
                        "bottom": 24,
                        "right": 273,
                        "opacity": 1.0,
                        "messagex": 0.22,
                        "messagey": 0.12,
                    }
                ),
                encoding="utf-8",
            )
            before = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (png, info)
            }

            script = r'''
import json
import os
from pathlib import Path
import sys

root = Path(sys.argv[1])
os.environ["EMBERCADE_CONFIGS"] = str(root / "writable/configs")
os.environ["EMBERCADE_USERDATA"] = str(root / "writable/data")
os.environ["EMBERCADE_SYSTEM_DECORATIONS"] = str(root / "static/decorations")
(root / "writable/configs/retroarch").mkdir(parents=True)

from configgen.generators.libretro.libretroConfig import writeBezelConfig
from configgen.generators.libretro.libretroPaths import RETROARCH_OVERLAY_CONFIG

class Config(dict):
    def get_bool(self, key, default=False):
        return bool(self.get(key, default))

class System:
    name = "nes"
    config = Config()
    es_game_info = {}

retroarch = {"aspect_ratio_index": "22"}
writeBezelConfig(
    object(),
    "consoles",
    False,
    retroarch,
    root / "game.nes",
    {"width": 2560, "height": 1440},
    System(),
    None,
    None,
)
serializable = {
    key: str(value) if isinstance(value, Path) else value
    for key, value in retroarch.items()
}
print(json.dumps({
    "config": serializable,
    "overlay_path": str(RETROARCH_OVERLAY_CONFIG),
    "overlay": RETROARCH_OVERLAY_CONFIG.read_text(encoding="utf-8"),
}))
'''
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            completed = subprocess.run(
                [str(runtime.python), "-I", "-c", script, str(root)],
                check=False,
                capture_output=True,
                env=environment,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)

            self.assertEqual(result["config"]["input_overlay_enable"], "true")
            self.assertEqual(
                result["config"]["input_overlay"],
                f'"{result["overlay_path"]}"',
            )
            self.assertEqual(result["config"]["input_overlay_opacity"], 1.0)
            self.assertEqual(result["config"]["custom_viewport_x"], 364)
            self.assertEqual(result["config"]["custom_viewport_y"], 32)
            self.assertEqual(result["config"]["custom_viewport_width"], 1832)
            self.assertEqual(result["config"]["custom_viewport_height"], 1376)
            self.assertTrue(result["overlay_path"].startswith(str(root / "writable")))
            self.assertIn(
                str(root / "writable/configs/retroarch/overlays/nes_adapted.png"),
                result["overlay"],
            )
            self.assertNotIn("/userdata", result["overlay"])
            self.assertEqual(
                before,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (png, info)
                },
            )


class C64MediaOptionsTests(unittest.TestCase):
    def _runtime_check(self, code):
        project = Path(__file__).resolve().parents[1]
        environment = {k: v for k, v in os.environ.items() if not k.startswith('EMBERCADE_')}
        result = subprocess.run([str(ProjectRuntime(project).python), '-B', '-I', '-c', code],
                                env=environment, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_stock_rom_default_is_limited_to_c64_desktop(self):
        self._runtime_check(r"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from configgen.config import SystemConfig
from configgen.generators.libretro.libretroOptions import generateCoreSettings

def generate(flag, core='vice_x64'):
    values = {}
    system = SimpleNamespace(name='c64' if core == 'vice_x64' else 'c128',
                             config=SystemConfig({'core': core}, 'c64' if core == 'vice_x64' else 'c128'))
    settings = SimpleNamespace(save=lambda key, value: values.__setitem__(key, value))
    with patch.dict('os.environ', {'EMBERCADE_DESKTOP': flag}):
        generateCoreSettings(settings, system, Path('/nonexistent/Game with spaces.D64'), [], {})
    return values
stock = generate('1')
appliance = generate('0')
assert stock['vice_jiffydos'] == '"disabled"'
assert appliance['vice_jiffydos'] == '"enabled"'
assert generate('')['vice_jiffydos'] == '"enabled"'
assert generate('1', 'vice_x128')['vice_jiffydos'] == '"enabled"'
assert {k:v for k,v in stock.items() if k != 'vice_jiffydos'} == {k:v for k,v in appliance.items() if k != 'vice_jiffydos'}
""")

    def test_explicit_jiffydos_choices_and_final_core_override_keep_priority(self):
        self._runtime_check(r"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from configgen.config import SystemConfig
from configgen.generators.libretro.libretroOptions import generateCoreSettings
for data, expected in (({'vice_jiffydos':'enabled'},'enabled'),
                       ({'vice_jiffydos':'disabled'},'disabled'),
                       ({'retroarchcore.vice_jiffydos':'enabled'},'enabled'),
                       ({'vice_jiffydos':'enabled','retroarchcore.vice_jiffydos':'disabled'},'disabled'),
                       ({'vice_jiffydos':'disabled','retroarchcore.vice_jiffydos':'enabled'},'enabled')):
    values = {}
    settings = SimpleNamespace(save=lambda key, value: values.__setitem__(key, value))
    system = SimpleNamespace(name='c64', config=SystemConfig({'core':'vice_x64', **data}, 'c64'))
    with patch.dict('os.environ', {'EMBERCADE_DESKTOP':'1'}):
        generateCoreSettings(settings, system, Path('/nonexistent/Game.D64'), [], {})
    assert values['vice_jiffydos'] == '"'+expected+'"', (data,values)
""")

    def test_disk_cartridge_tape_and_playlist_keep_native_media_arguments(self):
        project = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root/'host bin/retroarch'
            binary.parent.mkdir();binary.write_text('#!/bin/sh\nexit 99\n');binary.chmod(0o755)
            core = root/'host cores/vice_x64_libretro.so'
            core.parent.mkdir();core.write_bytes(b'\x7fELFfixture; dry run only')
            bios = root/'empty BIOS';bios.mkdir()
            environment = {k:v for k,v in os.environ.items() if not k.startswith('EMBERCADE_')}
            environment.update(HOME=str(root/'home'), PATH=f'{binary.parent}:{os.environ.get("PATH", "")}',
                EMBERCADE_CONFIG_HOME=str(root/'config'), EMBERCADE_DATA_HOME=str(root/'data'),
                EMBERCADE_CACHE_HOME=str(root/'cache'), EMBERCADE_STATE_HOME=str(root/'state'),
                EMBERCADE_RUNTIME_HOME=str(root/'runtime'),
                EMBERCADE_DISPLAY_WIDTH='1280', EMBERCADE_DISPLAY_HEIGHT='720')
            config = {'paths':{'bios':str(bios)}, 'libretro':{'cores':str(core.parent)}}
            paths = EmbercadePaths.from_environment(environment, config=config)
            prepare_launch_layout(paths, project)
            options = paths.emulator_configs/'retroarch/cores/retroarch-core-options.cfg'
            # Existing generated state must not retain the old forced default.
            options.write_text('vice_jiffydos = "enabled"\n')
            for suffix in ('.D64', '.d81', '.crt', '.t64', '.tap', '.prg', '.m3u', '.zip'):
                with self.subTest(suffix=suffix):
                    rom = root/('Game with spaces, punctuation'+suffix)
                    rom.write_bytes(b'synthetic; config-generating dry run only')
                    before = rom.read_bytes(),rom.stat().st_mtime_ns
                    plan = create_launch_plan(system='c64', rom=rom, paths=paths,
                        runtime=ProjectRuntime(project), config=config, environment=environment,
                        dry_run=True, batocera_choice=BatoceraSystemChoice('c64','libretro','vice_x64',False,False))
                    plan = with_graphics_probe(plan)
                    completed = subprocess.run(plan.command, env=dict(plan.environment),
                                               capture_output=True, text=True, timeout=30)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    command = next(line.partition('=')[2] for line in completed.stdout.splitlines()
                                   if line.startswith('EMBERCADE_FINAL_COMMAND='))
                    args = shlex.split(command)
                    self.assertEqual(args[:3], [str(binary), '-L', str(core)])
                    self.assertEqual(args[-1], str(rom))
                    self.assertEqual(args.count(str(rom)), 1)
                    self.assertIn('vice_jiffydos = "disabled"', options.read_text())
                    self.assertEqual((rom.read_bytes(),rom.stat().st_mtime_ns), before)


if __name__ == "__main__":
    unittest.main()

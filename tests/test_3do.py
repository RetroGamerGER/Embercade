from hashlib import md5
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import xml.etree.ElementTree as ET

from embercade.batocera_config import BatoceraSystemChoice
from embercade.bios_inventory import BATOCERA_COMMIT, OPERA_BIOS_HASHES, inspect_opera_bios
from embercade.compatibility import build_compatibility_matrix
from embercade.controller import ControllerDevice, write_es_input_override, write_es_input_overrides
from embercade.cores import CORE_FAMILIES, CoreResolutionError, LibretroCoreResolver
from embercade.doctor import report
from embercade.launcher import (
    SIMPLE_LIBRETRO_SYSTEMS, LaunchError, create_launch_plan, prepare_launch_layout,
)
from embercade.libretro_dry_run import (
    LibretroDryRunError, execute_dry_run, expected_system_directory, required_system_resources,
    snapshot_metadata,
)
from embercade.paths import EmbercadePaths
from embercade.rom_inventory import load_batocera_systems
from embercade.runtime import ProjectRuntime
from embercade.ui_data import REGISTRY_PATHS, customize_production_systems
from embercade.shaders import load_catalog
from graphics_helpers import with_graphics_probe
from visual_helpers import shader_provider_fixture
import shlex
import subprocess


class ThreeDOTests(unittest.TestCase):
    def test_removed_host_package_keeps_saved_choice_and_starts_without_effect(self):
        from embercade.shaders import prepare_host_template
        (self.bios / "panafz1.bin").write_bytes(b"test firmware")
        fixture, paths = self._plan()
        project = Path(__file__).resolve().parents[1]
        prepare_launch_layout(paths, project)
        template = self.root / "app host shader mappings"
        prepare_host_template(template, project / "resources/shaders/catalog.toml")
        text = '3do.shaderset=newpixie\n3do.gfxbackend=vulkan\n'
        paths.batocera_conf.write_text(text)
        env = {k: v for k, v in fixture.environment.items() if k != "XDG_RUNTIME_DIR"}
        env.update(EMBERCADE_SHADER_RESOURCES=str(template),
                   EMBERCADE_HOST_SLANG_ROOT=str(self.root / "removed package"))
        plan = create_launch_plan(system="3do", rom=fixture.rom, paths=paths,
            runtime=ProjectRuntime(project), config={"libretro": {"cores": str(fixture.core.parent)}},
            environment=env, controller=fixture.controller, dry_run=True,
            batocera_choice=BatoceraSystemChoice("3do", "libretro", "opera", False, False))
        plan = with_graphics_probe(plan, True)
        run = subprocess.run(plan.command, env=dict(plan.environment), capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        command = next(l.partition("=")[2] for l in run.stdout.splitlines() if l.startswith("EMBERCADE_FINAL_COMMAND="))
        self.assertNotIn("--set-shader", shlex.split(command))
        self.assertEqual((paths.logs / "launch-notice.txt").read_text().strip(), "shader-unavailable")
        self.assertEqual(paths.batocera_conf.read_text(), text)

    def test_missing_selected_shader_is_reported_without_cancelling_game(self):
        (self.bios / "panafz1.bin").write_bytes(b"test firmware")
        fixture, paths = self._plan()
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        prepare_launch_layout(paths, project)
        shader_root = self.root / "incomplete shader resources"
        (shader_root / "configs/newpixie").mkdir(parents=True)
        (shader_root / "configs/rendering-defaults.yml").write_text("default:\n  shader:\n")
        (shader_root / "configs/newpixie/rendering-defaults.yml").write_text("default:\n  shader: embercade/missing-preset\n")
        text = "3do.shaderset=newpixie\n3do.gfxbackend=vulkan\n3do.retroarch.video_shader_enable=true\n"
        paths.batocera_conf.write_text(text)
        environment = {k: v for k, v in fixture.environment.items() if k != "XDG_RUNTIME_DIR"}
        environment["EMBERCADE_SHADER_RESOURCES"] = str(shader_root)
        plan = create_launch_plan(
            system="3do", rom=fixture.rom, paths=paths, runtime=runtime,
            config={"libretro": {"cores": str(fixture.core.parent)}}, environment=environment,
            controller=fixture.controller, dry_run=True,
            batocera_choice=BatoceraSystemChoice("3do", "libretro", "opera", False, False),
        )
        plan = with_graphics_probe(plan, True)
        result = subprocess.run(plan.command, env=dict(plan.environment), capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        command = next(line.removeprefix("EMBERCADE_FINAL_COMMAND=") for line in result.stdout.splitlines() if line.startswith("EMBERCADE_FINAL_COMMAND="))
        args = shlex.split(command)
        self.assertNotIn("--set-shader", args)
        self.assertEqual((paths.logs / "launch-notice.txt").read_text().strip(), "shader-unavailable")
        appended = Path(args[args.index("--appendconfig") + 1].split("|")[-1])
        self.assertEqual(appended.read_text(), 'video_shader_enable = "false"\n')
        self.assertEqual(paths.batocera_conf.read_text(), text)

    def test_all_host_shader_mappings_use_automatic_vulkan_with_opera(self):
        (self.bios / "panafz1.bin").write_bytes(b"test firmware")
        fixture, paths = self._plan()
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        prepare_launch_layout(paths, project)
        for shader in load_catalog(project / "resources/shaders/catalog.toml"):
            with self.subTest(shader=shader.identifier):
                text = f"3do.bezel=consoles\n3do.shaderset={shader.identifier}\n"
                paths.batocera_conf.write_text(text)
                plan = create_launch_plan(
                    system="3do", rom=fixture.rom, paths=paths, runtime=runtime,
                    config={"libretro": {"cores": str(fixture.core.parent)}},
                    environment={k: v for k, v in fixture.environment.items() if k != "XDG_RUNTIME_DIR"}, controller=fixture.controller, dry_run=True,
                    batocera_choice=BatoceraSystemChoice("3do", "libretro", "opera", False, False),
                )
                plan = with_graphics_probe(plan, True)
                completed = subprocess.run(plan.command, env=dict(plan.environment),
                                           capture_output=True, text=True, timeout=60)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                command = next(line.removeprefix("EMBERCADE_FINAL_COMMAND=")
                               for line in completed.stdout.splitlines()
                               if line.startswith("EMBERCADE_FINAL_COMMAND="))
                args = shlex.split(command)
                self.assertEqual(args[0], str(fixture.executable))
                selected = Path(args[args.index("--set-shader") + 1])
                self.assertEqual(selected.name, shader.alias_name + ".slangp")
                self.assertTrue(selected.is_file())
                generated = (paths.emulator_configs / "retroarch/retroarchcustom.cfg").read_text()
                self.assertIn('video_driver = "vulkan"', generated)
                self.assertIn('input_enable_hotkey_btn = 4', generated)
                self.assertEqual(paths.batocera_conf.read_text(), text)

    def test_manual_gl_shader_conflict_starts_without_effect(self):
        (self.bios / "panafz1.bin").write_bytes(b"test firmware")
        fixture, paths = self._plan()
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        prepare_launch_layout(paths, project)
        before = (snapshot_metadata(self.bios), snapshot_metadata(fixture.rom.parent))
        cases = (("gl", True, "shader-incompatible"), ("glcore", False, None), (None, False, None))
        for backend, available, notice in cases:
            with self.subTest(backend=backend, vulkan=available):
                text = "3do.shaderset=newpixie\n" + (f"3do.gfxbackend={backend}\n" if backend else "")
                paths.batocera_conf.write_text(text)
                warning = paths.logs / "launch-notice.txt"
                warning.unlink(missing_ok=True)
                plan = create_launch_plan(
                    system="3do", rom=fixture.rom, paths=paths, runtime=runtime,
                    config={"libretro": {"cores": str(fixture.core.parent)}},
                    environment={k: v for k, v in fixture.environment.items() if k != "XDG_RUNTIME_DIR"}, controller=fixture.controller, dry_run=True,
                    batocera_choice=BatoceraSystemChoice("3do", "libretro", "opera", False, False),
                )
                plan = with_graphics_probe(plan, available)
                completed = subprocess.run(plan.command, env=dict(plan.environment), capture_output=True, text=True, timeout=60)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                command = next(line.removeprefix("EMBERCADE_FINAL_COMMAND=") for line in completed.stdout.splitlines() if line.startswith("EMBERCADE_FINAL_COMMAND="))
                args = shlex.split(command)
                if notice:
                    self.assertNotIn("--set-shader", args)
                    self.assertEqual(warning.read_text().strip(), notice)
                    append = args[args.index("--appendconfig") + 1].split("|")
                    self.assertEqual(Path(append[-1]).read_text(), 'video_shader_enable = "false"\n')
                else:
                    self.assertIn("--set-shader", args)
                    self.assertFalse(warning.exists())
                self.assertEqual(paths.batocera_conf.read_text(), text)
        self.assertEqual(before, (snapshot_metadata(self.bios), snapshot_metadata(fixture.rom.parent)))

    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.shader_provider = shader_provider_fixture(self.root)
        self.bios = self.root / "external BIOS files"
        self.bios.mkdir()
        # Synthetic test firmware, never distribute or require real BIOS data.
        self.hashes = {"panafz1.bin": md5(b"test firmware").hexdigest(),
                       "goldstar.bin": md5(b"alternative firmware").hexdigest()}
        self.patch = patch("embercade.bios_inventory.OPERA_BIOS_HASHES", self.hashes)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_one_verified_bios_is_sufficient_and_external_files_are_read_only(self) -> None:
        file = self.bios / "goldstar.bin"
        file.write_bytes(b"alternative firmware")
        file.chmod(0o444)
        before = (snapshot_metadata(self.bios), file.read_bytes())
        status = inspect_opera_bios(self.bios)
        self.assertTrue(status.available)
        self.assertEqual(status.files, (file,))
        self.assertEqual(before, (snapshot_metadata(self.bios), file.read_bytes()))
        self.assertFalse((self.bios / "panafz1.bin").exists())

    def test_missing_bios_is_not_ready_and_lists_upstream_alternatives(self) -> None:
        status = inspect_opera_bios(self.bios)
        self.assertEqual(status.status, "MISSING")
        self.assertFalse(status.available)
        self.assertIn("panafz1.bin", status.detail)
        self.assertIn("goldstar.bin", status.detail)

    def test_wrong_location_is_reported_without_moving_bios(self) -> None:
        folder = self.bios / "3do"
        folder.mkdir()
        file = folder / "panafz1.bin"
        file.write_bytes(b"test firmware")
        status = inspect_opera_bios(self.bios)
        self.assertFalse(status.available)
        self.assertIn("WRONG_LOCATION", status.detail)
        self.assertIn("3do/panafz1.bin", status.detail)
        self.assertTrue(file.is_file())
        self.assertFalse((self.bios / "panafz1.bin").exists())

    def test_wrong_case_and_wrong_hash_are_not_silently_accepted(self) -> None:
        (self.bios / "PANAFZ1.BIN").write_bytes(b"test firmware")
        (self.bios / "goldstar.bin").write_bytes(b"wrong bytes")
        status = inspect_opera_bios(self.bios)
        self.assertFalse(status.available)
        self.assertIn("CASE_MISMATCH", status.detail)
        self.assertIn("HASH_MISMATCH", status.detail)

    def test_unavailable_bios_folder_is_not_created(self) -> None:
        missing = self.bios / "not configured"
        self.assertEqual(inspect_opera_bios(missing).status, "PATH_UNAVAILABLE")
        self.assertFalse(missing.exists())

    def test_bios_contract_has_exact_pinned_names_and_no_font_requirement(self) -> None:
        self.assertEqual(len(OPERA_BIOS_HASHES), 10)
        self.assertEqual(OPERA_BIOS_HASHES["panafz10.bin"], "51f2f43ae2f3508a14d9f56597e2d3ce")
        self.assertTrue(all(len(digest) == 32 for digest in OPERA_BIOS_HASHES.values()))
        self.assertNotIn("panafz1-kanji.bin", OPERA_BIOS_HASHES)

    def test_existing_catalog_keeps_cue_visible_but_not_companion_bin(self) -> None:
        catalogue = self.root / "es_systems.cfg"
        catalogue.write_text(
            '<systemList><system><name>3do</name><fullname>3DO</fullname>'
            '<path>/userdata/roms/3do</path><extension>.iso .chd .cue</extension>'
            '<command>upstream</command><emulators><emulator name="libretro">'
            '<cores><core default="true">opera</core></cores></emulator></emulators>'
            '</system><system><name>unsupported</name></system></systemList>'
        )
        customize_production_systems(catalogue, systems=SIMPLE_LIBRETRO_SYSTEMS)
        system = load_batocera_systems(catalogue)[0]
        self.assertEqual(system.system, "3do")
        self.assertEqual(set(system.extensions), {".cue", ".chd", ".iso"})
        roms = self.root / "ROM root/3do"
        roms.mkdir(parents=True)
        (roms / "Game with spaces.cue").write_text('FILE "Game with spaces.bin" BINARY\n')
        (roms / "Game with spaces.bin").write_bytes(b"track")
        self.assertEqual([file.name for file in roms.iterdir() if file.suffix in system.extensions],
                         ["Game with spaces.cue"])
        node = ET.parse(catalogue).getroot().find("system")
        self.assertEqual(node.findtext("command"),
                         '"/app/bin/embercade" launch --system 3do --rom %ROM%')
        self.assertEqual(node.findtext("./emulators/emulator/cores/core"), "opera")
        self.assertTrue(any(path.endswith("opera.libretro.core.yml") for path in REGISTRY_PATHS))

    def test_opera_uses_existing_managed_core_resolver(self) -> None:
        core = self.root / "data/embercade/cores/opera_libretro.so"
        core.parent.mkdir(parents=True)
        core.write_bytes(b"\x7fELFtest core")
        resolver = LibretroCoreResolver.from_host(
            {}, {"HOME": str(self.root), "XDG_DATA_HOME": str(self.root / "data")},
            user_config=self.root / "missing.cfg", system_config=self.root / "absent.cfg",
            fallback_core_directories=(), fallback_info_directories=(),
        )
        self.assertEqual(CORE_FAMILIES["3DO"], ("opera",))
        self.assertEqual(resolver.resolve("opera").path, core)
        self.assertEqual(resolver.resolve("opera").source, "embercade-managed")
        core.unlink()
        with self.assertRaisesRegex(CoreResolutionError, "opera"):
            resolver.resolve("opera")

    def test_ready_requires_confirmed_e2e_not_just_installed_prerequisites(self) -> None:
        binary = self.root / "bin/retroarch"
        binary.parent.mkdir()
        binary.write_text("#!/bin/sh\nexit 99\n")
        binary.chmod(0o755)
        roms = {"batocera_commit": BATOCERA_COMMIT, "systems": [{
            "system": "3do", "fullname": "3DO", "directory": "3do", "match": "EXACT",
            "content_status": "ROM_PRESENT", "default_emulator": "libretro", "default_core": "opera",
        }]}
        bios = {"batocera_commit": BATOCERA_COMMIT, "systems": [{
            "system": "3do", "requirements_total": 1, "required_matched": 1,
        }]}
        cores = {"batocera_commit": BATOCERA_COMMIT, "batocera_cores": [{
            "batocera_name": "opera", "path": str(self.root / "opera_libretro.so"),
            "probably_loadable": True,
        }]}
        environment = {"PATH": str(binary.parent)}
        prerequisites = build_compatibility_matrix(roms, bios, cores, environment=environment,
                                                   e2e_systems=frozenset())
        self.assertEqual(prerequisites["systems"][0]["result_status"], "EMBERCADE_PORT_MISSING")
        dry_runs = {
            "batocera_commit": BATOCERA_COMMIT,
            "host_retroarch_profile_unchanged": True,
            "summary": {"systems": 1, "successful": 1},
            "systems": [{"system": "3do", "emulator": "libretro", "core": "opera",
                         "core_path": cores["batocera_cores"][0]["path"],
                         "retroarch_config": str(self.root / "isolated/retroarchcustom.cfg"),
                         "controller_arguments_complete": True, "launcher_exit_code": 0}],
        }
        untested = build_compatibility_matrix(roms, bios, cores, environment=environment,
                                             libretro_dry_runs=dry_runs, e2e_systems=frozenset())
        self.assertEqual(untested["systems"][0]["result_status"], "UNTESTED")
        confirmed = build_compatibility_matrix(roms, bios, cores, environment=environment)
        self.assertEqual(confirmed["systems"][0]["result_status"], "READY")

    def _plan(self, hotkey: str = "guide-start"):
        project = self.root / "project"
        resources = project / ".work/ui/share/batocera"
        (resources / "shaders/configs").mkdir(parents=True, exist_ok=True)
        (resources / "shaders/configs/rendering-defaults.yml").write_text("default: {}\n")
        (resources / "datainit/decorations").mkdir(parents=True, exist_ok=True)
        runtime = ProjectRuntime(project)
        runtime.launcher.parent.mkdir(parents=True, exist_ok=True)
        runtime.launcher.write_text("#!/bin/sh\n")
        runtime.launcher.chmod(0o755)
        executable = self.root / "bin/retroarch"
        executable.parent.mkdir(exist_ok=True)
        executable.write_text("#!/bin/sh\n")
        executable.chmod(0o755)
        cores = self.root / "core sources"
        cores.mkdir(exist_ok=True)
        (cores / "opera_libretro.so").write_bytes(b"\x7fELFtest core")
        rom = self.root / "external ROMs/3do/Test Game (USA).cue"
        rom.parent.mkdir(parents=True, exist_ok=True)
        track = rom.with_suffix(".bin")
        if not rom.exists():
            rom.write_text('FILE "Test Game (USA).bin" BINARY\n')
            track.write_bytes(b"test track")
            rom.chmod(0o444)
            track.chmod(0o444)
        env = {"HOME": str(self.root), "PATH": str(executable.parent),
               "EMBERCADE_HOST_SLANG_ROOT": str(self.shader_provider),
               "EMBERCADE_DISPLAY_WIDTH": "1920", "EMBERCADE_DISPLAY_HEIGHT": "1080"}
        config = {"paths": {"bios": str(self.bios), "roms": str(rom.parent.parent)},
                  "libretro": {"cores": str(cores)}, "controller": {"exit_hotkey": hotkey}}
        paths = EmbercadePaths.from_environment(env, config=config)
        controller = ControllerDevice(0, "030081b85e0400008e02000010010000",
                                      "Xbox 360 Controller", Path("/dev/input/event23"),
                                      11, 1, 6, "test SDL mapping", real_name="Microsoft X-Box 360 pad")
        before = snapshot_metadata(rom.parent)
        plan = create_launch_plan(
            system="3do", rom=rom, paths=paths, runtime=runtime, config=config,
            environment=env, controller=controller, dry_run=True,
            batocera_choice=BatoceraSystemChoice("3do", "libretro", "opera", False, False),
        )
        self.assertEqual(before, snapshot_metadata(rom.parent))
        return plan, paths

    def test_generic_plan_preserves_cue_path_spaces_controller_and_exit_choice(self) -> None:
        (self.bios / "panafz1.bin").write_bytes(b"test firmware")
        for hotkey in ("guide-start", "back-start"):
            with self.subTest(hotkey=hotkey):
                plan, paths = self._plan(hotkey)
                self.assertEqual(plan.command[1:9],
                                 ("-system", "3do", "-rom", str(plan.rom),
                                  "-emulator", "libretro", "-core", "opera"))
                self.assertEqual(plan.command.count(str(plan.rom)), 1)
                self.assertIn("-p1devicepath", plan.command)
                self.assertEqual(plan.environment["EMBERCADE_EXIT_HOTKEY"], hotkey)
                self.assertEqual(plan.environment["EMBERCADE_BIOS"], str(self.bios))
                self.assertEqual(plan.environment["EMBERCADE_LIBRETRO_CORE"], str(plan.core))
                self.assertEqual(expected_system_directory("3do", paths), self.bios)
                self.assertEqual(required_system_resources("3do", paths),
                                 (self.bios / "panafz1.bin",))
                self.assertFalse(any(value.startswith("/userdata") for value in plan.environment.values()))

    def test_missing_bios_prevents_launch_and_dry_run_before_emulator_execution(self) -> None:
        with self.assertRaisesRegex(LaunchError, "3DO BIOS MISSING"):
            self._plan()
        paths = EmbercadePaths.from_environment({"HOME": str(self.root)},
                                              config={"paths": {"bios": str(self.bios)}})
        with self.assertRaisesRegex(LibretroDryRunError, "3DO BIOS MISSING"):
            required_system_resources("3do", paths)

    def test_pinned_configgen_generates_opera_options_overlay_shader_and_native_exit(self) -> None:
        (self.bios / "panafz1.bin").write_bytes(b"test firmware")
        fixture, paths = self._plan()
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        prepare_launch_layout(paths, project)
        paths.batocera_conf.write_text(
            "3do.bezel=consoles\n3do.shaderset=crt-easymode\n3do.gfxbackend=vulkan\n"
        )
        second = ControllerDevice(
            1, "050018dc5e040000130b000017050000", "Xbox Series X Controller",
            Path("/dev/input/event27"), fixture.controller.buttons,
            fixture.controller.hats, fixture.controller.axes,
            "050018dc5e040000130b000017050000,Xbox Wireless Controller,"
            "a:b0,b:b1,x:b3,y:b4,guide:b12,start:b11,"
            "dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,platform:Linux,",
            real_name="Xbox Wireless Controller",
        )
        write_es_input_overrides((fixture.controller, second),
                                 runtime.share / "emulationstation/es_input.cfg",
                                 paths.emulationstation_config / "es_input.cfg")
        plan = create_launch_plan(
            system="3do", rom=fixture.rom, paths=paths, runtime=runtime,
            config={"libretro": {"cores": str(fixture.core.parent)},
                    "controller": {"exit_hotkey": "guide-start"}},
            environment={key: value for key, value in fixture.environment.items()
                         if key != "XDG_RUNTIME_DIR"},
            controllers=(fixture.controller, second), dry_run=True,
            batocera_choice=BatoceraSystemChoice("3do", "libretro", "opera", False, False),
        )
        before = (snapshot_metadata(self.bios), snapshot_metadata(fixture.rom.parent))
        result = execute_dry_run(plan, paths)
        self.assertEqual(result["core"], "opera")
        self.assertEqual(result["rom"], str(fixture.rom))
        self.assertTrue(result["overlay_enabled"])
        self.assertTrue(Path(result["shader"]).is_file())
        generated = (paths.emulator_configs / "retroarch/retroarchcustom.cfg").read_text()
        options = (paths.emulator_configs / "retroarch/cores/retroarch-core-options.cfg").read_text()
        self.assertIn('opera_active_devices = "1"', options)
        self.assertIn('opera_nvram_storage = "per game"', options)
        self.assertIn('opera_dsp_threaded = "enabled"', options)
        self.assertIn('input_exit_emulator_btn = 6', generated)
        self.assertIn('input_enable_hotkey_btn = 5', generated)
        self.assertIn('input_player1_joypad_index = 0', generated)
        self.assertIn('input_player2_joypad_index = 1', generated)
        self.assertIn('input_player1_device_reservation_type = 2', generated)
        self.assertIn('input_player1_reserved_device = "045e:028e"', generated)
        self.assertIn('input_player2_device_reservation_type = 2', generated)
        self.assertIn('input_player2_reserved_device = "045e:0b13"', generated)
        for player in (1, 2):
            self.assertIn(f'input_player{player}_up_btn = 11', generated)
            self.assertIn(f'input_player{player}_down_btn = 12', generated)
            self.assertIn(f'input_player{player}_left_btn = 13', generated)
            self.assertIn(f'input_player{player}_right_btn = 14', generated)
            self.assertIn(f'input_player{player}_a_btn = 1', generated)
            self.assertIn(f'input_player{player}_b_btn = 0', generated)
            self.assertNotIn(f'input_player{player}_up_btn = h0up', generated)
        self.assertIn('input_joypad_driver = sdl2', generated)
        self.assertIn('input_driver = udev', generated)
        self.assertNotIn("/userdata", generated + options)
        self.assertEqual(before, (snapshot_metadata(self.bios), snapshot_metadata(fixture.rom.parent)))

    def test_identical_controller_models_are_not_reserved_ambiguously(self) -> None:
        (self.bios / "panafz1.bin").write_bytes(b"test firmware")
        fixture, paths = self._plan()
        runtime = ProjectRuntime(Path(__file__).resolve().parents[1])
        prepare_launch_layout(paths, Path(__file__).resolve().parents[1])
        second = ControllerDevice(
            1, fixture.controller.guid, fixture.controller.name,
            Path("/dev/input/event27"), fixture.controller.buttons,
            fixture.controller.hats, fixture.controller.axes, fixture.controller.mapping,
            real_name=fixture.controller.real_name,
        )
        write_es_input_overrides((fixture.controller, second),
                                 runtime.share / "emulationstation/es_input.cfg",
                                 paths.emulationstation_config / "es_input.cfg")
        plan = create_launch_plan(
            system="3do", rom=fixture.rom, paths=paths, runtime=runtime,
            config={"libretro": {"cores": str(fixture.core.parent)},
                    "controller": {"exit_hotkey": "guide-start"}},
            environment={key: value for key, value in fixture.environment.items()
                         if key != "XDG_RUNTIME_DIR"},
            controllers=(fixture.controller, second), dry_run=True,
            batocera_choice=BatoceraSystemChoice("3do", "libretro", "opera", False, False),
        )
        execute_dry_run(plan, paths)
        generated = (paths.emulator_configs / "retroarch/retroarchcustom.cfg").read_text()
        self.assertIn('input_player1_joypad_index = 0', generated)
        self.assertIn('input_player2_joypad_index = 1', generated)
        self.assertNotIn('device_reservation_type = 2', generated)
        self.assertNotIn('reserved_device = "045e:028e"', generated)

    def test_doctor_uses_same_one_of_bios_check_without_writes(self) -> None:
        (self.root / "roms/3do").mkdir(parents=True)
        file = self.bios / "goldstar.bin"
        file.write_bytes(b"alternative firmware")
        paths = EmbercadePaths.from_environment({"HOME": str(self.root)}, config={"paths": {
            "bios": str(self.bios), "roms": str(self.root / "roms")}})
        output = StringIO()
        before = snapshot_metadata(self.bios)
        resolver = type("NoEmulators", (), {"probe_all": staticmethod(lambda: {})})()
        report(paths, resolver, environment={}, stream=output)
        self.assertIn("3DO BIOS          OK", output.getvalue())
        self.assertIn("goldstar.bin", output.getvalue())
        self.assertIn("one system BIOS is sufficient", output.getvalue())
        self.assertEqual(before, snapshot_metadata(self.bios))


if __name__ == "__main__":
    unittest.main()

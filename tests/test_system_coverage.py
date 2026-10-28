from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
import json
import os
import unittest

from embercade.batocera_config import BatoceraSystemChoice, resolve_system_choice
from embercade.compatibility import E2E_VALIDATED_SYSTEMS
from embercade.controller import ControllerDevice, write_es_input_override
from embercade.cores import LibretroCoreResolver
from embercade.dolphin_dry_run import execute_dry_run as execute_dolphin_dry_run
from embercade.host_requirements import _system_has_content
from embercade.launcher import SIMPLE_LIBRETRO_SYSTEMS, create_launch_plan, prepare_launch_layout
from embercade.libretro_dry_run import execute_dry_run
from embercade.paths import EmbercadePaths
from embercade.rom_inventory import load_batocera_systems
from embercade.runtime import ProjectRuntime, load_config
from embercade.system_coverage import (classify, collect_coverage, inspect_core, STATUSES,
                                       structure_inputs_digest, BATOCERA_COMMIT)
from embercade.ui_data import customize_production_systems


PROJECT = Path(__file__).resolve().parents[1]


class CoverageTests(unittest.TestCase):
    def row(self, **changes):
        row = dict(system="new", out_of_scope=False, runtime_available=True,
                   launch_path_implemented=True, extensions=[".rom"],
                   bios_status="SATISFIED", structural_verified=True)
        return row | changes

    def test_prepared_is_never_inferred_ready(self):
        self.assertEqual(classify(self.row())[0], "PREPARED")
        self.assertEqual(classify(self.row(system="wii"), e2e=frozenset())[0], "PREPARED")
        self.assertEqual(classify(self.row(system="nes"))[0], "READY")
        self.assertEqual(classify(self.row(system="nes", effective_emulator="libretro",
                                           core_metadata_verified=False))[0], "READY")
        self.assertEqual(classify(self.row(effective_emulator="libretro",
                                           core_metadata_verified=False)),
                         ("PREPARED", "REAL_GAME_E2E_PENDING"))

    def test_optional_core_info_cannot_block_a_verified_runtime(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            core = root / "vecx_libretro.so"
            core.write_bytes(b"\x7fELFfixture; never executed")
            info = root / "vecx_libretro.info"
            resolver = LibretroCoreResolver.from_host(
                {"libretro": {"cores": str(root), "info": str(root)}},
                {"HOME": str(root)}, fallback_core_directories=(), fallback_info_directories=())
            exports = SimpleNamespace(returncode=0, stdout="\n".join(
                " FUNC GLOBAL DEFAULT 1 " + name for name in (
                    "retro_init", "retro_run", "retro_load_game",
                    "retro_get_system_info", "retro_api_version")))
            with patch("embercade.system_coverage.subprocess.run", return_value=exports), \
                 patch("embercade.system_coverage.inspect_elf_runtime",
                       return_value=SimpleNamespace(healthy=True)):
                missing = inspect_core(resolver, "vecx")
                self.assertTrue(missing["available"])
                self.assertFalse(missing["metadata_verified"])
                self.assertEqual(missing["metadata_status"], "MISSING_OPTIONAL")
                info.write_text('display_name = "Vectrex"\n')
                incomplete = inspect_core(resolver, "vecx")
                self.assertTrue(incomplete["available"])
                self.assertEqual(incomplete["metadata_status"], "INCOMPLETE_OPTIONAL")
                info.write_text('display_name = "Vectrex"\nsupported_extensions = "vec|bin"\n')
                complete = inspect_core(resolver, "vecx")
                self.assertTrue(complete["available"])
                self.assertTrue(complete["metadata_verified"])
                with patch.object(Path, "read_text", side_effect=PermissionError):
                    unreadable = inspect_core(resolver, "vecx")
                self.assertTrue(unreadable["available"])
                self.assertEqual(unreadable["metadata_status"], "UNREADABLE_OPTIONAL")
            self.assertEqual(core.read_bytes(), b"\x7fELFfixture; never executed")

    def test_missing_bios_is_an_explicit_prepared_setup_requirement(self):
        self.assertEqual(classify(self.row(bios_status="MISSING")),
                         ("PREPARED", "BIOS_SETUP_REQUIRED"))
        self.assertEqual(classify(self.row(system="nes", bios_status="MISSING"))[0], "PREPARED")

    def test_missing_core_port_and_structural_proof_remain_blocked(self):
        for changes in (dict(runtime_available=False), dict(launch_path_implemented=False),
                        dict(structural_verified=False), dict(extensions=[])):
            self.assertEqual(classify(self.row(**changes))[0], "BLOCKED")
        self.assertEqual(classify(self.row(out_of_scope=True))[0], "UNSUPPORTED")
        self.assertEqual(set(STATUSES), {"READY", "PREPARED", "BLOCKED", "UNSUPPORTED"})
        self.assertEqual(classify(self.row(resource_missing=True))[0], "BLOCKED")

    def test_file_name_and_elf_magic_are_not_sufficient_core_evidence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            core = root / "vecx_libretro.so"
            core.write_bytes(b"\x7fELFnot a shared library")
            resolver = LibretroCoreResolver.from_host({"libretro": {"cores": str(root)}},
                                                      {"HOME": str(root)},
                                                      fallback_core_directories=(),
                                                      fallback_info_directories=())
            self.assertFalse(inspect_core(resolver, "vecx")["available"])
            self.assertEqual(core.read_bytes(), b"\x7fELFnot a shared library")

    def test_discovery_ignores_companions_and_future_rom_needs_no_code_change(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "systems.cfg"
            catalog.write_text('<systemList><system><name>vectrex</name><fullname>Vectrex</fullname>'
                               '<path>/userdata/roms/vectrex</path><extension>.vec .zip</extension>'
                               '<command>old</command><emulators><emulator name="libretro">'
                               '<cores><core default="true">vecx</core></cores></emulator></emulators>'
                               '</system></systemList>')
            customize_production_systems(catalog, systems=SIMPLE_LIBRETRO_SYSTEMS)
            system = load_batocera_systems(catalog)[0]
            roms = root / "roms"
            folder = roms / "vectrex"
            folder.mkdir(parents=True)
            for filename in ("info.txt", "gamelist.xml"):
                (folder / filename).touch()
            (folder / "images").mkdir()
            (folder / "images/cover.png").touch()
            self.assertFalse(_system_has_content(roms, system))
            (folder / "Game with spaces.vec").write_bytes(b"synthetic fixture")
            self.assertTrue(_system_has_content(roms, system))
            self.assertEqual(system.default_core, "vecx")

    def test_upstream_pins_and_bios_metadata_are_packaged_not_work_dependencies(self):
        stage = (PROJECT / "src/embercade/staging.py").read_text()
        self.assertIn('"systems-catalog.xml"', stage)
        self.assertNotIn('/ "es_systems_all.cfg"', stage)
        self.assertIn('"bios-requirements.json"', stage)
        self.assertIn('"system-structure.json"', stage)
        self.assertIn('structure_inputs_digest(project_root)', stage)
        self.assertTrue(E2E_VALIDATED_SYSTEMS <= SIMPLE_LIBRETRO_SYSTEMS | {
            "gamecube", "ps2", "ps3", "ps4", "wii", "xbox", "xbox360"})
        self.assertNotIn("x68000", SIMPLE_LIBRETRO_SYSTEMS)
        self.assertNotIn("arcadia", SIMPLE_LIBRETRO_SYSTEMS)
        self.assertNotIn("arduboy", SIMPLE_LIBRETRO_SYSTEMS)

    def test_complete_matrix_without_roms_has_prepared_and_blocked_not_ready(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.cfg"
            catalog.write_text('<systemList>' + ''.join(
                f'<system><name>{name}</name><fullname>{name}</fullname>'
                f'<path>/userdata/roms/{name}</path><extension>.rom</extension>'
                '<emulators><emulator name="libretro"><cores>'
                '<core default="true">fixture</core></cores></emulator></emulators></system>'
                for name in ("vectrex", "arcadia")) + '</systemList>')
            requirements = root / "bios.json"
            requirements.write_text(json.dumps({"batocera_commit": BATOCERA_COMMIT,
                                                "requirements": []}))
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            with patch('embercade.system_coverage.inspect_core',
                       return_value={"available": True, "abi_dependencies_verified": True}), \
                 patch('embercade.system_coverage._resolve_effective_executable',
                       return_value={"present": True}):
                report = collect_coverage(catalog, requirements, paths=paths, config={},
                                          environment={"HOME": str(root)}, structural={
                                              "vectrex": {"verified": True, "core": "fixture"}})
            self.assertEqual(report["summary"], {"total": 2, "READY": 0, "PREPARED": 1,
                                                 "BLOCKED": 1, "UNSUPPORTED": 0})
            self.assertTrue(all(row["collection_status"] == "NO_ROM" for row in report["systems"]))
            prepared = next(row for row in report["systems"] if row["status"] == "PREPARED")
            self.assertTrue(prepared["launch_path_implemented"])
            self.assertTrue(prepared["extensions"])
            self.assertEqual(prepared["bios_status"], "NONE_DECLARED")


class PinnedSystemStructureTests(unittest.TestCase):
    def test_all_new_libretro_routes_generate_without_running_a_game(self):
        catalog = PROJECT / ".work/system-catalog/output/es_systems.cfg"
        runtime = ProjectRuntime(PROJECT)
        if not catalog.exists() or not runtime.python.exists():
            self.skipTest("prepared pinned catalog/runtime required for structural integration test")
        config = load_config(Path.home() / ".config/embercade/embercade.toml")
        resolver = LibretroCoreResolver.from_host(config)
        catalog_systems = load_batocera_systems(catalog)
        self.assertEqual(len(catalog_systems), len({s.system for s in catalog_systems}))
        proofs = {}
        controller = ControllerDevice(0, "030081b85e0400008e02000010010000",
                                      "Xbox 360 Controller", Path("/dev/input/fixture"),
                                      11, 1, 6, "fixture", real_name="Microsoft X-Box 360 pad")
        for system in catalog_systems:
            if system.system not in SIMPLE_LIBRETRO_SYSTEMS - E2E_VALIDATED_SYSTEMS:
                continue
            try:
                core = resolver.resolve(system.default_core)
            except Exception as error:
                proofs[system.system] = {"verified": False, "core": system.default_core,
                                         "error": type(error).__name__}
                continue
            with TemporaryDirectory(prefix="embercade-structure-", dir=PROJECT / ".work") as directory:
                root = Path(directory)
                env = {"HOME": str(root), "PATH": os.environ.get("PATH", ""),
                       "EMBERCADE_DISPLAY_WIDTH": "1920", "EMBERCADE_DISPLAY_HEIGHT": "1080"}
                from visual_helpers import shader_provider_fixture
                env["EMBERCADE_HOST_SLANG_ROOT"] = str(shader_provider_fixture(root))
                settings = {"paths": {"roms": str(root / "roms"), "bios": str(root / "read-only BIOS")},
                            "libretro": {"core_overrides": {system.default_core: str(core.path)}},
                            "controller": {"exit_hotkey": "back-start"}}
                # Resolver uses the exact verified directory, without importing cores.
                settings["libretro"] = {"cores": str(core.path.parent)}
                # Only pinned generators run. A sentinel fails if a regression
                # ever tries to execute fixture content; no host emulator needed.
                executable = root / "retroarch"
                executable.write_text("#!/bin/sh\nexit 99\n")
                executable.chmod(0o755)
                settings["executables"] = {"retroarch": str(executable)}
                paths = EmbercadePaths.from_environment(env, config=settings)
                paths.bios_root.mkdir()
                paths.bios_root.chmod(0o555)
                prepare_launch_layout(paths, PROJECT)
                rom = root / "roms" / system.path_name / ("Synthetic Game (Test)" + system.extensions[0])
                rom.parent.mkdir(parents=True)
                rom.write_bytes(b"not a real ROM; generator only")
                write_es_input_override(controller, runtime.share / "emulationstation/es_input.cfg",
                                        paths.emulationstation_config / "es_input.cfg")
                paths.batocera_conf.write_text(
                    f"global.bezel=consoles\nglobal.shaderset=crt-easymode\n"
                    f"{system.system}.gfxbackend=vulkan\n")
                try:
                    choice = resolve_system_choice(system=system.system, rom=rom, paths=paths,
                                                   runtime=runtime, environment=env)
                    self.assertEqual((choice.emulator, choice.core), ("libretro", system.default_core))
                    plan = create_launch_plan(system=system.system, rom=rom, paths=paths,
                                              runtime=runtime, config=settings, environment=env,
                                              controller=controller, dry_run=True, batocera_choice=choice)
                    result = execute_dry_run(plan, paths)
                    generated = Path(result["retroarch_config"]).read_text()
                    self.assertNotIn("/userdata", generated)
                    self.assertIn('input_enable_hotkey_btn = 4', generated)
                    self.assertIn('input_exit_emulator_btn = 6', generated)
                    self.assertTrue(Path(result["shader"]).is_file())
                    self.assertEqual(rom.read_bytes(), b"not a real ROM; generator only")
                except Exception as error:
                    proofs[system.system] = {"verified": False, "core": system.default_core,
                                             "error": str(error)}
                else:
                    proofs[system.system] = {"verified": True, "core": choice.core,
                                             "controller": True, "isolation": True,
                                             "shader": True, "decoration_optional": True}
        # Existing Wii integration is structurally checked with the actual
        # pinned plugin too; this does not test Wiimote hardware or gameplay.
        wii_core = next(system.default_core for system in catalog_systems if system.system == "wii")
        with TemporaryDirectory(prefix="embercade-structure-", dir=PROJECT / ".work") as directory:
            root = Path(directory)
            env = {"HOME": str(root), "PATH": os.environ.get("PATH", ""), "LANG": "en_US.UTF-8",
                   "EMBERCADE_DISPLAY_WIDTH": "1920", "EMBERCADE_DISPLAY_HEIGHT": "1080"}
            settings = {"paths": {"roms": str(root / "roms"), "bios": str(root / "bios")},
                        "controller": {"exit_hotkey": "back-start"}}
            executable = root / "dolphin-emu"
            executable.write_text("#!/bin/sh\nexit 99\n")
            executable.chmod(0o755)
            settings["executables"] = {"dolphin": str(executable)}
            paths = EmbercadePaths.from_environment(env, config=settings)
            prepare_launch_layout(paths, PROJECT)
            rom = paths.rom_root / "wii/Synthetic Game (Test).wbfs"
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b"generator-only fixture; never boot")
            write_es_input_override(controller, runtime.share / "emulationstation/es_input.cfg",
                                    paths.emulationstation_config / "es_input.cfg")
            try:
                plan = create_launch_plan(system="wii", rom=rom, paths=paths, runtime=runtime,
                                          config=settings, environment=env, controller=controller,
                                          dry_run=True)
                execute_dolphin_dry_run(plan, paths)
                self.assertEqual(rom.read_bytes(), b"generator-only fixture; never boot")
            except Exception as error:
                proofs["wii"] = {"verified": False, "core": wii_core, "error": str(error)}
            else:
                proofs["wii"] = {"verified": True, "core": wii_core, "isolation": True,
                                 "controller": True, "special_peripherals": "NOT_VALIDATED"}
        # PS4 is an explicitly approved older-platform addition. Reuse the
        # exact same pinned-generator dry-run contract, never boot the fixture.
        from tests.test_shadps4 import structural_ps4
        with TemporaryDirectory(prefix="embercade-ps4-structure-", dir=PROJECT / ".work") as directory:
            try:
                structural_ps4(Path(directory))
            except Exception as error:
                proofs["ps4"] = {"verified": False, "core": "shadps4", "error": str(error)}
            else:
                proofs["ps4"] = {"verified": True, "core": "shadps4", "isolation": True,
                                 "controller": "NATIVE_SDL", "gameplay": "NOT_VALIDATED"}
        output = PROJECT / ".work/reports/system-structure.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"source_digest": structure_inputs_digest(PROJECT),
                                     "systems": proofs}, indent=2) + "\n")
        self.assertTrue(proofs, "no new system fixture generated")
        # Failures are blocked, not disguised as prepared. Assert the basic
        # cartridge routes plus newly added computer/disc routes really pass.
        for system in ("vectrex", "lynx", "ngp", "amiga500", "amigacdtv", "msx1", "pcfx", "ps4"):
            self.assertTrue(proofs[system]["verified"], proofs[system])

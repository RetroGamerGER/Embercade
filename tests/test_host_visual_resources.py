from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import subprocess
import unittest
from unittest.mock import Mock, patch

from embercade.decorations import (
    SETS, FALLBACK, DecorationResourceError, prepare_collection, validate_collection,
)
from embercade.shaders import (
    available_presets, find_host_shader_root, prepare_host_runtime, prepare_host_template,
)
from embercade.host_requirements import (
    DistroInfo, HostRequirement, RequirementStatus, XeniaProviderStatus,
    _probe_requirement, assess_host, create_bootstrap_plan,
)

PROJECT = Path(__file__).resolve().parents[1]


class HostVisualResourceTests(unittest.TestCase):
    def collection(self, root):
        source = root / "upstream"
        for name in SETS:
            (source / name).mkdir(parents=True)
        (source / "README.md").write_text("Original author notices\n")
        primary = source / FALLBACK / "systems"
        primary.mkdir()
        (primary / "snes.png").write_bytes(b"unchanged original art")
        (primary / "snes.info").write_text('{"width":1920}')
        (primary / "pal.info").write_text("snes.info\n")
        arcade = source / "arcade_vertical_default/system"
        arcade.mkdir()
        (arcade / "snes.png").symlink_to("../../default/systems/snes.png")
        (arcade / "snes.info").symlink_to("../../default/systems/snes.info")
        (arcade / "missing.png").symlink_to("../../default/systems/missing.png")
        return source

    def shader(self, root):
        package = root / "official package with spaces"
        folder = package / "crt"
        folder.mkdir(parents=True)
        (package / "README.md").write_text("Original package README")
        (folder / "test.slangp").write_text('shader0 = "test.slang"\ntextures = "FRAME"\nFRAME = "frame.png"\n')
        (folder / "test.slang").write_text('#include "helper.inc"\n')
        (folder / "helper.inc").write_text("// original implementation")
        (folder / "frame.png").write_bytes(b"original frame texture")
        catalog = root / "catalog.toml"
        catalog.write_text('[catalog]\nformat = 1\nbackend = "slang"\n'
            '[[preset]]\nid = "test"\nlabel = "Test"\nupstream = "crt/test"\n'
            'scanlines = false\nlicense = "Original grant"\nattribution = "Original author"\n')
        return package, catalog

    def test_official_collection_preserves_bytes_links_and_reports_real_gaps(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.collection(root)
            extra = source / "default_nocurve/systems"
            extra.mkdir()
            (extra / "arcadia.png").write_bytes(b"official alternative set art")
            (extra / "arcadia.info").write_text('{"width":1920}')
            (source / "default_nocurve/default.png").write_bytes(b"official generic frame")
            (source / "default_nocurve/default.info").write_text('{"width":1920}')
            output = root / "new payload"
            report = prepare_collection(source, output, PROJECT / "runtime/decorations.lock")
            self.assertEqual((output / "consoles").resolve(), (output / FALLBACK).resolve())
            self.assertEqual((output / "arcade_vertical_default/systems/snes.png").read_bytes(), b"unchanged original art")
            self.assertEqual((output / FALLBACK / "systems/arcadia.png").read_bytes(), b"official alternative set art")
            self.assertEqual((output / FALLBACK / "default.png").read_bytes(), b"official generic frame")
            self.assertIn(FALLBACK + "/systems/arcadia.png", report["same_system_fallback_links"])
            self.assertEqual(report["missing_upstream_links"], ["arcade_vertical_default/system/missing.png"])
            self.assertEqual(len(report["sets"]), 14)
            self.assertFalse(next(s for s in report["sets"] if s["id"] == "animated")["selectable"])
            self.assertEqual((output / "README.md").read_bytes(), (source / "README.md").read_bytes())
            self.assertTrue((output / FALLBACK / "systems/pal.info").is_symlink())
            self.assertEqual(report["normalized_text_aliases"], [FALLBACK + "/systems/pal.info"])
            self.assertTrue((output / "animated/.embercade-unavailable").is_file())
            self.assertEqual(validate_collection(output)["missing_upstream_links"], report["missing_upstream_links"])

    def test_collection_rejects_legacy_artwork_and_external_links(self):
        for bad in ("consoles", "outside-link"):
            with self.subTest(bad=bad), TemporaryDirectory() as temp:
                root = Path(temp)
                source = self.collection(root)
                if bad == "consoles":
                    (source / "consoles").mkdir()
                else:
                    (source / FALLBACK / "outside.png").symlink_to("../../../foreign.png")
                with self.assertRaises(DecorationResourceError):
                    prepare_collection(source, root / "out", PROJECT / "runtime/decorations.lock")
                self.assertFalse((root / "out").exists())

    def test_native_selection_for_all_regular_sets_scopes_and_legacy_replacement(self):
        from embercade.runtime import ProjectRuntime
        from embercade.backend import backend_command
        runtime = ProjectRuntime(PROJECT)
        if not runtime.python.is_file():
            self.skipTest("Prepared pinned runtime required")
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.collection(root)
            for name in SETS:
                if name == "animated":
                    continue
                systems = source / name / "systems"
                systems.mkdir(exist_ok=True)
                for system in ("ps2", "xbox", "snes"):
                    (systems / (system + ".png")).write_bytes(b"selection fixture only")
                    (systems / (system + ".info")).write_text('{"width":1920}')
            output = root / "resources"
            prepare_collection(source, output, PROJECT / "runtime/decorations.lock")
            config = root / "batocera.conf"
            es = root / "user/system/configs/emulationstation/es_settings.cfg"
            es.parent.mkdir(parents=True)
            es.write_text("<config/>")
            env = os.environ | {"EMBERCADE_DESKTOP": "1", "EMBERCADE_BATOCERA_SHARE_DIR": str(runtime.share / "batocera"),
                "EMBERCADE_BATOCERA_CONF": str(config), "EMBERCADE_SYSTEM_DECORATIONS": str(output),
                "EMBERCADE_USERDATA": str(root / "user")}
            def standalone(system, text):
                config.write_text(text)
                run = subprocess.run(backend_command(runtime.python, "resolve-decoration", system, "/roms/Game.iso"), env=env, text=True, capture_output=True, timeout=15)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(config.read_text(), text)
                return json.loads(run.stdout)["png"]
            for name in SETS:
                if name == "animated":
                    continue
                for system in ("ps2", "xbox"):
                    with self.subTest(name=name, system=system):
                        result = standalone(system, f"global.bezel={name}\n")
                        self.assertEqual(Path(result), output / name / "systems" / (system + ".png"))
            self.assertEqual(standalone("ps2", "global.bezel=default_curve\nps2.bezel=default_unglazed\n"), str(output / FALLBACK / "systems/ps2.png"))
            self.assertIsNone(standalone("ps2", 'global.bezel=default_curve\nps2["Game.iso"].bezel=none\n'))
            legacy = root / "user/decorations/consoles/systems/ps2.png"
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(b"old art must never be used")
            self.assertEqual(standalone("ps2", "global.bezel=consoles\n"), str(output / FALLBACK / "systems/ps2.png"))
            self.assertIsNone(standalone("xbox", "global.bezel=animated\n"))
            # Exercise the distinct Libretro getBezelInfos route as well.
            probe = """from pathlib import Path
from configgen.utils.bezels import getBezelInfos
import json,sys
result=getBezelInfos('/roms/Game.sfc',sys.argv[1],'snes','retroarch')
print(json.dumps({k:str(v) for k,v in result.items()} if result else None))
"""
            for name in (*[s for s in SETS if s != "animated"], "consoles", "animated"):
                run = subprocess.run([str(runtime.python), "-I", "-B", "-c", probe, name], env=env, capture_output=True, text=True, timeout=15)
                self.assertEqual(run.returncode, 0, run.stderr)
                result = json.loads(run.stdout)
                if name == "animated":
                    self.assertIsNone(result)
                else:
                    selected = FALLBACK if name == "consoles" else name
                    self.assertEqual(result["png"], str(output / selected / "systems/snes.png"))

    def test_host_menu_validates_include_and_texture_graph_and_never_copies_collection(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            package, catalog = self.shader(root)
            before = {p: p.read_bytes() for p in package.rglob("*") if p.is_file()}
            template = root / "app resources"
            prepare_host_template(template, catalog)
            env = {"EMBERCADE_HOST_SLANG_ROOT": str(package)}
            runtime = prepare_host_runtime(template, root / "private session", env)
            self.assertTrue((runtime / "configs/test/rendering-defaults.yml").is_file())
            self.assertEqual((runtime / "provider").resolve(), package)
            self.assertEqual((runtime / "embercade/test.slangp").read_text(), '#reference "../provider/crt/test.slangp"\n')
            self.assertFalse(list(template.rglob("*.slang")))
            self.assertFalse(list(template.rglob("*.png")))
            self.assertEqual(before, {p: p.read_bytes() for p in package.rglob("*") if p.is_file()})
            # Refresh after an incomplete/removed package. No stale selectable entry.
            (package / "crt/frame.png").unlink()
            available, missing = available_presets(package, catalog)
            self.assertEqual(available, {})
            self.assertIn("test", missing)
            runtime = prepare_host_runtime(template, root / "private session", env)
            self.assertFalse((runtime / "configs/test").exists())
            self.assertFalse((runtime / "embercade/test.slangp").exists())
            self.assertIn("test", json.loads((runtime / "embercade-metadata/status.json").read_text())["unavailable"])

    def test_missing_host_package_is_optional_and_default_remains_no_shader(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            _, catalog = self.shader(root)
            template = root / "template"
            prepare_host_template(template, catalog)
            env = {"EMBERCADE_HOST_SLANG_ROOT": str(root / "absent")}
            runtime = prepare_host_runtime(template, root / "session", env)
            self.assertEqual(list((runtime / "configs").iterdir()), [runtime / "configs/rendering-defaults.yml"])
            self.assertIn("  shader:\n", (runtime / "configs/rendering-defaults.yml").read_text())
            self.assertIsNone(find_host_shader_root(env))
            defaults = (PROJECT / "resources/defaults/batocera.conf").read_text()
            self.assertEqual([s for s in defaults.splitlines() if ".shaderset=" in s], ["global.shaderset=none"])

    def test_real_distro_package_file_list_is_used_without_assuming_mounts(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            package, _ = self.shader(root)
            result = subprocess.CompletedProcess([], 0, f"{package}/shaders/extra/README.md\n", "")
            actual = package / "shaders/extra"
            actual.mkdir(parents=True)
            (actual / "README.md").write_text("Installed shader files")
            with patch("embercade.shaders.HOST_SLANG_ROOTS", ()), patch("embercade.shaders.subprocess.run", return_value=result) as query:
                self.assertEqual(find_host_shader_root({}), actual)
                self.assertEqual(query.call_args.args[0], ["pacman", "-Qlq", "libretro-shaders-slang"])

    def test_optional_package_uses_existing_arch_garuda_cachyos_plan_and_translations(self):
        for distro in ("arch", "garuda", "cachyos"):
            with self.subTest(distro=distro), \
                 patch("embercade.host_requirements._active_routes", return_value=((), (), ())), \
                 patch("embercade.host_requirements.inspect_appimage_provider", return_value=XeniaProviderStatus("OPTIONAL", "optional")), \
                 patch("embercade.host_requirements.inspect_xenia_provider", return_value=XeniaProviderStatus("OPTIONAL", "optional")), \
                 patch("embercade.host_requirements._probe_requirement", side_effect=lambda r, *_: RequirementStatus(r, r.key != "libretro-shaders", "fixture")):
                assessment = assess_host(resolver=Mock(), core_resolver=Mock(), environment={}, rom_root=Path("/roms"), systems_config=Path("/systems"), default_config=Path("/defaults"), user_config=Path("/user"), distro=DistroInfo(distro, distro, ("arch",) if distro in {"garuda", "cachyos", "endeavouros"} else ()))
                plan = create_bootstrap_plan(assessment, Mock(available=lambda _: True))
                self.assertEqual(plan.packages, ("libretro-shaders-slang",))
                requirement = next(s.requirement for s in assessment.requirements if s.requirement.key == "libretro-shaders")
                self.assertFalse(requirement.required)
                from embercade.i18n import Translator
                self.assertEqual(Translator("de")(requirement.label), "RetroArch-Shader-Sammlung")
                self.assertEqual(Translator("en")(requirement.label), requirement.label)

    def test_host_probe_checks_newpixie_dependencies_without_running_emulator(self):
        requirement = HostRequirement("libretro-shaders", "RetroArch shader collection", "libretro-shaders-slang", probe="libretro-shaders", required=False)
        with TemporaryDirectory() as temp:
            root = Path(temp)
            package, _ = self.shader(root)
            (package / "crt/newpixie-crt.slangp").write_text('#reference "test.slangp"\n')
            env = {"EMBERCADE_HOST_SLANG_ROOT": str(package)}
            self.assertTrue(_probe_requirement(requirement, Mock(), env).installed)
            (package / "crt/helper.inc").unlink()
            self.assertFalse(_probe_requirement(requirement, Mock(), env).installed)


if __name__ == "__main__":
    unittest.main()

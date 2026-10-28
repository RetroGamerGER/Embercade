from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.paths import EmbercadePaths
from embercade.runtime import load_config


class EmbercadePathsTests(unittest.TestCase):
    def test_xdg_defaults_and_mapping(self) -> None:
        env = {
            "HOME": "/home/tester",
            "XDG_CONFIG_HOME": "/xdg/config",
            "XDG_DATA_HOME": "/xdg/data",
            "XDG_CACHE_HOME": "/xdg/cache",
            "XDG_STATE_HOME": "/xdg/state",
            "XDG_RUNTIME_DIR": "/run/user/1000",
        }
        paths = EmbercadePaths.from_environment(env)

        self.assertEqual(paths.config, Path("/xdg/config/embercade"))
        self.assertEqual(paths.data, Path("/xdg/data/embercade"))
        self.assertEqual(paths.cache, Path("/xdg/cache/embercade"))
        self.assertEqual(paths.state, Path("/xdg/state/embercade"))
        self.assertEqual(paths.runtime, Path("/run/user/1000/embercade"))
        self.assertEqual(paths.roms, Path("/xdg/data/embercade/roms"))
        self.assertEqual(paths.bios, Path("/xdg/data/embercade/bios"))
        self.assertEqual(paths.rom_root, paths.roms)
        self.assertEqual(paths.bios_root, paths.bios)
        self.assertEqual(paths.isolated_bios, Path("/xdg/data/embercade/bios"))
        self.assertEqual(paths.secrets, Path("/xdg/config/embercade/secrets"))
        self.assertFalse(paths.roms_configured)
        self.assertFalse(paths.bios_configured)
        self.assertEqual(
            paths.emulationstation_config,
            Path("/xdg/config/embercade/emulators/emulationstation"),
        )

        mapping = paths.batocera_mapping()
        self.assertEqual(mapping["/userdata/system/configs"], paths.emulator_configs)
        self.assertEqual(
            mapping["/userdata/system/configs/emulationstation"],
            paths.emulationstation_config,
        )
        self.assertEqual(mapping["/userdata/system/cache"], paths.cache)
        self.assertEqual(mapping["/userdata/saves"], paths.saves)
        self.assertEqual(mapping["/userdata/themes"], paths.themes)
        self.assertEqual(paths.themes, Path("/xdg/data/embercade/themes"))
        self.assertEqual(paths.theme_downloads, paths.themes / ".tmp")
        self.assertEqual(mapping["/userdata/decorations"], paths.decorations)
        self.assertEqual(mapping["/run"], paths.runtime)
        self.assertEqual(mapping["/var/run"], paths.runtime)
        self.assertEqual(paths.writable_roots_inside(Path("/app")), ())

    def test_appimage_runtime_cannot_own_writable_xdg_state(self) -> None:
        with TemporaryDirectory() as directory:
            appdir = Path(directory) / "AppDir"
            paths = EmbercadePaths.from_environment({
                "HOME": str(Path(directory) / "home"),
                "XDG_CONFIG_HOME": str(appdir / "config"),
            })
            self.assertEqual(paths.writable_roots_inside(appdir), ("config",))

    def test_rom_bios_and_embercade_overrides(self) -> None:
        env = {
            "HOME": "/home/tester",
            "EMBERCADE_CONFIG_HOME": "/portable/config",
            "EMBERCADE_RUNTIME_HOME": "/portable/run",
            "EMBERCADE_ROMS_ROOT": "/games/roms",
            "EMBERCADE_BIOS_ROOT": "/games/bios",
        }
        paths = EmbercadePaths.from_environment(env)
        self.assertEqual(paths.config, Path("/portable/config"))
        self.assertEqual(paths.runtime, Path("/portable/run"))
        self.assertEqual(paths.roms, Path("/games/roms"))
        self.assertEqual(paths.bios, Path("/games/bios"))
        self.assertTrue(paths.roms_configured)
        self.assertTrue(paths.bios_configured)

    def test_configured_existing_roots_with_spaces_are_valid(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "ROM collection with spaces"
            bios = root / "BIOS collection with spaces"
            roms.mkdir()
            bios.mkdir()

            paths = EmbercadePaths.from_environment(
                {"HOME": str(root / "home")},
                config={"paths": {"roms": str(roms), "bios": str(bios)}},
            )
            statuses = paths.validate_collection_roots()

            self.assertEqual(paths.rom_root, roms)
            self.assertEqual(paths.bios_root, bios)
            self.assertEqual([status.status for status in statuses], ["OK", "OK"])

    def test_configured_missing_roots_are_reported_without_creation(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "missing roms"
            bios = root / "missing bios"
            paths = EmbercadePaths.from_environment(
                {"HOME": str(root / "home")},
                config={"paths": {"roms": str(roms), "bios": str(bios)}},
            )

            statuses = paths.validate_collection_roots()

            self.assertEqual([status.status for status in statuses], ["MISSING", "MISSING"])
            self.assertFalse(roms.exists())
            self.assertFalse(bios.exists())

    def test_unconfigured_roots_are_distinct_from_missing_roots(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})

            statuses = paths.validate_collection_roots()

            self.assertEqual(
                [status.status for status in statuses],
                ["NOT CONFIGURED", "NOT CONFIGURED"],
            )

    def test_environment_override_precedes_paths_config(self) -> None:
        paths = EmbercadePaths.from_environment(
            {
                "HOME": "/home/tester",
                "EMBERCADE_ROMS_ROOT": "/environment/roms",
                "EMBERCADE_BIOS_ROOT": "/environment/bios",
            },
            config={"paths": {"roms": "/config/roms", "bios": "/config/bios"}},
        )
        self.assertEqual(paths.rom_root, Path("/environment/roms"))
        self.assertEqual(paths.bios_root, Path("/environment/bios"))

    def test_tilde_uses_selected_home_and_config_file_is_not_modified(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "selected home"
            config_path = root / "embercade.toml"
            original = '[paths]\nroms = "~/ROMs"\nbios = "~/BIOS files"\n'
            config_path.write_text(original, encoding="utf-8")

            paths = EmbercadePaths.from_environment(
                {"HOME": str(home)}, config=load_config(config_path)
            )

            self.assertEqual(paths.rom_root, home / "ROMs")
            self.assertEqual(paths.bios_root, home / "BIOS files")
            self.assertEqual(config_path.read_text(encoding="utf-8"), original)

    def test_invalid_paths_table_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, r"\[paths\]"):
            EmbercadePaths.from_environment({}, config={"paths": "not a table"})
        with self.assertRaisesRegex(ValueError, r"\[paths\]\.roms"):
            EmbercadePaths.from_environment({}, config={"paths": {"roms": 42}})

    def test_resolution_has_no_directory_creation_side_effect(self) -> None:
        home = Path("/tmp/embercade-path-test-must-not-exist")
        paths = EmbercadePaths.from_environment({"HOME": str(home)})
        self.assertEqual(paths.config, home / ".config/embercade")
        self.assertFalse(paths.config.exists())


if __name__ == "__main__":
    unittest.main()

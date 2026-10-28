from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from embercade.cores import (
    CoreResolutionError,
    LibretroCoreResolver,
    SearchDirectory,
    load_batocera_catalog,
    read_retroarch_paths,
    write_inventory,
)


class LibretroCoreResolverTests(unittest.TestCase):
    @staticmethod
    def _core(directory: Path, name: str) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{name}_libretro.so"
        path.write_bytes(b"\x7fELFtest core")
        return path

    def test_reads_relevant_retroarch_paths_without_modifying_config(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "retro arch.cfg"
            original = (
                'libretro_directory = "cores with spaces"\n'
                'core_info_path = "~/retro info"\n'
                'assets_directory = "/opt/retro assets" # comment\n'
                'system_directory = "default"\n'
                'unrelated_setting = "ignored"\n'
            )
            config.write_text(original, encoding="utf-8")

            settings = read_retroarch_paths(config, home=root / "home")

            self.assertEqual(settings["libretro_directory"], root / "cores with spaces")
            self.assertEqual(settings["core_info_path"], root / "home/retro info")
            self.assertEqual(settings["assets_directory"], Path("/opt/retro assets"))
            self.assertNotIn("system_directory", settings)
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_user_configured_core_precedes_system_configured_core(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            user_cores = root / "user cores"
            system_cores = root / "system cores"
            expected = self._core(user_cores, "nestopia")
            self._core(system_cores, "nestopia")
            user_config = root / "user.cfg"
            system_config = root / "system.cfg"
            user_config.write_text(f'libretro_directory = "{user_cores}"\n', encoding="utf-8")
            system_config.write_text(f'libretro_directory = "{system_cores}"\n', encoding="utf-8")

            resolver = LibretroCoreResolver.from_host(
                {},
                {"HOME": str(root)},
                user_config=user_config,
                system_config=system_config,
                fallback_core_directories=(),
                fallback_info_directories=(),
            )

            self.assertEqual(resolver.resolve("nestopia").path, expected)
            self.assertEqual(resolver.resolve("nestopia").source, "retroarch-user-config")

    def test_managed_core_precedes_host_retroarch_and_survives_source_removal(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            managed = self._core(root / "data/embercade/cores", "nestopia")
            host = self._core(root / "retroarch/cores", "nestopia")
            user_config = root / "retroarch.cfg"
            user_config.write_text(f'libretro_directory = "{host.parent}"\n')
            resolver = LibretroCoreResolver.from_host(
                {}, {"HOME": str(root), "XDG_DATA_HOME": str(root / "data")},
                user_config=user_config,
                system_config=root / "missing.cfg",
                fallback_core_directories=(),
                fallback_info_directories=(),
            )
            self.assertEqual(resolver.resolve("nestopia").path, managed)
            self.assertEqual(resolver.resolve("nestopia").source, "embercade-managed")

    def test_explicit_per_core_override_has_highest_precedence(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            override = self._core(root / "override", "custom_nestopia")
            self._core(root / "configured", "nestopia")
            resolver = LibretroCoreResolver.from_host(
                {
                    "libretro": {
                        "cores": str(root / "configured"),
                        "core_overrides": {"nestopia": str(override)},
                    }
                },
                {"HOME": str(root)},
                user_config=root / "absent-user.cfg",
                system_config=root / "absent-system.cfg",
                fallback_core_directories=(),
                fallback_info_directories=(),
            )

            result = resolver.resolve("nestopia")
            self.assertEqual(result.path, override)
            self.assertEqual(result.source, "embercade-override")

    def test_missing_info_does_not_make_binary_unavailable(self) -> None:
        with TemporaryDirectory() as directory:
            core = self._core(Path(directory) / "cores", "nestopia")
            resolver = LibretroCoreResolver(
                core_directories=(SearchDirectory(core.parent, "test", "user", True),)
            )

            result = resolver.resolve("nestopia")

            self.assertEqual(result.path, core)
            self.assertIsNone(result.info_path)
            self.assertTrue(result.probably_loadable)

    def test_batocera_alias_maps_to_distribution_binary(self) -> None:
        with TemporaryDirectory() as directory:
            core = self._core(Path(directory) / "cores", "genesis_plus_gx")
            resolver = LibretroCoreResolver(
                core_directories=(SearchDirectory(core.parent, "test", "system", True),)
            )

            result = resolver.resolve("genesisplusgx")

            self.assertEqual(result.path, core)
            self.assertEqual(result.alias, "genesis_plus_gx")

    def test_batocera_beetle_psx_prefers_desktop_hardware_build(self) -> None:
        with TemporaryDirectory() as directory:
            cores = Path(directory) / "cores"
            self._core(cores, "mednafen_psx")
            hardware = self._core(cores, "mednafen_psx_hw")
            resolver = LibretroCoreResolver(
                core_directories=(SearchDirectory(cores, "test", "user", True),)
            )

            result = resolver.resolve("mednafen_psx")

            self.assertEqual(result.path, hardware)
            self.assertEqual(result.alias, "mednafen_psx_hw")

    def test_new_desktop_override_cores_use_exact_core_names(self) -> None:
        with TemporaryDirectory() as directory:
            cores = Path(directory) / "cores"
            expected = {
                name: self._core(cores, name)
                for name in (
                    "ppsspp",
                    "azahar",
                    "citra",
                    "citra2018",
                    "parallel_n64",
                    "virtualjaguar",
                )
            }
            resolver = LibretroCoreResolver(
                core_directories=(SearchDirectory(cores, "test", "user", True),)
            )

            for name, path in expected.items():
                with self.subTest(core=name):
                    result = resolver.resolve(name)
                    self.assertEqual(result.path, path)
                    self.assertIsNone(result.alias)

            mupen_path = self._core(cores, "mupen64plus_next")
            mupen = resolver.resolve("mupen64plus-next")
            self.assertEqual(mupen.path, mupen_path)
            self.assertEqual(mupen.alias, "mupen64plus_next")

    def test_missing_core_has_clear_candidates_and_directories(self) -> None:
        resolver = LibretroCoreResolver(
            core_directories=(SearchDirectory(Path("/cores with spaces"), "test", "user", True),)
        )
        with self.assertRaisesRegex(
            CoreResolutionError,
            r"missing.*missing_libretro\.so.*cores with spaces",
        ):
            resolver.resolve("missing")

    def test_inventory_is_reproducible_and_machine_readable(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cores = root / "cores"
            info = root / "info"
            self._core(cores, "nestopia")
            info.mkdir()
            (info / "nestopia_libretro.info").write_text(
                'display_name = "Nestopia UE"\n', encoding="utf-8"
            )
            resolver = LibretroCoreResolver(
                core_directories=(SearchDirectory(cores, "test", "system", True),),
                info_directories=(SearchDirectory(info, "test", "system", True),),
            )
            inventory = resolver.inventory(("nestopia", "missing"))
            output = root / "inventory with spaces.json"

            write_inventory(output, inventory)
            loaded = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(loaded["summary"]["installed_unique"], 1)
            self.assertEqual(loaded["summary"]["batocera_found"], 1)
            self.assertEqual(loaded["summary"]["batocera_missing"], 1)
            nestopia = next(
                row for row in loaded["batocera_cores"] if row["batocera_name"] == "nestopia"
            )
            self.assertEqual(nestopia["info_path"], str(info / "nestopia_libretro.info"))

    def test_symlinked_distribution_directory_is_counted_once(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cores = root / "lib/libretro"
            self._core(cores, "nestopia")
            link = root / "lib64"
            link.symlink_to(root / "lib", target_is_directory=True)
            resolver = LibretroCoreResolver(
                core_directories=(
                    SearchDirectory(cores, "primary", "system", False),
                    SearchDirectory(link / "libretro", "alias", "system", False),
                )
            )

            self.assertEqual(len(resolver.core_directories), 1)
            self.assertEqual(len(resolver.installed_cores()), 1)

    def test_project_catalog_is_sorted_unique_and_contains_nestopia(self) -> None:
        catalog = load_batocera_catalog(
            Path(__file__).resolve().parents[1]
            / "resources/libretro/batocera-44-cores.txt"
        )
        self.assertEqual(catalog, tuple(sorted(set(catalog))))
        self.assertIn("nestopia", catalog)
        self.assertIn("ppsspp", catalog)
        self.assertIn("azahar", catalog)
        self.assertIn("mupen64plus-next", catalog)
        self.assertIn("parallel_n64", catalog)
        self.assertIn("virtualjaguar", catalog)
        self.assertEqual(len(catalog), 124)


if __name__ == "__main__":
    unittest.main()

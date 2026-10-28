from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.launcher import _prepare_ppsspp_system_directory
from embercade.paths import EmbercadePaths
from embercade.ppsspp import PpssppAssetsError, resolve_ppsspp_assets
from embercade.production import _optional_host_sources


class PpssppAssetsTests(unittest.TestCase):
    def assets(self, root: Path) -> Path:
        root.mkdir(parents=True)
        (root / "ppge_atlas.zim").write_bytes(b"atlas")
        (root / "lang").mkdir()
        (root / "flash0").mkdir()
        return root

    def test_default_discovery_and_isolated_system_link(self):
        with TemporaryDirectory() as temporary:
            paths = EmbercadePaths.from_environment({"HOME": temporary})
            source = self.assets(paths.data / "resources/PPSSPP")
            system = _prepare_ppsspp_system_directory(paths, {}, {})
            self.assertEqual((system / "PPSSPP").resolve(), source)
            self.assertTrue(system.is_relative_to(paths.data))
            self.assertEqual((source / "ppge_atlas.zim").read_bytes(), b"atlas")

    def test_override_precedence_and_incomplete_override_never_falls_back(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = EmbercadePaths.from_environment({"HOME": temporary})
            self.assets(paths.data / "resources/PPSSPP")
            configured = self.assets(root / "configured assets")
            override = self.assets(root / "environment assets")
            config = {"libretro": {"ppsspp_assets": str(configured)}}
            self.assertEqual(resolve_ppsspp_assets(paths, config, {}), configured)
            env = {"EMBERCADE_PPSSPP_ASSETS": str(override)}
            self.assertEqual(resolve_ppsspp_assets(paths, config, env), override)
            (override / "flash0").rmdir()
            with self.assertRaisesRegex(PpssppAssetsError, "flash0"):
                resolve_ppsspp_assets(paths, config, env)

    def test_production_mounts_external_assets_read_only_at_stable_path(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = EmbercadePaths.from_environment({"HOME": temporary})
            source = self.assets(root / "external assets")
            alias = root / "asset symlink"
            alias.symlink_to(source, target_is_directory=True)
            mounts, variables = _optional_host_sources(
                paths, {"libretro": {"ppsspp_assets": str(alias)}}, {"HOME": temporary}
            )
            self.assertEqual(mounts, ["--ro-bind", str(source), "/embercade-ppsspp-assets"])
            self.assertEqual(variables, ["--setenv", "EMBERCADE_PPSSPP_ASSETS", "/embercade-ppsspp-assets"])

    def test_missing_assets_do_not_block_other_systems(self):
        with TemporaryDirectory() as temporary:
            paths = EmbercadePaths.from_environment({"HOME": temporary})
            with self.assertRaisesRegex(PpssppAssetsError, "ppge_atlas.zim"):
                resolve_ppsspp_assets(paths, {}, {})
            mounts, variables = _optional_host_sources(paths, {}, {"HOME": temporary})
            self.assertEqual((mounts, variables), ([], []))
            self.assertFalse(paths.data.exists())

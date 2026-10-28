from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from embercade.paths import EmbercadePaths
from embercade.rpcs3 import (
    Rpcs3RuntimeError,
    existing_firmware_package,
    inspect_rpcs3_firmware,
    open_firmware_installer,
    prepare_rpcs3_firmware,
    resolve_rpcs3_runtime,
    rpcs3_writable_directories,
)


class Rpcs3RuntimeTests(unittest.TestCase):
    @staticmethod
    def _firmware(root: Path, version: str = "04.9300") -> Path:
        (root / "dev_flash/vsh/etc").mkdir(parents=True)
        (root / "dev_flash/vsh/etc/version.txt").write_text(
            f"release:{version}:build:test\n", encoding="utf-8"
        )
        (root / "dev_flash/sys/external").mkdir(parents=True)
        (root / "dev_flash/sys/external/liblv2.sprx").write_bytes(b"firmware")
        (root / "dev_flash2").mkdir()
        (root / "dev_flash3").mkdir()
        return root

    def test_existing_firmware_is_copied_only_into_isolated_config(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root / "home"),
                    "EMBERCADE_CONFIG_HOME": str(root / "project/.work/config"),
                    "EMBERCADE_DATA_HOME": str(root / "project/.work/data"),
                    "EMBERCADE_CACHE_HOME": str(root / "project/.work/cache"),
                    "EMBERCADE_STATE_HOME": str(root / "project/.work/state"),
                }
            )
            source = self._firmware(root / "host-profile")
            runtime = prepare_rpcs3_firmware(
                paths, {}, {"EMBERCADE_RPCS3_FIRMWARE_SOURCE": str(source)}
            )

            self.assertEqual(runtime.firmware_version, "04.9300")
            self.assertEqual(
                (runtime.config_dir / "dev_flash/sys/external/liblv2.sprx").read_bytes(),
                b"firmware",
            )
            marker = json.loads(
                (runtime.config_dir / "embercade-firmware.json").read_text(encoding="utf-8")
            )
            self.assertEqual(marker["source"], str(source))
            self.assertEqual((source / "dev_flash/sys/external/liblv2.sprx").read_bytes(), b"firmware")

    def test_missing_firmware_is_rejected_before_plugin_launch(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            with self.assertRaisesRegex(Rpcs3RuntimeError, "firmware source is unavailable"):
                resolve_rpcs3_runtime(paths, {}, {"HOME": str(root)})

    def test_pup_file_does_not_count_as_installed_firmware(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bios = root / "bios"
            bios.mkdir()
            (bios / "PS3UPDAT.PUP").write_bytes(b"not installed")
            paths = EmbercadePaths.from_environment(
                {"HOME": str(root), "EMBERCADE_BIOS_ROOT": str(bios)}
            )
            status = inspect_rpcs3_firmware(paths, {}, {"HOME": str(root)})
            self.assertFalse(status.installed)
            self.assertIn("alone is not installed firmware", status.detail)
            self.assertEqual(existing_firmware_package(bios), bios / "PS3UPDAT.PUP")

    def test_firmware_ui_uses_only_embercade_xdg_and_rechecks(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            binary = root / "rpcs3"
            binary.touch()
            host_config = root / "host-config"
            host_config.mkdir()
            def run(argv, *, check, env):
                self.assertEqual(argv, [str(binary)])
                self.assertFalse(check)
                self.assertEqual(env["XDG_CONFIG_HOME"], str(paths.emulator_configs))
                self.assertEqual(env["XDG_DATA_HOME"], str(paths.data))
                self.assertTrue(env["HOME"].startswith(str(paths.data)))
                self._firmware(paths.emulator_configs / "rpcs3")
                return __import__("subprocess").CompletedProcess(argv, 0)
            status = open_firmware_installer(
                binary, paths, {}, {"HOME": str(root), "XDG_CONFIG_HOME": str(host_config)}, runner=run
            )
            self.assertTrue(status.installed)
            self.assertFalse((host_config / "rpcs3").exists())
            self.assertEqual(
                prepare_rpcs3_firmware(paths, {}, {"HOME": str(root)}).firmware_source,
                paths.emulator_configs / "rpcs3",
            )

    def test_normal_host_profile_counts_as_installed_firmware_source(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._firmware(root / "config/rpcs3")
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            status = inspect_rpcs3_firmware(
                paths, {}, {"HOME": str(root), "XDG_CONFIG_HOME": str(root / "config")}
            )
            self.assertTrue(status.installed)
            self.assertEqual(status.version, "04.9300")
            runtime = prepare_rpcs3_firmware(
                paths, {}, {"HOME": str(root), "XDG_CONFIG_HOME": str(root / "config")})
            self.assertEqual(runtime.firmware_source, paths.emulator_configs / "rpcs3")
            self.assertEqual(runtime.firmware_version, status.version)
            self.assertTrue((root / "config/rpcs3/dev_flash/vsh/etc/version.txt").is_file())

    def test_mismatched_existing_firmware_is_not_overwritten(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            source = self._firmware(root / "source", "04.9300")
            self._firmware(paths.emulator_configs / "rpcs3", "04.9200")
            with self.assertRaisesRegex(Rpcs3RuntimeError, "refusing to overwrite"):
                prepare_rpcs3_firmware(
                    paths, {}, {"EMBERCADE_RPCS3_FIRMWARE_SOURCE": str(source)}
                )

    def test_every_writable_directory_is_inside_embercade_roots(self) -> None:
        paths = EmbercadePaths.from_environment(
            {
                "HOME": "/host-home",
                "EMBERCADE_CONFIG_HOME": "/project/.work/config",
                "EMBERCADE_DATA_HOME": "/project/.work/data",
                "EMBERCADE_CACHE_HOME": "/project/.work/cache",
                "EMBERCADE_STATE_HOME": "/project/.work/state",
            }
        )
        allowed = (paths.config, paths.data, paths.cache, paths.state)
        for directory in rpcs3_writable_directories(paths):
            self.assertTrue(any(directory.is_relative_to(root) for root in allowed), directory)
            self.assertNotIn("/userdata", str(directory))
            self.assertNotIn("/host-home/.config/rpcs3", str(directory))


if __name__ == "__main__":
    unittest.main()

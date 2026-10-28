from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from embercade.paths import EmbercadePaths
from embercade.xemu import (
    XemuRuntimeError,
    inspect_xemu_files,
    isolated_xemu_files,
    prepare_xemu_files,
    prepare_xemu_files_from,
)


class XemuRuntimeTests(unittest.TestCase):
    def test_first_preparation_without_eeprom_leaves_generation_to_xemu(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Xbox source"
            source.mkdir()
            for name in ("Complex_4627.bin", "mcpx_1.0.bin", "xbox_hdd.qcow2"):
                (source / name).write_bytes(name.encode())
            paths = EmbercadePaths.from_environment({"HOME": str(root / "home")})
            files = prepare_xemu_files_from(paths, source, {
                "EMBERCADE_XEMU_EEPROM_SOURCE": "/unrelated/old/profile/eeprom.bin",
            })
            self.assertFalse(files.eeprom.exists())
            self.assertTrue(files.eeprom.parent.is_dir())
            self.assertEqual(files.as_environment()["EMBERCADE_XEMU_EEPROM"], str(files.eeprom))
            self.assertIn("created by Xemu on first start", inspect_xemu_files(paths, {}).eeprom_detail)
            files.eeprom.write_bytes(b"persistent emulator-generated EEPROM")
            before = files.eeprom.stat().st_mtime_ns
            prepare_xemu_files_from(paths, source, {})
            self.assertEqual(files.eeprom.read_bytes(), b"persistent emulator-generated EEPROM")
            self.assertEqual(files.eeprom.stat().st_mtime_ns, before)
            self.assertEqual(sorted(p.name for p in source.iterdir()),
                             ["Complex_4627.bin", "mcpx_1.0.bin", "xbox_hdd.qcow2"])

    def test_missing_explicit_eeprom_backup_is_not_silently_regenerated(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            files = isolated_xemu_files(paths)
            for path in (files.flashrom, files.bootrom):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"existing firmware")
            with self.assertRaisesRegex(XemuRuntimeError, "Configured Xemu EEPROM seed"):
                prepare_xemu_files(paths, {"EMBERCADE_XEMU_EEPROM_SOURCE": str(Path(directory)/"missing")})
            self.assertFalse(files.eeprom.exists())

    def test_existing_eeprom_symlink_is_preserved_and_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            files = isolated_xemu_files(paths)
            for path in (files.flashrom, files.bootrom):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"existing firmware")
            files.eeprom.parent.mkdir(parents=True)
            files.eeprom.symlink_to(Path(directory)/"missing external EEPROM")
            with self.assertRaisesRegex(XemuRuntimeError, "Existing isolated Xemu eeprom"):
                prepare_xemu_files(paths, {})
            self.assertTrue(files.eeprom.is_symlink())

    def test_selected_directory_is_read_only_and_workfiles_are_isolated(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "original Xbox files"
            source.mkdir()
            for name in ("Complex_4627.bin", "mcpx_1.0.bin", "eeprom.bin", "xbox_hdd.qcow2"):
                (source / name).write_bytes(name.encode())
            paths = EmbercadePaths.from_environment({"HOME": str(root / "home")})
            files = prepare_xemu_files_from(paths, source, {"HOME": str(root / "home")})
            self.assertEqual(files.hdd.read_bytes(), b"xbox_hdd.qcow2")
            files.hdd.write_bytes(b"isolated save")
            prepare_xemu_files_from(paths, source, {"HOME": str(root / "home")})
            self.assertEqual(files.hdd.read_bytes(), b"isolated save")
            self.assertEqual((source / "xbox_hdd.qcow2").read_bytes(), b"xbox_hdd.qcow2")

    def test_missing_selected_file_fails_before_creating_any_workfiles(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            for name in ("Complex_4627.bin", "mcpx_1.0.bin", "eeprom.bin"):
                (source / name).write_bytes(b"file")
            paths = EmbercadePaths.from_environment({"HOME": str(root / "home")})
            with self.assertRaisesRegex(XemuRuntimeError, "xbox_hdd.qcow2"):
                prepare_xemu_files_from(paths, source, {"HOME": str(root / "home")})
            self.assertFalse(paths.data.exists())

    def test_sources_are_copied_once_into_isolated_writable_state(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root),
                    "EMBERCADE_CONFIG_HOME": str(root / "isolated/config"),
                    "EMBERCADE_DATA_HOME": str(root / "isolated/data"),
                    "EMBERCADE_BIOS_ROOT": str(root / "isolated/data/bios"),
                }
            )
            source_root = root / "sources"
            source_root.mkdir()
            sources = {}
            for field, name in (
                ("FLASHROM", "Complex_4627.bin"),
                ("BOOTROM", "mcpx_1.0.bin"),
                ("EEPROM", "eeprom.bin"),
                ("HDD", "xbox_hdd.qcow2"),
            ):
                source = source_root / name
                source.write_bytes(field.encode("ascii"))
                sources[field] = source
            before = {
                field: hashlib.sha256(source.read_bytes()).hexdigest()
                for field, source in sources.items()
            }
            env = {
                f"EMBERCADE_XEMU_{field}_SOURCE": str(source)
                for field, source in sources.items()
            }

            files = prepare_xemu_files(paths, env)
            self.assertEqual(files, isolated_xemu_files(paths))
            self.assertEqual(files.flashrom.read_bytes(), b"FLASHROM")
            self.assertEqual(files.bootrom.read_bytes(), b"BOOTROM")
            self.assertEqual(files.eeprom.read_bytes(), b"EEPROM")
            self.assertEqual(files.hdd.read_bytes(), b"HDD")

            files.eeprom.write_bytes(b"changed isolated state")
            prepare_xemu_files(paths, env)
            self.assertEqual(files.eeprom.read_bytes(), b"changed isolated state")
            self.assertEqual(
                before,
                {
                    field: hashlib.sha256(source.read_bytes()).hexdigest()
                    for field, source in sources.items()
                },
            )

    def test_missing_source_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            with self.assertRaisesRegex(XemuRuntimeError, "FLASHROM_SOURCE.*Complex_4627.bin"):
                prepare_xemu_files(paths, {})

    def test_central_read_only_bios_files_are_valid_default_sources(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bios = root / "central bios"
            bios.mkdir()
            expected = {
                "Complex_4627.bin": b"FLASHROM",
                "mcpx_1.0.bin": b"BOOTROM",
                "eeprom.bin": b"EEPROM",
                "xbox_hdd.qcow2": b"HDD",
            }
            for name, content in expected.items():
                (bios / name).write_bytes(content)
            before = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in bios.iterdir()
            }
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root),
                    "EMBERCADE_DATA_HOME": str(root / "isolated data"),
                    "EMBERCADE_BIOS_ROOT": str(bios),
                }
            )

            files = prepare_xemu_files(paths, {})

            self.assertEqual(files.flashrom.read_bytes(), b"FLASHROM")
            self.assertEqual(files.bootrom.read_bytes(), b"BOOTROM")
            self.assertEqual(files.eeprom.read_bytes(), b"EEPROM")
            self.assertEqual(files.hdd.read_bytes(), b"HDD")
            self.assertEqual(
                before,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in bios.iterdir()
                },
            )

    def test_existing_unusable_destination_is_never_replaced(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            destination = isolated_xemu_files(paths).flashrom
            destination.mkdir(parents=True)
            with self.assertRaisesRegex(XemuRuntimeError, "not a readable, writable file"):
                prepare_xemu_files(paths, {})
            self.assertTrue(destination.is_dir())

    def test_firmware_and_missing_mutable_files_are_reported_separately(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bios = root / "bios"
            bios.mkdir()
            (bios / "Complex_4627.bin").write_bytes(b"flash")
            (bios / "mcpx_1.0.bin").write_bytes(b"mcpx")
            paths = EmbercadePaths.from_environment(
                {"HOME": str(root), "EMBERCADE_BIOS_ROOT": str(bios)}
            )
            status = inspect_xemu_files(paths, {})
            self.assertTrue(status.firmware_ready)
            self.assertFalse(status.eeprom_ready)
            self.assertFalse(status.hdd_ready)


if __name__ == "__main__":
    unittest.main()

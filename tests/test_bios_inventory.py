from hashlib import md5
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from embercade.bios_inventory import (
    build_bios_inventory,
    load_batocera_bios_requirements,
    render_documentation,
)


def _digest(value: bytes) -> str:
    return md5(value).hexdigest()


class BiosInventoryTests(unittest.TestCase):
    def _source(self) -> str:
        return f'''systems = {{
            "ps3": {{"name": "PlayStation 3", "biosFiles": [
                {{"md5": "{_digest(b'good')}", "file": "bios/exact.bin"}},
                {{"md5": "{_digest(b'expected')}", "file": "bios/mismatch.bin"}},
                {{"md5": "", "file": "bios/path only.bin"}},
                {{"md5": "{_digest(b'missing')}", "file": "bios/missing.bin"}},
                {{"md5": "{_digest(b'alternative')}", "file": "bios/primary.bin",
                 "alternatives": ["bios/alternative.bin"]}},
                {{"md5": "{_digest(b'case')}", "file": "bios/Case.bin"}},
                {{"md5": "{_digest(b'wrong')}", "file": "bios/sub/wrong.bin"}},
                {{"md5": "", "file": "bios/optional.bin", "optional": True}},
                {{"md5": "", "file": "bios/archive.zip"}},
                {{"md5": "{_digest(b'zip member')}", "file": "bios/archive.zip",
                 "zippedFile": "member.rom"}},
                {{"md5": "{_digest(b'spaced')}", "file": "bios/space dir/firmware.bin"}}
            ]}},
            "nes": {{"name": "NES", "biosFiles": [
                {{"md5": "", "file": "bios/nes-present.bin"}}
            ]}},
            "triforce": {{"name": "Triforce", "biosFiles": [
                {{"md5": "{_digest(b'outside')}",
                 "file": "saves/dolphin-emu/Triforce/segaboot.gcm"}}
            ]}}
        }}'''

    @staticmethod
    def _rom_inventory():
        return {
            "systems": [
                {"system": "ps3", "content_status": "ROM_PRESENT"},
                {"system": "nes", "content_status": "COMPANION_ONLY"},
                {"system": "empty", "content_status": "EMPTY"},
            ]
        }

    @staticmethod
    def _row(inventory, source_path: str, zipped_file: str | None = None):
        return next(
            row
            for row in inventory["requirements"]
            if row["source_path"] == source_path and row["zipped_file"] == zipped_file
        )

    def test_hash_path_zip_and_alternative_matches_are_targeted(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "BIOS root with spaces"
            (root / "space dir").mkdir(parents=True)
            (root / "exact.bin").write_bytes(b"good")
            (root / "mismatch.bin").write_bytes(b"not expected")
            (root / "path only.bin").write_bytes(b"anything")
            (root / "alternative.bin").write_bytes(b"alternative")
            (root / "space dir/firmware.bin").write_bytes(b"spaced")
            with zipfile.ZipFile(root / "archive.zip", "w") as archive:
                archive.writestr("member.rom", b"zip member")

            inventory = build_bios_inventory(
                root,
                load_batocera_bios_requirements(self._source()),
                self._rom_inventory(),
            )

            self.assertEqual(self._row(inventory, "bios/exact.bin")["status"], "HASH_MATCH")
            self.assertEqual(
                self._row(inventory, "bios/mismatch.bin")["status"], "HASH_MISMATCH"
            )
            self.assertEqual(
                self._row(inventory, "bios/path only.bin")["status"], "PATH_MATCH"
            )
            self.assertEqual(
                self._row(inventory, "bios/primary.bin")["status"], "ALTERNATIVE_MATCH"
            )
            self.assertEqual(
                self._row(inventory, "bios/archive.zip", "member.rom")["status"],
                "HASH_MATCH",
            )
            self.assertGreater(inventory["summary"]["hashes_performed"], 0)

    def test_missing_optional_case_wrong_location_unknown_and_unreferenced(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "bios"
            (root / "elsewhere").mkdir(parents=True)
            (root / "case.bin").write_bytes(b"case")
            (root / "elsewhere/wrong.bin").write_bytes(b"wrong")
            (root / "extra.dat").write_bytes(b"extra")

            inventory = build_bios_inventory(
                root,
                load_batocera_bios_requirements(self._source()),
                self._rom_inventory(),
            )

            self.assertEqual(self._row(inventory, "bios/missing.bin")["status"], "MISSING")
            self.assertEqual(
                self._row(inventory, "bios/optional.bin")["status"], "OPTIONAL_MISSING"
            )
            case_row = self._row(inventory, "bios/Case.bin")
            self.assertEqual(case_row["status"], "CASE_MISMATCH")
            self.assertEqual(case_row["actual_hash"], _digest(b"case"))
            self.assertIn("content hash matches", case_row["diagnostic"])
            self.assertEqual(
                self._row(inventory, "bios/sub/wrong.bin")["status"], "WRONG_LOCATION"
            )
            self.assertEqual(
                self._row(
                    inventory,
                    "saves/dolphin-emu/Triforce/segaboot.gcm",
                )["status"],
                "UNKNOWN",
            )
            self.assertIn("extra.dat", inventory["unreferenced"]["relative_paths"])

    def test_only_rom_present_systems_are_summarized_and_root_is_not_mutated(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "bios"
            root.mkdir()
            file = root / "nes-present.bin"
            file.write_bytes(b"unchanged")
            before = (file.read_bytes(), file.stat().st_mtime_ns)

            inventory = build_bios_inventory(
                root,
                load_batocera_bios_requirements(self._source()),
                self._rom_inventory(),
            )
            documentation = render_documentation(inventory)

            self.assertEqual([row["system"] for row in inventory["systems"]], ["ps3"])
            self.assertEqual(before, (file.read_bytes(), file.stat().st_mtime_ns))
            self.assertNotIn(str(root), documentation)
            self.assertIn("PlayStation 3", json.dumps(inventory))


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.rom_inventory import (
    inventory_rom_root,
    load_batocera_systems,
    render_documentation,
)


SYSTEMS_XML = """<?xml version="1.0"?>
<systemList>
  <system>
    <fullname>Nintendo Entertainment System</fullname><name>nes</name>
    <path>/userdata/roms/nes</path><extension>.7z .nes .zip</extension>
    <emulators><emulator name="libretro"><cores><core default="true">nestopia</core></cores></emulator></emulators>
  </system>
  <system>
    <fullname>PlayStation 3</fullname><name>ps3</name>
    <path>/userdata/roms/ps3</path><extension>.iso .ps3 .psn</extension>
    <emulators><emulator name="rpcs3"><cores><core default="true">rpcs3</core></cores></emulator></emulators>
  </system>
  <system>
    <fullname>DOS</fullname><name>dos</name>
    <path>/userdata/roms/dos</path><extension>.dos .m3u .zip</extension>
  </system>
  <system><fullname>Shared A</fullname><name>shared-a</name><path>/userdata/roms/shared</path><extension>.rom</extension></system>
  <system><fullname>Shared B</fullname><name>shared-b</name><path>/userdata/roms/shared</path><extension>.rom</extension></system>
</systemList>
"""


class RomInventoryTests(unittest.TestCase):
    @staticmethod
    def _systems(root: Path):
        definition = root / "es systems.cfg"
        definition.write_text(SYSTEMS_XML, encoding="utf-8")
        return load_batocera_systems(definition)

    @staticmethod
    def _row(inventory, directory: str):
        return next(row for row in inventory["systems"] if row["directory"] == directory)

    def test_exact_unknown_recognized_mixed_case_and_nested_directories(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "ROM root with spaces"
            nested = roms / "nes/sub directory"
            nested.mkdir(parents=True)
            (nested / "GAME.NES").write_bytes(b"rom")
            (nested / "readme.TXT").write_bytes(b"notes")
            unknown = roms / "mystery system"
            unknown.mkdir()
            (unknown / "unknown.xyz").write_bytes(b"unknown")

            inventory = inventory_rom_root(roms, self._systems(root))
            nes = self._row(inventory, "nes")
            mystery = self._row(inventory, "mystery system")

            self.assertEqual(nes["match"], "EXACT")
            self.assertEqual(nes["extensions"], {".nes": 1, ".txt": 1})
            self.assertEqual(nes["extension_match"], "MIXED")
            self.assertEqual(nes["recognized_count"], 1)
            self.assertEqual(nes["unrecognized_count"], 1)
            self.assertEqual(nes["directory_count"], 1)
            self.assertEqual(nes["content_status"], "ROM_PRESENT")
            self.assertEqual(mystery["match"], "UNKNOWN")
            self.assertEqual(mystery["content_status"], "UNCLASSIFIED_CONTENT")

    def test_alias_ambiguous_empty_and_directories_only(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            (roms / "Nintendo NES").mkdir(parents=True)
            (roms / "shared").mkdir()
            (roms / "arcade").mkdir()
            (roms / "empty").mkdir()
            (roms / "folders only/child").mkdir(parents=True)
            (roms / "dos").mkdir()
            (roms / "dos/info.txt").write_text("information", encoding="utf-8")

            inventory = inventory_rom_root(
                roms,
                self._systems(root),
                aliases={"Nintendo NES": "nes"},
                ambiguous_aliases={"arcade": ("shared-a", "shared-b")},
            )

            self.assertEqual(self._row(inventory, "Nintendo NES")["match"], "ALIAS")
            self.assertEqual(self._row(inventory, "shared")["match"], "AMBIGUOUS")
            self.assertEqual(
                self._row(inventory, "arcade")["candidates"], ["shared-a", "shared-b"]
            )
            self.assertEqual(self._row(inventory, "empty")["content_status"], "EMPTY")
            self.assertEqual(
                self._row(inventory, "folders only")["content_status"],
                "UNCLASSIFIED_CONTENT",
            )
            self.assertEqual(
                self._row(inventory, "dos")["content_status"], "COMPANION_ONLY"
            )

    def test_m3u_and_ps3_directory_layout_are_metadata_only_markers(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            dos = roms / "dos"
            dos.mkdir(parents=True)
            (dos / "Multi Disc.m3u").write_text("disc1.cue\n", encoding="utf-8")
            ps3_file = roms / "ps3/Game.ps3/PS3_GAME/USRDIR/EBOOT.BIN"
            ps3_file.parent.mkdir(parents=True)
            ps3_file.write_bytes(b"synthetic")

            inventory = inventory_rom_root(roms, self._systems(root))
            dos_row = self._row(inventory, "dos")
            ps3_row = self._row(inventory, "ps3")

            self.assertEqual(dos_row["special_layouts"]["multi_disc_m3u_files"], 1)
            self.assertEqual(dos_row["recognized_count"], 1)
            self.assertEqual(ps3_row["special_layouts"]["ps3_game_directories"], 1)
            self.assertEqual(ps3_row["content_status"], "SPECIAL_LAYOUT_PRESENT")

    def test_scan_does_not_modify_collection_and_docs_hide_absolute_root(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "private ROM root"
            game = roms / "nes/Game.nes"
            game.parent.mkdir(parents=True)
            game.write_bytes(b"unchanged bytes")
            before = game.read_bytes()
            before_mtime = game.stat().st_mtime_ns

            inventory = inventory_rom_root(roms, self._systems(root))
            documentation = render_documentation(inventory)

            self.assertEqual(game.read_bytes(), before)
            self.assertEqual(game.stat().st_mtime_ns, before_mtime)
            self.assertNotIn(str(roms), documentation)
            self.assertIn("ROM_ROOT/nes", documentation)
            self.assertIn("## Folder occupancy", documentation)
            self.assertIn("### Directories with unclassified content", documentation)
            self.assertIn(
                "Directories containing only companion files: 0", documentation
            )
            self.assertIn(
                "Directories with unclassified content: 0",
                documentation,
            )


if __name__ == "__main__":
    unittest.main()

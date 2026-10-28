from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import unittest
from unittest.mock import patch

from embercade.bios_inventory import BATOCERA_COMMIT
from embercade.compatibility import (
    CompatibilityError,
    E2E_VALIDATED_SYSTEMS,
    build_compatibility_matrix,
    render_documentation,
    write_documentation,
    write_matrix,
)
from embercade.executables import EmulatorProvider, ProviderType


class CompatibilityMatrixTests(unittest.TestCase):
    def test_manual_e2e_ledger_contains_user_confirmed_wii_and_other_routes(self) -> None:
        self.assertTrue(
            {
                "3ds",
                "amiga1200",
                "c64",
                "dos",
                "jaguar",
                "mame",
                "n64",
                "nds",
                "psp",
                "wii",
                "wiiu",
                "xbox360",
            }
            <= E2E_VALIDATED_SYSTEMS
        )

    def test_nds_route_records_the_proven_desktop_core_override(self) -> None:
        from embercade.compatibility import IMPLEMENTED_LAUNCH_PATHS

        self.assertEqual(
            IMPLEMENTED_LAUNCH_PATHS["nds"]["effective_core"], "melondsds"
        )

    @staticmethod
    def _rom_rows():
        def row(system, emulator, core, *, directory=None, status="ROM_PRESENT"):
            return {
                "system": system,
                "fullname": system,
                "directory": directory or system,
                "match": "EXACT",
                "content_status": status,
                "default_emulator": emulator,
                "default_core": core,
            }

        return [
            row("nes", "libretro", "fceumm", directory="local-private-folder"),
            row("gamecube", "dolphin", "dolphin"),
            row("wii", "dolphin", "dolphin"),
            row("missingcore", "libretro", "absent"),
            row("3ds", "azahar", "azahar"),
            row("psp", "ppsspp", "ppsspp"),
            row("n64", "mupen64plus", "glide64mk2"),
            row("jaguar", "bigpemu", "bigpemu"),
            row("missingstandalone", "bigpemu", "bigpemu"),
            row("smallport", "libretro", "snes9x"),
            row("biosless", "libretro", "snes9x"),
            row("ambiguous", "libretro", "snes9x", directory="one"),
            row("ambiguous", "dolphin", "dolphin", directory="two"),
            row("ports", "sh", "sh"),
            row("ignored", "libretro", "snes9x", status="COMPANION_ONLY"),
        ]

    @staticmethod
    def _bios_rows():
        rows = []
        for system in (
            "nes",
            "gamecube",
            "wii",
            "missingcore",
            "3ds",
            "psp",
            "n64",
            "jaguar",
            "missingstandalone",
            "smallport",
            "ambiguous",
            "ports",
        ):
            rows.append(
                {
                    "system": system,
                    "requirements_total": 0,
                    "required_matched": 0,
                    "required_missing": 0,
                    "hash_mismatches": 0,
                    "case_mismatches": 0,
                    "wrong_location": 0,
                    "unknown_requirements": 0,
                }
            )
        rows.append(
            {
                "system": "biosless",
                "requirements_total": 1,
                "required_matched": 0,
                "required_missing": 1,
                "hash_mismatches": 0,
                "case_mismatches": 0,
                "wrong_location": 0,
                "unknown_requirements": 0,
            }
        )
        return rows

    def _inventories(self):
        rom = {"batocera_commit": BATOCERA_COMMIT, "systems": self._rom_rows()}
        bios = {"batocera_commit": BATOCERA_COMMIT, "systems": self._bios_rows()}
        cores = {
            "batocera_cores": [
                {
                    "batocera_name": name,
                    "path": f"/host cores/{name}_libretro.so",
                    "probably_loadable": True,
                    "alias": None,
                }
                for name in (
                    "azahar",
                    "fceumm",
                    "nestopia",
                    "mupen64plus-next",
                    "ppsspp",
                    "snes9x",
                    "virtualjaguar",
                )
            ]
        }
        return rom, bios, cores

    @staticmethod
    def _row(matrix, system):
        return next(row for row in matrix["systems"] if row["system"] == system)

    @staticmethod
    def _dry_runs(*systems):
        cores = {
            "nes": "nestopia",
            "n64": "mupen64plus-next",
            "jaguar": "virtualjaguar",
        }
        return {
            "batocera_commit": BATOCERA_COMMIT,
            "host_retroarch_profile_unchanged": True,
            "summary": {"systems": len(systems), "successful": len(systems)},
            "systems": [
                {
                    "system": system,
                    "emulator": "libretro",
                    "core": cores.get(system, "snes9x"),
                    "core_path": f"/host cores/{cores.get(system, 'snes9x')}_libretro.so",
                    "retroarch_config": "/isolated/retroarchcustom.cfg",
                    "controller_arguments_complete": True,
                    "launcher_exit_code": 0,
                }
                for system in systems
            ],
        }

    @staticmethod
    def _dolphin_dry_runs():
        return {
            "batocera_commit": BATOCERA_COMMIT,
            "host_profiles_unchanged": True,
            "systems": [
                {
                    "system": "wii",
                    "emulator": "dolphin",
                    "host_binary": "/host/bin/dolphin-emu",
                    "config_root": "/isolated/config/dolphin-emu",
                    "nand_root": "/isolated/saves/dolphin-emu/Wii",
                    "controller_arguments_complete": True,
                    "launcher_exit_code": 0,
                    "special_controller_validation": "PENDING",
                }
            ],
        }

    def test_status_precedence_aggregation_and_no_process_execution(self) -> None:
        with TemporaryDirectory() as directory:
            bin_dir = Path(directory) / "bin"
            bin_dir.mkdir()
            for command in ("retroarch", "dolphin-emu", "sh"):
                path = bin_dir / command
                path.write_text("never executed\n", encoding="utf-8")
                path.chmod(0o755)
            rom, bios, cores = self._inventories()
            matrix = build_compatibility_matrix(
                rom,
                bios,
                cores,
                environment={"PATH": str(bin_dir)},
                e2e_systems=frozenset({"nes"}),
                libretro_dry_runs=self._dry_runs(),
            )

        self.assertEqual(self._row(matrix, "nes")["result_status"], "READY")
        self.assertEqual(
            self._row(matrix, "gamecube")["result_status"], "EMBERCADE_PORT_MISSING"
        )
        self.assertEqual(self._row(matrix, "wii")["result_status"], "EMBERCADE_PORT_MISSING")
        self.assertEqual(self._row(matrix, "missingcore")["result_status"], "CORE_MISSING")
        self.assertEqual(
            self._row(matrix, "3ds")["result_status"], "EMBERCADE_PORT_MISSING"
        )
        self.assertEqual(
            self._row(matrix, "3ds")["embercade_launch"]["effective_emulator"],
            "libretro",
        )
        self.assertEqual(
            self._row(matrix, "3ds")["embercade_launch"]["effective_core"],
            "azahar",
        )
        self.assertEqual(
            self._row(matrix, "psp")["result_status"], "EMBERCADE_PORT_MISSING"
        )
        self.assertEqual(
            self._row(matrix, "psp")["embercade_launch"]["effective_emulator"],
            "libretro",
        )
        self.assertEqual(
            self._row(matrix, "psp")["embercade_launch"]["effective_core"],
            "ppsspp",
        )
        for system, core in (("n64", "mupen64plus-next"), ("jaguar", "virtualjaguar")):
            row = self._row(matrix, system)
            self.assertEqual(row["result_status"], "EMBERCADE_PORT_MISSING")
            self.assertEqual(row["embercade_launch"]["effective_emulator"], "libretro")
            self.assertEqual(row["embercade_launch"]["effective_core"], core)
            self.assertTrue(row["embercade_launch"]["effective_core_status"]["present"])
        self.assertEqual(
            self._row(matrix, "missingstandalone")["result_status"],
            "EMULATOR_MISSING",
        )
        self.assertEqual(
            self._row(matrix, "smallport")["result_status"], "EMBERCADE_PORT_MISSING"
        )
        self.assertEqual(self._row(matrix, "biosless")["result_status"], "BIOS_MISSING")
        self.assertEqual(self._row(matrix, "ambiguous")["result_status"], "AMBIGUOUS")
        self.assertEqual(self._row(matrix, "ports")["result_status"], "UNSUPPORTED")
        self.assertEqual(len(self._row(matrix, "ambiguous")["collections"]), 2)
        self.assertNotIn("ignored", {row["system"] for row in matrix["systems"]})

    def test_rejects_inventory_from_another_batocera_commit(self) -> None:
        rom, bios, cores = self._inventories()
        rom["batocera_commit"] = "wrong"
        with self.assertRaisesRegex(CompatibilityError, "expected"):
            build_compatibility_matrix(rom, bios, cores, environment={"PATH": ""})

    def test_reports_are_reproducible_path_neutral_and_do_not_mutate_inputs(self) -> None:
        rom, bios, cores = self._inventories()
        before = json.dumps((rom, bios, cores), sort_keys=True)
        matrix = build_compatibility_matrix(
            rom, bios, cores, environment={"PATH": os.defpath}, e2e_systems=frozenset()
        )
        documentation = render_documentation(matrix)
        self.assertNotIn("/host cores", documentation)
        self.assertNotIn("local-private-folder", documentation)
        self.assertIn("Batocera reference", documentation)
        self.assertEqual(before, json.dumps((rom, bios, cores), sort_keys=True))

        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_matrix(root / "matrix.json", matrix)
            write_documentation(root / "matrix.md", matrix)
            self.assertEqual(
                json.loads((root / "matrix.json").read_text(encoding="utf-8"))["schema_version"],
                1,
            )
            self.assertEqual((root / "matrix.md").read_text(encoding="utf-8"), documentation)

    @patch("embercade.executables.shutil.which", return_value="/fixture/retroarch")
    def test_successful_libretro_dry_run_promotes_only_to_untested(self, _which) -> None:
        rom, bios, cores = self._inventories()
        matrix = build_compatibility_matrix(
            rom,
            bios,
            cores,
            environment={"PATH": os.defpath},
            e2e_systems=frozenset(),
            libretro_dry_runs=self._dry_runs("nes"),
        )
        row = self._row(matrix, "nes")
        self.assertEqual(row["result_status"], "UNTESTED")
        self.assertTrue(row["embercade_launch"]["implemented"])
        self.assertTrue(row["embercade_launch"]["dry_run_validated"])

    @patch("embercade.executables.shutil.which", return_value="/fixture/retroarch")
    def test_desktop_core_overrides_do_not_require_missing_batocera_standalones(self, _which) -> None:
        rom, bios, cores = self._inventories()
        matrix = build_compatibility_matrix(
            rom,
            bios,
            cores,
            environment={"PATH": os.defpath},
            e2e_systems=frozenset(),
            libretro_dry_runs=self._dry_runs("n64", "jaguar"),
        )
        for system in ("n64", "jaguar"):
            row = self._row(matrix, system)
            self.assertEqual(row["result_status"], "UNTESTED")
            self.assertTrue(row["embercade_launch"]["dry_run_validated"])

    def test_wiiu_core_and_xenia_appimage_are_effective_desktop_providers(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            retroarch = bin_dir / "retroarch"
            retroarch.write_text("never executed\n", encoding="utf-8")
            retroarch.chmod(0o755)
            cemu = root / "cores/cemu_libretro.so"
            cemu.parent.mkdir()
            cemu.write_bytes(b"\x7fELFcore")
            appimage = root / "providers/Xenia Edge.AppImage"
            appimage.parent.mkdir()
            appimage.write_text("never executed\n", encoding="utf-8")
            appimage.chmod(0o755)
            rom, bios, cores = self._inventories()
            rom["systems"].extend(
                [
                    {
                        "system": "wiiu",
                        "fullname": "Wii U",
                        "directory": "wiiu",
                        "match": "EXACT",
                        "content_status": "ROM_PRESENT",
                        "default_emulator": "cemu",
                        "default_core": "cemu",
                    },
                    {
                        "system": "xbox360",
                        "fullname": "Xbox 360",
                        "directory": "xbox360",
                        "match": "EXACT",
                        "content_status": "ROM_PRESENT",
                        "default_emulator": "xenia-edge",
                        "default_core": "xenia-edge",
                    },
                ]
            )
            for system in ("wiiu", "xbox360"):
                bios["systems"].append(
                    {
                        "system": system,
                        "requirements_total": 0,
                        "required_matched": 0,
                        "required_missing": 0,
                        "hash_mismatches": 0,
                        "case_mismatches": 0,
                        "wrong_location": 0,
                        "unknown_requirements": 0,
                    }
                )
            cores["installed_cores"] = [
                {"logical_name": "cemu", "path": str(cemu)}
            ]

            matrix = build_compatibility_matrix(
                rom,
                bios,
                cores,
                environment={"PATH": str(bin_dir)},
                emulator_providers={
                    "xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(appimage))
                },
                e2e_systems=frozenset(),
            )

        wiiu = self._row(matrix, "wiiu")
        self.assertEqual(wiiu["embercade_launch"]["effective_emulator"], "libretro")
        self.assertEqual(wiiu["embercade_launch"]["effective_core"], "cemu")
        self.assertTrue(wiiu["embercade_launch"]["effective_core_status"]["present"])
        self.assertEqual(wiiu["result_status"], "EMBERCADE_PORT_MISSING")
        xbox360 = self._row(matrix, "xbox360")
        provider = xbox360["embercade_launch"]["effective_emulator_status"]
        self.assertTrue(provider["present"])
        self.assertEqual(provider["provider"], "appimage")
        self.assertEqual(provider["path"], str(appimage))
        self.assertEqual(xbox360["result_status"], "EMBERCADE_PORT_MISSING")

    def test_rejects_untrusted_libretro_dry_run_report(self) -> None:
        rom, bios, cores = self._inventories()
        report = self._dry_runs("nes")
        report["host_retroarch_profile_unchanged"] = False
        with self.assertRaisesRegex(CompatibilityError, "host-profile"):
            build_compatibility_matrix(
                rom,
                bios,
                cores,
                environment={"PATH": os.defpath},
                libretro_dry_runs=report,
            )

    def test_wii_dry_run_cannot_substitute_for_the_manual_e2e_ledger(self) -> None:
        with TemporaryDirectory() as directory:
            bin_dir = Path(directory) / "bin"
            bin_dir.mkdir()
            dolphin = bin_dir / "dolphin-emu"
            dolphin.write_text("never executed\n", encoding="utf-8")
            dolphin.chmod(0o755)
            rom, bios, cores = self._inventories()
            matrix = build_compatibility_matrix(
                rom,
                bios,
                cores,
                environment={"PATH": str(bin_dir)},
                e2e_systems=frozenset(),
                dolphin_dry_runs=self._dolphin_dry_runs(),
            )

        row = self._row(matrix, "wii")
        self.assertEqual(row["result_status"], "UNTESTED")
        self.assertTrue(row["embercade_launch"]["dry_run_validated"])
        self.assertEqual(
            row["embercade_launch"]["capabilities"]["special_controller_validation"],
            "DOLPHINBAR_NUNCHUK_VALIDATED",
        )
        self.assertIn("special controller validation", render_documentation(matrix))


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from io import StringIO
import os
import tomllib
import unittest
from test_imports import elf, XENIA_METADATA

from embercade.setup_flow import (
    SetupError,
    choose_source_directory,
    configure,
    detect_xenia_edge,
    recommended_xenia_directory,
    interactive_setup,
    update_config_text,
    validate_provider_path,
    write_config_atomic,
)


class SetupFlowTests(unittest.TestCase):
    def setUp(self):
        metadata = patch("embercade.imports._provider_metadata", return_value=XENIA_METADATA)
        metadata.start()
        self.addCleanup(metadata.stop)

    def test_source_selection_accepts_detected_or_skips(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            output = StringIO()
            self.assertEqual(choose_source_directory(
                label="RetroArch core", suggested=path, question="unused",
                input_function=lambda _: "1", output=output,
            ), path)
            self.assertIn(str(path), output.getvalue())
            self.assertIsNone(choose_source_directory(
                label="Provider/AppImage", suggested=path, question="unused",
                input_function=lambda _: "3", output=StringIO(),
            ))

    def test_source_selection_reprompts_invalid_manual_directory(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            chosen = root / "chosen"
            chosen.mkdir()
            answers = iter(("y", str(root / "missing"), str(chosen)))
            output = StringIO()
            self.assertEqual(choose_source_directory(
                label="Provider/AppImage", suggested=None, question="Have AppImages?",
                input_function=lambda _: next(answers), output=output,
            ), chosen)
            self.assertIn("does not exist", output.getvalue())

    def test_fresh_config_with_paths_containing_spaces_and_provider(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "ROM files"
            bios = root / "BIOS files"
            provider = root / "Providers" / "Xenia Edge.AppImage"
            roms.mkdir()
            bios.mkdir()
            provider.parent.mkdir()
            provider.write_bytes(elf(appimage=True))
            provider.chmod(0o700)
            config = root / "config" / "embercade.toml"

            result = configure(
                config,
                roms_value=str(roms),
                bios_value=str(bios),
                xenia_value=str(provider),
            )

            parsed = tomllib.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(parsed["paths"]["roms"], str(roms))
            self.assertEqual(parsed["paths"]["bios"], str(bios))
            self.assertEqual(parsed["emulators"]["xenia-edge"]["executable"], str(provider))
            self.assertEqual(result.xenia_edge, provider)
            self.assertEqual(parsed["controller"]["exit_hotkey"], "back-start")
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)

    def test_ppsspp_source_is_referenced_read_only_and_survives_reconfigure(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios, assets = root / "roms", root / "bios", root / "official PSP assets"
            for path in (roms, bios, assets / "lang", assets / "flash0"):
                path.mkdir(parents=True, exist_ok=True)
            (assets / "ppge_atlas.zim").write_bytes(b"atlas")
            config = root / "embercade.toml"
            configure(config, roms_value=str(roms), bios_value=str(bios),
                      ppsspp_assets_value=str(assets))
            before = (assets / "ppge_atlas.zim").read_bytes()
            configure(config, roms_value=str(roms), bios_value=str(bios))
            self.assertEqual(tomllib.loads(config.read_text())["libretro"]["ppsspp_assets"], str(assets))
            self.assertEqual((assets / "ppge_atlas.zim").read_bytes(), before)

    def test_incomplete_ppsspp_source_does_not_change_existing_config(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "embercade.toml"
            config.write_text("# existing settings\n")
            with self.assertRaisesRegex(SetupError, "ppge_atlas.zim"):
                configure(config, roms_value=directory, bios_value=directory,
                          ppsspp_assets_value=directory)
            self.assertEqual(config.read_text(), "# existing settings\n")

    def test_existing_unknown_values_and_comments_are_preserved(self) -> None:
        original = "# keep me\n[custom]\nanswer = 42\n\n[paths]\nroms = \"old\"\n"
        result = update_config_text(
            original,
            roms=Path("/new roms"),
            bios=Path("/new bios"),
            xenia_edge=None,
        )
        self.assertIn("# keep me", result)
        self.assertIn("answer = 42", result)
        self.assertEqual(tomllib.loads(result)["custom"]["answer"], 42)

    def test_invalid_collection_paths_do_not_replace_existing_config(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "embercade.toml"
            original = "[custom]\nkept = true\n"
            config.write_text(original, encoding="utf-8")
            with self.assertRaises(SetupError):
                configure(
                    config,
                    roms_value=str(root / "missing"),
                    bios_value=str(root),
                )
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_invalid_bios_path_does_not_replace_existing_config(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            roms.mkdir()
            config = root / "embercade.toml"
            original = "[custom]\nkept = true\n"
            config.write_text(original, encoding="utf-8")
            with self.assertRaises(SetupError):
                configure(
                    config,
                    roms_value=str(roms),
                    bios_value=str(root / "missing-bios"),
                )
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_repeated_setup_is_idempotent_and_keeps_unrelated_values(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            bios = root / "bios"
            roms.mkdir()
            bios.mkdir()
            config = root / "embercade.toml"
            config.write_text("[custom]\nkept = true\n", encoding="utf-8")
            for _ in range(2):
                configure(config, roms_value=str(roms), bios_value=str(bios))
            before = config.stat()
            configure(config, roms_value=str(roms), bios_value=str(bios))
            self.assertEqual(config.stat().st_ino, before.st_ino)
            self.assertEqual(config.stat().st_mtime_ns, before.st_mtime_ns)
            parsed = tomllib.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(parsed["paths"], {"roms": str(roms), "bios": str(bios)})
            self.assertTrue(parsed["custom"]["kept"])

    def test_atomic_write_failure_preserves_existing_config(self) -> None:
        with TemporaryDirectory() as directory:
            config = Path(directory) / "embercade.toml"
            config.write_text("old\n", encoding="utf-8")
            with patch("embercade.setup_flow.os.replace", side_effect=OSError("test failure")):
                with self.assertRaises(OSError):
                    write_config_atomic(config, "new\n")
            self.assertEqual(config.read_text(encoding="utf-8"), "old\n")

    def test_symlinked_config_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("unchanged", encoding="utf-8")
            config = root / "embercade.toml"
            config.symlink_to(target)
            with self.assertRaises(SetupError):
                write_config_atomic(config, "replacement")
            self.assertEqual(target.read_text(encoding="utf-8"), "unchanged")

    def test_recommended_provider_directory_and_spaces_are_detected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = {
                "HOME": str(root / "home"),
                "XDG_DATA_HOME": str(root / "Data with spaces"),
                "PATH": "",
            }
            provider_directory = recommended_xenia_directory(environment)
            provider_directory.mkdir(parents=True)
            provider = provider_directory / "Xenia Edge Linux.AppImage"
            provider.write_bytes(elf(appimage=True))
            provider.chmod(0o700)
            self.assertEqual(detect_xenia_edge({}, environment), provider)

    def test_provider_must_be_regular_executable_plausible_appimage(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = root / "Xenia.AppImage"
            invalid.write_bytes(b"not an ELF")
            invalid.chmod(0o700)
            with self.assertRaisesRegex(SetupError, "truncated ELF"):
                validate_provider_path(str(invalid))

            valid = root / "Xenia Edge.AppImage"
            valid.write_bytes(elf(appimage=True))
            valid.chmod(0o700)
            link = root / "Linked.AppImage"
            link.symlink_to(valid)
            with self.assertRaisesRegex(SetupError, "unavailable"):
                validate_provider_path(str(link))

    def test_missing_provider_remains_optional(self) -> None:
        with TemporaryDirectory() as directory:
            environment = {"HOME": directory, "XDG_DATA_HOME": directory, "PATH": ""}
            self.assertIsNone(detect_xenia_edge({}, environment))

    def test_existing_configured_provider_precedes_recommended_directory(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            configured = root / "Configured Xenia.AppImage"
            configured.write_bytes(elf(appimage=True))
            configured.chmod(0o700)
            environment = {"HOME": str(root), "XDG_DATA_HOME": str(root / "data"), "PATH": ""}
            recommended = recommended_xenia_directory(environment)
            recommended.mkdir(parents=True)
            other = recommended / "Xenia.AppImage"
            other.write_bytes(elf(appimage=True) + b"other")
            other.chmod(0o700)
            config = {"emulators": {"xenia-edge": {"executable": str(configured)}}}
            self.assertEqual(detect_xenia_edge(config, environment), configured)

    def test_invalid_override_is_not_masked_by_managed_discovery(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = {"HOME": directory, "PATH": ""}
            managed = recommended_xenia_directory(environment)
            managed.mkdir(parents=True)
            file = managed / "renamed.appimage"
            file.write_bytes(elf(appimage=True))
            file.chmod(0o700)
            config = {"executables": {"xenia-edge": str(root / "missing.AppImage")}}
            with self.assertRaisesRegex(SetupError, "Configured.*needs attention"):
                detect_xenia_edge(config, environment)

    def test_ambiguous_managed_discovery_does_not_guess(self):
        with TemporaryDirectory() as directory:
            environment = {"HOME": directory, "PATH": ""}
            managed = recommended_xenia_directory(environment)
            managed.mkdir(parents=True)
            for index in range(2):
                file = managed / f"{index}.appimage"
                file.write_bytes(elf(appimage=True) + bytes([index]))
                file.chmod(0o700)
            with self.assertRaisesRegex(SetupError, "Multiple different"):
                detect_xenia_edge({}, environment)

    def test_damaged_provider_does_not_prevent_setup_or_erase_path(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "embercade.toml"
            original = '[emulators.xenia-edge]\nprovider="appimage"\nexecutable="/missing/Xenia.AppImage"\n'
            config.write_text(original)
            result = configure(config, roms_value=directory, bios_value=directory,
                               environment={"HOME": directory, "PATH": ""})
            self.assertIsNone(result.xenia_edge)
            self.assertIn("needs attention", result.provider_notice)
            self.assertIn(original, config.read_text())

    def test_new_selection_cannot_silently_shadow_explicit_override(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "embercade.toml"
            original = '[executables]\nxenia-edge="/old/Xenia.AppImage"\n'
            config.write_text(original)
            candidate = root / "valid.AppImage"
            candidate.write_bytes(elf(appimage=True))
            candidate.chmod(0o700)
            with self.assertRaisesRegex(SetupError, "override has priority"):
                configure(config, roms_value=directory, bios_value=directory,
                          xenia_value=str(candidate))
            self.assertEqual(config.read_text(), original)

    def test_invalid_provider_type_has_clear_preserved_setting_notice(self):
        with TemporaryDirectory() as directory:
            config = Path(directory) / "embercade.toml"
            original = '[emulators.xenia-edge]\nprovider="typo"\nexecutable="/bad/AppImage"\n'
            config.write_text(original)
            result = configure(config, roms_value=directory, bios_value=directory,
                               environment={"HOME": directory, "PATH": ""})
            self.assertIn("needs attention", result.provider_notice)
            self.assertIn(original, config.read_text())

    def test_exit_hotkey_presets_are_persisted_and_validated(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            bios = root / "bios"
            roms.mkdir()
            bios.mkdir()
            config = root / "embercade.toml"
            result = configure(
                config,
                roms_value=str(roms),
                bios_value=str(bios),
                exit_hotkey="guide-start",
            )
            self.assertEqual(result.exit_hotkey, "guide-start")
            self.assertEqual(tomllib.loads(config.read_text())["controller"]["exit_hotkey"], "guide-start")
            with self.assertRaisesRegex(SetupError, "unknown exit-hotkey"):
                configure(
                    config,
                    roms_value=str(roms),
                    bios_value=str(bios),
                    exit_hotkey="custom",
                )

    def test_interactive_setup_offers_both_tested_exit_presets(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            bios = root / "bios"
            roms.mkdir()
            bios.mkdir()
            answers = iter((str(roms), str(bios), "2", ""))
            result = interactive_setup(
                root / "embercade.toml",
                input_function=lambda _prompt: next(answers),
                output=StringIO(),
                environment={"HOME": str(root), "PATH": ""},
            )
            self.assertEqual(result.exit_hotkey, "guide-start")


if __name__ == "__main__":
    unittest.main()

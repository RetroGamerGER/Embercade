from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import tomllib
import unittest
from types import SimpleNamespace

from embercade.cli import _suggest_core_source, main
from embercade.cores import LibretroCoreResolver, SearchDirectory
from embercade.host_requirements import BootstrapPlan, DistroInfo, HostAssessment
from tests.test_imports import elf, XENIA_METADATA
from embercade.imports import ImportResult
from embercade.cli import _print_provider_import


class ProductCliTests(unittest.TestCase):
    def test_suggests_complete_core_collection_not_one_package_core(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            system = root / "system"
            collection = root / "collection"
            managed = root / "managed"
            for path in (system, collection, managed):
                path.mkdir()
            (system / "nestopia_libretro.so").write_bytes(b"core")
            for name in ("nestopia", "snes9x", "mgba"):
                (collection / f"{name}_libretro.so").write_bytes(b"core")
            for name in ("a", "b", "c", "d"):
                (managed / f"{name}_libretro.so").write_bytes(b"core")
            resolver = LibretroCoreResolver(core_directories=(
                SearchDirectory(managed, "embercade-managed", "user", True),
                SearchDirectory(system, "retroarch-user-config", "user", True),
                SearchDirectory(collection, "user-fallback", "user", False),
            ))
            self.assertEqual(_suggest_core_source(resolver), collection)

    def test_unconfigured_default_start_has_setup_hint_without_traceback(self) -> None:
        with TemporaryDirectory() as directory:
            output = StringIO()
            with patch.dict(os.environ, {"HOME": directory}, clear=True), redirect_stderr(output):
                result = main([])
            self.assertEqual(result, 2)
            self.assertIn("embercade setup", output.getvalue())
            self.assertNotIn("Traceback", output.getvalue())

    def test_noninteractive_setup_writes_selected_roots(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "ROMs"
            bios = root / "BIOS"
            roms.mkdir()
            bios.mkdir()
            output = StringIO()
            with (
                patch.dict(os.environ, {"HOME": str(root / "home")}, clear=True),
                redirect_stdout(output),
            ):
                result = main(["setup", "--roms", str(roms), "--bios", str(bios)])
            self.assertEqual(result, 0)
            config = root / "home/.config/embercade/embercade.toml"
            parsed = tomllib.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(parsed["paths"], {"roms": str(roms), "bios": str(bios)})
            self.assertIn("Checking Embercade setup...", output.getvalue())
            self.assertIn("Missing optional components:", output.getvalue())
            self.assertIn("no import folder selected", output.getvalue())

    def test_noninteractive_setup_imports_managed_cores_and_provider(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios, cores, providers = (root / name for name in ("roms", "bios", "cores", "providers"))
            for path in (roms, bios, cores, providers):
                path.mkdir()
            (cores / "nestopia_libretro.so").write_bytes(elf())
            (providers / "xenia_edge_linux.AppImage").write_bytes(elf(appimage=True, symbols=False))
            with (
                patch("embercade.imports._provider_metadata", return_value=XENIA_METADATA),
                patch.dict(os.environ, {"HOME": str(root / "home")}, clear=True),
                redirect_stdout(StringIO()),
            ):
                self.assertEqual(main([
                    "setup", "--roms", str(roms), "--bios", str(bios),
                    "--cores-from", str(cores), "--providers-from", str(providers),
                ]), 0)
            data = root / "home/.local/share/embercade"
            self.assertTrue((data / "cores/nestopia_libretro.so").is_file())
            provider = data / "providers/xenia/xenia_edge_linux.AppImage"
            self.assertTrue(provider.is_file())
            config = tomllib.loads((root / "home/.config/embercade/embercade.toml").read_text())
            self.assertEqual(config["emulators"]["xenia-edge"]["executable"], str(provider))

    def test_setup_uses_selected_psp_assets_and_prepares_xemu_workfiles(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios, assets, xbox = (root / name for name in
                                        ("roms", "bios", "PSP assets", "Xbox files"))
            for path in (roms, bios, assets / "lang", assets / "flash0", xbox):
                path.mkdir(parents=True, exist_ok=True)
            (assets / "ppge_atlas.zim").write_bytes(b"atlas")
            for name in ("Complex_4627.bin", "mcpx_1.0.bin", "eeprom.bin", "xbox_hdd.qcow2"):
                (xbox / name).write_bytes(name.encode())
            original = (xbox / "xbox_hdd.qcow2").read_bytes()
            with (
                patch.dict(os.environ, {"HOME": str(root / "home")}, clear=True),
                redirect_stdout(StringIO()),
            ):
                self.assertEqual(main([
                    "setup", "--roms", str(roms), "--bios", str(bios),
                    "--ppsspp-assets-from", str(assets), "--xemu-files-from", str(xbox),
                ]), 0)
            config = tomllib.loads((root / "home/.config/embercade/embercade.toml").read_text())
            self.assertEqual(config["libretro"]["ppsspp_assets"], str(assets))
            self.assertEqual((root / "home/.local/share/embercade/saves/xbox/xbox_hdd.qcow2").read_bytes(), original)
            self.assertEqual((xbox / "xbox_hdd.qcow2").read_bytes(), original)

    def test_missing_xemu_source_does_not_create_config(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            xbox = root / "incomplete"
            xbox.mkdir()
            (xbox / "eeprom.bin").write_bytes(b"eeprom")
            with (
                patch.dict(os.environ, {"HOME": str(root / "home")}, clear=True),
                redirect_stderr(StringIO()),
                self.assertRaises(SystemExit),
            ):
                main(["setup", "--roms", directory, "--bios", directory,
                      "--xemu-files-from", str(xbox)])
            self.assertFalse((root / "home/.config/embercade/embercade.toml").exists())

    def test_interactive_first_run_can_skip_optional_imports_and_launch(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios = root / "roms", root / "bios"
            roms.mkdir()
            bios.mkdir()
            answers = iter((str(roms), str(bios), "1", "", "3", "n", "n", "n"))
            assessment = HostAssessment(DistroInfo("other", "Other Linux", ()), (), (), ())
            output = StringIO()
            with (
                patch.dict(os.environ, {"HOME": str(root / "home"), "PATH": ""}, clear=True),
                patch("embercade.cli.sys.stdin", SimpleNamespace(isatty=lambda: True)),
                patch("builtins.input", side_effect=lambda _prompt: next(answers)),
                patch("embercade.cli._assess_host", return_value=assessment),
                redirect_stdout(output),
            ):
                self.assertEqual(main(["setup"]), 0)
            self.assertIn("Configuration saved", output.getvalue())
            config = tomllib.loads((root / "home/.config/embercade/embercade.toml").read_text())
            self.assertEqual(config["paths"]["roms"], str(roms))

    def test_interactive_setup_can_choose_different_core_and_provider_folders(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios, detected, chosen, detected_provider, providers = (
                root / name for name in ("roms", "bios", "detected", "chosen", "old-provider", "providers")
            )
            for path in (roms, bios, detected, chosen, detected_provider, providers):
                path.mkdir()
            (detected / "nestopia_libretro.so").write_bytes(elf())
            (chosen / "mgba_libretro.so").write_bytes(elf())
            old_xenia = detected_provider / "xenia_edge_linux.AppImage"
            old_xenia.write_bytes(elf(appimage=True, symbols=False))
            old_xenia.chmod(0o700)
            new_xenia = providers / "xenia_edge_linux.AppImage"
            new_xenia.write_bytes(elf(appimage=True, symbols=False) + b"new")
            new_xenia.chmod(0o700)
            home = root / "home"
            config = home / ".config/embercade/embercade.toml"
            config.parent.mkdir(parents=True)
            config.write_text(f'[emulators.xenia-edge]\nprovider = "appimage"\nexecutable = "{old_xenia}"\n')
            answers = iter((str(roms), str(bios), "1", "", "2", str(chosen), "2", str(providers), "n", "n"))
            assessment = HostAssessment(DistroInfo("other", "Other Linux", ()), (), (), ())
            with (
                patch("embercade.imports._provider_metadata", return_value=XENIA_METADATA),
                patch.dict(os.environ, {"HOME": str(home), "PATH": ""}, clear=True),
                patch("embercade.cli.sys.stdin", SimpleNamespace(isatty=lambda: True)),
                patch("builtins.input", side_effect=lambda _prompt: next(answers)),
                patch("embercade.cli._assess_host", return_value=assessment),
                patch("embercade.cli._suggest_core_source", return_value=detected),
                redirect_stdout(StringIO()),
            ):
                self.assertEqual(main(["setup"]), 0)
            data = home / ".local/share/embercade"
            self.assertTrue((data / "cores/mgba_libretro.so").is_file())
            self.assertFalse((data / "cores/nestopia_libretro.so").exists())
            managed_provider = data / "providers/xenia/xenia_edge_linux.AppImage"
            self.assertEqual(managed_provider.read_bytes(), new_xenia.read_bytes())
            self.assertEqual(tomllib.loads(config.read_text())["emulators"]["xenia-edge"]["executable"], str(managed_provider))

    def test_provider_import_messages_distinguish_safe_outcomes(self):
        outcomes = (
            (ImportResult(0, 0, 0, 0, (), (), ()), "no files found"),
            (ImportResult(1, 0, 0, 0, ("Other.AppImage: unsupported provider",), (), ()), "no valid supported"),
            (ImportResult(1, 1, 1, 0, (), (), (Path("/managed/xenia.AppImage"),)), "source file was not changed"),
            (ImportResult(1, 1, 0, 1, (), (), (Path("/managed/xenia.AppImage"),)), "existing copy reused"),
            (ImportResult(1, 1, 0, 0, (), ("old.AppImage",), ()), "kept unchanged"),
            (ImportResult(2, 2, 0, 0, (), (), (), ("a.AppImage", "b.AppImage")), "nothing imported"),
        )
        for result, expected in outcomes:
            with self.subTest(expected=expected):
                output = StringIO()
                with redirect_stdout(output):
                    _print_provider_import(result)
                self.assertIn(expected, output.getvalue())
                self.assertNotIn("/managed/", output.getvalue())

    def test_explicit_override_not_silently_replaced_by_import(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            home, source = root / "home", root / "source"
            source.mkdir()
            incoming = source / "renamed.AppImage"
            incoming.write_bytes(elf(appimage=True))
            override = root / "override.AppImage"
            override.write_bytes(elf(appimage=True) + b"old")
            override.chmod(0o700)
            config = home / ".config/embercade/embercade.toml"
            config.parent.mkdir(parents=True)
            config.write_text(f'[executables]\nxenia-edge = "{override}"\n')
            output = StringIO()
            with (
                patch("embercade.imports._provider_metadata", return_value=XENIA_METADATA),
                patch.dict(os.environ, {"HOME": str(home), "PATH": ""}, clear=True),
                redirect_stdout(output),
            ):
                self.assertEqual(main(["setup", "--roms", directory, "--bios", directory,
                                       "--providers-from", str(source)]), 0)
            self.assertEqual(tomllib.loads(config.read_text())["executables"]["xenia-edge"], str(override))
            self.assertIn("override kept", output.getvalue())

    def test_bootstrap_dry_run_reports_no_changes(self) -> None:
        assessment = HostAssessment(DistroInfo("arch", "Arch Linux", ()), (), (), ())
        output = StringIO()
        with (
            TemporaryDirectory() as directory,
            patch.dict(os.environ, {"HOME": directory}, clear=True),
            patch("embercade.cli._assess_host", return_value=assessment),
            patch(
                "embercade.cli.create_bootstrap_plan",
                return_value=BootstrapPlan(assessment, ("retroarch",)),
            ),
            redirect_stdout(output),
        ):
            result = main(["bootstrap", "--dry-run", "--verbose"])
        self.assertEqual(result, 0)
        self.assertIn("sudo pacman -S --needed retroarch", output.getvalue())
        self.assertIn("NO CHANGES MADE", output.getvalue())

    def test_installer_sends_user_to_wizard_before_bootstrap(self) -> None:
        output = StringIO()
        with (
            patch("embercade.cli.install_user", return_value=SimpleNamespace(mode="NEW INSTALL")),
            patch("embercade.cli.print_operations"),
            redirect_stdout(output),
        ):
            result = main(["install", "--payload", "/tmp/payload", "--no-setup"])
        self.assertEqual(result, 0)
        self.assertIn("Host emulator dependencies have not been changed", output.getvalue())
        self.assertIn("Next: embercade wizard", output.getvalue())
        self.assertNotIn("Next: embercade bootstrap", output.getvalue())

    def test_interactive_setup_offers_optional_steam_before_doctor_and_launch(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios = root / "roms", root / "bios"
            roms.mkdir()
            bios.mkdir()
            answers = iter((str(roms), str(bios), "1", "", "3", "n", "n", "n"))
            assessment = HostAssessment(DistroInfo("other", "Other Linux", ()), (), (), ())
            with (
                patch.dict(os.environ, {"HOME": str(root / "home"), "PATH": ""}, clear=True),
                patch("embercade.cli.sys.stdin", SimpleNamespace(isatty=lambda: True)),
                patch("builtins.input", side_effect=lambda _prompt: next(answers)),
                patch("embercade.cli._assess_host", return_value=assessment),
                patch("embercade.cli.offer_integration") as steam_offer,
                redirect_stdout(StringIO()),
            ):
                self.assertEqual(main(["setup"]), 0)
            steam_offer.assert_called_once()


if __name__ == "__main__":
    unittest.main()

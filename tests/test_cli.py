from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import tomllib
import unittest

from embercade.cli import main
from tests.test_imports import elf, XENIA_METADATA


class ProviderConfigurationCliTests(unittest.TestCase):
    def test_setup_reports_invalid_provider_type_and_preserves_its_settings(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "embercade.toml"
            provider = {"provider": "typo", "executable": "/external/Provider.AppImage"}
            config.write_text(
                '[emulators.xenia-edge]\nprovider="typo"\nexecutable="/external/Provider.AppImage"\n',
            )
            output, errors = StringIO(), StringIO()
            with (
                patch.dict(os.environ, {"HOME": str(root / "home"), "PATH": ""}, clear=True),
                redirect_stdout(output), redirect_stderr(errors),
                self.assertRaises(SystemExit) as exit_status,
            ):
                main(["--config", str(config), "setup", "--roms", directory, "--bios", directory])
            self.assertEqual(exit_status.exception.code, 2)
            self.assertIn("existing provider needs attention; settings kept", output.getvalue())
            self.assertIn("invalid Embercade configuration", errors.getvalue())
            self.assertIn("provider must be one of", errors.getvalue())
            self.assertNotIn("Traceback", output.getvalue() + errors.getvalue())
            self.assertEqual(tomllib.loads(config.read_text())["emulators"]["xenia-edge"], provider)

    def test_doctor_reports_invalid_provider_type_without_traceback_or_writes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "embercade.toml"
            original = '[emulators.xenia-edge]\nprovider="typo"\nexecutable="/external/Provider.AppImage"\n'
            config.write_text(original)
            before = config.stat().st_mtime_ns
            for flags in ([], ["--verbose"]):
                with self.subTest(flags=flags):
                    errors = StringIO()
                    with (
                        patch.dict(os.environ, {"HOME": str(root / "home"), "PATH": ""}, clear=True),
                        redirect_stderr(errors),
                        self.assertRaises(SystemExit) as exit_status,
                    ):
                        main(["--config", str(config), "doctor", *flags])
                    self.assertEqual(exit_status.exception.code, 2)
                    self.assertIn("provider must be one of", errors.getvalue())
                    self.assertNotIn("Traceback", errors.getvalue())
                    self.assertEqual((config.read_text(), config.stat().st_mtime_ns), (original, before))
                    self.assertFalse((root / "home").exists())

    def test_explicit_setup_selection_reports_invalid_override_values(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "embercade.toml"
            original = '[executables]\nxenia-edge=42\n'
            config.write_text(original)
            provider = root / "Provider.AppImage"
            provider.write_bytes(elf(appimage=True))
            provider.chmod(0o700)
            output, errors = StringIO(), StringIO()
            with (
                patch("embercade.imports._provider_metadata", return_value=XENIA_METADATA),
                patch.dict(os.environ, {"HOME": str(root / "home"), "PATH": ""}, clear=True),
                redirect_stdout(output), redirect_stderr(errors),
                self.assertRaises(SystemExit) as exit_status,
            ):
                main([
                    "--config", str(config), "setup", "--roms", directory, "--bios", directory,
                    "--xenia-edge", str(provider),
                ])
            self.assertEqual(exit_status.exception.code, 2)
            self.assertIn("Every [executables] value must be a string", errors.getvalue())
            self.assertNotIn("Traceback", output.getvalue() + errors.getvalue())
            self.assertEqual(config.read_text(), original)


if __name__ == "__main__":
    unittest.main()

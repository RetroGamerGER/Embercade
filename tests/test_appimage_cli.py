"""Mounted-image CLI uses the existing setup and immutable/XDG contracts."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import subprocess
import unittest

from embercade.cli import main, _diagnostic_root
from embercade.paths import EmbercadePaths


class AppImageCliTests(unittest.TestCase):
    def test_every_xdg_override_and_explicit_write_target_is_protected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            env = {"HOME": str(root / "home"), "APPDIR": str(root / "AppDir"),
                   "EMBERCADE_PREFIX": str(root / "AppDir/usr")}
            for name in ("CONFIG", "DATA", "CACHE", "STATE", "RUNTIME"):
                with self.subTest(name=name):
                    paths = EmbercadePaths.from_environment({**env, f"EMBERCADE_{name}_HOME": str(root / "AppDir/state")})
                    with self.assertRaisesRegex(ValueError, "read-only"):
                        paths.validate_application_boundary(env)
            paths = EmbercadePaths.from_environment(env)
            with self.assertRaises(ValueError):
                paths.validate_application_boundary(env, targets=(root / "AppDir/settings.toml",))
            # Storing the image in HOME never relocates normal XDG children.
            paths.validate_application_boundary({**env, "APPIMAGE": str(root / "home/Embercade.AppImage")})

    def test_setup_and_wizard_reject_package_local_state_before_mutation(self):
        with TemporaryDirectory() as directory:
            appdir = Path(directory) / "AppDir"
            env = {"HOME": directory, "APPDIR": str(appdir), "XDG_CONFIG_HOME": str(appdir / "config")}
            for command in ("wizard", "setup", "steam", "install"):
                arguments = [command] if command != "install" else [command, "--payload", "/not-read"]
                with self.subTest(command=command), patch.dict("os.environ", env, clear=True), redirect_stderr(StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        main(arguments)
                    self.assertEqual(error.exception.code, 2)
                    self.assertFalse(appdir.exists())

    def test_first_image_start_reuses_wizard_without_installing(self):
        with TemporaryDirectory() as directory:
            env = {"HOME": directory, "APPDIR": directory + "/AppDir",
                   "EMBERCADE_PREFIX": directory + "/AppDir/usr", "DISPLAY": ":test"}
            with patch.dict("os.environ", env, clear=True), patch("embercade.cli.subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run:
                self.assertEqual(main([]), 0)
            arguments = run.call_args.args[0]
            self.assertIn("embercade.first_run_ui", arguments)
            self.assertNotIn("install", arguments)
            self.assertFalse((Path(directory) / "AppDir").exists())

    def test_existing_state_skips_questions_and_uses_exact_image_prefix(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "roms").mkdir()
            (root / "bios").mkdir()
            config = root / ".config/embercade/embercade.toml"
            config.parent.mkdir(parents=True)
            config.write_text(f'[paths]\nroms="{root / "roms"}"\nbios="{root / "bios"}"\n')
            env = {"HOME": directory, "APPDIR": directory + "/AppDir", "EMBERCADE_PREFIX": directory + "/AppDir/usr"}
            before = config.read_bytes()
            with patch.dict("os.environ", env, clear=True), patch("embercade.cli.run_production", return_value=0) as run, redirect_stdout(StringIO()):
                self.assertEqual(main([]), 0)
            self.assertEqual(run.call_args.args[0].prefix, root / "AppDir/usr")
            self.assertEqual(config.read_bytes(), before)

    def test_default_reports_use_user_state_in_production_not_appdir(self):
        with TemporaryDirectory() as directory:
            project = Path(directory) / "AppDir/usr/share/embercade"
            env = {"HOME": directory, "EMBERCADE_PREFIX": str(project.parents[2])}
            paths = EmbercadePaths.from_environment(env)
            with patch.dict("os.environ", env, clear=True):
                self.assertEqual(_diagnostic_root(project, paths), paths.state / "diagnostics")
            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(_diagnostic_root(project, paths), project / ".work")

    def test_controller_output_list_is_checked_before_input_enumeration(self):
        with TemporaryDirectory() as directory:
            appdir = Path(directory) / "AppDir"
            env = {"HOME": directory, "APPDIR": str(appdir), "EMBERCADE_PREFIX": str(appdir / "usr")}
            with patch.dict("os.environ", env, clear=True), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(["controller-prepare", "--database", "/read-only-source.xml",
                          "--output", str(appdir / "es_input.cfg")])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(appdir.exists())

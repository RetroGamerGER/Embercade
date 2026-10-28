"""Narrow controller preferences never re-run setup or change host drivers."""
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import unittest

from embercade.cli import _parser, main
from embercade.exit_hotkey import resolve_exit_hotkey
from embercade.first_run import read_state
from embercade.installer_preferences import save_exit_hotkey
from embercade.runtime import load_config
from embercade.setup_flow import SetupError


class InstallerControllerPreferencesTests(unittest.TestCase):
    def test_preconfiguration_persists_without_collection_or_emulator_setup(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config/embercade.toml"
            profile = root / "emulators/xemu/eeprom.bin"
            profile.parent.mkdir(parents=True)
            profile.write_bytes(b"isolated test fixture")
            before = profile.stat()
            save_exit_hotkey(config, "guide-start")
            state = read_state(config, {"HOME": directory})
            self.assertFalse(state.configured)
            self.assertEqual(state.exit_hotkey, "guide-start")
            self.assertEqual(resolve_exit_hotkey(load_config(config)).key, "guide-start")
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(profile.read_bytes(), b"isolated test fixture")
            self.assertEqual(profile.stat(), before)
            self.assertEqual(set(root.iterdir()), {root / "config", root / "emulators"})

    def test_only_selected_value_changes_and_all_comments_and_line_endings_survive(self):
        original = (
            '# Preserve user formatting\r\n[installer]\r\nlanguage = "de"\r\n'
            '[custom]\r\nexit_hotkey = "back-start" # unrelated\r\n'
            '[controller] # my controller preferences\r\n'
            '\t"exit_hotkey" = \'back-start\'  # keep this comment\r\n'
            'player_order = [2, 1]\r\n[emulators.custom]\r\n'
            'executable = "/synthetic/emulator" # keep this too'
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.toml"
            path.write_bytes(original.encode())
            save_exit_hotkey(path, "guide-start")
            expected = original.replace("'back-start'", '"guide-start"')
            self.assertEqual(path.read_bytes(), expected.encode())
            after = path.stat()
            save_exit_hotkey(path, "guide-start")
            self.assertEqual(path.stat(), after)
            self.assertEqual(load_config(path)["custom"]["exit_hotkey"], "back-start")

    def test_missing_key_preserves_existing_controller_table_and_other_fields(self):
        original = '# setup\n["controller"] # existing options\nplayer = 2\n[installer]\nlanguage = "en"\n'
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.toml"
            path.write_text(original)
            save_exit_hotkey(path, "back-start")
            self.assertEqual(path.read_text().replace('exit_hotkey = "back-start"\n', ''), original)
            self.assertEqual(load_config(path), {"controller": {"player": 2, "exit_hotkey": "back-start"},
                                                  "installer": {"language": "en"}})

    def test_dotted_controller_preferences_remain_valid(self):
        for original in ('controller.exit_hotkey = "back-start" # chord\n',
                         'controller.player = 2\n[installer]\nlanguage = "en"\n'):
            with self.subTest(original=original), TemporaryDirectory() as directory:
                path = Path(directory) / "settings.toml"
                path.write_text(original)
                save_exit_hotkey(path, "guide-start")
                self.assertEqual(load_config(path)["controller"]["exit_hotkey"], "guide-start")
                self.assertIn('# chord' if '# chord' in original else 'controller.player = 2', path.read_text())

    def test_invalid_or_unsupported_configuration_is_left_byte_identical(self):
        for original in ('[invalid', 'controller = "invalid"\n',
                         '[[controller]]\nexit_hotkey = "back-start"\n',
                         'controller = { exit_hotkey = "back-start", player = 2 }\n'):
            with self.subTest(original=original), TemporaryDirectory() as directory:
                path = Path(directory) / "settings.toml"
                path.write_text(original)
                before = path.stat()
                with self.assertRaises(ValueError):
                    save_exit_hotkey(path, "guide-start")
                self.assertEqual(path.read_text(), original)
                self.assertEqual(path.stat(), before)

    def test_invalid_preset_does_not_create_configuration(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "new/settings.toml"
            for hotkey in ("custom", "", "Guide + Start"):
                with self.subTest(hotkey=hotkey), self.assertRaises(ValueError):
                    save_exit_hotkey(path, hotkey)
            self.assertFalse(path.parent.exists())

    def test_symlink_and_unsafe_parent_refuse_writes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "settings.toml"
            target.write_text('[controller]\nexit_hotkey = "back-start"\n')
            link = root / "link.toml"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                save_exit_hotkey(link, "guide-start")
            self.assertEqual(load_config(target)["controller"]["exit_hotkey"], "back-start")
            parent = root / "config-link"
            parent.symlink_to(root, target_is_directory=True)
            with self.assertRaises(SetupError):
                save_exit_hotkey(parent / "new.toml", "guide-start")
            self.assertFalse((root / "new.toml").exists())

    def test_atomic_publication_failure_keeps_original_and_removes_temporary_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.toml"
            original = '[controller]\nexit_hotkey = "back-start" # keep\n'
            path.write_text(original)
            with patch("embercade.setup_flow.os.replace", side_effect=OSError("test write failure")):
                with self.assertRaises(OSError):
                    save_exit_hotkey(path, "guide-start")
            self.assertEqual(path.read_text(), original)
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_cli_saves_only_preference_without_probing_or_running_host_tools(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"HOME": directory}, clear=True):
            config = Path(directory) / "settings.toml"
            config.write_text('[installer]\nlanguage = "de"\n')
            forbidden = AssertionError("controller preference must not probe or change the host")
            with patch("embercade.cli._assess_host", side_effect=forbidden), \
                 patch("embercade.cli.configure", side_effect=forbidden), \
                 patch("embercade.cli.run_bootstrap", side_effect=forbidden), \
                 patch("embercade.cli.subprocess.run", side_effect=forbidden):
                result = main(["--config", str(config), "installer", "controller", "--exit-hotkey", "guide-start"])
            self.assertEqual(result, 0)
            self.assertEqual(load_config(config), {"installer": {"language": "de"},
                                                   "controller": {"exit_hotkey": "guide-start"}})

    def test_cli_reports_missing_invalid_and_malformed_input_without_writes(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"HOME": directory}, clear=True):
            path = Path(directory) / "settings.toml"
            for flags in ([], ["--exit-hotkey", "custom"]):
                with self.subTest(flags=flags), patch("sys.stderr", new_callable=StringIO) as output:
                    with self.assertRaises(SystemExit) as error:
                        main(["--config", str(path), "installer", "controller", *flags])
                    self.assertEqual(error.exception.code, 2)
                    self.assertNotIn("Traceback", output.getvalue())
                    self.assertFalse(path.exists())
            path.write_text('[invalid')
            with patch("sys.stderr", new_callable=StringIO) as output, self.assertRaises(SystemExit) as error:
                main(["--config", str(path), "installer", "controller", "--exit-hotkey", "back-start"])
            self.assertEqual(error.exception.code, 2)
            self.assertNotIn("Traceback", output.getvalue())
            self.assertEqual(path.read_text(), '[invalid')

    def test_cli_obeys_immutable_prefix_boundary_and_existing_setup_option(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {"HOME": directory, "EMBERCADE_PREFIX": str(root / "app")}, clear=True), \
                 patch("sys.stderr", new_callable=StringIO):
                with self.assertRaises(SystemExit) as error:
                    main(["--config", str(root / "app/settings.toml"), "installer", "controller", "--exit-hotkey", "guide-start"])
                self.assertEqual(error.exception.code, 2)
                self.assertFalse((root / "app").exists())
            setup = _parser().parse_args(["setup", "--exit-hotkey", "back-start"])
            self.assertEqual(setup.exit_hotkey, "back-start")


if __name__ == "__main__":
    unittest.main()

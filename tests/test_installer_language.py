from pathlib import Path
from tempfile import TemporaryDirectory
from string import Formatter
from unittest.mock import patch
import ast
import json
import os
import unittest

from embercade.i18n import GERMAN, Translator, system_language
from embercade.installer_preferences import save_language, saved_language
from embercade.first_run import read_state
from embercade.runtime import load_config


class InstallerLanguageTests(unittest.TestCase):
    def test_locale_precedence_and_supported_fallback(self):
        self.assertEqual(system_language(dict(LANG="de_DE.UTF-8")), "de")
        self.assertEqual(system_language(dict(LC_MESSAGES="en_US", LANG="de_DE")), "en")
        self.assertEqual(system_language(dict(LC_ALL="de_AT", LC_MESSAGES="en_US")), "de")
        self.assertEqual(system_language(dict(LANG="fr_FR")), "en")
        self.assertEqual(system_language({}), "en")

    def test_language_persists_before_setup_and_preserves_existing_settings(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.toml"
            save_language(path, "en")
            self.assertEqual(read_state(path, {"HOME": directory}).language, "en")
            self.assertFalse(read_state(path, {"HOME": directory}).configured)
            path.write_text(path.read_text() + '\n[controller]\nexit_hotkey="guide-start"\n[custom]\nvalue=42\n')
            before = load_config(path)
            save_language(path, "de")
            after = load_config(path)
            self.assertEqual(after["controller"], before["controller"])
            self.assertEqual(after["custom"], before["custom"])
            self.assertEqual(saved_language(after), "de")
            original = path.read_bytes()
            save_language(path, "de")
            self.assertEqual(original, path.read_bytes())

    def test_invalid_preferences_and_symlinks_do_not_overwrite_existing_files(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.toml"
            path.write_text("[invalid")
            with self.assertRaises(ValueError): save_language(path, "en")
            self.assertEqual(path.read_text(), "[invalid")
            with self.assertRaises(ValueError): save_language(path, "fr")
            link = Path(directory) / "link.toml"
            link.symlink_to(path)
            with self.assertRaises(ValueError): save_language(link, "de")
            self.assertEqual(path.read_text(), "[invalid")

    def test_catalog_preserves_format_fields_and_all_visible_literal_messages(self):
        fields = lambda text: {name for _, name, _, _ in Formatter().parse(text) if name is not None}
        for english, german in GERMAN.items():
            with self.subTest(message=english):
                self.assertTrue(german)
                self.assertEqual(fields(english), fields(german))
        source = Path(__file__).resolve().parents[1] / "src/embercade/first_run_ui.py"
        tree = ast.parse(source.read_text())
        visible = {"_label", "_button", "_field", "_message", "_question", "_t"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in visible:
                count = 2 if node.func.attr in {"_message", "_question"} else 1
                for arg in node.args[:count]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        self.assertIn(arg.value, GERMAN)
        # User paths may contain literal braces; translated UI must not format them.
        self.assertEqual(Translator("de")("/ROMs/{collection}"), "/ROMs/{collection}")

    def test_cli_language_obeys_prefix_boundary(self):
        from embercade.cli import main
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {"HOME": directory, "EMBERCADE_PREFIX": str(root / "app")}, clear=True):
                with self.assertRaises(SystemExit):
                    main(["--config", str(root / "app/settings.toml"), "installer", "language", "--language", "de"])
                self.assertFalse((root / "app").exists())

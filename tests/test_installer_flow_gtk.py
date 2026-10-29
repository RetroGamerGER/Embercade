"""Opt-in bilingual GUI flow with real isolated CLI setup/checks and fake host transaction.

No emulator/game, package manager, Steam or normal profile is started. This is
GUI automation evidence, never two-host interactive/gameplay acceptance.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest
from unittest.mock import Mock, patch

from embercade.first_run import read_state, run_action
from embercade.first_run_ui import Wizard, _gtk
from embercade.host_install import read_result, run_installation
from embercade.host_requirements import DistroInfo
from embercade.i18n import Translator


@unittest.skipUnless(os.environ.get("EMBERCADE_TEST_GTK") == "1", "opt-in GTK test display required")
class BilingualInstallerFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.GLib, cls.Gtk = _gtk()

    def flow(self, language):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios = root / "ROM files {collection}", root / "BIOS files"
            roms.mkdir(); bios.mkdir()
            config = root / "config/embercade.toml"
            environment = {key: value for key, value in os.environ.items() if not key.startswith("EMBERCADE_") and key not in {"LC_ALL", "LC_MESSAGES"}}
            environment.update(HOME=directory, XDG_CONFIG_HOME=str(root / "config"),
                               XDG_DATA_HOME=str(root / "data"), XDG_CACHE_HOME=str(root / "cache"),
                               XDG_STATE_HOME=str(root / "state"), LANG="de_DE.UTF-8")
            failures, visited, messages = [], [], []
            with patch.dict(os.environ, environment, clear=True), patch("embercade.first_run_ui.Gamepad"), patch("embercade.first_run_ui.read_os_release", return_value=DistroInfo("arch", "Arch Linux", ())):
                wizard = Wizard(config, self.GLib, self.Gtk)
                wizard._message = lambda title, body, **kw: messages.append((wizard._t(title), wizard._t(body)))
                wizard._question = Mock(return_value=True)
                def backend(arguments, callback):
                    result = run_action((sys.executable, "-B", "-m", "embercade"), arguments, environment=environment)
                    callback(result)
                wizard._run_arguments = backend
                def visit(expected):
                    self.assertEqual(wizard.page, expected)
                    visited.append(expected)
                    if expected in ('welcome','host'):
                        notice='Automatic host-software installation supports Arch-based distributions with pacman, including Arch Linux, CachyOS, Garuda and EndeavourOS.'
                        labels=[child.get_text() for child in wizard.root.get_children() if isinstance(child,self.Gtk.Label)]
                        self.assertIn(Translator(language)(notice),labels)
                def begin():
                    try:
                        visit("language")
                        self.assertEqual(wizard.language, "de")
                        self.assertFalse(config.exists())
                        wizard.language_choice.set_active_id(language)
                        wizard._save_language()
                        visit("welcome")
                        self.assertEqual(read_state(config, environment).language, language)
                        wizard._go("paths"); visit("paths")
                        wizard.rom_entry.set_text(str(roms)); wizard.bios_entry.set_text(str(bios))
                        # Changing language later must preserve fields and setup state.
                        wizard._language_settings(); self.assertEqual(wizard.page, "language")
                        wizard._save_language(); self.assertEqual(wizard.page, "paths")
                        self.assertEqual(wizard.rom_entry.get_text(), str(roms))
                        wizard._save_paths(); visit("sources")
                        wizard._save_sources(); visit("shadps4")
                        wizard._save_shadps4(); visit("assets")
                        self.assertEqual(wizard.ppsspp_entry.get_text(), "")
                        self.assertEqual(wizard.xemu_entry.get_text(), "")
                        self.assertTrue(any(isinstance(child, self.Gtk.Button) and
                            child.get_label() == Translator(language)("Skip for now")
                            for child in wizard.root.get_children()))
                        if language == "en":
                            # A general BIOS folder is not valid system-specific
                            # input. Rejection stays on the page and Skip recovers.
                            wizard.ppsspp_entry.set_text(str(bios))
                            wizard.xemu_entry.set_text(str(bios))
                            wizard._save_assets()
                            self.assertEqual(wizard.page, "assets")
                            self.assertIn("Skip for now", messages[-1][1])
                            wizard._skip_assets()
                        else:
                            wizard._save_assets()
                        visit("host")
                        result_dir = root / "transaction"; result_dir.mkdir(mode=0o700)
                        result_file = result_dir / "result.json"
                        run_installation(result_file, [sys.executable, "-c", "print('fake post-transaction hooks complete')"],
                                         language, input_function=lambda _: self.fail("Success must not hold"), output=lambda _: None)
                        transaction = Mock()
                        transaction.result.side_effect = lambda: read_result(result_file)
                        with patch("embercade.first_run_ui.TerminalInstallation.start", return_value=transaction):
                            wizard._bootstrap()
                        self.GLib.timeout_add(300, finish)
                    except BaseException as error:
                        failures.append(error); wizard.window.destroy()
                    return False
                def finish():
                    try:
                        self.assertFalse(wizard.busy)
                        self.assertIn(Translator(language)("Host installation completed."), "\n".join(body for _, body in messages))
                        wizard._go("controller"); visit("controller")
                        wizard._choose_hotkey("guide-start"); visit("controller")
                        wizard._save_controller(); visit("xbox")
                        self.assertEqual(read_state(config, environment).exit_hotkey, "guide-start")
                        wizard.eeprom_entry.set_text("/chosen EEPROM.bin")
                        wizard.xbox_combos["language"].set_active_id("de")
                        wizard._language_settings(); wizard._save_language()
                        self.assertEqual(wizard.page,"xbox")
                        self.assertEqual(wizard.eeprom_entry.get_text(),"/chosen EEPROM.bin")
                        self.assertEqual(wizard.xbox_combos["language"].get_active_id(),"de")
                        wizard._continue_xbox(); visit("ps3")
                        wizard._continue_ps3(); visit("desktop")
                        self.assertTrue(wizard.desktop_toggles["menu_enabled"].get_active())
                        wizard._save_desktop(); visit("checks")
                        wizard._apply(); visit("finish")
                        self.assertTrue(wizard.state.configured)
                        self.assertEqual(read_state(config, environment).language, language)
                        self.assertEqual(read_state(config, environment).roms, str(roms))
                        self.assertFalse(list(roms.iterdir())); self.assertFalse(list(bios.iterdir()))
                        # Reading the saved state preserves the completed setup.
                        reopened = read_state(config, environment)
                        self.assertTrue(reopened.configured)
                        wizard._launch()
                        self.assertTrue(wizard.launch_after_close)
                        self.assertEqual(visited, ["language", "welcome", "paths", "sources", "shadps4", "assets", "host", "controller", "controller", "xbox", "ps3", "desktop", "checks", "finish"])
                    except BaseException as error:
                        failures.append(error); wizard.window.destroy()
                    return False
                wizard.window.show_all()
                self.GLib.idle_add(begin)
                self.Gtk.main()
                while self.Gtk.events_pending(): self.Gtk.main_iteration_do(False)
                wizard.window.get_display().sync()
            if failures: raise failures[0]

    def test_complete_english_flow(self): self.flow("en")
    def test_complete_german_flow(self): self.flow("de")

    def test_every_restart_begins_with_saved_language_without_resetting_setup(self):
        for language in ("de", "en"):
            for configured in (False, True):
                with self.subTest(language=language, configured=configured), TemporaryDirectory() as directory:
                    root = Path(directory)
                    config = root / "config" / "embercade.toml"
                    config.parent.mkdir()
                    text = (f'[installer]\nlanguage = "{language}"\n\n'
                            '[controller]\nexit_hotkey = "back-start"\n')
                    roms, bios = root / "ROM files", root / "BIOS files"
                    if configured:
                        roms.mkdir(); bios.mkdir()
                        (roms / "preserved.fixture").write_bytes(b"synthetic collection fixture")
                        (bios / "preserved.fixture").write_bytes(b"synthetic BIOS fixture")
                        text += f'\n[paths]\nroms = {json.dumps(str(roms))}\nbios = {json.dumps(str(bios))}\n'
                    config.write_text(text)
                    baseline = {path: (path.read_bytes(), path.stat().st_mtime_ns)
                                for path in root.rglob("*") if path.is_file()}
                    environment = {key: value for key, value in os.environ.items()
                                   if not key.startswith("EMBERCADE_")
                                   and key not in {"LC_ALL", "LC_MESSAGES", "LANGUAGE"}}
                    environment.update(
                        HOME=directory, XDG_CONFIG_HOME=str(root / "config"),
                        XDG_DATA_HOME=str(root / "data"), XDG_CACHE_HOME=str(root / "cache"),
                        XDG_STATE_HOME=str(root / "state"),
                        LANG="en_US.UTF-8" if language == "de" else "de_DE.UTF-8",
                    )
                    failures = []
                    with patch.dict(os.environ, environment, clear=True), patch("embercade.first_run_ui.Gamepad"):
                        wizard = Wizard(config, self.GLib, self.Gtk)
                        wizard._message = Mock()

                        def backend(arguments, callback):
                            self.assertEqual(arguments[2:4], ("installer", "language"))
                            callback(run_action((sys.executable, "-B", "-m", "embercade"),
                                                arguments, environment=environment))

                        wizard._run_arguments = backend

                        def inspect_and_continue():
                            try:
                                self.assertEqual(wizard.page, "language")
                                self.assertEqual(wizard.language_choice.get_active_id(), language)
                                self.assertEqual(wizard.language, language)
                                self.assertEqual(wizard.state.configured, configured)
                                self.assertEqual(
                                    {path: (path.read_bytes(), path.stat().st_mtime_ns)
                                     for path in root.rglob("*") if path.is_file()}, baseline,
                                    "Opening the language page must not create or rewrite profile files",
                                )
                                selected = "en" if language == "de" else "de"
                                wizard.language_choice.set_active_id(selected)
                                wizard._save_language()
                                self.assertEqual(wizard.page, "welcome")
                                self.assertEqual(wizard.state.configured, configured)
                                expected = tomllib.loads(text)
                                expected["installer"]["language"] = selected
                                self.assertEqual(tomllib.loads(config.read_text()), expected)
                                self.assertEqual(wizard.state.roms, str(roms) if configured else "")
                                self.assertEqual(wizard.state.bios, str(bios) if configured else "")
                                self.assertEqual(wizard.state.exit_hotkey, "back-start")
                                for path, original in baseline.items():
                                    if path != config:
                                        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), original)
                                wizard._message.assert_not_called()
                            except BaseException as error:
                                failures.append(error)
                            finally:
                                wizard.window.destroy()
                            return False

                        wizard.window.show_all()
                        self.GLib.idle_add(inspect_and_continue)
                        self.Gtk.main()
                        while self.Gtk.events_pending(): self.Gtk.main_iteration_do(False)
                        wizard.window.get_display().sync()
                    if failures:
                        raise failures[0]

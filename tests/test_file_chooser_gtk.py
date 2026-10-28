"""Opt-in real GTK fallback/lifecycle tests; no setup action or emulator launch."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from embercade.first_run_ui import Wizard, _gtk


@unittest.skipUnless(os.environ.get("EMBERCADE_TEST_GTK") == "1", "opt-in GTK display required")
class GtkFileChooserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.GLib, cls.Gtk = _gtk()

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.folder = self.root / "External ROMs {test}"
        self.folder.mkdir()
        self.file = self.folder / "test EEPROM.bin"
        self.file.write_bytes(b"synthetic file selection only")
        self.wizard = Wizard.__new__(Wizard)
        self.wizard.Gtk = self.Gtk
        self.wizard.window = self.Gtk.Window(title="Embercade chooser lifecycle test")
        self.entry = self.Gtk.Entry()
        self.wizard.window.add(self.entry)
        self.wizard.window.show_all()
        self.wizard.folder_dialog = self.wizard.message_dialog = None
        self.wizard._message = Mock()
        self.wizard._back = Mock()
        self.wizard.pad = Mock()
        self.wizard.busy = False
        self.wizard.page = "paths"

    def tearDown(self):
        self.wizard.window.destroy()
        while self.Gtk.events_pending():
            self.Gtk.main_iteration_do(False)
        self.temporary.cleanup()

    def choose(self, inspect, *, file=False, native=False):
        errors = []
        def respond():
            try:
                inspect(self.wizard.folder_dialog)
            except BaseException as error:
                errors.append(error)
                self.wizard.folder_dialog.response(self.Gtk.ResponseType.CANCEL)
            return False
        self.GLib.timeout_add(300, respond)
        with patch("embercade.first_run_ui.native_portal_available", return_value=native):
            self.wizard._choose_directory(self.entry, file=file)
        self.assertIsNone(self.wizard.folder_dialog)
        if errors:
            raise errors[0]

    def test_folder_accept_cancel_and_reopen_in_both_languages(self):
        for language in ("de", "en"):
            with self.subTest(language=language):
                self.wizard.language = language
                self.entry.set_text(str(self.folder))
                def accept(dialog):
                    self.assertIsInstance(dialog, self.Gtk.FileChooserDialog)
                    self.assertTrue(dialog.get_modal())
                    self.assertEqual(dialog.get_transient_for(), self.wizard.window)
                    self.assertEqual(dialog.get_current_folder(), str(self.folder))
                    dialog.response(self.Gtk.ResponseType.ACCEPT)
                self.choose(accept)
                self.assertEqual(self.entry.get_text(), str(self.folder))
                def cancel(dialog):
                    dialog.set_current_folder(str(self.root))
                    dialog.response(self.Gtk.ResponseType.CANCEL)
                self.choose(cancel)
                self.assertEqual(self.entry.get_text(), str(self.folder))
                self.choose(accept)

    def test_file_preselection_and_accept_preserve_file_mode(self):
        self.entry.set_text(str(self.file))
        def accept(dialog):
            self.assertEqual(dialog.get_action(), self.Gtk.FileChooserAction.OPEN)
            self.assertEqual(dialog.get_filename(), str(self.file))
            dialog.response(self.Gtk.ResponseType.ACCEPT)
        self.choose(accept, file=True)
        self.assertEqual(self.entry.get_text(), str(self.file))

    def test_gamepad_cancel_does_not_navigate_parent(self):
        self.entry.set_text(str(self.folder))
        def cancel(dialog):
            self.wizard.pad.poll.return_value = {"b"}
            self.wizard._poll_gamepad()
        self.choose(cancel)
        self.assertEqual(self.entry.get_text(), str(self.folder))
        self.wizard._back.assert_not_called()

    def test_parent_close_cancels_without_changing_selection(self):
        self.entry.set_text(str(self.folder))
        # GTK destroys child entry contents with its parent; assert that the
        # chooser never writes a selection during this teardown.
        with patch.object(self.entry, "set_text", wraps=self.entry.set_text) as write:
            self.choose(lambda dialog: self.wizard.window.destroy())
        write.assert_not_called()
        self.wizard._message.assert_not_called()

    def test_native_dialog_can_be_cancelled_and_reopened(self):
        self.entry.set_text(str(self.folder))
        def cancel(dialog):
            self.assertIsInstance(dialog, self.Gtk.FileChooserNative)
            self.assertTrue(dialog.get_modal())
            self.assertEqual(dialog.get_transient_for(), self.wizard.window)
            self.wizard.pad.poll.return_value = {"b"}
            self.wizard._poll_gamepad()
        self.choose(cancel, native=True)
        self.choose(cancel, native=True)
        self.assertEqual(self.entry.get_text(), str(self.folder))
        self.wizard._back.assert_not_called()

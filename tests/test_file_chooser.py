"""Native chooser contracts without GTK sessions or existing user profiles."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
import sys
import unittest

from embercade.file_chooser import (
    create_chooser, initial_location, native_portal_available, validate_selection,
)
from embercade.first_run_ui import Wizard
from embercade.i18n import Translator


def fake_gtk():
    return SimpleNamespace(
        FileChooserAction=SimpleNamespace(OPEN=0, SELECT_FOLDER=2),
        ResponseType=SimpleNamespace(ACCEPT=-3, OK=-5, CANCEL=-6, DELETE_EVENT=-4),
        FileChooserNative=SimpleNamespace(new=Mock(return_value=Mock())),
        FileChooserDialog=Mock(return_value=Mock()),
    )


class FileChooserPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "test home"
        self.home.mkdir()
        self.collection = self.root / "run" / "media" / "owner" / "ROM drive"
        self.collection.mkdir(parents=True)
        self.source = self.collection / "sample firmware.bin"
        self.source.write_bytes(b"synthetic fixture")

    def test_empty_entry_opens_home_instead_of_working_directory(self):
        with patch("pathlib.Path.home", return_value=self.home):
            for value in ("", "   ", "\t\n"):
                with self.subTest(value=value):
                    self.assertEqual(initial_location(value), (self.home, None))

    def test_existing_mount_directory_with_spaces_is_retained(self):
        for file in (False, True):
            with self.subTest(file=file):
                self.assertEqual(
                    initial_location(str(self.collection), file=file, home=self.home),
                    (self.collection, None),
                )

    def test_existing_file_selects_parent_and_preselects_that_file(self):
        self.assertEqual(
            initial_location(str(self.source), file=True, home=self.home),
            (self.collection, self.source),
        )

    def test_missing_or_wrong_type_initial_path_falls_back_to_home(self):
        for value, file in ((str(self.root / "removed mount"), False),
                            (str(self.root / "missing firmware.bin"), True),
                            (str(self.source), False)):
            with self.subTest(value=value, file=file):
                self.assertEqual(initial_location(value, file=file, home=self.home),
                                 (self.home, None))

    def test_relative_and_home_paths_are_expanded_without_changing_cwd(self):
        relative = str(self.collection.relative_to(self.root))
        with patch("os.getcwd", return_value=str(self.root)):
            self.assertEqual(initial_location(relative, home=self.home),
                             (self.collection, None))
        with patch.dict("os.environ", {"HOME": str(self.home)}):
            self.assertEqual(initial_location("~", home=self.home), (self.home, None))

    def test_directory_symlink_retains_selected_path(self):
        alias = self.root / "collection shortcut"
        alias.symlink_to(self.collection, target_is_directory=True)
        self.assertEqual(initial_location(str(alias), home=self.home), (alias, None))
        self.assertEqual(validate_selection(str(alias)), str(alias))

    def test_local_existing_expected_type_is_accepted(self):
        self.assertEqual(validate_selection(str(self.collection)), str(self.collection))
        self.assertEqual(validate_selection(str(self.source), file=True), str(self.source))

    def test_invalid_remote_missing_and_wrong_type_results_are_rejected(self):
        for value, file in ((None, False), ("", False), ("   ", False),
                            ("smb://example.invalid/games", False),
                            ("relative/path", False),
                            (str(self.root / "gone"), False),
                            (str(self.root / "gone.bin"), True),
                            (str(self.source), False),
                            (str(self.collection), True)):
            with self.subTest(value=value, file=file):
                self.assertIsNone(validate_selection(value, file=file))

    def test_unreadable_selection_is_rejected(self):
        with patch("os.access", return_value=False):
            self.assertIsNone(validate_selection(str(self.collection)))
            self.assertIsNone(validate_selection(str(self.source), file=True))

    def test_validation_never_creates_missing_paths(self):
        missing = self.root / "new directory" / "new file.bin"
        self.assertIsNone(validate_selection(str(missing), file=True))
        self.assertFalse(missing.parent.exists())

    def test_unknown_home_user_is_rejected_without_crashing(self):
        with patch("pathlib.Path.expanduser", side_effect=RuntimeError("unknown user")):
            self.assertIsNone(validate_selection("~unavailable-user/games"))
            self.assertEqual(initial_location("~unavailable-user/games", home=self.home),
                             (self.home, None))


class FileChooserConstructionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gtk = fake_gtk()
        self.parent = object()

    def test_native_chooser_uses_translated_labels_and_local_folder_mode(self):
        for language in ("de", "en"):
            with self.subTest(language=language):
                self.gtk = fake_gtk()
                translate = Translator(language)
                dialog = create_chooser(
                    self.gtk, self.parent, title=translate("Choose folder"),
                    accept_label=translate("Use this folder"),
                    cancel_label=translate("Cancel"), initial=str(self.root),
                )
                self.gtk.FileChooserNative.new.assert_called_once_with(
                    translate("Choose folder"), self.parent,
                    self.gtk.FileChooserAction.SELECT_FOLDER,
                    translate("Use this folder"), translate("Cancel"),
                )
                self.assertIs(dialog, self.gtk.FileChooserNative.new.return_value)
                dialog.set_local_only.assert_called_once_with(True)
                dialog.set_select_multiple.assert_called_once_with(False)
                dialog.set_create_folders.assert_called_once_with(False)
                dialog.set_current_folder.assert_called_once_with(str(self.root))
                self.gtk.FileChooserDialog.assert_not_called()

    def test_file_mode_preselects_existing_file(self):
        source = self.root / "selected update.PUP"
        source.write_bytes(b"synthetic fixture")
        dialog = create_chooser(
            self.gtk, self.parent, title="Choose file", accept_label="Use this file",
            cancel_label="Cancel", initial=str(source), file=True,
        )
        self.assertEqual(self.gtk.FileChooserNative.new.call_args.args[2],
                         self.gtk.FileChooserAction.OPEN)
        dialog.set_current_folder.assert_called_once_with(str(self.root))
        dialog.set_filename.assert_called_once_with(str(source))

    def test_explicit_gtk_fallback_still_selects_local_existing_folders(self):
        dialog = create_chooser(
            self.gtk, self.parent, title="Choose folder", accept_label="Use this folder",
            cancel_label="Cancel", initial=str(self.root), use_native=False,
        )
        self.gtk.FileChooserNative.new.assert_not_called()
        self.gtk.FileChooserDialog.assert_called_once()
        self.assertIs(dialog, self.gtk.FileChooserDialog.return_value)
        dialog.set_local_only.assert_called_once_with(True)
        dialog.set_select_multiple.assert_called_once_with(False)
        dialog.set_create_folders.assert_called_once_with(False)
        dialog.set_current_folder.assert_called_once_with(str(self.root))

    def test_missing_native_api_falls_back_to_gtk_chooser(self):
        del self.gtk.FileChooserNative
        dialog = create_chooser(
            self.gtk, self.parent, title="Choose folder", accept_label="Use this folder",
            cancel_label="Cancel", initial=str(self.root),
        )
        self.assertIs(dialog, self.gtk.FileChooserDialog.return_value)
        dialog.set_current_folder.assert_called_once_with(str(self.root))

    def test_native_construction_failure_falls_back_to_gtk_chooser(self):
        self.gtk.FileChooserNative.new.side_effect = RuntimeError("native API unavailable")
        dialog = create_chooser(
            self.gtk, self.parent, title="Choose folder", accept_label="Use this folder",
            cancel_label="Cancel", initial=str(self.root),
        )
        self.assertIs(dialog, self.gtk.FileChooserDialog.return_value)
        dialog.set_current_folder.assert_called_once_with(str(self.root))

    def test_configuration_failure_destroys_unreturned_dialog(self):
        dialog = self.gtk.FileChooserNative.new.return_value
        dialog.set_current_folder.side_effect = RuntimeError("location unavailable")
        with self.assertRaisesRegex(RuntimeError, "location unavailable"):
            create_chooser(
                self.gtk, self.parent, title="Choose folder", accept_label="Use this folder",
                cancel_label="Cancel", initial=str(self.root),
            )
        dialog.destroy.assert_called_once()

    def test_rejected_initial_folder_retries_home(self):
        home = self.root / "test home"
        home.mkdir()
        dialog = self.gtk.FileChooserNative.new.return_value
        dialog.set_current_folder.side_effect = (False, True)
        with patch("pathlib.Path.home", return_value=home):
            result = create_chooser(
                self.gtk, self.parent, title="Choose folder", accept_label="Use this folder",
                cancel_label="Cancel", initial=str(self.root),
            )
        self.assertIs(result, dialog)
        self.assertEqual([call.args[0] for call in dialog.set_current_folder.call_args_list],
                         [str(self.root), str(home)])
        dialog.destroy.assert_not_called()


class FileChooserPortalTests(unittest.TestCase):
    def setUp(self):
        self.connection = Mock()
        self.Gio = SimpleNamespace(
            BusType=SimpleNamespace(SESSION=0), DBusCallFlags=SimpleNamespace(NONE=0),
            bus_get_sync=Mock(return_value=self.connection),
        )
        self.GLib = SimpleNamespace(
            Error=RuntimeError, Variant=Mock(), VariantType=SimpleNamespace(new=Mock()),
        )
        for patcher in (
            patch.dict("os.environ", {"GTK_USE_PORTAL": "1", "GAMESCOPE_WAYLAND_DISPLAY": ""}),
            patch.dict(sys.modules, {"gi.repository": SimpleNamespace(Gio=self.Gio, GLib=self.GLib)}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_directory_mode_requires_portal_directory_selection_version(self):
        for version, expected in ((1, False), (2, False), (3, True), (4, True)):
            with self.subTest(version=version):
                self.connection.call_sync.return_value.unpack.return_value = (version,)
                self.assertEqual(native_portal_available(), expected)

    def test_file_mode_supports_older_portals(self):
        self.connection.call_sync.return_value.unpack.return_value = (1,)
        self.assertTrue(native_portal_available(file=True))

    def test_missing_portal_service_falls_back_after_bounded_call(self):
        self.connection.call_sync.side_effect = RuntimeError("service unavailable")
        self.assertFalse(native_portal_available())
        arguments = self.connection.call_sync.call_args.args
        self.assertEqual(arguments[0], "org.freedesktop.portal.Desktop")
        self.assertEqual(arguments[-2], 1000)

    def test_portal_disabled_or_gamescope_does_not_contact_session_bus(self):
        for values in ({"GTK_USE_PORTAL": "0"}, {"GAMESCOPE_WAYLAND_DISPLAY": "gamescope-0"}):
            with self.subTest(values=values), patch.dict("os.environ", values):
                self.assertFalse(native_portal_available())
                self.Gio.bus_get_sync.assert_not_called()


class WizardFileChooserTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "External games"
        self.folder.mkdir()
        self.source = self.root / "update file.PUP"
        self.source.write_bytes(b"synthetic fixture")
        self.wizard = object.__new__(Wizard)
        self.wizard.Gtk = fake_gtk()
        self.wizard.window = Mock()
        self.wizard.language = "en"
        self.wizard.folder_dialog = None
        self.wizard._message = Mock()
        self.entry = Mock()
        self.entry.get_text.return_value = "previous selection"
        self.dialog = Mock()
        portal = patch("embercade.first_run_ui.native_portal_available", return_value=True)
        portal.start()
        self.addCleanup(portal.stop)

    def choose(self, *, file=False):
        with patch("embercade.first_run_ui.create_chooser", return_value=self.dialog) as create:
            self.wizard._choose_directory(self.entry, file=file)
        self.assertIsNone(self.wizard.folder_dialog)
        self.dialog.destroy.assert_called_once()
        return create

    def test_cancel_close_and_non_accept_responses_preserve_previous_entry(self):
        for response in (self.wizard.Gtk.ResponseType.CANCEL,
                         self.wizard.Gtk.ResponseType.DELETE_EVENT,
                         self.wizard.Gtk.ResponseType.OK):
            with self.subTest(response=response):
                self.dialog.reset_mock()
                self.entry.reset_mock()
                self.dialog.run.return_value = response
                self.dialog.get_filename.return_value = str(self.folder)
                create = self.choose()
                create.assert_called_once()
                self.entry.set_text.assert_not_called()

    def test_accept_valid_folder_updates_entry_once_and_owns_dialog_during_run(self):
        def accept():
            self.assertIsNotNone(self.wizard.folder_dialog)
            return self.wizard.Gtk.ResponseType.ACCEPT

        self.dialog.run.side_effect = accept
        self.dialog.get_filename.return_value = str(self.folder)
        self.choose()
        self.entry.set_text.assert_called_once_with(str(self.folder))

    def test_accept_valid_file_keeps_file_mode_and_translated_labels(self):
        for language in ("de", "en"):
            with self.subTest(language=language):
                self.dialog.reset_mock()
                self.entry.reset_mock()
                self.wizard.language = language
                self.dialog.run.return_value = self.wizard.Gtk.ResponseType.ACCEPT
                self.dialog.get_filename.return_value = str(self.source)
                create = self.choose(file=True)
                translate = Translator(language)
                self.assertEqual(create.call_args.kwargs["title"], translate("Choose file"))
                self.assertEqual(create.call_args.kwargs["accept_label"], translate("Use this file"))
                self.assertEqual(create.call_args.kwargs["cancel_label"], translate("Cancel"))
                self.assertTrue(create.call_args.kwargs["file"])
                self.entry.set_text.assert_called_once_with(str(self.source))

    def test_accept_wrong_type_remote_or_removed_selection_preserves_entry(self):
        for selected, file in ((str(self.source), False), (str(self.folder), True),
                               (None, False), (str(self.root / "removed drive"), False)):
            with self.subTest(selected=selected, file=file):
                self.dialog.reset_mock()
                self.entry.reset_mock()
                self.dialog.run.return_value = self.wizard.Gtk.ResponseType.ACCEPT
                self.dialog.get_filename.return_value = selected
                self.choose(file=file)
                self.entry.set_text.assert_not_called()

    def test_failed_native_and_fallback_runs_are_cleaned_up_with_readable_error(self):
        self.dialog.run.side_effect = RuntimeError("simulated chooser failure")
        fallback = Mock()
        fallback.run.side_effect = OSError("simulated fallback failure")
        with patch("embercade.first_run_ui.create_chooser", side_effect=[self.dialog, fallback]) as create:
            self.wizard._choose_directory(self.entry)
        self.assertIsNone(self.wizard.folder_dialog)
        self.dialog.destroy.assert_called_once()
        fallback.destroy.assert_called_once()
        self.entry.set_text.assert_not_called()
        self.wizard._message.assert_called_once()
        self.assertTrue(self.wizard._message.call_args.kwargs["error"])
        self.assertEqual([call.kwargs["use_native"] for call in create.call_args_list],
                         [True, False])

    def test_native_run_failure_retries_gtk_and_accepts_valid_selection(self):
        self.dialog.run.side_effect = RuntimeError("portal disappeared")
        fallback = Mock()
        fallback.run.return_value = self.wizard.Gtk.ResponseType.ACCEPT
        fallback.get_filename.return_value = str(self.folder)
        with patch("embercade.first_run_ui.create_chooser", side_effect=[self.dialog, fallback]) as create:
            self.wizard._choose_directory(self.entry)
        self.assertEqual([call.kwargs["use_native"] for call in create.call_args_list],
                         [True, False])
        self.dialog.destroy.assert_called_once()
        fallback.destroy.assert_called_once()
        self.assertIsNone(self.wizard.folder_dialog)
        self.entry.set_text.assert_called_once_with(str(self.folder))
        self.wizard._message.assert_not_called()

    def test_native_construction_failure_can_cancel_fallback_without_changing_entry(self):
        self.dialog.run.return_value = self.wizard.Gtk.ResponseType.CANCEL
        with patch("embercade.first_run_ui.create_chooser",
                   side_effect=[RuntimeError("native configuration failed"), self.dialog]) as create:
            self.wizard._choose_directory(self.entry)
        self.assertEqual([call.kwargs["use_native"] for call in create.call_args_list],
                         [True, False])
        self.dialog.destroy.assert_called_once()
        self.assertIsNone(self.wizard.folder_dialog)
        self.entry.set_text.assert_not_called()
        self.wizard._message.assert_not_called()

    def test_parent_close_hides_own_chooser_without_accepting(self):
        def parent_closes():
            signal, callback = self.wizard.window.connect.call_args.args
            self.assertEqual(signal, "destroy")
            callback(self.wizard.window)
            return self.wizard.Gtk.ResponseType.DELETE_EVENT

        self.dialog.run.side_effect = parent_closes
        self.choose()
        self.dialog.hide.assert_called_once()
        self.entry.set_text.assert_not_called()
        self.entry.grab_focus.assert_not_called()
        self.wizard.window.disconnect.assert_called_once_with(
            self.wizard.window.connect.return_value)

    def test_existing_open_chooser_prevents_second_dialog(self):
        self.wizard.folder_dialog = self.dialog
        with patch("embercade.first_run_ui.create_chooser") as create:
            self.wizard._choose_directory(self.entry)
        create.assert_not_called()
        self.dialog.destroy.assert_not_called()
        self.entry.set_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Opt-in real GTK lifecycle checks; no package manager or emulator is started.

Run with EMBERCADE_TEST_GTK=1 in a test display (Broadway also works).
These signal-driven checks do not establish visible interactive acceptance.
"""

import os
import unittest
import warnings
from unittest.mock import Mock

from embercade.first_run_ui import Wizard
from embercade.i18n import Translator


@unittest.skipUnless(os.environ.get("EMBERCADE_TEST_GTK") == "1", "opt-in GTK test display required")
class GtkDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from embercade.first_run_ui import _gtk
        cls.GLib, cls.Gtk = _gtk()

    def setUp(self):
        self.wizard = Wizard.__new__(Wizard)
        self.wizard.Gtk = self.Gtk
        self.wizard.window = self.Gtk.Window(title="Embercade automated GTK check")
        self.wizard.window.show_all()
        self.wizard.message_dialog = self.wizard.folder_dialog = None
        self.wizard.pad = Mock()
        self.wizard.busy, self.wizard.page = False, "checks"
        self.wizard._back = Mock()

    def tearDown(self):
        self.wizard.window.destroy()
        # Complete queued Wayland window destruction before non-GUI tests run.
        while self.Gtk.events_pending():
            self.Gtk.main_iteration_do(False)
        self.wizard.window.get_display().sync()

    def check_question(self, button=None):
        inspected, errors, result = [], [], []
        def inspect():
            dialog = self.wizard.message_dialog
            try:
                self.assertIsNotNone(dialog)
                self.assertTrue(dialog.get_visible())
                self.assertTrue(dialog.get_modal())
                self.assertTrue(dialog.get_destroy_with_parent())
                self.assertEqual(dialog.get_transient_for(), self.wizard.window)
                self.assertEqual(dialog.get_focus(), dialog.get_widget_for_response(self.Gtk.ResponseType.NO))
                inspected.append(True)
                if button:
                    self.wizard.pad.poll.return_value = {button}
                    self.wizard._poll_gamepad()
            except Exception as error:
                errors.append(error)
            finally:
                if dialog is not None:
                    dialog.response(self.Gtk.ResponseType.NO)
            return False
        def open_question():
            self.GLib.timeout_add(80, inspect)
            try:
                result.append(self.wizard._question("Install?", "Automated test; no installation."))
            finally:
                self.Gtk.main_quit()
            return False
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            self.GLib.idle_add(open_question)
            self.Gtk.main()
        if errors:
            raise errors[0]
        self.assertEqual(inspected, [True])
        self.assertEqual(result, [False])
        self.assertIsNone(self.wizard.message_dialog)
        self.assertEqual(self.wizard.page, "checks")
        self.wizard._back.assert_not_called()
        self.assertFalse([w for w in recorded if w.category.__name__ == "PyGTKDeprecationWarning"])

    def descendants(self, widget):
        yield widget
        if isinstance(widget, self.Gtk.Container):
            for child in widget.get_children():
                yield from self.descendants(child)

    def assert_action_visible(self, dialog, response):
        button = dialog.get_widget_for_response(response)
        self.assertTrue(button.get_visible())
        self.assertTrue(button.get_mapped())
        x, y = button.translate_coordinates(dialog, 0, 0)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertLessEqual(x + button.get_allocated_width(), dialog.get_allocated_width())
        self.assertLessEqual(y + button.get_allocated_height(), dialog.get_allocated_height())

    def body_widgets(self, dialog, body):
        labels = [widget for widget in self.descendants(dialog)
                  if isinstance(widget, self.Gtk.Label) and widget.get_text() == body]
        self.assertEqual(len(labels), 1)
        details = labels[0]
        viewport = details.get_ancestor(self.Gtk.Viewport)
        scroll = details.get_ancestor(self.Gtk.ScrolledWindow)
        self.assertFalse(details.get_layout().is_ellipsized())
        self.assertEqual(details.get_lines(), -1)
        self.assertLessEqual(details.get_layout().get_pixel_size().height,
                             details.get_allocated_height() + 1)
        return details, viewport, scroll

    def check_readable_short_body(self, title, body, *, question=False, error=False):
        failures = []
        response = self.Gtk.ResponseType.NO if question else self.Gtk.ResponseType.OK
        translated = Translator(self.wizard.language)(body)

        def inspect():
            dialog = self.wizard.message_dialog
            try:
                details, viewport, scroll = self.body_widgets(dialog, translated)
                self.assertLessEqual(dialog.get_allocated_height(),
                                     dialog.get_screen().get_height(),
                                     "An ordinary message must fit on the display")
                if scroll is not None:
                    adjustment = scroll.get_vadjustment()
                    self.assertLessEqual(adjustment.get_upper(), adjustment.get_page_size() + 1,
                                         "A short message must not require vertical scrolling")
                    self.assertLessEqual(details.get_layout().get_pixel_size().height,
                                         viewport.get_allocated_height() + 1)
                self.assert_action_visible(dialog, response)
                if question:
                    self.assert_action_visible(dialog, self.Gtk.ResponseType.YES)
            except BaseException as exc:
                failures.append(exc)
            finally:
                dialog.response(response)
            return False

        self.GLib.timeout_add(180, inspect)
        if question:
            self.assertFalse(self.wizard._question(title, body))
        else:
            self.wizard._message(title, body, error=error)
        if failures:
            raise failures[0]
        self.assertIsNone(self.wizard.message_dialog)

    def test_exact_ps3_success_is_fully_visible_in_both_languages(self):
        for language in ("de", "en"):
            with self.subTest(language=language):
                self.wizard.language = language
                self.check_readable_short_body(
                    "Check complete", "PS3 firmware is installed in Embercade's isolated profile.")

    def test_multisentence_error_and_confirmation_are_fully_readable(self):
        for language in ("de", "en"):
            with self.subTest(language=language):
                self.wizard.language = language
                self.check_readable_short_body(
                    "PS3 setup needs attention",
                    "Check your connection and PUP file, close RPCS3 and try again. Existing firmware is never replaced. If automatic download fails, select the official PUP downloaded in your browser.",
                    error=True,
                )
                self.check_readable_short_body(
                    "Install selected firmware?",
                    "RPCS3 will validate and install this PUP in a temporary Embercade profile. Only a successful installation is copied to your isolated profile. Existing firmware is preserved.",
                    question=True,
                )

    def test_long_localized_status_scrolls_to_last_line_with_visible_acknowledgment(self):
        self.wizard.language = "en"
        failures = []
        final_line = "Final test component 80"
        body = "\n".join([f"Missing test component {index}" for index in range(1, 80)] + [final_line])

        def inspect_bottom():
            dialog = self.wizard.message_dialog
            try:
                from gi.repository import Pango
                details, viewport, scroll = self.body_widgets(dialog, body)
                adjustment = scroll.get_vadjustment()
                self.assertAlmostEqual(adjustment.get_value() + adjustment.get_page_size(),
                                       adjustment.get_upper(), delta=1)
                position = details.get_layout().index_to_pos(len(body[:body.rindex(final_line)].encode()))
                _, label_y = details.translate_coordinates(viewport, 0, 0)
                line_top = label_y + position.y / Pango.SCALE
                line_bottom = line_top + position.height / Pango.SCALE
                self.assertGreaterEqual(line_top, -1, "The final line must be inside the viewport")
                self.assertLessEqual(line_bottom, viewport.get_allocated_height() + 1,
                                     "The final line must be fully readable after scrolling")
                self.assert_action_visible(dialog, self.Gtk.ResponseType.OK)
            except BaseException as exc:
                failures.append(exc)
            finally:
                dialog.response(self.Gtk.ResponseType.OK)
            return False

        def inspect_top():
            dialog = self.wizard.message_dialog
            try:
                details, viewport, scroll = self.body_widgets(dialog, body)
                self.assertIsNotNone(scroll)
                self.assertIsNotNone(viewport)
                adjustment = scroll.get_vadjustment()
                self.assertEqual(details.get_layout().get_line_count(), 80)
                self.assertGreater(adjustment.get_upper(), adjustment.get_page_size())
                self.assertLessEqual(dialog.get_allocated_height(),
                                     dialog.get_screen().get_height())
                self.assert_action_visible(dialog, self.Gtk.ResponseType.OK)
                adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
                self.GLib.timeout_add(100, inspect_bottom)
            except BaseException as exc:
                failures.append(exc)
                dialog.response(self.Gtk.ResponseType.OK)
            return False

        self.GLib.timeout_add(180, inspect_top)
        self.wizard._message("Host software", body)
        if failures:
            raise failures[0]

    def test_confirmation_lives_until_response_in_nested_main_loop(self):
        self.check_question()

    def test_gamepad_back_cancels_dialog_without_leaving_wizard_page(self):
        self.check_question("b")

    def test_gamepad_confirm_defaults_to_no(self):
        self.check_question("a")

    def test_closing_confirmation_is_not_approval(self):
        def close():
            self.wizard.message_dialog.response(self.Gtk.ResponseType.DELETE_EVENT)
            return False
        self.GLib.timeout_add(30, close)
        self.assertFalse(self.wizard._question("Install?", "No installation."))
        self.assertIsNone(self.wizard.message_dialog)

    def test_explicit_yes_is_approval(self):
        def approve():
            self.wizard.message_dialog.get_widget_for_response(self.Gtk.ResponseType.YES).clicked()
            return False
        self.GLib.timeout_add(30, approve)
        self.assertTrue(self.wizard._question("Install?", "No installation is invoked in this test."))
        self.assertIsNone(self.wizard.message_dialog)

"""Opt-in GTK controller tests with synthetic input and forbidden host mutation.

Run only in an isolated test display, e.g. Broadway. These dialog/input checks
are not hardware or emulator-exit acceptance.
"""
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import Mock, patch

from embercade.first_run_ui import Wizard, _gtk
from embercade.i18n import Translator
from tests.test_controller_setup_ui import FakePad, REPORT


@unittest.skipUnless(os.environ.get("EMBERCADE_TEST_GTK") == "1", "opt-in GTK test display required")
class ControllerSetupGtkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.GLib, cls.Gtk = _gtk()

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(TemporaryDirectory()))
        environment = {key: value for key, value in os.environ.items() if not key.startswith("EMBERCADE_")}
        environment.update(HOME=str(root), XDG_CONFIG_HOME=str(root / "config"),
                           XDG_DATA_HOME=str(root / "data"), XDG_STATE_HOME=str(root / "state"),
                           XDG_CACHE_HOME=str(root / "cache"))
        self.stack.enter_context(patch.dict(os.environ, environment, clear=True))
        self.pad = FakePad()
        self.stack.enter_context(patch("embercade.first_run_ui.Gamepad", return_value=self.pad))
        self.stack.enter_context(patch("embercade.first_run_ui.controller_compat.status", return_value=dict(REPORT)))
        self.backend = self.stack.enter_context(patch("embercade.first_run_ui.controller_compat.apply",
            side_effect=AssertionError("Host driver changes are forbidden in GTK tests")))
        self.clock = 10.0
        self.stack.enter_context(patch("embercade.first_run_ui.time.monotonic", side_effect=lambda: self.clock))
        self.config = root / "config/embercade.toml"
        self.wizard = Wizard(self.config, self.GLib, self.Gtk)
        # Sample input explicitly: no physical controller or timer race participates.
        self.GLib.source_remove(self.wizard.pad_source)
        self.wizard.pad_source = self.GLib.timeout_add(60000, lambda: True)
        self.wizard._run_arguments = Mock(side_effect=AssertionError("Setup actions forbidden"))
        self.wizard._message = Mock()
        self.wizard._back = Mock()
        self.wizard.language = "en"
        self.wizard._go("controller")

    def tearDown(self):
        if not self.wizard.closed:
            self.GLib.idle_add(lambda: (self.wizard.window.destroy(), False)[1])
            self.Gtk.main()
        while self.Gtk.events_pending():
            self.Gtk.main_iteration_do(False)
        self.wizard.window.get_display().sync()
        self.backend.assert_not_called()
        self.assertFalse(self.config.exists())
        self.stack.close()

    def descendants(self, widget):
        yield widget
        if isinstance(widget, self.Gtk.Container):
            for child in widget.get_children():
                yield from self.descendants(child)

    def run_chord(self, samples, *, passed):
        failures = []
        def drive():
            try:
                dialog = self.wizard.message_dialog
                self.assertIs(dialog, self.wizard.controller_test_dialog)
                self.assertTrue(dialog.get_modal())
                self.assertTrue(dialog.get_visible())
                self.assertEqual(dialog.get_transient_for(), self.wizard.window)
                for offset, buttons, connected, generation, phase in samples:
                    self.clock = 10.0 + offset
                    self.pad.sample(buttons, connected=connected, generation=generation)
                    self.wizard._poll_gamepad()
                    if phase is not None:
                        self.assertEqual(self.wizard.controller_test.phase, phase)
                    self.assertEqual(self.wizard.page, "controller")
                    self.wizard._back.assert_not_called()
                if not passed:
                    dialog.response(self.Gtk.ResponseType.CANCEL)
            except BaseException as error:
                failures.append(error)
                if self.wizard.message_dialog is not None:
                    self.wizard.message_dialog.response(self.Gtk.ResponseType.CANCEL)
            return False
        def watchdog():
            failures.append(AssertionError("Controller dialog did not finish after its final sample"))
            if self.wizard.message_dialog is not None:
                self.wizard.message_dialog.response(self.Gtk.ResponseType.CANCEL)
            return False
        self.GLib.timeout_add(20, drive)
        guard = self.GLib.timeout_add(1000, watchdog)
        try:
            self.wizard._start_controller_test()
        finally:
            if self.GLib.MainContext.default().find_source_by_id(guard):
                self.GLib.source_remove(guard)
        if failures:
            raise failures[0]
        expected = (self.wizard.hotkey, self.pad.generation) if passed else None
        self.assertEqual(self.wizard.controller_test_result, expected)
        self.assertIsNone(self.wizard.message_dialog)
        self.assertIsNone(self.wizard.controller_test_dialog)
        self.assertIsNone(self.wizard.controller_test)
        self.assertTrue(self.wizard._controller_release_pending)
        self.wizard._run_arguments.assert_not_called()

    def test_bilingual_host_progress_updates_without_completing_transaction(self):
        messages={
            'checking':'Checking installed software and available packages…',
            'confirmation':'Please review and confirm the installation in the terminal.',
            'repository':'Installing host software: downloads, package checks and completion hooks…',
            'community':'Building additional host software. This can take several minutes; follow the terminal output.',
        }
        transaction=Mock();transaction.result.return_value=None
        for language in ('de','en'):
            self.wizard.language=language;self.wizard._go('host')
            self.wizard.progress=self.wizard._label('Working… Please wait.')
            self.wizard.window.show_all()
            for phase,message in messages.items():
                transaction.progress.return_value=dict(phase=phase,started=10.0,updated=10.0)
                self.clock=205.0
                self.assertTrue(self.wizard._host_poll(transaction))
                text=self.wizard.progress.get_text()
                self.assertIn(Translator(language)(message),text)
                self.assertIn('3:15',text)
                self.assertNotIn('ScreenScraper',text)
        transaction.reap.assert_not_called()
        self.wizard._run_arguments.assert_not_called()

    def test_separate_bilingual_page_and_selection_does_not_continue_or_save(self):
        english = "Choose your exit combination, check compatibility and try it here."
        for language in ("de", "en"):
            with self.subTest(language=language):
                self.wizard.language = language
                self.wizard._go("controller")
                labels = [widget.get_text() for widget in self.descendants(self.wizard.window)
                          if isinstance(widget, self.Gtk.Label)]
                self.assertIn(Translator(language)(english), labels)
                if language == "de":
                    self.assertNotEqual(Translator(language)(english), english)
                self.wizard.controller_test_result = (self.wizard.hotkey, self.pad.generation)
                selected = "guide-start" if self.wizard.hotkey == "back-start" else "back-start"
                self.wizard.hotkey_choice.set_active_id(selected)
                self.assertEqual(self.wizard.page, "controller")
                self.assertEqual(self.wizard.hotkey_choice.get_active_id(), selected)
                self.assertIsNone(self.wizard.controller_test_result)
                self.wizard._run_arguments.assert_not_called()

    def test_both_presets_require_initial_release_sustained_overlap_and_final_release(self):
        for preset, modifier in (("guide-start", "guide"), ("back-start", "back")):
            with self.subTest(preset=preset):
                self.clock = 10.0
                self.wizard.hotkey = preset
                self.run_chord([
                    (0.00, {modifier, "start"}, True, 1, "release"),
                    (0.01, set(), True, 1, "press"),
                    (0.02, {modifier, "start"}, True, 1, "hold"),
                    (0.36, {modifier, "start"}, True, 1, "hold"),
                    (0.38, {modifier, "start"}, True, 1, "release_after"),
                    (0.40, {modifier}, True, 1, "release_after"),
                    (0.42, set(), True, 1, "passed"),
                ], passed=True)

    def test_brief_guide_pulse_is_not_accepted(self):
        self.wizard.hotkey = "guide-start"
        self.run_chord([
            (0.00, set(), True, 1, "press"),
            (0.01, {"guide", "start"}, True, 1, "hold"),
            (0.10, {"start"}, True, 1, "press"),
            (0.60, set(), True, 1, "press"),
        ], passed=False)

    def test_reconnect_generation_discards_progress_and_requires_new_release(self):
        self.wizard.hotkey = "guide-start"
        self.run_chord([
            (0.00, set(), True, 1, "press"),
            (0.01, {"guide", "start"}, True, 1, "hold"),
            (0.40, {"guide", "start"}, True, 1, "release_after"),
            (0.42, {"guide", "start"}, True, 2, "release"),
            (0.44, set(), True, 2, "press"),
            (0.46, {"guide", "start"}, True, 2, "hold"),
            (0.82, {"guide", "start"}, True, 2, "release_after"),
            (0.84, set(), True, 2, "passed"),
        ], passed=True)

    def test_b_cancels_only_test_and_wizard_waits_for_all_buttons_to_release(self):
        self.wizard.hotkey = "guide-start"
        self.run_chord([
            (0.00, set(), True, 1, "press"),
            (0.01, {"start"}, True, 1, "press"),
            (0.02, {"start", "b"}, True, 1, None),
        ], passed=False)
        for buttons in ({"start", "b"}, {"b"}):
            self.pad.sample(buttons)
            self.wizard._poll_gamepad()
            self.assertTrue(self.wizard._controller_release_pending)
            self.wizard._back.assert_not_called()
        self.pad.sample(set())
        self.wizard._poll_gamepad()
        self.assertFalse(self.wizard._controller_release_pending)
        self.wizard._back.assert_not_called()
        self.pad.sample({"b"})
        self.wizard._poll_gamepad()
        self.wizard._back.assert_called_once_with()

    def test_refusing_real_confirmation_never_reaches_driver_backend(self):
        def decline():
            self.wizard.message_dialog.get_widget_for_response(self.Gtk.ResponseType.NO).clicked()
            return False
        self.GLib.timeout_add(20, decline)
        self.wizard._adjust_controller("enable")
        self.backend.assert_not_called()
        self.assertFalse(self.wizard.busy)
        self.assertEqual(self.wizard.page, "controller")

    def test_parent_close_during_test_does_not_render_or_open_another_dialog(self):
        self.wizard._render = Mock()
        def open_test():
            self.GLib.timeout_add(20, lambda: (self.wizard.window.destroy(), False)[1])
            self.wizard._start_controller_test()
            return False
        self.GLib.idle_add(open_test)
        self.Gtk.main()
        self.assertTrue(self.wizard.closed)
        self.assertIsNone(self.wizard.controller_test_result)
        self.assertIsNone(self.wizard.message_dialog)
        self.wizard._render.assert_not_called()
        self.wizard._message.assert_not_called()

    def test_timer_opened_dialog_keeps_sampling_chord_cancel_and_timeout(self):
        # GLib sources are non-reentrant: the ordinary poll timer opens the
        # modal here. The test must still receive fresh samples inside run().
        for outcome in ("pass", "cancel", "timeout"):
            with self.subTest(outcome=outcome):
                self.clock = 10.0
                self.pad.previous.clear()
                self.pad.sample({"a"})
                self.wizard.hotkey = "guide-start"
                self.wizard._controller_release_pending = False
                self.wizard._message.reset_mock()
                self.wizard._render()
                buttons = [widget for widget in self.descendants(self.wizard.window)
                           if isinstance(widget, self.Gtk.Button)
                           and widget.get_label() == self.wizard._t("Test exit combination")]
                self.assertEqual(len(buttons), 1)
                buttons[0].grab_focus()
                observed, failures, stage = [], [], [0]
                sequence = [(10.1, set()), (10.2, {"guide", "start"}),
                            (10.6, {"guide", "start"}), (10.7, set())]
                if outcome == "cancel":
                    sequence = [(10.1, set()), (10.2, {"start", "b"})]
                elif outcome == "timeout":
                    sequence = [(10.1, set()), (41.0, set())]

                def feed():
                    if self.wizard.controller_test_dialog is not None:
                        observed.append(True)
                        if stage[0] < len(sequence):
                            self.clock, pressed = sequence[stage[0]]
                            self.pad.sample(pressed)
                            stage[0] += 1
                    elif observed:
                        self.Gtk.main_quit()
                        return False
                    return True

                def watchdog():
                    failures.append("Timer-opened controller dialog stopped sampling live input")
                    if self.wizard.message_dialog is not None:
                        self.wizard.message_dialog.response(self.Gtk.ResponseType.CANCEL)
                    self.Gtk.main_quit()
                    return False

                self.GLib.source_remove(self.wizard.pad_source)
                self.wizard.pad_source = self.GLib.timeout_add(10, self.wizard._poll_gamepad)
                sources = [self.GLib.timeout_add(90, feed), self.GLib.timeout_add(1500, watchdog)]
                try:
                    self.Gtk.main()
                finally:
                    for source in sources:
                        if self.GLib.MainContext.default().find_source_by_id(source):
                            self.GLib.source_remove(source)
                    self.GLib.source_remove(self.wizard.pad_source)
                    self.wizard.pad_source = self.GLib.timeout_add(60000, lambda: True)
                self.assertFalse(failures, failures)
                self.assertTrue(observed)
                self.assertEqual(self.wizard.page, "controller")
                self.wizard._back.assert_not_called()
                self.assertEqual(self.wizard.controller_test_result,
                                 ("guide-start", self.pad.generation) if outcome == "pass" else None)
                if outcome == "timeout":
                    self.wizard._message.assert_called_once()
                    self.assertEqual(self.wizard._message.call_args.args[0], "Exit combination not detected")


if __name__ == "__main__":
    unittest.main()

"""Controller-page decisions use mocked backends and never touch host drivers."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from embercade.first_run_ui import Wizard


class FakePad:
    def __init__(self):
        self.previous = set()
        self.pressed = set()
        self.controller = object()
        self.generation = 1
        self.name = "Synthetic controller"

    def sample(self, pressed, *, connected=True, generation=None):
        self.pressed = set(pressed)
        self.controller = object() if connected else None
        if generation is not None:
            self.generation = generation

    def poll(self):
        pressed = self.pressed if self.controller else set()
        edges = pressed - self.previous
        self.previous = set(pressed)
        return edges

    def close(self):
        self.controller = None


REPORT = {"driver_present": True, "shift_disabled": False, "can_enable": True,
          "can_undo": False, "devices": [{"name": "Synthetic controller"}], "code": "ready"}


class ControllerSetupUiTests(unittest.TestCase):
    def setUp(self):
        status = patch("embercade.first_run_ui.controller_compat.status", return_value=dict(REPORT))
        apply = patch("embercade.first_run_ui.controller_compat.apply",
                      side_effect=AssertionError("host adjustment forbidden in UI test"))
        self.status, self.apply = status.start(), apply.start()
        self.addCleanup(status.stop)
        self.addCleanup(apply.stop)
        self.wizard = Wizard.__new__(Wizard)
        self.wizard.language = "en"
        self.wizard.page = "controller"
        self.wizard.busy = False
        self.wizard.message_dialog = self.wizard.folder_dialog = None
        self.wizard.hotkey = "back-start"
        self.wizard.pad = FakePad()
        self.wizard.state = SimpleNamespace(config_path=Path("/synthetic/settings.toml"))
        self.wizard.controller_test_result = None
        self.wizard._render = Mock()
        self.wizard._run_arguments = Mock()
        self.wizard._question = Mock(return_value=False)
        self.wizard._message = Mock()
        self.wizard.window = Mock()
        self.wizard._go = Mock()

    def test_changing_selection_stays_on_page_and_invalidates_test_without_saving(self):
        self.wizard.controller_test_result = ("back-start", 1)
        self.wizard._choose_hotkey("guide-start")
        self.assertEqual(self.wizard.page, "controller")
        self.assertEqual(self.wizard.hotkey, "guide-start")
        self.assertIsNone(self.wizard.controller_test_result)
        self.wizard._render.assert_called_once_with()
        self.wizard._run_arguments.assert_not_called()
        self.apply.assert_not_called()

    def test_refusing_driver_confirmation_never_calls_backend(self):
        for operation in ("enable", "undo"):
            with self.subTest(operation=operation):
                self.wizard._adjust_controller(operation)
                self.assertFalse(self.wizard.busy)
                self.wizard.window.set_sensitive.assert_not_called()
                self.apply.assert_not_called()
        self.assertEqual(self.wizard._question.call_count, 2)

    def test_busy_or_modal_state_does_not_open_another_driver_confirmation(self):
        for busy, modal in ((True, None), (False, object())):
            self.wizard.busy, self.wizard.message_dialog = busy, modal
            self.wizard._adjust_controller("enable")
        self.wizard._question.assert_not_called()
        self.apply.assert_not_called()

    def test_unverified_and_reconnected_controller_require_confirmation_before_save(self):
        for tested in (None, ("back-start", 0), ("guide-start", 1)):
            with self.subTest(tested=tested):
                self.wizard.controller_test_result = tested
                self.wizard._save_controller()
                self.wizard._run_arguments.assert_not_called()
        self.assertEqual(self.wizard._question.call_count, 3)
        self.wizard.controller_test_result = ("back-start", 1)
        self.wizard._save_controller()
        self.wizard._run_arguments.assert_called_once_with(
            ("--config", "/synthetic/settings.toml", "installer", "controller", "--exit-hotkey", "back-start"),
            self.wizard._controller_saved,
        )
        self.apply.assert_not_called()

    def test_pending_reconnect_reports_need_for_live_retest(self):
        self.wizard.busy = True
        self.wizard._controller_adjusted({"ok": False, "code": "reconnect_pending"})
        self.assertFalse(self.wizard.busy)
        self.assertTrue(self.wizard._controller_release_pending)
        self.wizard._go.assert_called_once_with("controller")
        self.assertIn("has not reconnected", self.wizard._message.call_args.args[1])
        self.assertTrue(self.wizard._message.call_args.kwargs["error"])

    def test_remaining_tick_edges_do_not_reactivate_button_after_modal_returns(self):
        class Button:
            def clicked(button):
                clicked()
                self.wizard._controller_release_pending = True
            def get_toplevel(button):
                return self.wizard.window
        self.wizard.Gtk = SimpleNamespace(Button=Button, CheckButton=type("Check", (), {}),
                                         ComboBox=type("Combo", (), {}))
        self.wizard.GLib = SimpleNamespace(idle_add=Mock())
        clicked = Mock()
        self.wizard.window.get_focus.return_value = Button()
        self.wizard.pad.sample({"a", "start"})
        self.wizard._poll_gamepad()
        clicked.assert_not_called()
        self.wizard.GLib.idle_add.assert_called_once()
        callback, focused = self.wizard.GLib.idle_add.call_args.args
        self.assertFalse(callback(focused))
        clicked.assert_called_once_with()
        self.assertTrue(self.wizard._controller_release_pending)

    def test_reconnect_invalidates_previous_result_and_its_visible_status(self):
        self.wizard.controller_test_result = ("back-start", 1)
        self.wizard.controller_test_summary = Mock()
        self.wizard.pad.sample(set(), generation=2)
        self.wizard._poll_gamepad()
        self.assertIsNone(self.wizard.controller_test_result)
        self.wizard.controller_test_summary.set_text.assert_called_once_with(
            "The exit combination has not been tested in this session.")


if __name__ == "__main__":
    unittest.main()

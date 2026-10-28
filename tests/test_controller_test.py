"""Synthetic held-button timelines; no live device or host setting changes."""

import unittest

from embercade.controller_test import ChordTest, HOLD_SECONDS


class ChordTestTests(unittest.TestCase):
    def test_both_presets_require_overlap_and_final_release(self):
        for hotkey, modifier in (("guide-start", "guide"), ("back-start", "back")):
            with self.subTest(hotkey=hotkey):
                exercise = ChordTest(hotkey)
                self.assertEqual(exercise.phase, "release")
                self.assertEqual(exercise.update(set(), True, 0), "press")
                self.assertEqual(exercise.update({modifier}, True, 1), "press")
                self.assertEqual(exercise.update({modifier, "start"}, True, 2), "hold")
                self.assertEqual(exercise.update({modifier, "start"}, True, 2.3), "hold")
                self.assertEqual(exercise.update({modifier, "start"}, True, 2 + HOLD_SECONDS),
                                 "release_after")
                self.assertEqual(exercise.update({modifier}, True, 2.4), "release_after")
                self.assertEqual(exercise.update(set(), True, 2.5), "passed")

    def test_buttons_held_while_starting_cannot_complete_test(self):
        exercise = ChordTest("guide-start")
        for now in (0, 1, 2):
            self.assertEqual(exercise.update({"guide", "start"}, True, now), "release")
        self.assertEqual(exercise.update({"a"}, True, 3), "release")
        self.assertEqual(exercise.update(set(), True, 4), "press")
        self.assertEqual(exercise.update({"guide", "start"}, True, 5), "hold")

    def test_nonoverlapping_buttons_are_not_combined_into_a_chord(self):
        exercise = ChordTest("guide-start")
        exercise.update(set(), True, 0)
        for now, pressed in ((1, {"start"}), (2, set()), (3, {"guide"}),
                             (4, set()), (5, {"start"}), (6, {"guide"})):
            self.assertEqual(exercise.update(pressed, True, now), "press")

    def test_short_delayed_guide_pulse_does_not_pass(self):
        exercise = ChordTest("guide-start")
        exercise.update(set(), True, 0)
        self.assertEqual(exercise.update({"start"}, True, 1), "press")
        self.assertEqual(exercise.update({"guide", "start"}, True, 1.1), "hold")
        self.assertEqual(exercise.update({"start"}, True, 1.2), "press")
        self.assertEqual(exercise.update(set(), True, 2), "press")

    def test_interrupted_overlap_requires_a_new_complete_hold(self):
        exercise = ChordTest("back-start")
        exercise.update(set(), True, 0)
        exercise.update({"back", "start"}, True, 1)
        self.assertEqual(exercise.update({"back"}, True, 1.3), "press")
        self.assertEqual(exercise.update({"back", "start"}, True, 1.4), "hold")
        self.assertEqual(exercise.update({"back", "start"}, True, 1.7), "hold")
        self.assertEqual(exercise.update({"back", "start"}, True, 1.4 + HOLD_SECONDS),
                         "release_after")

    def test_other_preset_modifier_does_not_pass(self):
        for hotkey, other in (("guide-start", "back"), ("back-start", "guide")):
            with self.subTest(hotkey=hotkey):
                exercise = ChordTest(hotkey)
                exercise.update(set(), True, 0)
                self.assertEqual(exercise.update({other, "start"}, True, 1), "press")
                self.assertEqual(exercise.update({other, "start"}, True, 2), "press")
                self.assertEqual(exercise.update(set(), True, 3), "press")

    def test_all_buttons_must_be_released_before_navigation_can_resume(self):
        exercise = ChordTest("guide-start")
        exercise.update(set(), True, 0)
        exercise.update({"guide", "start", "a"}, True, 1)
        exercise.update({"guide", "start", "a"}, True, 1.5)
        self.assertEqual(exercise.update({"a"}, True, 2), "release_after")
        self.assertEqual(exercise.update(set(), True, 3), "passed")

    def test_disconnect_and_reconnect_discard_previous_hold(self):
        exercise = ChordTest("guide-start")
        exercise.update(set(), True, 0, device_id=1)
        exercise.update({"guide", "start"}, True, 1, device_id=1)
        self.assertEqual(exercise.update(set(), False, 2, device_id=1), "release")
        self.assertEqual(exercise.update({"guide", "start"}, True, 3, device_id=2), "release")
        self.assertEqual(exercise.update(set(), True, 4, device_id=2), "press")
        self.assertEqual(exercise.update({"guide", "start"}, True, 5, device_id=2), "hold")
        self.assertEqual(exercise.update({"guide", "start"}, True, 5.5, device_id=2), "release_after")
        self.assertEqual(exercise.update(set(), True, 6, device_id=2), "passed")

    def test_replaced_device_cannot_complete_old_devices_chord(self):
        exercise = ChordTest("back-start")
        exercise.update(set(), True, 0, device_id="first")
        exercise.update({"back", "start"}, True, 1, device_id="first")
        self.assertEqual(exercise.update({"back", "start"}, True, 2, device_id="replacement"),
                         "release")
        self.assertEqual(exercise.update(set(), True, 3, device_id="replacement"), "press")

    def test_disconnection_after_hold_still_requires_a_new_exercise(self):
        exercise = ChordTest("guide-start")
        exercise.update(set(), True, 0)
        exercise.update({"guide", "start"}, True, 1)
        exercise.update({"guide", "start"}, True, 1.5)
        self.assertEqual(exercise.update(set(), False, 2), "release")
        self.assertEqual(exercise.update(set(), True, 3), "press")

    def test_success_stays_visible_until_connection_changes(self):
        exercise = ChordTest("back-start")
        exercise.update(set(), True, 0)
        exercise.update({"back", "start"}, True, 1)
        exercise.update({"back", "start"}, True, 1.5)
        self.assertEqual(exercise.update(set(), True, 2), "passed")
        self.assertEqual(exercise.update({"a"}, True, 3), "passed")
        self.assertEqual(exercise.update(set(), False, 4), "release")

    def test_backwards_clock_cannot_complete_a_hold(self):
        exercise = ChordTest("guide-start")
        exercise.update(set(), True, 10)
        exercise.update({"guide", "start"}, True, 11)
        self.assertEqual(exercise.update({"guide", "start"}, True, 1), "release")
        self.assertEqual(exercise.update(set(), True, 2), "press")

    def test_invalid_preset_or_sample_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            ChordTest("custom")
        exercise = ChordTest("guide-start")
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "finite"):
                exercise.update(set(), True, value)


if __name__ == "__main__":
    unittest.main()

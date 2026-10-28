from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from embercade.doctor import report
from embercade.paths import EmbercadePaths
from embercade.special_input import SpecialInputSummary, classify_input_tags


class _NoEmulators:
    @staticmethod
    def probe_all() -> dict[str, object]:
        return {}


class SpecialInputTests(unittest.TestCase):
    def test_udev_tags_keep_pointer_wheel_and_gun_classes_separate(self) -> None:
        summary = classify_input_tags((
            {"ID_INPUT_MOUSE": "1"},
            {"ID_INPUT_MOUSE": "1", "ID_INPUT_GUN": "1"},
            {"ID_INPUT_JOYSTICK": "1", "ID_INPUT_WHEEL": "1"},
            {"ID_INPUT_MOUSE": "1", "ID_INPUT_TRACKBALL": "1"},
        ))
        self.assertEqual((summary.guns, summary.wheels, summary.trackballs, summary.mouse_pointers),
                         (1, 1, 1, 3))

    def test_no_special_hardware_is_informational_not_a_doctor_failure(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            output = StringIO()
            with patch("embercade.doctor.inspect_special_inputs", return_value=SpecialInputSummary()):
                baseline = report(paths, _NoEmulators(), environment={}, stream=output)
            self.assertIn("Lightguns   PREPARED / UNVALIDATED; udev gun nodes: 0", output.getvalue())
            self.assertIn("Wheels      PREPARED / UNVALIDATED; udev wheel nodes: 0", output.getvalue())
            self.assertIn("Trackballs  PREPARED / UNVALIDATED; explicitly tagged nodes: 0", output.getvalue())
            self.assertNotIn("Special controllers (structural only; no hardware READY claim):\n  FATAL", output.getvalue())
            output2 = StringIO()
            with patch("embercade.doctor.inspect_special_inputs", return_value=SpecialInputSummary(probe_available=False)):
                self.assertEqual(report(paths, _NoEmulators(), environment={}, stream=output2), baseline)
            self.assertIn("udev probe unavailable (optional)", output2.getvalue())

    def test_no_tags_never_promote_ordinary_mouse_to_trackball(self) -> None:
        summary = classify_input_tags(({"ID_INPUT_MOUSE": "1"}, {}))
        self.assertEqual(summary.trackballs, 0)
        self.assertEqual(summary.mouse_pointers, 1)

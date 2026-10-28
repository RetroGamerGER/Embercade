"""Check the pinned Dolphin compatibility patch against its installed runtime."""

import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest


PROJECT = Path(__file__).resolve().parents[1]
RUNTIME_PYTHON = PROJECT / ".work/runtime/venv/bin/python"


def _key_bitmap(codes: list[int]) -> str:
    bits = sum(1 << code for code in codes)
    words = [(bits >> offset) & ((1 << 64) - 1) for offset in range(0, 384, 64)]
    return " ".join(f"{word:x}" for word in reversed(words)) + "\n"


@unittest.skipUnless(RUNTIME_PYTHON.is_file(), "prepared compatibility runtime required")
class DolphinButtonOrderTests(unittest.TestCase):
    def test_extra_linux_key_is_not_mistaken_for_gamecube_button(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for event, codes in {
                "event1": list(range(304, 315)),
                "event2": [167, *range(304, 319)],
            }.items():
                bitmap = root / event / "device/capabilities/key"
                bitmap.parent.mkdir(parents=True)
                bitmap.write_text(_key_bitmap(codes), encoding="ascii")

            probe = """
import json
import os
from pathlib import Path
from types import SimpleNamespace
from batocera_launch_dolphin import controllers, emulator
controllers._INPUT_SYSFS = Path(os.environ['EMBERCADE_TEST_SYSFS'])
def pad(event, count):
    return SimpleNamespace(device_path='/dev/input/' + event, button_count=count)
usb = controllers._sdl_to_dolphin_evdev_buttons(pad('event1', 11))
bluetooth = controllers._sdl_to_dolphin_evdev_buttons(pad('event2', 16))
bluetooth_exit = emulator._desktop_exit_binding(
    pad('event2', 16), SimpleNamespace(id='10'), SimpleNamespace(id='11')
)
bad_count = controllers._sdl_to_dolphin_evdev_buttons(pad('event2', 15))
generic_exit = emulator._desktop_exit_binding(
    pad('event2', 15), SimpleNamespace(id='6'), SimpleNamespace(id='7')
)
os.environ.pop('EMBERCADE_DESKTOP')
non_desktop = controllers._sdl_to_dolphin_evdev_buttons(pad('event2', 16))
print(json.dumps([usb, bluetooth, bluetooth_exit, bad_count, generic_exit, non_desktop]))
"""
            env = os.environ.copy()
            env["EMBERCADE_DESKTOP"] = "1"
            env["EMBERCADE_TEST_SYSFS"] = str(root)
            result = subprocess.run(
                [str(RUNTIME_PYTHON), "-c", probe],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            usb, bluetooth, bluetooth_exit, bad_count, generic_exit, non_desktop = json.loads(result.stdout)
            self.assertEqual(usb, {})
            self.assertEqual(bluetooth["0"], 1)
            self.assertEqual(bluetooth["1"], 2)
            self.assertEqual(bluetooth["15"], 0)
            self.assertEqual(bluetooth_exit, "`Button 11` & `Button 12`")
            self.assertEqual(bad_count, {})
            self.assertEqual(generic_exit, "`Button 6` & `Button 7`")
            self.assertEqual(non_desktop, {})


if __name__ == "__main__":
    unittest.main()

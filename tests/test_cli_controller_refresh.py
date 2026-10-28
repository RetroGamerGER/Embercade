from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, sentinel
import unittest

from embercade.cli import main
from embercade.controller import ControllerDevice


class CliControllerRefreshTests(unittest.TestCase):
    def test_each_launch_uses_a_fresh_controller_enumeration_after_reconnect(self) -> None:
        old = ControllerDevice(
            index=0,
            guid="030081b85e0400008e02000010010000",
            name="Xbox 360 Controller",
            device_path=Path("/dev/input/event23"),
            buttons=11,
            hats=1,
            axes=6,
            mapping="mapping",
            real_name="Microsoft X-Box 360 pad",
            usb_vendor="045e",
            usb_product="028e",
            kernel_driver="xpad",
        )
        new = replace(old, index=4, device_path=Path("/dev/input/event31"))
        with TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"EMBERCADE_PROJECT_ROOT": directory}, clear=False
        ), patch(
            "embercade.cli.prepare_launch_layout"
        ), patch(
            "embercade.cli.enumerate_sdl_game_controllers",
            side_effect=((old,), (new,)),
        ) as enumerate_mock, patch(
            "embercade.cli.write_es_input_overrides"
        ) as input_override, patch(
            "embercade.cli.create_launch_plan",
            side_effect=(sentinel.old_plan, sentinel.new_plan),
        ) as create_plan, patch(
            "embercade.cli.run_launch", return_value=0
        ):
            argv = ["launch", "--system", "nes", "--rom", "/read-only/game.nes"]
            self.assertEqual(main(argv), 0)
            self.assertEqual(main(argv), 0)

        self.assertEqual(enumerate_mock.call_count, 2)
        self.assertEqual(input_override.call_count, 2)
        self.assertEqual(create_plan.call_args_list[0].kwargs["controllers"], (old,))
        self.assertEqual(create_plan.call_args_list[1].kwargs["controllers"], (new,))
        self.assertEqual(new.player_one_arguments()[1], "4")
        self.assertIn("/dev/input/event31", new.player_one_arguments())
        self.assertNotIn("/dev/input/event23", new.player_one_arguments())

    def test_second_pad_disconnect_and_reconnect_is_reflected_at_each_launch(self) -> None:
        first = ControllerDevice(
            0, "030081b85e0400008e02000010010000", "Xbox 360 Controller",
            Path("/dev/input/event23"), 11, 1, 6, "mapping",
            real_name="Microsoft X-Box 360 pad",
        )
        second = replace(first, index=1, device_path=Path("/dev/input/event24"))
        reconnected = replace(second, index=3, device_path=Path("/dev/input/event31"))
        with TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"EMBERCADE_PROJECT_ROOT": directory}, clear=False
        ), patch("embercade.cli.prepare_launch_layout"), patch(
            "embercade.cli.enumerate_sdl_game_controllers",
            side_effect=((first, second), (first,), (first, reconnected)),
        ), patch("embercade.cli.write_es_input_overrides"), patch(
            "embercade.cli.create_launch_plan", return_value=sentinel.plan
        ) as create_plan, patch("embercade.cli.run_launch", return_value=0):
            for _ in range(3):
                self.assertEqual(main(["launch", "--system", "nes",
                                       "--rom", "/read-only/game.nes"]), 0)
        self.assertEqual([call.kwargs["controllers"] for call in create_plan.call_args_list],
                         [(first, second), (first,), (first, reconnected)])


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import Mock, call, patch
import os
import signal
import subprocess
import sys

from embercade.provider_runner import (
    ProviderRunnerError,
    _terminate_provider_process_group,
    _watch_steam_exit_chord,
    appimage_mounts,
    build_host_provider_command,
    main as provider_main,
    run_host_provider,
    service_control_environment,
    tag_xenia_windows_once,
    translate_provider_argument,
    translate_sandbox_path,
)


class ProviderRunnerTests(unittest.TestCase):
    def test_service_control_uses_host_runtime_without_changing_provider_environment(self) -> None:
        environment = {
            "XDG_RUNTIME_DIR": "/userdata/system/xdg/runtime/embercade",
            "EMBERCADE_HOST_SESSION_RUNTIME_ROOT": "/run/user/1000",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
            "XDG_DATA_HOME": "/userdata/system/xdg/data/embercade",
        }
        controlled = service_control_environment(environment)
        self.assertEqual(controlled["XDG_RUNTIME_DIR"], "/run/user/1000")
        self.assertEqual(controlled["XDG_DATA_HOME"], environment["XDG_DATA_HOME"])
        self.assertEqual(controlled["DBUS_SESSION_BUS_ADDRESS"], environment["DBUS_SESSION_BUS_ADDRESS"])
        self.assertEqual(environment["XDG_RUNTIME_DIR"], "/userdata/system/xdg/runtime/embercade")

    def test_service_control_without_valid_host_runtime_does_not_invent_one(self) -> None:
        for host_runtime in (None, "", "relative/runtime"):
            with self.subTest(host_runtime=host_runtime):
                environment = {"XDG_RUNTIME_DIR": "/private/runtime"}
                if host_runtime is not None:
                    environment["EMBERCADE_HOST_SESSION_RUNTIME_ROOT"] = host_runtime
                self.assertEqual(service_control_environment(environment), environment)

    def test_interrupted_runner_stops_only_its_service_in_host_runtime_context(self) -> None:
        environment = {
            "PATH": "/usr/bin",
            "XDG_RUNTIME_DIR": "/userdata/system/xdg/runtime/embercade",
            "EMBERCADE_HOST_SESSION_RUNTIME_ROOT": "/run/user/1000",
            "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": "/external/Xenia.AppImage",
            "EMBERCADE_EXTERNAL_PROVIDER_UNIT": "embercade-xenia",
        }
        process = Mock()
        process.wait.side_effect = (KeyboardInterrupt(), 0)
        process.poll.return_value = None
        with (
            patch.dict("os.environ", environment, clear=True),
            patch("embercade.provider_runner.build_host_provider_command", return_value=("delegated-provider",)),
            patch("embercade.provider_runner.shutil.which", side_effect=lambda name, **kwargs: f"/usr/bin/{name}"),
            patch("embercade.provider_runner.signal.signal"),
            patch("embercade.provider_runner.subprocess.Popen", return_value=process),
            patch("embercade.provider_runner.subprocess.run") as run,
            patch("builtins.print"),
        ):
            self.assertEqual(provider_main(("/roms/game.iso",)), 130)
            self.assertEqual(dict(os.environ), environment)
        run.assert_called_once_with(
            ("/usr/bin/systemctl", "--user", "stop", "embercade-xenia.service"),
            env={**environment, "XDG_RUNTIME_DIR": "/run/user/1000"},
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.terminate.assert_called_once_with()

    def test_command_preserves_provider_and_rom_as_separate_arguments(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Provider files/Xenia Edge.AppImage"
            provider.parent.mkdir()
            provider.write_text("#!/bin/sh\n", encoding="utf-8")
            provider.chmod(0o755)
            home = root / "isolated home"
            tmp = root / "isolated tmp"
            working = root / "Xenia config"
            for path in (home, tmp, working):
                path.mkdir()
            environment = {
                "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                "EMBERCADE_EXTERNAL_PROVIDER_HOME": str(home),
                "EMBERCADE_EXTERNAL_PROVIDER_TMPDIR": str(tmp),
                "XDG_CONFIG_HOME": str(root / "config"),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_CACHE_HOME": str(root / "cache"),
                "XDG_STATE_HOME": str(root / "state"),
                "XDG_RUNTIME_DIR": str(root / "runtime"),
                "WAYLAND_DISPLAY": "/run/user/1000/wayland-1",
                "XAUTHORITY": "/run/user/1000/embercade-xauthority",
                "EMBERCADE_HOST_XAUTHORITY": "/run/user/1000/xauth_cookie",
                "SDL_GAMECONTROLLERCONFIG": "guid,name,a:b0,",
                "EMBERCADE_XENIA_EDGE_LOG": str(root / "state/xenia-edge.log"),
                "SteamAppId": "4059814080",
            }
            rom = "/roms/Test Game.iso"

            command = build_host_provider_command(
                (rom,),
                environment=environment,
                working_directory=working,
                systemd_run=Path("/usr/bin/systemd-run"),
                unit_name="embercade-provider-test",
            )

            self.assertEqual(command[-2:], ("--host-child", rom))
            self.assertEqual(command[-5], "--")
            self.assertEqual(command[-4], sys.executable)
            self.assertIn(f"--working-directory={working}", command)
            self.assertIn("--unit=embercade-provider-test", command)
            self.assertIn("--property=KillMode=mixed", command)
            self.assertIn(f"--setenv=HOME={home}", command)
            self.assertIn(f"--setenv=TMPDIR={tmp}", command)
            self.assertIn(f"--setenv=XDG_DATA_HOME={working.parent}", command)
            self.assertIn(
                f"--setenv=EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE={provider}", command
            )
            self.assertIn("--setenv=SDL_GAMECONTROLLERCONFIG=guid,name,a:b0,", command)
            self.assertIn("--setenv=SteamAppId=4059814080", command)
            self.assertIn(
                "--setenv=XAUTHORITY=/run/user/1000/xauth_cookie",
                command,
            )
            self.assertNotIn(
                "--setenv=XAUTHORITY=/run/user/1000/embercade-xauthority",
                command,
            )
            self.assertIn(
                f"--setenv=EMBERCADE_XENIA_EDGE_LOG={root / 'state/xenia-edge.log'}",
                command,
            )
            self.assertNotIn("sh", command)

    def test_appimage_mounts_only_returns_fuse_mounts_below_private_tmp(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            tmp = root / "private tmp"
            tmp.mkdir()
            inside = tmp / ".mount_Xenia_123"
            outside = root / "unrelated"
            mountinfo = root / "mountinfo"
            encoded_inside = str(inside).replace(" ", "\\040")
            mountinfo.write_text(
                "\n".join(
                    (
                        f"42 31 0:50 / {encoded_inside} rw - fuse.Xenia AppImage rw",
                        f"43 31 0:51 / {outside} rw - fuse.Other Other rw",
                        f"44 31 0:52 / {tmp / 'ordinary'} rw - ext4 disk rw",
                    )
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                appimage_mounts(tmp, mountinfo=mountinfo), frozenset({inside})
            )

    def test_xenia_windows_receive_the_inherited_numeric_steam_app_id(self) -> None:
        tagged: list[tuple[str, int, int]] = []

        count = tag_xenia_windows_once(
            {"DISPLAY": ":1", "SteamAppId": "4059814080"},
            windows=lambda display: (0x60000E, 0x600010),
            set_property=lambda display, window, app_id: tagged.append(
                (display, window, app_id)
            )
            or True,
        )

        self.assertEqual(count, 2)
        self.assertEqual(
            tagged,
            [
                (":1", 0x60000E, 4059814080),
                (":1", 0x600010, 4059814080),
            ],
        )

    def test_xenia_window_tagging_is_disabled_without_numeric_steam_identity(self) -> None:
        windows = Mock()
        self.assertEqual(
            tag_xenia_windows_once(
                {"DISPLAY": ":1", "SteamAppId": "not-numeric"},
                windows=windows,
            ),
            0,
        )
        windows.assert_not_called()

    def test_host_watcher_exits_only_its_provider_group_on_select_start(self) -> None:
        probe = Mock(info=Mock(vendor=0x28DE, product=0x11FF))
        device = Mock(fd=12)
        device.read.return_value = (
            Mock(type=1, code=314, value=1),
            Mock(type=1, code=315, value=1),
        )
        evdev = Mock(
            ecodes=Mock(EV_KEY=1, BTN_SELECT=314, BTN_START=315, BTN_MODE=316)
        )
        evdev.list_devices.return_value = ("/dev/input/event25",)
        evdev.InputDevice.side_effect = (probe, device)
        process = Mock(pid=4321)
        stop = Event()
        exit_requested = Event()

        with (
            patch(
                "embercade.provider_runner.select.select",
                return_value=([12], [], []),
            ),
            patch(
                "embercade.provider_runner._terminate_provider_process_group"
            ) as terminate,
        ):
            _watch_steam_exit_chord(
                {"SteamAppId": "4059814080"},
                process,
                stop,
                exit_requested,
                evdev=evdev,
            )

        self.assertTrue(exit_requested.is_set())
        terminate.assert_called_once_with(process)
        probe.close.assert_called_once_with()
        device.close.assert_called_once_with()

    def test_production_sandbox_paths_translate_only_through_whitelist(self) -> None:
        environment = {
            "EMBERCADE_HOST_CONFIG_ROOT": "/home/user/.config/embercade",
            "EMBERCADE_HOST_STATE_ROOT": "/home/user/.local/state/embercade",
            "EMBERCADE_HOST_ROMS_ROOT": "/mnt/ROM Library",
        }
        self.assertEqual(
            translate_sandbox_path(
                Path("/userdata/system/xdg/config/embercade/emulators/Xenia"),
                environment,
            ),
            Path("/home/user/.config/embercade/emulators/Xenia"),
        )
        self.assertEqual(
            translate_provider_argument(
                "/userdata/roms/xbox360/Test Game.iso", environment
            ),
            "/mnt/ROM Library/xbox360/Test Game.iso",
        )
        self.assertEqual(
            translate_provider_argument(
                "--log_file=/userdata/system/xdg/state/embercade/logs/xenia.log",
                environment,
            ),
            "--log_file=/home/user/.local/state/embercade/logs/xenia.log",
        )
        self.assertEqual(
            translate_sandbox_path(Path("/etc/passwd"), environment),
            Path("/etc/passwd"),
        )

    def test_production_command_uses_host_paths_for_delegated_provider(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Xenia.AppImage"
            provider.write_text("provider", encoding="utf-8")
            provider.chmod(0o755)
            host_config = root / "host config"
            host_data = root / "host data"
            host_cache = root / "host cache"
            host_state = root / "host state"
            host_roms = root / "ROM Library"
            working = host_config / "emulators/Xenia"
            home = host_data / "system"
            tmp = root / "runtime/appimage-tmp"
            for path in (working, home, tmp, host_cache, host_state, host_roms):
                path.mkdir(parents=True, exist_ok=True)
            environment = {
                "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                "EMBERCADE_EXTERNAL_PROVIDER_HOME": "/userdata/system/xdg/data/embercade/system",
                "EMBERCADE_EXTERNAL_PROVIDER_TMPDIR": "/userdata/system/xdg/runtime/embercade/appimage-tmp",
                "EMBERCADE_HOST_CONFIG_ROOT": str(host_config),
                "EMBERCADE_HOST_DATA_ROOT": str(host_data),
                "EMBERCADE_HOST_CACHE_ROOT": str(host_cache),
                "EMBERCADE_HOST_STATE_ROOT": str(host_state),
                "EMBERCADE_HOST_PRIVATE_RUNTIME_ROOT": str(root / "runtime"),
                "EMBERCADE_HOST_ROMS_ROOT": str(host_roms),
                "XDG_CONFIG_HOME": "/userdata/system/xdg/config/embercade/emulators",
                "XDG_DATA_HOME": "/userdata/system/xdg/data/embercade",
                "XDG_CACHE_HOME": "/userdata/system/xdg/cache/embercade",
                "XDG_STATE_HOME": "/userdata/system/xdg/state/embercade",
                "XDG_RUNTIME_DIR": "/run/user/1000",
            }
            command = build_host_provider_command(
                ("/userdata/roms/xbox360/Game.iso",),
                environment=environment,
                working_directory=Path(
                    "/userdata/system/xdg/config/embercade/emulators/Xenia"
                ),
                systemd_run=Path("/usr/bin/systemd-run"),
            )
            self.assertIn(f"--working-directory={working}", command)
            self.assertIn(f"--setenv=HOME={home}", command)
            self.assertIn(f"--setenv=TMPDIR={tmp}", command)
            self.assertIn(f"--setenv=XDG_DATA_HOME={working.parent}", command)
            self.assertEqual(command[-1], str(host_roms / "xbox360/Game.iso"))

    def test_host_child_cleans_only_new_private_appimage_mounts(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Xenia.AppImage"
            provider.write_text("provider", encoding="utf-8")
            provider.chmod(0o755)
            tmp = root / "tmp"
            tmp.mkdir()
            mountpoint = tmp / ".mount_Xenia_123"
            mountpoint.mkdir()
            environment = {
                "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                "TMPDIR": str(tmp),
            }
            with (
                patch(
                    "embercade.provider_runner.appimage_mounts",
                    side_effect=(frozenset(), frozenset({mountpoint})),
                ),
                patch(
                    "embercade.provider_runner.shutil.which",
                    return_value="/usr/bin/fusermount3",
                ),
                patch("embercade.provider_runner.subprocess.Popen") as popen,
                patch("embercade.provider_runner.subprocess.run") as run,
            ):
                process = Mock(pid=1234)
                process.wait.return_value = 0
                popen.return_value = process
                run.return_value = subprocess.CompletedProcess((), 0, "", "")
                result = run_host_provider(("/roms/Game.iso",), environment=environment)

            self.assertEqual(result, 0)
            popen.assert_called_once_with(
                (str(provider), "/roms/Game.iso"),
                start_new_session=True,
            )
            self.assertEqual(
                run.call_args_list,
                [
                    call(
                        ("/usr/bin/fusermount3", "-uz", str(mountpoint)),
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                    ),
                ],
            )
            self.assertFalse(mountpoint.exists())

    def test_service_sigterm_runs_scoped_cleanup_and_repeated_signal_is_harmless(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Xenia.AppImage"
            provider.write_bytes(b"provider")
            tmp = root / "tmp"
            tmp.mkdir()
            existing_mount = tmp / ".mount_existing"
            new_mount = tmp / ".mount_new"
            existing_mount.mkdir()
            new_mount.mkdir()
            process = Mock(pid=4321)
            handlers = {}
            old_handler = Mock()

            def set_handler(signum, handler):
                handlers[signum] = handler
                return old_handler

            def wait(timeout=None):
                if timeout is not None:
                    handlers[signal.SIGTERM](signal.SIGTERM, None)
                    raise subprocess.TimeoutExpired("provider", timeout)
                return -signal.SIGTERM

            def unmount(*args, **kwargs):
                handlers[signal.SIGTERM](signal.SIGTERM, None)
                return subprocess.CompletedProcess(args[0], 0)

            process.wait.side_effect = wait
            environment = {
                "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                "TMPDIR": str(tmp),
            }
            with (
                patch("embercade.provider_runner.signal.signal", side_effect=set_handler) as register,
                patch("embercade.provider_runner.appimage_mounts", side_effect=(
                    frozenset({existing_mount}), frozenset({existing_mount, new_mount}),
                )),
                patch("embercade.provider_runner.subprocess.Popen", return_value=process),
                patch("embercade.provider_runner._terminate_provider_process_group") as terminate,
                patch("embercade.provider_runner.shutil.which", return_value="/usr/bin/fusermount3"),
                patch("embercade.provider_runner.subprocess.run", side_effect=unmount) as run,
            ):
                self.assertEqual(run_host_provider(("/roms/Game.iso",), environment=environment), 0)
            terminate.assert_called_once_with(process)
            run.assert_called_once_with(
                ("/usr/bin/fusermount3", "-uz", str(new_mount)),
                check=False, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, text=True,
            )
            self.assertTrue(existing_mount.is_dir())
            self.assertFalse(new_mount.exists())
            self.assertEqual(register.call_args_list[-1], call(signal.SIGTERM, old_handler))

    def test_owned_provider_stop_escalates_within_its_bounded_grace(self) -> None:
        process = Mock(pid=4321)
        with (
            patch("embercade.provider_runner.os.killpg") as killpg,
            patch("embercade.provider_runner.time.monotonic", side_effect=(0.0, 0.0, 2.1)),
            patch("embercade.provider_runner.time.sleep"),
        ):
            _terminate_provider_process_group(process)
        self.assertEqual(killpg.call_args_list, [
            call(4321, signal.SIGTERM), call(4321, 0), call(4321, signal.SIGKILL),
        ])

    def test_prompt_provider_exit_is_reaped_without_unnecessary_sigkill(self) -> None:
        process = Mock(pid=4321)
        events = []

        def poll():
            events.append("reaped")
            return -signal.SIGTERM

        def killpg(pgid, signum):
            self.assertEqual(pgid, 4321)
            events.append(signum)
            if signum == 0:
                self.assertIn("reaped", events)
                raise ProcessLookupError

        process.poll.side_effect = poll
        with (
            patch("embercade.provider_runner.os.killpg", side_effect=killpg) as kill,
            patch("embercade.provider_runner.time.monotonic", side_effect=(0.0, 0.0)),
            patch("embercade.provider_runner.time.sleep") as sleep,
        ):
            _terminate_provider_process_group(process)
        self.assertEqual(events, [signal.SIGTERM, "reaped", 0])
        self.assertEqual(kill.call_args_list, [call(4321, signal.SIGTERM), call(4321, 0)])
        sleep.assert_not_called()

    def test_service_stop_reports_a_real_mount_cleanup_failure(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Xenia.AppImage"
            provider.write_bytes(b"provider")
            tmp = root / "tmp"
            tmp.mkdir()
            mount = tmp / ".mount_new"
            mount.mkdir()
            handlers = {}
            process = Mock(pid=4321)

            def set_handler(signum, handler):
                handlers[signum] = handler

            def wait(timeout=None):
                if timeout is not None:
                    handlers[signal.SIGTERM](signal.SIGTERM, None)
                    raise subprocess.TimeoutExpired("provider", timeout)
                return -signal.SIGTERM

            process.wait.side_effect = wait
            with (
                patch("embercade.provider_runner.signal.signal", side_effect=set_handler),
                patch("embercade.provider_runner.appimage_mounts", side_effect=(
                    frozenset(), frozenset({mount}), frozenset({mount}),
                )),
                patch("embercade.provider_runner.subprocess.Popen", return_value=process),
                patch("embercade.provider_runner._terminate_provider_process_group"),
                patch("embercade.provider_runner.shutil.which", return_value="/usr/bin/fusermount3"),
                patch("embercade.provider_runner.subprocess.run", return_value=
                      subprocess.CompletedProcess((), 1, "", "still mounted")),
                patch("builtins.print"),
            ):
                result = run_host_provider((), environment={
                    "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                    "TMPDIR": str(tmp),
                })
            self.assertEqual(result, 1)
            self.assertTrue(mount.is_dir())

    def test_abnormal_host_provider_exit_is_not_reported_as_intentional_success(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Xenia.AppImage"
            provider.write_bytes(b"provider")
            tmp = root / "tmp"
            tmp.mkdir()
            process = Mock(pid=4321)
            process.wait.return_value = 23
            with (
                patch("embercade.provider_runner.appimage_mounts", return_value=frozenset()),
                patch("embercade.provider_runner.subprocess.Popen", return_value=process),
            ):
                result = run_host_provider((), environment={
                    "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                    "TMPDIR": str(tmp),
                })
            self.assertEqual(result, 23)
            process.wait.assert_called_once_with(timeout=0.1)

    def test_late_service_signal_does_not_hide_an_already_observed_error(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Xenia.AppImage"
            provider.write_bytes(b"provider")
            tmp = root / "tmp"
            tmp.mkdir()
            process = Mock(pid=4321)
            process.wait.return_value = 23
            handlers = {}
            watcher = Mock()

            def set_handler(signum, handler):
                handlers[signum] = handler

            def finish_watcher(**kwargs):
                # The provider's error is known; SIGTERM now arrives while
                # unwinding the watcher, before exit-status construction.
                handlers[signal.SIGTERM](signal.SIGTERM, None)

            watcher.join.side_effect = finish_watcher

            with (
                patch("embercade.provider_runner.signal.signal", side_effect=set_handler),
                patch("embercade.provider_runner.appimage_mounts", return_value=frozenset()),
                patch("embercade.provider_runner.subprocess.Popen", return_value=process),
                patch("embercade.provider_runner.Thread", return_value=watcher),
            ):
                result = run_host_provider((), environment={
                    "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                    "TMPDIR": str(tmp),
                    "SteamAppId": "123",
                })
            self.assertEqual(result, 23)

    def test_host_child_accepts_appimage_cleanup_race(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "Xenia.AppImage"
            provider.write_text("provider", encoding="utf-8")
            provider.chmod(0o755)
            tmp = root / "tmp"
            tmp.mkdir()
            mountpoint = tmp / ".mount_Xenia_123"
            mountpoint.mkdir()
            environment = {
                "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                "TMPDIR": str(tmp),
            }
            with (
                patch(
                    "embercade.provider_runner.appimage_mounts",
                    side_effect=(
                        frozenset(),
                        frozenset({mountpoint}),
                        frozenset(),
                    ),
                ),
                patch(
                    "embercade.provider_runner.shutil.which",
                    return_value="/usr/bin/fusermount3",
                ),
                patch("embercade.provider_runner.subprocess.Popen") as popen,
                patch("embercade.provider_runner.subprocess.run") as run,
            ):
                process = Mock(pid=1234)
                process.wait.return_value = 0
                popen.return_value = process
                run.return_value = subprocess.CompletedProcess(
                    (), 1, "", "already gone"
                )
                result = run_host_provider(("/roms/Game.iso",), environment=environment)

            self.assertEqual(result, 0)
            self.assertFalse(mountpoint.exists())

    def test_relative_or_missing_provider_is_rejected(self) -> None:
        environment = {"EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": "relative.AppImage"}
        with self.assertRaisesRegex(ProviderRunnerError, "absolute path"):
            build_host_provider_command(
                (),
                environment=environment,
                working_directory=Path("/tmp"),
                systemd_run=Path("/usr/bin/systemd-run"),
            )


if __name__ == "__main__":
    unittest.main()

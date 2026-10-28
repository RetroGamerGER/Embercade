"""Launch-scoped configured controller chord to desktop-window exit bridge."""

from __future__ import annotations

from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from threading import Event, Thread
from typing import Callable, Iterator, Mapping
import logging
import os
import select
import sys

from embercade.controller import ControllerDevice
from embercade.exit_hotkey import ExitHotkey, EXIT_HOTKEYS


SDL_CONTROLLER_BUTTON_BACK = 4
SDL_CONTROLLER_BUTTON_GUIDE = 5
SDL_CONTROLLER_BUTTON_START = 6

_logger = logging.getLogger(__name__)
_STEAM_VIRTUAL_GAMEPAD = (0x28DE, 0x11FF)


class ControllerExitError(RuntimeError):
    """The temporary controller-to-window exit bridge could not start."""


def load_host_evdev() -> object:
    """Load host evdev without exposing every host package to the runtime."""
    try:
        return import_module("evdev")
    except ImportError as direct_error:
        host_packages = (
            Path(sys.base_prefix)
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages"
        )
        if not host_packages.is_dir():
            raise direct_error
        value = str(host_packages)
        sys.path.insert(0, value)
        try:
            return import_module("evdev")
        except ImportError as host_error:
            raise direct_error from host_error
        finally:
            if sys.path[:1] == [value]:
                del sys.path[0]


def _exit_chord_pressed(
    sdl: object, handle: object, exit_button: int = SDL_CONTROLLER_BUTTON_BACK
) -> bool:
    """Refresh SDL's snapshot before reading the two controller buttons."""
    sdl.SDL_GameControllerUpdate()
    return bool(
        sdl.SDL_GameControllerGetButton(handle, exit_button)
        and sdl.SDL_GameControllerGetButton(handle, SDL_CONTROLLER_BUTTON_START)
    )


def _emit_alt_f4(keyboard: object, ecodes: object) -> None:
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 1)
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_F4, 1)
    keyboard.syn()
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_F4, 0)
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 0)
    keyboard.syn()


def _evdev_exit_button_codes(ecodes: object, hotkey: ExitHotkey) -> tuple[int, int]:
    exit_button = (
        ecodes.BTN_MODE
        if hotkey.sdl_button == SDL_CONTROLLER_BUTTON_GUIDE
        else ecodes.BTN_SELECT
    )
    return exit_button, ecodes.BTN_START


def _steam_virtual_gamepad_paths(
    evdev: object,
    environment: Mapping[str, str],
) -> tuple[Path, ...]:
    """Find Steam's forwarded Xbox pad only inside a Steam/Gamescope session."""
    if not (
        environment.get("SteamAppId")
        or environment.get("GAMESCOPE_WAYLAND_DISPLAY")
    ):
        return ()
    result: list[Path] = []
    for candidate in evdev.list_devices():
        try:
            device = evdev.InputDevice(candidate)
        except OSError:
            continue
        try:
            identity = (device.info.vendor, device.info.product)
            if identity == _STEAM_VIRTUAL_GAMEPAD:
                result.append(Path(candidate))
        finally:
            device.close()
    return tuple(result)


@contextmanager
def controller_exit_bridge(
    controller: ControllerDevice,
    *,
    emulator: str = "emulator",
    hotkey: ExitHotkey = EXIT_HOTKEYS["back-start"],
    on_exit: Callable[[], None] | None = None,
) -> Iterator[None]:
    """Translate one live configured chord edge to a launch-scoped exit action."""
    try:
        evdev = load_host_evdev()
        UInput = evdev.UInput
        ecodes = evdev.ecodes
        input_devices = [evdev.InputDevice(str(controller.device_path))]
    except (ImportError, OSError) as error:
        raise ControllerExitError(
            f"Cannot open {controller.device_path} for the {emulator} exit bridge: {error}"
        ) from error

    for candidate in _steam_virtual_gamepad_paths(evdev, os.environ):
        if candidate == controller.device_path:
            continue
        try:
            input_devices.append(evdev.InputDevice(str(candidate)))
        except OSError as error:
            _logger.warning(
                "Cannot open Steam virtual gamepad %s for the %s exit bridge: %s",
                candidate,
                emulator,
                error,
            )

    keyboard = None
    if on_exit is None:
        try:
            keyboard = UInput(
                {ecodes.EV_KEY: [ecodes.KEY_LEFTALT, ecodes.KEY_F4]},
                name=f"Embercade {emulator.upper()} Exit",
            )
        except OSError as error:
            for input_device in input_devices:
                input_device.close()
            raise ControllerExitError(
                f"Cannot create the temporary {emulator} exit keyboard: {error}"
            ) from error

    stop = Event()
    exit_button, start_button = _evdev_exit_button_codes(ecodes, hotkey)

    def watch() -> None:
        devices_by_fd = {device.fd: device for device in input_devices}
        held = {device.fd: set() for device in input_devices}
        exit_requested = False
        try:
            while not stop.is_set():
                readable, _, _ = select.select(tuple(devices_by_fd), (), (), 0.02)
                if not readable:
                    continue
                for fd in readable:
                    for event in devices_by_fd[fd].read():
                        if event.type != ecodes.EV_KEY or event.code not in {
                            exit_button,
                            start_button,
                        }:
                            continue
                        if event.value:
                            held[fd].add(event.code)
                        else:
                            held[fd].discard(event.code)
                        chord = exit_button in held[fd] and start_button in held[fd]
                        if chord and not exit_requested:
                            exit_requested = True
                            if on_exit is None:
                                assert keyboard is not None
                                _emit_alt_f4(keyboard, ecodes)
                            else:
                                on_exit()
        except OSError as error:
            _logger.error("%s exit bridge input failed: %s", emulator, error)

    thread = Thread(target=watch, name=f"embercade-{emulator}-exit", daemon=True)
    try:
        thread.start()
        yield
    finally:
        stop.set()
        thread.join(timeout=1)
        if keyboard is not None:
            keyboard.close()
        for input_device in input_devices:
            input_device.close()

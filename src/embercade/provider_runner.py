"""Run a user-supplied executable outside the frontend's mount namespace."""

from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from typing import Callable, Mapping, Sequence
import ctypes
from importlib import import_module
import os
import select
import signal
import shlex
import shutil
import subprocess
import sys
import time


class ProviderRunnerError(RuntimeError):
    pass


def service_control_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Address the host user manager without changing the emulator's XDG roots."""
    result = dict(environment)
    host_runtime = environment.get("EMBERCADE_HOST_SESSION_RUNTIME_ROOT", "")
    if host_runtime and Path(host_runtime).is_absolute():
        result["XDG_RUNTIME_DIR"] = host_runtime
    return result


_FORWARDED_ENVIRONMENT = (
    "DBUS_SESSION_BUS_ADDRESS",
    "DISPLAY",
    "EMBERCADE_EXIT_HOTKEY",
    "EMBERCADE_EXTERNAL_PROVIDER_ID",
    "SDL_VIDEODRIVER",
    "ENABLE_GAMESCOPE_WSI",
    "GAMESCOPE_WAYLAND_DISPLAY",
    "EMBERCADE_XENIA_EDGE_LOG",
    "GDK_BACKEND",
    "LANG",
    "LC_ALL",
    "PULSE_SERVER",
    "QT_QPA_PLATFORM",
    "SDL_GAMECONTROLLERCONFIG",
    "SDL_JOYSTICK_HIDAPI",
    "SteamAppId",
    "WAYLAND_DISPLAY",
    "XAUTHORITY",
    "XDG_SESSION_TYPE",
)

_STEAM_VIRTUAL_GAMEPAD = (0x28DE, 0x11FF)


class _XClassHint(ctypes.Structure):
    _fields_ = (("res_name", ctypes.c_void_p), ("res_class", ctypes.c_void_p))


def _owned_window_pid(pid: int, process_group: int) -> bool:
    """Only the launched provider group, including its native helper dialogs."""
    if pid <= 0 or process_group <= 0:
        return False
    try:
        return os.getpgid(pid) == process_group
    except OSError:
        return False


def _x11_window_pid(x11, display, window: int) -> int:
    atom = x11.XInternAtom(display, b"_NET_WM_PID", 1)
    if not atom:
        return 0
    actual_type, remaining = ctypes.c_ulong(), ctypes.c_ulong()
    actual_format, count = ctypes.c_int(), ctypes.c_ulong()
    value = ctypes.POINTER(ctypes.c_ubyte)()
    try:
        status = x11.XGetWindowProperty(
            display, window, atom, 0, 1, 0, 6,  # XA_CARDINAL
            ctypes.byref(actual_type), ctypes.byref(actual_format),
            ctypes.byref(count), ctypes.byref(remaining), ctypes.byref(value),
        )
        if status == 0 and actual_type.value == 6 and actual_format.value == 32 and count.value == 1 and value:
            return int(ctypes.cast(value, ctypes.POINTER(ctypes.c_ulong))[0])
        return 0
    finally:
        if value:
            x11.XFree(value)


def _xenia_x11_windows(
    display_name: str, *, wm_class: str = "xenia_edge",
    process_group: int | None = None,
) -> tuple[int, ...]:
    """Return provider windows; an owned group also covers SDL helper dialogs."""
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    x11.XDefaultRootWindow.restype = ctypes.c_ulong
    x11.XQueryTree.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),
        ctypes.POINTER(ctypes.c_uint),
    ]
    x11.XQueryTree.restype = ctypes.c_int
    x11.XGetClassHint.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(_XClassHint),
    ]
    x11.XGetClassHint.restype = ctypes.c_int
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XGetWindowProperty.argtypes = [
        ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_long,
        ctypes.c_long, ctypes.c_int, ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
    ]
    x11.XGetWindowProperty.restype = ctypes.c_int
    x11.XFree.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]

    display = x11.XOpenDisplay(display_name.encode())
    if not display:
        return ()
    root = x11.XDefaultRootWindow(display)
    root_return = ctypes.c_ulong()
    parent_return = ctypes.c_ulong()
    children = ctypes.POINTER(ctypes.c_ulong)()
    count = ctypes.c_uint()
    result: list[int] = []
    try:
        if not x11.XQueryTree(
            display,
            root,
            ctypes.byref(root_return),
            ctypes.byref(parent_return),
            ctypes.byref(children),
            ctypes.byref(count),
        ):
            return ()
        for index in range(count.value):
            window = children[index]
            if process_group is not None:
                if _owned_window_pid(_x11_window_pid(x11, display, window), process_group):
                    result.append(window)
                continue
            hint = _XClassHint()
            if not x11.XGetClassHint(display, window, ctypes.byref(hint)):
                continue
            try:
                names = tuple(
                    ctypes.cast(value, ctypes.c_char_p).value.decode(
                        errors="replace"
                    ).casefold()
                    for value in (hint.res_name, hint.res_class)
                    if value
                )
                if wm_class in names:
                    result.append(window)
            finally:
                if hint.res_name:
                    x11.XFree(hint.res_name)
                if hint.res_class:
                    x11.XFree(hint.res_class)
    finally:
        if children:
            x11.XFree(children)
        x11.XCloseDisplay(display)
    return tuple(result)


def _set_steam_game_property(display_name: str, window: int, app_id: int) -> bool:
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XChangeProperty.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int,
    ]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    display = x11.XOpenDisplay(display_name.encode())
    if not display:
        return False
    try:
        property_atom = x11.XInternAtom(display, b"STEAM_GAME", 0)
        cardinal_atom = x11.XInternAtom(display, b"CARDINAL", 0)
        value = ctypes.c_ulong(app_id)
        x11.XChangeProperty(
            display,
            window,
            property_atom,
            cardinal_atom,
            32,
            0,
            ctypes.cast(ctypes.byref(value), ctypes.POINTER(ctypes.c_ubyte)),
            1,
        )
        x11.XSync(display, 0)
        return True
    finally:
        x11.XCloseDisplay(display)


def tag_xenia_windows_once(
    environment: Mapping[str, str],
    *,
    windows: Callable[[str], tuple[int, ...]] = _xenia_x11_windows,
    set_property: Callable[[str, int, int], bool] = _set_steam_game_property,
) -> int:
    display = environment.get("DISPLAY", "")
    app_id_text = environment.get("SteamAppId", "")
    if not display or not app_id_text.isdecimal():
        return 0
    app_id = int(app_id_text)
    return sum(
        bool(set_property(display, window, app_id))
        for window in windows(display)
    )


def _load_host_evdev() -> object:
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


def _steam_virtual_gamepad_paths(
    evdev: object,
    environment: Mapping[str, str],
) -> tuple[Path, ...]:
    if not environment.get("SteamAppId"):
        return ()
    result: list[Path] = []
    for candidate in evdev.list_devices():
        try:
            device = evdev.InputDevice(candidate)
        except OSError:
            continue
        try:
            if (device.info.vendor, device.info.product) == _STEAM_VIRTUAL_GAMEPAD:
                result.append(Path(candidate))
        finally:
            device.close()
    return tuple(result)


def _terminate_provider_process_group(process: subprocess.Popen[object]) -> None:
    """Stop only this provider's process group, escalating after a short grace."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        # Reap the direct child before testing its process group. Otherwise a
        # zombie can keep the group visible and trigger an unnecessary SIGKILL.
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _watch_steam_exit_chord(
    environment: Mapping[str, str],
    process: subprocess.Popen[object],
    stop: Event,
    exit_requested: Event,
    *,
    evdev: object | None = None,
) -> None:
    """Watch Steam's forwarded gamepad at the host/provider boundary."""
    try:
        evdev = _load_host_evdev() if evdev is None else evdev
        devices = [
            evdev.InputDevice(str(path))
            for path in _steam_virtual_gamepad_paths(evdev, environment)
        ]
    except (ImportError, OSError) as error:
        print(f"Cannot start the Xenia exit watcher: {error}", file=sys.stderr)
        return
    if not devices:
        return
    ecodes = evdev.ecodes
    exit_button = (
        ecodes.BTN_MODE
        if environment.get("EMBERCADE_EXIT_HOTKEY") == "guide-start"
        else ecodes.BTN_SELECT
    )
    held = {device.fd: set() for device in devices}
    devices_by_fd = {device.fd: device for device in devices}
    try:
        while not stop.is_set():
            readable, _, _ = select.select(tuple(devices_by_fd), (), (), 0.05)
            for fd in readable:
                for event in devices_by_fd[fd].read():
                    if event.type != ecodes.EV_KEY or event.code not in {
                        exit_button,
                        ecodes.BTN_START,
                    }:
                        continue
                    if event.value:
                        held[fd].add(event.code)
                    else:
                        held[fd].discard(event.code)
                    if exit_button in held[fd] and ecodes.BTN_START in held[fd]:
                        exit_requested.set()
                        _terminate_provider_process_group(process)
                        return
    except OSError as error:
        print(f"Xenia exit watcher input failed: {error}", file=sys.stderr)
    finally:
        for device in devices:
            device.close()

_SANDBOX_PATH_MAPPINGS = (
    (Path("/userdata/system/xdg/config/embercade"), "EMBERCADE_HOST_CONFIG_ROOT"),
    (Path("/userdata/system/xdg/data/embercade"), "EMBERCADE_HOST_DATA_ROOT"),
    (Path("/userdata/system/xdg/cache/embercade"), "EMBERCADE_HOST_CACHE_ROOT"),
    (Path("/userdata/system/xdg/state/embercade"), "EMBERCADE_HOST_STATE_ROOT"),
    (Path("/userdata/system/xdg/runtime/embercade"), "EMBERCADE_HOST_PRIVATE_RUNTIME_ROOT"),
    (Path("/userdata/roms"), "EMBERCADE_HOST_ROMS_ROOT"),
    (Path("/userdata/bios"), "EMBERCADE_HOST_BIOS_ROOT"),
)


def translate_sandbox_path(path: Path, environment: Mapping[str, str]) -> Path:
    """Translate only known Embercade bind targets back to explicit host roots."""
    if not path.is_absolute():
        return path
    for sandbox_root, variable in _SANDBOX_PATH_MAPPINGS:
        host_value = environment.get(variable)
        if not host_value:
            continue
        host_root = Path(host_value)
        if not host_root.is_absolute():
            raise ProviderRunnerError(f"{variable} must be an absolute path")
        try:
            relative = path.relative_to(sandbox_root)
        except ValueError:
            continue
        return host_root / relative
    return path


def translate_provider_argument(value: str, environment: Mapping[str, str]) -> str:
    option, separator, candidate = value.partition("=")
    if separator and option.startswith("--") and candidate.startswith("/"):
        return f"{option}={translate_sandbox_path(Path(candidate), environment)}"
    if value.startswith("/"):
        return str(translate_sandbox_path(Path(value), environment))
    return value


def _translated_existing_directory(
    path: Path,
    environment: Mapping[str, str],
    *,
    label: str,
) -> Path:
    """Validate a directory on either side of the production sandbox boundary."""
    translated = translate_sandbox_path(path, environment)
    if not path.is_absolute() or not translated.is_absolute():
        raise ProviderRunnerError(f"{label} is unavailable: {path}")
    # In production only the sandbox spelling is visible here; unit-level host
    # checks can instead see the translated spelling.  systemd-run receives the
    # translated host path in both cases.
    if not path.is_dir() and not translated.is_dir():
        raise ProviderRunnerError(f"{label} is unavailable: {path}")
    return translated


def _host_or_sandbox_environment_path(
    environment: Mapping[str, str], host_name: str, sandbox_name: str
) -> str:
    value = environment.get(host_name)
    if value:
        return value
    return environment[sandbox_name]


def _unescape_mountinfo_path(value: str) -> Path:
    """Decode the octal escapes used for paths in /proc/*/mountinfo."""

    for encoded, decoded in (
        ("\\040", " "),
        ("\\011", "\t"),
        ("\\012", "\n"),
        ("\\134", "\\"),
    ):
        value = value.replace(encoded, decoded)
    return Path(value)


def appimage_mounts(
    temporary_directory: Path,
    *,
    mountinfo: Path = Path("/proc/self/mountinfo"),
) -> frozenset[Path]:
    """Return FUSE AppImage mounts contained by Embercade's private TMPDIR."""

    if not mountinfo.is_file():
        return frozenset()
    result: set[Path] = set()
    for line in mountinfo.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) < 10 or "-" not in fields:
            continue
        separator = fields.index("-")
        if separator + 1 >= len(fields) or not fields[separator + 1].startswith("fuse."):
            continue
        mountpoint = _unescape_mountinfo_path(fields[4])
        try:
            mountpoint.relative_to(temporary_directory)
        except ValueError:
            continue
        result.add(mountpoint)
    return frozenset(result)


def run_host_provider(
    arguments: Sequence[str],
    *,
    environment: Mapping[str, str],
    mountinfo: Path = Path("/proc/self/mountinfo"),
) -> int:
    """Run the provider and clean FUSE mounts created by this invocation."""

    service_stop = Event()

    def request_service_stop(_signum: int, _frame: object) -> None:
        # Keep this installed through unmount cleanup. Repeated SIGTERM only
        # records the same request; it must not interrupt that cleanup.
        service_stop.set()

    previous_handler = signal.signal(signal.SIGTERM, request_service_stop)
    try:
        return _run_host_provider(
            arguments, environment=environment, mountinfo=mountinfo,
            service_stop=service_stop,
        )
    finally:
        signal.signal(signal.SIGTERM, previous_handler)


def _run_host_provider(
    arguments: Sequence[str],
    *,
    environment: Mapping[str, str],
    mountinfo: Path,
    service_stop: Event,
) -> int:

    provider = Path(environment.get("EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE", ""))
    temporary_directory = Path(environment.get("TMPDIR", ""))
    if not provider.is_absolute() or not provider.is_file():
        raise ProviderRunnerError(f"External provider is unavailable: {provider}")
    if not temporary_directory.is_absolute() or not temporary_directory.is_dir():
        raise ProviderRunnerError(
            f"External provider TMPDIR is unavailable: {temporary_directory}"
        )

    mounts_before = appimage_mounts(temporary_directory, mountinfo=mountinfo)
    tagger_stop = Event()
    provider_process = subprocess.Popen(
        (str(provider), *arguments),
        start_new_session=True,
    )

    def tag_windows() -> None:
        while not tagger_stop.is_set():
            try:
                if environment.get("EMBERCADE_EXTERNAL_PROVIDER_ID") == "shadps4":
                    tag_xenia_windows_once(
                        environment,
                        windows=lambda display: _xenia_x11_windows(
                            display, process_group=provider_process.pid,
                        ),
                    )
                else:
                    tag_xenia_windows_once(environment)
            except OSError as error:
                print(f"Cannot tag provider window for Gamescope: {error}", file=sys.stderr)
                return
            tagger_stop.wait(0.1)

    tagger = None
    if environment.get("DISPLAY") and environment.get("SteamAppId", "").isdecimal():
        tagger = Thread(target=tag_windows, name="embercade-provider-focus", daemon=True)
        tagger.start()
    exit_watcher_stop = Event()
    exit_requested = Event()
    exit_watcher = None
    if environment.get("SteamAppId", "").isdecimal():
        exit_watcher = Thread(
            target=_watch_steam_exit_chord,
            args=(environment, provider_process, exit_watcher_stop, exit_requested),
            name="embercade-xenia-exit",
            daemon=True,
        )
        exit_watcher.start()
    try:
        while True:
            if service_stop.is_set():
                exit_requested.set()
                # Bound an unresponsive owned child to two seconds, leaving
                # time for the existing FUSE cleanup before the unit timeout.
                _terminate_provider_process_group(provider_process)
                provider_returncode = provider_process.wait()
                break
            try:
                provider_returncode = provider_process.wait(timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                continue
    finally:
        exit_watcher_stop.set()
        if exit_watcher is not None:
            exit_watcher.join(timeout=3)
        tagger_stop.set()
        if tagger is not None:
            tagger.join(timeout=1)
    result = subprocess.CompletedProcess(
        (str(provider), *arguments),
        0 if exit_requested.is_set() else provider_returncode,
    )
    mounts_after = appimage_mounts(temporary_directory, mountinfo=mountinfo)
    cleanup_failed = False
    fusermount = shutil.which("fusermount3") or shutil.which("fusermount")
    for mountpoint in sorted(mounts_after - mounts_before):
        if fusermount is None:
            print(f"Cannot clean AppImage mount without fusermount: {mountpoint}", file=sys.stderr)
            cleanup_failed = True
            continue
        cleanup = subprocess.run(
            (fusermount, "-uz", str(mountpoint)),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        if cleanup.returncode != 0:
            # The AppImage runtime and this fallback may race to remove the
            # same mount.  A failed fusermount is harmless when the mount has
            # already disappeared from the current namespace.
            if mountpoint not in appimage_mounts(
                temporary_directory, mountinfo=mountinfo
            ):
                try:
                    mountpoint.rmdir()
                except OSError:
                    pass
                continue
            print(
                f"Failed to clean AppImage mount {mountpoint}: {cleanup.stderr.strip()}",
                file=sys.stderr,
            )
            cleanup_failed = True
            continue
        try:
            mountpoint.rmdir()
        except OSError:
            # The AppImage runtime may remove it itself, or it may still contain
            # runtime-owned files while the lazy unmount finishes.
            pass
    if result.returncode == 0 and cleanup_failed:
        return 1
    return result.returncode


def build_host_provider_command(
    arguments: Sequence[str],
    *,
    environment: Mapping[str, str],
    working_directory: Path,
    systemd_run: Path,
    unit_name: str | None = None,
) -> tuple[str, ...]:
    provider_text = environment.get("EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE", "")
    provider = Path(provider_text)
    if not provider.is_absolute():
        raise ProviderRunnerError("External provider executable must be an absolute path")
    if not provider.is_file() or not os.access(provider, os.R_OK | os.X_OK):
        raise ProviderRunnerError(
            f"External provider is unavailable, unreadable or not executable: {provider}"
        )
    working_directory = _translated_existing_directory(
        working_directory,
        environment,
        label="External provider working directory",
    )

    isolated_home = _translated_existing_directory(
        Path(environment.get("EMBERCADE_EXTERNAL_PROVIDER_HOME", "")),
        environment,
        label="External provider HOME",
    )
    isolated_tmp = _translated_existing_directory(
        Path(environment.get("EMBERCADE_EXTERNAL_PROVIDER_TMPDIR", "")),
        environment,
        label="External provider TMPDIR",
    )

    forwarded = {}
    for name in _FORWARDED_ENVIRONMENT:
        if not environment.get(name):
            continue
        value = environment[name]
        if name == "EMBERCADE_XENIA_EDGE_LOG":
            value = str(translate_sandbox_path(Path(value), environment))
        elif name == "XAUTHORITY":
            value = _host_or_sandbox_environment_path(
                environment,
                "EMBERCADE_HOST_XAUTHORITY",
                "XAUTHORITY",
            )
        forwarded[name] = value
    forwarded.update(
        {
            "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
            "HOME": str(isolated_home),
            "TMPDIR": str(isolated_tmp),
            "XDG_CONFIG_HOME": _host_or_sandbox_environment_path(
                environment, "EMBERCADE_HOST_CONFIG_ROOT", "XDG_CONFIG_HOME"
            ),
            # Both providers append their own product directory. Xenia's cwd
            # already ends in Xenia; shadPS4's cwd is the emulator-config root.
            # In either case consume the exact pinned-generator config.
            "XDG_DATA_HOME": str(working_directory if environment.get("EMBERCADE_EXTERNAL_PROVIDER_ID") == "shadps4" else working_directory.parent),
            "XDG_CACHE_HOME": _host_or_sandbox_environment_path(
                environment, "EMBERCADE_HOST_CACHE_ROOT", "XDG_CACHE_HOME"
            ),
            "XDG_STATE_HOME": _host_or_sandbox_environment_path(
                environment, "EMBERCADE_HOST_STATE_ROOT", "XDG_STATE_HOME"
            ),
            "XDG_RUNTIME_DIR": _host_or_sandbox_environment_path(
                environment, "EMBERCADE_HOST_PRIVATE_RUNTIME_ROOT", "XDG_RUNTIME_DIR"
            ),
        }
    )

    command = [
        str(systemd_run),
        "--user",
        "--wait",
        "--collect",
        "--quiet",
        "--pipe",
        "--service-type=exec",
        "--property=KillMode=mixed",
        "--expand-environment=no",
        f"--working-directory={working_directory}",
    ]
    if unit_name is not None:
        command.append(f"--unit={unit_name}")
    command.extend(f"--setenv={name}={value}" for name, value in sorted(forwarded.items()))
    command.extend(
        (
            "--",
            sys.executable,
            str(Path(__file__).resolve()),
            "--host-child",
            *(translate_provider_argument(value, environment) for value in arguments),
        )
    )
    return tuple(command)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == ("--host-child",):
        try:
            return run_host_provider(arguments[1:], environment=os.environ)
        except ProviderRunnerError as error:
            print(f"External provider error: {error}", file=sys.stderr)
            return 2
    systemd_run_text = shutil.which("systemd-run", path=os.environ.get("PATH"))
    if systemd_run_text is None:
        print("External AppImage provider requires systemd-run", file=sys.stderr)
        return 127
    unit_name = os.environ.get(
        "EMBERCADE_EXTERNAL_PROVIDER_UNIT", f"embercade-provider-{os.getpid()}"
    )
    try:
        command = build_host_provider_command(
            arguments,
            environment=os.environ,
            working_directory=Path.cwd(),
            systemd_run=Path(systemd_run_text),
            unit_name=unit_name,
        )
    except (KeyError, ProviderRunnerError) as error:
        print(f"External provider error: {error}", file=sys.stderr)
        return 2
    provider = os.environ["EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE"]
    print(f"EMBERCADE_PROVIDER_COMMAND={shlex.join((provider, *arguments))}")

    interrupted: int | None = None

    def remember_interrupt(signum: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = signum
        raise KeyboardInterrupt

    previous_handlers = {
        signum: signal.signal(signum, remember_interrupt)
        for signum in (signal.SIGINT, signal.SIGTERM)
    }
    process = subprocess.Popen(command)
    try:
        return process.wait()
    except KeyboardInterrupt:
        systemctl = shutil.which("systemctl", path=os.environ.get("PATH"))
        if systemctl is not None:
            subprocess.run(
                (systemctl, "--user", "stop", f"{unit_name}.service"),
                env=service_control_environment(os.environ),
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        if process.poll() is None:
            process.terminate()
            process.wait()
        return 128 + (interrupted or signal.SIGINT)
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only description of the current desktop display session."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import json
import os
import re
import shutil
import subprocess


class DisplayResolutionError(RuntimeError):
    """The desktop pixel size cannot be determined safely."""


@dataclass(frozen=True, slots=True)
class DisplayResolution:
    width: int
    height: int


def _positive_dimension(value: str, name: str) -> int:
    try:
        result = int(value)
    except ValueError as error:
        raise DisplayResolutionError(f"{name} must be a positive integer") from error
    if result <= 0:
        raise DisplayResolutionError(f"{name} must be a positive integer")
    return result


def _hyprland_resolution(
    environment: Mapping[str, str],
    *,
    runner: Any = subprocess.run,
) -> DisplayResolution:
    executable = shutil.which("hyprctl", path=environment.get("PATH"))
    if executable is None:
        raise DisplayResolutionError("Hyprland is active but hyprctl is unavailable")
    try:
        completed = runner(
            [executable, "-j", "monitors"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
            env=dict(environment),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DisplayResolutionError(f"cannot query Hyprland monitor size: {error}") from error
    if completed.returncode != 0:
        raise DisplayResolutionError("cannot query Hyprland monitor size")
    try:
        monitors = json.loads(completed.stdout)
        monitor = next(
            (item for item in monitors if item.get("focused") is True),
            monitors[0],
        )
        width = int(monitor["width"])
        height = int(monitor["height"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise DisplayResolutionError("hyprctl returned invalid monitor data") from error
    if width <= 0 or height <= 0:
        raise DisplayResolutionError("hyprctl returned an invalid monitor size")
    return DisplayResolution(width, height)


def current_resolution(
    environment: Mapping[str, str] | None = None,
    *,
    runner: Any = subprocess.run,
) -> DisplayResolution:
    """Resolve desktop pixel dimensions without changing the display mode."""
    env = os.environ if environment is None else environment
    width_value = env.get("EMBERCADE_DISPLAY_WIDTH")
    height_value = env.get("EMBERCADE_DISPLAY_HEIGHT")
    if width_value is not None or height_value is not None:
        if width_value is None or height_value is None:
            raise DisplayResolutionError(
                "EMBERCADE_DISPLAY_WIDTH and EMBERCADE_DISPLAY_HEIGHT must be set together"
            )
        return DisplayResolution(
            _positive_dimension(width_value, "EMBERCADE_DISPLAY_WIDTH"),
            _positive_dimension(height_value, "EMBERCADE_DISPLAY_HEIGHT"),
        )
    if env.get("GAMESCOPE_WAYLAND_DISPLAY") and env.get("DISPLAY"):
        return _x11_resolution(env, runner=runner)
    if env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return _hyprland_resolution(env, runner=runner)
    if env.get("WAYLAND_DISPLAY") and "KDE" in env.get("XDG_CURRENT_DESKTOP", "").upper():
        return _kde_resolution(env, runner=runner)
    if env.get("DISPLAY"):
        return _x11_resolution(env, runner=runner)
    # Non-graphical config generation retains Batocera's conservative fallback.
    return DisplayResolution(1920, 1080)


def _kde_resolution(environment: Mapping[str, str], *, runner: Any) -> DisplayResolution:
    executable = shutil.which("kscreen-doctor", path=environment.get("PATH"))
    if executable is None:
        raise DisplayResolutionError("KDE is active but kscreen-doctor is unavailable")
    try:
        result = runner([executable, "-j"], capture_output=True, text=True,
                        check=False, timeout=5, env=dict(environment))
        if result.returncode:
            raise ValueError("kscreen-doctor failed")
        outputs = [o for o in json.loads(result.stdout)["outputs"]
                   if o.get("connected") and o.get("enabled")]
        active_name = None
        if len(outputs) > 1:
            if qdbus := shutil.which("qdbus6", path=environment.get("PATH")):
                active = runner([qdbus, "org.kde.KWin", "/KWin", "org.kde.KWin.activeOutputName"],
                                capture_output=True, text=True, check=False, timeout=5,
                                env=dict(environment))
                if active.returncode == 0:
                    active_name = active.stdout.strip()
        output = next((o for o in outputs if o.get("name") == active_name),
                      min(outputs, key=lambda o: o.get("priority", 999)))
        mode = next(m for m in output["modes"] if m["id"] == output["currentModeId"])
        # KScreen's output size can be logical/scaled. RetroArch's viewport
        # and bezel generator need the actual framebuffer mode in pixels.
        width, height = int(mode["size"]["width"]), int(mode["size"]["height"])
        if output.get("rotation", 1) in (2, 8):
            width, height = height, width
        if min(width, height) <= 0:
            raise ValueError("invalid output mode")
        return DisplayResolution(width, height)
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError, StopIteration) as error:
        raise DisplayResolutionError(f"cannot query KDE monitor size: {error}") from error


def _x11_resolution(environment: Mapping[str, str], *, runner: Any) -> DisplayResolution:
    executable = shutil.which("xrandr", path=environment.get("PATH"))
    if executable is None:
        raise DisplayResolutionError("X11 is active but xrandr is unavailable")
    try:
        result = runner([executable, "--current"], capture_output=True, text=True,
                        check=False, timeout=5, env=dict(environment))
        matches = re.findall(r"^\S+ connected (primary )?(\d+)x(\d+)[+-]\d+[+-]\d+", result.stdout, re.M)
        if result.returncode or not matches:
            raise ValueError("no active X11 output")
        match = next((m for m in matches if m[0]), matches[0])
        width, height = int(match[1]), int(match[2])
        if min(width, height) <= 0:
            raise ValueError("invalid output size")
        # In Gamescope this is the game's logical Xwayland output, not the
        # external-overlay plane's physical DRM scanout size.
        return DisplayResolution(width, height)
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        raise DisplayResolutionError(f"cannot query X11 monitor size: {error}") from error


@dataclass(frozen=True, slots=True)
class DisplaySession:
    protocol: str
    display: str | None
    wayland_display: str | None

    @classmethod
    def current(cls, environment: Mapping[str, str] | None = None) -> "DisplaySession":
        env = os.environ if environment is None else environment
        wayland = env.get("WAYLAND_DISPLAY")
        x11 = env.get("DISPLAY")
        if wayland:
            protocol = "wayland"
        elif x11:
            protocol = "x11"
        else:
            protocol = "headless"
        return cls(protocol=protocol, display=x11, wayland_display=wayland)

    @property
    def supports_mode_switch(self) -> bool:
        return False

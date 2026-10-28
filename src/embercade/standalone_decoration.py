"""Optional, launch-scoped decorations for desktop standalone emulators.

Batocera owns selection and precedence. This module only validates its result,
protects the game rectangle and supervises the disposable desktop renderer.
No GTK dependency is imported by the launcher.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path
import socket
import subprocess
from typing import Iterator, Mapping, TYPE_CHECKING

from embercade.backend import backend_command

if TYPE_CHECKING:
    from embercade.launcher import LaunchPlan

log = logging.getLogger(__name__)
SUPPORTED = {"ps2": "pcsx2", "xbox": "xemu", "gamecube": "dolphin", "wii": "dolphin"}

@dataclass(frozen=True)
class Decoration:
    png: Path
    width: int
    height: int
    left: float
    top: float
    right: float
    bottom: float
    opacity: float
    ratio: float

    def to_json(self) -> str:
        return json.dumps({**self.__dict__, "png": str(self.png)})


def protected_ratio(system: str, options: Mapping[str, str]) -> float | None:
    """Do not force emulator settings. Protect the widest possible auto frame.

PCSX2 auto can switch to 3:2 in PS1/FMVs. Xemu auto can follow a widescreen
game. Dolphin follows its generated aspect and TV-mode settings. Explicit 4:3
permits the full validated frame; ambiguous/wide modes conservatively reserve
more space instead of covering game pixels.
"""
    if system == "ps2":
        ratios = {"4:3": 4 / 3, "10:7": 10 / 7, "16:9": 16 / 9, "Auto 4:3/3:2": 3 / 2, "": 3 / 2}
        values = [options.get(key) or "" for key in ("pcsx2_ratio", "pcsx2_fmv_ratio")]
        if values[1] == 'off':
            values[1] = values[0]
        if any(value not in ratios for value in values):
            return None
        return max(ratios[value] for value in values)
    if system == "xbox":
        if (options.get("xemu_scaling") or "") not in ("", "scale"):
            return None
        return {"4x3": 4 / 3, "16x9": 16 / 9, "auto": 16 / 9, "": 16 / 9}.get(
            options.get("xemu_aspect") or ""
        )
    if system in {"gamecube", "wii"}:
        # Mirror the pinned Dolphin plugin's in_game_ratio contract. Auto
        # follows the existing TV-mode choice; stretch has no protected bars.
        aspect = options.get("dolphin_aspect_ratio") or "0"
        if aspect == "2" or (aspect == "0" and (options.get("tv_mode") or "0") == "0"):
            return 4 / 3
        if aspect == "1" or (aspect == "0" and options.get("tv_mode") == "1"):
            return 16 / 9
    return None


def validate_decoration(payload: dict, system: str, roots: tuple[Path, ...]) -> Decoration | None:
    if payload.get("emulator") != SUPPORTED.get(system) or not payload.get("png"):
        return None
    ratio = protected_ratio(system, payload.get("options", {}))
    if ratio is None:
        log.warning("Standalone decoration omitted: unsupported viewport options %s", payload.get("options"))
        return None
    png = Path(payload["png"]).resolve(strict=True)
    info = Path(payload["info"]).resolve(strict=True)
    for path in (png, info):
        if not any(path.is_relative_to(root.resolve()) for root in roots):
            raise ValueError("Decoration escaped its configured resource roots")
    with png.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("Decoration is not a PNG")
    width, height = int.from_bytes(header[16:20]), int.from_bytes(header[20:24])
    if not (0 < width <= 16384 and 0 < height <= 16384 and width * height <= 40_000_000):
        raise ValueError("Decoration dimensions are unsafe")
    layout = json.loads(info.read_text(encoding="utf-8"))
    if (layout.get("width"), layout.get("height")) != (width, height):
        raise ValueError("PNG and .info dimensions differ")
    left, top, right, bottom = (float(layout.get(key, 0)) for key in ("left", "top", "right", "bottom"))
    opacity = float(layout.get("opacity", 1))
    if (not all(math.isfinite(value) for value in (left, top, right, bottom, opacity))
            or min(left, top, right, bottom) < 0 or left + right >= width
            or top + bottom >= height or not 0 <= opacity <= 1):
        raise ValueError("Invalid decoration aperture/opacity")
    return Decoration(png, width, height, left, top, right, bottom, opacity, ratio)


def safe_margins(decoration: Decoration, width: int, height: int) -> tuple[float, float]:
    """Only side bars, outside both centered game and declared image aperture.

The image keeps its aspect ratio; neither emulator nor game is resized. One
logical pixel protects the edge against interpolation and rounding.
"""
    scale = min(width / decoration.width, height / decoration.height)
    offset = (width - decoration.width * scale) / 2
    game_margin = max(0, (width - height * decoration.ratio) / 2 - 1)
    return (
        max(0, min(game_margin, offset + decoration.left * scale - 1)),
        max(0, min(game_margin, offset + decoration.right * scale - 1)),
    )


def hyprland_socket_dir(environment: Mapping[str, str]) -> Path | None:
    if environment.get("GAMESCOPE_WAYLAND_DISPLAY") or "gamescope" in environment.get("XDG_CURRENT_DESKTOP", "").lower():
        return None
    signature = environment.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    runtime = environment.get("EMBERCADE_DECORATION_SESSION_RUNTIME", environment.get("XDG_RUNTIME_DIR", ""))
    if not environment.get("WAYLAND_DISPLAY") or not runtime or not signature or Path(signature).name != signature:
        return None
    directory = Path(runtime) / "hypr" / signature
    return directory if all((directory / name).is_socket() for name in (".socket.sock", ".socket2.sock")) else None


def decoration_backend(environment: Mapping[str, str]) -> str | None:
    if environment.get("GAMESCOPE_WAYLAND_DISPLAY") and environment.get("DISPLAY"):
        return "gamescope"
    if hyprland_socket_dir(environment) is not None:
        return "hyprland"
    if environment.get("WAYLAND_DISPLAY") and "KDE" in environment.get("XDG_CURRENT_DESKTOP", "").upper():
        return "kwin"
    return None


def belongs_to_launch(pid: int, owner: int, executable: Path, proc: Path = Path('/proc')) -> bool:
    """Match exact executable and ancestry, never a global process-name search."""
    try:
        if (proc / str(pid) / "exe").resolve(strict=True) != executable.resolve(strict=True):
            return False
        seen = set()
        while pid > 1 and pid not in seen:
            if pid == owner:
                return True
            seen.add(pid)
            # comm may contain spaces and parentheses; ppid follows the last ')'.
            fields = (proc / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
            pid = int(fields[1])
    except (OSError, ValueError, IndexError):
        pass
    return False


def visible_on_monitor(active: dict, monitor: tuple[int, int, int, int], owned: bool) -> bool:
    x, y, width, height = monitor
    return bool(owned and active.get("mapped") and not active.get("hidden")
                and active.get("fullscreen") == 2
                and active.get("at") == [x, y] and active.get("size") == [width, height])


def hyprland_request(directory: Path, command: str) -> object:
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(0.15)
        connection.connect(str(directory / ".socket.sock"))
        connection.sendall(command.encode())
        chunks = []
        while chunk := connection.recv(65536):
            chunks.append(chunk)
            if sum(map(len, chunks)) > 1_000_000:
                raise ValueError("Unexpected compositor reply size")
    return json.loads(b"".join(chunks))


def resolve_decoration(plan: LaunchPlan) -> Decoration | None:
    completed = subprocess.run(
        backend_command(Path(plan.command[0]).parent / "python", "resolve-decoration",
                        "--", plan.system, str(plan.rom)),
        env=dict(plan.environment), capture_output=True, text=True, timeout=10, check=True,
    )
    roots = (Path(plan.environment["EMBERCADE_SYSTEM_DECORATIONS"]),
             Path(plan.environment["EMBERCADE_USERDATA"]) / "decorations")
    return validate_decoration(json.loads(completed.stdout), plan.system, roots)


@contextmanager
def standalone_decoration(plan: LaunchPlan) -> Iterator[None]:
    helper = None
    if not plan.dry_run and plan.system in SUPPORTED and SUPPORTED[plan.system] == plan.emulator:
        try:
            decoration = resolve_decoration(plan)
            if decoration is not None:
                backend = decoration_backend(plan.environment)
                if backend is None:
                    log.warning("Standalone decoration unavailable: unsupported compositor; game unchanged")
                else:
                    helper = subprocess.Popen(
                        ["/usr/bin/python", "-B", str(Path(__file__).with_name("decoration_window.py")),
                         backend, str(os.getpid()), str(plan.executable), decoration.to_json()],
                        env=dict(plan.environment), stdin=subprocess.PIPE,
                    )
        except Exception as error:
            # Optional visual preparation cannot turn into a launch prerequisite.
            log.warning("Standalone decoration unavailable; game unchanged: %s", error)
    try:
        yield
    finally:
        if helper is not None:
            try:
                # EOF also handles owner death, including SIGKILL/crashes. The
                # descriptor is not inherited by the emulator (close_fds=True).
                if helper.stdin:
                    helper.stdin.close()
                try:
                    helper.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    helper.terminate()
                    try:
                        helper.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Last resort for a wedged optional renderer only.
                        # Never signal the emulator or a name-matched process.
                        helper.kill()
                        helper.wait(timeout=2)
                if helper.returncode:
                    log.warning("Standalone decoration helper exited %s; emulator status unchanged", helper.returncode)
            except (OSError, subprocess.TimeoutExpired) as error:
                log.warning("Standalone decoration cleanup: %s", error)

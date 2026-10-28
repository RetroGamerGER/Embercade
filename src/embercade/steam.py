"""Opt-in, offline Steam shortcut/artwork registration with Steam stopped.

Binary VDF nodes retain their original bytes: foreign shortcuts and unknown
fields are never reserialized. Unsupported/malformed input fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, TextIO
import fcntl
import json
import os
import stat
import struct
import tempfile
import zlib

from embercade.installer import UserInstallPaths
from embercade.version import FRONTEND_PRODUCT_LABEL


class SteamError(RuntimeError):
    """No Steam data should be changed when registration is unsafe."""


@dataclass(frozen=True)
class Node:
    kind: int
    key: str
    value: bytes | tuple["Node", ...]
    raw: bytes


def _cstring(value: str) -> bytes:
    if "\0" in value:
        raise SteamError("NUL is not allowed in a Steam field")
    return value.encode("utf-8", errors="surrogateescape") + b"\0"


def _node(key: str, value: str | int | tuple[Node, ...]) -> Node:
    if isinstance(value, tuple):
        kind, payload = 0, b"".join(item.raw for item in value) + b"\x08"
    elif isinstance(value, int):
        kind, payload = 2, struct.pack("<I", value)
    else:
        kind, payload = 1, _cstring(value)
    raw = bytes((kind,)) + _cstring(key) + payload
    return Node(kind, key, value if kind == 0 else payload, raw)


def parse_vdf(data: bytes) -> tuple[Node, ...]:
    if len(data) > 16 * 1024 * 1024:
        raise SteamError("Steam shortcut file exceeds the safety limit")
    position = 0

    def string() -> bytes:
        nonlocal position
        end = data.find(b"\0", position)
        if end < 0:
            raise SteamError("Unterminated Steam VDF string")
        result = data[position:end + 1]
        position = end + 1
        return result

    def nodes(depth: int) -> tuple[Node, ...]:
        nonlocal position
        if depth > 32:
            raise SteamError("Steam VDF nesting exceeds the safety limit")
        result = []
        while position < len(data):
            start = position
            kind = data[position]
            position += 1
            if kind == 8:
                return tuple(result)
            key = string()[:-1].decode("utf-8", errors="surrogateescape")
            if kind == 0:
                value = nodes(depth + 1)
            elif kind == 1:
                value = string()
            elif kind in (2, 3, 4, 6, 7, 10):
                size = 8 if kind in (7, 10) else 4
                value = data[position:position + size]
                position += size
                if len(value) != size:
                    raise SteamError("Truncated Steam VDF value")
            else:
                raise SteamError(f"Unsupported Steam VDF type {kind}; file left unchanged")
            result.append(Node(kind, key, value, data[start:position]))
        raise SteamError("Incomplete Steam VDF object")

    result = nodes(0)
    if position != len(data):
        raise SteamError("Trailing Steam VDF data")
    return result


def _fields(nodes: tuple[Node, ...]) -> dict[str, Node]:
    result = {}
    for node in nodes:
        key = node.key.casefold()
        if key in result:
            raise SteamError(f"Ambiguous duplicate Steam field: {node.key}")
        result[key] = node
    return result


def _text(fields: Mapping[str, Node], key: str) -> str:
    node = fields.get(key.casefold())
    if node is None or node.kind != 1:
        raise SteamError(f"Missing/invalid Steam shortcut field: {key}")
    return node.value[:-1].decode("utf-8", errors="surrogateescape")


def _appid(fields: Mapping[str, Node]) -> int:
    node = fields.get("appid")
    if node is None or node.kind != 2:
        raise SteamError("Missing/invalid Steam shortcut appid")
    return struct.unpack("<I", node.value)[0]


def shortcut_id(executable: str, name: str = "Embercade") -> int:
    """Deterministic ID for a NEW shortcut only; existing IDs are authoritative."""
    return zlib.crc32((executable + name).encode("utf-8")) | 0x80000000


def update_shortcut(
    data: bytes | None, launcher: Path, icon: Path, *, replace_existing: bool = False,
) -> tuple[bytes, int, bool]:
    if any(character in str(launcher) for character in ('"', "\n", "\r", "\0")):
        raise SteamError("Installed launcher path cannot be quoted safely for Steam")
    executable = f'"{launcher}"'
    root = parse_vdf(data) if data is not None else (_node("shortcuts", ()),)
    if len(root) != 1 or root[0].key.casefold() != "shortcuts" or root[0].kind != 0:
        raise SteamError("Expected one Steam shortcuts root object")
    entries = root[0].value
    _fields(entries)
    matches = []
    ids = set()
    for index, entry in enumerate(entries):
        if entry.kind != 0 or not entry.key.isascii() or not entry.key.isdecimal():
            raise SteamError("Invalid Steam shortcut index")
        fields = _fields(entry.value)
        appid = _appid(fields)
        if appid in ids:
            raise SteamError("Duplicate Steam appid; refusing artwork changes")
        ids.add(appid)
        name, exe = _text(fields, "appname"), _text(fields, "exe")
        if exe.strip('"') == str(launcher):
            matches.append(index)
        elif name.casefold() in {"embercade", "embercade 0.5", FRONTEND_PRODUCT_LABEL.casefold()}:
            if replace_existing:
                matches.append(index)
            else:
                raise SteamError("An Embercade shortcut targets another executable; use --replace-existing to switch it explicitly")
    if len(matches) > 1:
        raise SteamError("Multiple Embercade shortcuts; review duplicates in Steam")
    if matches:
        index = matches[0]
        entry = entries[index]
        fields = _fields(entry.value)
        appid = _appid(fields)  # Never rederive an existing Steam-assigned identity.
        desired = {"appname": FRONTEND_PRODUCT_LABEL, "exe": executable,
                   "startdir": f'"{launcher.parent}"', "icon": str(icon)}
        replacement = []
        for field in entry.value:
            key = field.key.casefold()
            if key in desired:
                if field.kind != 1:
                    raise SteamError(f"Invalid Embercade Steam field type: {field.key}")
                replacement.append(field if _text(fields, key) == desired[key] else _node(field.key, desired[key]))
            else:
                replacement.append(field)
        for key, value in desired.items():
            if key not in fields:
                replacement.append(_node("StartDir" if key == "startdir" else key, value))
        changed = list(entries)
        changed[index] = _node(entry.key, tuple(replacement))
    else:
        appid = shortcut_id(executable)
        if appid in ids:
            raise SteamError("New Embercade appid collides with another shortcut")
        index = max((int(entry.key) for entry in entries), default=-1) + 1
        values = {
            "appid": appid, "AppName": FRONTEND_PRODUCT_LABEL, "Exe": executable,
            "StartDir": f'"{launcher.parent}"', "icon": str(icon),
            "ShortcutPath": "", "LaunchOptions": "", "IsHidden": 0,
            "AllowDesktopConfig": 1, "AllowOverlay": 1, "OpenVR": 0,
            "Devkit": 0, "DevkitGameID": "", "DevkitOverrideAppID": 0,
            "LastPlayTime": 0, "FlatpakAppID": "", "tags": (),
        }
        changed = [*entries, _node(str(index), tuple(_node(key, value) for key, value in values.items()))]
    updated = _node(root[0].key, tuple(changed)).raw + b"\x08"
    parse_vdf(updated)
    return updated, appid, not matches


def discover_profiles(environment: Mapping[str, str] | None = None) -> tuple[Path, ...]:
    env = os.environ if environment is None else environment
    home = Path(env.get("HOME", str(Path.home()))).absolute()
    data = Path(env.get("XDG_DATA_HOME", str(home / ".local/share"))).absolute()
    roots = (data / "Steam", home / ".local/share/Steam", home / ".steam/steam",
             home / ".steam/root", home / ".var/app/com.valvesoftware.Steam/data/Steam")
    profiles = set()
    for root in roots:
        userdata = root.resolve() / "userdata"
        if not userdata.is_dir():
            continue
        for account in userdata.iterdir():
            if account.name.isascii() and account.name.isdecimal() and account.is_dir():
                config = account / "config"
                if config.is_dir():
                    profiles.add(config.resolve())
    return tuple(sorted(profiles))


def steam_running(proc_root: Path = Path("/proc")) -> bool:
    for process in proc_root.iterdir():
        if not process.name.isdecimal():
            continue
        try:
            if process.stat().st_uid == os.getuid() and (process / "comm").read_text().strip() in {"steam", "steamwebhelper"}:
                return True
        except FileNotFoundError:
            continue  # Process exited during enumeration.
        except PermissionError as error:
            raise SteamError("Cannot verify that Steam is stopped") from error
    return False


def _safe_path(path: Path) -> None:
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise SteamError(f"Refusing symlinked Steam write path: {parent}")
    if path.exists() and (path.stat().st_uid != os.getuid() or not path.is_file()):
        raise SteamError(f"Steam target is not a user-owned regular file: {path}")


def _snapshot(path: Path) -> tuple[bytes | None, int]:
    _safe_path(path)
    if not path.exists():
        return None, 0o600
    return path.read_bytes(), stat.S_IMODE(path.stat().st_mode)


def _atomic_write(path: Path, content: bytes, mode: int) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".embercade-steam-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class SteamResult:
    profile: Path
    appid: int
    created: bool
    changed: bool
    backup: Path | None = None


def register(
    profile: Path, *, environment: Mapping[str, str] | None = None,
    dry_run: bool = False, running: Callable[[], bool] | None = None,
    replace_existing: bool = False,
) -> SteamResult:
    env = os.environ if environment is None else environment
    running = steam_running if running is None else running
    if profile not in discover_profiles(env):
        raise SteamError("Select an existing discovered Steam profile")
    if running():
        raise SteamError("Close Steam completely, then run 'embercade steam' again; no Steam data changed")
    paths = UserInstallPaths.from_environment(env)
    if profile.is_relative_to(paths.home / ".var/app/com.valvesoftware.Steam"):
        raise SteamError("Flatpak Steam is detected, but host-launcher access is not validated; native Steam registration only")
    launcher, prefix = paths.launcher, paths.prefix
    if env.get("EMBERCADE_APPIMAGE") == "1":
        image, appdir, active_prefix = (env.get(key) for key in ("APPIMAGE", "APPDIR", "EMBERCADE_PREFIX"))
        if not all((image, appdir, active_prefix)):
            raise SteamError("Run this command through the mounted Embercade AppImage, not an extracted AppDir")
        launcher, prefix = Path(image), Path(active_prefix)
        if prefix.resolve() != (Path(appdir) / "usr").resolve():
            raise SteamError("Invalid AppImage runtime root")
        try:
            with launcher.open("rb") as stream:
                header = stream.read(16)
        except OSError as error:
            raise SteamError("Embercade AppImage is unavailable") from error
        if (not launcher.is_absolute() or launcher.is_symlink() or not launcher.is_file()
                or launcher.stat().st_uid != os.getuid() or not os.access(launcher, os.X_OK)
                or header[:4] != b"\x7fELF" or header[8:11] != b"AI\x02"):
            raise SteamError("Steam needs the user-owned executable Embercade AppImage")
    elif launcher.resolve() != prefix / "bin/embercade" or not os.access(launcher, os.X_OK):
        raise SteamError("Install Embercade first; Steam must use the installed launcher")
    branding = prefix / "share/embercade/resources/branding"
    grid = profile / "grid"
    shortcut_file = profile / "shortcuts.vdf"
    original, mode = _snapshot(shortcut_file)
    # Resolve appid before constructing its icon path, then perform the final update.
    _, appid, created = update_shortcut(original, launcher, grid / "pending", replace_existing=replace_existing)
    updated, _, _ = update_shortcut(original, launcher, grid / f"{appid}_icon.png", replace_existing=replace_existing)
    assets = {
        f"{appid}_icon.png": branding / "icon/embercade-512.png",
        f"{appid}p.jpg": branding / "steam/embercade-grid-900x1800.jpg",
        f"{appid}.jpg": branding / "steam/embercade-hero.jpg",
        f"{appid}_hero.jpg": branding / "steam/embercade-hero.jpg",
        f"{appid}_logo.jpg": branding / "steam/embercade-hero.jpg",
    }
    planned: dict[Path, bytes | None] = {shortcut_file: updated}
    snapshots = {shortcut_file: (original, mode)}
    for name, source in assets.items():
        if not source.is_file() or not source.resolve().is_relative_to(branding.resolve()):
            raise SteamError(f"Missing/unsafe installed Steam branding resource: {source}")
        planned[grid / name] = source.read_bytes()
    # Steam can prefer a stale PNG over a new JPEG. Remove only same-app variants.
    for suffix in ("", "p", "_hero", "_logo", "_icon"):
        for extension in ("png", "jpg", "jpeg", "webp"):
            path = grid / f"{appid}{suffix}.{extension}"
            if path.exists() or path.is_symlink():
                if created:
                    raise SteamError("New Embercade appid collides with existing Steam artwork")
                if path not in planned:
                    planned[path] = None
    for path in planned:
        snapshots.setdefault(path, _snapshot(path))
    changes = {path: content for path, content in planned.items() if content != snapshots[path][0]}
    if not changes or dry_run:
        return SteamResult(profile, appid, created, bool(changes))
    state = paths.state_root
    _safe_path(state / "steam-integration.lock")
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / "steam-integration.lock").open("a+b") as lock:
        os.fchmod(lock.fileno(), 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if running() or any(_snapshot(path) != before for path, before in snapshots.items()):
            raise SteamError("Steam started or its data changed during preparation; retry with Steam stopped")
        backup_root = state / "steam-backups"
        _safe_path(backup_root / "probe")
        backup_root.mkdir(mode=0o700, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix="registration-", dir=backup_root))
        records = []
        for index, path in enumerate(changes):
            content, permissions = snapshots[path]
            saved = f"{index}.original" if content is not None else None
            if saved:
                _atomic_write(backup / saved, content, 0o600)
            records.append({"path": str(path), "original": saved, "mode": permissions})
        _atomic_write(backup / "restore.json", (json.dumps(records, indent=2) + "\n").encode(), 0o600)
        applied = []
        grid_created = False
        try:
            if not grid.exists():
                grid.mkdir(mode=0o700)
                grid_created = True
            for path, content in changes.items():
                if running() or _snapshot(path) != snapshots[path]:
                    raise SteamError("Steam started or target changed during activation; stopping")
                if content is None:
                    path.unlink()
                else:
                    _atomic_write(path, content, snapshots[path][1])
                applied.append(path)
            if running():
                raise SteamError("Steam started during registration")
        except BaseException:
            for path in reversed(applied):
                if _snapshot(path)[0] != changes[path]:
                    raise SteamError(f"Concurrent Steam write detected; original files are in {backup}")
                content, permissions = snapshots[path]
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_write(path, content, permissions)
            if grid_created:
                grid.rmdir()
            raise
    return SteamResult(profile, appid, created, True, backup)


def offer_integration(
    *, environment: Mapping[str, str] | None = None, output: TextIO,
    input_function: Callable[[str], str] = input, profile: Path | None = None,
    accepted: bool = False, dry_run: bool = False, interactive: bool = True,
    strict: bool = False, replace_existing: bool = False,
) -> SteamResult | None:
    """Optional errors never invalidate the completed Embercade installation."""
    try:
        profiles = discover_profiles(environment)
        if not profiles:
            print("Steam integration: no initialized Steam profile found; skipped.", file=output)
            return None
        if not accepted and input_function("Add Embercade to Steam? [Y/n] ").strip().casefold() not in {"", "y", "yes"}:
            print("Steam integration skipped; Steam data unchanged.", file=output)
            return None
        if profile is None:
            if len(profiles) == 1:
                profile = profiles[0]
            else:
                if not interactive:
                    raise SteamError("Multiple Steam profiles; explicitly select one with --profile")
                print("Choose the Steam profile (no automatic account selection):", file=output)
                for index, candidate in enumerate(profiles, 1):
                    print(f"  {index}. {candidate}", file=output)
                answer = input_function("Profile number (Enter to skip): ").strip()
                if not answer:
                    return None
                if not answer.isdecimal() or not 1 <= int(answer) <= len(profiles):
                    raise SteamError("Invalid Steam profile selection; no Steam data changed")
                profile = profiles[int(answer) - 1]
        result = register(profile, environment=environment, dry_run=dry_run,
                          replace_existing=replace_existing)
        if dry_run:
            print(f"Steam integration dry run: appid {result.appid}; no changes made.", file=output)
        else:
            print("Embercade Steam shortcut and icon/grid/hero/logo are ready. Start Steam to load them.", file=output)
        if result.backup:
            print(f"Steam backup: {result.backup}", file=output)
        return result
    except (SteamError, OSError, EOFError, KeyboardInterrupt) as error:
        print(f"Steam integration deferred: {error}", file=output)
        if strict:
            raise SteamError(str(error)) from error
        return None

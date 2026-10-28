"""Narrow filesystem access for the existing frontend scraper, not a scraper."""

from __future__ import annotations

from pathlib import Path
import os
import stat
import xml.etree.ElementTree as ET

from embercade.paths import EmbercadePaths

SECRET_KEYS = frozenset((
    "SCREENSCRAPER_DEV_ID", "SCREENSCRAPER_DEV_PASSWORD",
    "SCREENSCRAPER_DEV_DEBUG_PASSWORD",
))
USER_SECRET_KEYS = frozenset(("SCREENSCRAPER_USER", "SCREENSCRAPER_PASSWORD"))
MEDIA_DIRECTORIES = ("images", "videos", "manuals", "magazines")


def _private_file_status(source: Path, keys: frozenset[str], required: tuple[str, ...]) -> str:
    """Validate a local credential file without returning contents or errors."""
    try:
        parent = source.parent.lstat()
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
                or parent.st_mode & 0o077):
            return "UNSAFE PERMISSIONS"
        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_mode & 0o077 or info.st_size > 16384):
                return "UNSAFE PERMISSIONS"
            raw = stream.read(16385)
        if len(raw) > 16384 or b"\0" in raw:
            return "INVALID FORMAT"
        values: dict[str, str] = {}
        for line in raw.decode("utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if not separator or key not in keys or key in values:
                return "INVALID FORMAT"
            values[key] = value
        if any(not values.get(key) for key in required):
            return "INCOMPLETE"
        return "CONFIGURED (NOT AUTHENTICATED)"
    except FileNotFoundError:
        return "NOT CONFIGURED"
    except (OSError, UnicodeError):
        return "UNREADABLE OR INVALID"


def secret_status(paths: EmbercadePaths) -> str:
    """Developer-secret status only; no credential values leave this function."""
    return _private_file_status(
        paths.secrets / "screenscraper.conf", SECRET_KEYS,
        ("SCREENSCRAPER_DEV_ID", "SCREENSCRAPER_DEV_PASSWORD"),
    )


def _legacy_user_status(paths: EmbercadePaths) -> str:
    settings = paths.emulationstation_config / "es_settings.cfg"
    try:
        info = settings.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            return "LEGACY SETTINGS UNREADABLE OR INVALID"
        if info.st_size > 1024 * 1024:
            return "LEGACY SETTINGS UNREADABLE OR INVALID"
        root = ET.fromstring(settings.read_bytes())
        names = {node.get("name") for node in root.iter("string")}
        if "ScreenScraperUser" in names or "ScreenScraperPass" in names:
            if info.st_mode & 0o077:
                return "LEGACY SETTINGS INSECURE"
            return "LEGACY PRIVATE SETTINGS (MIGRATION PENDING)"
    except FileNotFoundError:
        pass
    except (OSError, ET.ParseError):
        return "LEGACY SETTINGS UNREADABLE OR INVALID"
    return "NOT CONFIGURED"


def user_secret_status(paths: EmbercadePaths) -> str:
    """Personal scraper account status, including the pre-migration ES file."""
    current = _private_file_status(
        paths.secrets / "screenscraper-user.conf", USER_SECRET_KEYS,
        ("SCREENSCRAPER_USER", "SCREENSCRAPER_PASSWORD"),
    )
    legacy = _legacy_user_status(paths)
    if current == "NOT CONFIGURED":
        return legacy
    if legacy == "LEGACY PRIVATE SETTINGS (MIGRATION PENDING)":
        return current + "; LEGACY COPY PENDING REMOVAL"
    if legacy == "LEGACY SETTINGS INSECURE":
        return current + "; LEGACY SETTINGS INSECURE"
    return current


def secret_mounts(paths: EmbercadePaths) -> tuple[list[str], list[str]]:
    """Freeze the developer file read-only; leave the personal account writable."""
    if secret_status(paths) != "CONFIGURED (NOT AUTHENTICATED)":
        return [], []
    destination = "/userdata/system/xdg/config/embercade/secrets/screenscraper.conf"
    return (
        ["--ro-bind", str(paths.secrets / "screenscraper.conf"), destination],
        ["--setenv", "EMBERCADE_SCREENSCRAPER_SECRET_FILE", destination],
    )


def metadata_mounts(paths: EmbercadePaths, systems_file: Path) -> tuple[list[str], tuple[str, ...]]:
    """Bind only gamelist.xml and four upstream media directories into a RO library.

    The pinned frontend writes gamelist directly; media downloads rename their
    temporary file inside the media directory. No writable ROM-system directory
    or collection mount is necessary. Unwritable systems remain read-only.
    """
    mounts: list[str] = []
    unavailable: list[str] = []
    root = paths.rom_root.resolve()
    seen: set[Path] = set()
    for system in ET.parse(systems_file).getroot().findall("system"):
        raw_path = system.findtext("path", "").strip()
        try:
            relative = Path(raw_path).relative_to("/userdata/roms")
        except ValueError:
            continue
        if not relative.parts or ".." in relative.parts:
            continue
        directory = paths.rom_root / relative
        if not directory.is_dir() or directory in seen:
            continue
        seen.add(directory)
        if directory.is_symlink() or not directory.resolve().is_relative_to(root):
            unavailable.append(str(relative))
            continue
        targets = [directory / "gamelist.xml", *(directory / name for name in MEDIA_DIRECTORIES)]
        try:
            # Reject all unsafe existing targets before creating anything.
            for target in targets:
                if target.is_symlink():
                    raise OSError("symlinked metadata destination")
                if target.exists() and (target.is_file() != (target.name == "gamelist.xml")):
                    raise OSError("unexpected metadata destination type")
            if not targets[0].exists():
                # Upstream may previously have read a fallback gamelist from
                # ES config when the collection was entirely read-only.
                name = system.findtext("name", "")
                legacy = paths.emulationstation_config / "gamelists" / name / "gamelist.xml"
                initial = b'<?xml version="1.0"?>\n<gameList />\n'
                if name and Path(name).name == name and legacy.is_file() and not legacy.is_symlink():
                    initial = legacy.read_bytes()
                fd = os.open(targets[0], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(initial)
            for target in targets[1:]:
                target.mkdir(exist_ok=True)
            if any(not os.access(target, os.W_OK) for target in targets):
                raise OSError("metadata destination not writable")
        except OSError:
            unavailable.append(str(relative))
            continue
        for target in targets:
            # Both aliases must have identical protection; standalone emulator
            # ROM content remains under the surrounding read-only root.
            mounts += ["--bind", str(target), str(target)]
            mounts += ["--bind", str(target), str(Path("/userdata/roms") / relative / target.name)]
    return mounts, tuple(unavailable)

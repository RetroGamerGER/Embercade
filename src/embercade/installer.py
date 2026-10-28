"""Transactional user-local installation and manifest-based removal."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, TextIO
import json
import os
import posixpath
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

from embercade.runtime import load_config
from embercade.version import __version__


INSTALL_MANIFEST_FORMAT = 1
STAGE_MANIFEST_RELATIVE = Path("share/embercade/stage-manifest.json")
APP_ICON_RELATIVE = Path("share/embercade/resources/branding/icon/embercade-512.png")


class InstallationError(RuntimeError):
    """An install or uninstall operation cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class UserInstallPaths:
    home: Path
    prefix: Path
    launcher: Path
    desktop_entry: Path
    icon: Path
    manifest: Path
    config_root: Path
    data_root: Path
    cache_root: Path
    state_root: Path

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "UserInstallPaths":
        env = os.environ if environment is None else environment
        home = Path(env.get("HOME", str(Path.home()))).expanduser().absolute()
        data_home = Path(env.get("XDG_DATA_HOME", home / ".local/share")).expanduser().absolute()
        config_home = Path(env.get("XDG_CONFIG_HOME", home / ".config")).expanduser().absolute()
        cache_home = Path(env.get("XDG_CACHE_HOME", home / ".cache")).expanduser().absolute()
        state_home = Path(env.get("XDG_STATE_HOME", home / ".local/state")).expanduser().absolute()
        if home == Path("/"):
            raise InstallationError("refusing to use the filesystem root as HOME")
        state_root = state_home / "embercade"
        return cls(
            home=home,
            prefix=home / ".local/lib/embercade",
            launcher=home / ".local/bin/embercade",
            desktop_entry=data_home / "applications/embercade.desktop",
            icon=data_home / "icons/hicolor/512x512/apps/embercade.png",
            manifest=state_root / "install-manifest.json",
            config_root=config_home / "embercade",
            data_root=data_home / "embercade",
            cache_root=cache_home / "embercade",
            state_root=state_root,
        )


@dataclass(frozen=True, slots=True)
class InstallResult:
    mode: str
    paths: UserInstallPaths
    operations: tuple[str, ...]
    payload_manifest_sha256: str | None = None
    current_manifest_sha256: str | None = None
    current_version: str | None = None
    incoming_version: str | None = None
    current_product_label: str | None = None
    incoming_product_label: str | None = None


@dataclass(frozen=True, slots=True)
class PayloadVerification:
    manifest_sha256: str
    installed_files: tuple[str, ...]
    pins: Mapping[str, str]
    version: str | None = None
    product_label: str | None = None


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\0" in value:
        raise InstallationError("payload manifest contains an invalid path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise InstallationError(f"payload manifest path is unsafe: {value!r}")
    return path


def _actual_payload_entries(root: Path) -> set[str]:
    entries: set[str] = set()
    for base, directories, files in os.walk(root, followlinks=False):
        base_path = Path(base)
        for name in files:
            path = base_path / name
            if path != root / STAGE_MANIFEST_RELATIVE:
                entries.add(path.relative_to(root).as_posix())
        for name in directories:
            path = base_path / name
            if path.is_symlink():
                entries.add(path.relative_to(root).as_posix())
    return entries


def _is_runtime_bytecode(relative: str) -> bool:
    return (
        (relative.startswith("share/embercade/runtime/venv/")
         or (relative.startswith("share/embercade/app/embercade/")
             and PurePosixPath(relative).parent.name == "__pycache__"))
        and relative.endswith((".pyc", ".pyo"))
    )


def verify_payload(
    payload_root: Path,
    *,
    allow_runtime_bytecode_drift: bool = False,
) -> PayloadVerification:
    """Verify every staged payload entry without executing payload code."""
    root = payload_root.expanduser().absolute()
    if root.is_symlink() or not root.is_dir():
        raise InstallationError(f"installation payload is not a real directory: {root}")
    manifest_path = root / STAGE_MANIFEST_RELATIVE
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise InstallationError(f"payload manifest is missing: {manifest_path}")
    try:
        raw_manifest = manifest_path.read_bytes()
        manifest = json.loads(raw_manifest)
    except (OSError, json.JSONDecodeError) as error:
        raise InstallationError(f"payload manifest is unreadable: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("format") != 1:
        raise InstallationError("unsupported payload manifest format")
    entries = manifest.get("entries")
    pins = manifest.get("pins")
    if not isinstance(entries, list) or not isinstance(pins, dict):
        raise InstallationError("payload manifest is incomplete")
    version = manifest.get("embercade_version")
    product_label = manifest.get("product_label")
    if version is not None and (not isinstance(version, str) or not version):
        raise InstallationError("payload packaging version is invalid")
    if product_label is not None and (not isinstance(product_label, str) or not product_label):
        raise InstallationError("payload product label is invalid")

    expected: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise InstallationError("payload manifest contains an invalid entry")
        relative = _safe_relative(entry.get("path"))
        relative_text = relative.as_posix()
        if relative_text in expected:
            raise InstallationError(f"duplicate payload manifest path: {relative_text}")
        expected.add(relative_text)
        ignored_bytecode = (
            allow_runtime_bytecode_drift and _is_runtime_bytecode(relative_text)
        )
        path = root.joinpath(*relative.parts)
        entry_type = entry.get("type")
        if entry_type == "file":
            if ignored_bytecode:
                continue
            if path.is_symlink() or not path.is_file():
                raise InstallationError(f"payload file is missing: {relative_text}")
            size = entry.get("size")
            digest = entry.get("sha256")
            if not isinstance(size, int) or size < 0 or not isinstance(digest, str):
                raise InstallationError(f"payload file metadata is invalid: {relative_text}")
            if path.stat().st_size != size or _sha256_file(path) != digest:
                raise InstallationError(f"payload file verification failed: {relative_text}")
        elif entry_type == "symlink":
            target = entry.get("target")
            if (
                not isinstance(target, str)
                or not target
                or "\0" in target
                or not path.is_symlink()
                or os.readlink(path) != target
            ):
                raise InstallationError(f"payload symlink verification failed: {relative_text}")
            if target.startswith("/"):
                if target != "/usr/bin/python":
                    raise InstallationError(
                        f"payload contains an unexpected absolute symlink: {relative_text} -> {target}"
                    )
            else:
                joined = posixpath.normpath((relative.parent / target).as_posix())
                if joined == ".." or joined.startswith("../"):
                    raise InstallationError(
                        f"payload symlink escapes its root: {relative_text} -> {target}"
                    )
        else:
            raise InstallationError(f"unknown payload entry type for {relative_text}")

    actual = _actual_payload_entries(root)
    comparable_expected = expected
    comparable_actual = actual
    if allow_runtime_bytecode_drift:
        comparable_expected = {path for path in expected if not _is_runtime_bytecode(path)}
        comparable_actual = {path for path in actual if not _is_runtime_bytecode(path)}
    if comparable_actual != comparable_expected:
        missing = sorted(comparable_expected - comparable_actual)
        unexpected = sorted(comparable_actual - comparable_expected)
        detail = f"missing={missing[:3]}, unexpected={unexpected[:3]}"
        raise InstallationError(f"payload file set does not match its manifest: {detail}")
    for executable in (
        root / "bin/embercade",
        root / "bin/embercade-provider-runner",
        root / "share/embercade/frontend/emulationstation",
        root / "share/embercade/runtime/venv/bin/python",
    ):
        if not executable.is_file() or not os.access(executable, os.R_OK | os.X_OK):
            raise InstallationError(f"required payload executable is unavailable: {executable}")
    installed_files = tuple(sorted(expected | {STAGE_MANIFEST_RELATIVE.as_posix()}))
    string_pins = {str(name): str(value) for name, value in pins.items()}
    return PayloadVerification(
        sha256(raw_manifest).hexdigest(), installed_files, string_pins, version, product_label
    )


def _desktop_exec_quote(path: Path) -> str:
    value = str(path).replace("%", "%%")
    escaped = "".join(f"\\{character}" if character in {'\\', '"', '`', '$'} else character for character in value)
    return f'"{escaped}"'


def _desktop_entry(payload_root: Path, launcher: Path) -> str:
    template = payload_root / "share/applications/embercade.desktop"
    if template.is_symlink() or not template.is_file():
        raise InstallationError(f"desktop entry template is missing: {template}")
    lines = template.read_text(encoding="utf-8").splitlines()
    replacements = 0
    icon_references = 0
    result: list[str] = []
    for line in lines:
        if line.startswith("Exec="):
            result.append(f"Exec={_desktop_exec_quote(launcher)}")
            replacements += 1
        elif line == "Icon=embercade":
            result.append(line)
            icon_references += 1
        else:
            result.append(line)
    if replacements != 1:
        raise InstallationError("desktop entry template must contain exactly one Exec field")
    if icon_references != 1:
        raise InstallationError("desktop entry template must contain exactly one Icon=embercade field")
    return "\n".join(result) + "\n"


def _install_manifest(
    paths: UserInstallPaths,
    verification: PayloadVerification,
    desktop_text: str,
    icon_sha256: str,
) -> dict[str, Any]:
    return {
        "format": INSTALL_MANIFEST_FORMAT,
        "embercade_version": verification.version or __version__,
        "product_label": verification.product_label,
        "install_prefix": str(paths.prefix),
        "executable": str(paths.launcher),
        "desktop_entry": str(paths.desktop_entry),
        "desktop_entry_sha256": sha256(desktop_text.encode()).hexdigest(),
        "icon_path": str(paths.icon),
        "icon_sha256": icon_sha256,
        "launcher_target": str(paths.prefix / "bin/embercade"),
        "payload_manifest_sha256": verification.manifest_sha256,
        "payload_pins": dict(verification.pins),
        "relative_installed_files": list(verification.installed_files),
    }


def _load_install_manifest(paths: UserInstallPaths) -> dict[str, Any] | None:
    if not paths.manifest.exists():
        return None
    if paths.manifest.is_symlink() or not paths.manifest.is_file():
        raise InstallationError(f"installation manifest is not a regular file: {paths.manifest}")
    try:
        manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallationError(f"installation manifest is unreadable: {error}") from error
    expected = {
        "install_prefix": paths.prefix,
        "executable": paths.launcher,
        "desktop_entry": paths.desktop_entry,
    }
    if not isinstance(manifest, dict) or manifest.get("format") != INSTALL_MANIFEST_FORMAT:
        raise InstallationError("unsupported installation manifest format")
    for key, path in expected.items():
        if manifest.get(key) != str(path):
            raise InstallationError(f"installation manifest has unexpected {key}: {manifest.get(key)!r}")
    if manifest.get("launcher_target") != str(paths.prefix / "bin/embercade"):
        raise InstallationError("installation manifest has an unexpected launcher target")
    return manifest


def _existing_installation(paths: UserInstallPaths) -> dict[str, Any] | None:
    manifest = _load_install_manifest(paths)
    targets_exist = any(
        path.exists() or path.is_symlink()
        for path in (paths.prefix, paths.launcher, paths.desktop_entry, paths.icon)
    )
    if manifest is None:
        if targets_exist:
            raise InstallationError(
                "installation targets already exist without an Embercade manifest; refusing to overwrite"
            )
        return None
    if not paths.prefix.is_dir() or paths.prefix.is_symlink():
        raise InstallationError("existing Embercade install prefix is missing or unsafe")
    if not paths.launcher.is_symlink() or Path(os.readlink(paths.launcher)) != paths.prefix / "bin/embercade":
        raise InstallationError("existing Embercade launcher does not match its manifest")
    if paths.desktop_entry.is_symlink() or not paths.desktop_entry.is_file():
        raise InstallationError("existing Embercade desktop entry is missing or unsafe")
    if _sha256_file(paths.desktop_entry) != manifest.get("desktop_entry_sha256"):
        raise InstallationError("existing Embercade desktop entry was modified; refusing to overwrite")
    icon_sha256 = manifest.get("icon_sha256")
    if icon_sha256 is None:
        if paths.icon.exists() or paths.icon.is_symlink():
            raise InstallationError(
                f"user icon path already exists and is not managed by this installation: {paths.icon}"
            )
    elif (
        manifest.get("icon_path") != str(paths.icon)
        or paths.icon.is_symlink()
        or not paths.icon.is_file()
        or _sha256_file(paths.icon) != icon_sha256
    ):
        raise InstallationError(f"installed Embercade icon was modified or moved: {paths.icon}")
    embedded = paths.prefix / STAGE_MANIFEST_RELATIVE
    if not embedded.is_file() or _sha256_file(embedded) != manifest.get("payload_manifest_sha256"):
        raise InstallationError("existing Embercade payload does not match its installation manifest")
    # Older payloads tracked runtime/app caches that Python may regenerate after
    # relocation. Validate every non-cache file strictly, then replace the
    # complete prefix transactionally with the cache-free payload.
    verification = verify_payload(
        paths.prefix,
        allow_runtime_bytecode_drift=True,
    )
    if verification.manifest_sha256 != manifest.get("payload_manifest_sha256"):
        raise InstallationError("existing Embercade payload verification failed")
    return manifest


def _operation_list(paths: UserInstallPaths, *, mode: str) -> tuple[str, ...]:
    return (
        f"{mode}: immutable payload -> {paths.prefix}",
        f"install launcher -> {paths.launcher}",
        f"install desktop entry -> {paths.desktop_entry}",
        f"install hicolor application icon -> {paths.icon}",
        f"write install manifest -> {paths.manifest}",
        "preserve Embercade config, saves/states, screenshots, themes, managed cores/providers and PPSSPP assets",
        "preserve Steam shortcut/artwork and external ROM/BIOS references",
    )


def _temporary_file(parent: Path, name: str, data: bytes, mode: int) -> Path:
    descriptor, raw_path = tempfile.mkstemp(prefix=f".{name}.", dir=parent)
    path = Path(raw_path)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(mode)
        return path
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _replace(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _require_exact_child(path: Path, parent: Path, label: str) -> None:
    """Reject broad, aliased or unexpectedly nested deletion targets."""
    if path.is_symlink() or path.parent != parent or path.name != "embercade":
        raise InstallationError(f"unsafe {label} path: {path}")


def running_installation_pids(
    paths: UserInstallPaths,
    *,
    proc_root: Path = Path("/proc"),
    current_pid: int | None = None,
) -> tuple[int, ...]:
    """Find live processes whose executable or argv belongs to this installation."""
    own_pid = os.getpid() if current_pid is None else current_pid
    found: list[int] = []
    try:
        entries = tuple(proc_root.iterdir())
    except OSError:
        return ()
    prefix = str(paths.prefix) + os.sep
    for entry in entries:
        if not entry.name.isdigit() or int(entry.name) == own_pid:
            continue
        pid = int(entry.name)
        values: list[str] = []
        try:
            values.extend(
                value.decode(errors="replace")
                for value in (entry / "cmdline").read_bytes().split(b"\0")
                if value
            )
            values.append(str((entry / "exe").resolve(strict=True)))
        except OSError:
            pass
        if any(value == str(paths.prefix) or value.startswith(prefix) for value in values):
            found.append(pid)
    return tuple(sorted(found))


def launcher_path_guidance(
    paths: UserInstallPaths, environment: Mapping[str, str] | None = None
) -> tuple[str, ...]:
    env = os.environ if environment is None else environment
    path_entries = {
        str(Path(value).expanduser().absolute())
        for value in env.get("PATH", "").split(os.pathsep)
        if value
    }
    if str(paths.launcher.parent) in path_entries:
        return ()
    shell = Path(env.get("SHELL", "")).name
    command = (
        f"fish_add_path {paths.launcher.parent}"
        if shell == "fish"
        else f'Add {paths.launcher.parent} to PATH in your {shell or "shell"} configuration.'
    )
    return (
        f"Embercade was installed, but {paths.launcher.parent} is not in the current PATH.",
        command,
    )


def install_user(
    payload_root: Path,
    *,
    environment: Mapping[str, str] | None = None,
    dry_run: bool = False,
) -> InstallResult:
    paths = UserInstallPaths.from_environment(environment)
    verification = verify_payload(payload_root)
    icon_source = payload_root / APP_ICON_RELATIVE
    if icon_source.is_symlink() or not icon_source.is_file():
        raise InstallationError(f"application icon is missing from the payload: {icon_source}")
    existing = _existing_installation(paths)
    desktop_text = _desktop_entry(payload_root, paths.launcher)
    icon_digest = _sha256_file(icon_source)
    identical = bool(
        existing is not None
        and existing.get("payload_manifest_sha256") == verification.manifest_sha256
        and existing.get("desktop_entry_sha256") == sha256(desktop_text.encode()).hexdigest()
        and existing.get("icon_sha256") == icon_digest
    )
    mode = "ALREADY UP TO DATE" if identical else "UPDATE/REINSTALL" if existing else "NEW INSTALL"
    if existing is not None and not identical and running_installation_pids(paths):
        raise InstallationError(
            "Embercade is currently running.\n"
            "Close Embercade before updating or reinstalling."
        )
    operations = ("no application files or user data will be changed",) if identical else _operation_list(paths, mode=mode)
    result = InstallResult(
        mode, paths, operations, verification.manifest_sha256,
        existing.get("payload_manifest_sha256") if existing else None,
        existing.get("embercade_version") if existing else None,
        verification.version,
        existing.get("product_label") if existing else None,
        verification.product_label,
    )
    if dry_run or identical:
        return result

    for parent in {
        paths.prefix.parent,
        paths.launcher.parent,
        paths.desktop_entry.parent,
        paths.icon.parent,
        paths.manifest.parent,
    }:
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if parent.is_symlink() or not parent.is_dir():
            raise InstallationError(f"installation parent is unsafe: {parent}")

    manifest = _install_manifest(paths, verification, desktop_text, icon_digest)
    transaction = uuid.uuid4().hex
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".embercade-install-{transaction}-", dir=paths.prefix.parent)
    )
    temporary_payload = temporary_root / "payload"
    temporary_launcher = paths.launcher.parent / f".embercade-launcher-{transaction}"
    temporary_desktop: Path | None = None
    temporary_icon: Path | None = None
    temporary_manifest: Path | None = None
    backups: dict[Path, Path] = {}
    activated: list[Path] = []
    try:
        shutil.copytree(payload_root, temporary_payload, symlinks=True)
        copied = verify_payload(temporary_payload)
        if copied.manifest_sha256 != verification.manifest_sha256:
            raise InstallationError("copied payload changed during installation")
        temporary_launcher.symlink_to(paths.prefix / "bin/embercade")
        temporary_desktop = _temporary_file(
            paths.desktop_entry.parent,
            "embercade.desktop",
            desktop_text.encode(),
            0o644,
        )
        temporary_manifest = _temporary_file(
            paths.manifest.parent,
            "install-manifest.json",
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
            0o600,
        )
        temporary_icon = _temporary_file(
            paths.icon.parent,
            "embercade.png",
            icon_source.read_bytes(),
            0o644,
        )

        for target in (paths.prefix, paths.launcher, paths.desktop_entry, paths.icon, paths.manifest):
            if target.exists() or target.is_symlink():
                backup = target.parent / f".{target.name}.embercade-backup-{transaction}"
                _replace(target, backup)
                backups[target] = backup
        for source, target in (
            (temporary_payload, paths.prefix),
            (temporary_launcher, paths.launcher),
            (temporary_desktop, paths.desktop_entry),
            (temporary_icon, paths.icon),
            (temporary_manifest, paths.manifest),
        ):
            _replace(source, target)
            activated.append(target)
        installed = _existing_installation(paths)
        if installed is None or installed.get("payload_manifest_sha256") != verification.manifest_sha256:
            raise InstallationError("installed application verification failed; activation rolled back")
    except BaseException:
        for target in reversed(activated):
            _remove_path(target)
        for target, backup in reversed(tuple(backups.items())):
            if backup.exists() or backup.is_symlink():
                _replace(backup, target)
        raise
    finally:
        _remove_path(temporary_launcher)
        if temporary_desktop is not None:
            _remove_path(temporary_desktop)
        if temporary_manifest is not None:
            _remove_path(temporary_manifest)
        if temporary_icon is not None:
            _remove_path(temporary_icon)
        _remove_path(temporary_root)
    for backup in backups.values():
        _remove_path(backup)

    updater_env = os.environ if environment is None else environment
    updater = shutil.which("update-desktop-database", path=updater_env.get("PATH", ""))
    if updater:
        subprocess.run(
            [updater, str(paths.desktop_entry.parent)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return result


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.absolute().relative_to(parent.absolute())
    except ValueError:
        return False
    return True


def _purge_protected_paths(paths: UserInstallPaths) -> tuple[Path, ...]:
    config_path = paths.config_root / "embercade.toml"
    config = load_config(config_path)
    protected: list[Path] = []
    path_section = config.get("paths", {})
    if isinstance(path_section, Mapping):
        for name in ("roms", "bios"):
            value = path_section.get(name)
            if isinstance(value, str):
                protected.append(Path(value).expanduser().absolute())
    for section_name in ("executables", "emulators"):
        section = config.get(section_name, {})
        if not isinstance(section, Mapping):
            continue
        for value in section.values():
            candidate = value.get("executable") if isinstance(value, Mapping) else value
            if isinstance(candidate, str) and os.sep in candidate:
                executable = Path(candidate).expanduser().absolute()
                # Imported known providers belong to Embercade's own data root.
                # External provider paths still block an unsafe purge.
                if any(_is_within(executable, paths.data_root / "providers" / name)
                       for name in ("xenia", "shadps4")):
                    continue
                protected.append(executable)
    return tuple(protected)


def _validate_purge(paths: UserInstallPaths) -> None:
    owned = (paths.config_root, paths.data_root, paths.cache_root, paths.state_root)
    for root in owned:
        _require_exact_child(root, root.parent, "purge")
        if root == paths.home:
            raise InstallationError(f"refusing unsafe purge root: {root}")
    for protected in _purge_protected_paths(paths):
        for root in owned:
            if _is_within(protected, root):
                raise InstallationError(
                    f"refusing purge because protected external content is inside {root}: {protected}"
                )


def uninstall_user(
    *,
    environment: Mapping[str, str] | None = None,
    dry_run: bool = False,
    purge: bool = False,
    purge_confirmed: bool = False,
) -> InstallResult:
    paths = UserInstallPaths.from_environment(environment)
    if purge and not purge_confirmed:
        raise InstallationError("purge requires explicit confirmation")
    if purge:
        _validate_purge(paths)
    manifest = _load_install_manifest(paths)
    if manifest is None:
        leftovers = any(
            path.exists() or path.is_symlink()
            for path in (paths.prefix, paths.launcher, paths.desktop_entry, paths.icon)
        )
        if leftovers:
            raise InstallationError(
                "Embercade files exist without an installation manifest; refusing unsafe removal"
            )
        mode = "NOT INSTALLED"
    else:
        _existing_installation(paths)
        mode = "UNINSTALL"
    operations = [
        f"remove immutable payload -> {paths.prefix}",
        f"remove launcher -> {paths.launcher}",
        f"remove desktop entry -> {paths.desktop_entry}",
        f"remove hicolor application icon -> {paths.icon}",
        f"remove install manifest -> {paths.manifest}",
    ]
    if purge:
        operations.extend(
            f"purge Embercade-owned user root -> {root}"
            for root in (paths.config_root, paths.data_root, paths.cache_root, paths.state_root)
        )
        operations.append("preserve configured ROM, BIOS and external provider paths")
    else:
        operations.append("keep Embercade user config, saves, state and cache")
    if dry_run:
        return InstallResult(mode, paths, tuple(operations))

    if manifest is not None:
        _require_exact_child(paths.prefix, paths.home / ".local/lib", "install prefix")
        paths.launcher.unlink()
        paths.desktop_entry.unlink()
        paths.icon.unlink(missing_ok=True)
        shutil.rmtree(paths.prefix)
        paths.manifest.unlink()
    if purge:
        for root in (paths.config_root, paths.data_root, paths.cache_root, paths.state_root):
            if root.exists():
                if root.is_symlink() or not root.is_dir():
                    raise InstallationError(f"refusing unsafe purge target: {root}")
                shutil.rmtree(root)
    return InstallResult(mode, paths, tuple(operations))


def print_operations(result: InstallResult, *, stream: TextIO | None = None) -> None:
    output = sys.stdout if stream is None else stream
    if result.payload_manifest_sha256:
        def describe(label: str | None, version: str | None, revision: str | None) -> str:
            return f"{label or 'product version unknown'} (package {version or 'unknown'}, payload {revision[:12] if revision else 'none'})"
        print(f"Current: {describe(result.current_product_label, result.current_version, result.current_manifest_sha256)}", file=output)
        print(f"Incoming: {describe(result.incoming_product_label, result.incoming_version, result.payload_manifest_sha256)}", file=output)
        print("Payload manifest and file hashes: verified.", file=output)
    print(result.mode, file=output)
    for operation in result.operations:
        print(f"  {operation}", file=output)

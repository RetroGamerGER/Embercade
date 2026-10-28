"""Build and verify a deterministic, offline-installable transfer bundle."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
import argparse
import gzip
import json
import os
import re
import shutil
import stat
import tarfile

from embercade.installer import InstallationError, verify_payload
from embercade.version import __version__


TRANSFER_FORMAT = 1
README_NAME = "README-FIRST-TEST.txt"
CHECKSUM_NAME = "SHA256SUMS"
MANIFEST_NAME = "manifest.json"
FORBIDDEN_RUNTIME_MARKERS = (
    b"e2e" + b"-xdg",
    b"Roms" + b" test",
    b"dev" + b"-run",
)
FORBIDDEN_CONTENT_SUFFIXES = frozenset(
    {
        ".appimage",
        ".chd",
        ".cue",
        ".gcz",
        ".iso",
        ".nes",
        ".rvz",
        ".sfc",
        ".wbfs",
        ".xiso",
    }
)
FORBIDDEN_EMULATOR_BINARIES = frozenset(
    {"retroarch", "dolphin-emu", "pcsx2-qt", "rpcs3", "xemu", "xenia_edge"}
)


class TransferPayloadError(RuntimeError):
    """The transfer payload is incomplete, unsafe or not reproducible."""


@dataclass(frozen=True, slots=True)
class TransferPayloadResult:
    directory: Path
    archive: Path
    manifest: Path
    manifest_sha256: str
    archive_sha256: str
    archive_size: int
    payload_tree_sha256: str


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\0" in value:
        raise TransferPayloadError("transfer manifest contains an invalid path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise TransferPayloadError(f"unsafe transfer manifest path: {value!r}")
    return path


def _entries(root: Path, *, excluded: Iterable[str] = ()) -> tuple[dict[str, Any], ...]:
    excluded_set = set(excluded)
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded_set or path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink():
            entries.append({"path": relative, "type": "symlink", "target": os.readlink(path)})
        elif path.is_file():
            entries.append(
                {
                    "path": relative,
                    "type": "file",
                    "size": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
            )
        else:
            raise TransferPayloadError(f"unsupported transfer payload entry: {path}")
    return tuple(entries)


def _tree_digest(entries: Iterable[dict[str, Any]]) -> str:
    digest = sha256()
    for entry in entries:
        digest.update(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _install_script() -> str:
    return (
        "#!/bin/sh\n"
        "set -eu\n"
        "bundle_root=$(CDPATH= cd -- \"$(dirname -- \"$0\")\" && pwd -P)\n"
        "cd -- \"$bundle_root\"\n"
        "sha256sum --check --quiet SHA256SUMS\n"
        "payload=$bundle_root/payload\n"
        "exec \"$payload/bin/embercade\" install --payload \"$payload\" --no-setup \"$@\"\n"
    )


def _first_test_readme() -> str:
    return """Embercade 0.1 Desktop-Test auf dem zweiten Rechner

1. Dieses Archiv in ein normales Benutzerverzeichnis kopieren und entpacken.
2. Das entpackte Verzeichnis öffnen.
3. Embercade ohne sudo installieren:
   ./install
4. Grafische Einrichtung für ROM-/BIOS-Pfade, Exit-Hotkey und optionale
   Core-/AppImage-Quellen öffnen (bei bestehender gültiger Einrichtung
   können die Fragen übersprungen werden):
   embercade wizard
   Ohne grafische Sitzung bleibt embercade setup verfügbar.
5. Den danach sammlungsabhängigen Host-Paketplan nur anzeigen:
   embercade bootstrap --dry-run
6. Optional die bestätigten CachyOS/Arch/Garuda-Pakete installieren:
   embercade bootstrap
7. Die Installation prüfen:
   embercade doctor
8. Embercade starten:
   embercade

ROM- und BIOS-Mounts werden von diesem Paket weder verändert noch mitgeliefert.
Xenia Edge wird nicht mitgeliefert und muss vom Benutzer separat bereitgestellt werden.
Empfohlener Provider-Ordner:
  $XDG_DATA_HOME/embercade/providers/xenia/
Default:
  ~/.local/share/embercade/providers/xenia/

Falls ~/.local/bin noch nicht in PATH liegt, für die Befehle oben vorübergehend
~/.local/bin/embercade statt embercade verwenden.
"""


def _runtime_surfaces(payload_root: Path) -> tuple[Path, ...]:
    surfaces: list[Path] = []
    for relative in (
        "bin",
        "share/applications",
        "share/embercade/resources",
    ):
        root = payload_root / relative
        if root.is_dir():
            surfaces.extend(path for path in root.rglob("*") if path.is_file())
    for relative in (
        "share/embercade/runtime/venv/pyvenv.cfg",
        "share/embercade/runtime/runtime-info.txt",
    ):
        path = payload_root / relative
        if path.is_file():
            surfaces.append(path)
    return tuple(sorted(set(surfaces)))


def audit_stage_payload(stage_root: Path, *, build_root: Path | None = None) -> None:
    """Reject bundled user content and runtime-facing development references."""
    verify_payload(stage_root)
    for path in stage_root.rglob("*"):
        if path.is_dir() and not path.is_symlink():
            if path.name.casefold() in {"roms", "bios", "providers", "logs", "secrets"}:
                raise TransferPayloadError(f"forbidden user-data directory in payload: {path}")
            continue
        name = path.name.casefold()
        if name in {"screenscraper.conf", "screenscraper-user.conf", "screenscraper-build.conf", "screenscraperauthorization.h", "retroachievements-user.conf", "retroachievements-build.conf"}:
            raise TransferPayloadError("forbidden local credential file in payload")
        if name == "es_settings.cfg" and path.is_file() and not path.is_symlink():
            data = path.read_bytes()
            if b"ScreenScraperPass" in data or b"ScreenScraperUser" in data:
                raise TransferPayloadError("forbidden personal account settings in payload")
        if path.suffix.casefold() in FORBIDDEN_CONTENT_SUFFIXES:
            raise TransferPayloadError(f"forbidden ROM/provider content in payload: {path}")
        if name in FORBIDDEN_EMULATOR_BINARIES:
            raise TransferPayloadError(f"forbidden emulator binary in payload: {path}")

    markers = list(FORBIDDEN_RUNTIME_MARKERS)
    if build_root is not None:
        markers.append(str(build_root.absolute()).encode())
    for path in _runtime_surfaces(stage_root):
        try:
            data = path.read_bytes()
        except OSError as error:
            raise TransferPayloadError(f"cannot audit runtime surface: {path}") from error
        for marker in markers:
            if marker in data:
                raise TransferPayloadError(
                    f"development path marker {marker!r} in runtime surface: {path}"
                )
        if b"PRIVATE KEY-----" in data:
            raise TransferPayloadError(f"private-key material in runtime surface: {path}")


def _checksum_text(bundle_root: Path) -> str:
    lines: list[str] = []
    paths = sorted(
        bundle_root.rglob("*"),
        key=lambda item: item.relative_to(bundle_root).as_posix(),
    )
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.name == CHECKSUM_NAME:
            continue
        relative = path.relative_to(bundle_root).as_posix()
        if "\n" in relative or "\\" in relative:
            raise TransferPayloadError(
                f"path cannot be represented safely in SHA256SUMS: {relative}"
            )
        lines.append(f"{_sha256_file(path)}  {relative}")
    return "\n".join(lines) + "\n"


def _write_checksums(bundle_root: Path) -> None:
    checksums = bundle_root / CHECKSUM_NAME
    checksums.write_text(_checksum_text(bundle_root), encoding="utf-8")
    checksums.chmod(0o644)


def verify_transfer_bundle(bundle_root: Path) -> dict[str, Any]:
    root = bundle_root.absolute()
    manifest_path = root / MANIFEST_NAME
    checksum_path = root / CHECKSUM_NAME
    if root.is_symlink() or not root.is_dir():
        raise TransferPayloadError(f"transfer bundle is not a real directory: {root}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TransferPayloadError(f"transfer manifest is unreadable: {manifest_path}") from error
    if not isinstance(manifest, dict) or manifest.get("format") != TRANSFER_FORMAT:
        raise TransferPayloadError("unsupported transfer manifest format")
    raw_entries = manifest.get("bundle_files")
    if not isinstance(raw_entries, list):
        raise TransferPayloadError("transfer manifest has no bundle file list")
    expected: dict[str, dict[str, Any]] = {}
    for entry in raw_entries:
        if not isinstance(entry, dict):
            raise TransferPayloadError("transfer manifest contains an invalid entry")
        relative = _safe_relative(entry.get("path")).as_posix()
        if relative in expected:
            raise TransferPayloadError(f"duplicate transfer manifest path: {relative}")
        expected[relative] = entry
        path = root / relative
        if entry.get("type") == "symlink":
            if not path.is_symlink() or os.readlink(path) != entry.get("target"):
                raise TransferPayloadError(f"transfer symlink verification failed: {relative}")
        elif entry.get("type") == "file":
            if path.is_symlink() or not path.is_file():
                raise TransferPayloadError(f"transfer file is missing: {relative}")
            size_changed = path.stat().st_size != entry.get("size")
            digest_changed = _sha256_file(path) != entry.get("sha256")
            if size_changed or digest_changed:
                raise TransferPayloadError(f"transfer file verification failed: {relative}")
        else:
            raise TransferPayloadError(f"unknown transfer entry type: {relative}")
    actual = {
        entry["path"]
        for entry in _entries(root, excluded=(MANIFEST_NAME, CHECKSUM_NAME))
    }
    if actual != set(expected):
        raise TransferPayloadError("transfer bundle file set differs from its manifest")
    if not checksum_path.is_file() or checksum_path.is_symlink():
        raise TransferPayloadError(f"transfer checksums are unavailable: {checksum_path}")
    if checksum_path.read_text(encoding="utf-8") != _checksum_text(root):
        raise TransferPayloadError("transfer checksum file does not match bundle contents")
    verify_payload(root / "payload")
    return manifest


def _normalized_tar_info(path: Path, arcname: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(arcname)
    stat_result = path.lstat()
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = 0
    if path.is_symlink():
        info.type = tarfile.SYMTYPE
        info.linkname = os.readlink(path)
        info.mode = 0o777
    elif path.is_dir():
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
    elif path.is_file():
        info.type = tarfile.REGTYPE
        info.size = stat_result.st_size
        info.mode = 0o755 if stat_result.st_mode & stat.S_IXUSR else 0o644
    else:
        raise TransferPayloadError(f"unsupported archive entry: {path}")
    return info


def _write_archive(bundle_root: Path, archive: Path) -> None:
    temporary = archive.with_name(f".{archive.name}.tmp")
    temporary.unlink(missing_ok=True)
    with temporary.open("wb") as raw_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_stream, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as tar:
                paths = (bundle_root, *sorted(bundle_root.rglob("*")))
                for path in paths:
                    relative = path.relative_to(bundle_root.parent).as_posix()
                    info = _normalized_tar_info(path, relative)
                    if path.is_file() and not path.is_symlink():
                        with path.open("rb") as stream:
                            tar.addfile(info, stream)
                    else:
                        tar.addfile(info)
    os.replace(temporary, archive)


def build_transfer_payload(
    *,
    stage_root: Path,
    dist_root: Path,
    source_commit: str,
    version: str = __version__,
    build_root: Path | None = None,
) -> TransferPayloadResult:
    stage = stage_root.absolute()
    dist = dist_root.absolute()
    if dist == Path("/") or dist.is_symlink():
        raise TransferPayloadError(f"unsafe transfer output root: {dist}")
    if dist.is_relative_to(stage) or stage.is_relative_to(dist):
        raise TransferPayloadError("stage and transfer output roots must not overlap")
    if re.fullmatch(r"[0-9a-f]{7,64}", source_commit.casefold()) is None:
        raise TransferPayloadError("source commit must be a hexadecimal Git identifier")
    audit_stage_payload(stage, build_root=build_root)
    bundle_name = f"Embercade-{version}-test"
    bundle = dist / bundle_name
    archive = dist / f"{bundle_name}.tar.gz"
    if bundle.name != bundle_name or archive.name != f"{bundle_name}.tar.gz":
        raise TransferPayloadError("unsafe transfer output names")
    dist.mkdir(parents=True, exist_ok=True)
    if bundle.exists():
        if bundle.is_symlink() or not bundle.is_dir():
            raise TransferPayloadError(f"unsafe existing transfer output: {bundle}")
        shutil.rmtree(bundle)
    archive.unlink(missing_ok=True)
    bundle.mkdir(mode=0o755)
    payload = bundle / "payload"
    shutil.copytree(stage, payload, symlinks=True)
    copied = verify_payload(payload)

    install = bundle / "install"
    install.write_text(_install_script(), encoding="utf-8")
    install.chmod(0o755)
    readme = bundle / README_NAME
    readme.write_text(_first_test_readme(), encoding="utf-8")
    readme.chmod(0o644)

    bundle_entries = _entries(bundle, excluded=(MANIFEST_NAME, CHECKSUM_NAME))
    payload_entries = tuple(
        {**entry, "path": entry["path"].removeprefix("payload/")}
        for entry in bundle_entries
        if entry["path"].startswith("payload/")
    )
    payload_digest = _tree_digest(payload_entries)
    manifest_data = {
        "format": TRANSFER_FORMAT,
        "embercade_version": version,
        "source_commit": source_commit,
        "stage_manifest_sha256": copied.manifest_sha256,
        "payload_tree_sha256": payload_digest,
        "payload_files": list(payload_entries),
        "bundle_files": list(bundle_entries),
    }
    manifest = bundle / MANIFEST_NAME
    manifest.write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest.chmod(0o644)
    _write_checksums(bundle)
    verify_transfer_bundle(bundle)
    _write_archive(bundle, archive)
    return TransferPayloadResult(
        bundle,
        archive,
        manifest,
        _sha256_file(manifest),
        _sha256_file(archive),
        archive.stat().st_size,
        payload_digest,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m embercade.transfer_payload")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--stage-root", required=True, type=Path)
    build.add_argument("--dist-root", required=True, type=Path)
    build.add_argument("--source-commit", required=True)
    build.add_argument("--build-root", type=Path)
    verify = subparsers.add_parser("verify")
    verify.add_argument("bundle_root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            manifest = verify_transfer_bundle(args.bundle_root)
            print(
                f"Verified Embercade {manifest['embercade_version']} transfer payload "
                f"from {manifest['source_commit']}"
            )
            return 0
        result = build_transfer_payload(
            stage_root=args.stage_root,
            dist_root=args.dist_root,
            source_commit=args.source_commit,
            build_root=args.build_root,
        )
    except (OSError, InstallationError, TransferPayloadError, ValueError) as error:
        parser.error(str(error))
    print(f"Prepared transfer directory: {result.directory}")
    print(f"Archive: {result.archive}")
    print(f"Manifest SHA256: {result.manifest_sha256}")
    print(f"Archive SHA256: {result.archive_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Copy user-supplied Libretro cores and known AppImages into Embercade data.

Sources are never executed or modified.  Existing managed files are immutable:
an equal provider is reused regardless of its source name; different content
is a conflict. Recognition is not a signature/authenticity guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import stat
import struct
import tempfile
import selectors
import shutil
import subprocess
import time

from embercade.cores import CORE_SUFFIX


class ImportError(RuntimeError):
    """An import source or destination cannot be used safely."""


@dataclass(frozen=True, slots=True)
class ImportResult:
    found: int
    valid: int
    imported: int
    present: int
    skipped: tuple[str, ...]
    conflicts: tuple[str, ...]
    imported_paths: tuple[Path, ...]
    ambiguous: tuple[str, ...] = ()


def _source_directory(path: Path) -> Path:
    path = path.expanduser().absolute()
    if path.is_symlink() or not path.is_dir() or not os.access(path, os.R_OK | os.X_OK):
        raise ImportError(f"Source directory is not readable: {path}")
    return path


def _elf_header(stream, size: int, *, appimage: bool = False) -> str | None:
    """Validate bounded ELF64/x86-64 metadata without loading untrusted code."""
    if size < 64:
        return "truncated ELF"
    stream.seek(0)
    header = stream.read(64)
    if len(header) != 64:
        return "truncated ELF"
    if header[:4] != b"\x7fELF" or header[4:7] != b"\x02\x01\x01":
        return "not a 64-bit little-endian ELF"
    if appimage and header[8:11] not in (b"AI\x01", b"AI\x02"):
        return "not an AppImage"
    e_type, machine, version = struct.unpack_from("<HHI", header, 16)
    if e_type not in ((2, 3) if appimage else (3,)) or machine != 62 or version != 1:
        return "not an x86-64 shared object"
    phoff = struct.unpack_from("<Q", header, 32)[0]
    phentsize, phnum = struct.unpack_from("<HH", header, 54)
    if not phoff or not phnum or phentsize < 56 or phoff + phentsize * phnum > size:
        return "damaged ELF program headers"
    loadable = False
    for index in range(phnum):
        stream.seek(phoff + index * phentsize)
        entry = stream.read(56)
        if len(entry) != 56:
            return "truncated ELF program header"
        p_type, _flags, p_offset, _vaddr, _paddr, filesz, memsz, _align = struct.unpack(
            "<IIQQQQQQ", entry
        )
        if p_type == 1:
            if p_offset + filesz > size or filesz > memsz:
                return "damaged ELF load segment"
            loadable = True
    return None if loadable else "no ELF load segment"


def _has_libretro_symbols(stream) -> bool:
    required = {b"retro_init\0", b"retro_get_system_info\0", b"retro_set_environment\0"}
    found: set[bytes] = set()
    stream.seek(0)
    tail = b""
    while chunk := stream.read(1024 * 1024):
        data = tail + chunk
        found.update(symbol for symbol in required if symbol in data)
        if found == required:
            return True
        tail = data[-32:]
    return False


def _digest(stream) -> str:
    stream.seek(0)
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def _open_regular(path: Path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
    descriptor = os.open(path, flags)
    stream = os.fdopen(descriptor, "rb")
    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
        stream.close()
        raise ImportError(f"Not a regular file: {path}")
    return stream


KNOWN_APPIMAGES = {
    "xenia-edge": ("xenia", "xenia_edge_linux.AppImage",
                   "usr/share/applications/xenia_edge.desktop", "Xenia Edge", "xenia_edge"),
    "shadps4": ("shadps4", "shadps4.AppImage",
                "usr/share/applications/net.shadps4.shadPS4.desktop", "shadPS4", "shadps4"),
}


def _provider_metadata(stream, size: int, provider: str = "xenia-edge") -> dict[str, str]:
    entry = KNOWN_APPIMAGES[provider][2]
    output = _appimage_read(stream, size, entry)
    fields: dict[str, str] = {}
    in_entry = False
    for line in output.decode("utf-8", errors="replace").splitlines():
        if line.startswith("["):
            in_entry = line.strip() == "[Desktop Entry]"
        elif in_entry and "=" in line:
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip()
    return fields


def _appimage_read(stream, size: int, entry: str, *, limit: int = 8192) -> bytes:
    """Read the known type-2 AppImage desktop entry, never its executable.

    unsquashfs/7z are host inspection tools, not provider downloaders/runtimes.
    Pass the already-open fd so a replaced source path cannot change this read.
    Bound the ELF offsets, helper output and time; no extraction writes.
    """
    stream.seek(0)
    header = stream.read(64)
    if len(header) != 64 or header[8:11] != b"AI\x02":
        raise ImportError("Provider recognition requires a type-2 AppImage")
    shoff = struct.unpack_from("<Q", header, 40)[0]
    entsize, count = struct.unpack_from("<HH", header, 58)
    if not shoff or not count or entsize < 64 or shoff + entsize * count > size:
        raise ImportError("damaged AppImage section headers")
    offset = shoff + entsize * count
    for index in range(count):
        stream.seek(shoff + entsize * index)
        section = stream.read(64)
        if len(section) != 64:
            raise ImportError("truncated AppImage section header")
        section_type = struct.unpack_from("<I", section, 4)[0]
        section_offset, section_size = struct.unpack_from("<QQ", section, 24)
        if section_type != 8:  # SHT_NOBITS has no file contents
            if section_offset + section_size > size:
                raise ImportError("damaged AppImage section")
            offset = max(offset, section_offset + section_size)
    stream.seek(offset)
    if stream.read(4) != b"hsqs":
        raise ImportError("missing AppImage SquashFS payload")
    source = f"/proc/self/fd/{stream.fileno()}"
    if helper := shutil.which("unsquashfs"):
        command = [helper, "-o", str(offset), "-cat", source, entry]
    elif helper := next((found for name in ("7zz", "7z", "7za")
                         if (found := shutil.which(name))), None):
        command = [helper, "e", "-so", "-tSquashFS", "-spd", source, entry]
    else:
        raise ImportError("cannot inspect AppImage identity: unsquashfs or 7z is unavailable")
    with subprocess.Popen(command, pass_fds=(stream.fileno(),), stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as process:
        assert process.stdout is not None
        output = bytearray()
        deadline = time.monotonic() + 5
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            try:
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise ImportError("AppImage metadata inspection timed out")
                    if not selector.select(remaining):
                        continue
                    chunk = os.read(process.stdout.fileno(), min(1024 * 1024, limit + 1 - len(output)))
                    if not chunk:
                        selector.unregister(process.stdout)
                        break
                    output.extend(chunk)
                    if len(output) > limit:
                        raise ImportError("AppImage desktop metadata is too large")
                if process.wait(timeout=max(0.01, deadline - time.monotonic())):
                    raise ImportError("unsupported provider: desktop entry not found")
            except (ImportError, subprocess.TimeoutExpired) as error:
                process.kill()  # only the bounded metadata helper, never the AppImage
                process.wait()
                if isinstance(error, ImportError):
                    raise
                raise ImportError("AppImage metadata inspection timed out") from error
    return bytes(output)


def provider_runtime_dependencies(path: Path, *, provider: str) -> tuple[str, ...]:
    """Read the embedded ELF, not the static AppImage runtime. No extraction writes.

    Use an anonymous memfd and the existing loader-closure checker. The provider
    is never executed. Host-only closure is deliberately conservative: bundled
    libraries cannot mask a missing host dependency here.
    """
    from embercade.elf_runtime import inspect_elf_runtime
    executable = KNOWN_APPIMAGES[provider][4]
    with _open_regular(path) as stream:
        before = os.fstat(stream.fileno())
        payload = _appimage_read(stream, before.st_size, f"usr/bin/{executable}", limit=128 * 1024 * 1024)
        if _inspection_stamp(os.fstat(stream.fileno())) != _inspection_stamp(before):
            raise ImportError("Source changed during provider dependency inspection")
    descriptor = os.memfd_create("embercade-provider-elf", 0)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as output:
            output.write(payload)
            output.flush()
        def runner(command, **options):
            return subprocess.run(command, pass_fds=(descriptor,), timeout=10, **options)
        closure = inspect_elf_runtime(Path(f"/proc/self/fd/{descriptor}"), runner=runner)
        return closure.missing + ((closure.error,) if closure.error else ())
    finally:
        os.close(descriptor)


def _inspection_stamp(metadata) -> tuple[int, int, int]:
    return metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns


def _inspect_provider_stream(stream, *, require_executable: bool, provider: str = "xenia-edge"):
    metadata = os.fstat(stream.fileno())
    if not metadata.st_mode & 0o444:
        raise ImportError("provider is unreadable")
    if require_executable and not metadata.st_mode & 0o111:
        raise ImportError("provider is not executable; reimport to repair managed permissions")
    if error := _elf_header(stream, metadata.st_size, appimage=True):
        raise ImportError(error)
    if provider not in KNOWN_APPIMAGES:
        raise ImportError(f"unsupported provider: {provider}")
    fields = (_provider_metadata(stream, metadata.st_size) if provider == "xenia-edge"
              else _provider_metadata(stream, metadata.st_size, provider))
    _directory, _filename, _entry, name, executable = KNOWN_APPIMAGES[provider]
    if (fields.get("Name") != name
            or fields.get("Exec") not in {executable, f"{executable} %f", f"{executable} %F"}
            or fields.get("StartupWMClass", "").rstrip(";") != executable):
        raise ImportError(f"unsupported provider: desktop identity is not {name}")
    if _inspection_stamp(os.fstat(stream.fileno())) != _inspection_stamp(metadata):
        raise ImportError("Source changed during provider inspection")
    return metadata


def inspect_provider(path: Path, *, require_executable: bool = False, provider: str = "xenia-edge") -> Path:
    """Validate one known user-supplied AppImage without running it."""
    path = Path(path).expanduser().absolute()
    if path.suffix.casefold() != ".appimage":
        raise ImportError("not an AppImage file")
    try:
        with _open_regular(path) as stream:
            _inspect_provider_stream(stream, require_executable=require_executable, provider=provider)
        if not os.access(path, os.R_OK | (os.X_OK if require_executable else 0)):
            raise ImportError("provider is unreadable or not executable")
    except OSError as error:
        raise ImportError(f"provider is unavailable: {path}: {error.strerror}") from error
    return path


def provider_candidates(source: Path, *, require_executable: bool = False, provider: str = "xenia-edge") -> tuple[dict[str, Path], tuple[str, ...], int]:
    """One candidate per content hash; never choose between different builds."""
    source = Path(source).expanduser().absolute()
    paths = (source,) if source.is_file() or source.is_symlink() else tuple(sorted(_source_directory(source).iterdir()))
    candidates: dict[str, Path] = {}
    skipped: list[str] = []
    found = 0
    for path in paths:
        if path.suffix.casefold() != ".appimage":
            continue
        found += 1
        try:
            with _open_regular(path) as stream:
                inspected = _inspect_provider_stream(stream, require_executable=require_executable, provider=provider)
                digest = _digest(stream)
                if _inspection_stamp(os.fstat(stream.fileno())) != _inspection_stamp(inspected):
                    raise ImportError("Source changed during provider hashing")
            candidates.setdefault(digest, path)
        except (OSError, ImportError) as error:
            skipped.append(f"{path.name}: {error}")
    return candidates, tuple(skipped), found


def _copy_new(stream, source_digest: str, target: Path, *, executable: bool) -> str:
    if target.is_symlink():
        return "conflict"
    if target.exists():
        if not target.is_file():
            return "conflict"
        with _open_regular(target) as existing:
            return "present" if _digest(existing) == source_digest else "conflict"
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if target.parent.is_symlink() or not target.parent.is_dir():
        raise ImportError(f"Managed directory is unsafe: {target.parent}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".embercade-import-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            stream.seek(0)
            digest = hashlib.sha256()
            while chunk := stream.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
            output.flush()
            os.fsync(output.fileno())
        if digest.hexdigest() != source_digest:
            raise ImportError("Source changed during import")
        temporary.chmod(0o700 if executable else 0o600)
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError:
            with _open_regular(target) as existing:
                return "present" if _digest(existing) == source_digest else "conflict"
        return "imported"
    finally:
        temporary.unlink(missing_ok=True)


def _import_directory(source: Path, destination: Path) -> ImportResult:
    source = _source_directory(source)
    if destination.resolve(strict=False) == source.resolve():
        raise ImportError("Source and managed destination must be different")
    root = destination.parent
    check = destination
    while True:
        if check.is_symlink():
            raise ImportError(f"Managed directory is a symlink: {check}")
        if check == root:
            break
        check = check.parent
    found = valid = imported = present = 0
    skipped: list[str] = []
    conflicts: list[str] = []
    imported_paths: list[Path] = []
    for candidate in sorted(source.iterdir()):
        if not candidate.name.endswith(CORE_SUFFIX):
            continue
        found += 1
        if candidate.is_symlink() or not candidate.is_file():
            skipped.append(f"{candidate.name}: not a regular file")
            continue
        try:
            with _open_regular(candidate) as stream:
                error = _elf_header(stream, os.fstat(stream.fileno()).st_size)
                if error is None and not _has_libretro_symbols(stream):
                    error = "missing Libretro entry points"
                if error is not None:
                    skipped.append(f"{candidate.name}: {error}")
                    continue
                valid += 1
                digest = _digest(stream)
                target = destination / candidate.name
                state = _copy_new(stream, digest, target, executable=False)
                if state == "imported":
                    imported += 1
                    imported_paths.append(target)
                elif state == "present":
                    present += 1
                    imported_paths.append(target)
                else:
                    conflicts.append(candidate.name)
        except (OSError, ImportError) as error:
            skipped.append(f"{candidate.name}: {error}")
    return ImportResult(found, valid, imported, present, tuple(skipped), tuple(conflicts), tuple(imported_paths))


def import_cores(source: Path, managed_data: Path) -> ImportResult:
    return _import_directory(source, managed_data / "cores")


def import_providers(source: Path, managed_data: Path, *, provider: str = "xenia-edge") -> ImportResult:
    if provider not in KNOWN_APPIMAGES:
        raise ImportError(f"unsupported provider: {provider}")
    source = Path(source).expanduser().absolute()
    directory, filename, *_identity = KNOWN_APPIMAGES[provider]
    destination = managed_data / "providers" / directory
    # Validate the whole existing managed chain even when reusing a file.
    for path in (managed_data, destination.parent, destination):
        if path.is_symlink():
            raise ImportError(f"Managed directory is a symlink: {path}")
    candidates, skipped, found = provider_candidates(source, provider=provider)
    valid = len(candidates)
    if valid != 1:
        return ImportResult(found, valid, 0, 0, skipped, (), (),
                            tuple(path.name for path in candidates.values()) if valid > 1 else ())
    digest, candidate = next(iter(candidates.items()))
    existing = tuple(sorted(destination.iterdir())) if destination.exists() else ()
    for path in existing:
        if path.suffix.casefold() != ".appimage":
            continue
        try:
            with _open_regular(path) as stream:
                _inspect_provider_stream(stream, require_executable=False, provider=provider)
                if _digest(stream) == digest:
                    # Repair only this verified managed file's executable bit.
                    if not os.fstat(stream.fileno()).st_mode & 0o111:
                        os.fchmod(stream.fileno(), 0o700)
                    return ImportResult(found, valid, 0, 1, skipped, (), (path,))
        except (OSError, ImportError):
            pass
    if any(path.suffix.casefold() == ".appimage" for path in existing):
        return ImportResult(found, valid, 0, 0, skipped,
                            tuple(path.name for path in existing if path.suffix.casefold() == ".appimage"), ())
    if source.resolve() == destination.resolve(strict=False):
        raise ImportError("Managed provider needs attention; no valid source to import")
    # A single stable managed filename, independent of the supplied basename.
    target = destination / filename
    try:
        with _open_regular(candidate) as stream:
            _inspect_provider_stream(stream, require_executable=False, provider=provider)
            state = _copy_new(stream, digest, target, executable=True)
    except OSError as error:
        raise ImportError(f"Provider could not be copied safely: {error}") from error
    return ImportResult(found, valid, int(state == "imported"), int(state == "present"), skipped,
                        (target.name,) if state == "conflict" else (),
                        (target,) if state in {"imported", "present"} else ())

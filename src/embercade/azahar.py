"""Compatibility for Azahar Libretro's isolated emulated-system settings."""

from __future__ import annotations

from pathlib import Path
from struct import unpack_from
import os
import stat
import tempfile


class AzaharConfigError(RuntimeError):
    """The isolated Azahar system configuration is unsafe or malformed."""


CONFIG_SIZE = 0x8000
CONFIG_HEADER_SIZE = 0x455C
MAX_BLOCK_ENTRIES = 1479
BLOCK_ENTRY_SIZE = 12
LANGUAGE_BLOCK_ID = 0x000A0002
LANGUAGE_VALUES = {
    "Japanese": 0,
    "English": 1,
    "French": 2,
    "German": 3,
    "Italian": 4,
    "Spanish": 5,
    "Simplified Chinese": 6,
    "Korean": 7,
    "Dutch": 8,
    "Portuguese": 9,
    "Russian": 10,
    "Traditional Chinese": 11,
}


def _batocera_value(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    value: str | None = None
    for raw_line in path.read_text(encoding="latin1").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        candidate, raw_value = line.split("=", 1)
        if candidate.strip() == key:
            value = raw_value.strip()
    return value


def azahar_system_config(saves_root: Path) -> Path:
    return (
        saves_root
        / "3ds/Azahar/nand/data/00000000000000000000000000000000"
        / "sysdata/00010017/00000000/config"
    )


def sync_azahar_system_language(*, batocera_conf: Path, saves_root: Path) -> bool:
    """Persist the selected language in Azahar's private 3DS CFG save.

    Azahar Libretro parses ``citra_language_value`` but currently does not
    reliably expose it through the CFG block commercial titles read.  Only the
    Embercade-owned NAND copy is changed, atomically and after validating the
    upstream file layout.  A missing file is a normal first-launch condition.
    """
    selected = _batocera_value(batocera_conf, "3ds.3ds_system_language")
    if selected is None:
        return False
    try:
        language = LANGUAGE_VALUES[selected]
    except KeyError as error:
        raise AzaharConfigError(f"Unsupported Azahar system language: {selected}") from error

    config = azahar_system_config(saves_root)
    if not config.exists():
        return False
    if config.is_symlink() or not config.is_file():
        raise AzaharConfigError(f"Refusing unsafe Azahar system configuration: {config}")

    original = config.read_bytes()
    if len(original) != CONFIG_SIZE:
        raise AzaharConfigError(
            f"Unexpected Azahar system configuration size {len(original)}: {config}"
        )
    total_entries, data_offset = unpack_from("<HH", original, 0)
    if total_entries > MAX_BLOCK_ENTRIES or data_offset != CONFIG_HEADER_SIZE:
        raise AzaharConfigError(f"Malformed Azahar system configuration header: {config}")

    matches: list[int] = []
    for index in range(total_entries):
        entry_offset = 4 + index * BLOCK_ENTRY_SIZE
        block_id, _offset_or_data, size, _flags = unpack_from(
            "<IIHH", original, entry_offset
        )
        if block_id == LANGUAGE_BLOCK_ID:
            if size != 1:
                raise AzaharConfigError(
                    f"Unexpected Azahar language block size {size}: {config}"
                )
            matches.append(entry_offset + 4)
    if len(matches) != 1:
        raise AzaharConfigError(
            f"Expected one Azahar language block, found {len(matches)}: {config}"
        )
    if original[matches[0]] == language:
        return False

    updated = bytearray(original)
    updated[matches[0]] = language
    descriptor, raw_temporary = tempfile.mkstemp(prefix=".config.embercade.", dir=config.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(stat.S_IMODE(config.stat().st_mode))
        os.replace(temporary, config)
    finally:
        temporary.unlink(missing_ok=True)
    return True

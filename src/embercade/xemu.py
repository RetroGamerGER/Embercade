"""Prepare isolated Xemu firmware and writable state from read-only sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import os
import shutil

from embercade.paths import EmbercadePaths


class XemuRuntimeError(RuntimeError):
    """A required Xemu source or isolated runtime file is unavailable."""


@dataclass(frozen=True, slots=True)
class XemuFiles:
    flashrom: Path
    bootrom: Path
    eeprom: Path
    hdd: Path

    def as_environment(self) -> dict[str, str]:
        return {
            "EMBERCADE_XEMU_FLASHROM": str(self.flashrom),
            "EMBERCADE_XEMU_BOOTROM": str(self.bootrom),
            "EMBERCADE_XEMU_EEPROM": str(self.eeprom),
            "EMBERCADE_XEMU_HDD": str(self.hdd),
        }


def isolated_xemu_files(paths: EmbercadePaths) -> XemuFiles:
    firmware = paths.isolated_bios / "xemu"
    saves = paths.saves / "xbox"
    return XemuFiles(
        flashrom=firmware / "Complex_4627.bin",
        bootrom=firmware / "mcpx_1.0.bin",
        eeprom=saves / "xemu_eeprom.bin",
        hdd=saves / "xbox_hdd.qcow2",
    )


@dataclass(frozen=True, slots=True)
class XemuStatus:
    firmware_ready: bool
    eeprom_ready: bool
    hdd_ready: bool
    firmware_detail: str
    eeprom_detail: str
    hdd_detail: str


def inspect_xemu_files(
    paths: EmbercadePaths,
    environment: Mapping[str, str] | None = None,
) -> XemuStatus:
    env = os.environ if environment is None else environment
    files = isolated_xemu_files(paths)

    def source(field: str) -> Path:
        value = env.get(_SOURCE_ENV[field])
        candidate = (
            Path(value).expanduser().absolute()
            if value
            else paths.bios_root / _BIOS_SOURCE_NAMES[field]
        )
        if value or candidate.is_file():
            return candidate
        home = Path(env.get("HOME", str(Path.home()))).expanduser().absolute()
        data_home = Path(env.get("XDG_DATA_HOME", home / ".local/share"))
        return data_home / "xemu" / "xemu" / _BIOS_SOURCE_NAMES[field]

    flash = files.flashrom.is_file() or source("flashrom").is_file()
    boot = files.bootrom.is_file() or source("bootrom").is_file()
    hdd_source = source("hdd")
    return XemuStatus(
        flash and boot,
        files.eeprom.is_file(),
        files.hdd.is_file(),
        "MCPX and flash ROM available" if flash and boot else "MCPX and/or flash ROM missing",
        (
            str(files.eeprom)
            if files.eeprom.is_file()
            else f"created by Xemu on first start at {files.eeprom}"
        ),
        (
            str(files.hdd)
            if files.hdd.is_file()
            else f"missing; seed source {'available' if hdd_source.is_file() else 'missing'}"
        ),
    )


_SOURCE_ENV = {
    "flashrom": "EMBERCADE_XEMU_FLASHROM_SOURCE",
    "bootrom": "EMBERCADE_XEMU_BOOTROM_SOURCE",
    "eeprom": "EMBERCADE_XEMU_EEPROM_SOURCE",
    "hdd": "EMBERCADE_XEMU_HDD_SOURCE",
}

_BIOS_SOURCE_NAMES = {
    "flashrom": "Complex_4627.bin",
    "bootrom": "mcpx_1.0.bin",
    "eeprom": "eeprom.bin",
    "hdd": "xbox_hdd.qcow2",
}


def prepare_xemu_files(
    paths: EmbercadePaths,
    environment: Mapping[str, str] | None = None,
) -> XemuFiles:
    """Create first-run working copies without modifying or replacing sources."""
    env = os.environ if environment is None else environment
    files = isolated_xemu_files(paths)
    for field, source_variable in _SOURCE_ENV.items():
        destination = getattr(files, field)
        if destination.exists() or destination.is_symlink():
            if not destination.is_symlink() and destination.is_file() and os.access(destination, os.R_OK | os.W_OK):
                continue
            raise XemuRuntimeError(
                f"Existing isolated Xemu {field} is not a readable, writable file: {destination}"
            )
        source_text = env.get(source_variable)
        source = (
            Path(source_text).expanduser().absolute()
            if source_text
            else paths.bios_root / _BIOS_SOURCE_NAMES[field]
        )
        # Xemu's get_eeprom_path() generates a valid EEPROM at the configured
        # path if it is absent. Keep legacy/user-selected seeds optional.
        if field == "eeprom" and not source.exists() and not source.is_symlink():
            if source_text:
                raise XemuRuntimeError(f"Configured Xemu EEPROM seed is unavailable: {source}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            continue
        if not source.is_file() or not os.access(source, os.R_OK):
            raise XemuRuntimeError(
                f"Xemu {field} source is unavailable; configure {source_variable} "
                f"or provide {paths.bios_root / _BIOS_SOURCE_NAMES[field]}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.embercade-copy")
        try:
            shutil.copyfile(source, temporary)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    return files


def xemu_source_environment(
    source_directory: Path,
    environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Preflight firmware/HDD and an optional EEPROM seed before any writes."""
    source_directory = source_directory.expanduser().absolute()
    if not source_directory.is_dir():
        raise XemuRuntimeError(f"Xbox-Systemdateien: Ordner nicht lesbar: {source_directory}")
    source_environment = dict(os.environ if environment is None else environment)
    for field, variable in _SOURCE_ENV.items():
        source = source_directory / _BIOS_SOURCE_NAMES[field]
        if field == "eeprom" and not source.exists() and not source.is_symlink():
            source_environment.pop(variable, None)
            continue
        if not source.is_file() or not os.access(source, os.R_OK):
            raise XemuRuntimeError(f"Xbox-Systemdatei fehlt: {source}")
        source_environment[variable] = str(source)
    return source_environment


def prepare_xemu_files_from(
    paths: EmbercadePaths,
    source_directory: Path,
    environment: Mapping[str, str] | None = None,
) -> XemuFiles:
    """Use the normal Xemu preparation path with a selected read-only source."""
    return prepare_xemu_files(paths, xemu_source_environment(source_directory, environment))

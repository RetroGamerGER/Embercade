"""Prepare an isolated RPCS3 firmware tree from an existing read-only profile."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os
import re
import shutil
import subprocess

from embercade.paths import EmbercadePaths


class Rpcs3RuntimeError(RuntimeError):
    """The isolated RPCS3 runtime cannot be prepared safely."""


@dataclass(frozen=True, slots=True)
class Rpcs3Runtime:
    config_dir: Path
    firmware_source: Path
    firmware_version: str
    icons_dir: Path | None

    def as_environment(self) -> dict[str, str]:
        environment = {
            "EMBERCADE_RPCS3_FIRMWARE_SOURCE": str(self.firmware_source),
        }
        if self.icons_dir is not None:
            environment["EMBERCADE_RPCS3_ICONS"] = str(self.icons_dir)
        return environment


def _configured_path(
    config: Mapping[str, Any], key: str, environment: Mapping[str, str], env_key: str
) -> Path | None:
    section = config.get("rpcs3", {})
    if not isinstance(section, Mapping):
        raise Rpcs3RuntimeError("[rpcs3] must be a TOML table")
    value = section.get(key, environment.get(env_key))
    if value is None:
        return None
    if not isinstance(value, (str, os.PathLike)):
        raise Rpcs3RuntimeError(f"[rpcs3].{key} must be a path string")
    return Path(value).expanduser().absolute()


def firmware_version(root: Path) -> str | None:
    version_file = root / "dev_flash" / "vsh" / "etc" / "version.txt"
    try:
        for line in version_file.read_text(encoding="utf-8").splitlines():
            if match := re.match(r"^release:([^:]+):", line):
                return match.group(1)
    except OSError:
        return None
    return None


@dataclass(frozen=True, slots=True)
class Rpcs3FirmwareStatus:
    installed: bool
    version: str | None
    detail: str


def inspect_rpcs3_firmware(
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
) -> Rpcs3FirmwareStatus:
    isolated = paths.emulator_configs / "rpcs3"
    if version := firmware_version(isolated):
        return Rpcs3FirmwareStatus(True, version, f"installed in {isolated}")
    source = _firmware_source(paths, config, environment)
    if source is not None and (version := firmware_version(source)):
        return Rpcs3FirmwareStatus(
            True, version, f"installed host profile ready to import from {source}"
        )
    return Rpcs3FirmwareStatus(
        False,
        None,
        "not installed (a PS3UPDAT.PUP file alone is not installed firmware)",
    )


def _firmware_source(paths: EmbercadePaths, config: Mapping[str, Any],
                     environment: Mapping[str, str]) -> Path | None:
    source = _configured_path(config, "firmware_source", environment, "EMBERCADE_RPCS3_FIRMWARE_SOURCE")
    if source is not None:
        return source
    isolated = paths.emulator_configs / "rpcs3"
    if firmware_version(isolated) is not None:
        return isolated
    home = Path(environment.get("HOME", str(Path.home()))).expanduser().absolute()
    candidate = Path(environment.get("XDG_CONFIG_HOME", home / ".config")) / "rpcs3"
    return candidate if firmware_version(candidate) is not None else None


def existing_firmware_package(bios_root: Path) -> Path | None:
    """Find only the conventional user-supplied PUP in the selected BIOS root."""
    for candidate in (bios_root / "PS3UPDAT.PUP", bios_root / "ps3" / "PS3UPDAT.PUP"):
        if candidate.is_file() and not candidate.is_symlink() and os.access(candidate, os.R_OK):
            return candidate
    return None


def open_firmware_installer(
    executable: Path,
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
    *,
    runner=subprocess.run,
    pup: Path | None = None,
) -> Rpcs3FirmwareStatus:
    """Open RPCS3's UI with only Embercade-owned writable XDG locations."""
    private_home = paths.data / "rpcs3-first-run-home"
    for directory in (paths.emulator_configs, paths.data, paths.cache, paths.state, private_home):
        directory.mkdir(parents=True, exist_ok=True)
    isolated_env = dict(environment)
    isolated_env.update({
        "HOME": str(private_home),
        "XDG_CONFIG_HOME": str(paths.emulator_configs),
        "XDG_DATA_HOME": str(paths.data),
        "XDG_CACHE_HOME": str(paths.cache),
        "XDG_STATE_HOME": str(paths.state),
    })
    command = [str(executable)]
    if pup is not None:
        command.extend(('--installfw', str(pup)))
    result = runner(command, check=False, env=isolated_env)
    if result.returncode:
        raise Rpcs3RuntimeError('RPCS3 firmware installer failed or was cancelled')
    return inspect_rpcs3_firmware(paths, config, environment)


def rpcs3_writable_directories(paths: EmbercadePaths) -> tuple[Path, ...]:
    config_dir = paths.emulator_configs / "rpcs3"
    return (
        config_dir,
        config_dir / "GuiConfigs",
        config_dir / "input_configs" / "global",
        paths.saves / "ps3" / "rpcs3" / "dev_hdd0",
        paths.cache / "ps3",
        paths.logs / "rpcs3",
    )


def resolve_rpcs3_runtime(
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
    *,
    require_isolated_firmware: bool = True,
) -> Rpcs3Runtime:
    config_dir = paths.emulator_configs / "rpcs3"
    source = _firmware_source(paths, config, environment)
    if source is None or not source.is_dir() or not os.access(source, os.R_OK):
        raise Rpcs3RuntimeError(
            "RPCS3 firmware source is unavailable; configure [rpcs3].firmware_source "
            "or EMBERCADE_RPCS3_FIRMWARE_SOURCE"
        )
    source_version = firmware_version(source)
    if source_version is None:
        raise Rpcs3RuntimeError(f"No installed RPCS3 firmware found in: {source}")

    if require_isolated_firmware:
        isolated_version = firmware_version(config_dir)
        if isolated_version != source_version:
            raise Rpcs3RuntimeError(
                "Isolated RPCS3 firmware is missing or does not match the configured source"
            )

    icons = _configured_path(config, "icons", environment, "EMBERCADE_RPCS3_ICONS_SOURCE")
    if icons is None:
        default_icons = Path("/usr/share/rpcs3/Icons")
        icons = default_icons if default_icons.is_dir() else None
    elif not icons.is_dir() or not os.access(icons, os.R_OK):
        raise Rpcs3RuntimeError(f"RPCS3 icon resource directory is not readable: {icons}")

    return Rpcs3Runtime(config_dir, source, source_version, icons)


def prepare_rpcs3_firmware(
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
) -> Rpcs3Runtime:
    runtime = resolve_rpcs3_runtime(
        paths,
        config,
        environment,
        require_isolated_firmware=False,
    )
    runtime.config_dir.mkdir(parents=True, exist_ok=True)

    current_version = firmware_version(runtime.config_dir)
    if current_version is not None and current_version != runtime.firmware_version:
        raise Rpcs3RuntimeError(
            f"Isolated RPCS3 firmware {current_version} differs from source "
            f"{runtime.firmware_version}; refusing to overwrite it"
        )

    if current_version is None:
        for name in ("dev_flash", "dev_flash2", "dev_flash3"):
            source = runtime.firmware_source / name
            if not source.is_dir():
                raise Rpcs3RuntimeError(f"RPCS3 firmware component is missing: {source}")
            target = runtime.config_dir / name
            if target.exists():
                raise Rpcs3RuntimeError(
                    f"Incomplete isolated RPCS3 firmware target already exists: {target}"
                )
            temporary = runtime.config_dir / f".{name}.embercade-new"
            if temporary.exists():
                raise Rpcs3RuntimeError(f"Stale RPCS3 firmware staging path exists: {temporary}")
            shutil.copytree(source, temporary, copy_function=shutil.copy2)
            temporary.replace(target)

    if runtime.firmware_source == runtime.config_dir:
        return runtime

    marker = runtime.config_dir / "embercade-firmware.json"
    marker.write_text(
        json.dumps(
            {
                "source": str(runtime.firmware_source),
                "version": runtime.firmware_version,
                "components": ["dev_flash", "dev_flash2", "dev_flash3"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return resolve_rpcs3_runtime(paths, config, environment)

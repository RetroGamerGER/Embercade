"""PCSX2 desktop prerequisites with read-only source firmware."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import os
import shutil

from embercade.paths import EmbercadePaths


class Pcsx2RuntimeError(RuntimeError):
    """A host PCSX2 prerequisite is missing or unsafe."""


@dataclass(frozen=True, slots=True)
class Pcsx2Runtime:
    bios_dir: Path
    resources_dir: Path

    def as_environment(self) -> dict[str, str]:
        return {
            "EMBERCADE_PCSX2_BIOS_DIR": str(self.bios_dir),
            "EMBERCADE_PCSX2_RESOURCES": str(self.resources_dir),
            "EMBERCADE_PCSX2_INSTALL_DIR": str(self.resources_dir.parent),
        }


_BIOS_IMAGE_SUFFIXES = frozenset({".bin", ".rom"})
_BIOS_COMPANION_SUFFIXES = frozenset({".mec", ".nvm"})
_DEFAULT_RESOURCE_CANDIDATES = (
    Path("/usr/share/pcsx2/resources"),
    Path("/usr/share/PCSX2/resources"),
)


def _prepare_bios_workspace(paths: EmbercadePaths, source: Path) -> Path:
    """Expose immutable BIOS images beside private, writable PCSX2 state."""
    workspace = paths.isolated_bios / "ps2"
    if workspace.is_symlink():
        raise Pcsx2RuntimeError(f"Refusing symlink PCSX2 BIOS workspace: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)

    images = tuple(
        path
        for path in source.iterdir()
        if path.is_file()
        and path.suffix.casefold() in _BIOS_IMAGE_SUFFIXES
        and os.access(path, os.R_OK)
    )
    if not images:
        raise Pcsx2RuntimeError(f"No readable PCSX2 BIOS image found in: {source}")

    expected_links = {image.name: image.absolute() for image in images}
    for existing in workspace.iterdir():
        if not existing.is_symlink():
            continue
        expected = expected_links.get(existing.name)
        if expected is None or existing.resolve(strict=False) != expected.resolve(strict=False):
            existing.unlink()

    for name, image in expected_links.items():
        target = workspace / name
        if target.is_symlink():
            continue
        if target.exists():
            raise Pcsx2RuntimeError(
                f"Refusing non-symlink PCSX2 BIOS image in workspace: {target}"
            )
        target.symlink_to(image)

    # NVM/MEC files are mutable console state.  Seed an isolated copy once if
    # the user's BIOS pack contains one, then let PCSX2 update only that copy.
    for companion in source.iterdir():
        if (
            not companion.is_file()
            or companion.suffix.casefold() not in _BIOS_COMPANION_SUFFIXES
            or not os.access(companion, os.R_OK)
        ):
            continue
        target = workspace / companion.name
        if target.is_symlink():
            raise Pcsx2RuntimeError(
                f"Refusing symlink PCSX2 BIOS companion in workspace: {target}"
            )
        if not target.exists():
            shutil.copyfile(companion, target)

    return workspace


def _section_path(
    config: Mapping[str, Any],
    key: str,
    environment: Mapping[str, str],
    environment_name: str,
    default: Path,
) -> Path:
    section = config.get("pcsx2", {})
    if not isinstance(section, Mapping):
        raise Pcsx2RuntimeError("[pcsx2] must be a TOML table")
    value = section.get(key, environment.get(environment_name, default))
    if not isinstance(value, (str, os.PathLike)):
        raise Pcsx2RuntimeError(f"[pcsx2].{key} must be a path string")
    return Path(value).expanduser().absolute()


def _resources_complete(resources_dir: Path) -> bool:
    required = (resources_dir / "GameIndex.yaml", resources_dir / "patches.zip")
    return all(path.is_file() and os.access(path, os.R_OK) for path in required)


def _resolve_resources_dir(
    config: Mapping[str, Any], environment: Mapping[str, str]
) -> Path:
    section = config.get("pcsx2", {})
    if not isinstance(section, Mapping):
        raise Pcsx2RuntimeError("[pcsx2] must be a TOML table")

    explicit = section.get("resources", environment.get("EMBERCADE_PCSX2_RESOURCES_SOURCE"))
    if explicit is not None:
        if not isinstance(explicit, (str, os.PathLike)):
            raise Pcsx2RuntimeError("[pcsx2].resources must be a path string")
        return Path(explicit).expanduser().absolute()

    for candidate in _DEFAULT_RESOURCE_CANDIDATES:
        if _resources_complete(candidate):
            return candidate
    return _DEFAULT_RESOURCE_CANDIDATES[0]


def resolve_pcsx2_runtime(
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
) -> Pcsx2Runtime:
    """Resolve existing read-only firmware and host resources for PCSX2."""
    bios_source = _section_path(
        config,
        "bios",
        environment,
        "EMBERCADE_PCSX2_BIOS_SOURCE",
        paths.bios_root / "ps2",
    )
    if not bios_source.is_dir() or not os.access(bios_source, os.R_OK | os.X_OK):
        raise Pcsx2RuntimeError(f"PCSX2 BIOS directory is not readable: {bios_source}")
    bios_dir = _prepare_bios_workspace(paths, bios_source)

    resources_dir = _resolve_resources_dir(config, environment)
    required_resources = (resources_dir / "GameIndex.yaml", resources_dir / "patches.zip")
    missing = [path for path in required_resources if not path.is_file() or not os.access(path, os.R_OK)]
    if missing:
        detail = ", ".join(map(str, missing))
        raise Pcsx2RuntimeError(f"PCSX2 host resources are incomplete: {detail}")
    return Pcsx2Runtime(bios_dir=bios_dir, resources_dir=resources_dir)


def pcsx2_writable_directories(paths: EmbercadePaths) -> tuple[Path, ...]:
    config_dir = paths.emulator_configs / "PCSX2"
    save_dir = paths.saves / "ps2" / "pcsx2"
    return (
        config_dir / "inis",
        config_dir / "inputprofiles",
        config_dir / "patches",
        config_dir / "resources",
        config_dir / "textures",
        config_dir / "debuggerlayouts",
        config_dir / "debuggersettings",
        save_dir / "memcards",
        save_dir / "sstates",
        save_dir / "videos",
        paths.isolated_bios / "ps2",
        paths.cache / "ps2",
        paths.logs / "pcsx2",
        paths.screenshots,
    )

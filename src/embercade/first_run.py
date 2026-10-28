"""Small, testable bridge from the graphical first run to existing CLI backends.

The CLI remains the owner of configuration, imports, Doctor, host bootstrap and
Steam registration.  This module only prepares argv and reads current state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
import os
import subprocess
import sys

from embercade.exit_hotkey import DEFAULT_EXIT_HOTKEY, resolve_exit_hotkey
from embercade.paths import EmbercadePaths
from embercade.ppsspp import PpssppAssetsError, validate_ppsspp_assets
from embercade.runtime import load_config, emulator_provider_config
from embercade.setup_flow import SetupError, detect_xenia_edge, validate_collection_path
from embercade.xemu import XemuRuntimeError, isolated_xemu_files, xemu_source_environment
from embercade.imports import ImportError as ManagedImportError, inspect_provider
from embercade.installer_preferences import saved_language


class FirstRunError(RuntimeError):
    """A wizard action cannot be performed safely."""


@dataclass(frozen=True, slots=True)
class FirstRunState:
    config_path: Path
    roms: str
    bios: str
    exit_hotkey: str
    configured: bool
    ppsspp_assets: str = ""
    managed_cores: int = 0
    managed_xenia: bool = False
    xemu_prepared: bool = False
    shadps4: str = ""
    language: str | None = None


def read_state(config_path: Path, environment: Mapping[str, str] | None = None) -> FirstRunState:
    """Never create or repair files merely by opening the wizard."""
    try:
        config = load_config(config_path)
        paths = EmbercadePaths.from_environment(environment, config=config)
        hotkey = resolve_exit_hotkey(config).key
        providers = emulator_provider_config(config)
        shadps4 = providers.get("shadps4")
        libretro = config.get("libretro", {})
        if not isinstance(libretro, Mapping):
            raise ValueError("[libretro] must be a TOML table")
        ppsspp_assets = libretro.get("ppsspp_assets", "")
        if not isinstance(ppsspp_assets, str):
            raise ValueError("[libretro].ppsspp_assets must be a path string")
    except (OSError, ValueError) as error:
        raise FirstRunError(f"Existing settings need attention: {error}") from error
    managed_cores = sum(path.is_file() for path in (paths.data / "cores").glob("*_libretro.so"))
    try:
        xenia = detect_xenia_edge(config, environment)
    except SetupError:
        xenia = None
    managed_xenia = bool(xenia and xenia.is_relative_to(paths.data / "providers"))
    xemu = isolated_xemu_files(paths)
    xemu_prepared = all(path.is_file() for path in (xemu.flashrom, xemu.bootrom, xemu.hdd))
    return FirstRunState(
        config_path=config_path,
        roms=str(paths.roms) if paths.roms_configured else "",
        bios=str(paths.bios) if paths.bios_configured else "",
        exit_hotkey=hotkey or DEFAULT_EXIT_HOTKEY,
        configured=all(item.ok for item in paths.validate_collection_roots()),
        ppsspp_assets=ppsspp_assets,
        managed_cores=managed_cores,
        managed_xenia=managed_xenia,
        xemu_prepared=xemu_prepared,
        shadps4=shadps4.executable or "" if shadps4 else "",
        language=saved_language(config),
    )


def launcher_command(environment: Mapping[str, str] | None = None) -> tuple[str, ...]:
    env = os.environ if environment is None else environment
    prefix = env.get("EMBERCADE_PREFIX")
    if prefix:
        launcher = Path(prefix).expanduser().absolute() / "bin" / "embercade"
        if not launcher.is_file():
            raise FirstRunError(f"Installed Embercade launcher is missing: {launcher}")
        return (str(launcher),)
    return (sys.executable, "-B", "-m", "embercade")


def branding_icon(environment: Mapping[str, str] | None = None) -> Path | None:
    env = os.environ if environment is None else environment
    root = Path(env.get("EMBERCADE_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
    icon = root / "resources" / "branding" / "icon" / "embercade-256.png"
    return icon if icon.is_file() else None


def setup_arguments(
    config_path: Path,
    *,
    roms: str,
    bios: str,
    exit_hotkey: str,
    cores_from: str = "",
    providers_from: str = "",
    ppsspp_assets_from: str = "",
    xemu_files_from: str = "",
    shadps4_from: str = "",
) -> tuple[str, ...]:
    try:
        rom_root = validate_collection_path(roms, "ROM")
        bios_root = validate_collection_path(bios, "BIOS")
        core_root = validate_collection_path(cores_from, "RetroArch core source") if cores_from.strip() else None
        provider_root = validate_collection_path(providers_from, "AppImage source") if providers_from.strip() else None
        ppsspp_root = validate_collection_path(ppsspp_assets_from, "PSP assets") if ppsspp_assets_from.strip() else None
        xemu_root = validate_collection_path(xemu_files_from, "Xbox system files") if xemu_files_from.strip() else None
    except SetupError as error:
        raise FirstRunError(str(error)) from error
    if exit_hotkey not in {"back-start", "guide-start"}:
        raise FirstRunError("Choose a supported controller exit shortcut")
    validate_asset_sources(ppsspp_root, xemu_root)
    shadps4 = None
    if shadps4_from.strip():
        try:
            shadps4 = inspect_provider(Path(shadps4_from), provider="shadps4")
        except ManagedImportError as error:
            raise FirstRunError(f"shadPS4-AppImage: {error}") from error
    arguments = [
        "--config", str(config_path), "setup", "--roms", str(rom_root),
        "--bios", str(bios_root), "--exit-hotkey", exit_hotkey,
    ]
    if core_root is not None:
        arguments.extend(("--cores-from", str(core_root)))
    if provider_root is not None:
        arguments.extend(("--providers-from", str(provider_root)))
    if ppsspp_root is not None:
        arguments.extend(("--ppsspp-assets-from", str(ppsspp_root)))
    if xemu_root is not None:
        arguments.extend(("--xemu-files-from", str(xemu_root)))
    if shadps4 is not None:
        arguments.extend(("--shadps4-from", str(shadps4)))
    return tuple(arguments)


def validate_asset_sources(ppsspp_root: Path | None, xemu_root: Path | None) -> None:
    """Reuse the runtime validators before advancing past the asset page."""
    try:
        if ppsspp_root is not None:
            validate_ppsspp_assets(ppsspp_root)
        if xemu_root is not None:
            xemu_source_environment(xemu_root)
    except (PpssppAssetsError, XemuRuntimeError) as error:
        raise FirstRunError(str(error)) from error


def action_arguments(config_path: Path, action: str) -> tuple[str, ...]:
    actions = {
        "doctor": ("doctor",),
        "bootstrap-plan": ("bootstrap", "--dry-run"),
        "bootstrap": ("bootstrap",),
        "steam-plan": ("steam", "--dry-run"),
        "steam": ("steam", "--yes"),
        "start": ("start",),
    }
    if action not in actions:
        raise FirstRunError(f"Unknown wizard action: {action}")
    return ("--config", str(config_path), *actions[action])


def run_action(
    command: Sequence[str], arguments: Sequence[str],
    *, environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Use an argv vector, not a shell, for paths containing spaces or punctuation."""
    return subprocess.run(
        [*command, *arguments], env=None if environment is None else dict(environment),
        stdin=subprocess.DEVNULL, text=True, capture_output=True, check=False,
    )


def friendly_failure(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line.strip() for line in (result.stderr + "\n" + result.stdout).splitlines() if line.strip()]
    for line in reversed(lines):
        if "error:" in line.lower():
            return line.split("error:", 1)[-1].strip()
    return lines[-1] if lines else "Embercade could not complete this step. Your existing files were kept."

"""Execute and verify config-generating Libretro dry runs without starting RetroArch."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import os
import re
import shlex
import subprocess

from embercade.bios_inventory import BATOCERA_COMMIT, inspect_opera_bios
from embercade.launcher import LaunchPlan, SIMPLE_LIBRETRO_SYSTEMS
from embercade.paths import EmbercadePaths


class LibretroDryRunError(RuntimeError):
    """A dry run did not prove the expected isolated Libretro path."""


_SETTING = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*"?([^"\r\n]*)"?\s*$')
_PLAYER_ONE_ARGUMENTS = (
    "-p1index",
    "-p1guid",
    "-p1name",
    "-p1devicepath",
    "-p1nbbuttons",
    "-p1nbhats",
    "-p1nbaxes",
)

# Core metadata can require data below RetroArch's system directory even when
# Batocera's standalone default has no BIOS declaration. Keep these checks
# data-driven and limited to resources the selected Libretro core marks as
# mandatory.
_REQUIRED_SYSTEM_RESOURCES: Mapping[str, tuple[tuple[str, str], ...]] = {
    "psp": (
        ("file", "PPSSPP/ppge_atlas.zim"),
        ("directory", "PPSSPP/lang"),
        ("directory", "PPSSPP/flash0"),
    ),
}


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.absolute().relative_to(root.absolute())
    except ValueError:
        return False
    return True


def _settings(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if match := _SETTING.match(line):
            result[match.group(1)] = match.group(2).strip()
    return result


def expected_system_directory(system: str, paths: EmbercadePaths) -> Path:
    """Return the Batocera core-specific firmware directory for a dry run."""
    if system in {"amiga500", "amiga1200", "amigacd32", "amigacdtv"}:
        return paths.bios_root / "amiga"
    if system == "psp":
        return paths.isolated_bios / "psp"
    return paths.bios_root


def required_system_resources(system: str, paths: EmbercadePaths) -> tuple[Path, ...]:
    """Validate mandatory core data without mutating the read-only BIOS root."""
    system_directory = expected_system_directory(system, paths)
    if system == "3do":
        firmware = inspect_opera_bios(system_directory)
        if not firmware.available:
            raise LibretroDryRunError(f"3DO BIOS {firmware.status}: {firmware.detail}")
        return firmware.files
    resolved: list[Path] = []
    for kind, relative in _REQUIRED_SYSTEM_RESOURCES.get(system, ()):
        path = system_directory / relative
        available = path.is_file() if kind == "file" else path.is_dir()
        if not available or not os.access(path, os.R_OK):
            raise LibretroDryRunError(
                f"{system}: required {kind} is unavailable below system_directory: {relative}"
            )
        resolved.append(path)
    return tuple(resolved)


def snapshot_metadata(root: Path) -> dict[str, tuple[int, int, int]]:
    """Read a shallow proof of host-profile immutability without file contents."""
    if not root.exists():
        return {}
    result: dict[str, tuple[int, int, int]] = {}
    for path in sorted(root.rglob("*")):
        try:
            stat = path.lstat()
        except OSError:
            continue
        result[str(path.relative_to(root))] = (stat.st_mode, stat.st_size, stat.st_mtime_ns)
    return result


def execute_dry_run(plan: LaunchPlan, paths: EmbercadePaths) -> dict[str, Any]:
    if not plan.dry_run or plan.system not in SIMPLE_LIBRETRO_SYSTEMS:
        raise LibretroDryRunError("plan is not a supported Libretro dry run")
    if plan.emulator != "libretro" or plan.core is None or plan.core_name is None:
        raise LibretroDryRunError("plan has no resolved Libretro core")
    controller_complete = plan.controller is not None and all(
        argument in plan.command for argument in _PLAYER_ONE_ARGUMENTS
    )
    if not controller_complete:
        raise LibretroDryRunError(f"{plan.system}: player-one controller arguments are incomplete")
    try:
        completed = subprocess.run(
            plan.command,
            env=dict(plan.environment),
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LibretroDryRunError(f"{plan.system}: launcher dry run failed: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise LibretroDryRunError(f"{plan.system}: launcher dry run failed: {detail}")

    prefix = "EMBERCADE_FINAL_COMMAND="
    command_lines = [line[len(prefix):] for line in completed.stdout.splitlines() if line.startswith(prefix)]
    if len(command_lines) != 1:
        raise LibretroDryRunError(f"{plan.system}: launcher emitted no unique final command")
    try:
        final_command = shlex.split(command_lines[0])
    except ValueError as error:
        raise LibretroDryRunError(f"{plan.system}: final command is not shell-parseable") from error
    if not final_command or Path(final_command[0]) != plan.executable:
        raise LibretroDryRunError(f"{plan.system}: final command does not use resolved RetroArch")
    if final_command.count(str(plan.rom)) != 1:
        raise LibretroDryRunError(f"{plan.system}: ROM is not one exact final-command argument")
    try:
        core_index = final_command.index("-L") + 1
        config_index = final_command.index("--config") + 1
        final_core = Path(final_command[core_index])
        retroarch_config = Path(final_command[config_index])
    except (ValueError, IndexError) as error:
        raise LibretroDryRunError(f"{plan.system}: final RetroArch command lacks core/config") from error
    if final_core != plan.core or not final_core.is_file():
        raise LibretroDryRunError(f"{plan.system}: final command core differs from resolver output")
    if not retroarch_config.is_file() or not _is_within(retroarch_config, paths.emulator_configs):
        raise LibretroDryRunError(f"{plan.system}: RetroArch config is outside Embercade")

    config = _settings(retroarch_config)
    system_directory = expected_system_directory(plan.system, paths)
    if config.get("system_directory") != str(system_directory):
        raise LibretroDryRunError(
            f"{plan.system}: RetroArch system_directory is not the expected BIOS path"
        )
    system_resources = required_system_resources(plan.system, paths)
    isolated_directories: dict[str, Path] = {}
    for setting, root in (
        ("savefile_directory", paths.saves),
        ("savestate_directory", paths.saves),
        ("cache_directory", paths.config),
    ):
        configured = config.get(setting)
        if not configured:
            raise LibretroDryRunError(f"{plan.system}: RetroArch {setting} is missing")
        directory = Path(configured)
        if not _is_within(directory, root):
            raise LibretroDryRunError(
                f"{plan.system}: RetroArch {setting} is outside Embercade"
            )
        isolated_directories[setting] = directory
    shader = None
    if "--set-shader" in final_command:
        try:
            shader = Path(final_command[final_command.index("--set-shader") + 1])
        except IndexError as error:
            raise LibretroDryRunError(f"{plan.system}: shader argument is incomplete") from error
        if not shader.is_file():
            raise LibretroDryRunError(f"{plan.system}: selected shader is unavailable: {shader}")

    overlay_enabled = config.get("input_overlay_enable", "false").casefold() == "true"
    overlay = Path(config["input_overlay"]) if config.get("input_overlay") else None
    if overlay_enabled and (overlay is None or not overlay.is_file()):
        raise LibretroDryRunError(f"{plan.system}: enabled overlay is unavailable")

    return {
        "system": plan.system,
        "emulator": plan.emulator,
        "core": plan.core_name,
        "core_path": str(plan.core),
        "rom": str(plan.rom),
        "bios_root": str(paths.bios_root),
        "system_directory": str(system_directory),
        "required_system_resources": [str(path) for path in system_resources],
        "controller_arguments_complete": controller_complete,
        "final_command": final_command,
        "retroarch_config": str(retroarch_config),
        "retroarch_config_sha256": sha256(retroarch_config.read_bytes()).hexdigest(),
        "savefile_directory": str(isolated_directories["savefile_directory"]),
        "savestate_directory": str(isolated_directories["savestate_directory"]),
        "cache_directory": str(isolated_directories["cache_directory"]),
        "memory_card_directory": str(isolated_directories["savefile_directory"]),
        "shader": str(shader) if shader else None,
        "overlay_enabled": overlay_enabled,
        "overlay": str(overlay) if overlay else None,
        "launcher_exit_code": completed.returncode,
    }


def build_report(
    rows: Iterable[Mapping[str, Any]],
    *,
    host_profile_unchanged: bool,
) -> dict[str, Any]:
    systems = sorted((dict(row) for row in rows), key=lambda row: str(row["system"]))
    return {
        "schema_version": 1,
        "batocera_commit": BATOCERA_COMMIT,
        "mode": "config-generating dry run; RetroArch not started",
        "host_retroarch_profile_unchanged": host_profile_unchanged,
        "summary": {
            "systems": len(systems),
            "successful": sum(row.get("launcher_exit_code") == 0 for row in systems),
        },
        "systems": systems,
    }


def write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

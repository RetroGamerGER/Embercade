"""Verify an isolated Dolphin configuration run without starting Dolphin."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Any, Mapping
import json
import shlex
import subprocess

from embercade.bios_inventory import BATOCERA_COMMIT
from embercade.launcher import LaunchPlan
from embercade.paths import EmbercadePaths


class DolphinDryRunError(RuntimeError):
    """The Dolphin generator did not prove the expected desktop isolation."""


_PLAYER_ONE_ARGUMENTS = (
    "-p1index",
    "-p1guid",
    "-p1name",
    "-p1devicepath",
    "-p1nbbuttons",
    "-p1nbhats",
    "-p1nbaxes",
)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.absolute().relative_to(root.absolute())
    except ValueError:
        return False
    return True


def _read_ini(path: Path) -> ConfigParser:
    # Dolphin's controller format permits repeated binding keys.
    parser = ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    if not path.is_file():
        raise DolphinDryRunError(f"Dolphin config was not generated: {path}")
    # Dolphin controller files are emitted with a UTF-8 BOM.
    parser.read(path, encoding="utf-8-sig")
    return parser


def execute_dry_run(plan: LaunchPlan, paths: EmbercadePaths) -> dict[str, Any]:
    """Run only Dolphin's generator and validate its final command and paths."""
    if not plan.dry_run or plan.system != "wii" or plan.emulator != "dolphin":
        raise DolphinDryRunError("plan is not a Wii Dolphin dry run")
    if plan.controller is None or not all(argument in plan.command for argument in _PLAYER_ONE_ARGUMENTS):
        raise DolphinDryRunError("Wii player-one controller arguments are incomplete")

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
        raise DolphinDryRunError(f"Wii Dolphin dry run failed: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise DolphinDryRunError(f"Wii Dolphin dry run failed: {detail}")

    prefix = "EMBERCADE_FINAL_COMMAND="
    command_lines = [
        line[len(prefix):]
        for line in completed.stdout.splitlines()
        if line.startswith(prefix)
    ]
    if len(command_lines) != 1:
        raise DolphinDryRunError("Wii Dolphin dry run emitted no unique final command")
    try:
        final_command = shlex.split(command_lines[0])
    except ValueError as error:
        raise DolphinDryRunError("Wii Dolphin final command is not shell-parseable") from error
    if not final_command or Path(final_command[0]) != plan.executable:
        raise DolphinDryRunError("Wii Dolphin final command does not use the resolved host binary")
    if final_command.count(str(plan.rom)) != 1 or "-b" not in final_command or "-e" not in final_command:
        raise DolphinDryRunError("Wii Dolphin final command does not preserve batch/ROM arguments")

    config_root = paths.emulator_configs / "dolphin-emu"
    dolphin_ini = _read_ini(config_root / "Dolphin.ini")
    gfx_ini = _read_ini(config_root / "GFX.ini")
    _read_ini(config_root / "Qt.ini")
    _read_ini(config_root / "Hotkeys.ini")
    wiimote_ini = _read_ini(config_root / "WiimoteNew.ini")

    for value, root, label in (
        (plan.environment.get("XDG_CONFIG_HOME"), paths.config, "XDG config"),
        (plan.environment.get("XDG_DATA_HOME"), paths.data, "XDG data"),
        (plan.environment.get("XDG_CACHE_HOME"), paths.cache, "XDG cache"),
    ):
        if not value or not _is_within(Path(value), root):
            raise DolphinDryRunError(f"Wii Dolphin {label} path is outside Embercade")

    expected_iso_paths = {str(paths.rom_root / "wii"), str(paths.rom_root / "gamecube")}
    actual_iso_paths = {
        dolphin_ini.get("General", "ISOPath0", fallback=""),
        dolphin_ini.get("General", "ISOPath1", fallback=""),
    }
    if actual_iso_paths != expected_iso_paths:
        raise DolphinDryRunError("Wii Dolphin game-library paths do not use ROM_ROOT")
    if dolphin_ini.get("DSP", "Backend", fallback="") != "Cubeb":
        raise DolphinDryRunError("Wii Dolphin audio backend is not Batocera's Cubeb default")
    renderer = dolphin_ini.get("Core", "GFXBackend", fallback="")
    if renderer not in {"OGL", "Vulkan"}:
        raise DolphinDryRunError("Wii Dolphin renderer is neither OpenGL nor Vulkan")
    if dolphin_ini.get("Core", "WiimoteContinuousScanning", fallback="").casefold() != "true":
        raise DolphinDryRunError("Wii Dolphin continuous controller scanning is disabled")
    real_mode = wiimote_ini.get("Wiimote1", "Source", fallback="") == "2"
    if not real_mode and (not wiimote_ini.sections() or not any(
        plan.controller.real_name in value
        for section in wiimote_ini.sections()
        for _, value in wiimote_ini.items(section)
    )):
        raise DolphinDryRunError("Wii Dolphin emulated-Wiimote config lacks the live controller")

    save_root = paths.saves / "dolphin-emu"
    nand_root = save_root / "Wii"
    generated_files = sorted(str(path) for path in config_root.glob("*.ini"))
    if not generated_files or not all(_is_within(Path(path), paths.emulator_configs) for path in generated_files):
        raise DolphinDryRunError("Wii Dolphin generated config escaped Embercade")

    return {
        "system": "wii",
        "emulator": "dolphin",
        "rom": str(plan.rom),
        "host_binary": str(plan.executable),
        "final_command": final_command,
        "controller_arguments_complete": True,
        "controller_config": str(config_root / "WiimoteNew.ini"),
        "config_root": str(config_root),
        "generated_configs": generated_files,
        "save_root": str(save_root),
        "nand_root": str(nand_root),
        "cache_root": str(paths.cache),
        "renderer": renderer,
        "audio_backend": "Cubeb",
        "wiimote_mode": "real" if real_mode else "emulated",
        "extension_handling": "native Dolphin" if real_mode else "Batocera mapping",
        "launcher_exit_code": completed.returncode,
        "special_controller_validation": "PENDING",
    }


def build_report(row: Mapping[str, Any], *, host_profiles_unchanged: bool) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "batocera_commit": BATOCERA_COMMIT,
        "mode": "config-generating Dolphin dry run; Dolphin not started",
        "host_profiles_unchanged": host_profiles_unchanged,
        "systems": [dict(row)],
    }


def write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

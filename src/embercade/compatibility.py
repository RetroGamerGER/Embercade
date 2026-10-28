"""Build the host-specific Embercade 0.1 compatibility matrix without launching games."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import shutil

from embercade.bios_inventory import BATOCERA_COMMIT
from embercade.executables import (
    EmulatorProvider,
    ExecutableResolutionError,
    ExecutableResolver,
    SUPPORTED_EXECUTABLES,
)
from embercade.launcher import SIMPLE_LIBRETRO_SYSTEMS, SUPPORTED_LAUNCH_SYSTEMS


ROM_RELEVANT = frozenset({"ROM_PRESENT", "SPECIAL_LAYOUT_PRESENT"})
RESULT_STATUSES = (
    "READY",
    "UNTESTED",
    "CORE_MISSING",
    "EMULATOR_MISSING",
    "EMBERCADE_PORT_MISSING",
    "BIOS_MISSING",
    "AMBIGUOUS",
    "UNSUPPORTED",
)

# These names follow the commands used by the pinned Batocera 44 generators,
# with common desktop-distribution spellings included as fallbacks. Resolution
# is deliberately restricted to PATH; no emulator is executed.
EXECUTABLE_CANDIDATES: Mapping[str, tuple[str, ...]] = {
    "libretro": ("retroarch",),
    "azahar": ("azahar",),
    "bigpemu": ("bigpemu",),
    "cemu": ("cemu", "Cemu"),
    "dolphin": ("dolphin-emu",),
    "mupen64plus": ("mupen64plus",),
    "odcommander": ("od-commander",),
    "pcsx2": ("pcsx2-qt",),
    "ppsspp": ("PPSSPP", "PPSSPPQt", "PPSSPPSDL", "ppsspp"),
    "pygame": ("pygame",),
    "rpcs3": ("rpcs3",),
    "sdlpop": ("SDLPoP", "sdlpop"),
    "sh": ("sh",),
    "vita3k": ("Vita3K", "vita3k"),
    "xemu": ("xemu",),
    "xenia-edge": ("xenia_edge", "xenia-edge"),
    "shadps4": (),  # managed/configured AppImage only; no PATH fallback
}

# This is an explicit project capability ledger, not an inference from an
# installed binary. Each route exists in create_launch_plan and its supporting
# runtime code. NES intentionally uses Nestopia although Batocera's catalog
# default in the ROM inventory is FCEUmm.
_GENERIC_LIBRETRO_LAUNCH_PATHS: dict[str, Mapping[str, str | None]] = {
    system: {
        "route": "Batocera config -> Embercade core resolver -> configgen/libretro -> RetroArch",
        "effective_emulator": "libretro",
        "effective_core": None,
    }
    for system in SIMPLE_LIBRETRO_SYSTEMS
}
# The route is generic now, but the historic successful NES E2E used the
# explicit batocera.conf override to Nestopia. Retain that evidence detail.
_GENERIC_LIBRETRO_LAUNCH_PATHS["nes"] = {
    "route": "Batocera config -> Embercade core resolver -> configgen/libretro -> RetroArch",
    "effective_emulator": "libretro",
    "effective_core": "nestopia",
}
# The confirmed PSX route uses Batocera's mednafen_psx identity, resolved to
# the desktop distribution's hardware-capable mednafen_psx_hw binary.
_GENERIC_LIBRETRO_LAUNCH_PATHS["psx"] = {
    "route": "Batocera config -> Embercade core resolver -> configgen/libretro -> RetroArch",
    "effective_emulator": "libretro",
    "effective_core": "mednafen_psx",
}
# Batocera 44 defaults to melonDS. The installed melonDS library requests an
# executable stack and is rejected by this host's loader; the proven desktop
# route therefore uses Batocera's melonDS DS identity via batocera.conf.
_GENERIC_LIBRETRO_LAUNCH_PATHS["nds"] = {
    "route": "Batocera config -> Embercade core resolver -> configgen/libretro -> RetroArch",
    "effective_emulator": "libretro",
    "effective_core": "melondsds",
}
# Batocera keeps native standalone providers as its catalog defaults. These
# host-specific desktop routes retain those defaults in the matrix while using
# an installed Libretro provider selected through batocera.conf.
for _system, _core in (
    ("psp", "ppsspp"),
    ("3ds", "azahar"),
    ("n64", "mupen64plus-next"),
    ("jaguar", "virtualjaguar"),
    ("wiiu", "cemu"),
):
    _GENERIC_LIBRETRO_LAUNCH_PATHS[_system] = {
        "route": "Batocera config -> Embercade desktop provider override -> configgen/libretro -> RetroArch",
        "effective_emulator": "libretro",
        "effective_core": _core,
    }

IMPLEMENTED_LAUNCH_PATHS: Mapping[str, Mapping[str, str | None]] = {
    **_GENERIC_LIBRETRO_LAUNCH_PATHS,
    "gamecube": {
        "route": "batocera-launch -> batocera-launch-dolphin -> dolphin-emu",
        "effective_emulator": "dolphin",
        "effective_core": None,
    },
    "wii": {
        "route": "batocera-launch -> batocera-launch-dolphin -> dolphin-emu",
        "effective_emulator": "dolphin",
        "effective_core": None,
    },
    "ps2": {
        "route": "batocera-launch -> batocera-launch-pcsx2 -> pcsx2-qt",
        "effective_emulator": "pcsx2",
        "effective_core": None,
    },
    "ps3": {
        "route": "batocera-launch -> batocera-launch-rpcs3 -> rpcs3",
        "effective_emulator": "rpcs3",
        "effective_core": None,
    },
    "xbox": {
        "route": "batocera-launch -> Xemu generator -> xemu",
        "effective_emulator": "xemu",
        "effective_core": None,
    },
    "xbox360": {
        "route": "batocera-launch -> Xenia Edge generator -> external AppImage provider",
        "effective_emulator": "xenia-edge",
        "effective_core": None,
    },
    "ps4": {
        "route": "batocera-launch -> pinned Shadps4 generator -> user-supplied AppImage",
        "effective_emulator": "shadps4",
        "effective_core": None,
    },
}

LAUNCH_CAPABILITIES: Mapping[str, Mapping[str, str]] = {
    "wii": {
        "launch_path": "READY",
        "special_controller_validation": "DOLPHINBAR_NUNCHUK_VALIDATED",
        "note": (
            "Garuda and interactive Steam/Gamescope Super Mario Galaxy E2E validate "
            "RVL-003, DolphinBar mode 4, "
            "Nunchuk, IR, motion, rumble, wireless reconnect and gamepad exit. "
            "MotionPlus, direct Bluetooth, passthrough and multiple remotes "
            "remain unvalidated; Dolphin Libretro is not an implemented route."
        ),
    }
}

# These manual end-to-end acceptance tests were explicitly confirmed for
# Embercade 0.1 and targeted 1.0 additions. No system becomes READY because its binary or
# core happens to be installed.
E2E_VALIDATED_SYSTEMS = frozenset(
    {
        "3do",
        "3ds",
        "amiga1200",
        "amigacd32",
        "atari2600",
        "atari5200",
        "atari7800",
        "c64",
        "dreamcast",
        "dos",
        "gamecube",
        "gamegear",
        "gb",
        "gba",
        "gbc",
        "jaguar",
        "mastersystem",
        "mame",
        "megacd",
        "megadrive",
        "mrboom",
        "neogeo",
        "neogeocd",
        "nes",
        "n64",
        "nds",
        "ngpc",
        "pcengine",
        "pcenginecd",
        "prboom",
        "ps2",
        "ps3",
        "ps4",
        "psp",
        "psx",
        "saturn",
        "sega32x",
        "snes",
        "wii",
        "wiiu",
        "xbox",
        "xbox360",
    }
)

# A Batocera "ports" collection dispatches arbitrary per-game shell launchers;
# finding /bin/sh does not establish a meaningful generic desktop launch path.
UNSUPPORTED_SYSTEMS = frozenset({"ports"})

# Conservative prioritization only: these cartridge/simple-content Libretro
# routes are closest to the proven NES path. More complex systems remain
# EMBERCADE_PORT_MISSING but are not described as small until their runtime,
# media-layout and input requirements have been audited.
LIKELY_SMALL_PORT_SYSTEMS = frozenset(
    {
        "atari2600",
        "atari5200",
        "atari7800",
        "gamegear",
        "gb",
        "gba",
        "gbc",
        "mastersystem",
        "megadrive",
        "mrboom",
        "neogeo",
        "ngpc",
        "pcengine",
        "prboom",
        "sega32x",
        "snes",
    }
)


class CompatibilityError(RuntimeError):
    """An inventory is inconsistent or insufficient for a safe matrix."""


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CompatibilityError(f"{label} must be a JSON object")
    return value


def _require_sequence(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise CompatibilityError(f"{label} must be a JSON array")
    return value


def _check_pin(inventory: Mapping[str, Any], label: str) -> None:
    actual = inventory.get("batocera_commit")
    if actual != BATOCERA_COMMIT:
        raise CompatibilityError(
            f"{label} Batocera commit is {actual!r}, expected {BATOCERA_COMMIT}"
        )


def _bios_status(row: Mapping[str, Any] | None) -> tuple[str, dict[str, int]]:
    if row is None:
        return "UNKNOWN", {
            "requirements": 0,
            "matched": 0,
            "missing": 0,
            "mismatches": 0,
            "case_or_path_errors": 0,
            "unknown": 1,
        }
    total = int(row.get("requirements_total", 0))
    matched = int(row.get("required_matched", 0))
    missing = int(row.get("required_missing", 0))
    mismatches = int(row.get("hash_mismatches", 0))
    path_errors = int(row.get("case_mismatches", 0)) + int(row.get("wrong_location", 0))
    unknown = int(row.get("unknown_requirements", 0))
    counts = {
        "requirements": total,
        "matched": matched,
        "missing": missing,
        "mismatches": mismatches,
        "case_or_path_errors": path_errors,
        "unknown": unknown,
    }
    if total == 0:
        return "NOT_REQUIRED", counts
    if missing or mismatches or path_errors or unknown or matched < total:
        return "MISSING", counts
    return "SATISFIED", counts


def _resolve_executable(
    emulator: str,
    candidates: Mapping[str, tuple[str, ...]],
    environment: Mapping[str, str],
) -> dict[str, Any]:
    commands = candidates.get(emulator)
    if commands is None:
        return {
            "applicable": True,
            "known": False,
            "present": None,
            "candidates": [],
            "command": None,
            "path": None,
        }
    search_path = environment.get("PATH")
    for command in commands:
        if path := shutil.which(command, path=search_path):
            return {
                "applicable": True,
                "known": True,
                "present": True,
                "candidates": list(commands),
                "command": command,
                "path": str(Path(path).absolute()),
            }
    return {
        "applicable": True,
        "known": True,
        "present": False,
        "candidates": list(commands),
        "command": None,
        "path": None,
    }


def _resolve_effective_executable(
    emulator: str,
    candidates: Mapping[str, tuple[str, ...]],
    environment: Mapping[str, str],
    configured: Mapping[str, str],
    providers: Mapping[str, EmulatorProvider],
) -> dict[str, Any]:
    if emulator not in SUPPORTED_EXECUTABLES:
        return _resolve_executable(emulator, candidates, environment)
    resolver = ExecutableResolver(
        configured,
        providers=providers,
        environment=environment,
    )
    try:
        resolved = resolver.resolve(emulator)
    except ExecutableResolutionError as error:
        return {
            "applicable": True,
            "known": True,
            "present": False,
            "candidates": list(candidates.get(emulator, (SUPPORTED_EXECUTABLES[emulator],))),
            "command": None,
            "path": None,
            "provider": None,
            "error": str(error),
        }
    return {
        "applicable": True,
        "known": True,
        "present": True,
        "candidates": list(candidates.get(emulator, (SUPPORTED_EXECUTABLES[emulator],))),
        "command": resolved.path.name,
        "path": str(resolved.path),
        "provider": resolved.provider_type.value,
        "error": None,
    }


def _core_status(core: str, core_index: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    row = core_index.get(core)
    present = bool(row and row.get("path") and row.get("probably_loadable"))
    return {
        "applicable": True,
        "name": core,
        "present": present,
        "path": row.get("path") if row else None,
        "alias": row.get("alias") if row else None,
        "probably_loadable": bool(row and row.get("probably_loadable")),
    }


def _validated_dry_run_rows(
    report: Mapping[str, Any] | None,
) -> Mapping[str, Mapping[str, Any]]:
    if report is None:
        return {}
    _check_pin(report, "Libretro dry-run report")
    if report.get("host_retroarch_profile_unchanged") is not True:
        raise CompatibilityError("Libretro dry-run report does not prove host-profile immutability")
    rows = _require_sequence(report.get("systems"), "Libretro dry-run systems")
    validated: dict[str, Mapping[str, Any]] = {}
    for raw_row in rows:
        row = _require_mapping(raw_row, "Libretro dry-run row")
        system = row.get("system")
        if not isinstance(system, str) or system not in SIMPLE_LIBRETRO_SYSTEMS:
            raise CompatibilityError(f"invalid Libretro dry-run system: {system!r}")
        if system in validated:
            raise CompatibilityError(f"duplicate Libretro dry-run system: {system}")
        if (
            row.get("emulator") != "libretro"
            or row.get("launcher_exit_code") != 0
            or row.get("controller_arguments_complete") is not True
            or not isinstance(row.get("core"), str)
            or not row.get("core")
            or not isinstance(row.get("core_path"), str)
            or not row.get("core_path")
            or not isinstance(row.get("retroarch_config"), str)
            or not row.get("retroarch_config")
        ):
            raise CompatibilityError(f"incomplete or unsuccessful Libretro dry run: {system}")
        validated[system] = row
    summary = _require_mapping(report.get("summary"), "Libretro dry-run summary")
    if summary.get("systems") != len(rows) or summary.get("successful") != len(rows):
        raise CompatibilityError("Libretro dry-run summary does not match its system rows")
    return validated


def _validated_dolphin_dry_run_rows(
    report: Mapping[str, Any] | None,
) -> Mapping[str, Mapping[str, Any]]:
    if report is None:
        return {}
    _check_pin(report, "Dolphin dry-run report")
    if report.get("host_profiles_unchanged") is not True:
        raise CompatibilityError("Dolphin dry-run report does not prove host-profile immutability")
    rows = _require_sequence(report.get("systems"), "Dolphin dry-run systems")
    validated: dict[str, Mapping[str, Any]] = {}
    for raw_row in rows:
        row = _require_mapping(raw_row, "Dolphin dry-run row")
        system = row.get("system")
        if system != "wii" or system in validated:
            raise CompatibilityError(f"invalid Dolphin dry-run system: {system!r}")
        if (
            row.get("emulator") != "dolphin"
            or row.get("launcher_exit_code") != 0
            or row.get("controller_arguments_complete") is not True
            or row.get("special_controller_validation") != "PENDING"
            or not isinstance(row.get("host_binary"), str)
            or not row.get("host_binary")
            or not isinstance(row.get("config_root"), str)
            or not row.get("config_root")
            or not isinstance(row.get("nand_root"), str)
            or not row.get("nand_root")
        ):
            raise CompatibilityError("incomplete or unsuccessful Wii Dolphin dry run")
        validated[system] = row
    return validated


def _result_status(
    *,
    system: str,
    ambiguous: bool,
    bios_status: str,
    default_emulator: str,
    default_core_status: Mapping[str, Any] | None,
    executable: Mapping[str, Any],
    effective_executable: Mapping[str, Any] | None,
    implemented: bool,
    route_validated: bool,
    effective_core_status: Mapping[str, Any] | None,
    e2e_tested: bool,
    unsupported_systems: frozenset[str],
) -> tuple[str, str]:
    if ambiguous:
        return "AMBIGUOUS", "collection rows disagree on the Batocera default emulator/core"
    if bios_status in {"MISSING", "UNKNOWN"}:
        return "BIOS_MISSING", "required BIOS/firmware is missing, invalid or unresolved"
    if system in unsupported_systems:
        return "UNSUPPORTED", "the Batocera route has no meaningful generic desktop equivalent"
    if implemented:
        if effective_executable is not None and effective_executable.get("present") is False:
            return "EMULATOR_MISSING", "Embercade's effective host emulator is not on PATH"
        if effective_executable is not None and effective_executable.get("known") is False:
            return "AMBIGUOUS", "no deterministic executable mapping exists for Embercade's route"
        if effective_core_status is not None and not effective_core_status["present"]:
            return "CORE_MISSING", "the core used by Embercade's implemented route is unavailable"
        if e2e_tested:
            return "READY", "prerequisites, Embercade route and manual end-to-end test are confirmed"
        if route_validated:
            return "UNTESTED", "the Embercade route passed an isolated dry run but lacks an end-to-end test"
        return "EMBERCADE_PORT_MISSING", "the route exists in code but lacks a successful isolated dry run"
    if default_emulator == "libretro" and not bool(default_core_status and default_core_status["present"]):
        return "CORE_MISSING", "the Batocera default Libretro core is unavailable"
    if executable.get("present") is False:
        return "EMULATOR_MISSING", "the Batocera default host emulator is not on PATH"
    if executable.get("known") is False:
        return "AMBIGUOUS", "no deterministic desktop executable mapping is available"
    return "EMBERCADE_PORT_MISSING", "host prerequisites exist but Embercade has no launch route"


def build_compatibility_matrix(
    rom_inventory: Mapping[str, Any],
    bios_inventory: Mapping[str, Any],
    core_inventory: Mapping[str, Any],
    *,
    libretro_dry_runs: Mapping[str, Any] | None = None,
    dolphin_dry_runs: Mapping[str, Any] | None = None,
    environment: Mapping[str, str] | None = None,
    configured_executables: Mapping[str, str] | None = None,
    emulator_providers: Mapping[str, EmulatorProvider] | None = None,
    executable_candidates: Mapping[str, tuple[str, ...]] = EXECUTABLE_CANDIDATES,
    launch_paths: Mapping[str, Mapping[str, str | None]] = IMPLEMENTED_LAUNCH_PATHS,
    e2e_systems: frozenset[str] = E2E_VALIDATED_SYSTEMS,
    unsupported_systems: frozenset[str] = UNSUPPORTED_SYSTEMS,
    likely_small_port_systems: frozenset[str] = LIKELY_SMALL_PORT_SYSTEMS,
) -> dict[str, Any]:
    """Combine existing inventories and PATH metadata; never execute an emulator."""
    _check_pin(rom_inventory, "ROM inventory")
    _check_pin(bios_inventory, "BIOS inventory")
    if set(launch_paths) != set(SUPPORTED_LAUNCH_SYSTEMS):
        raise CompatibilityError("launch capability ledger differs from Embercade's supported systems")
    if not e2e_systems.issubset(launch_paths):
        raise CompatibilityError("end-to-end ledger contains a system without an implemented route")
    dry_run_rows = _validated_dry_run_rows(libretro_dry_runs)
    dolphin_dry_run_rows = _validated_dolphin_dry_run_rows(dolphin_dry_runs)

    rom_rows = _require_sequence(rom_inventory.get("systems"), "ROM systems")
    relevant: dict[str, list[Mapping[str, Any]]] = {}
    for raw_row in rom_rows:
        row = _require_mapping(raw_row, "ROM system row")
        if row.get("content_status") not in ROM_RELEVANT:
            continue
        system = row.get("system")
        if not isinstance(system, str) or not system:
            raise CompatibilityError("ROM-relevant row has no Batocera system ID")
        relevant.setdefault(system, []).append(row)

    bios_rows = _require_sequence(bios_inventory.get("systems"), "BIOS systems")
    bios_index = {
        str(row["system"]): _require_mapping(row, "BIOS system row")
        for row in bios_rows
        if isinstance(row, Mapping) and "system" in row
    }
    core_rows = _require_sequence(core_inventory.get("batocera_cores"), "Batocera core rows")
    core_index = {
        str(row["batocera_name"]): _require_mapping(row, "core row")
        for row in core_rows
        if isinstance(row, Mapping) and "batocera_name" in row
    }
    installed_core_rows = _require_sequence(
        core_inventory.get("installed_cores", []), "installed core rows"
    )
    for raw_row in installed_core_rows:
        row = _require_mapping(raw_row, "installed core row")
        logical_name = row.get("logical_name")
        path = row.get("path")
        if not isinstance(logical_name, str) or not isinstance(path, str):
            continue
        core_index.setdefault(
            logical_name,
            {
                "batocera_name": logical_name,
                "path": path,
                "alias": None,
                "probably_loadable": Path(path).is_file(),
            },
        )
    env = os.environ if environment is None else environment
    configured = dict(configured_executables or {})
    providers = dict(emulator_providers or {})

    systems: list[dict[str, Any]] = []
    for system, collection_rows in sorted(relevant.items()):
        defaults = {
            (str(row.get("default_emulator", "")), str(row.get("default_core", "")))
            for row in collection_rows
        }
        ambiguous = len(defaults) != 1 or any(not emulator or not core for emulator, core in defaults)
        default_emulator, default_core = sorted(defaults)[0] if defaults else ("", "")
        collection_statuses = sorted({str(row["content_status"]) for row in collection_rows})
        collection_status = collection_statuses[0] if len(collection_statuses) == 1 else "AMBIGUOUS"

        firmware_status, firmware_counts = _bios_status(bios_index.get(system))
        default_core_result = (
            _core_status(default_core, core_index) if default_emulator == "libretro" else None
        )
        executable = _resolve_executable(default_emulator, executable_candidates, env)
        launch = launch_paths.get(system)
        dry_run = dry_run_rows.get(system)
        effective_emulator = (
            str(launch["effective_emulator"])
            if launch and launch.get("effective_emulator")
            else None
        )
        effective_core_name = (
            launch.get("effective_core") if launch and launch.get("effective_core") else None
        ) or (str(dry_run["core"]) if dry_run else None) or (
            default_core if effective_emulator == "libretro" else None
        )
        effective_core_result = (
            _core_status(str(effective_core_name), core_index) if effective_core_name else None
        )
        effective_executable = (
            _resolve_effective_executable(
                effective_emulator,
                executable_candidates,
                env,
                configured,
                providers,
            )
            if effective_emulator
            else None
        )
        if dry_run is not None and (
            effective_core_result is None
            or not effective_core_result["present"]
            or effective_core_result["path"] != dry_run["core_path"]
        ):
            raise CompatibilityError(
                f"Libretro dry-run core differs from the current core inventory: {system}"
            )
        implemented = launch is not None
        e2e_tested = system in e2e_systems
        route_validated = e2e_tested or system in dry_run_rows or system in dolphin_dry_run_rows
        status, reason = _result_status(
            system=system,
            ambiguous=ambiguous,
            bios_status=firmware_status,
            default_emulator=default_emulator,
            default_core_status=default_core_result,
            executable=executable,
            effective_executable=effective_executable,
            implemented=implemented,
            route_validated=route_validated,
            effective_core_status=effective_core_result,
            e2e_tested=e2e_tested,
            unsupported_systems=unsupported_systems,
        )
        systems.append(
            {
                "system": system,
                "fullname": str(collection_rows[0].get("fullname", system)),
                "collection_status": collection_status,
                "collections": [
                    {
                        "directory": str(row.get("directory", "")),
                        "match": str(row.get("match", "")),
                        "content_status": str(row.get("content_status", "")),
                    }
                    for row in sorted(collection_rows, key=lambda item: str(item.get("directory", "")))
                ],
                "default_emulator": default_emulator,
                "default_core": default_core,
                "bios": {"status": firmware_status, **firmware_counts},
                "host_core": default_core_result
                or {
                    "applicable": False,
                    "name": None,
                    "present": None,
                    "path": None,
                    "alias": None,
                    "probably_loadable": None,
                },
                "host_standalone_emulator": executable,
                "embercade_launch": {
                    "implemented": implemented,
                    "dry_run_validated": system in dry_run_rows or system in dolphin_dry_run_rows,
                    "route": launch.get("route") if launch else None,
                    "effective_emulator": launch.get("effective_emulator") if launch else None,
                    "effective_emulator_status": effective_executable,
                    "effective_core": effective_core_name,
                    "effective_core_status": effective_core_result,
                    "capabilities": dict(LAUNCH_CAPABILITIES.get(system, {})),
                },
                "e2e_tested": e2e_tested,
                "result_status": status,
                "reason": reason,
            }
        )

    counts = Counter(row["result_status"] for row in systems)
    missing_emulators: dict[str, list[str]] = {}
    missing_cores: dict[str, list[str]] = {}
    for row in systems:
        if row["result_status"] == "EMULATOR_MISSING":
            missing_emulators.setdefault(row["default_emulator"], []).append(row["system"])
        if row["result_status"] == "CORE_MISSING":
            core_name = row["default_core"]
            missing_cores.setdefault(core_name, []).append(row["system"])

    def ranked(values: Mapping[str, list[str]], key_name: str) -> list[dict[str, Any]]:
        return [
            {key_name: name, "systems": sorted(system_names), "system_count": len(system_names)}
            for name, system_names in sorted(
                values.items(), key=lambda item: (-len(item[1]), item[0])
            )
        ]

    return {
        "schema_version": 1,
        "batocera_commit": BATOCERA_COMMIT,
        "sources": {
            "rom_inventory": ".work/rom-inventory.json",
            "bios_inventory": ".work/bios-inventory.json",
            "core_inventory": ".work/core-inventory.json",
            "libretro_dry_runs": (
                ".work/libretro-dry-runs.json" if libretro_dry_runs is not None else None
            ),
            "dolphin_dry_runs": (
                ".work/dolphin-dry-runs.json" if dolphin_dry_runs is not None else None
            ),
            "host_executables": (
                "PATH plus configured native/explicit/AppImage provider metadata; "
                "no emulator executed"
            ),
        },
        "summary": {
            "rom_relevant_systems": len(systems),
            **{status.lower(): counts.get(status, 0) for status in RESULT_STATUSES},
        },
        "top_missing_standalone_emulators": ranked(missing_emulators, "emulator"),
        "top_missing_libretro_cores": ranked(missing_cores, "core"),
        "small_port_candidates": [
            row["system"]
            for row in systems
            if row["result_status"] == "EMBERCADE_PORT_MISSING"
            and row["system"] in likely_small_port_systems
        ],
        "e2e_proven_systems": [row["system"] for row in systems if row["e2e_tested"]],
        "systems": systems,
    }


def render_documentation(matrix: Mapping[str, Any]) -> str:
    summary = _require_mapping(matrix["summary"], "matrix summary")
    systems = _require_sequence(matrix["systems"], "matrix systems")
    lines = [
        "# Embercade 0.1 Compatibility Matrix",
        "",
        f"Batocera reference: `{matrix['batocera_commit']}`.",
        "",
        "This host snapshot combines the existing ROM, BIOS and Libretro-core inventories with "
        "PATH and configured external-provider discovery plus Embercade's explicit launch "
        "capability ledger. No emulator was started while generating this report. READY is "
        "reserved for manually confirmed end-to-end routes.",
        "",
        "Duplicate collection directories for the same Batocera system ID are combined into one "
        "row. Host paths and local collection-directory names remain in ignored reports and are "
        "deliberately omitted here.",
        "",
        "## Summary",
        "",
        f"- ROM-relevant systems: {summary['rom_relevant_systems']}",
    ]
    for status in RESULT_STATUSES:
        lines.append(f"- {status}: {summary[status.lower()]}")
    lines.extend(
        [
            "",
            "## Systems",
            "",
            "| System | Collection | Default emulator | Default core | BIOS | Host core | Host emulator | Embercade | Dry run | E2E | Result |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in systems:
        core = row["host_core"]
        host_core = "n/a" if not core["applicable"] else ("yes" if core["present"] else "no")
        emulator = row["host_standalone_emulator"]
        host_emulator = (
            "unknown" if emulator["present"] is None else ("yes" if emulator["present"] else "no")
        )
        lines.append(
            "| {system} | {collection} | {emulator} | {core_name} | {bios} | "
            "{host_core} | {host_emulator} | {implemented} | {dry_run} | {e2e} | **{result}** |".format(
                system=row["system"],
                collection=row["collection_status"],
                emulator=row["default_emulator"],
                core_name=row["default_core"],
                bios=row["bios"]["status"],
                host_core=host_core,
                host_emulator=host_emulator,
                implemented="yes" if row["embercade_launch"]["implemented"] else "no",
                dry_run="yes" if row["embercade_launch"]["dry_run_validated"] else "no",
                e2e="yes" if row["e2e_tested"] else "no",
                result=row["result_status"],
            )
        )

    controller_capabilities = [
        row for row in systems if row["embercade_launch"].get("capabilities")
    ]
    lines.extend(["", "## Controller capabilities", ""])
    if controller_capabilities:
        for row in controller_capabilities:
            capability = row["embercade_launch"]["capabilities"]
            lines.append(
                f"- `{row['system']}`: launch path **{capability['launch_path']}**; "
                f"special controller validation **{capability['special_controller_validation']}**. "
                f"{capability['note']}"
            )
    else:
        lines.append("None.")

    lines.extend(["", "## Missing standalone emulators", ""])
    missing_emulators = matrix["top_missing_standalone_emulators"]
    if missing_emulators:
        for item in missing_emulators:
            lines.append(f"- `{item['emulator']}`: {', '.join(item['systems'])}")
    else:
        lines.append("None.")

    lines.extend(["", "## Missing Libretro cores", ""])
    missing_cores = matrix["top_missing_libretro_cores"]
    if missing_cores:
        for item in missing_cores:
            lines.append(f"- `{item['core']}`: {', '.join(item['systems'])}")
    else:
        lines.append("None among the ROM-relevant Batocera defaults.")

    lines.extend(
        [
            "",
            "## Likely small Embercade ports",
            "",
            ", ".join(f"`{name}`" for name in matrix["small_port_candidates"]) or "None.",
            "",
            "These conservative candidates use comparatively direct Libretro routes, have the "
            "currently known host prerequisites, and are closest to the proven NES path. They "
            "still require a real Embercade route and end-to-end validation; the label is a "
            "prioritization hint, not a compatibility claim.",
            "",
            "## End-to-end proven",
            "",
            ", ".join(f"`{name}`" for name in matrix["e2e_proven_systems"]) or "None.",
            "",
            "NES is implemented with Nestopia; `fceumm` remains the pinned Batocera catalog "
            "default shown in the table. Both host cores are present in this snapshot.",
            "",
        ]
    )
    return "\n".join(lines)


def write_matrix(path: Path, matrix: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_documentation(path: Path, matrix: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_documentation(matrix), encoding="utf-8")

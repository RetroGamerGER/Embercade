"""Read-only coverage of the complete pinned catalog; never select a launcher."""

from hashlib import sha256
from pathlib import Path
from typing import Mapping
import json
import os
import re
import subprocess

from embercade.bios_inventory import (
    BATOCERA_COMMIT, BiosRequirement, RequirementEvaluator, MATCHED_STATUSES,
    scan_bios_root, inspect_opera_bios,
)
from embercade.compatibility import (
    E2E_VALIDATED_SYSTEMS, IMPLEMENTED_LAUNCH_PATHS, EXECUTABLE_CANDIDATES,
    _resolve_effective_executable,
)
from embercade.cores import LibretroCoreResolver, CoreResolutionError
from embercade.elf_runtime import inspect_elf_runtime
from embercade.host_requirements import _system_has_content
from embercade.launcher import SUPPORTED_LAUNCH_SYSTEMS
from embercade.paths import EmbercadePaths
from embercade.rom_inventory import load_batocera_systems
from embercade.runtime import executable_config, emulator_provider_config
from embercade.rpcs3 import inspect_rpcs3_firmware
from embercade.xemu import inspect_xemu_files
from embercade.ppsspp import resolve_ppsspp_assets, PpssppAssetsError


STATUSES = ("READY", "PREPARED", "BLOCKED", "UNSUPPORTED")
OUT_OF_SCOPE = frozenset({
    "ports", "steam", "moonlight", "flatpak", "imageviewer", "library",
    "recordings", "windows", "windows_installers", "odcommander", "pygame",
    "pico8", "lowresnx", "lutro", "tic80", "wasm4", "vircon32", "pyxel",
    # New community hardware and game-engine/port targets do not silently
    # become classical console ports because a host runtime happens to exist.
    "arduboy", "commanderx16", "gametank", "bennugd", "easyrpg", "flash",
    "ikemen", "mugen", "openbor", "solarus", "thextech", "vpinball", "zc210",
})


def structure_inputs_digest(project: Path) -> str:
    inputs = [project / "src/embercade/launcher.py", project / "src/embercade/libretro_dry_run.py",
              project / "src/embercade/shadps4.py",
              project / "src/embercade/wii.py",
              project / "src/embercade/backend.py", project / "src/embercade/batocera_config.py",
              project / "src/embercade/standalone_decoration.py", project / "src/embercade/runtime.py",
              project / "src/embercade/ui_data.py", project / "integration/batocera/adapter.py",
              project / "resources/defaults/batocera.conf", project / "upstream.lock"]
    inputs += sorted((project / "patches/batocera-launch").glob("*.patch"))
    digest = sha256()
    for path in inputs:
        digest.update(path.relative_to(project).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def inspect_core(resolver: LibretroCoreResolver, name: str) -> dict:
    """Verify actual ELF exports/loader closure; report optional core metadata."""
    try:
        resolution = resolver.resolve(name)
    except CoreResolutionError:
        return {"available": False, "reason": "CORE_MISSING", "path": None}
    result = resolution.as_json()
    result["available"] = False
    if not resolution.probably_loadable:
        result["reason"] = "CORE_NOT_ELF"
        return result
    try:
        exports = subprocess.run(["readelf", "--dyn-syms", "--wide", str(resolution.path)],
                                 capture_output=True, text=True, timeout=10, check=False)
        names = {line.split()[-1].split("@")[0] for line in exports.stdout.splitlines()
                 if line.split() and " UND " not in line}
        if exports.returncode or not {"retro_init", "retro_run", "retro_load_game",
                                      "retro_get_system_info", "retro_api_version"} <= names:
            result["reason"] = "CORE_ABI_UNVERIFIED"
            return result
        closure = inspect_elf_runtime(resolution.path)
    except (OSError, subprocess.TimeoutExpired):
        result["reason"] = "CORE_INSPECTION_UNAVAILABLE"
        return result
    if not closure.healthy:
        result.update(reason="CORE_DEPENDENCIES_MISSING", missing=list(closure.missing))
        return result
    result.update(abi_dependencies_verified=True, available=True,
                  reason="ELF_ABI_DEPENDENCIES_VERIFIED", metadata_verified=False)
    if resolution.info_path is None:
        result["metadata_status"] = "MISSING_OPTIONAL"
        return result
    info = {}
    try:
        lines = resolution.info_path.read_text(errors="replace").splitlines()
    except OSError:
        result["metadata_status"] = "UNREADABLE_OPTIONAL"
        return result
    for line in lines:
        if match := re.match(r'^\s*([a-zA-Z0-9_]+)\s*=\s*"([^"]*)"', line):
            info[match[1]] = match[2]
    result.update(metadata={key: info.get(key) for key in (
        "display_name", "systemname", "supported_extensions", "manufacturer")})
    if not info.get("display_name") or not info.get("supported_extensions"):
        result["metadata_status"] = "INCOMPLETE_OPTIONAL"
        return result
    result.update(metadata_verified=True, metadata_status="PRESENT")
    return result


def classify(row: Mapping, *, e2e=E2E_VALIDATED_SYSTEMS) -> tuple[str, str]:
    if row["out_of_scope"]:
        return "UNSUPPORTED", "NON_CLASSICAL_PORT_APP_OR_MEDIA"
    if not row["runtime_available"]:
        return "BLOCKED", row.get("runtime_reason", "EMULATOR_MISSING")
    if not row["launch_path_implemented"]:
        if row.get("effective_core") == "px68k":
            return "BLOCKED", "PX68K_WRITABLE_BIOS_CONFIG_NOT_ISOLATED"
        if row.get("effective_emulator") == "libretro" and row.get("effective_core") == "mame":
            return "BLOCKED", "MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED"
        return "BLOCKED", "EMBERCADE_PORT_MISSING"
    if not row["extensions"]:
        return "BLOCKED", "EXTENSIONS_UNKNOWN"
    if row.get("resource_missing"):
        return "BLOCKED", "REQUIRED_SYSTEM_ASSETS_MISSING"
    if row["system"] in e2e and row["bios_status"] not in {"MISSING", "UNKNOWN"}:
        return "READY", "CONFIRMED_GAME_E2E"
    if not row["structural_verified"]:
        return "BLOCKED", "STRUCTURAL_VALIDATION_PENDING"
    return "PREPARED", ("BIOS_SETUP_REQUIRED" if row["bios_status"] == "MISSING"
                        else "REAL_GAME_E2E_PENDING")


def collect_coverage(catalog: Path, requirements_file: Path, *, paths: EmbercadePaths,
                     config: Mapping, structural: Mapping | None = None,
                     environment: Mapping | None = None) -> dict:
    env = os.environ if environment is None else environment
    systems = load_batocera_systems(catalog)
    metadata = json.loads(requirements_file.read_text())
    if metadata["batocera_commit"] != BATOCERA_COMMIT:
        raise ValueError("BIOS metadata pin mismatch")
    requirements = [BiosRequirement(**row) for row in metadata["requirements"]]
    evaluator = RequirementEvaluator(scan_bios_root(paths.bios_root)) if paths.bios_root.is_dir() else None
    resolver = LibretroCoreResolver.from_host(config, env)
    core_cache, binary_cache = {}, {}
    rows = []
    for system in systems:
        route = IMPLEMENTED_LAUNCH_PATHS.get(system.system, {})
        emulator = route.get("effective_emulator") or system.default_emulator
        core = route.get("effective_core") or system.default_core
        if emulator not in binary_cache:
            candidates = dict(EXECUTABLE_CANDIDATES)
            # An unknown catalog command may be reported as installed, but it
            # never acquires a launch route merely by being found on PATH.
            if emulator and re.fullmatch(r"[A-Za-z0-9_+.-]+", emulator):
                candidates.setdefault(emulator, (emulator,))
            binary_cache[emulator] = _resolve_effective_executable(
                emulator or "", candidates, env, executable_config(config),
                emulator_provider_config(config))
        binary = binary_cache[emulator]
        if system.system == "ps4":
            from embercade.host_requirements import inspect_appimage_provider
            from embercade.executables import ExecutableResolver
            diagnosis = inspect_appimage_provider(
                ExecutableResolver(executable_config(config), providers=emulator_provider_config(config), environment=env),
                env, needed=True, provider_name="shadps4")
            binary = dict(binary, present=diagnosis.available, provider_status=diagnosis.status,
                          detail=diagnosis.detail)
        core_status = None
        if emulator == "libretro" and core:
            if core not in core_cache:
                core_cache[core] = inspect_core(resolver, core)
            core_status = core_cache[core]
        bios_results = []
        for requirement in requirements:
            if requirement.system != system.system:
                continue
            if requirement.emulator and requirement.emulator != emulator:
                continue
            if requirement.core and requirement.core != core:
                continue
            bios_results.append(evaluator.evaluate(requirement) if evaluator else {
                "relative_path": requirement.relative_path, "status": "MISSING",
                "required": not requirement.optional})
        bios_status = "NONE_DECLARED"
        if bios_results:
            bios_status = "SATISFIED" if all(not r["required"] or r["status"] in MATCHED_STATUSES
                                               for r in bios_results) else "MISSING"
        if system.system == "3do":
            bios_status = "SATISFIED" if inspect_opera_bios(paths.bios_root).available else "MISSING"
        if system.system == "ps3":
            bios_status = "SATISFIED" if inspect_rpcs3_firmware(paths, config, env).installed else "MISSING"
        if system.system == "xbox":
            xemu = inspect_xemu_files(paths, env)
            bios_status = "SATISFIED" if xemu.firmware_ready else "MISSING"
        resource_missing = False
        if system.system == "psp":
            try:
                resolve_ppsspp_assets(paths, config, env)
            except PpssppAssetsError:
                resource_missing = True
        proof = (structural or {}).get(system.system, {})
        row = {
            "system": system.system, "display_name": system.fullname,
            "upstream_present": True, "default_emulator": system.default_emulator,
            "default_core": system.default_core, "effective_emulator": emulator,
            "effective_core": core, "extensions": list(system.extensions),
            "collection_status": "ROM_PRESENT" if _system_has_content(paths.rom_root, system) else "NO_ROM",
            "bios_status": bios_status, "bios_requirements": bios_results,
            "host_core": core_status, "host_emulator": binary,
            "launch_path_implemented": system.system in SUPPORTED_LAUNCH_SYSTEMS,
            "route": route.get("route"),
            "out_of_scope": system.system not in E2E_VALIDATED_SYSTEMS and (
                system.group == "ports" or system.system in OUT_OF_SCOPE),
            "runtime_available": bool(binary.get("present")) and (
                emulator != "libretro" or bool(core_status and core_status.get("abi_dependencies_verified"))),
            # -L launches use the core ABI; .info is optional descriptive data.
            # Pinned Batocera supplies system/core mappings and extensions.
            "core_metadata_verified": bool(core_status and core_status.get("metadata_verified")),
            "runtime_reason": ((core_status or {}).get("reason", "CORE_MISSING")
                               if binary.get("present") and emulator == "libretro"
                               else "EMULATOR_MISSING"),
            "structural_verified": proof.get("verified", False) and proof.get("core") == core,
            "structural_error": proof.get("error"),
            "e2e_validated": system.system in E2E_VALIDATED_SYSTEMS,
            "resource_missing": resource_missing,
        }
        row["status"], row["reason"] = classify(row)
        rows.append(row)
    return {"schema_version": 1, "batocera_commit": BATOCERA_COMMIT,
            "mode": "complete upstream catalog; no game executed",
            "summary": {"total": len(rows), **{s: sum(r["status"] == s for r in rows) for s in STATUSES}},
            "systems": rows}


def render_coverage(report: Mapping) -> str:
    """Omit host paths from tracked prose; keep them only in local JSON evidence."""
    lines = ["## Complete pinned system coverage", "",
             f"Batocera `{report['batocera_commit']}`; all {report['summary']['total']} catalog IDs.", "",
             "READY is historical real game E2E. PREPARED is generator/ABI/dependency verification,",
             "not gameplay acceptance. Missing BIOS remains an explicit setup requirement.",
             "Optional Libretro .info companions never block a direct core launch or preparation.",
             "Ports/apps/media and new fantasy platforms are outside this classical-system sprint.",
             "An installed standalone without an implemented route remains BLOCKED.", "",
             "| Status | Count |", "|---|---:|"]
    lines.extend(f"| {status} | {report['summary'][status]} |" for status in STATUSES)
    for status in STATUSES:
        lines.extend(["", f"### {status}", "",
                      "| System | Name | Emulator / core | BIOS | Extensions | Launch route | Reason |",
                      "|---|---|---|---|---|---|---|"])
        for row in report["systems"]:
            if row["status"] != status:
                continue
            lines.append(f"| `{row['system']}` | {row['display_name']} | "
                         f"{row['effective_emulator']} / {row['effective_core']} | "
                         f"{row['bios_status']} | {' '.join(row['extensions'])} | "
                         f"{'implemented' if row['launch_path_implemented'] else 'missing'} | {row['reason']} |")
    lines.extend(["", "### Setup/E2E still required", "",
                  "Every PREPARED system needs a legally supplied compatible game/ROM set,",
                  "the listed firmware and real image/audio/input/exit/return acceptance.",
                  "Computer keyboard/media layouts, arcade BIOS/software sets, peripherals,",
                  "multiplayer and uncommon formats are not proven by a generator-only fixture.",
                  "Missing per-system artwork uses the existing optional decoration fallback;",
                  "shader presets are installation-local. Nothing is downloaded or installed.", ""])
    return "\n".join(lines)

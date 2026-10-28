"""Installer preferences and structured read-only diagnostics using existing backends."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping
import json
import re
import tomllib

from embercade.exit_hotkey import EXIT_HOTKEYS
from embercade.i18n import SUPPORTED_LANGUAGES
from embercade.runtime import load_config
from embercade.setup_flow import _replace_table_values, write_config_atomic


def saved_language(config: Mapping) -> str | None:
    section = config.get("installer", {})
    value = section.get("language") if isinstance(section, Mapping) else None
    return value if value in SUPPORTED_LANGUAGES else None


def save_language(path: Path, language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("Unsupported installer language")
    config = load_config(path)  # Refuse to repair/replace malformed existing configuration.
    if not isinstance(config.get("installer", {}), Mapping):
        raise ValueError("[installer] must be a TOML table")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    write_config_atomic(path, _replace_table_values(text, "installer", {"language": json.dumps(language)}))


def save_exit_hotkey(path: Path, hotkey: str) -> None:
    """Save only the existing shared exit preset, even before collection setup.

    Keep user formatting/comments and verify every candidate against the parsed
    configuration before the existing atomic writer publishes it. Unusual TOML
    layouts that cannot be edited narrowly are preserved rather than rewritten.
    """
    if hotkey not in EXIT_HOTKEYS:
        raise ValueError("Unsupported controller exit hotkey")
    if path.is_symlink():
        raise ValueError("Refusing to replace symlinked configuration")
    config = load_config(path)
    section = config.get("controller", {})
    if not isinstance(section, Mapping):
        raise ValueError("[controller] must be a TOML table")
    if section.get("exit_hotkey") == hotkey:
        return
    text = path.read_bytes().decode("utf-8") if path.exists() else ""
    expected = {**config, "controller": {**section, "exit_hotkey": hotkey}}
    value = json.dumps(hotkey)
    newline = "\r\n" if "\r\n" in text else "\n"

    def publish(candidate: str) -> bool:
        try:
            matches = tomllib.loads(candidate) == expected
        except tomllib.TOMLDecodeError:
            return False
        if not matches:
            return False
        write_config_atomic(path, candidate)
        return True

    # Replace only a scalar's value, retaining its indentation and inline comment.
    # Parsed equality also excludes lookalike keys in other tables/string content.
    key = r'(?:exit_hotkey|"exit_hotkey"|\'exit_hotkey\')'
    controller = r'(?:controller|"controller"|\'controller\')'
    assignment = re.compile(
        rf'(?m)^([ \t]*(?:{controller}[ \t]*\.[ \t]*)?{key}[ \t]*=[ \t]*)'
        r'(?:"(?:[^"\\\r\n]|\\.)*"|\'[^\'\r\n]*\'|[^#\r\n]*?)'
        r'([ \t]*(?:#[^\r\n]*)?)(?=\r?$)'
    )
    if "exit_hotkey" in section:
        for match in assignment.finditer(text):
            if publish(text[:match.start()] + match[1] + value + match[2] + text[match.end():]):
                return
    else:
        header = re.compile(rf'(?m)^[ \t]*\[[ \t]*{controller}[ \t]*\][ \t]*(?:#[^\r\n]*)?(?:\r?\n|$)')
        for match in header.finditer(text):
            separator = "" if match[0].endswith("\n") else newline
            if publish(text[:match.end()] + separator + f"exit_hotkey = {value}{newline}" + text[match.end():]):
                return
        separator = (newline if text and not text.endswith("\n") else "") + (newline if text else "")
        if publish(text + separator + f"[controller]{newline}exit_hotkey = {value}{newline}"):
            return
        # Existing dotted controller keys can only be extended before table headers.
        if publish(f"controller.exit_hotkey = {value}{newline}" + text):
            return
    raise ValueError("Cannot safely update [controller].exit_hotkey in this TOML layout")


def status_report(paths, config, assessment, plan, project_root=None) -> dict:
    def provider(status):
        return status.status if status else "OPTIONAL"
    from embercade.rpcs3 import firmware_version
    from embercade.xemu import isolated_xemu_files
    from embercade import xbox_eeprom
    try:
        eeprom = xbox_eeprom.inspect(xbox_eeprom.read(isolated_xemu_files(paths).eeprom))
    except FileNotFoundError: eeprom = {"missing": True}
    except (OSError, ValueError): eeprom = {"invalid": True}
    def required(item):
        r = item.requirement
        return r.required and (not r.emulator or r.emulator in assessment.active_emulators)
    checks = installation_checks(paths, config, assessment, project_root) if project_root else []
    return {
        "checks": checks,
        "active_systems": list(assessment.active_systems),
        "configured": all(check.ok for check in paths.validate_collection_roots()),
        "requirements": [{"label": s.requirement.label, "available": s.installed, "required": required(s)}
                         for s in sorted(assessment.requirements, key=lambda s: not required(s))],
        "cores": [{"label": s.core, "available": s.installed} for s in assessment.cores],
        "rpcs3": bool(firmware_version(paths.emulator_configs / "rpcs3")),
        "rpcs3_source": assessment.rpcs3_firmware == "OK",
        "eeprom": eeprom,
        "opera_bios": assessment.opera_bios,
        "xemu_firmware": assessment.xemu_firmware == "OK",
        "xemu_hdd": assessment.xemu_hdd == "OK",
        "xemu_eeprom": assessment.xemu_eeprom == "OK",
        "xenia": provider(assessment.xenia_provider),
        "shadps4": provider(assessment.shadps4_provider),
        "packages": list(plan.packages), "unavailable": list(plan.unavailable_packages),
        "community": list(plan.aur_packages),
    }


def installation_checks(paths, config, assessment, project):
    """Use pinned BIOS metadata, effective user routes and verified runtime probes.

    This is setup availability evidence, never per-host gameplay acceptance.
    """
    import os
    from embercade.production import ProductionLayout
    from embercade.bios_inventory import (BATOCERA_COMMIT, BiosRequirement, RequirementEvaluator,
                                          scan_bios_root, MATCHED_STATUSES, BiosInventoryError)
    from embercade.host_requirements import _read_batocera_values
    from embercade.rom_inventory import load_batocera_systems
    from embercade.ppsspp import resolve_ppsspp_assets, PpssppAssetsError
    from embercade.system_coverage import inspect_core
    from embercade.cores import LibretroCoreResolver
    rows = []
    layout = ProductionLayout.from_environment()
    rows.append(dict(label="Application runtime", available=bool(layout and not layout.validate()), required=True))
    resolver = LibretroCoreResolver.from_host(config, os.environ)
    for core in assessment.cores:
        rows.append(dict(label=core.core, available=bool(core.installed and inspect_core(resolver, core.core)["available"]), required=True))
    active = set(assessment.active_systems)
    if not active: return rows
    catalog = project/'resources/emulationstation'
    if not (catalog/'bios-requirements.json').is_file(): catalog = project/'.work/system-catalog/output'
    try:
        metadata = json.loads((catalog/'bios-requirements.json').read_text())
        if metadata['batocera_commit'] != BATOCERA_COMMIT: raise ValueError('Metadata pin mismatch')
        requirements = [BiosRequirement(**row) for row in metadata['requirements']]
        values = _read_batocera_values((project/'resources/defaults/batocera.conf',paths.batocera_conf))
        evaluator = RequirementEvaluator(scan_bios_root(paths.bios_root))
        for system in load_batocera_systems(catalog/'es_systems.cfg'):
            if system.system not in active or system.system in {'ps3','xbox'}: continue
            emulator = values.get(f'{system.system}.emulator', system.default_emulator or '')
            core = values.get(f'{system.system}.core',system.default_core or '')
            for requirement in requirements:
                if requirement.system != system.system: continue
                if requirement.emulator and requirement.emulator != emulator: continue
                if requirement.core and requirement.core != core: continue
                result = evaluator.evaluate(requirement)
                rows.append(dict(label=f'{system.fullname}: {requirement.relative_path}',
                    available=result['status'] in MATCHED_STATUSES, required=not requirement.optional,
                    invalid=result['status'] in {'HASH_MISMATCH','UNKNOWN','CASE_MISMATCH'}))
    except (OSError,ValueError,KeyError,BiosInventoryError):
        rows.append(dict(label="BIOS verification", available=False, required=True, invalid=True))
    if 'psp' in active:
        try: resolve_ppsspp_assets(paths,config,os.environ)
        except PpssppAssetsError: available=False
        else: available=True
        rows.append(dict(label="PSP assets",available=available,required=True))
    return rows

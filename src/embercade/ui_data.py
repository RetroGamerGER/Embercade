from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import os
import subprocess
import sys
from typing import Mapping
import xml.etree.ElementTree as ET

from embercade.backend import backend_command


REGISTRY_PATHS = (
    "package/batocera/emulationstation/batocera-es-system/_global.emulator.yml",
    "package/batocera/emulationstation/batocera-es-system/_shared.emulator.yml",
    "package/batocera/emulationstation/batocera-es-system/hud._shared.emulator.yml",
    "package/batocera/emulators/retroarch/retroarch/libretro.emulator.yml",
    "package/batocera/emulators/retroarch/retroarch/gfxbackend.libretro.emulator.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-opera/opera.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-nestopia/nestopia.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-fceumm/fceumm.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-mesen/mesen.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-stella/stella.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-atari800/atari800.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-prosystem/prosystem.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-genesisplusgx/genesisplusgx.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-gambatte/gambatte.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-mgba/mgba.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-mrboom/mrboom.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-fbneo/fbneo.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-beetle-ngp/mednafen_ngp.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-beetle-pce/pce.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-prboom/prboom.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-vice/vice_x64.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-melonds/melonds.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-melonds-ds/melondsds.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-ppsspp/ppsspp.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-azahar/azahar.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-mupen64plus-next/mupen64plus-next.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-virtualjaguar/virtualjaguar.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-puae/puae.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-dosbox-pure/dosbox_pure.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-mame2003-plus/mame078plus.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-flycast/flycast.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-neocd/neocd.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-pcsx/pcsx_rearmed.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-swanstation/swanstation.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-beetle-psx/mednafen_psx.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-beetle-saturn/beetle-saturn.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-picodrive/picodrive.libretro.core.yml",
    "package/batocera/emulators/retroarch/libretro/libretro-snes9x/snes9x.libretro.core.yml",
    "package/batocera/emulators/dolphin-emu/dolphin.emulator.yml",
    "package/batocera/emulators/dolphin-emu/gfxbackend.dolphin.emulator.yml",
    "package/batocera/emulators/xemu/xemu.emulator.yml",
    "package/batocera/emulators/pcsx2/pcsx2.emulator.yml",
    "package/batocera/emulators/rpcs3/rpcs3.emulator.yml",
    "package/batocera/emulators/cemu-common/cemu.emulator.yml",
    "package/batocera/emulators/xenia-edge/xenia-edge.emulator.yml",
)

BLOCKED_DESKTOP_FEATURES = frozenset(
    {
        "powermode",
        "batterymode",
        "tdp",
        "videomode",
        "wheel_rotation",
        "wheel_deadzone",
        "wheel_midzone",
        "pcsx2_crisis_fog",
        "pcsx2_crosshairs",
        "mesen_screenrotation",
    }
)

# Stable paths inside the production Bubblewrap namespace.  They never expose
# the staging/install prefix or a host-specific collection path in generated
# frontend data.
PRODUCTION_LAUNCH_COMMAND = Path("/app/bin/embercade")
PRODUCTION_ROM_ROOT = Path("/userdata/roms")


def _write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)


def _customize_systems(
    path: Path,
    *,
    rom_path: Path,
    launch_command: Path,
    gamecube_rom_path: Path | None = None,
    gamecube_launch_command: Path | None = None,
    wii_rom_path: Path | None = None,
    wii_launch_command: Path | None = None,
    xbox_rom_path: Path | None = None,
    xbox_launch_command: Path | None = None,
    ps2_rom_path: Path | None = None,
    ps2_launch_command: Path | None = None,
    ps3_rom_path: Path | None = None,
    ps3_launch_command: Path | None = None,
    libretro_systems: Mapping[str, Path] | None = None,
    libretro_launch_command: Path | None = None,
    external_systems: Mapping[str, Path] | None = None,
    external_launch_command: Path | None = None,
) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    selected: dict[str, tuple[Path, Path, str | None]] = {
        "nes": (rom_path, launch_command, None)
    }
    if gamecube_rom_path is not None and gamecube_launch_command is not None:
        selected["gamecube"] = (gamecube_rom_path, gamecube_launch_command, None)
    if wii_rom_path is not None and wii_launch_command is not None:
        selected["wii"] = (wii_rom_path, wii_launch_command, None)
    if xbox_rom_path is not None and xbox_launch_command is not None:
        selected["xbox"] = (xbox_rom_path, xbox_launch_command, None)
    if ps2_rom_path is not None and ps2_launch_command is not None:
        selected["ps2"] = (ps2_rom_path, ps2_launch_command, None)
    if ps3_rom_path is not None and ps3_launch_command is not None:
        selected["ps3"] = (ps3_rom_path, ps3_launch_command, None)
    if libretro_systems:
        if libretro_launch_command is None:
            raise ValueError("Libretro UI systems require one generic launch command")
        for name, path_value in libretro_systems.items():
            if name in selected:
                raise ValueError(f"duplicate UI system: {name}")
            selected[name] = (path_value, libretro_launch_command, name)
    if external_systems:
        if external_launch_command is None:
            raise ValueError("External UI systems require one generic launch command")
        for name, path_value in external_systems.items():
            if name in selected:
                raise ValueError(f"duplicate UI system: {name}")
            selected[name] = (path_value, external_launch_command, name)
    for system in list(root.findall("system")):
        name = system.findtext("name")
        if name not in selected:
            root.remove(system)
            continue
        selected_rom_path, selected_launch_command, generic_system = selected[name]
        system.find("path").text = str(selected_rom_path)
        system.find("command").text = (
            f'"{selected_launch_command}" --system {generic_system} --rom %ROM%'
            if generic_system is not None
            else f'"{selected_launch_command}" --rom %ROM%'
        )
        if name == "ps3":
            system.find("extension").text = ".iso .ps3 .psn"
        if name == "sega32x":
            group = system.find("group")
            if group is not None:
                system.remove(group)
        if name == "nes":
            for core in system.findall("./emulators/emulator/cores/core"):
                if core.text == "nestopia":
                    core.set("default", "true")
                else:
                    core.attrib.pop("default", None)
    _write_xml(tree, path)


def _filter_desktop_features(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    for parent in root.iter():
        for child in list(parent):
            if child.tag == "sharedFeature" and child.get("value") in BLOCKED_DESKTOP_FEATURES:
                parent.remove(child)
            elif child.tag == "feature" and child.get("value") in BLOCKED_DESKTOP_FEATURES:
                parent.remove(child)
            elif child.tag == "feature" and child.get("value") == "emulatedwiimotes":
                child.set("description", "Auto uses a connected real Wii Remote, otherwise your gamepad. On forces emulation; Off uses real Wii Remotes. Nunchuk and IR are handled by Dolphin.")
    _write_xml(tree, path)


def merge_feature_overlay(path: Path, overlay: Path) -> None:
    """Merge pinned Batocera feature metadata missing from the base bundle."""
    tree = ET.parse(path)
    root = tree.getroot()
    overlay_root = ET.parse(overlay).getroot()

    for source_emulator in overlay_root.findall("emulator"):
        emulator_name = source_emulator.get("name")
        target_emulator = root.find(f"./emulator[@name='{emulator_name}']")
        if target_emulator is None:
            root.append(deepcopy(source_emulator))
            continue

        source_cores = source_emulator.find("cores")
        if source_cores is None:
            continue
        target_cores = target_emulator.find("cores")
        if target_cores is None:
            target_cores = ET.SubElement(target_emulator, "cores")

        for source_core in source_cores.findall("core"):
            core_name = source_core.get("name")
            target_core = target_cores.find(f"./core[@name='{core_name}']")
            if target_core is None:
                target_cores.append(deepcopy(source_core))
                continue

            existing = {
                (child.tag, child.get("value"))
                for child in target_core
                if child.tag in {"feature", "sharedFeature"}
            }
            for child in source_core:
                identity = (child.tag, child.get("value"))
                if child.tag in {"feature", "sharedFeature"} and identity not in existing:
                    target_core.append(deepcopy(child))
                    existing.add(identity)

    _write_xml(tree, path)


def load_system_provider_defaults(path: Path) -> dict[str, tuple[str, str]]:
    """Read complete system emulator/core pairs from a Batocera config."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    systems = {
        key.removesuffix(".emulator")
        for key in values
        if key.endswith(".emulator")
    }
    return {
        system: (values[f"{system}.emulator"], values[f"{system}.core"])
        for system in sorted(systems)
        if values.get(f"{system}.emulator") and values.get(f"{system}.core")
    }


def _ensure_system_provider(
    system: ET.Element,
    *,
    emulator_name: str,
    core_name: str,
) -> None:
    emulators = system.find("emulators")
    if emulators is None:
        emulators = ET.SubElement(system, "emulators")
    emulator = emulators.find(f"./emulator[@name='{emulator_name}']")
    if emulator is None:
        emulator = ET.SubElement(emulators, "emulator", {"name": emulator_name})
    cores = emulator.find("cores")
    if cores is None:
        cores = ET.SubElement(emulator, "cores")
    if not any(core.text == core_name for core in cores.findall("core")):
        ET.SubElement(cores, "core").text = core_name


def customize_production_systems(
    path: Path,
    *,
    systems: frozenset[str],
    provider_defaults: Mapping[str, tuple[str, str]] | None = None,
) -> None:
    """Keep implemented systems and route all launches through Embercade."""
    tree = ET.parse(path)
    root = tree.getroot()
    for system in list(root.findall("system")):
        name = system.findtext("name")
        if name not in systems:
            root.remove(system)
            continue
        path_node = system.find("path")
        command_node = system.find("command")
        if path_node is None or command_node is None or name is None:
            raise ValueError(f"Incomplete Batocera system definition: {name!r}")
        collection_name = "segacd" if name == "megacd" else name
        path_node.text = str(PRODUCTION_ROM_ROOT / collection_name)
        command_node.text = (
            f'"{PRODUCTION_LAUNCH_COMMAND}" launch --system {name} --rom %ROM%'
        )
        if name == "ps3":
            extension = system.find("extension")
            if extension is not None:
                extension.text = ".iso .ps3 .psn"
        if name == "sega32x":
            group = system.find("group")
            if group is not None:
                system.remove(group)
        if name == "nes":
            for core in system.findall("./emulators/emulator/cores/core"):
                if core.text == "nestopia":
                    core.set("default", "true")
                else:
                    core.attrib.pop("default", None)
        if provider_defaults and name in provider_defaults:
            emulator_name, core_name = provider_defaults[name]
            _ensure_system_provider(
                system,
                emulator_name=emulator_name,
                core_name=core_name,
            )
    _write_xml(tree, path)


def build_ui_data(
    *,
    batocera_source: Path,
    defaults: Path,
    output: Path,
    rom_path: Path,
    launch_command: Path,
    gamecube_rom_path: Path | None = None,
    gamecube_launch_command: Path | None = None,
    wii_rom_path: Path | None = None,
    wii_launch_command: Path | None = None,
    xbox_rom_path: Path | None = None,
    xbox_launch_command: Path | None = None,
    ps2_rom_path: Path | None = None,
    ps2_launch_command: Path | None = None,
    ps3_rom_path: Path | None = None,
    ps3_launch_command: Path | None = None,
    libretro_systems: Mapping[str, Path] | None = None,
    libretro_launch_command: Path | None = None,
    external_systems: Mapping[str, Path] | None = None,
    external_launch_command: Path | None = None,
) -> tuple[Path, Path]:
    _build_raw_catalog(batocera_source, defaults, output, complete=False)

    systems_path = output / "es_systems.cfg"
    features_path = output / "es_features.cfg"
    _customize_systems(
        systems_path,
        rom_path=rom_path,
        launch_command=launch_command,
        gamecube_rom_path=gamecube_rom_path,
        gamecube_launch_command=gamecube_launch_command,
        wii_rom_path=wii_rom_path,
        wii_launch_command=wii_launch_command,
        xbox_rom_path=xbox_rom_path,
        xbox_launch_command=xbox_launch_command,
        ps2_rom_path=ps2_rom_path,
        ps2_launch_command=ps2_launch_command,
        ps3_rom_path=ps3_rom_path,
        ps3_launch_command=ps3_launch_command,
        libretro_systems=libretro_systems,
        libretro_launch_command=libretro_launch_command,
        external_systems=external_systems,
        external_launch_command=external_launch_command,
    )
    _filter_desktop_features(features_path)
    return systems_path, features_path


def build_complete_catalog(source: Path, defaults: Path, output: Path) -> None:
    """Use Batocera's builder and every pinned definition, not a ROM subset."""
    _build_raw_catalog(source, defaults, output, complete=True)
    _filter_desktop_features(output / "es_features.cfg")


def _build_raw_catalog(source: Path, defaults: Path, output: Path, *, complete: bool) -> None:
    arguments = ["--source", str(source), "--defaults", str(defaults),
                 "--output", str(output), "--mode", "complete" if complete else "selected"]
    if not complete:
        for relative in REGISTRY_PATHS:
            arguments.extend(("--registry", relative))
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    try:
        result = subprocess.run(
            backend_command(Path(sys.executable), "build-ui", *arguments),
            env=environment, capture_output=True, text=True, check=False,
        )
    except OSError as error:
        raise ValueError(f"Batocera UI builder failed: {error}") from error
    if result.returncode:
        raise ValueError(f"Batocera UI builder failed: {result.stderr.strip() or f'exit {result.returncode}'}")
    try:
        payload = json.loads(result.stdout)
        if (payload["systems"] != str(output / "es_systems.cfg")
                or payload["features"] != str(output / "es_features.cfg")
                or not all((output / name).is_file() for name in ("es_systems.cfg", "es_features.cfg"))):
            raise ValueError("Unexpected builder outputs")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ValueError("Batocera UI builder returned invalid data") from error
    if result.stderr:
        print(result.stderr, end="")

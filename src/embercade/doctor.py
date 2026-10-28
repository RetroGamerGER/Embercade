"""Human-readable host diagnostics used during the desktop port."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, TextIO
import glob
import os
import sys

from embercade.display import DisplaySession
from embercade.bios_inventory import inspect_opera_bios
from embercade.cores import LibretroCoreResolver
from embercade.controller import ControllerUnavailable, resolve_player_controllers
from embercade.controller_exit import load_host_evdev
from embercade.exit_hotkey import resolve_exit_hotkey
from embercade.executables import ExecutableResolutionError, ExecutableResolver
from embercade.host_requirements import HostAssessment
from embercade.paths import EmbercadePaths
from embercade.ppsspp import PpssppAssetsError, resolve_ppsspp_assets
from embercade.production import ProductionLayout
from embercade.runtime import ProjectRuntime, probe_runtime
from embercade.rpcs3 import inspect_rpcs3_firmware
from embercade.xemu import inspect_xemu_files
from embercade.version import __version__
from embercade.special_input import inspect_special_inputs


def _controller_nodes() -> list[str]:
    nodes: list[str] = []
    for link in sorted(glob.glob("/dev/input/by-id/*-event-joystick")):
        try:
            target = os.path.realpath(link)
        except OSError:
            continue
        nodes.append(f"{Path(link).name} -> {target}")
    return nodes


def report(
    paths: EmbercadePaths,
    resolver: ExecutableResolver,
    *,
    environment: Mapping[str, str] | None = None,
    runtime: ProjectRuntime | None = None,
    core_resolver: LibretroCoreResolver | None = None,
    core_catalog: tuple[str, ...] = (),
    production_layout: ProductionLayout | None = None,
    host_assessment: HostAssessment | None = None,
    config: Mapping[str, object] | None = None,
    stream: TextIO | None = None,
) -> int:
    env = os.environ if environment is None else environment
    output = sys.stdout if stream is None else stream
    session = DisplaySession.current(env)
    failures = 0

    print(f"Embercade doctor {__version__}", file=output)
    immutable_roots = [production_layout.prefix] if production_layout is not None else []
    if appdir := env.get("APPDIR"):
        immutable_roots.append(Path(appdir))
    misplaced = sorted({name for root in immutable_roots for name in paths.writable_roots_inside(root)})
    if misplaced:
        failures += 1
        print("AppImage state separation: UNSAFE (writable roots inside application: "
              + ", ".join(misplaced) + ")", file=output)
    else:
        print("AppImage state separation: OK (external writable roots)", file=output)
    if production_layout is not None:
        print("", file=output)
        print("Production staging/install layout:", file=output)
        layout_failures = production_layout.validate(check_frontend_libraries=False)
        frontend_report = production_layout.frontend_runtime()
        if layout_failures:
            failures += len(layout_failures)
            for failure in layout_failures:
                print(f"  FATAL    {failure}", file=output)
        if not layout_failures:
            print(f"  prefix   OK       {production_layout.prefix}", file=output)
            print(f"  runtime  OK       {production_layout.runtime.root}", file=output)
            print(f"  resources OK      {production_layout.resources}", file=output)
        print("", file=output)
        print("Frontend:", file=output)
        if production_layout.frontend.is_file():
            print(f"  binary present        OK       {production_layout.frontend}", file=output)
        else:
            print(f"  binary present        MISSING  {production_layout.frontend}", file=output)
        if frontend_report.healthy:
            print("  shared libraries      OK", file=output)
        else:
            failures += len(frontend_report.failures)
            print("  shared libraries      MISSING", file=output)
            if frontend_report.closure.missing:
                print("  missing:", file=output)
                for soname in frontend_report.closure.missing:
                    print(f"    {soname}", file=output)
            for failure in frontend_report.failures:
                if "shared libraries missing:" not in failure:
                    print(f"  FATAL    {failure}", file=output)
    print("", file=output)
    print("Paths (resolved, not created):", file=output)
    for name, path in paths.as_dict().items():
        print(f"  {name:8} {path}", file=output)

    print("", file=output)
    print("Writable Embercade XDG roots:", file=output)
    for name, path in paths.as_dict().items():
        if name in {"roms", "bios"}:
            continue
        candidate = path
        while not candidate.exists() and candidate != candidate.parent:
            candidate = candidate.parent
        writable = candidate.is_dir() and os.access(candidate, os.W_OK | os.X_OK)
        if writable:
            print(f"  {name:8} OK       {path}", file=output)
        else:
            failures += 1
            print(f"  {name:8} FATAL    {path}", file=output)

    print("", file=output)
    print("Collection roots (structure only):", file=output)
    for validation in paths.validate_collection_roots():
        if validation.ok:
            print(f"  {validation.label:10} OK              {validation.path}", file=output)
        elif not validation.configured:
            failures += 1
            print(
                f"  {validation.label:10} CONFIGURATION REQUIRED {validation.path}",
                file=output,
            )
        else:
            failures += 1
            print(f"  {validation.label:10} {validation.status:15} {validation.path}", file=output)

    print("", file=output)
    print("Runtime:", file=output)
    runtime_status = probe_runtime(runtime) if runtime is not None else None
    if runtime_status is None or not runtime_status.available:
        failures += 1
        print("  Python runtime       MISSING  run scripts/runtime-prepare", file=output)
        for label in (
            "batocera-common",
            "batocera-launch",
            "configgen",
            "configgen.launch",
            "libretro generator",
        ):
            print(f"  {label:20} MISSING", file=output)
        print("  launcher CLI         MISSING", file=output)
    else:
        print(
            f"  Python runtime       OK       {runtime_status.python_version} "
            f"({'production' if runtime and runtime.installed_root else 'dev compatibility'})",
            file=output,
        )
        for label, error in runtime_status.imports.items():
            if error is None:
                print(f"  {label:20} OK", file=output)
            else:
                failures += 1
                print(f"  {label:20} FAIL     {error}", file=output)
        if runtime_status.cli_error is None:
            print("  launcher CLI         OK       --help", file=output)
        else:
            failures += 1
            print(f"  launcher CLI         FAIL     {runtime_status.cli_error}", file=output)

    print("", file=output)
    print("Host emulators:", file=output)
    if host_assessment is not None:
        shadps4 = host_assessment.shadps4_provider
        if shadps4 is not None:
            print(f"  {'shadps4':12} {shadps4.status}  {shadps4.summary}", file=output)
            print(f"    {shadps4.detail}", file=output)
        emulator_keys = {"retroarch", "dolphin", "pcsx2", "rpcs3", "xemu"}
        for status in host_assessment.requirements:
            if status.requirement.key not in emulator_keys:
                continue
            state = "OK" if status.installed else "OPTIONAL SYSTEM UNAVAILABLE"
            print(
                f"  {status.requirement.key:12} {state}  {status.detail}", file=output
            )
        diagnosis = host_assessment.xenia_provider
        if diagnosis is not None:
            print(
                f"  {'xenia-edge':12} {diagnosis.status}  {diagnosis.summary}",
                file=output,
            )
            print(f"    {diagnosis.detail}", file=output)
            if diagnosis.path:
                print(f"    {diagnosis.path} ({diagnosis.source})", file=output)
        elif host_assessment.xenia_edge:
            print(f"  {'xenia-edge':12} OK  {host_assessment.xenia_edge}", file=output)
        else:
            print("  xenia-edge   OPTIONAL SYSTEM UNAVAILABLE  not configured", file=output)
    else:
        for name, result in resolver.probe_all().items():
            if isinstance(result, ExecutableResolutionError):
                print(f"  {name:12} OPTIONAL SYSTEM UNAVAILABLE  {result}", file=output)
            else:
                print(f"  {name:8} OK       {result.path} ({result.source})", file=output)

    if core_resolver is not None:
        inventory = core_resolver.inventory(core_catalog)
        summary = inventory["summary"]
        print("", file=output)
        print("Libretro cores (read-only discovery):", file=output)
        for directory in core_resolver.core_directories:
            state = "present" if directory.path.is_dir() else "missing"
            mode = "configured" if directory.configured else "fallback"
            print(
                f"  {directory.path} ({directory.path_type}, {directory.source}, {mode}, {state})",
                file=output,
            )
        print(
            f"  installed          {summary['installed_unique']} unique cores "
            f"in {summary['installed_locations']} locations",
            file=output,
        )
        if core_catalog:
            print(
                f"  Batocera 44        {summary['batocera_found']}/{summary['batocera_catalog']} found; "
                f"{summary['batocera_missing']} missing",
                file=output,
            )
        catalog_rows = {
            row["batocera_name"]: row for row in inventory["batocera_cores"]
        }
        for core_name in ("nestopia", "snes9x", "mgba", "flycast", "ppsspp"):
            if (row := catalog_rows.get(core_name)) is not None:
                status = row["path"] or "MISSING"
                print(f"  {core_name:18} {status}", file=output)
        if host_assessment is not None:
            required = host_assessment.cores
            found = sum(status.installed for status in required)
            print(f"  collection-required {found}/{len(required)} found", file=output)
            for status in required:
                if not status.installed:
                    package = f"; package {status.package}" if status.package else ""
                    print(f"  {status.core:18} CORE MISSING{package}", file=output)

    print("", file=output)
    print("Desktop session:", file=output)
    print(f"  protocol         {session.protocol}", file=output)
    print(f"  DISPLAY          {env.get('DISPLAY', '<unset>')}", file=output)
    print(f"  WAYLAND_DISPLAY  {env.get('WAYLAND_DISPLAY', '<unset>')}", file=output)
    print(f"  XDG_RUNTIME_DIR  {env.get('XDG_RUNTIME_DIR', '<unset>')}", file=output)
    print("  mode switching   disabled", file=output)

    print("", file=output)
    print("Normal evdev gamepads (optional probe):", file=output)
    controllers = _controller_nodes()
    if controllers:
        for controller in controllers:
            print(f"  {controller}", file=output)
    else:
        print("  WARNING  no controller exposed through /dev/input/by-id", file=output)

    print("SDL gamepads (optional, current player order):", file=output)
    try:
        players = resolve_player_controllers(
            es_settings=paths.emulationstation_config / "es_settings.cfg"
        )
        if not players:
            print("  none connected; frontend keyboard remains available", file=output)
        for slot, controller in enumerate(players, start=1):
            print(f"  P{slot}  {controller.name}  GUID {controller.guid}  "
                  f"{controller.device_path}  SDL index {controller.index}", file=output)
        identities = {(device.guid, device.name) for device in players}
        if len(identities) < len(players):
            print("  note: identical GUID/name pads share an input mapping, "
                  "but use separate live device paths", file=output)
    except ControllerUnavailable as error:
        print(f"  WARNING  {error}", file=output)

    from embercade.wii import wii_hardware_summary

    print("Wii input (optional, read-only): " + wii_hardware_summary(), file=output)
    print("  Nunchuk/MotionPlus/IR: unknown until native Dolphin gameplay; no pairing or HID probe performed", file=output)
    print("  Bluetooth adapters: " + str(len(tuple(Path('/sys/class/bluetooth').glob('hci*')))), file=output)

    special = inspect_special_inputs()
    print("Special controllers (structural only; no hardware READY claim):", file=output)
    if special.probe_available:
        print(f"  Lightguns   PREPARED / UNVALIDATED; udev gun nodes: {special.guns}", file=output)
        print(f"  Wheels      PREPARED / UNVALIDATED; udev wheel nodes: {special.wheels}", file=output)
        print(f"  Trackballs  PREPARED / UNVALIDATED; explicitly tagged nodes: {special.trackballs}; mouse/pointer nodes: {special.mouse_pointers}", file=output)
    else:
        print("  PREPARED / UNVALIDATED; udev probe unavailable (optional)", file=output)
    print("  Real device mapping, calibration, force feedback and hotplug gameplay require hardware E2E", file=output)

    print("", file=output)
    effective_config = {} if config is None else config
    try:
        ppsspp = resolve_ppsspp_assets(paths, effective_config, env)
    except PpssppAssetsError as error:
        print(f"PPSSPP assets: PSP GAMES UNAVAILABLE  {error}", file=output)
    else:
        print(f"PPSSPP assets: OK  {ppsspp}", file=output)
    try:
        exit_hotkey = resolve_exit_hotkey(effective_config)
    except ValueError as error:
        failures += 1
        print(f"Exit hotkey: INVALID ({error})", file=output)
    else:
        print(f"Exit hotkey: {exit_hotkey.label}", file=output)
    print("Native exit bridge:", file=output)
    try:
        evdev = load_host_evdev()
    except ImportError:
        print("  WARNING  host python-evdev is unavailable", file=output)
    else:
        print(f"  evdev OK       {evdev.__file__}", file=output)

    firmware = inspect_rpcs3_firmware(paths, effective_config, env)
    print("", file=output)
    print("Firmware and writable emulator state:", file=output)
    if (paths.rom_root / "3do").is_dir():
        opera = inspect_opera_bios(paths.bios_root)
        print(f"  3DO BIOS          {opera.status}  {opera.detail}", file=output)
        print(f"    Expected directly below {paths.bios_root}; one system BIOS is sufficient.", file=output)
    print(
        f"  PS3 firmware      {'OK' if firmware.installed else 'NOT INSTALLED'}  "
        f"{firmware.detail}",
        file=output,
    )
    if not firmware.installed:
        print(
            "  Install firmware from RPCS3's File > Install Firmware menu; "
            "Embercade never downloads it.",
            file=output,
        )
    xemu = inspect_xemu_files(paths, env)
    print(f"  Xemu firmware     {'OK' if xemu.firmware_ready else 'MISSING'}  {xemu.firmware_detail}", file=output)
    print(f"  Xemu EEPROM       {'OK' if xemu.eeprom_ready else 'FIRST START'}  {xemu.eeprom_detail}", file=output)
    print(f"  Xemu HDD          {'OK' if xemu.hdd_ready else 'MISSING'}  {xemu.hdd_detail}", file=output)

    if production_layout is not None and core_resolver is not None:
        catalog_root = production_layout.resources / "emulationstation"
        if (catalog_root / "systems-catalog.xml").is_file():
            from embercade.system_coverage import collect_coverage
            import json
            print("", file=output)
            print("Complete system preparation (no game E2E inferred):", file=output)
            try:
                coverage = collect_coverage(catalog_root / "systems-catalog.xml",
                                            catalog_root / "bios-requirements.json", paths=paths,
                                            config=effective_config, environment=env,
                                            structural=json.loads((catalog_root / "system-structure.json").read_text()))
                print("  " + "; ".join(f"{key}: {value}" for key, value in coverage["summary"].items()), file=output)
                for row in coverage["systems"]:
                    if row["status"] == "UNSUPPORTED":
                        continue
                    content = "INFO: no games yet" if row["collection_status"] == "NO_ROM" else "games present"
                    if row["status"] == "BLOCKED" or row["bios_status"] == "MISSING":
                        print(f"  {row['system']}: {row['status']} / {row['reason']}; {content}; BIOS {row['bios_status']}", file=output)
                print("  Missing games are informational, not an installation failure.", file=output)
            except (OSError, ValueError) as error:
                failures += 1
                print(f"  FATAL: coverage metadata unavailable: {error}", file=output)
    return 0 if failures == 0 else 1

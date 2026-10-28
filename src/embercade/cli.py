from __future__ import annotations

import argparse
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import os
import subprocess
import sys
import tomllib

from embercade.controller import (
    ControllerUnavailable,
    enumerate_sdl_game_controllers,
    require_player_one_controller,
    resolve_player_controllers,
    write_es_input_override,
    write_es_input_overrides,
)
from embercade.bios_inventory import (
    BiosInventoryError,
    build_bios_inventory,
    inspect_opera_bios,
    load_batocera_bios_requirements,
    read_pinned_batocera_source,
    write_documentation as write_bios_documentation,
    write_inventory as write_bios_inventory,
)
from embercade.cores import LibretroCoreResolver, load_batocera_catalog, write_inventory
from embercade.compatibility import (
    CompatibilityError,
    build_compatibility_matrix,
    write_documentation as write_compatibility_documentation,
    write_matrix as write_compatibility_matrix,
)
from embercade.doctor import report
from embercade.dolphin_dry_run import (
    DolphinDryRunError,
    build_report as build_dolphin_dry_run_report,
    execute_dry_run as execute_dolphin_dry_run,
    write_report as write_dolphin_dry_run_report,
)
from embercade.executables import ExecutableResolver, ExecutableResolutionError
from embercade.host_requirements import (
    AurHelper,
    HostAssessment,
    assess_host,
    create_bootstrap_plan,
    render_host_summary,
    run_bootstrap,
)
from embercade.imports import ImportError as ManagedImportError, import_cores, import_providers
from embercade.installer import (
    InstallationError,
    install_user,
    launcher_path_guidance,
    print_operations,
    uninstall_user,
)
from embercade.launcher import LaunchError, create_launch_plan, prepare_launch_layout, run_launch
from embercade.libretro_dry_run import (
    LibretroDryRunError,
    build_report as build_libretro_dry_run_report,
    execute_dry_run as execute_libretro_dry_run,
    snapshot_metadata,
    write_report as write_libretro_dry_run_report,
)
from embercade.paths import EmbercadePaths
from embercade.policy import DesktopPolicy
from embercade.production import ProductionError, ProductionLayout, run_production
from embercade.pcsx2 import Pcsx2RuntimeError
from embercade.rpcs3 import (
    Rpcs3RuntimeError, existing_firmware_package, inspect_rpcs3_firmware,
    open_firmware_installer, prepare_rpcs3_firmware,
)
from embercade.rom_inventory import (
    RomInventoryError,
    inventory_rom_root,
    load_batocera_systems,
    write_documentation as write_rom_documentation,
    write_inventory as write_rom_inventory,
)
from embercade.runtime import (
    ProjectRuntime,
    emulator_provider_config,
    executable_config,
    load_config,
)
from embercade.setup_flow import SetupError, choose_source_directory, configure, interactive_setup
from embercade.steam import SteamError, offer_integration
from embercade.ui_data import build_ui_data
from embercade.xemu import XemuRuntimeError, inspect_xemu_files, prepare_xemu_files, prepare_xemu_files_from, xemu_source_environment
from embercade.version import __version__


def _print_provider_import(result, *, verbose: bool = False, label: str = "Xenia Edge") -> None:
    if result.ambiguous:
        print(f"{label}: multiple different AppImages found; nothing imported.")
        print("Choose a folder containing only the intended build and run setup again.")
        print("Candidates: " + ", ".join(result.ambiguous))
    elif result.conflicts:
        print(f"{label}: different or damaged managed file already exists; kept unchanged.")
        print("No replacement or backup was created. Inspect it with 'embercade doctor --verbose'.")
        print("To replace it, explicitly move the old managed AppImage to a safe location, then reimport.")
    elif result.imported:
        print(f"{label}: imported; your source file was not changed.")
    elif result.present:
        print(f"{label}: already managed and identical; existing copy reused.")
    elif not result.found:
        print("AppImages: no files found in the selected folder.")
    else:
        print("AppImages: no valid supported provider found; nothing imported.")
    if result.skipped:
        print(f"AppImages ignored or invalid: {len(result.skipped)}.")
        if not verbose:
            for detail in result.skipped[:5]:
                name, _, reason = detail.partition(": ")
                state = "ignored (unsupported)" if reason.startswith("unsupported provider") else (
                    "not verified (inspection tool unavailable)" if "cannot inspect AppImage identity" in reason
                    else "invalid or unreadable"
                )
                print(f"  {name}: {state}")
            if len(result.skipped) > 5:
                print("  Further details: embercade setup --verbose")
    if verbose:
        for detail in result.skipped:
            print(f"  {detail}")
        for path in result.imported_paths:
            print(f"  Managed Xenia Edge: {path}")
        for name in result.conflicts:
            print(f"  Kept managed file: {name}")


def _default_config_path(paths: EmbercadePaths) -> Path:
    return paths.config / "embercade.toml"


def _project_root() -> Path:
    return Path(os.environ.get("EMBERCADE_PROJECT_ROOT", Path(__file__).resolve().parents[2]))


def _diagnostic_root(project_root: Path, paths: EmbercadePaths) -> Path:
    """Production reports are user state; development keeps its .work outputs."""
    return paths.state / "diagnostics" if os.environ.get("EMBERCADE_PREFIX") else project_root / ".work"


def _project_runtime(project_root: Path) -> ProjectRuntime:
    configured = os.environ.get("EMBERCADE_RUNTIME_ROOT")
    if configured:
        return ProjectRuntime(project_root, Path(configured).expanduser().absolute())
    return ProjectRuntime.for_application(project_root)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="embercade")
    parser.add_argument("--version", action="version", version=f"Embercade {__version__}")
    parser.add_argument("--config", type=Path, help="TOML configuration file")
    subparsers = parser.add_subparsers(dest="command")
    start = subparsers.add_parser("start", help="start the installed Embercade frontend")
    start.add_argument("--windowed", action="store_true", help="start ES in a desktop window")
    doctor = subparsers.add_parser("doctor", help="check Embercade setup")
    doctor.add_argument("--verbose", action="store_true", help="show technical diagnostics and paths")
    bootstrap = subparsers.add_parser(
        "bootstrap", help="optionally install known Arch/CachyOS/Garuda host packages"
    )
    bootstrap.add_argument(
        "--dry-run", action="store_true", help="print the package plan without sudo"
    )
    bootstrap.add_argument("--verbose", action="store_true", help="show package names and commands")
    bootstrap.add_argument("--language", choices=("de", "en"), help="installer message language")
    bootstrap.add_argument("--progress", type=Path, help=argparse.SUPPRESS)
    installer = subparsers.add_parser("installer", help="installer preferences and structured checks")
    installer.add_argument("action", choices=("language", "controller", "status", "firmware", "xbox-status", "xbox-init", "xbox-import", "xbox-edit", "desktop"))
    installer.add_argument("--language", choices=("de", "en"))
    installer.add_argument("--exit-hotkey", choices=("back-start", "guide-start"))
    installer.add_argument("--eeprom", type=Path)
    installer.add_argument("--replace-eeprom", action="store_true")
    installer.add_argument("--xbox-language", choices=("keep", "en", "de"), default="keep")
    installer.add_argument("--region", choices=("keep", "north-america", "japan", "europe"), default="keep")
    installer.add_argument("--video", choices=("keep", "ntsc-m", "ntsc-j", "pal"), default="keep")
    installer.add_argument("--pup", type=Path)
    installer.add_argument("--download", action="store_true")
    installer.add_argument("--yes", action="store_true", help="explicit firmware download consent")
    installer.add_argument("--no-menu", action="store_true")
    installer.add_argument("--shortcut", action="store_true")
    installer.add_argument("--original-image", action="store_true")
    host_install = subparsers.add_parser("host-install", help="private graphical installer terminal worker")
    host_install.add_argument("--result", type=Path, required=True)
    host_install.add_argument("--language", choices=("de", "en"), required=True)
    setup = subparsers.add_parser("setup", help="configure ROM, BIOS and optional provider paths")
    setup.add_argument("--roms", help="existing readable ROM directory")
    setup.add_argument("--bios", help="existing readable BIOS directory")
    setup.add_argument("--xenia-edge", help="optional existing Xenia Edge executable")
    setup.add_argument("--cores-from", type=Path, help="import all valid Libretro cores from this directory")
    setup.add_argument("--providers-from", type=Path, help="import known AppImages from this directory")
    setup.add_argument("--shadps4-from", type=Path, help="copy your optional shadPS4 AppImage or select a folder with one distinct build")
    setup.add_argument("--ppsspp-assets-from", type=Path, help="use complete user-provided PPSSPP assets read-only")
    setup.add_argument("--xemu-files-from", type=Path, help="prepare isolated Xemu working files from this directory")
    setup.add_argument("--verbose", action="store_true", help="show file paths and import details")
    setup.add_argument(
        "--exit-hotkey",
        choices=("back-start", "guide-start"),
        help="controller chord used to leave emulators",
    )
    subparsers.add_parser("wizard", help="open the graphical first-run setup")
    install = subparsers.add_parser("install", help=argparse.SUPPRESS)
    install.add_argument("--payload", required=True, type=Path)
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--no-setup", action="store_true")
    steam = subparsers.add_parser("steam", help="optionally register the installed launcher and artwork in Steam")
    steam.add_argument("--profile", type=Path, help="existing Steam userdata/<account>/config directory")
    steam.add_argument("--yes", action="store_true", help="explicitly approve Steam registration")
    steam.add_argument("--dry-run", action="store_true", help="check the plan without changing Steam data")
    steam.add_argument("--replace-existing", action="store_true", help="explicitly switch the existing Embercade shortcut between classic and AppImage, retaining its identity")
    uninstall = subparsers.add_parser("uninstall", help="remove the user-local Embercade application")
    uninstall.add_argument("--dry-run", action="store_true")
    uninstall.add_argument("--purge", action="store_true")
    uninstall.add_argument("--yes", action="store_true", help="confirm destructive --purge")
    inventory = subparsers.add_parser(
        "core-inventory", help="write a read-only host/Batocera Libretro core inventory"
    )
    inventory.add_argument("--output", type=Path)
    coverage = subparsers.add_parser("system-coverage", help="check every pinned classical system without starting games")
    coverage.add_argument("--output", required=True, type=Path)
    rom_inventory = subparsers.add_parser(
        "rom-inventory", help="scan ROM filenames and filesystem metadata once"
    )
    rom_inventory.add_argument("--systems-config", required=True, type=Path)
    rom_inventory.add_argument("--output", type=Path)
    rom_inventory.add_argument("--documentation", type=Path)
    rom_inventory.add_argument(
        "--alias",
        action="append",
        default=[],
        metavar="DIRECTORY=SYSTEM",
        help="explicit top-level directory alias",
    )
    rom_inventory.add_argument(
        "--ambiguous",
        action="append",
        default=[],
        metavar="DIRECTORY=SYSTEM,SYSTEM",
        help="explicit ambiguous top-level directory mapping",
    )
    bios_inventory = subparsers.add_parser(
        "bios-inventory", help="inventory BIOS_ROOT against pinned Batocera metadata"
    )
    bios_inventory.add_argument("--batocera-repository", type=Path)
    bios_inventory.add_argument("--rom-inventory", type=Path)
    bios_inventory.add_argument("--output", type=Path)
    bios_inventory.add_argument("--documentation", type=Path)
    compatibility = subparsers.add_parser(
        "compatibility-matrix",
        help="combine existing inventories into the host-specific Embercade 0.1 matrix",
    )
    compatibility.add_argument("--rom-inventory", type=Path)
    compatibility.add_argument("--bios-inventory", type=Path)
    compatibility.add_argument("--core-inventory", type=Path)
    compatibility.add_argument("--libretro-dry-runs", type=Path)
    compatibility.add_argument("--dolphin-dry-runs", type=Path)
    compatibility.add_argument("--output", type=Path)
    compatibility.add_argument("--documentation", type=Path)
    libretro_dry_runs = subparsers.add_parser(
        "libretro-dry-runs",
        help="verify generic Libretro launch plans without starting RetroArch",
    )
    libretro_dry_runs.add_argument(
        "--rom",
        action="append",
        required=True,
        metavar="SYSTEM=PATH",
        help="one explicit readable ROM path per system",
    )
    libretro_dry_runs.add_argument("--output", type=Path)
    dolphin_dry_run = subparsers.add_parser(
        "dolphin-dry-run",
        help="verify the prepared Wii Dolphin route without starting Dolphin",
    )
    dolphin_dry_run.add_argument("--rom", required=True, type=Path)
    dolphin_dry_run.add_argument("--output", type=Path)
    launch = subparsers.add_parser("launch", help="launch a game through the desktop Batocera runtime")
    launch.add_argument("--system", required=True)
    launch.add_argument("--rom", required=True, type=Path)
    launch.add_argument("--dry-run", action="store_true", help="generate config and print the emulator command")
    launch.add_argument(
        "--no-controller",
        action="store_true",
        help="retain the controllerless diagnostic path",
    )
    controller_info = subparsers.add_parser(
        "controller-info", help="inspect live SDL2 controller player slots"
    )
    controller_info.add_argument("--device-path-only", action="store_true")
    controller_prepare = subparsers.add_parser(
        "controller-prepare", help="generate exact ES input entries from Batocera's database"
    )
    controller_prepare.add_argument("--database", required=True, type=Path)
    controller_prepare.add_argument("--output", required=True, type=Path, action="append")
    policy_env = subparsers.add_parser(
        "policy-env", help="emit the validated desktop frontend policy environment"
    )
    policy_env.add_argument("--policy", required=True, type=Path)
    ui_build = subparsers.add_parser(
        "ui-build", help="generate desktop-filtered Batocera frontend data"
    )
    ui_build.add_argument("--batocera-source", required=True, type=Path)
    ui_build.add_argument("--defaults", required=True, type=Path)
    ui_build.add_argument("--output", required=True, type=Path)
    ui_build.add_argument("--rom-path", required=True, type=Path)
    ui_build.add_argument("--launch-command", required=True, type=Path)
    ui_build.add_argument("--gamecube-rom-path", type=Path)
    ui_build.add_argument("--gamecube-launch-command", type=Path)
    ui_build.add_argument("--wii-rom-path", type=Path)
    ui_build.add_argument("--wii-launch-command", type=Path)
    ui_build.add_argument("--xbox-rom-path", type=Path)
    ui_build.add_argument("--xbox-launch-command", type=Path)
    ui_build.add_argument("--ps2-rom-path", type=Path)
    ui_build.add_argument("--ps2-launch-command", type=Path)
    ui_build.add_argument("--ps3-rom-path", type=Path)
    ui_build.add_argument("--ps3-launch-command", type=Path)
    ui_build.add_argument(
        "--libretro-system",
        action="append",
        default=[],
        metavar="SYSTEM=ROM_DIRECTORY",
    )
    ui_build.add_argument("--libretro-launch-command", type=Path)
    ui_build.add_argument(
        "--external-system",
        action="append",
        default=[],
        metavar="SYSTEM=ROM_DIRECTORY",
    )
    ui_build.add_argument("--external-launch-command", type=Path)
    return parser


def _systems_config(project_root: Path) -> Path:
    installed = project_root / "resources" / "emulationstation" / "es_systems.cfg"
    if installed.is_file():
        return installed
    return (
        project_root
        / ".work"
        / "stage"
        / "share"
        / "embercade"
        / "resources"
        / "emulationstation"
        / "es_systems.cfg"
    )


def _assess_host(
    paths: EmbercadePaths,
    config: dict[str, object],
    project_root: Path,
) -> HostAssessment:
    resolver = ExecutableResolver(
        executable_config(config),
        providers=emulator_provider_config(config),
        environment=os.environ,
    )
    core_resolver = LibretroCoreResolver.from_host(config, os.environ)
    assessment = assess_host(
        resolver=resolver,
        core_resolver=core_resolver,
        environment=os.environ,
        rom_root=paths.rom_root,
        systems_config=_systems_config(project_root),
        default_config=project_root / "resources" / "defaults" / "batocera.conf",
        user_config=paths.batocera_conf,
    )
    firmware = inspect_rpcs3_firmware(paths, config, os.environ)
    xemu = inspect_xemu_files(paths, os.environ)
    return replace(
        assessment,
        rpcs3_firmware=("OK" if firmware.installed else "NOT INSTALLED"),
        xemu_firmware=("OK" if xemu.firmware_ready else "MISSING"),
        xemu_eeprom=("OK" if xemu.eeprom_ready else "CREATED ON FIRST START"),
        xemu_hdd=("OK" if xemu.hdd_ready else "MISSING"),
        opera_bios=(inspect_opera_bios(paths.bios_root).status
                    if (paths.rom_root / "3do").is_dir() else None),
    )


def _suggest_core_source(resolver: LibretroCoreResolver) -> Path | None:
    """Prefer a complete existing collection over a small system package dir."""
    best: Path | None = None
    best_count = 0
    for entry in resolver.core_directories:
        directory = entry.path
        if entry.source == "embercade-managed" or not directory.is_dir():
            continue
        try:
            count = sum(
                path.is_file() and not path.is_symlink()
                for path in directory.glob("*_libretro.so")
            )
        except OSError:
            continue
        if count > best_count:
            best, best_count = directory, count
    return best


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        targets = []
        for name in ("config", "output", "documentation", "result"):
            value = getattr(args, name, None)
            targets.extend([value] if isinstance(value, Path) else
                           [item for item in value if isinstance(item, Path)] if isinstance(value, list) else [])
        EmbercadePaths.from_environment().validate_application_boundary(os.environ, targets=targets)
    except ValueError as error:
        parser.error(str(error))
    if args.command == "ui-build" and os.environ.get("EMBERCADE_PREFIX"):
        parser.error("Frontend building is a development command; run it from the source checkout, not the read-only application")

    if args.command == "install":
        try:
            result = install_user(args.payload, dry_run=args.dry_run)
        except (InstallationError, OSError) as error:
            parser.error(f"installation/update stopped: {error}\nNo user data was purged. Run 'embercade doctor --verbose' if an existing installation needs attention.")
        print_operations(result)
        if args.dry_run:
            print("Dry run complete: no files changed.")
        elif result.mode == "ALREADY UP TO DATE":
            print("Already up to date. No files changed.")
        else:
            print("Application files installed and verified. User data was preserved.")
            print("Host emulator dependencies have not been changed.")
            print("Next: embercade doctor" if result.mode == "UPDATE/REINSTALL" else "Next: embercade wizard")
            if hasattr(result, "paths"):
                for line in launcher_path_guidance(result.paths):
                    print(line)
        if not args.dry_run and not args.no_setup and result.mode == "NEW INSTALL":
            if sys.stdin.isatty():
                if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"):
                    return main(["wizard"])
                return main(["setup"])
            else:
                print("Run 'embercade wizard' in a desktop session to finish setup.")
        return 0

    if args.command == "uninstall":
        try:
            result = uninstall_user(
                dry_run=args.dry_run,
                purge=args.purge,
                purge_confirmed=args.yes,
            )
        except (InstallationError, OSError, ValueError) as error:
            parser.error(str(error))
        print_operations(result)
        if not args.dry_run and not args.purge:
            print("User data was kept.")
        return 0

    if args.command == "steam":
        if not sys.stdin.isatty() and not (args.yes or args.dry_run):
            print("Steam integration needs confirmation; use --yes or --dry-run.")
            return 2
        try:
            offer_integration(
                output=sys.stdout, input_function=input,
                profile=args.profile.expanduser().resolve() if args.profile else None,
                accepted=args.yes or args.dry_run, dry_run=args.dry_run,
                interactive=sys.stdin.isatty(), strict=True,
                replace_existing=args.replace_existing,
            )
        except SteamError:
            return 2
        return 0

    base_paths = EmbercadePaths.from_environment()
    config_path = args.config if args.config is not None else _default_config_path(base_paths)
    if args.command == "wizard":
        if not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
            print("Graphical setup needs an active desktop session. The terminal setup remains available: embercade setup", file=sys.stderr)
            return 2
        environment = os.environ.copy()
        # The pinned runtime deliberately excludes host GUI bindings.  The
        # lightweight GTK window runs in host Python; all backend commands go
        # back through this exact staged/installed Embercade launcher.
        try:
            result = subprocess.run(
                ["/usr/bin/python", "-B", "-m", "embercade.first_run_ui",
                 "--config", str(config_path)],
                env=environment, check=False,
            )
        except OSError as error:
            print(f"Graphical setup could not open: {error}. Use 'embercade setup' in a terminal.", file=sys.stderr)
            return 2
        return result.returncode
    if args.command == "setup":
        try:
            if (args.roms is None) != (args.bios is None):
                parser.error("--roms and --bios must be supplied together")
            if args.xemu_files_from is not None:
                xemu_source_environment(args.xemu_files_from, os.environ)
            if args.roms is not None:
                setup_result = configure(
                    config_path,
                    roms_value=args.roms,
                    bios_value=args.bios,
                    xenia_value=args.xenia_edge,
                    exit_hotkey=args.exit_hotkey,
                    ppsspp_assets_value=(str(args.ppsspp_assets_from) if args.ppsspp_assets_from else None),
                )
            else:
                setup_result = interactive_setup(config_path, input_function=input, output=sys.stdout)
            configured = load_config(config_path)
            configured_paths = EmbercadePaths.from_environment(config=configured)
            shadps4_from = args.shadps4_from
            if args.roms is None and sys.stdin.isatty() and shadps4_from is None and "shadps4" not in emulator_provider_config(configured):
                answer = input("Optional shadPS4 AppImage file (Enter to skip): ").strip()
                shadps4_from = Path(answer).expanduser() if answer else None
            if shadps4_from is not None:
                result = import_providers(shadps4_from, configured_paths.data, provider="shadps4")
                _print_provider_import(result, verbose=args.verbose, label="shadPS4")
                if result.imported_paths:
                    selected, = result.imported_paths
                    if executable_config(configured).get("shadps4"):
                        print("shadPS4: explicit override retained; imported copy not selected.")
                    else:
                        configure(config_path, roms_value=str(setup_result.roms),
                                  bios_value=str(setup_result.bios),
                                  shadps4_value=str(selected), exit_hotkey=setup_result.exit_hotkey)
                        configured = load_config(config_path)
            if args.xemu_files_from is not None:
                prepare_xemu_files_from(configured_paths, args.xemu_files_from, os.environ)
                print("Xemu system files: isolated working copies ready; source files unchanged.")
            cores_from = args.cores_from
            providers_from = args.providers_from
            if args.roms is None and sys.stdin.isatty():
                if cores_from is None:
                    resolver = LibretroCoreResolver.from_host(configured, os.environ)
                    suggested = _suggest_core_source(resolver)
                    cores_from = choose_source_directory(
                        label="RetroArch core",
                        suggested=suggested,
                        question="Do you have RetroArch/Libretro cores to import?",
                        input_function=input,
                        output=sys.stdout,
                    )
                if providers_from is None:
                    suggested_provider = setup_result.xenia_edge.parent if setup_result.xenia_edge else None
                    if suggested_provider is not None and suggested_provider.is_relative_to(configured_paths.data / "providers"):
                        suggested_provider = None
                    providers_from = choose_source_directory(
                        label="Provider/AppImage",
                        suggested=suggested_provider,
                        question="Do you have emulator AppImages/providers to import?",
                        input_function=input,
                        output=sys.stdout,
                    )
            if cores_from is not None:
                result = import_cores(cores_from, configured_paths.data)
                print(
                    f"RetroArch cores: found {result.found}, valid {result.valid}, "
                    f"imported {result.imported}, already present {result.present}, "
                    f"skipped {len(result.skipped) + len(result.conflicts)}."
                )
                if args.verbose:
                    for detail in (*result.skipped, *(f"{name}: conflicting managed file" for name in result.conflicts)):
                        print(f"  {detail}")
            if providers_from is not None:
                result = import_providers(providers_from, configured_paths.data)
                _print_provider_import(result, verbose=args.verbose)
                if result.imported_paths:
                    selected, = result.imported_paths  # importer guarantees one identity
                    if executable_config(configured).get("xenia-edge"):
                        print("Xenia Edge: explicit executable override kept; the imported copy does not replace that selection.")
                    else:
                        setup_result = configure(
                            config_path,
                            roms_value=str(setup_result.roms),
                            bios_value=str(setup_result.bios),
                            xenia_value=str(selected),
                            exit_hotkey=setup_result.exit_hotkey,
                        )
            else:
                print("AppImages: no import folder selected; existing provider settings kept.")
            configured = load_config(config_path)
            configured_paths = EmbercadePaths.from_environment(config=configured)
        except (EOFError, KeyboardInterrupt, OSError, ValueError, SetupError, ManagedImportError, XemuRuntimeError) as error:
            parser.error(str(error))
        print("Configuration saved. ROM and BIOS directories are ready.")
        if args.verbose:
            print(f"Configuration: {setup_result.config_path}")
            print(f"ROM root: {setup_result.roms}")
            print(f"BIOS root: {setup_result.bios}")
        if setup_result.provider_notice:
            print("Xenia Edge: existing provider needs attention; settings kept. Run 'embercade doctor --verbose'.")
            if args.verbose:
                print(f"  {setup_result.provider_notice}")
        elif setup_result.xenia_edge:
            print(f"Xenia Edge: ready" + (f" ({setup_result.xenia_edge})" if args.verbose else ""))
        else:
            print("Xenia Edge: optional, not configured")
        from embercade.exit_hotkey import EXIT_HOTKEYS
        print(f"Exit hotkey: {EXIT_HOTKEYS[setup_result.exit_hotkey].label}")
        try:
            assessment = _assess_host(configured_paths, configured, _project_root())
        except ValueError as error:
            parser.error(f"invalid Embercade configuration: {error}")
        print("")
        print("Checking Embercade setup...")
        missing_components = [
            status.requirement.label
            for status in assessment.requirements
            if not status.installed
        ]
        missing_components.extend(
            f"Libretro core {status.core}"
            for status in assessment.cores
            if not status.installed
        )
        print(
            "Missing optional components: "
            + (", ".join(missing_components) if missing_components else "none")
        )
        if args.verbose:
            render_host_summary(assessment, sys.stdout, verbose=True)
        if assessment.distro.supports_automatic_install:
            if sys.stdin.isatty():
                answer = input("Run bootstrap now? [y/N] ").strip().casefold()
                if answer in {"y", "yes"}:
                    helper = AurHelper.detect()
                    plan = create_bootstrap_plan(assessment, aur_helper=helper)
                    result = run_bootstrap(
                        plan,
                        dry_run=False,
                        stream=sys.stdout,
                        aur_helper=helper,
                    )
                    if result:
                        return result
                    assessment = _assess_host(configured_paths, configured, _project_root())
            else:
                print("Optional next step: embercade bootstrap --dry-run")
        pup = existing_firmware_package(configured_paths.bios_root)
        firmware = inspect_rpcs3_firmware(configured_paths, configured, os.environ)
        if not firmware.installed and pup is None:
            print("RPCS3 firmware: not installed. Place your own PS3UPDAT.PUP in the selected BIOS folder, then run setup again.")
        if pup is not None and not firmware.installed:
            resolver = ExecutableResolver(
                executable_config(configured),
                providers=emulator_provider_config(configured),
                environment=os.environ,
            )
            try:
                rpcs3_binary = resolver.resolve("rpcs3").path
            except Exception:
                rpcs3_binary = None
            if rpcs3_binary is not None:
                print("RPCS3 needs its system firmware before PS3 games can run.")
                if args.verbose:
                    print(f"Firmware package: {pup}")
                if sys.stdin.isatty() and input("Open RPCS3 to install your firmware? [y/N] ").strip().casefold() in {"y", "yes"}:
                    print("In RPCS3 choose File → Install Firmware, select your PS3UPDAT.PUP, then close RPCS3.")
                    try:
                        status = open_firmware_installer(rpcs3_binary, configured_paths, configured, os.environ)
                    except OSError as error:
                        print(f"RPCS3 could not be opened: {error}")
                    else:
                        print("RPCS3 firmware: ready" if status.installed else "RPCS3 firmware: still not installed")
        if sys.stdin.isatty():
            offer_integration(output=sys.stdout, input_function=input)
            answer = input("Run doctor? [Y/n] ").strip().casefold()
            if answer not in {"n", "no"}:
                main(["--config", str(config_path), "doctor"])
            answer = input("Launch Embercade now? [Y/n] ").strip().casefold()
            if answer not in {"n", "no"}:
                return main(["--config", str(config_path), "start"])
        else:
            print("Next: embercade doctor")
            print("Then: embercade start")
        return 0

    try:
        config = load_config(config_path)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        if args.command in (None, "start") and (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
            return main(["--config", str(config_path), "wizard"])
        parser.error(f"invalid Embercade configuration {config_path}: {error}")
    paths = EmbercadePaths.from_environment(config=config)

    if args.command is None:
        args.command = "start"
        args.windowed = False

    if args.command == "host-install":
        from embercade.first_run import launcher_command
        from embercade.host_install import run_installation
        return run_installation(args.result,
            [*launcher_command(), "--config", str(config_path), "bootstrap", "--language", args.language,
             "--progress", str(args.result.with_name("progress.json"))],
            args.language)

    if args.command == "installer":
        from embercade.installer_preferences import save_exit_hotkey, save_language, status_report
        if args.action == "language":
            if args.language is None:
                parser.error("installer language requires --language")
            try:
                save_language(config_path, args.language)
            except (OSError, ValueError) as error:
                parser.error(str(error))
            return 0
        if args.action == "controller":
            if args.exit_hotkey is None:
                parser.error("installer controller requires --exit-hotkey")
            try:
                save_exit_hotkey(config_path, args.exit_hotkey)
            except (OSError, ValueError, SetupError) as error:
                parser.error(str(error))
            return 0
        if args.action == "status":
            assessment = _assess_host(paths, config, _project_root())
            plan = create_bootstrap_plan(assessment, aur_helper=AurHelper.detect())
            print(json.dumps(status_report(paths, config, assessment, plan, _project_root())))
            return 0
        from embercade.rpcs3 import prepare_rpcs3_firmware, Rpcs3RuntimeError
        try:
            if args.action == "desktop":
                from embercade.desktop_integration import integrate
                print(json.dumps(integrate(os.environ, menu=not args.no_menu,
                    shortcut=args.shortcut, local_image=not args.original_image)))
                return 0
            resolver = ExecutableResolver(executable_config(config), providers=emulator_provider_config(config),
                                          environment=os.environ)
            if args.action.startswith("xbox-"):
                from embercade import xbox_eeprom as eeprom
                from embercade.xemu import isolated_xemu_files
                if args.action == "xbox-status":
                    target = isolated_xemu_files(paths).eeprom
                    print(json.dumps(eeprom.inspect(eeprom.read(target)) if target.exists() else {"missing": True}))
                    return 0
                executable = resolver.resolve("xemu").path
                if args.action == "xbox-init":
                    print(json.dumps(eeprom.initialize(paths, executable, dict(os.environ))))
                    return 0
                with eeprom.transaction(paths, executable) as target:
                    if args.action == "xbox-import":
                        if args.eeprom is None: raise ValueError("Select your EEPROM file")
                        data = eeprom.read(args.eeprom.expanduser().absolute())
                        backup = eeprom.save(target, data, replace=args.replace_eeprom)
                    else:
                        data = eeprom.edit(eeprom.read(target), language=args.xbox_language,
                                           region=args.region, video=args.video)
                        backup = eeprom.save(target, data, replace=True)
                    print(json.dumps(dict(eeprom.inspect(data), backup=backup)))
                return 0
            if args.download or args.pup:
                from embercade.ps3_firmware import download, install
                if args.download and (not args.yes or args.pup):
                    raise ValueError("Official firmware download requires explicit consent and no selected PUP")
                executable = resolver.resolve("rpcs3").path
                pup = download(paths) if args.download else args.pup.expanduser().absolute()
                print(json.dumps(dict(version=install(executable, paths, config, os.environ, pup))))
            elif inspect_rpcs3_firmware(paths, config, os.environ).installed:
                prepare_rpcs3_firmware(paths, config, os.environ)
            else:
                status = open_firmware_installer(resolver.resolve("rpcs3").path, paths, config, os.environ)
                from embercade.rpcs3 import firmware_version
                if not firmware_version(paths.emulator_configs / "rpcs3"):
                    return 1
        except (OSError, ValueError, Rpcs3RuntimeError, ExecutableResolutionError, InstallationError) as error:
            parser.error(str(error))
        return 0

    if args.command == "bootstrap":
        try:
            from embercade.host_install import publish_progress
            announce = (lambda phase: publish_progress(args.progress, phase)) if args.progress else None
            if announce: announce("checking")
            assessment = _assess_host(paths, config, _project_root())
            helper = AurHelper.detect()
            plan = create_bootstrap_plan(assessment, aur_helper=helper)
            return run_bootstrap(
                plan,
                dry_run=args.dry_run,
                stream=sys.stdout,
                aur_helper=helper,
                verbose=args.verbose,
                language=args.language,
                progress=announce,
            )
        except (EOFError, KeyboardInterrupt):
            from embercade.i18n import Translator
            print(Translator(args.language or "en")("Host installation was cancelled."))
            return 130
        except (OSError, ValueError) as error:
            if args.language:
                from embercade.i18n import Translator
                print(Translator(args.language)("Host status could not be checked. Please try again."), file=sys.stderr)
                return 2
            parser.error(str(error))

    if args.command == "start":
        if any(not item.ok for item in paths.validate_collection_roots()):
            if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"):
                return main(["--config", str(config_path), "wizard"])
            print("Embercade is not configured yet.", file=sys.stderr)
            print("Run: embercade setup", file=sys.stderr)
            return 2
        layout = ProductionLayout.from_environment()
        if layout is None:
            parser.error(
                "production prefix is unknown; run the staged/installed bin/embercade entry point"
            )
        try:
            return run_production(
                layout,
                paths,
                config,
                frontend_arguments=("--windowed",) if args.windowed else (),
            )
        except (OSError, ProductionError, ValueError) as error:
            parser.error(str(error))

    if args.command == "doctor":
        try:
            production_layout = ProductionLayout.from_environment()
            resolver = ExecutableResolver(
                executable_config(config),
                providers=emulator_provider_config(config),
                environment=os.environ,
            )
            project_root = _project_root()
            catalog = load_batocera_catalog(
                project_root / "resources" / "libretro" / "batocera-44-cores.txt"
            )
            core_resolver = LibretroCoreResolver.from_host(config, os.environ)
            assessment = _assess_host(paths, config, project_root)
        except ValueError as error:
            parser.error(f"invalid Embercade configuration: {error}")
        detail = StringIO() if not args.verbose else None
        result = report(
            paths,
            resolver,
            runtime=_project_runtime(project_root),
            core_resolver=core_resolver,
            core_catalog=catalog,
            production_layout=production_layout,
            host_assessment=assessment,
            config=config,
            stream=detail,
        )
        if args.verbose:
            return result
        print("Checking Embercade setup...")
        for item in paths.validate_collection_roots():
            print(f"{'✓' if item.ok else '!'} {item.label}: {'ready' if item.ok else item.status.lower()}")
        cores_ready = sum(item.installed for item in assessment.cores)
        print(f"{'✓' if cores_ready == len(assessment.cores) else '!'} RetroArch cores: {cores_ready}/{len(assessment.cores)} needed for this collection")
        diagnosis = assessment.xenia_provider
        ready = diagnosis.available if diagnosis else bool(assessment.xenia_edge)
        summary = diagnosis.summary if diagnosis else 'ready' if ready else 'optional, not configured'
        print(f"{'✓' if ready else '!'} Xenia provider: {summary}")
        if assessment.shadps4_provider is not None:
            diagnosis = assessment.shadps4_provider
            print(f"{'✓' if diagnosis.available else '!'} shadPS4: {diagnosis.summary}")
        for item in assessment.requirements:
            if item.requirement.key in {"pcsx2", "rpcs3", "xemu"}:
                print(f"{'✓' if item.installed else '!'} {item.requirement.label}: {'ready' if item.installed else 'not available'}")
        print(f"{'✓' if assessment.rpcs3_firmware == 'OK' else '!'} RPCS3 firmware: {'ready' if assessment.rpcs3_firmware == 'OK' else 'setup required'}")
        print(f"{'✓' if assessment.xemu_firmware == 'OK' and assessment.xemu_hdd == 'OK' else '!'} Xemu system files: {'ready' if assessment.xemu_firmware == 'OK' and assessment.xemu_hdd == 'OK' else 'setup required'}")
        if assessment.opera_bios is not None:
            print(f"{'✓' if assessment.opera_bios == 'OK' else '!'} 3DO BIOS: {assessment.opera_bios}")
        from embercade.ppsspp import PpssppAssetsError, resolve_ppsspp_assets
        try:
            resolve_ppsspp_assets(paths, config, os.environ)
        except PpssppAssetsError:
            print("! PPSSPP assets: PSP setup required")
        else:
            print("✓ PPSSPP assets: ready")
        if result:
            print("! Some required checks need attention. Run 'embercade doctor --verbose' for details.")
        return result
    if args.command == "core-inventory":
        project_root = _project_root()
        catalog = load_batocera_catalog(
            project_root / "resources" / "libretro" / "batocera-44-cores.txt"
        )
        core_resolver = LibretroCoreResolver.from_host(config, os.environ)
        output = args.output or _diagnostic_root(project_root, paths) / "core-inventory.json"
        inventory_data = core_resolver.inventory(catalog)
        write_inventory(output, inventory_data)
        summary = inventory_data["summary"]
        print(f"Wrote {output.absolute()}")
        print(
            f"Installed: {summary['installed_unique']} unique; "
            f"Batocera 44: {summary['batocera_found']}/{summary['batocera_catalog']} found"
        )
        return 0
    if args.command == "rom-inventory":
        project_root = _project_root()
        aliases: dict[str, str] = {}
        for value in args.alias:
            directory, separator, system = value.partition("=")
            if not separator or not directory or not system:
                parser.error(f"invalid --alias {value!r}; expected DIRECTORY=SYSTEM")
            aliases[directory] = system
        ambiguous_aliases: dict[str, tuple[str, ...]] = {}
        for value in args.ambiguous:
            directory, separator, systems_value = value.partition("=")
            candidates = tuple(item for item in systems_value.split(",") if item)
            if not separator or not directory or not candidates:
                parser.error(
                    f"invalid --ambiguous {value!r}; expected DIRECTORY=SYSTEM,SYSTEM"
                )
            ambiguous_aliases[directory] = candidates
        try:
            systems = load_batocera_systems(args.systems_config)
            inventory_data = inventory_rom_root(
                paths.rom_root,
                systems,
                aliases=aliases,
                ambiguous_aliases=ambiguous_aliases,
            )
            output = args.output or _diagnostic_root(project_root, paths) / "rom-inventory.json"
            documentation = (
                args.documentation or _diagnostic_root(project_root, paths) / "reports" / "rom-inventory.md"
            )
            write_rom_inventory(output, inventory_data)
            write_rom_documentation(documentation, inventory_data)
        except (OSError, RomInventoryError) as error:
            parser.error(str(error))
        summary = inventory_data["summary"]
        print(f"Wrote {output.absolute()}")
        print(f"Wrote {documentation.absolute()}")
        print(
            f"Top-level: {summary['top_level_directories']}; exact: {summary['exact']}; "
            f"aliases: {summary['alias']}; ambiguous: {summary['ambiguous']}; "
            f"unknown: {summary['unknown']}"
        )
        return 0
    if args.command == "bios-inventory":
        project_root = _project_root()
        repository = args.batocera_repository or project_root.parent / "Batocera"
        rom_inventory_path = (
            args.rom_inventory or _diagnostic_root(project_root, paths) / "rom-inventory.json"
        )
        try:
            source = read_pinned_batocera_source(repository)
            requirements = load_batocera_bios_requirements(source)
            rom_inventory_data = json.loads(
                rom_inventory_path.read_text(encoding="utf-8")
            )
            inventory_data = build_bios_inventory(
                paths.bios_root, requirements, rom_inventory_data
            )
            output = args.output or _diagnostic_root(project_root, paths) / "bios-inventory.json"
            documentation = (
                args.documentation or _diagnostic_root(project_root, paths) / "reports" / "bios-inventory.md"
            )
            write_bios_inventory(output, inventory_data)
            write_bios_documentation(documentation, inventory_data)
        except (OSError, json.JSONDecodeError, BiosInventoryError) as error:
            parser.error(str(error))
        summary = inventory_data["summary"]
        print(f"Wrote {output.absolute()}")
        print(f"Wrote {documentation.absolute()}")
        print(
            f"Requirements: {summary['requirements_total']}; "
            f"hash matches: {summary['hash_match']}; "
            f"missing: {summary['missing']}; mismatches: {summary['hash_mismatch']}"
        )
        return 0
    if args.command == "compatibility-matrix":
        project_root = _project_root()
        rom_path = args.rom_inventory or _diagnostic_root(project_root, paths) / "rom-inventory.json"
        bios_path = args.bios_inventory or _diagnostic_root(project_root, paths) / "bios-inventory.json"
        core_path = args.core_inventory or _diagnostic_root(project_root, paths) / "core-inventory.json"
        dry_runs_path = (
            args.libretro_dry_runs or _diagnostic_root(project_root, paths) / "libretro-dry-runs.json"
        )
        dolphin_dry_runs_path = (
            args.dolphin_dry_runs or _diagnostic_root(project_root, paths) / "dolphin-dry-runs.json"
        )
        output = args.output or _diagnostic_root(project_root, paths) / "compatibility-0.1.json"
        documentation = (
            args.documentation
            or _diagnostic_root(project_root, paths) / "reports" / "compatibility-0.1.md"
        )
        try:
            inventory_data = build_compatibility_matrix(
                json.loads(rom_path.read_text(encoding="utf-8")),
                json.loads(bios_path.read_text(encoding="utf-8")),
                json.loads(core_path.read_text(encoding="utf-8")),
                libretro_dry_runs=(
                    json.loads(dry_runs_path.read_text(encoding="utf-8"))
                    if dry_runs_path.is_file()
                    else None
                ),
                dolphin_dry_runs=(
                    json.loads(dolphin_dry_runs_path.read_text(encoding="utf-8"))
                    if dolphin_dry_runs_path.is_file()
                    else None
                ),
                environment=os.environ,
                configured_executables=executable_config(config),
                emulator_providers=emulator_provider_config(config),
            )
            write_compatibility_matrix(output, inventory_data)
            write_compatibility_documentation(documentation, inventory_data)
        except (OSError, json.JSONDecodeError, CompatibilityError) as error:
            parser.error(str(error))
        summary = inventory_data["summary"]
        print(f"Wrote {output.absolute()}")
        print(f"Wrote {documentation.absolute()}")
        print(
            f"Systems: {summary['rom_relevant_systems']}; READY: {summary['ready']}; "
            f"ports missing: {summary['embercade_port_missing']}; "
            f"emulators missing: {summary['emulator_missing']}"
        )
        return 0
    if args.command == "system-coverage":
        from embercade.system_coverage import collect_coverage, structure_inputs_digest
        project_root = _project_root()
        catalog_root = project_root / "resources/emulationstation"
        proof_path = catalog_root / "system-structure.json"
        if not (catalog_root / "systems-catalog.xml").is_file():
            catalog_root = project_root / ".work/system-catalog/output"
            proof_path = project_root / ".work/reports/system-structure.json"
        try:
            structure = json.loads(proof_path.read_text())
            if "source_digest" in structure:
                if structure["source_digest"] != structure_inputs_digest(project_root):
                    raise ValueError("Structural checks are stale; rerun integration tests")
                structure = structure["systems"]
            result = collect_coverage(catalog_root / "systems-catalog.xml"
                                      if (catalog_root / "systems-catalog.xml").exists()
                                      else catalog_root / "es_systems.cfg",
                                      catalog_root / "bios-requirements.json", paths=paths,
                                      config=config, structural=structure)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print("Complete system coverage: " + "; ".join(f"{k}: {v}" for k, v in result["summary"].items()))
        return 0
    if args.command == "libretro-dry-runs":
        project_root = _project_root()
        assignments: list[tuple[str, Path]] = []
        seen: set[str] = set()
        for value in args.rom:
            system, separator, rom_value = value.partition("=")
            if not separator or not system or not rom_value:
                parser.error(f"invalid --rom {value!r}; expected SYSTEM=PATH")
            if system in seen:
                parser.error(f"duplicate --rom system: {system}")
            seen.add(system)
            assignments.append((system, Path(rom_value)))
        try:
            prepare_launch_layout(paths, project_root)
            controller = require_player_one_controller(enumerate_sdl_game_controllers())
            write_es_input_override(
                controller,
                _project_runtime(project_root).share / "emulationstation" / "es_input.cfg",
                paths.emulationstation_config / "es_input.cfg",
            )
            host_profile = Path.home() / ".config" / "retroarch"
            before = snapshot_metadata(host_profile)
            rows = []
            for system, rom in assignments:
                plan = create_launch_plan(
                    system=system,
                    rom=rom,
                    paths=paths,
                    runtime=_project_runtime(project_root),
                    config=config,
                    environment=os.environ,
                    dry_run=True,
                    controller=controller,
                )
                rows.append(execute_libretro_dry_run(plan, paths))
            unchanged = before == snapshot_metadata(host_profile)
            if not unchanged:
                raise LibretroDryRunError("normal RetroArch host profile changed during dry runs")
            report_data = build_libretro_dry_run_report(
                rows,
                host_profile_unchanged=unchanged,
            )
            output = args.output or _diagnostic_root(project_root, paths) / "libretro-dry-runs.json"
            write_libretro_dry_run_report(output, report_data)
        except (
            ControllerUnavailable,
            LaunchError,
            LibretroDryRunError,
            OSError,
            ValueError,
        ) as error:
            parser.error(str(error))
        print(f"Wrote {output.absolute()}")
        print(f"Dry runs: {report_data['summary']['successful']}/{report_data['summary']['systems']}")
        return 0
    if args.command == "dolphin-dry-run":
        project_root = _project_root()
        try:
            prepare_launch_layout(paths, project_root)
            controller = require_player_one_controller(enumerate_sdl_game_controllers())
            write_es_input_override(
                controller,
                _project_runtime(project_root).share / "emulationstation" / "es_input.cfg",
                paths.emulationstation_config / "es_input.cfg",
            )
            host_profiles = (
                Path.home() / ".config" / "dolphin-emu",
                Path.home() / ".local" / "share" / "dolphin-emu",
                Path.home() / ".cache" / "dolphin-emu",
            )
            before = {path: snapshot_metadata(path) for path in host_profiles}
            plan = create_launch_plan(
                system="wii",
                rom=args.rom,
                paths=paths,
                runtime=_project_runtime(project_root),
                config=config,
                environment=os.environ,
                dry_run=True,
                controller=controller,
            )
            row = execute_dolphin_dry_run(plan, paths)
            unchanged = before == {path: snapshot_metadata(path) for path in host_profiles}
            if not unchanged:
                raise DolphinDryRunError("normal Dolphin host profiles changed during dry run")
            report_data = build_dolphin_dry_run_report(
                row,
                host_profiles_unchanged=unchanged,
            )
            output = args.output or _diagnostic_root(project_root, paths) / "dolphin-dry-runs.json"
            write_dolphin_dry_run_report(output, report_data)
        except (
            ControllerUnavailable,
            DolphinDryRunError,
            LaunchError,
            OSError,
            ValueError,
        ) as error:
            parser.error(str(error))
        print(f"Wrote {output.absolute()}")
        print("Wii Dolphin dry run: 1/1")
        return 0
    if args.command == "controller-info":
        try:
            controllers = resolve_player_controllers(
                enumerate_sdl_game_controllers(),
                es_settings=paths.emulationstation_config / "es_settings.cfg",
            )
            if not controllers:
                raise ControllerUnavailable("No connected SDL2 GameController")
        except ControllerUnavailable as error:
            parser.error(str(error))
        if args.device_path_only:
            print(controllers[0].device_path)
        else:
            print(json.dumps([json.loads(device.as_json()) | {"player": slot}
                              for slot, device in enumerate(controllers, start=1)],
                             ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "controller-prepare":
        try:
            controllers = resolve_player_controllers(
                enumerate_sdl_game_controllers(),
                es_settings=paths.emulationstation_config / "es_settings.cfg",
            )
            if not controllers:
                raise ControllerUnavailable("No connected SDL2 GameController")
            for output in args.output:
                sources = write_es_input_overrides(controllers, args.database, output)
                source_by_identity = {}
                for controller, source in zip(dict.fromkeys(
                    (device.guid, device.name) for device in controllers), sources):
                    source_by_identity[controller] = source
                for slot, controller in enumerate(controllers, start=1):
                    source = source_by_identity[(controller.guid, controller.name)]
                    print(f"Prepared P{slot} {output} from {source.name} ({source.guid}) "
                          f"for {controller.name} ({controller.guid})")
        except ControllerUnavailable as error:
            parser.error(str(error))
        return 0
    if args.command == "policy-env":
        try:
            policy = DesktopPolicy.load(args.policy)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        for name, value in policy.frontend_environment().items():
            print(f"{name}={value}")
        return 0
    if args.command == "ui-build":
        libretro_systems: dict[str, Path] = {}
        for value in args.libretro_system:
            system, separator, rom_directory = value.partition("=")
            if not separator or not system or not rom_directory:
                parser.error(
                    f"invalid --libretro-system {value!r}; expected SYSTEM=ROM_DIRECTORY"
                )
            if system in libretro_systems:
                parser.error(f"duplicate --libretro-system: {system}")
            libretro_systems[system] = Path(rom_directory)
        if libretro_systems and args.libretro_launch_command is None:
            parser.error("--libretro-launch-command is required with --libretro-system")
        external_systems: dict[str, Path] = {}
        for value in args.external_system:
            system, separator, rom_directory = value.partition("=")
            if not separator or not system or not rom_directory:
                parser.error(
                    f"invalid --external-system {value!r}; expected SYSTEM=ROM_DIRECTORY"
                )
            if system in external_systems:
                parser.error(f"duplicate --external-system: {system}")
            external_systems[system] = Path(rom_directory)
        if external_systems and args.external_launch_command is None:
            parser.error("--external-launch-command is required with --external-system")
        try:
            systems, features = build_ui_data(
                batocera_source=args.batocera_source,
                defaults=args.defaults,
                output=args.output,
                rom_path=args.rom_path,
                launch_command=args.launch_command,
                gamecube_rom_path=args.gamecube_rom_path,
                gamecube_launch_command=args.gamecube_launch_command,
                wii_rom_path=args.wii_rom_path,
                wii_launch_command=args.wii_launch_command,
                xbox_rom_path=args.xbox_rom_path,
                xbox_launch_command=args.xbox_launch_command,
                ps2_rom_path=args.ps2_rom_path,
                ps2_launch_command=args.ps2_launch_command,
                ps3_rom_path=args.ps3_rom_path,
                ps3_launch_command=args.ps3_launch_command,
                libretro_systems=libretro_systems,
                libretro_launch_command=args.libretro_launch_command,
                external_systems=external_systems,
                external_launch_command=args.external_launch_command,
            )
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print(f"Generated {systems}")
        print(f"Generated {features}")
        return 0
    if args.command == "launch":
        project_root = _project_root()
        try:
            prepare_launch_layout(paths, project_root)
            if args.system == "xbox":
                prepare_xemu_files(paths, os.environ)
            if args.system == "ps3":
                prepare_rpcs3_firmware(paths, config, os.environ)
            controllers = ()
            if not args.no_controller:
                controllers = resolve_player_controllers(
                    enumerate_sdl_game_controllers(),
                    es_settings=paths.emulationstation_config / "es_settings.cfg",
                )
                if controllers:
                    write_es_input_overrides(
                        controllers,
                        _project_runtime(project_root).share / "emulationstation" / "es_input.cfg",
                        paths.emulationstation_config / "es_input.cfg",
                    )
            plan = create_launch_plan(
                system=args.system,
                rom=args.rom,
                paths=paths,
                runtime=_project_runtime(project_root),
                config=config,
                environment=os.environ,
                dry_run=args.dry_run,
                controllers=controllers,
            )
            return run_launch(plan)
        except (
            ControllerUnavailable,
            LaunchError,
            Pcsx2RuntimeError,
            Rpcs3RuntimeError,
            XemuRuntimeError,
            OSError,
            ValueError,
        ) as error:
            parser.error(str(error))
    return 2

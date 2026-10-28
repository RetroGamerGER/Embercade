"""Minimal synchronous desktop bridge to the pinned Batocera launcher."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import os
import signal
import shutil
import subprocess

from embercade.azahar import AzaharConfigError, sync_azahar_system_language
from embercade.batocera_config import BatoceraConfigError, BatoceraSystemChoice, resolve_system_choice
from embercade.bios_inventory import inspect_opera_bios
from embercade.controller import ControllerDevice
from embercade.controller_exit import ControllerExitError, controller_exit_bridge
from embercade.exit_hotkey import EXIT_HOTKEYS, resolve_exit_hotkey
from embercade.cores import CoreResolutionError, LibretroCoreResolver
from embercade.display import DisplayResolutionError, current_resolution
from embercade.executables import ExecutableResolutionError, ExecutableResolver, ProviderType
from embercade.paths import EmbercadePaths
from embercade.ppsspp import PpssppAssetsError, resolve_ppsspp_assets
from embercade.provider_runner import service_control_environment
from embercade.pcsx2 import pcsx2_writable_directories, resolve_pcsx2_runtime
from embercade.rpcs3 import resolve_rpcs3_runtime, rpcs3_writable_directories
from embercade.resources import BatoceraResources, ResourceError
from embercade.runtime import ProjectRuntime, emulator_provider_config, executable_config
from embercade.xemu import isolated_xemu_files
from embercade.standalone_decoration import standalone_decoration
from embercade.imports import ImportError as ManagedImportError, inspect_provider


class LaunchError(RuntimeError):
    """A launch prerequisite is missing or unsafe."""


SIMPLE_LIBRETRO_SYSTEMS = frozenset(
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
        "psp",
        "psx",
        "saturn",
        "sega32x",
        "snes",
        "wiiu",
        # Reviewed classical systems using the same pinned Libretro generator.
        # This is a capability boundary, not a replacement emulator/core table.
        "amiga500", "amigacdtv", "amstradcpc",
        "atari800", "atarist", "atomiswave", "bk", "cassettevision",
        "channelf", "colecovision", "dice", "fbneo", "fds", "gameandwatch", "gx4000",
        "intellivision", "lynx", "msx1", "msx2", "msx2+",
        "msxturbor", "multivision", "naomi", "naomi2", "ngp", "odyssey2",
        "pc88", "pc98", "pcfx", "pico", "pokemini", "satellaview", "scv",
        "sg1000", "sgb", "sufami", "supergrafx", "supervision",
        "systemsp", "thomson", "tvc", "uzebox", "vectrex",
        "videopacplus", "virtualboy", "wswan", "wswanc", "x1",
        "zx81", "zxspectrum",
    }
)
STANDALONE_LAUNCH_SYSTEMS = frozenset(
    {"gamecube", "ps2", "ps3", "ps4", "wii", "xbox", "xbox360"}
)
SUPPORTED_LAUNCH_SYSTEMS = SIMPLE_LIBRETRO_SYSTEMS | STANDALONE_LAUNCH_SYSTEMS


@dataclass(frozen=True, slots=True)
class LaunchPlan:
    command: tuple[str, ...]
    environment: Mapping[str, str]
    executable: Path
    core: Path | None
    rom: Path
    controller: ControllerDevice | None = None
    controllers: tuple[ControllerDevice, ...] = ()
    system: str = "nes"
    dry_run: bool = False
    emulator: str | None = None
    core_name: str | None = None
    provider_type: ProviderType | None = None
    working_directory: Path | None = None

    @property
    def retroarch(self) -> Path:
        """Compatibility name retained for the original NES-only callers."""
        return self.executable


def _configured_path(config: Mapping[str, Any], key: str, default: Path) -> Path:
    section = config.get("libretro", {})
    if not isinstance(section, Mapping):
        raise LaunchError("[libretro] must be a TOML table")
    value = section.get(key, default)
    if not isinstance(value, (str, os.PathLike)):
        raise LaunchError(f"[libretro].{key} must be a path string")
    return Path(value).expanduser().absolute()


def _prepare_ppsspp_system_directory(
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
) -> Path:
    """Expose user-provided PPSSPP assets below an isolated system directory."""
    try:
        source = resolve_ppsspp_assets(paths, config, environment)
    except PpssppAssetsError as error:
        raise LaunchError(str(error)) from error

    system_directory = paths.isolated_bios / "psp"
    system_directory.mkdir(parents=True, exist_ok=True)
    target = system_directory / "PPSSPP"
    if target.is_symlink():
        if target.resolve(strict=False) != source.resolve(strict=False):
            target.unlink()
            target.symlink_to(source, target_is_directory=True)
    elif target.exists():
        raise LaunchError(f"Refusing non-symlink PPSSPP asset target: {target}")
    else:
        target.symlink_to(source, target_is_directory=True)
    return system_directory


def _required_directories(paths: EmbercadePaths) -> tuple[Path, ...]:
    return (
        paths.config,
        paths.data,
        paths.cache,
        paths.state,
        paths.runtime,
        paths.runtime / "appimage-tmp",
        paths.emulator_configs,
        paths.emulationstation_config,
        paths.isolated_bios,
        paths.data / "system",
        paths.isolated_bios / "xemu",
        paths.saves / "gamecube",
        paths.saves / "wii",
        paths.saves / "xbox",
        paths.saves / "xbox360",
        paths.emulator_configs / "Xenia",
        paths.emulator_configs / "shadPS4",
        paths.saves / "shadps4",
        paths.data / "shadps4-addons",
        paths.screenshots,
        paths.recordings,
        paths.overlays,
        paths.cheats / "cht",
        paths.cheats / "saves",
        paths.extractions,
        paths.logs,
        paths.shaders,
    ) + tuple(
        paths.saves / system for system in sorted(SIMPLE_LIBRETRO_SYSTEMS)
    ) + pcsx2_writable_directories(paths) + rpcs3_writable_directories(paths)


def prepare_launch_layout(paths: EmbercadePaths, project_root: Path) -> None:
    """Create only Embercade-owned launch directories and a first-run config."""
    for directory in _required_directories(paths):
        directory.mkdir(parents=True, exist_ok=True)

    retroarch_config = paths.emulator_configs / "retroarch"
    # Seed the tested SDL2 profile only when absent. Never replace user mappings.
    profile = project_root / "resources/retroarch/autoconfig/sdl2/Embercade GameSir G7 Pro.cfg"
    if profile.is_file():
        target = retroarch_config / "inputs/sdl2" / profile.name
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as output:
                output.write(profile.read_bytes())
        except FileExistsError:
            pass
    (retroarch_config / "cores").mkdir(parents=True, exist_ok=True)
    (retroarch_config / "retroarchcustom.cfg").touch(exist_ok=True)
    (retroarch_config / "cores" / "retroarch-core-options.cfg").touch(exist_ok=True)

    if not paths.batocera_conf.exists():
        source = project_root / "resources" / "defaults" / "batocera.conf"
        shutil.copyfile(source, paths.batocera_conf)

    es_settings = paths.emulationstation_config / "es_settings.cfg"
    if not es_settings.exists():
        source = project_root / "resources" / "defaults" / "es_settings.cfg"
        shutil.copyfile(source, es_settings)


def create_launch_plan(
    *,
    system: str,
    rom: Path,
    paths: EmbercadePaths,
    runtime: ProjectRuntime,
    config: Mapping[str, Any],
    environment: Mapping[str, str] | None = None,
    dry_run: bool = False,
    controller: ControllerDevice | None = None,
    controllers: tuple[ControllerDevice, ...] | None = None,
    batocera_choice: BatoceraSystemChoice | None = None,
) -> LaunchPlan:
    if controllers is not None and controller is not None:
        raise LaunchError("Pass either controller or controllers, not both")
    active_controllers = (controller,) if controllers is None and controller is not None else (controllers or ())
    if len(active_controllers) > 8:
        raise LaunchError("Batocera supports at most eight controller player slots")
    controller = active_controllers[0] if active_controllers else None
    if system not in SUPPORTED_LAUNCH_SYSTEMS:
        raise LaunchError(f"Embercade has no implemented launch path for system '{system}'")

    rom = rom.expanduser().absolute()
    if system == "ps3":
        eboot = rom / "PS3_GAME" / "USRDIR" / "EBOOT.BIN"
        if not rom.is_dir() or not os.access(rom, os.R_OK) or not eboot.is_file():
            raise LaunchError(f"PS3 game directory is missing a readable EBOOT.BIN: {rom}")
    elif system == "ps4":
        eboot = rom / "eboot.bin" if rom.is_dir() else rom
        valid_layout = (rom.suffix == ".ps4" and rom.is_dir()) or (rom.suffix == ".zar" and rom.is_file())
        if not valid_layout or not eboot.is_file() or not os.access(eboot, os.R_OK):
            raise LaunchError(f"PS4 content needs a readable eboot.bin directory or ZAR archive: {rom}")
    elif not rom.is_file() or not os.access(rom, os.R_OK):
        raise LaunchError(f"ROM is not a readable file: {rom}")

    if not runtime.launcher.is_file() or not os.access(runtime.launcher, os.X_OK):
        raise LaunchError("Embercade runtime is not prepared; run scripts/runtime-prepare")

    source_env = os.environ if environment is None else environment
    system_directory = (
        _prepare_ppsspp_system_directory(paths, config, source_env)
        if system == "psp"
        else paths.bios_root
    )
    try:
        display_resolution = current_resolution(source_env)
    except DisplayResolutionError as error:
        raise LaunchError(str(error)) from error
    resolver = ExecutableResolver(
        executable_config(config),
        providers=emulator_provider_config(config),
        environment=source_env,
    )
    executable_name = {
        "gamecube": "dolphin",
        "ps2": "pcsx2",
        "ps3": "rpcs3",
        "ps4": "shadps4",
        "wii": "dolphin",
        "xbox": "xemu",
        "xbox360": "xenia-edge",
    }.get(system, "retroarch")
    try:
        executable_resolution = resolver.resolve(executable_name)
        executable = executable_resolution.path
    except ExecutableResolutionError as error:
        raise LaunchError(str(error)) from error
    if system == "ps4":
        try:
            inspect_provider(executable, provider="shadps4", require_executable=True)
        except ManagedImportError as error:
            raise LaunchError(f"shadPS4 AppImage: {error}") from error
    host_provider_runner: Path | None = None
    if executable_resolution.provider_type is ProviderType.APPIMAGE:
        runner_text = source_env.get("EMBERCADE_HOST_PROVIDER_RUNNER")
        if runner_text:
            host_provider_runner = Path(runner_text)
            if (
                not host_provider_runner.is_absolute()
                or not host_provider_runner.is_file()
                or not os.access(host_provider_runner, os.R_OK | os.X_OK)
            ):
                raise LaunchError(
                    f"Configured host provider runner is unavailable: {host_provider_runner}"
                )
    core: Path | None = None
    core_name: str | None = None
    core_dir = Path("/usr/lib/libretro")
    libretro_share = _configured_path(config, "share", runtime.share / "libretro")
    effective_emulator = {
        "gamecube": "dolphin",
        "ps2": "pcsx2",
        "ps3": "rpcs3",
        "ps4": "shadps4",
        "wii": "dolphin",
        "xbox": "xemu",
        "xbox360": "xenia-edge",
    }.get(system)
    if system in SIMPLE_LIBRETRO_SYSTEMS:
        try:
            choice = batocera_choice or resolve_system_choice(
                system=system,
                rom=rom,
                paths=paths,
                runtime=runtime,
                environment=source_env,
            )
        except BatoceraConfigError as error:
            raise LaunchError(str(error)) from error
        if choice.system != system:
            raise LaunchError(
                f"Batocera configuration choice is for '{choice.system}', expected '{system}'"
            )
        if choice.emulator != "libretro":
            raise LaunchError(
                f"Batocera selected emulator '{choice.emulator}' for '{system}'; "
                "this generic path accepts only libretro"
            )
        effective_emulator = choice.emulator
        core_name = choice.core
        try:
            core = LibretroCoreResolver.from_host(config, source_env).resolve(core_name).path
        except (CoreResolutionError, ValueError) as error:
            raise LaunchError(str(error)) from error
        core_dir = core.parent
        if system == "3do" and core_name == "opera":
            firmware = inspect_opera_bios(paths.bios_root)
            if not firmware.available:
                raise LaunchError(f"3DO BIOS {firmware.status}: {firmware.detail}")
    xemu_files = isolated_xemu_files(paths) if system == "xbox" else None
    pcsx2_runtime = resolve_pcsx2_runtime(paths, config, source_env) if system == "ps2" else None
    rpcs3_runtime = resolve_rpcs3_runtime(paths, config, source_env) if system == "ps3" else None
    if xemu_files is not None:
        for label, path in (
            ("flash ROM", xemu_files.flashrom),
            ("MCPX ROM", xemu_files.bootrom),
            ("EEPROM", xemu_files.eeprom),
            ("HDD", xemu_files.hdd),
        ):
            if label == "EEPROM" and not path.exists() and not path.is_symlink():
                continue  # Xemu generates it at this isolated, configured path.
            if not path.is_file() or not os.access(path, os.R_OK):
                raise LaunchError(f"Isolated Xemu {label} is unavailable: {path}")
    try:
        resources = BatoceraResources.for_project(runtime.project_root, source_env)
        from embercade.shaders import prepare_host_runtime

        resources = BatoceraResources(
            prepare_host_runtime(resources.shaders, paths.runtime, source_env),
            resources.decorations,
        )
        # Standalone decoration is optional polish, even if the whole image
        # directory is unavailable. Keep other providers' validation unchanged.
        if system not in {"ps2", "xbox", "gamecube", "wii"}:
            resources.validate()
    except ResourceError as error:
        raise LaunchError(str(error)) from error
    launch_env = dict(source_env)
    launch_env.pop("PYTHONPATH", None)
    host_runtime_dir = launch_env.get("XDG_RUNTIME_DIR")
    if host_runtime_dir and Path(host_runtime_dir).is_absolute():
        launch_env.setdefault("EMBERCADE_HOST_SESSION_RUNTIME_ROOT", host_runtime_dir)
    if system in {"ps2", "xbox", "gamecube", "wii"} and host_runtime_dir:
        launch_env["EMBERCADE_DECORATION_SESSION_RUNTIME"] = host_runtime_dir
    if wayland_display := launch_env.get("WAYLAND_DISPLAY"):
        wayland_socket = Path(wayland_display)
        if not wayland_socket.is_absolute():
            if not host_runtime_dir:
                raise LaunchError("WAYLAND_DISPLAY requires the host XDG_RUNTIME_DIR")
            wayland_socket = Path(host_runtime_dir) / wayland_socket
        if not wayland_socket.is_socket():
            raise LaunchError(f"Desktop Wayland socket is unavailable: {wayland_socket}")
        launch_env["WAYLAND_DISPLAY"] = str(wayland_socket)
    if not launch_env.get("PULSE_SERVER") and host_runtime_dir:
        pulse_socket = Path(host_runtime_dir) / "pulse" / "native"
        if not pulse_socket.is_socket():
            raise LaunchError(f"Desktop PulseAudio compatibility socket is unavailable: {pulse_socket}")
        launch_env["PULSE_SERVER"] = f"unix:{pulse_socket}"
    launch_env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "XDG_CONFIG_HOME": str(paths.config),
            "XDG_DATA_HOME": str(paths.data),
            "XDG_CACHE_HOME": str(paths.cache),
            "XDG_STATE_HOME": str(paths.state),
            "XDG_RUNTIME_DIR": str(paths.runtime),
            "EMBERCADE_DESKTOP": "1",
            "SDL_JOYSTICK_HIDAPI_WII": "0",
            "EMBERCADE_EXIT_HOTKEY": resolve_exit_hotkey(config).key,
            "EMBERCADE_DISPLAY_WIDTH": str(display_resolution.width),
            "EMBERCADE_DISPLAY_HEIGHT": str(display_resolution.height),
            "EMBERCADE_BATOCERA_SHARE_DIR": str(runtime.share / "batocera"),
            "EMBERCADE_BATOCERA_SHADERS": str(resources.shaders),
            "EMBERCADE_SYSTEM_DECORATIONS": str(resources.decorations),
            "EMBERCADE_SYSTEM_ES_DIR": str(runtime.share / "emulationstation"),
            "EMBERCADE_EVMAPY_SHARE_DIR": str(runtime.share / "evmapy"),
            "EMBERCADE_USERDATA": str(paths.data),
            "EMBERCADE_HOME": str(paths.data / "system"),
            "EMBERCADE_CONFIGS": str(paths.emulator_configs),
            "EMBERCADE_SAVES": str(paths.saves),
            "EMBERCADE_SCREENSHOTS": str(paths.screenshots),
            "EMBERCADE_RECORDINGS": str(paths.recordings),
            "EMBERCADE_BIOS": str(system_directory),
            "EMBERCADE_OVERLAYS": str(paths.overlays),
            "EMBERCADE_CACHE": str(paths.cache),
            "EMBERCADE_ROMS": str(paths.rom_root),
            "EMBERCADE_CHEATS": str(paths.cheats),
            "EMBERCADE_LOGS": str(paths.logs),
            "EMBERCADE_BATOCERA_CONF": str(paths.batocera_conf),
            "EMBERCADE_SQUASHFS_DIR": str(paths.runtime / "squashfs"),
            "EMBERCADE_ROM_OVERLAY_DIR": str(paths.runtime / "rom-overlays"),
            "EMBERCADE_PROFILER_PATH": str(paths.runtime / "batocera-launch.perf"),
            "EMBERCADE_LAUNCH_ERROR_PATH": str(paths.logs / "launch_error.log"),
            "EMBERCADE_LAUNCH_NOTICE_PATH": str(paths.logs / "launch-notice.txt"),
            "EMBERCADE_RETROARCH_BIN": str(
                executable if system in SIMPLE_LIBRETRO_SYSTEMS else "/usr/bin/retroarch"
            ),
            "EMBERCADE_DOLPHIN_BIN": str(
                executable if system in {"gamecube", "wii"} else "/usr/bin/dolphin-emu"
            ),
            "EMBERCADE_XEMU_BIN": str(executable if system == "xbox" else "xemu"),
            "EMBERCADE_PCSX2_BIN": str(executable if system == "ps2" else "pcsx2-qt"),
            "EMBERCADE_RPCS3_BIN": str(executable if system == "ps3" else "rpcs3"),
            "EMBERCADE_XENIA_EDGE_BIN": str(
                (host_provider_runner or executable) if system == "xbox360" else "xenia_edge"
            ),
            "EMBERCADE_XENIA_EDGE_LOG": str(paths.logs / "xenia-edge.log"),
            "EMBERCADE_SHADPS4_BIN": str((host_provider_runner or executable) if system == "ps4" else "shadps4"),
            "EMBERCADE_LIBRETRO_CORES": str(core_dir),
            "EMBERCADE_LIBRETRO_SHARE": str(libretro_share),
        }
    )
    if system == "ps3":
        # Current RPCS3 builds abort inside Gamescope's optional Vulkan WSI
        # bypass layer.  Keep the normal X11/Vulkan presentation path while
        # leaving Gamescope WSI enabled for compatible emulators such as PCSX2.
        launch_env["ENABLE_GAMESCOPE_WSI"] = "0"
    if system == "wii":
        from embercade.wii import real_wiimote_connected

        # Structural dry runs must not send output reports to live hardware.
        connected = not dry_run and real_wiimote_connected()
        launch_env["EMBERCADE_WII_REAL_CONNECTED"] = "1" if connected else "0"
    else:
        launch_env.pop("EMBERCADE_WII_REAL_CONNECTED", None)
    if host_provider_runner is not None and system == "xbox360":
        xenia_storage_root = paths.emulator_configs / "Xenia"
        xenia_content_root = paths.saves / "xbox360"
        xenia_cache_root = paths.cache / "xenia-edge"
        if host_config_root := source_env.get("EMBERCADE_HOST_CONFIG_ROOT"):
            xenia_storage_root = Path(host_config_root) / "emulators/Xenia"
        if host_data_root := source_env.get("EMBERCADE_HOST_DATA_ROOT"):
            xenia_content_root = Path(host_data_root) / "saves/xbox360"
        if host_cache_root := source_env.get("EMBERCADE_HOST_CACHE_ROOT"):
            xenia_cache_root = Path(host_cache_root) / "xenia-edge"
        launch_env.update(
            {
                "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(executable),
                "EMBERCADE_EXTERNAL_PROVIDER_UNIT": "embercade-xenia",
                "EMBERCADE_EXTERNAL_PROVIDER_HOME": str(paths.data / "system"),
                "EMBERCADE_EXTERNAL_PROVIDER_TMPDIR": str(paths.runtime / "appimage-tmp"),
                "EMBERCADE_XENIA_EDGE_STORAGE_ROOT": str(xenia_storage_root),
                "EMBERCADE_XENIA_EDGE_CONTENT_ROOT": str(xenia_content_root),
                "EMBERCADE_XENIA_EDGE_CACHE_ROOT": str(xenia_cache_root),
            }
        )
    if system == "ps4":
        host_data = Path(source_env.get("EMBERCADE_HOST_DATA_ROOT", paths.data))
        host_roms = Path(source_env.get("EMBERCADE_HOST_ROMS_ROOT", paths.rom_root))
        launch_env.update({
            "EMBERCADE_SHADPS4_SAVES": str(host_data / "saves/shadps4"),
            "EMBERCADE_SHADPS4_ADDONS": str(host_data / "shadps4-addons"),
            "EMBERCADE_SHADPS4_ROMS": str(host_roms / "ps4"),
        })
        if host_provider_runner is not None:
            launch_env.update({
                "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(executable),
                "EMBERCADE_EXTERNAL_PROVIDER_ID": "shadps4",
                "EMBERCADE_EXTERNAL_PROVIDER_UNIT": "embercade-shadps4",
                "EMBERCADE_EXTERNAL_PROVIDER_HOME": str(paths.data / "system"),
                "EMBERCADE_EXTERNAL_PROVIDER_TMPDIR": str(paths.runtime / "appimage-tmp"),
            })
    if core is not None and core_name is not None:
        launch_env["EMBERCADE_LIBRETRO_CORE"] = str(core)
        launch_env["EMBERCADE_LIBRETRO_CORE_NAME"] = core_name
    if xemu_files is not None:
        launch_env.update(xemu_files.as_environment())
    if pcsx2_runtime is not None:
        launch_env.update(pcsx2_runtime.as_environment())
    if rpcs3_runtime is not None:
        launch_env.update(rpcs3_runtime.as_environment())
    if dry_run:
        launch_env["EMBERCADE_DRY_RUN"] = "1"
    else:
        launch_env.pop("EMBERCADE_DRY_RUN", None)

    command = (
        str(runtime.launcher),
        "-system",
        system,
        "-rom",
        str(rom),
    )
    if system in SIMPLE_LIBRETRO_SYSTEMS:
        command += ("-emulator", "libretro", "-core", core_name or "")
    for slot, device in enumerate(active_controllers, start=1):
        # RPCS3's SDL3 handler matches its live SDL device name.  The other
        # Batocera generators currently require the evdev/kernel name here.
        controller_name = device.name if system == "ps3" else None
        command += device.player_arguments(slot, device_name=controller_name)
    return LaunchPlan(
        command,
        launch_env,
        executable,
        core,
        rom,
        controller,
        active_controllers,
        system=system,
        dry_run=dry_run,
        emulator=effective_emulator,
        core_name=core_name,
        provider_type=executable_resolution.provider_type,
        working_directory=(
            paths.emulator_configs / "Xenia" if system == "xbox360"
            else paths.emulator_configs if system == "ps4" else None
        ),
    )


def run_launch(plan: LaunchPlan) -> int:
    """Run synchronously so the frontend resumes only after launcher cleanup."""
    if not plan.dry_run and (notice := plan.environment.get("EMBERCADE_LAUNCH_NOTICE_PATH")):
        Path(notice).unlink(missing_ok=True)
    with standalone_decoration(plan):
        return _run_launch(plan)


def _run_launch(plan: LaunchPlan) -> int:
    sync_azahar = (
        plan.system == "3ds"
        and plan.emulator == "libretro"
        and plan.core_name == "azahar"
        and not plan.dry_run
    )
    if sync_azahar:
        try:
            sync_azahar_system_language(
                batocera_conf=Path(plan.environment["EMBERCADE_BATOCERA_CONF"]),
                saves_root=Path(plan.environment["EMBERCADE_SAVES"]),
            )
        except (AzaharConfigError, KeyError) as error:
            raise LaunchError(str(error)) from error
    run_options: dict[str, object] = {
        "env": dict(plan.environment),
        "check": False,
    }
    if plan.working_directory is not None:
        run_options["cwd"] = plan.working_directory
    if plan.system in {"xbox", "xbox360", "ps3", "ps4"} and plan.controller is not None and not plan.dry_run:
        try:
            bridge_options: dict[str, object] = {"emulator": plan.system}
            preset = EXIT_HOTKEYS[
                plan.environment.get("EMBERCADE_EXIT_HOTKEY", "back-start")
            ]
            if preset.key != "back-start":
                bridge_options["hotkey"] = preset
            popen_options = dict(run_options)
            popen_options.pop("check", None)
            process = subprocess.Popen(plan.command, **popen_options)

            def request_process_exit() -> None:
                if process.poll() is None:
                    provider_unit = plan.environment.get(
                        "EMBERCADE_EXTERNAL_PROVIDER_UNIT"
                    )
                    if provider_unit:
                        systemctl = shutil.which(
                            "systemctl", path=plan.environment.get("PATH")
                        )
                        if systemctl is not None:
                            stopped = subprocess.run(
                                (
                                    systemctl,
                                    "--user",
                                    "stop",
                                    f"{provider_unit}.service",
                                ),
                                env=service_control_environment(plan.environment),
                                check=False,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            if stopped.returncode == 0:
                                return
                    process.send_signal(signal.SIGINT)

            bridge_options["on_exit"] = request_process_exit
            with controller_exit_bridge(plan.controller, **bridge_options):
                returncode = process.wait()
            completed = subprocess.CompletedProcess(plan.command, returncode)
        except ControllerExitError as error:
            raise LaunchError(str(error)) from error
    else:
        completed = subprocess.run(plan.command, **run_options)
    if sync_azahar:
        try:
            sync_azahar_system_language(
                batocera_conf=Path(plan.environment["EMBERCADE_BATOCERA_CONF"]),
                saves_root=Path(plan.environment["EMBERCADE_SAVES"]),
            )
        except (AzaharConfigError, KeyError) as error:
            raise LaunchError(str(error)) from error
    return completed.returncode

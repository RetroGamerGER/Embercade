"""Production frontend launch using an install-shaped Embercade prefix."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import os
import shutil
import subprocess
import sys

from embercade.controller import (
    ControllerUnavailable,
    enumerate_sdl_game_controllers,
    resolve_player_controllers,
    write_es_input_overrides,
)
from embercade.display import DisplayResolutionError, current_resolution
from embercade.elf_runtime import FrontendRuntimeReport, inspect_frontend_runtime
from embercade.paths import EmbercadePaths
from embercade.ppsspp import PpssppAssetsError, resolve_ppsspp_assets
from embercade.policy import DesktopPolicy
from embercade.runtime import ProjectRuntime, probe_runtime
from embercade.scraper_access import metadata_mounts, secret_mounts


class ProductionError(RuntimeError):
    """The staged/installed application cannot safely start."""


@dataclass(frozen=True, slots=True)
class ProductionLayout:
    prefix: Path

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "ProductionLayout | None":
        env = os.environ if environment is None else environment
        value = env.get("EMBERCADE_PREFIX")
        if not value:
            return None
        return cls(Path(value).expanduser().absolute())

    @property
    def application(self) -> Path:
        return self.prefix / "share" / "embercade"

    @property
    def runtime(self) -> ProjectRuntime:
        return ProjectRuntime(self.application, self.application / "runtime")

    @property
    def frontend(self) -> Path:
        return self.application / "frontend" / "emulationstation"

    @property
    def resources(self) -> Path:
        return self.application / "resources"

    @property
    def libraries(self) -> Path:
        return self.application / "lib"

    @property
    def splash_image(self) -> Path:
        return self.resources / "branding" / "splash" / "embercade-splash-3840x2160.jpg"

    @property
    def provider_runner(self) -> Path:
        return self.prefix / "bin" / "embercade-provider-runner"

    @property
    def manifest(self) -> Path:
        return self.application / "stage-manifest.json"

    def required_paths(self) -> tuple[Path, ...]:
        return (
            self.runtime.python,
            self.runtime.launcher,
            self.frontend,
            self.resources / "emulationstation" / "es_systems.cfg",
            self.resources / "emulationstation" / "es_features.cfg",
            self.resources / "emulationstation" / "es_input.cfg",
            self.resources / "emulationstation" / "resources",
            self.resources / "emulationstation" / "themes" / "es-theme-carbon",
            self.resources / "batocera" / "shaders",
            self.resources / "batocera" / "datainit" / "decorations",
            self.resources / "defaults" / "batocera.conf",
            self.resources / "branding" / "icon" / "embercade-512.png",
            self.resources / "policy" / "desktop-capabilities.conf",
            self.provider_runner,
            self.manifest,
        )

    def frontend_runtime(self) -> FrontendRuntimeReport:
        return inspect_frontend_runtime(self.frontend, self.libraries)

    def validate(self, *, check_frontend_libraries: bool = True) -> tuple[str, ...]:
        failures = []
        for path in self.required_paths():
            if not path.exists():
                failures.append(f"missing production path: {path}")
        if self.frontend.exists() and not os.access(self.frontend, os.R_OK | os.X_OK):
            failures.append(f"frontend is not executable: {self.frontend}")
        if check_frontend_libraries and self.frontend.is_file():
            failures.extend(self.frontend_runtime().failures)
        status = probe_runtime(self.runtime)
        if not status.healthy:
            failures.append("installed launcher runtime is unhealthy")
        return tuple(failures)


def _frontend_splash_arguments(layout: ProductionLayout) -> tuple[str, ...]:
    if not layout.splash_image.is_file():
        return ("--no-splash",)
    return (
        "--splash-image",
        "/app/share/embercade/resources/branding/splash/embercade-splash-3840x2160.jpg",
    )


def _ensure_link(path: Path, target: str) -> None:
    if path.is_symlink():
        if os.readlink(path) == target:
            return
        path.unlink()
    elif path.exists():
        raise ProductionError(f"Refusing non-symlink compatibility path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)


def _prepare_compatibility_root(paths: EmbercadePaths) -> tuple[Path, Path]:
    root = paths.runtime / "frontend-root"
    runtime_session = paths.runtime / "session"
    for directory in (
        root / "system/xdg/config",
        root / "system/xdg/data",
        root / "system/xdg/cache",
        root / "system/xdg/state",
        root / "system/xdg/runtime",
        runtime_session,
        paths.data / "system",
        paths.data / "music",
        paths.themes,
        paths.theme_downloads,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    links = {
        root / "system/batocera.conf": "/userdata/system/xdg/config/embercade/batocera.conf",
        root / "system/configs": "/userdata/system/xdg/config/embercade/emulators",
        root / "system/logs": "/userdata/system/xdg/state/embercade/logs",
        root / "system/home": "/userdata/system/xdg/data/embercade/system",
        root / "saves": "/userdata/system/xdg/data/embercade/saves",
        root / "screenshots": "/userdata/system/xdg/data/embercade/screenshots",
        root / "recordings": "/userdata/system/xdg/data/embercade/recordings",
        root / "themes": "/userdata/system/xdg/data/embercade/themes",
        root / "decorations": "/userdata/system/xdg/data/embercade/decorations",
        root / "shaders": "/userdata/system/xdg/data/embercade/shaders",
        root / "overlays": "/userdata/system/xdg/data/embercade/overlays",
        root / "cheats": "/userdata/system/xdg/data/embercade/cheats",
        root / "extractions": "/userdata/system/xdg/cache/embercade/extractions",
        root / "music": "/userdata/system/xdg/data/embercade/music",
    }
    for link, target in links.items():
        _ensure_link(link, target)
    return root, runtime_session


def _runtime_mounts(
    environment: Mapping[str, str],
) -> tuple[list[str], str, str, str | None, str | None]:
    host_runtime_text = environment.get("XDG_RUNTIME_DIR", "")
    host_runtime = Path(host_runtime_text)
    if not host_runtime_text or not host_runtime.is_absolute() or not host_runtime.is_dir():
        raise ProductionError("XDG_RUNTIME_DIR is unavailable; start Embercade in a desktop session")
    if not environment.get("WAYLAND_DISPLAY") and not environment.get("DISPLAY"):
        raise ProductionError("No active Wayland or X11 display is visible")
    pulse_socket = host_runtime / "pulse" / "native"
    if not pulse_socket.is_socket():
        raise ProductionError(f"PulseAudio compatibility socket is unavailable: {pulse_socket}")
    pulse_server = environment.get("PULSE_SERVER", f"unix:{pulse_socket}")
    mounts = [
        "--dir", "/run",
        "--dir", "/run/user",
        "--dir", str(host_runtime),
        "--dir", str(host_runtime / "pulse"),
        "--ro-bind", "/run/udev", "/run/udev",
        "--ro-bind", str(pulse_socket), str(pulse_socket),
    ]
    if wayland := environment.get("WAYLAND_DISPLAY"):
        socket = Path(wayland) if Path(wayland).is_absolute() else host_runtime / wayland
        if not socket.is_socket():
            raise ProductionError(f"Wayland socket is unavailable: {socket}")
        mounts += ["--ro-bind", str(socket), str(socket)]
    # The optional decoration helper only reads window state/events. Expose
    # these two sockets, not the entire compositor runtime directory.
    from embercade.standalone_decoration import hyprland_socket_dir

    if hyprland := hyprland_socket_dir(environment):
        for name in (".socket.sock", ".socket2.sock"):
            mounts += ["--ro-bind", str(hyprland / name), str(hyprland / name)]
    gamescope_display = None
    if gamescope := environment.get("GAMESCOPE_WAYLAND_DISPLAY"):
        gamescope_socket = (
            Path(gamescope) if Path(gamescope).is_absolute() else host_runtime / gamescope
        )
        if not gamescope_socket.is_socket():
            raise ProductionError(
                f"Gamescope display socket is unavailable: {gamescope_socket}"
            )
        mounts += ["--ro-bind", str(gamescope_socket), str(gamescope_socket)]
        gamescope_display = str(gamescope_socket)
    if environment.get("DBUS_SESSION_BUS_ADDRESS", "").startswith("unix:path="):
        dbus_socket = environment["DBUS_SESSION_BUS_ADDRESS"].removeprefix("unix:path=").split(",", 1)[0]
        if Path(dbus_socket).is_socket():
            mounts += ["--ro-bind", dbus_socket, dbus_socket]
    # systemctl --user uses this manager socket rather than the session bus.
    # Expose only the socket for launch-scoped provider cleanup, not host state.
    manager_socket = host_runtime / "systemd" / "private"
    if manager_socket.is_socket():
        mounts += [
            "--dir", str(manager_socket.parent),
            "--ro-bind", str(manager_socket), str(manager_socket),
        ]
    sandbox_xauthority = None
    if xauthority_text := environment.get("XAUTHORITY"):
        xauthority = Path(xauthority_text).expanduser().absolute()
        if not xauthority.is_file() or not os.access(xauthority, os.R_OK):
            raise ProductionError(f"XAUTHORITY file is unavailable: {xauthority}")
        sandbox_xauthority = str(host_runtime / "embercade-xauthority")
        mounts += ["--ro-bind", str(xauthority), sandbox_xauthority]
    return mounts, str(host_runtime), pulse_server, sandbox_xauthority, gamescope_display


def _optional_host_sources(
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
) -> tuple[list[str], list[str]]:
    mounts: list[str] = []
    variables: list[str] = []
    try:
        ppsspp = resolve_ppsspp_assets(paths, config, environment)
    except PpssppAssetsError:
        # PSP is optional; its launcher and Doctor report the precise error.
        pass
    else:
        mounts += ["--ro-bind", str(ppsspp), "/embercade-ppsspp-assets"]
        variables += ["--setenv", "EMBERCADE_PPSSPP_ASSETS", "/embercade-ppsspp-assets"]
    host_home = Path(environment.get("HOME", str(Path.home())))
    host_config = Path(environment.get("XDG_CONFIG_HOME", host_home / ".config"))
    host_data = Path(environment.get("XDG_DATA_HOME", host_home / ".local/share"))

    retroarch = host_config / "retroarch"
    if not retroarch.is_dir():
        retroarch = host_home / ".config" / "retroarch"
    if retroarch.is_dir():
        mounts += ["--ro-bind", str(retroarch), "/host-retroarch-profile"]
        variables += [
            "--setenv", "EMBERCADE_RETROARCH_USER_CONFIG", "/host-retroarch-profile/retroarch.cfg",
            "--setenv", "EMBERCADE_LIBRETRO_USER_CORES", "/host-retroarch-profile/cores",
            "--setenv", "EMBERCADE_LIBRETRO_USER_INFO", "/host-retroarch-profile/info",
        ]

    xemu = host_data / "xemu" / "xemu"
    xemu_names = {
        "EMBERCADE_XEMU_FLASHROM_SOURCE": "Complex_4627.bin",
        "EMBERCADE_XEMU_BOOTROM_SOURCE": "mcpx_1.0.bin",
        "EMBERCADE_XEMU_EEPROM_SOURCE": "eeprom.bin",
        "EMBERCADE_XEMU_HDD_SOURCE": "xbox_hdd.qcow2",
    }
    if all((xemu / name).is_file() for variable, name in xemu_names.items()
           if variable != "EMBERCADE_XEMU_EEPROM_SOURCE"):
        mounts += ["--ro-bind", str(xemu), "/host-xemu-data"]
        for variable, name in xemu_names.items():
            if (xemu / name).is_file():
                variables += ["--setenv", variable, f"/host-xemu-data/{name}"]

    rpcs3_section = config.get("rpcs3", {})
    configured_rpcs3 = rpcs3_section.get("firmware_source") if isinstance(rpcs3_section, Mapping) else None
    rpcs3 = Path(configured_rpcs3).expanduser() if isinstance(configured_rpcs3, str) else host_config / "rpcs3"
    isolated_rpcs3 = paths.emulator_configs / "rpcs3/dev_flash/vsh/etc/version.txt"
    if not isolated_rpcs3.is_file() and (rpcs3 / "dev_flash/vsh/etc/version.txt").is_file():
        mounts += ["--ro-bind", str(rpcs3.absolute()), "/host-rpcs3-profile"]
        variables += ["--setenv", "EMBERCADE_RPCS3_FIRMWARE_SOURCE", "/host-rpcs3-profile"]

    provider_paths = [
        provider.get("executable") for provider in config.get("emulators", {}).values()
        if isinstance(provider, Mapping)
    ] if isinstance(config.get("emulators", {}), Mapping) else []
    # Legacy explicit overrides have resolver priority and need the same
    # read-only visibility as provider-configured external files.
    overrides = config.get("executables", {})
    if isinstance(overrides, Mapping):
        provider_paths.extend(overrides.values())
    bound: set[Path] = set()
    for executable in provider_paths:
        if isinstance(executable, str):
            path = Path(executable).expanduser().absolute()
            if path.is_file() and path not in bound:
                mounts += ["--ro-bind", str(path), str(path)]
                bound.add(path)
    return mounts, variables


def production_command(
    layout: ProductionLayout,
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    *,
    environment: Mapping[str, str] | None = None,
    frontend_arguments: Sequence[str] = (),
) -> tuple[str, ...]:
    env = os.environ if environment is None else environment
    immutable_roots = [layout.prefix]
    if appdir := env.get("APPDIR"):
        immutable_roots.append(Path(appdir))
    for immutable in immutable_roots:
        if conflicts := paths.writable_roots_inside(immutable):
            raise ProductionError(
                "Writable Embercade user state must be outside the read-only application: "
                + ", ".join(conflicts)
            )
    failures = layout.validate()
    if failures:
        raise ProductionError("; ".join(failures))
    validations = paths.validate_collection_roots()
    unconfigured = [item.label for item in validations if not item.configured]
    if unconfigured:
        raise ProductionError(
            "FIRST RUN / CONFIG MISSING: configure [paths].roms and [paths].bios "
            f"in {paths.config / 'embercade.toml'}"
        )
    invalid = [item for item in validations if not item.ok]
    if invalid:
        raise ProductionError(
            "; ".join(f"{item.label} {item.status}: {item.path}" for item in invalid)
        )
    if shutil.which("bwrap", path=env.get("PATH")) is None:
        raise ProductionError("Bubblewrap (bwrap) is required")
    if not Path("/dev/input").is_dir() or not os.access("/dev/input", os.R_OK | os.X_OK):
        raise ProductionError("Controller input directory is unavailable: /dev/input")
    if not Path("/dev/dri").is_dir():
        raise ProductionError("Graphics devices are unavailable: /dev/dri")
    try:
        display_resolution = current_resolution(env)
    except DisplayResolutionError as error:
        raise ProductionError(str(error)) from error

    from embercade.launcher import prepare_launch_layout

    prepare_launch_layout(paths, layout.application)
    compatibility_root, runtime_session = _prepare_compatibility_root(paths)
    from embercade.shaders import prepare_host_runtime, find_host_shader_root

    shader_root = prepare_host_runtime(
        layout.resources / "batocera/shaders", paths.runtime, env)
    host_shaders = find_host_shader_root(env)
    shader_mounts = (["--ro-bind", str(host_shaders), str(host_shaders)]
                     if host_shaders is not None else [])
    try:
        controllers = resolve_player_controllers(
            enumerate_sdl_game_controllers(),
            es_settings=paths.emulationstation_config / "es_settings.cfg",
        )
    except ControllerUnavailable:
        controllers = ()
    if controllers:
        write_es_input_overrides(
            controllers,
            layout.runtime.share / "emulationstation" / "es_input.cfg",
            paths.emulationstation_config / "es_input.cfg",
        )

    (
        runtime_mounts,
        host_runtime,
        pulse_server,
        sandbox_xauthority,
        gamescope_display,
    ) = _runtime_mounts(env)
    optional_mounts, optional_variables = _optional_host_sources(paths, config, env)
    scraper_mounts, scraper_variables = secret_mounts(paths)
    library_mounts, unavailable_metadata = metadata_mounts(
        paths, layout.resources / "emulationstation" / "es_systems.cfg"
    )
    if unavailable_metadata:
        print("Embercade: some library metadata/media destinations are read-only; "
              "scraping there is unavailable. Game files remain protected.", file=sys.stderr)
    if sandbox_xauthority is not None:
        optional_variables += [
            "--setenv",
            "XAUTHORITY",
            sandbox_xauthority,
            "--setenv",
            "EMBERCADE_HOST_XAUTHORITY",
            str(Path(env["XAUTHORITY"]).expanduser().absolute()),
        ]
    if gamescope_display is not None:
        optional_variables += [
            "--setenv",
            "GAMESCOPE_WAYLAND_DISPLAY",
            gamescope_display,
        ]
        # Discover only the compositor's card nodes outside the sandbox. The
        # helper reads current mode data inside; never expose host /proc or
        # grant additional DRM permissions just for optional artwork.
        from embercade.drm_output import gamescope_device_hint

        try:
            hint = gamescope_device_hint(env)
        except Exception:
            hint = None
        if hint is not None:
            optional_variables += ['--setenv', 'EMBERCADE_DECORATION_DRM_DEVICES', hint]
    policy = DesktopPolicy.load(layout.resources / "policy" / "desktop-capabilities.conf")
    policy_variables: list[str] = []
    for name, value in policy.frontend_environment().items():
        policy_variables += ["--setenv", name, value]

    prefix = layout.prefix
    frontend_branding = _frontend_splash_arguments(layout)
    command = [
        "bwrap", "--die-with-parent", "--new-session",
        "--ro-bind", "/usr/bin", "/usr/bin",
        "--ro-bind", "/usr/lib", "/usr/lib",
        "--ro-bind", "/etc", "/etc",
        *runtime_mounts,
        "--overlay-src", "/usr/share",
        "--tmp-overlay", "/usr/share",
        "--ro-bind", str(layout.resources / "emulationstation"), "/usr/share/emulationstation",
        "--ro-bind", str(layout.resources / "batocera"), "/usr/share/batocera",
        "--ro-bind", str(shader_root), "/usr/share/batocera/shaders",
        *shader_mounts,
        "--ro-bind", "/sys", "/sys",
        "--ro-bind", "/var", "/var",
        "--ro-bind", str(prefix), "/app",
        "--ro-bind", str(prefix), str(prefix),
        "--ro-bind", str(paths.rom_root), str(paths.rom_root),
        "--ro-bind", str(paths.bios_root), str(paths.bios_root),
        "--dev", "/dev",
        "--dir", "/dev/input",
        "--dev-bind", "/dev/input", "/dev/input",
    ]
    if Path("/dev/uinput").is_char_device() and os.access("/dev/uinput", os.R_OK | os.W_OK):
        command += ["--dev-bind", "/dev/uinput", "/dev/uinput"]
    from embercade.wii import wii_device_mounts

    command += wii_device_mounts()
    command += [
        "--dev-bind", "/dev/dri", "/dev/dri",
        "--proc", "/proc",
        "--bind", str(compatibility_root), "/userdata",
        "--bind", str(paths.config), "/userdata/system/xdg/config/embercade",
        "--bind", str(paths.data), "/userdata/system/xdg/data/embercade",
        "--bind", str(paths.cache), "/userdata/system/xdg/cache/embercade",
        "--bind", str(paths.state), "/userdata/system/xdg/state/embercade",
        "--bind", str(runtime_session), "/userdata/system/xdg/runtime/embercade",
        "--ro-bind", str(paths.rom_root), "/userdata/roms",
        "--ro-bind", str(paths.bios_root), "/userdata/bios",
        *library_mounts,
        *scraper_mounts,
        *optional_mounts,
        "--ro-bind-try", "/tmp/.X11-unix", "/tmp/.X11-unix",
        "--symlink", "usr/bin", "/bin",
        "--symlink", "usr/bin", "/sbin",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib", "/lib64",
        "--setenv", "HOME", "/userdata/system/home",
        "--setenv", "XDG_CONFIG_HOME", "/userdata/system/xdg/config",
        "--setenv", "XDG_DATA_HOME", "/userdata/system/xdg/data",
        "--setenv", "XDG_CACHE_HOME", "/userdata/system/xdg/cache",
        "--setenv", "XDG_STATE_HOME", "/userdata/system/xdg/state",
        "--setenv", "XDG_RUNTIME_DIR", host_runtime,
        "--setenv", "PULSE_SERVER", pulse_server,
        "--setenv", "EMBERCADE_RUNTIME_HOME", "/userdata/system/xdg/runtime/embercade",
        "--setenv", "EMBERCADE_DISPLAY_WIDTH", str(display_resolution.width),
        "--setenv", "EMBERCADE_DISPLAY_HEIGHT", str(display_resolution.height),
        "--setenv", "EMBERCADE_PREFIX", "/app",
        "--setenv", "EMBERCADE_LAUNCH_NOTICE_PATH", "/userdata/system/xdg/state/embercade/logs/launch-notice.txt",
        "--setenv", "EMBERCADE_PROJECT_ROOT", "/app/share/embercade",
        "--setenv", "EMBERCADE_RUNTIME_ROOT", "/app/share/embercade/runtime",
        "--setenv", "EMBERCADE_SHADER_RESOURCES", "/usr/share/batocera/shaders",
        "--setenv", "EMBERCADE_DECORATION_RESOURCES", "/app/share/embercade/resources/batocera/datainit/decorations",
        "--setenv", "EMBERCADE_HOST_PROVIDER_RUNNER", str(layout.provider_runner),
        "--setenv", "EMBERCADE_HOST_CONFIG_ROOT", str(paths.config),
        "--setenv", "EMBERCADE_HOST_DATA_ROOT", str(paths.data),
        "--setenv", "EMBERCADE_HOST_CACHE_ROOT", str(paths.cache),
        "--setenv", "EMBERCADE_HOST_STATE_ROOT", str(paths.state),
        "--setenv", "EMBERCADE_HOST_PRIVATE_RUNTIME_ROOT", str(runtime_session),
        "--setenv", "EMBERCADE_HOST_SESSION_RUNTIME_ROOT", host_runtime,
        "--setenv", "EMBERCADE_HOST_ROMS_ROOT", str(paths.rom_root),
        "--setenv", "EMBERCADE_HOST_BIOS_ROOT", str(paths.bios_root),
        "--setenv", "PYTHONPATH", "/app/share/embercade/app",
        "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        "--setenv", "LD_LIBRARY_PATH", "/app/share/embercade/lib",
        "--setenv", "SDL_GAMECONTROLLER_ALLOW_STEAM_VIRTUAL_GAMEPAD", "0",
        "--setenv", "SDL_JOYSTICK_HIDAPI_WII", "0",
        "--unsetenv", "SDL_GAMECONTROLLER_IGNORE_DEVICES",
        "--unsetenv", "SDL_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT",
        *optional_variables,
        "--unsetenv", "EMBERCADE_SCREENSCRAPER_SECRET_FILE",
        "--unsetenv", "EMBERCADE_SCREENSCRAPER_BUILD_SECRET_FILE",
        *scraper_variables,
        *policy_variables,
        "--chdir", "/userdata",
        "/app/share/embercade/frontend/emulationstation",
        *frontend_branding,
        *frontend_arguments,
    ]
    return tuple(command)


def run_production(
    layout: ProductionLayout,
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    *,
    environment: Mapping[str, str] | None = None,
    frontend_arguments: Sequence[str] = (),
) -> int:
    command = production_command(
        layout,
        paths,
        config,
        environment=environment,
        frontend_arguments=frontend_arguments,
    )
    return subprocess.run(command, check=False).returncode

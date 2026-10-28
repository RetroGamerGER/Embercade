"""Read-only host requirement discovery and an explicit Arch package plan."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence, TextIO
import os
import shutil
import subprocess

from embercade.controller_exit import load_host_evdev
from embercade.cores import CoreResolutionError, LibretroCoreResolver
from embercade.executables import (
    ExecutableResolutionError,
    ExecutableResolver,
    ProviderType,
)
from embercade import imports as managed_imports
from embercade.elf_runtime import direct_elf_sonames, inspect_elf_runtime
from embercade.rom_inventory import BatoceraSystem, load_batocera_systems


SUPPORTED_DISTRO_IDS = frozenset({"arch", "cachyos", "garuda"})


@dataclass(frozen=True, slots=True)
class DistroInfo:
    distro_id: str
    name: str
    id_like: tuple[str, ...]

    @property
    def supports_automatic_install(self) -> bool:
        return self.distro_id in SUPPORTED_DISTRO_IDS


@dataclass(frozen=True, slots=True)
class HostRequirement:
    key: str
    label: str
    package: str | None
    executable: str | None = None
    emulator: str | None = None
    probe: str | None = None
    required: bool = True
    reason: str = "Embercade 0.1 production host requirement"
    # Also a repository fallback when the target already configures a source
    # providing this exact package (e.g. Chaotic-AUR). Probe pacman before AUR.
    aur_package: str | None = None


@dataclass(frozen=True, slots=True)
class RequirementStatus:
    requirement: HostRequirement
    installed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class CoreRequirementStatus:
    core: str
    installed: bool
    detail: str
    package: str | None


@dataclass(frozen=True, slots=True)
class XeniaProviderStatus:
    """Read-only diagnosis of the existing Xenia provider resolution."""

    status: str
    detail: str
    path: str | None = None
    source: str | None = None
    needed: bool = False

    @property
    def available(self) -> bool:
        return self.status in {"MANAGED", "OVERRIDE", "FOUND"}

    @property
    def summary(self) -> str:
        return {
            "MANAGED": "ready, managed copy",
            "OVERRIDE": "ready, explicit override",
            "FOUND": "ready, host provider" if self.source == "PATH" else "ready, external provider",
            "UNSELECTED": "found, run setup to select it",
            "MISSING": "missing" if self.needed else "optional, configured file missing",
            "INVALID": "invalid or unreadable",
            "UNVERIFIED": "not verified; inspection tool required or timed out",
            "AMBIGUOUS": "multiple candidates, choose one in setup",
            "OPTIONAL": "optional, not needed for this collection",
            "RUNTIME_DEPENDENCY_MISSING": "runtime dependencies missing",
        }[self.status]


@dataclass(frozen=True, slots=True)
class HostAssessment:
    distro: DistroInfo
    requirements: tuple[RequirementStatus, ...]
    cores: tuple[CoreRequirementStatus, ...]
    active_systems: tuple[str, ...]
    xenia_edge: str | None = None
    rpcs3_firmware: str | None = None
    xemu_firmware: str | None = None
    xemu_eeprom: str | None = None
    xemu_hdd: str | None = None
    xenia_provider: XeniaProviderStatus | None = None
    opera_bios: str | None = None
    shadps4_provider: XeniaProviderStatus | None = None
    active_emulators: tuple[str, ...] = ()

    @property
    def missing_packages(self) -> tuple[str, ...]:
        packages = {
            status.requirement.package
            for status in self.requirements
            if not status.installed and status.requirement.package
        }
        packages.update(
            status.package for status in self.cores if not status.installed and status.package
        )
        return tuple(sorted(package for package in packages if package))


@dataclass(frozen=True, slots=True)
class BootstrapPlan:
    assessment: HostAssessment
    packages: tuple[str, ...]
    unavailable_packages: tuple[str, ...] = ()
    aur_packages: tuple[str, ...] = ()
    aur_helper: str | None = None

    @property
    def command(self) -> tuple[str, ...]:
        if not self.packages:
            return ()
        return ("sudo", "pacman", "-S", "--needed", *self.packages)


# This is the only package mapping used by bootstrap. Each non-null entry is a
# conservative repository candidate that is still probed with pacman on the
# current host. Never infer package availability from the distro name or from
# repositories configured on another host.
HOST_REQUIREMENTS: tuple[HostRequirement, ...] = (
    HostRequirement(
        "libretro-shaders", "RetroArch shader collection", "libretro-shaders-slang",
        probe="libretro-shaders", required=False,
        reason="official Libretro Slang presets, textures and LUTs; optional effects",
    ),
    HostRequirement(
        "vlc-video", "Library video playback", "vlc-plugin-ffmpeg", probe="vlc-video",
        reason="libVLC video decoding and RGBA conversion for frontend previews",
    ),
    HostRequirement(
        "vulkan-tools", "Vulkan detection", "vulkan-tools", executable="vulkaninfo",
        required=False, reason="automatic graphics capability detection",
    ),
    HostRequirement(
        "python", "Python runtime", "python", executable="python",
        reason="host bridge and command runtime",
    ),
    HostRequirement(
        "binutils", "ELF inspection", "binutils", executable="readelf",
        reason="actual frontend/core ABI and dependency checks",
    ),
    HostRequirement(
        "bubblewrap", "Bubblewrap isolation", "bubblewrap", executable="bwrap",
        reason="desktop frontend isolation",
    ),
    HostRequirement(
        "evdev", "Select+Start exit bridge", "python-evdev", probe="evdev",
        reason="native controller exit bridge",
    ),
    HostRequirement(
        "retroarch", "RetroArch", "retroarch", emulator="retroarch",
        reason="proven Libretro launch routes",
    ),
    HostRequirement(
        "dolphin", "Dolphin", "dolphin-emu", emulator="dolphin",
        reason="proven GameCube and Wii routes",
    ),
    HostRequirement(
        "pcsx2", "PCSX2", "pcsx2", emulator="pcsx2",
        reason="proven PlayStation 2 route",
        aur_package="pcsx2-git",
    ),
    HostRequirement(
        "rpcs3", "RPCS3", "rpcs3", emulator="rpcs3",
        reason="proven PlayStation 3 route",
        aur_package="rpcs3-git",
    ),
    HostRequirement(
        "xemu", "Xemu", "xemu", emulator="xemu",
        reason="proven original Xbox route",
        aur_package="xemu-git",
    ),
)

XENIA_SCOPE_REQUIREMENT = HostRequirement(
    "systemd-run", "Xenia process scope", "systemd", executable="systemd-run",
    reason="scoped external Xenia provider execution"
)
XENIA_FUSE_REQUIREMENT = HostRequirement(
    "fuse2", "AppImage FUSE 2 runtime", "fuse2", probe="fuse2",
    reason="user-supplied Xenia AppImage mounting"
)

# Only exact logical-core/file mappings verified from repository file lists.
CORE_ARCH_PACKAGES: Mapping[str, str] = {
    "nestopia": "libretro-nestopia",
    "mgba": "libretro-mgba",
    "gambatte": "libretro-gambatte",
    "flycast": "libretro-flycast",
    "genesisplusgx": "libretro-genesis-plus-gx",
    "mupen64plus-next": "libretro-mupen64plus-next",
    "pce": "libretro-beetle-pce",
    "mednafen_psx": "libretro-beetle-psx-hw",
    "picodrive": "libretro-picodrive",
    "snes9x": "libretro-snes9x",
    "ppsspp": "libretro-ppsspp",
}


def read_os_release(path: Path = Path("/etc/os-release")) -> DistroInfo:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return DistroInfo("unknown", "Unknown Linux", ())
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key] = value
    distro_id = values.get("ID", "unknown").casefold()
    return DistroInfo(
        distro_id,
        values.get("PRETTY_NAME", values.get("NAME", distro_id)),
        tuple(value.casefold() for value in values.get("ID_LIKE", "").split()),
    )


def _read_batocera_values(paths: Iterable[Path]) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", ";")) or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _system_has_content(rom_root: Path, system: BatoceraSystem) -> bool:
    directory = rom_root / system.path_name
    if not directory.is_dir() or directory.is_symlink():
        return False
    extensions = set(system.extensions)
    try:
        for base, directories, files in os.walk(directory, followlinks=False):
            directories[:] = [
                name for name in directories
                if name not in {"images", "videos", "manuals", "magazines", ".tmp"}
                and not (Path(base) / name).is_symlink()
            ]
            if system.system == "ps3":
                if Path(base).name.casefold().endswith(".ps3") or "PS3_GAME" in directories:
                    return True
            if system.system == "ps4" and Path(base).suffix.casefold() == ".ps4":
                eboot = Path(base) / "eboot.bin"
                if eboot.is_file() and not eboot.is_symlink() and os.access(eboot, os.R_OK):
                    return True
            for name in files:
                path = Path(base) / name
                if not path.is_symlink() and path.suffix.casefold() in extensions:
                    return True
    except OSError:
        return False
    return False


def _active_routes(
    rom_root: Path,
    systems_config: Path,
    default_config: Path,
    user_config: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if not rom_root.is_dir() or not systems_config.is_file():
        return (), (), ()
    systems = load_batocera_systems(systems_config)
    values = _read_batocera_values((default_config, user_config))
    active_systems: list[str] = []
    cores: set[str] = set()
    emulators: set[str] = set()
    for system in systems:
        if not _system_has_content(rom_root, system):
            continue
        active_systems.append(system.system)
        emulator = values.get(f"{system.system}.emulator", system.default_emulator or "")
        emulators.add("retroarch" if emulator == "libretro" else emulator)
        core = values.get(f"{system.system}.core", system.default_core or "")
        if emulator == "libretro" and core:
            cores.add(core)
    return tuple(sorted(active_systems)), tuple(sorted(cores)), tuple(sorted(emulators))


def active_libretro_cores(rom_root, systems_config, default_config, user_config):
    systems, cores, _ = _active_routes(rom_root, systems_config, default_config, user_config)
    return systems, cores


def _probe_requirement(
    requirement: HostRequirement,
    resolver: ExecutableResolver,
    environment: Mapping[str, str],
) -> RequirementStatus:
    if requirement.emulator:
        try:
            resolved = resolver.resolve(requirement.emulator)
        except ExecutableResolutionError as error:
            return RequirementStatus(requirement, False, str(error))
        return RequirementStatus(requirement, True, str(resolved.path))
    if requirement.executable:
        candidate = shutil.which(requirement.executable, path=environment.get("PATH"))
        return RequirementStatus(
            requirement,
            candidate is not None,
            candidate or f"'{requirement.executable}' is unavailable on PATH",
        )
    if requirement.probe == "libretro-shaders":
        from embercade.shaders import find_host_shader_root, dependency_graph, ShaderResourceError

        root = find_host_shader_root(environment)
        try:
            if root is None:
                raise ShaderResourceError("libretro-shaders-slang is unavailable")
            dependency_graph(root, (root / "crt/newpixie-crt.slangp",))
        except (OSError, UnicodeError, ShaderResourceError) as error:
            return RequirementStatus(requirement, False, str(error))
        return RequirementStatus(requirement, True, str(root))
    if requirement.probe == "vlc-video":
        from embercade.video_runtime import video_runtime_failures
        failures = video_runtime_failures()
        return RequirementStatus(requirement, not failures, "; ".join(failures) if failures else "VLC video modules available")
    if requirement.probe == "evdev":
        try:
            module = load_host_evdev()
        except ImportError:
            return RequirementStatus(requirement, False, "python-evdev is unavailable")
        return RequirementStatus(requirement, True, str(getattr(module, "__file__", "available")))
    if requirement.probe == "gtk-layer-shell":
        try:
            completed = subprocess.run(["/usr/bin/python", "-I", "-B", "-c",
                "import gi; gi.require_version('GtkLayerShell', '0.1'); from gi.repository import GtkLayerShell"],
                capture_output=True, timeout=5, check=False)
            found = completed.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            found = False
        return RequirementStatus(requirement, found, "available" if found else "GTK layer-shell typelib unavailable")
    if requirement.probe == "python-cairo":
        try:
            completed = subprocess.run(["/usr/bin/python", "-I", "-B", "-c",
                "import cairo, gi; gi.require_foreign('cairo'); "
                "cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)); cairo.Region()"],
                capture_output=True, timeout=5, check=False)
            found = completed.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            found = False
        return RequirementStatus(requirement, found, "available" if found else "Python Cairo drawing support unavailable")
    if requirement.probe == "fuse2":
        candidates = (Path("/usr/lib/libfuse.so.2"), Path("/usr/lib64/libfuse.so.2"))
        found = next((path for path in candidates if path.is_file()), None)
        return RequirementStatus(
            requirement, found is not None, str(found) if found else "libfuse.so.2 is unavailable"
        )
    raise ValueError(f"unknown host requirement probe: {requirement.key}")


def _provider_error_status(error: Exception) -> str:
    detail = str(error).casefold()
    if "cannot inspect appimage identity" in detail or "metadata inspection timed out" in detail:
        return "UNVERIFIED"
    return "INVALID"


def inspect_appimage_provider(
    resolver: ExecutableResolver,
    environment: Mapping[str, str],
    *,
    needed: bool,
    provider_name: str = "xenia-edge",
) -> XeniaProviderStatus:
    """Keep override precedence while explaining optional provider failures."""
    from embercade.setup_flow import (
        SetupError,
        detect_xenia_edge,
        recommended_xenia_directory,
    )

    managed = recommended_xenia_directory(environment)
    label = "Xenia Edge" if provider_name == "xenia-edge" else "shadPS4"
    if provider_name != "xenia-edge":
        managed = managed.parent / managed_imports.KNOWN_APPIMAGES[provider_name][0]
    override = resolver.configured.get(provider_name)
    configured = resolver.providers.get(provider_name)
    candidate = override or (configured.executable if configured else None)
    source = "executables override" if override else "configured provider" if configured else "PATH"
    try:
        if provider_name == "shadps4" and not override and not configured:
            raise ExecutableResolutionError("shadPS4 is not selected")
        resolved = resolver.resolve(provider_name)
    except ExecutableResolutionError as error:
        if override or configured:
            path = Path(candidate).expanduser() if candidate else None
            missing = bool(path and path.is_absolute() and not path.exists())
            return XeniaProviderStatus(
                "MISSING" if missing else _provider_error_status(error),
                str(error),
                str(path) if path else None,
                source,
                needed,
            )
        try:
            if provider_name == "xenia-edge":
                discovered = detect_xenia_edge({}, environment)
            elif managed.exists() or managed.is_symlink():
                candidates, skipped, _found = managed_imports.provider_candidates(managed, provider=provider_name, require_executable=True)
                if len(candidates) > 1:
                    raise SetupError("Multiple different shadPS4 AppImages found; choose explicitly.")
                if not candidates and skipped:
                    raise SetupError(skipped[0])
                discovered = next(iter(candidates.values()), None)
            else:
                discovered = None
        except (SetupError, managed_imports.ImportError) as discovery_error:
            ambiguous = "multiple" in str(discovery_error).casefold()
            return XeniaProviderStatus(
                "AMBIGUOUS" if ambiguous else _provider_error_status(discovery_error),
                str(discovery_error),
                source="managed discovery",
                needed=needed,
            )
        if discovered is not None:
            return XeniaProviderStatus(
                "UNSELECTED",
                "A valid managed copy is available; run embercade setup to select it.",
                str(discovered),
                "managed discovery",
                needed,
            )
        if managed.is_dir():
            try:
                candidates = sorted(managed.iterdir())
            except OSError as inspection_error:
                return XeniaProviderStatus(
                    "INVALID", f"Managed provider directory is unreadable: {inspection_error}",
                    str(managed), "managed discovery", needed,
                )
            for path in candidates:
                if path.suffix.casefold() != ".appimage":
                    continue
                try:
                    managed_imports.inspect_provider(path, require_executable=True, provider=provider_name)
                except managed_imports.ImportError as inspection_error:
                    if str(inspection_error).startswith("unsupported provider"):
                        continue
                    return XeniaProviderStatus(
                        _provider_error_status(inspection_error), str(inspection_error),
                        str(path), "managed discovery", needed,
                    )
        return XeniaProviderStatus(
            "MISSING" if needed else "OPTIONAL",
            f"No {provider_name} provider is configured."
            if needed else f"{label} is optional for this collection; no provider is configured.",
            needed=needed,
        )

    is_appimage = resolved.provider_type is ProviderType.APPIMAGE or (
        resolved.provider_type is ProviderType.EXPLICIT
        and resolved.path.suffix.casefold() == ".appimage"
    )
    if is_appimage:
        try:
            if provider_name == "xenia-edge":
                managed_imports.inspect_provider(resolved.path, require_executable=True)
            else:
                managed_imports.inspect_provider(resolved.path, require_executable=True, provider=provider_name)
                dependencies = list(managed_imports.provider_runtime_dependencies(resolved.path, provider=provider_name))
                dependencies.extend(appimage_host_dependencies(resolved.path, environment))
                if dependencies:
                    return XeniaProviderStatus("RUNTIME_DEPENDENCY_MISSING", ", ".join(dependencies),
                                               str(resolved.path), source, needed)
        except managed_imports.ImportError as error:
            return XeniaProviderStatus(
                _provider_error_status(error), str(error), str(resolved.path), source, needed,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return XeniaProviderStatus(
                "UNVERIFIED", "Provider dependency inspection could not complete: " + type(error).__name__,
                str(resolved.path), source, needed,
            )
    if resolved.path.is_relative_to(managed) and is_appimage:
        status = "MANAGED"
    elif override or resolved.provider_type is ProviderType.EXPLICIT:
        status = "OVERRIDE"
    else:
        status = "FOUND"
    return XeniaProviderStatus(
        status,
        f"Readable, executable managed {label} AppImage."
        if status == "MANAGED" else "Explicit provider override is readable and executable."
        if status == "OVERRIDE" else f"External {label} AppImage is readable and executable."
        if is_appimage else "Host Xenia Edge executable is available on PATH.",
        str(resolved.path),
        source,
        needed,
    )


def appimage_host_dependencies(binary: Path, environment: Mapping[str, str]) -> tuple[str, ...]:
    """Inspect the actual outer runtime; static FUSE3 runtimes need no libfuse2.

    This is a dependency check, not evidence that an AppImage/game can run.
    The cleanup helper accepts either fusermount implementation, like the runner.
    """
    missing = []
    if not shutil.which("systemd-run", path=environment.get("PATH")):
        missing.append("systemd-run")
    if not any(shutil.which(name, path=environment.get("PATH"))
               for name in ("fusermount3", "fusermount")):
        missing.append("fusermount3/fusermount")
    direct, error = direct_elf_sonames(binary)
    if error:
        raise managed_imports.ImportError("AppImage runtime inspection failed: " + error)
    if direct:
        closure = inspect_elf_runtime(binary, environment=environment)
        if closure.error:
            raise managed_imports.ImportError(closure.error)
        missing.extend(closure.missing)
    return tuple(sorted(set(missing)))


def inspect_xenia_provider(resolver: ExecutableResolver, environment: Mapping[str, str],
                          *, needed: bool) -> XeniaProviderStatus:
    return inspect_appimage_provider(resolver, environment, needed=needed)


def assess_host(
    *,
    resolver: ExecutableResolver,
    core_resolver: LibretroCoreResolver,
    environment: Mapping[str, str],
    rom_root: Path,
    systems_config: Path,
    default_config: Path,
    user_config: Path,
    distro: DistroInfo | None = None,
) -> HostAssessment:
    active_systems, cores, emulators = _active_routes(
        rom_root, systems_config, default_config, user_config
    )
    requirements = list(HOST_REQUIREMENTS)
    desktop = environment.get("XDG_CURRENT_DESKTOP", "").upper()
    desktop_decorations = (environment.get("WAYLAND_DISPLAY") and not environment.get("GAMESCOPE_WAYLAND_DISPLAY")
                           and ("KDE" in desktop or environment.get("HYPRLAND_INSTANCE_SIGNATURE")))
    if desktop_decorations:
        requirements.append(HostRequirement("gtk-layer-shell", "Wayland decorations", "gtk-layer-shell",
                                           probe="gtk-layer-shell", required=False))
    if desktop_decorations or (environment.get("GAMESCOPE_WAYLAND_DISPLAY") and environment.get("DISPLAY")):
        # Every shared renderer uses Pycairo, including Gamescope. Finding the
        # layer-shell typelib alone does not prove its GTK draw callback works.
        requirements.append(HostRequirement("python-cairo", "Standalone decoration drawing", "python-cairo",
                                           probe="python-cairo", required=False))
    if environment.get("GAMESCOPE_WAYLAND_DISPLAY") or (environment.get("DISPLAY") and not environment.get("WAYLAND_DISPLAY")):
        requirements.append(HostRequirement("display-query", "Display size detection", "xorg-xrandr", executable="xrandr"))
    elif environment.get("WAYLAND_DISPLAY") and "KDE" in desktop:
        requirements.append(HostRequirement("display-query", "Display size detection", "kscreen", executable="kscreen-doctor"))
    provider_status = inspect_xenia_provider(
        resolver, environment, needed="xbox360" in active_systems,
    )
    xenia_edge = provider_status.path if provider_status.available else None
    if provider_status.available:
        try:
            xenia_resolution = resolver.resolve("xenia-edge")
        except ExecutableResolutionError as error:
            # A user may replace/remove the file between the read-only probes.
            path = Path(provider_status.path)
            provider_status = XeniaProviderStatus(
                "MISSING" if not path.exists() else _provider_error_status(error),
                str(error), str(path), provider_status.source, provider_status.needed,
            )
            xenia_edge = None
        else:
            requirements.append(XENIA_SCOPE_REQUIREMENT)
            if xenia_resolution.provider_type is ProviderType.APPIMAGE:
                requirements.append(XENIA_FUSE_REQUIREMENT)
    statuses = tuple(
        _probe_requirement(requirement, resolver, environment) for requirement in requirements
    )
    shadps4_status = inspect_appimage_provider(resolver, environment, needed="ps4" in active_systems,
                                             provider_name="shadps4")
    core_statuses: list[CoreRequirementStatus] = []
    for core in cores:
        try:
            resolved = core_resolver.resolve(core)
        except CoreResolutionError as error:
            core_statuses.append(
                CoreRequirementStatus(core, False, str(error), CORE_ARCH_PACKAGES.get(core))
            )
        else:
            core_statuses.append(
                CoreRequirementStatus(core, True, str(resolved.path), CORE_ARCH_PACKAGES.get(core))
            )
    return HostAssessment(
        distro or read_os_release(), statuses, tuple(core_statuses), active_systems,
        xenia_edge, xenia_provider=provider_status, shadps4_provider=shadps4_status,
        active_emulators=emulators,
    )


class Pacman:
    """Small argv-only adapter; it never invokes a shell or updates the system."""

    def __init__(self, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run):
        self.runner = runner

    def available(self, package: str) -> bool:
        completed = self.runner(
            ["pacman", "-Si", "--", package],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return completed.returncode == 0

    def install(self, packages: Sequence[str]) -> int:
        if not packages:
            return 0
        completed = self.runner(
            ["sudo", "pacman", "-S", "--needed", *packages],
            check=False,
            text=True,
        )
        return completed.returncode


class AurHelper:
    """Optional existing AUR helper; discovery never installs or configures one."""

    def __init__(
        self,
        executable: str,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.executable = executable
        self.runner = runner

    @classmethod
    def detect(
        cls,
        environment: Mapping[str, str] | None = None,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> "AurHelper | None":
        env = os.environ if environment is None else environment
        for name in ("paru", "yay"):
            if executable := shutil.which(name, path=env.get("PATH")):
                return cls(executable, runner)
        return None

    def available(self, package: str) -> bool:
        completed = self.runner(
            [self.executable, "-Si", "--", package],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return completed.returncode == 0

    def install(self, packages: Sequence[str]) -> int:
        if not packages:
            return 0
        completed = self.runner(
            [self.executable, "-S", "--needed", *packages], check=False, text=True
        )
        return completed.returncode


def create_bootstrap_plan(
    assessment: HostAssessment,
    pacman: Pacman | None = None,
    aur_helper: AurHelper | None = None,
) -> BootstrapPlan:
    if not assessment.distro.supports_automatic_install:
        return BootstrapPlan(assessment, ())
    adapter = pacman or Pacman()
    packages: list[str] = []
    unavailable: list[str] = []
    aur_packages: list[str] = []
    fallbacks = {
        status.requirement.package: status.requirement.aur_package
        for status in assessment.requirements
        if not status.installed and status.requirement.aur_package
    }
    for package in assessment.missing_packages:
        if adapter.available(package):
            packages.append(package)
        elif (candidate := fallbacks.get(package)) and adapter.available(candidate):
            packages.append(candidate)
        else:
            unavailable.append(package)
    if aur_helper is not None:
        for status in assessment.requirements:
            candidate = status.requirement.aur_package
            if (
                not status.installed
                and candidate
                and status.requirement.package not in packages
                and candidate not in packages
                and aur_helper.available(candidate)
            ):
                aur_packages.append(candidate)
    return BootstrapPlan(
        assessment,
        tuple(packages),
        tuple(unavailable),
        tuple(aur_packages),
        aur_helper.executable if aur_helper is not None else None,
    )


def render_host_summary(
    assessment: HostAssessment, stream: TextIO, *, verbose: bool = False
) -> None:
    installed = sum(status.installed for status in assessment.requirements)
    print(
        f"Host ({assessment.distro.name}): {installed}/{len(assessment.requirements)} "
        "runtime requirements available",
        file=stream,
    )
    for status in assessment.requirements:
        state = "OK" if status.installed else "MISSING"
        detail = f"  {status.detail}" if verbose else ""
        print(f"  {status.requirement.label:26} {state:7}{detail}", file=stream)
    for status in assessment.cores:
        state = "OK" if status.installed else "CORE MISSING"
        package = (
            f" (package: {status.package})"
            if verbose and status.package and not status.installed
            else ""
        )
        print(f"  Libretro {status.core:17} {state}{package}", file=stream)
    required_cores = len(assessment.cores)
    installed_cores = sum(status.installed for status in assessment.cores)
    print(f"Libretro: required cores {installed_cores}/{required_cores}", file=stream)
    diagnosis = assessment.xenia_provider
    if diagnosis is not None:
        xenia_status = diagnosis.summary
    elif assessment.xenia_edge:
        xenia_status = assessment.xenia_edge if verbose else "READY"
    else:
        xenia_status = "NOT CONFIGURED"
    print(f"External: Xenia Edge     {xenia_status}", file=stream)
    if assessment.shadps4_provider is not None:
        print(f"External: shadPS4        {assessment.shadps4_provider.summary}", file=stream)
        if verbose:
            print(f"  {assessment.shadps4_provider.status}: {assessment.shadps4_provider.detail}", file=stream)
    if diagnosis is not None and verbose:
        print(f"  {diagnosis.status}: {diagnosis.detail}", file=stream)
        if diagnosis.path:
            print(f"  {diagnosis.path} ({diagnosis.source})", file=stream)
    if assessment.rpcs3_firmware is not None:
        print(f"PS3 firmware:             {assessment.rpcs3_firmware}", file=stream)
    if assessment.opera_bios is not None:
        print(f"3DO BIOS:                 {assessment.opera_bios}", file=stream)
    if assessment.xemu_firmware is not None:
        print(f"Xemu firmware:            {assessment.xemu_firmware}", file=stream)
        print(f"Xemu EEPROM:              {assessment.xemu_eeprom}", file=stream)
        print(f"Xemu HDD:                 {assessment.xemu_hdd}", file=stream)
    if not assessment.distro.supports_automatic_install:
        print(
            "Automatic dependency installation is currently supported on Arch/CachyOS/Garuda. "
            "Run 'embercade doctor' to see the required host components. "
            f"Detected distro ID: {assessment.distro.distro_id}. No packages will be installed.",
            file=stream,
        )


def render_bootstrap_plan(
    plan: BootstrapPlan, stream: TextIO, *, verbose: bool = False
) -> None:
    render_host_summary(plan.assessment, stream, verbose=verbose)
    print("", file=stream)
    if plan.packages:
        print("Can be installed automatically:", file=stream)
        package_set = set(plan.packages)
        for status in plan.assessment.requirements:
            if status.requirement.package in package_set or status.requirement.aur_package in package_set:
                suffix = " (repository development package)" if status.requirement.aur_package in package_set else ""
                print(f"  {status.requirement.label}{suffix}", file=stream)
        for status in plan.assessment.cores:
            if status.package in package_set:
                print(f"  Libretro core: {status.core}", file=stream)
        if verbose:
            print("Advanced package details:", file=stream)
            print("  sudo pacman -S --needed " + " ".join(plan.packages), file=stream)
    elif plan.assessment.distro.supports_automatic_install:
        print("No repository-backed package changes are needed or safely mappable.", file=stream)
    if plan.unavailable_packages:
        print(
            "Unavailable in configured pacman repositories "
            "(not installed automatically):",
            file=stream,
        )
        for package in plan.unavailable_packages:
            label = next(
                (s.requirement.label for s in plan.assessment.requirements if s.requirement.package == package),
                package,
            )
            print(f"  {label}" + (f" ({package})" if verbose else ""), file=stream)
    if plan.aur_packages:
        print("Requires an optional community package source:", file=stream)
        for package in plan.aur_packages:
            label = next(
                (
                    status.requirement.label
                    for status in plan.assessment.requirements
                    if status.requirement.aur_package == package
                ),
                package.removesuffix("-git"),
            )
            print(f"  {package if verbose else label}", file=stream)


def run_bootstrap(
    plan: BootstrapPlan,
    *,
    dry_run: bool,
    input_function: Callable[[str], str] = input,
    stream: TextIO,
    pacman: Pacman | None = None,
    aur_helper: AurHelper | None = None,
    verbose: bool = False,
    language: str | None = None,
    progress: Callable[[str], None] | None = None,
) -> int:
    from embercade.i18n import Translator
    t = Translator(language or "en")
    announce = progress or (lambda _phase: None)
    if language:
        print(t("Host package installation"), file=stream)
        for key, message in (("packages", "Installable repository packages: {packages}"),
                             ("unavailable_packages", "Unavailable packages: {packages}"),
                             ("aur_packages", "Optional community packages: {packages}")):
            packages = getattr(plan, key)
            if packages:
                print(t(message, packages=", ".join(packages)), file=stream)
        if not plan.packages and not plan.aur_packages:
            print(t("No packages to install."), file=stream)
        if not plan.assessment.distro.supports_automatic_install:
            print(t("Automatic installation is unavailable on this distribution."), file=stream)
    else:
        render_bootstrap_plan(plan, stream, verbose=verbose)
    if dry_run:
        print("", file=stream)
        print(t("No changes made.") if language else "NO CHANGES MADE", file=stream)
        return 0
    if not plan.assessment.distro.supports_automatic_install:
        return 2
    if plan.unavailable_packages and not plan.packages and not plan.aur_packages:
        return 1
    result = 0
    prefer_git = False
    if plan.aur_packages and aur_helper is not None:
        announce("confirmation")
        answer = input_function(t("Prefer development/git packages? [y/N] ")).strip().casefold()
        prefer_git = answer in {"y", "yes", "j", "ja"}
    stable_packages = plan.packages
    if prefer_git:
        replaced = {package.removesuffix("-git") for package in plan.aur_packages}
        stable_packages = tuple(package for package in plan.packages if package not in replaced)
    if stable_packages and plan.assessment.distro.supports_automatic_install:
        announce("confirmation")
        answer = input_function(t("Install available repository packages? [y/N] ")).strip().casefold()
        if answer in {"y", "yes", "j", "ja"}:
            announce("repository")
            result = (pacman or Pacman()).install(stable_packages)
        else:
            print(t("No repository packages installed."), file=stream)
            return 130
    if result == 0 and prefer_git and aur_helper is not None:
        announce("confirmation")
        answer = input_function(t("Install selected community packages? [y/N] ")).strip().casefold()
        if answer in {"y", "yes", "j", "ja"}:
            announce("community")
            result = aur_helper.install(plan.aur_packages)
        else:
            print(t("No community packages installed."), file=stream)
            return 130
    if result:
        print(t("Host package installation failed or was cancelled (exit {code}). Review the package-manager output above before retrying.", code=result), file=stream)
    return result

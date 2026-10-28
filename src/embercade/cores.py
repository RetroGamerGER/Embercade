"""Host Libretro discovery and Batocera 44 core-name resolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import os
import re

from embercade.paths import EmbercadePaths


CORE_SUFFIX = "_libretro.so"
INFO_SUFFIX = "_libretro.info"

# Batocera renames several upstream core binaries while packaging them.  Desktop
# distributions generally keep the upstream filename, so these candidates are
# tried after Batocera's own expected filename, within the same directory.
BATOCERA_44_BINARY_ALIASES: Mapping[str, tuple[str, ...]] = {
    "beetle-saturn": ("mednafen_saturn_hw", "mednafen_saturn"),
    "bsnes_hd": ("bsnes_hd_beta",),
    "ep128emu-core": ("ep128emu_core",),
    "fbalpha": ("fbalpha2012",),
    "flycastvl": ("flycast",),
    "genesisplusgx": ("genesis_plus_gx",),
    "genesisplusgx-expanded": ("genesis_plus_gx",),
    "genesisplusgx-wide": ("genesis_plus_gx_wide",),
    "imame4all": ("mame2000",),
    "mame078plus": ("mame2003_plus",),
    # Batocera builds Beetle PSX with HAVE_HW=1 and installs that binary as
    # mednafen_psx_libretro.so.  Desktop packages expose the same build under
    # its upstream mednafen_psx_hw name, often alongside the software build.
    "mednafen_psx": ("mednafen_psx_hw",),
    # Batocera's logical package name contains a dash; upstream desktop builds
    # publish the same core with an underscore in the shared-object filename.
    "mupen64plus-next": ("mupen64plus_next",),
    "pce": ("mednafen_pce",),
    "pce_fast": ("mednafen_pce_fast",),
    "pcfx": ("mednafen_pcfx",),
    "pocketsnes": ("snes9x2002",),
    "snes9x_next": ("snes9x2010",),
    "vb": ("mednafen_vb",),
    "vba-m": ("vbam",),
}


CORE_FAMILIES: Mapping[str, tuple[str, ...]] = {
    "3DO": ("opera",),
    "NES": ("nestopia", "fceumm", "mesen"),
    "SNES": ("snes9x", "bsnes", "mesen-s"),
    "GB/GBC": ("gambatte", "tgbdual"),
    "GBA": ("mgba", "gpsp", "vba-m"),
    "Master System / Game Gear": ("genesisplusgx", "gearsystem", "smsplus"),
    "Mega Drive / Genesis": ("genesisplusgx", "picodrive", "blastem"),
    "PC Engine": ("pce", "pce_fast"),
    "Atari": ("stella", "atari800", "prosystem", "handy"),
    "Neo Geo": ("fbneo", "neocd"),
    "Arcade": ("fbneo", "mame", "mame078plus", "imame4all"),
    "PlayStation": ("mednafen_psx", "pcsx_rearmed", "swanstation"),
    "Nintendo 64": ("mupen64plus-next", "parallel_n64"),
    "Dreamcast": ("flycast",),
    "PSP": ("ppsspp",),
}


class CoreResolutionError(RuntimeError):
    """A requested Batocera core cannot be mapped to a readable host binary."""


@dataclass(frozen=True, slots=True)
class SearchDirectory:
    path: Path
    source: str
    path_type: str
    configured: bool

    def as_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload


@dataclass(frozen=True, slots=True)
class CoreResolution:
    batocera_name: str
    expected_binary: str
    path: Path
    source: str
    path_type: str
    alias: str | None
    info_path: Path | None
    probably_loadable: bool

    def as_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        payload["info_path"] = str(self.info_path) if self.info_path is not None else None
        return payload


@dataclass(frozen=True, slots=True)
class InstalledCore:
    logical_name: str
    filename: str
    path: Path
    source: str
    path_type: str
    info_path: Path | None

    def as_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        payload["info_path"] = str(self.info_path) if self.info_path is not None else None
        return payload


_SETTING_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9_]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^#;]*?))\s*(?:[#;].*)?$"
)
_PATH_SETTINGS = (
    "libretro_directory",
    "core_info_path",
    "assets_directory",
    "system_directory",
)


def _expand_path(value: str, *, home: Path, config_path: Path) -> Path | None:
    value = value.strip()
    if not value or value.casefold() == "default":
        return None
    expanded = os.path.expandvars(value)
    if expanded.startswith("~"):
        expanded = str(home) + expanded[1:]
    result = Path(expanded)
    if not result.is_absolute():
        result = config_path.parent / result
    return result.absolute()


def read_retroarch_paths(path: Path, *, home: Path) -> dict[str, Path]:
    """Read only the four path settings relevant to host-core discovery."""
    if not path.is_file():
        return {}
    settings: dict[str, Path] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _SETTING_PATTERN.match(line)
        if match is None or match.group(1) not in _PATH_SETTINGS:
            continue
        raw_value = next((value for value in match.groups()[1:] if value is not None), "")
        if (resolved := _expand_path(raw_value, home=home, config_path=path)) is not None:
            settings[match.group(1)] = resolved
    return settings


def load_batocera_catalog(path: Path) -> tuple[str, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise CoreResolutionError(f"Batocera core catalog is unavailable: {path}") from error
    names = sorted({line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")})
    if not names:
        raise CoreResolutionError(f"Batocera core catalog is empty: {path}")
    return tuple(names)


def _is_probably_loadable(path: Path) -> bool:
    if not path.is_file() or not os.access(path, os.R_OK):
        return False
    try:
        with path.open("rb") as stream:
            return stream.read(4) == b"\x7fELF"
    except OSError:
        return False


def _unique_directories(entries: Iterable[SearchDirectory]) -> tuple[SearchDirectory, ...]:
    unique: list[SearchDirectory] = []
    seen: set[Path] = set()
    for entry in entries:
        path = entry.path.absolute()
        identity = path.resolve(strict=False)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(SearchDirectory(path, entry.source, entry.path_type, entry.configured))
    return tuple(unique)


class LibretroCoreResolver:
    """Resolve Batocera logical cores against deterministic desktop paths."""

    def __init__(
        self,
        *,
        core_directories: Iterable[SearchDirectory],
        info_directories: Iterable[SearchDirectory] = (),
        overrides: Mapping[str, Path] | None = None,
        aliases: Mapping[str, tuple[str, ...]] = BATOCERA_44_BINARY_ALIASES,
        retroarch_configs: Mapping[str, Path] | None = None,
        retroarch_settings: Mapping[str, Mapping[str, Path]] | None = None,
    ) -> None:
        self.core_directories = _unique_directories(core_directories)
        self.info_directories = _unique_directories(info_directories)
        self.overrides = {name: path.absolute() for name, path in (overrides or {}).items()}
        self.aliases = aliases
        self.retroarch_configs = dict(retroarch_configs or {})
        self.retroarch_settings = {
            scope: dict(settings) for scope, settings in (retroarch_settings or {}).items()
        }

    @classmethod
    def from_host(
        cls,
        config: Mapping[str, Any],
        environment: Mapping[str, str] | None = None,
        *,
        home: Path | None = None,
        user_config: Path | None = None,
        system_config: Path | None = None,
        fallback_core_directories: Iterable[Path] | None = None,
        fallback_info_directories: Iterable[Path] | None = None,
    ) -> "LibretroCoreResolver":
        env = os.environ if environment is None else environment
        user_home = (home or Path(env.get("HOME", Path.home()))).expanduser().absolute()
        config_home = Path(env.get("XDG_CONFIG_HOME", user_home / ".config")).expanduser().absolute()
        user_config = user_config or Path(
            env.get("EMBERCADE_RETROARCH_USER_CONFIG", config_home / "retroarch" / "retroarch.cfg")
        )
        system_config = system_config or Path(
            env.get("EMBERCADE_RETROARCH_SYSTEM_CONFIG", "/etc/retroarch.cfg")
        )
        user_settings = read_retroarch_paths(user_config, home=user_home)
        system_settings = read_retroarch_paths(system_config, home=user_home)

        libretro = config.get("libretro", {})
        if not isinstance(libretro, Mapping):
            raise ValueError("[libretro] must be a TOML table")
        configured_directory = libretro.get("cores")
        if configured_directory is not None and not isinstance(configured_directory, str):
            raise ValueError("[libretro].cores must be a path string")
        configured_info = libretro.get("info")
        if configured_info is not None and not isinstance(configured_info, str):
            raise ValueError("[libretro].info must be a path string")
        configured_share = libretro.get("share")
        if configured_share is not None and not isinstance(configured_share, str):
            raise ValueError("[libretro].share must be a path string")
        raw_overrides = libretro.get("core_overrides", {})
        if not isinstance(raw_overrides, Mapping):
            raise ValueError("[libretro.core_overrides] must be a TOML table")
        overrides: dict[str, Path] = {}
        for name, value in raw_overrides.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise ValueError("Every [libretro.core_overrides] value must be a path string")
            overrides[name] = Path(value).expanduser().absolute()

        core_entries: list[SearchDirectory] = []
        if configured_directory:
            core_entries.append(
                SearchDirectory(Path(configured_directory).expanduser().absolute(), "embercade-config", "user", True)
            )
        managed = EmbercadePaths.from_environment(env, config=config).data / "cores"
        core_entries.append(SearchDirectory(managed, "embercade-managed", "user", True))
        if path := user_settings.get("libretro_directory"):
            core_entries.append(SearchDirectory(path, "retroarch-user-config", "user", True))
        if path := system_settings.get("libretro_directory"):
            core_entries.append(SearchDirectory(path, "retroarch-system-config", "system", True))
        core_fallbacks = tuple(
            (
                Path(env.get("EMBERCADE_LIBRETRO_USER_CORES", user_home / ".config/retroarch/cores")),
                Path("/usr/lib/libretro"),
                Path("/usr/lib64/libretro"),
                Path("/usr/local/lib/libretro"),
            )
            if fallback_core_directories is None
            else fallback_core_directories
        )
        for path in core_fallbacks:
            kind = "user" if path in {
                user_home / ".config/retroarch/cores",
                Path(env.get("EMBERCADE_LIBRETRO_USER_CORES", user_home / ".config/retroarch/cores")),
            } else "system"
            core_entries.append(SearchDirectory(path, f"{kind}-fallback", kind, False))

        info_entries: list[SearchDirectory] = []
        if configured_info:
            info_entries.append(
                SearchDirectory(Path(configured_info).expanduser().absolute(), "embercade-config", "user", True)
            )
        if configured_share:
            info_entries.append(
                SearchDirectory(Path(configured_share).expanduser().absolute() / "info", "embercade-share", "user", True)
            )
        if path := user_settings.get("core_info_path"):
            info_entries.append(SearchDirectory(path, "retroarch-user-config", "user", True))
        if path := system_settings.get("core_info_path"):
            info_entries.append(SearchDirectory(path, "retroarch-system-config", "system", True))
        info_fallbacks = tuple(
            (
                Path(env.get("EMBERCADE_LIBRETRO_USER_INFO", user_home / ".config/retroarch/info")),
                Path("/usr/share/libretro/info"),
                Path("/usr/local/share/libretro/info"),
            )
            if fallback_info_directories is None
            else fallback_info_directories
        )
        for path in info_fallbacks:
            kind = "user" if path in {
                user_home / ".config/retroarch/info",
                Path(env.get("EMBERCADE_LIBRETRO_USER_INFO", user_home / ".config/retroarch/info")),
            } else "system"
            info_entries.append(SearchDirectory(path, f"{kind}-fallback", kind, False))

        return cls(
            core_directories=core_entries,
            info_directories=info_entries,
            overrides=overrides,
            retroarch_configs={"user": user_config, "system": system_config},
            retroarch_settings={"user": user_settings, "system": system_settings},
        )

    @staticmethod
    def expected_binary(core_name: str) -> str:
        return f"{core_name}{CORE_SUFFIX}"

    def binary_candidates(self, core_name: str) -> tuple[str, ...]:
        if core_name == "mednafen_psx":
            return (*self.aliases.get(core_name, ()), core_name)
        return (core_name, *self.aliases.get(core_name, ()))

    def _info_for_binary(self, binary_name: str) -> Path | None:
        filename = f"{binary_name}{INFO_SUFFIX}"
        for entry in self.info_directories:
            candidate = entry.path / filename
            if candidate.is_file() and os.access(candidate, os.R_OK):
                return candidate
        return None

    def resolve(self, core_name: str) -> CoreResolution:
        if override := self.overrides.get(core_name):
            if not override.is_file() or not os.access(override, os.R_OK):
                raise CoreResolutionError(
                    f"Configured Libretro core '{core_name}' is not a readable file: {override}"
                )
            binary_name = override.name.removesuffix(CORE_SUFFIX)
            return CoreResolution(
                core_name,
                self.expected_binary(core_name),
                override,
                "embercade-override",
                "user",
                binary_name if binary_name != core_name else None,
                self._info_for_binary(binary_name),
                _is_probably_loadable(override),
            )

        for directory in self.core_directories:
            for binary_name in self.binary_candidates(core_name):
                candidate = directory.path / f"{binary_name}{CORE_SUFFIX}"
                if candidate.is_file() and os.access(candidate, os.R_OK):
                    return CoreResolution(
                        core_name,
                        self.expected_binary(core_name),
                        candidate,
                        directory.source,
                        directory.path_type,
                        binary_name if binary_name != core_name else None,
                        self._info_for_binary(binary_name),
                        _is_probably_loadable(candidate),
                    )
        searched = ", ".join(str(entry.path) for entry in self.core_directories) or "<none>"
        candidates = ", ".join(f"{name}{CORE_SUFFIX}" for name in self.binary_candidates(core_name))
        raise CoreResolutionError(
            f"Libretro core '{core_name}' is unavailable; looked for {candidates} in: {searched}"
        )

    def installed_cores(self) -> tuple[InstalledCore, ...]:
        installed: list[InstalledCore] = []
        seen_paths: set[Path] = set()
        for directory in self.core_directories:
            if not directory.path.is_dir():
                continue
            for path in sorted(directory.path.glob(f"*{CORE_SUFFIX}")):
                absolute = path.absolute()
                identity = absolute.resolve(strict=False)
                if identity in seen_paths or not path.is_file():
                    continue
                seen_paths.add(identity)
                name = path.name.removesuffix(CORE_SUFFIX)
                installed.append(
                    InstalledCore(
                        name,
                        path.name,
                        absolute,
                        directory.source,
                        directory.path_type,
                        self._info_for_binary(name),
                    )
                )
        for name, path in sorted(self.overrides.items()):
            identity = path.resolve(strict=False)
            if identity in seen_paths or not path.is_file():
                continue
            seen_paths.add(identity)
            binary_name = path.name.removesuffix(CORE_SUFFIX)
            installed.append(
                InstalledCore(
                    binary_name or name,
                    path.name,
                    path,
                    "embercade-override",
                    "user",
                    self._info_for_binary(binary_name),
                )
            )
        return tuple(sorted(installed, key=lambda item: (item.logical_name, str(item.path))))

    def catalog_status(self, names: Iterable[str]) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for name in sorted(set(names)):
            try:
                resolution = self.resolve(name)
            except CoreResolutionError:
                rows.append(
                    {
                        "batocera_name": name,
                        "expected_binary": self.expected_binary(name),
                        "host_candidates": [f"{candidate}{CORE_SUFFIX}" for candidate in self.binary_candidates(name)],
                        "path": None,
                        "source": None,
                        "path_type": None,
                        "alias": None,
                        "info_path": None,
                        "probably_loadable": False,
                    }
                )
            else:
                row = resolution.as_json()
                row["host_candidates"] = [
                    f"{candidate}{CORE_SUFFIX}" for candidate in self.binary_candidates(name)
                ]
                rows.append(row)
        return tuple(rows)

    def inventory(self, catalog_names: Iterable[str]) -> dict[str, Any]:
        installed = self.installed_cores()
        catalog = self.catalog_status(catalog_names)
        found = sum(row["path"] is not None for row in catalog)
        unique_installed = len({core.logical_name for core in installed})
        families: dict[str, list[dict[str, Any]]] = {}
        for family, names in CORE_FAMILIES.items():
            family_rows = {row["batocera_name"]: row for row in self.catalog_status(names)}
            families[family] = [family_rows[name] for name in names]
        return {
            "schema_version": 1,
            "retroarch_configs": {name: str(path) for name, path in self.retroarch_configs.items()},
            "retroarch_settings": {
                scope: {name: str(path) for name, path in settings.items()}
                for scope, settings in self.retroarch_settings.items()
            },
            "core_directories": [entry.as_json() for entry in self.core_directories],
            "info_directories": [entry.as_json() for entry in self.info_directories],
            "installed_cores": [core.as_json() for core in installed],
            "batocera_cores": list(catalog),
            "families": families,
            "summary": {
                "installed_locations": len(installed),
                "installed_unique": unique_installed,
                "batocera_catalog": len(catalog),
                "batocera_found": found,
                "batocera_missing": len(catalog) - found,
            },
        }


def write_inventory(path: Path, inventory: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

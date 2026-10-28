"""Central path model for translating Batocera paths to desktop XDG paths."""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any, Mapping
import os


def _expanded(
    value: str | PathLike[str],
    *,
    home: Path | None = None,
) -> Path:
    raw = os.fspath(value)
    if home is not None and (raw == "~" or raw.startswith("~/")):
        path = home if raw == "~" else home / raw[2:]
    else:
        path = Path(raw).expanduser()
    return path.absolute()


def _path_config(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if config is None:
        return {}
    section = config.get("paths", {})
    if not isinstance(section, Mapping):
        raise ValueError("[paths] must be a TOML table")
    for name in ("roms", "bios"):
        value = section.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"[paths].{name} must be a path string")
    return section


@dataclass(frozen=True, slots=True)
class RootValidation:
    label: str
    path: Path
    configured: bool
    status: str

    @property
    def ok(self) -> bool:
        return self.status == "OK"


@dataclass(frozen=True, slots=True)
class EmbercadePaths:
    """Resolved Embercade paths without creating anything on disk."""

    config: Path
    data: Path
    cache: Path
    state: Path
    runtime: Path
    roms: Path
    bios: Path
    roms_configured: bool = False
    bios_configured: bool = False

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        *,
        home: str | PathLike[str] | None = None,
        config: Mapping[str, Any] | None = None,
    ) -> "EmbercadePaths":
        env = os.environ if environment is None else environment
        user_home = _expanded(home if home is not None else env.get("HOME", Path.home()))
        configured_paths = _path_config(config)

        config_base = _expanded(env.get("XDG_CONFIG_HOME", user_home / ".config"), home=user_home)
        data_base = _expanded(env.get("XDG_DATA_HOME", user_home / ".local/share"), home=user_home)
        cache_base = _expanded(env.get("XDG_CACHE_HOME", user_home / ".cache"), home=user_home)
        state_base = _expanded(env.get("XDG_STATE_HOME", user_home / ".local/state"), home=user_home)

        # XDG_RUNTIME_DIR has no specification-defined fallback.  A private
        # state-directory fallback keeps diagnostics deterministic without
        # silently using a shared /tmp location.
        runtime_base = _expanded(env.get("XDG_RUNTIME_DIR", state_base / "runtime"), home=user_home)

        config_root = _expanded(env.get("EMBERCADE_CONFIG_HOME", config_base / "embercade"), home=user_home)
        data = _expanded(env.get("EMBERCADE_DATA_HOME", data_base / "embercade"), home=user_home)
        cache = _expanded(env.get("EMBERCADE_CACHE_HOME", cache_base / "embercade"), home=user_home)
        state = _expanded(env.get("EMBERCADE_STATE_HOME", state_base / "embercade"), home=user_home)
        runtime = _expanded(env.get("EMBERCADE_RUNTIME_HOME", runtime_base / "embercade"), home=user_home)

        roms_configured = "EMBERCADE_ROMS_ROOT" in env or "roms" in configured_paths
        bios_configured = "EMBERCADE_BIOS_ROOT" in env or "bios" in configured_paths
        roms_value = env.get("EMBERCADE_ROMS_ROOT", configured_paths.get("roms", data / "roms"))
        bios_value = env.get("EMBERCADE_BIOS_ROOT", configured_paths.get("bios", data / "bios"))

        return cls(
            config=config_root,
            data=data,
            cache=cache,
            state=state,
            runtime=runtime,
            roms=_expanded(roms_value, home=user_home),
            bios=_expanded(bios_value, home=user_home),
            roms_configured=roms_configured,
            bios_configured=bios_configured,
        )

    @property
    def rom_root(self) -> Path:
        return self.roms

    @property
    def bios_root(self) -> Path:
        return self.bios

    @property
    def isolated_bios(self) -> Path:
        """Embercade-owned firmware workspace, separate from the read-only BIOS root."""
        return self.data / "bios"

    @staticmethod
    def _validate_root(label: str, path: Path, configured: bool) -> RootValidation:
        if not configured:
            return RootValidation(label, path, False, "NOT CONFIGURED")
        if not path.exists():
            return RootValidation(label, path, True, "MISSING")
        if not path.is_dir():
            return RootValidation(label, path, True, "NOT A DIRECTORY")
        if not os.access(path, os.R_OK | os.X_OK):
            return RootValidation(label, path, True, "NOT READABLE")
        return RootValidation(label, path, True, "OK")

    def validate_collection_roots(self) -> tuple[RootValidation, RootValidation]:
        """Validate only root structure without enumerating any ROM or BIOS content."""
        return (
            self._validate_root("ROM root", self.rom_root, self.roms_configured),
            self._validate_root("BIOS root", self.bios_root, self.bios_configured),
        )

    @property
    def emulator_configs(self) -> Path:
        return self.config / "emulators"

    @property
    def secrets(self) -> Path:
        """Owner-only credentials; never part of staged application resources."""
        return self.config / "secrets"

    def writable_roots_inside(self, immutable_root: Path) -> tuple[str, ...]:
        """Report writable roots erroneously placed inside a read-only package."""
        immutable = immutable_root.expanduser().resolve(strict=False)
        return tuple(
            name for name, root in (
                ("config", self.config), ("data", self.data),
                ("cache", self.cache), ("state", self.state),
                ("runtime", self.runtime),
            ) if root.resolve(strict=False).is_relative_to(immutable)
        )

    def validate_application_boundary(
        self, environment: Mapping[str, str], *, targets: tuple[Path, ...] = (),
    ) -> None:
        """Reject package-local state before any CLI/wizard mutation.

        Image location never defines XDG state. HOME may legitimately contain
        both an image and normal XDG children; do not reject that common layout.
        """
        for key in ("EMBERCADE_PREFIX", "APPDIR"):
            if value := environment.get(key):
                root = Path(value).resolve(strict=False)
                conflicts = self.writable_roots_inside(root)
                if conflicts or any(target.resolve(strict=False).is_relative_to(root) for target in targets):
                    raise ValueError("Writable Embercade user state must be outside the read-only application")

    @property
    def emulationstation_config(self) -> Path:
        return self.emulator_configs / "emulationstation"

    @property
    def saves(self) -> Path:
        return self.data / "saves"

    @property
    def themes(self) -> Path:
        return self.data / "themes"

    @property
    def theme_downloads(self) -> Path:
        """Frontend-owned download/extraction workspace inside persistent themes."""
        return self.themes / ".tmp"

    @property
    def decorations(self) -> Path:
        return self.data / "decorations"

    @property
    def screenshots(self) -> Path:
        return self.data / "screenshots"

    @property
    def recordings(self) -> Path:
        return self.data / "recordings"

    @property
    def overlays(self) -> Path:
        return self.data / "overlays"

    @property
    def cheats(self) -> Path:
        return self.data / "cheats"

    @property
    def extractions(self) -> Path:
        return self.cache / "extractions"

    @property
    def logs(self) -> Path:
        return self.state / "logs"

    @property
    def batocera_conf(self) -> Path:
        return self.config / "batocera.conf"

    @property
    def shaders(self) -> Path:
        return self.data / "shaders"

    def batocera_mapping(self) -> dict[str, Path]:
        """Return the 0.1 compatibility mapping; no directories are created."""
        return {
            "/userdata/system/configs": self.emulator_configs,
            "/userdata/system/configs/emulationstation": self.emulationstation_config,
            "/userdata/system/cache": self.cache,
            "/userdata/saves": self.saves,
            "/userdata/screenshots": self.screenshots,
            "/userdata/recordings": self.recordings,
            "/userdata/bios": self.bios_root,
            "/userdata/roms": self.rom_root,
            "/userdata/overlays": self.overlays,
            "/userdata/cheats": self.cheats,
            "/userdata/extractions": self.extractions,
            "/userdata/themes": self.themes,
            "/userdata/decorations": self.decorations,
            "/userdata/shaders": self.shaders,
            "/userdata/system/logs": self.logs,
            "/userdata/system/batocera.conf": self.batocera_conf,
            "/run": self.runtime,
            "/var/run": self.runtime,
        }

    def as_dict(self) -> dict[str, Path]:
        return {
            "config": self.config,
            "data": self.data,
            "cache": self.cache,
            "state": self.state,
            "runtime": self.runtime,
            "roms": self.roms,
            "bios": self.bios,
        }

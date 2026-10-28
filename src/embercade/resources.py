"""Read-only Batocera resources used by the desktop launcher."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import os


class ResourceError(RuntimeError):
    """A required read-only UI or emulator resource is unavailable."""


def _resource_path(value: str | os.PathLike[str]) -> Path:
    return Path(value).expanduser().absolute()


@dataclass(frozen=True, slots=True)
class BatoceraResources:
    """Static resource roots shared by ES and configgen without copying them."""

    shaders: Path
    decorations: Path

    @classmethod
    def for_project(
        cls,
        project_root: Path,
        environment: Mapping[str, str] | None = None,
    ) -> "BatoceraResources":
        env = os.environ if environment is None else environment
        installed_root = project_root / "resources" / "batocera"
        default_root = (
            installed_root
            if installed_root.is_dir()
            else project_root / ".work" / "ui" / "share" / "batocera"
        )
        return cls(
            shaders=_resource_path(
                env.get("EMBERCADE_SHADER_RESOURCES", default_root / "shaders")
            ),
            decorations=_resource_path(
                env.get(
                    "EMBERCADE_DECORATION_RESOURCES",
                    default_root / "datainit" / "decorations",
                )
            ),
        )

    def validate(self) -> None:
        required = (
            self.shaders / "configs" / "rendering-defaults.yml",
            self.decorations,
        )
        for path in required:
            if not path.exists():
                raise ResourceError(f"Required Batocera resource is unavailable: {path}")

    def shader_preset(self, relative: str, suffix: str = ".slangp") -> Path:
        """Resolve and validate one configgen shader name below the static root."""
        candidate = (self.shaders / f"{relative}{suffix}").resolve()
        root = self.shaders.resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            raise ResourceError(f"Shader preset is unavailable: {candidate}")
        return candidate

    def system_bezel(self, decoration: str, system: str) -> tuple[Path, Path]:
        """Resolve the system fallback used by Batocera's Libretro bezel path."""
        root = self.decorations.resolve()
        png = (self.decorations / decoration / "systems" / f"{system}.png").resolve()
        info = png.with_suffix(".info")
        if not png.is_relative_to(root) or not png.is_file():
            raise ResourceError(f"Bezel image is unavailable: {png}")
        if not info.is_file():
            raise ResourceError(f"Bezel layout is unavailable: {info}")
        return png, info

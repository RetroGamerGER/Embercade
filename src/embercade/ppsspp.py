"""Read-only resolution of user-provided PPSSPP system assets."""

from pathlib import Path
from typing import Any, Mapping
import os

from embercade.paths import EmbercadePaths


class PpssppAssetsError(ValueError):
    """The selected asset directory is missing or incomplete."""


def validate_ppsspp_assets(source: Path) -> Path:
    """Validate a user-selected, read-only official assets directory."""
    source = source.expanduser().resolve()
    if source.exists() and (not source.is_dir() or not os.access(source, os.R_OK | os.X_OK)):
        raise PpssppAssetsError(f"PSP-Dateien: Ordner nicht lesbar: {source}")
    for kind, relative in (
        ("file", "ppge_atlas.zim"),
        ("directory", "lang"),
        ("directory", "flash0"),
    ):
        candidate = source / relative
        available = candidate.is_file() if kind == "file" else candidate.is_dir()
        mode = os.R_OK | (os.X_OK if kind == "directory" else 0)
        if not available or not os.access(candidate, mode):
            raise PpssppAssetsError(
                f"PSP-Datei fehlt: {candidate}. Wähle den vollständigen offiziellen "
                "PPSSPP-assets-Ordner mit ppge_atlas.zim, lang/ und flash0/."
            )
    return source


def resolve_ppsspp_assets(
    paths: EmbercadePaths,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
) -> Path:
    section = config.get("libretro", {})
    if not isinstance(section, Mapping):
        raise PpssppAssetsError("[libretro] must be a TOML table")
    configured = environment.get(
        "EMBERCADE_PPSSPP_ASSETS",
        section.get("ppsspp_assets", paths.data / "resources" / "PPSSPP"),
    )
    if not isinstance(configured, (str, os.PathLike)) or not str(configured).strip():
        raise PpssppAssetsError("[libretro].ppsspp_assets must be a non-empty path")
    return validate_ppsspp_assets(Path(configured))

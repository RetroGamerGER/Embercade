"""Read Batocera's effective system emulator/core choice without launching it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import json
import os
import subprocess

from embercade.backend import backend_command
from embercade.paths import EmbercadePaths
from embercade.runtime import ProjectRuntime


class BatoceraConfigError(RuntimeError):
    """Batocera's pinned configuration could not resolve a launch choice."""


@dataclass(frozen=True, slots=True)
class BatoceraSystemChoice:
    system: str
    emulator: str
    core: str
    emulator_forced: bool
    core_forced: bool


def _probe_environment(
    paths: EmbercadePaths,
    runtime: ProjectRuntime,
    environment: Mapping[str, str],
) -> dict[str, str]:
    result = dict(environment)
    result.pop("PYTHONPATH", None)
    result.update(
        {
            "PYTHONNOUSERSITE": "1",
            "HOME": str(runtime.root / "home"),
            "EMBERCADE_BATOCERA_SHARE_DIR": str(runtime.share / "batocera"),
            "EMBERCADE_USERDATA": str(paths.data),
            "EMBERCADE_HOME": str(paths.data / "system"),
            "EMBERCADE_CONFIGS": str(paths.emulator_configs),
            "EMBERCADE_BATOCERA_CONF": str(paths.batocera_conf),
            "EMBERCADE_SYSTEM_ES_DIR": str(runtime.share / "emulationstation"),
        }
    )
    return result


def resolve_system_choice(
    *,
    system: str,
    rom: Path,
    paths: EmbercadePaths,
    runtime: ProjectRuntime,
    environment: Mapping[str, str] | None = None,
) -> BatoceraSystemChoice:
    """Ask the prepared pinned runtime to apply Batocera's real config layers."""
    if not runtime.python.is_file() or not os.access(runtime.python, os.X_OK):
        raise BatoceraConfigError("Embercade runtime is not prepared; run scripts/runtime-prepare")
    if not paths.batocera_conf.is_file() or not os.access(paths.batocera_conf, os.R_OK):
        raise BatoceraConfigError(f"Batocera configuration is unavailable: {paths.batocera_conf}")

    source_environment = os.environ if environment is None else environment
    try:
        completed = subprocess.run(
            backend_command(runtime.python, "resolve-system", "--", system, str(rom)),
            check=False,
            capture_output=True,
            env=_probe_environment(paths, runtime, source_environment),
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise BatoceraConfigError(f"Batocera configuration probe failed: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise BatoceraConfigError(f"Batocera configuration probe failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
        choice = BatoceraSystemChoice(
            system=str(payload["system"]),
            emulator=str(payload["emulator"]),
            core=str(payload["core"]),
            emulator_forced=bool(payload["emulator_forced"]),
            core_forced=bool(payload["core_forced"]),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise BatoceraConfigError("Batocera configuration probe returned invalid data") from error
    if choice.system != system or not choice.emulator or not choice.core:
        raise BatoceraConfigError(f"Batocera returned an incomplete choice for system '{system}'")
    return choice

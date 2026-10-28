"""Configuration and development/installed-runtime helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os
import re
import subprocess
import tomllib

from embercade.backend import backend_command
from embercade.executables import EmulatorProvider, ProviderType


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("rb") as stream:
        value = tomllib.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Configuration root must be a table: {path}")
    return value


def executable_config(config: Mapping[str, Any]) -> dict[str, str]:
    section = config.get("executables", {})
    if not isinstance(section, Mapping):
        raise ValueError("[executables] must be a TOML table")
    result: dict[str, str] = {}
    for name, value in section.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("Every [executables] value must be a string")
        result[name] = value
    return result


def emulator_provider_config(config: Mapping[str, Any]) -> dict[str, EmulatorProvider]:
    """Read generic emulator providers without resolving or executing them."""
    section = config.get("emulators", {})
    if not isinstance(section, Mapping):
        raise ValueError("[emulators] must be a TOML table")
    result: dict[str, EmulatorProvider] = {}
    for name, raw_provider in section.items():
        if not isinstance(name, str) or not isinstance(raw_provider, Mapping):
            raise ValueError("Every [emulators] entry must be a TOML table")
        raw_type = raw_provider.get("provider")
        executable = raw_provider.get("executable")
        if raw_type is None:
            raw_type = (
                ProviderType.APPIMAGE.value
                if isinstance(executable, str) and executable.casefold().endswith(".appimage")
                else ProviderType.EXPLICIT.value
            )
        if not isinstance(raw_type, str):
            raise ValueError(f"[emulators.{name}].provider must be a string")
        try:
            provider_type = ProviderType(raw_type.casefold())
        except ValueError as error:
            known = ", ".join(provider.value for provider in ProviderType)
            raise ValueError(
                f"[emulators.{name}].provider must be one of: {known}"
            ) from error
        if executable is not None and not isinstance(executable, str):
            raise ValueError(f"[emulators.{name}].executable must be a string")
        if provider_type is not ProviderType.NATIVE and not executable:
            raise ValueError(
                f"[emulators.{name}].executable is required for {provider_type.value} providers"
            )
        result[name] = EmulatorProvider(provider_type, executable)
    return result


@dataclass(frozen=True, slots=True)
class DevelopmentLayout:
    project_root: Path

    @property
    def root(self) -> Path:
        return self.project_root / ".work" / "dev"

    @property
    def userdata(self) -> Path:
        return self.root / "userdata"

    @property
    def system_share(self) -> Path:
        return self.root / "system-share"

    @property
    def home(self) -> Path:
        return self.root / "home"


# Stable response labels, not Python API modules imported by this client.
RUNTIME_LABELS = (
    "batocera-common", "batocera-launch", "configgen", "configgen.launch",
    "libretro generator", "Dolphin generator", "PCSX2 generator", "RPCS3 generator",
    "Xemu generator", "Xenia Edge generator", "shadPS4 generator",
)


@dataclass(frozen=True, slots=True)
class ProjectRuntime:
    project_root: Path
    installed_root: Path | None = None

    @property
    def root(self) -> Path:
        return (
            self.installed_root
            if self.installed_root is not None
            else self.project_root / ".work" / "runtime"
        )

    @classmethod
    def for_application(cls, application_root: Path) -> "ProjectRuntime":
        """Select an installed runtime when present, otherwise the dev runtime."""
        installed = application_root / "runtime"
        return cls(
            application_root,
            installed_root=installed if installed.is_dir() else None,
        )

    @property
    def source_root(self) -> Path:
        return self.root / "src"

    @property
    def venv(self) -> Path:
        return self.root / "venv"

    @property
    def python(self) -> Path:
        return self.venv / "bin" / "python"

    @property
    def launcher(self) -> Path:
        return self.venv / "bin" / "batocera-launch"

    @property
    def info(self) -> Path:
        return self.root / "runtime-info.txt"

    @property
    def share(self) -> Path:
        return self.root / "share"


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    available: bool
    python_version: str | None
    imports: Mapping[str, str | None]
    cli_error: str | None

    @property
    def healthy(self) -> bool:
        return (
            self.available
            and self.python_version is not None
            and all(error is None for error in self.imports.values())
            and self.cli_error is None
        )


def locked_requirements(path: Path) -> dict[str, str]:
    requirements: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s]+)", line)
        if match is None:
            raise ValueError(f"Unpinned or unsupported runtime requirement: {line}")
        requirements[match.group(1).lower().replace("_", "-")] = match.group(2)
    return requirements


def probe_runtime(runtime: ProjectRuntime) -> RuntimeStatus:
    if not runtime.python.is_file() or not runtime.launcher.is_file():
        missing = {label: "runtime not prepared" for label in RUNTIME_LABELS}
        return RuntimeStatus(False, None, missing, "runtime not prepared")

    clean_environment = dict(os.environ)
    clean_environment.pop("PYTHONPATH", None)
    clean_environment["PYTHONNOUSERSITE"] = "1"
    clean_environment["HOME"] = str(runtime.root / "home")

    try:
        completed = subprocess.run(
            backend_command(runtime.python, "probe-runtime"),
            check=False,
            capture_output=True,
            env=clean_environment,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"probe exited {completed.returncode}"
            imports = {label: detail for label in RUNTIME_LABELS}
            return RuntimeStatus(True, None, imports, "imports unavailable")
        payload = json.loads(completed.stdout)
        if (not isinstance(payload, dict) or not isinstance(payload.get("python"), str)
                or not isinstance(payload.get("imports"), dict)
                or set(payload["imports"]) != set(RUNTIME_LABELS)
                or any(value is not None and not isinstance(value, str)
                       for value in payload["imports"].values())):
            raise ValueError("Runtime probe returned invalid data")
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        imports = {label: str(error) for label in RUNTIME_LABELS}
        return RuntimeStatus(True, None, imports, "imports unavailable")

    try:
        cli = subprocess.run(
            [str(runtime.launcher), "--help"],
            check=False,
            capture_output=True,
            env=clean_environment,
            text=True,
            timeout=30,
        )
        cli_error = None if cli.returncode == 0 else (cli.stderr.strip() or f"exit {cli.returncode}")
    except (OSError, subprocess.TimeoutExpired) as error:
        cli_error = str(error)
    return RuntimeStatus(True, payload["python"], payload["imports"], cli_error)

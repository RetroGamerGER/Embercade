"""Resolve host-provided emulator executables."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Mapping
import os
import shutil


SUPPORTED_EXECUTABLES: dict[str, str] = {
    "retroarch": "retroarch",
    "dolphin": "dolphin-emu",
    "pcsx2": "pcsx2-qt",
    "rpcs3": "rpcs3",
    "xemu": "xemu",
    "xenia-edge": "xenia_edge",
    "xenia-canary": "xenia_canary",
    "shadps4": "shadps4",
}
OPTIONAL_EXECUTABLES = frozenset({"xenia-canary", "shadps4"})


class ExecutableResolutionError(RuntimeError):
    pass


class ProviderType(str, Enum):
    NATIVE = "native"
    EXPLICIT = "explicit"
    APPIMAGE = "appimage"


@dataclass(frozen=True, slots=True)
class EmulatorProvider:
    provider_type: ProviderType
    executable: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedExecutable:
    name: str
    path: Path
    source: str
    provider_type: ProviderType


def _resolve_candidate(candidate: str | PathLike[str], path: str | None) -> Path | None:
    text = os.fspath(candidate)
    if os.sep in text:
        candidate_path = Path(text).expanduser()
        if candidate_path.is_file() and os.access(candidate_path, os.R_OK | os.X_OK):
            return candidate_path.absolute()
        return None

    located = shutil.which(text, path=path)
    return Path(located).absolute() if located else None


class ExecutableResolver:
    def __init__(
        self,
        configured: Mapping[str, str] | None = None,
        *,
        providers: Mapping[str, EmulatorProvider] | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.configured = dict(configured or {})
        self.providers = dict(providers or {})
        self.environment = os.environ if environment is None else environment

    def _resolve_provider(self, name: str, provider: EmulatorProvider) -> ResolvedExecutable:
        if name == "shadps4" and provider.provider_type is not ProviderType.APPIMAGE:
            raise ExecutableResolutionError("shadPS4 requires a user-supplied AppImage selected in setup")
        search_path = self.environment.get("PATH")
        if provider.provider_type is ProviderType.NATIVE:
            command = provider.executable or SUPPORTED_EXECUTABLES[name]
            if os.sep in command:
                raise ExecutableResolutionError(
                    f"Native provider for '{name}' must be a PATH command, not a path: {command}"
                )
            resolved = _resolve_candidate(command, search_path)
            if resolved is None:
                raise ExecutableResolutionError(
                    f"Native provider for '{name}' is unavailable on PATH: {command}"
                )
            return ResolvedExecutable(name, resolved, "PATH", ProviderType.NATIVE)

        candidate = provider.executable
        if not candidate:
            raise ExecutableResolutionError(
                f"{provider.provider_type.value} provider for '{name}' requires an executable path"
            )
        configured_path = Path(candidate).expanduser()
        if not configured_path.is_absolute():
            raise ExecutableResolutionError(
                f"Configured executable for '{name}' must be an absolute path: {candidate}"
            )
        resolved = _resolve_candidate(configured_path, search_path)
        if resolved is None:
            raise ExecutableResolutionError(
                f"Configured executable for '{name}' is unavailable, unreadable or not executable: {candidate}"
            )
        source = "appimage" if provider.provider_type is ProviderType.APPIMAGE else "config"
        return ResolvedExecutable(name, resolved, source, provider.provider_type)

    def resolve(self, name: str) -> ResolvedExecutable:
        if name not in SUPPORTED_EXECUTABLES:
            known = ", ".join(sorted(SUPPORTED_EXECUTABLES))
            raise ExecutableResolutionError(f"Unknown emulator '{name}'. Known names: {known}")

        search_path = self.environment.get("PATH")
        explicit = self.configured.get(name)
        if explicit:
            return self._resolve_provider(
                name,
                EmulatorProvider(ProviderType.EXPLICIT, explicit),
            )

        if provider := self.providers.get(name):
            return self._resolve_provider(name, provider)

        if name == "shadps4":
            raise ExecutableResolutionError("shadPS4 is not configured; select your AppImage in setup")

        command = SUPPORTED_EXECUTABLES[name]
        resolved = _resolve_candidate(command, search_path)
        if resolved is None:
            raise ExecutableResolutionError(
                f"No executable found for '{name}'. Configure [executables].{name} "
                f"or make '{command}' available on PATH."
            )
        return ResolvedExecutable(name, resolved, "PATH", ProviderType.NATIVE)

    def probe_all(self) -> dict[str, ResolvedExecutable | ExecutableResolutionError]:
        result: dict[str, ResolvedExecutable | ExecutableResolutionError] = {}
        for name in SUPPORTED_EXECUTABLES:
            if name in OPTIONAL_EXECUTABLES:
                continue
            try:
                result[name] = self.resolve(name)
            except ExecutableResolutionError as error:
                result[name] = error
        return result

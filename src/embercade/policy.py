from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class CapabilityStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    HIDDEN = "hidden"
    DESKTOP_MANAGED = "desktop-managed"


@dataclass(frozen=True)
class DesktopPolicy:
    capabilities: dict[str, CapabilityStatus]

    @classmethod
    def load(cls, path: Path) -> "DesktopPolicy":
        capabilities: dict[str, CapabilityStatus] = {}
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"{path}:{line_number}: expected capability=status")
            name, raw_status = (part.strip() for part in line.split("=", 1))
            if not name or name in capabilities:
                raise ValueError(f"{path}:{line_number}: invalid or duplicate capability")
            try:
                capabilities[name] = CapabilityStatus(raw_status)
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number}: unsupported status {raw_status!r}"
                ) from error
        return cls(capabilities)

    def status(self, capability: str) -> CapabilityStatus:
        try:
            return self.capabilities[capability]
        except KeyError as error:
            raise ValueError(f"desktop policy has no {capability!r} capability") from error

    def frontend_environment(self) -> dict[str, str]:
        hidden_system_features = (
            "storage-management",
            "services",
            "system-audio-management",
            "display-mode-switching",
            "overclocking",
            "tdp-power-mode",
        )
        power_actions = ("suspend", "reboot", "shutdown")
        return {
            "EMBERCADE_DESKTOP_POLICY": "1",
            "EMBERCADE_HIDE_SYSTEM_SETTINGS": "1"
            if any(self.status(name) is CapabilityStatus.HIDDEN for name in hidden_system_features)
            else "0",
            "EMBERCADE_EXIT_ONLY": "1"
            if all(self.status(name) is CapabilityStatus.HIDDEN for name in power_actions)
            else "0",
        }


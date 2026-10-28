"""Read-only udev summary for optional specialty input diagnostics.

Classification is delegated to the host's udev tags, as in pinned Batocera.
This is not a controller database or a substitute for game-level hardware E2E.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class SpecialInputSummary:
    guns: int = 0
    wheels: int = 0
    trackballs: int = 0
    mouse_pointers: int = 0
    probe_available: bool = True


def classify_input_tags(devices: tuple[Mapping[str, str], ...]) -> SpecialInputSummary:
    """Count event devices; ordinary mice are never relabeled as trackballs."""
    return SpecialInputSummary(
        guns=sum(device.get("ID_INPUT_GUN") == "1" for device in devices),
        wheels=sum(device.get("ID_INPUT_WHEEL") == "1" for device in devices),
        trackballs=sum(device.get("ID_INPUT_TRACKBALL") == "1" for device in devices),
        mouse_pointers=sum(device.get("ID_INPUT_MOUSE") == "1" for device in devices),
    )


def inspect_special_inputs() -> SpecialInputSummary:
    """Inspect current udev metadata without opening or modifying input nodes."""
    try:
        import pyudev

        devices = tuple(
            device.properties
            for device in pyudev.Context().list_devices(subsystem="input")
            if device.device_node and device.device_node.startswith("/dev/input/event")
        )
    except (ImportError, OSError):
        return SpecialInputSummary(probe_available=False)
    return classify_input_tags(devices)

"""One data-driven exit chord shared by every Embercade emulator route."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ExitHotkey:
    key: str
    label: str
    sdl_button: int
    sdl_name: str
    batocera_input: str


EXIT_HOTKEYS: Mapping[str, ExitHotkey] = {
    "back-start": ExitHotkey(
        "back-start", "Back/Select + Start", 4, "Back", "select"
    ),
    "guide-start": ExitHotkey(
        "guide-start", "Guide + Start", 5, "Guide", "hotkey"
    ),
}
DEFAULT_EXIT_HOTKEY = "back-start"


def resolve_exit_hotkey(config: Mapping[str, Any]) -> ExitHotkey:
    section = config.get("controller", {})
    if not isinstance(section, Mapping):
        raise ValueError("[controller] must be a TOML table")
    value = section.get("exit_hotkey", DEFAULT_EXIT_HOTKEY)
    if not isinstance(value, str) or value not in EXIT_HOTKEYS:
        choices = ", ".join(EXIT_HOTKEYS)
        raise ValueError(f"[controller].exit_hotkey must be one of: {choices}")
    return EXIT_HOTKEYS[value]

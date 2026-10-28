"""Read-only exit-chord exercise over live controller snapshots.

This observes input; it never emits keys, exits an emulator or saves settings.
A sustained overlap rejects short reported pulses, without claiming that SDL
can distinguish a real physical hold from every possible driver fault.
"""

from __future__ import annotations

import math

from embercade.exit_hotkey import EXIT_HOTKEYS


HOLD_SECONDS = 0.35


class ChordTest:
    """Require release, sustained simultaneous buttons, then release again."""

    def __init__(self, hotkey: str) -> None:
        if hotkey not in EXIT_HOTKEYS:
            raise ValueError("Unsupported exit shortcut")
        self.hotkey = hotkey
        self.modifier = "guide" if hotkey == "guide-start" else "back"
        self.phase = "release"
        self._connected = False
        self._device_id: object = None
        self._last_now: float | None = None
        self._hold_started: float | None = None

    def _reset(self) -> None:
        self.phase = "release"
        self._hold_started = None

    def update(self, pressed: set[str], connected: bool, now: float,
               device_id: object = None) -> str:
        """Consume one current snapshot, never a union of remembered edges.

        ``device_id`` should identify this connection, such as the UI's handle
        generation counter. A disconnect, new connection or backwards clock
        discards progress. All buttons must be released before arming and before
        reporting success, so the completed chord cannot navigate the wizard.
        """
        if not math.isfinite(now):
            raise ValueError("Controller sample time must be finite")
        if not connected:
            self._reset()
            self._connected = False
            self._device_id = None
            self._last_now = now
            return self.phase

        if (not self._connected or device_id != self._device_id
                or (self._last_now is not None and now < self._last_now)):
            self._reset()
        self._connected = True
        self._device_id = device_id
        self._last_now = now

        chord = {self.modifier, "start"}.issubset(pressed)
        if self.phase == "release":
            if not pressed:
                self.phase = "press"
        elif self.phase == "press":
            if chord:
                self._hold_started = now
                self.phase = "hold"
        elif self.phase == "hold":
            if not chord:
                self._hold_started = None
                self.phase = "press"
            elif self._hold_started is not None and now >= self._hold_started + HOLD_SECONDS:
                self.phase = "release_after"
        elif self.phase == "release_after":
            if not pressed:
                self.phase = "passed"
        return self.phase

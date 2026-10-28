# Multi-controller input (1.0)

Embercade uses the existing EmulationStation input configuration and Batocera
launcher/configuration generators. It does not keep a second controller profile
database. Every game launch re-enumerates SDL gamepads (up to Batocera's eight
player slots), resolves EmulationStation's saved player preferences, and passes
each live GUID, SDL index, device path and input counts to the pinned launcher.
The transient SDL index and Linux `eventXX` path are never stored as fixed
device identities. EmulationStation's path preference wins when available,
followed by GUID/name and name; otherwise devices are ordered by their physical
USB/Bluetooth parent path. If a preferred device is absent, remaining slots
are filled from the current devices. The configured exit chord belongs to
Player 1, as in the established Batocera behavior.

## Emulator handoff

RetroArch uses its SDL2 joypad backend in Embercade desktop mode so the indices
and live mappings agree with the launcher. The existing EmulationStation
mapping provides each player's face buttons, D-pad and triggers. Where the
vendor/product pair is unique among connected pads, RetroArch reserves that
identity for the player's port to survive a live reconnect. Duplicate models
cannot be distinguished by that reservation alone; they keep launch order and
are not claimed to preserve player identity through every live reconnect.

Standalone Dolphin still uses its pinned Batocera generator and native evdev
devices. Some Bluetooth pads expose an extra Linux system key before the
gamepad key range. SDL counts gamepad keys first, while Dolphin's evdev backend
counts all keys numerically. Embercade translates the live device's SDL button
slots to Dolphin evdev slots from the read-only kernel capability bitmap.
The same translation is used for Dolphin's Player-1 `Hotkeys.ini` exit chord;
otherwise a Bluetooth pad with an extra system key could steer the game but
fail to exit. If the OS still reports another pad as connected, it can be
selected as Player 1 at launch even when the user intends to use a different
pad. The CachyOS Handheld reported an Xbox Bluetooth pad while the user was using
one at Garuda; whether this was a stale link or another same-named device was
not established. Embercade does not rewrite or disconnect the host device;
check the actual live Player-1 assignment if another pad's exit chord fails.
When the bitmap is unavailable or inconsistent, generation falls back to the
upstream numbering rather than guessing. The existing per-port GameCube
`Rotate Face Buttons` setting is independent and remains user-controlled.
The normal host Dolphin profile is not changed.

No extra input daemon or host-wide controller mapping is installed. Wii's
native Real Wiimote path and its existing Auto/gamepad fallback stay separate.

## Visible acceptance and limits

On Garuda/Hyprland, the tested pair is an Xbox 360 controller through its USB
receiver (Player 1) and an Xbox Series controller over Bluetooth (Player 2).
Both navigate the frontend. NES Contra has independently working two-player
controls, D-pads and face buttons. Either player's disconnect/reconnect during
the running RetroArch game restored both players to their original figures;
only Player 1's configured chord exited to the same frontend. Standalone
GameCube Mario Kart: Double Dash!! likewise has two independent controllers;
after the evdev correction their physical face-button behavior matches.
Single-player 3DO and Wii/gamepad start, control and return also passed after
the change. These are actual user-visible tests, not just generator fixtures.

The automated suite covers player ordering/preferences, multi-controller
arguments/configuration, single-controller fallback, duplicate identities,
P1-only exit ownership and Dolphin's extra-key translation. Prepared runtime,
frontend-library smoke, Production Stage and installed Doctor pass. Real
P3/P4, two identical Bluetooth models, live reconnect in standalone Dolphin,
and simultaneous two-gamepad-plus-Real-Wiimote gameplay are not established by
these tests. Other standalone emulator hotplug remains emulator-owned and is
not labeled READY by RetroArch's successful reconnect.

The tested shadPS4 v0.19.0 gameplay input path assigns pads in its own SDL
enumeration order to the first free player slot. It does not consume its
declared `default_controller_id` setting in that assignment path. Embercade
therefore does not claim deterministic frontend-P1 parity for two-pad shadPS4
sessions. No global SDL reorder or host-profile workaround is applied; the
validated single-controller Bloodborne route is unaffected. See
`PROJECT_STATE.md` for the exact upstream revision and scope.

On CachyOS Handheld/CachyOS Handheld Edition, the tested pair is a generic
USB Xbox-style pad (Player 1) and an Xbox Series Bluetooth pad (Player 2).
The user launched Embercade in the real Steam/Gamescope session. NES Contra
again had two independent players with correct D-pad/face buttons, and both
remained steerable after Player 2 disconnected and reconnected. Mario Kart:
Double Dash!! separately had independent two-player control and identical
physical face-button behavior on both pads. Player 1's exit returned each
game to the same frontend. PCSX2 and Xenia single-player launch, input and
exit regressions also passed in that session. This visible acceptance is
separate from the matching-payload and installed-Doctor checks; SSH launches
alone would not establish it. A live Player 1 reconnect on this host, two
identical Bluetooth pads and GameCube in-emulator reconnect remain untested.

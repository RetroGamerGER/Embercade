# Wii controllers (Embercade 1.0 development)

Wii uses the existing EmulationStation → Embercade → pinned Batocera 44
Dolphin plugin → separately installed Dolphin route. There is no second
controller database, mapping daemon or replacement emulator. Product identity
is `EMBERCADE 1.0`; the private 1.0 scope has reached feature freeze.

## Connection and configuration

The reference hardware is an RVL-003 Wii Remote, Nunchuk and Mayflash
DolphinBar in **mode 4**, synchronized as player 1. USB `057e:0306` is reported
as a Nintendo remote by the USB ID database but its descriptors identify the
Mayflash adapter. It exposes four generic HID channels, not four proven
connected remotes. The ordinary Xbox gamepad remains the frontend/exit device.

The Embercade session sets `SDL_JOYSTICK_HIDAPI_WII=0` before SDL
initialization. This disables only SDL's Wii HID interpretation, not native
Dolphin HID access or other SDL controller drivers. A real regression showed
PCSX2/SDL3 enumerating the receiver's four slots ahead of the Xbox pad, shifting
that pad to SDL-4 despite the generated SDL-0 binding. The scoped hint avoids
this competing driver. Discovery temporarily applies the same hint and
restores the caller environment; no global controller setting is changed.

Production and the development harness discover kernel HID identities in
sysfs and expose only permitted Wii `hidraw` character devices. Paths and
device numbers are discovered, not hardcoded. Keyboard/mouse/unrelated HID
nodes and the full `/dev` directory are not exposed for this feature. Existing
host uaccess ACLs already allow this hardware; no udev rule, permission change,
driver rebinding, Bluetooth pairing, service or package installation is made.

Use the existing Wii **EMULATE WIIMOTE** option (`emulatedwiimotes`):

| Setting | Dolphin configuration |
|---|---|
| Auto / unset | A responding, permitted real HID selects Real Wii Remote; otherwise existing gamepad emulation |
| On (`true`) | Existing emulated-Wiimote mapping, including Batocera's Nunchuk/controller-mode/profile options |
| Off (`false`) | Native Real Wii Remote with continuous scanning, including when the remote is connected later |

New setups use Auto. Normal updates preserve an existing On/Off setting;
select Auto explicitly to change an older gamepad-only setup. Game/per-system
overrides remain Batocera's responsibility. Light-gun branching is unchanged.
GameCube never applies the Wii auto policy and retains its existing mapping.

At each Wii launch, the desktop adapter re-enumerates permitted HID nodes and
sends only the native status-request output report. Unused DolphinBar slots
reject this request; simply plugging in the bar does not force Real mode.
The probe closes before Dolphin starts. Structural dry runs select emulation
without a hardware probe. Doctor/inventory never open/probe HID
devices, and absent hardware never makes Doctor fail. Doctor cannot infer a
Nunchuk, IR visibility or MotionPlus from USB identity alone.

Real mode writes `Source = 2` using the original Batocera generator; emulation
uses `Source = 1`. Dolphin interprets remote buttons, the extension protocol,
IR camera, acceleration and rumble natively. No separate Nunchuk stick/C/Z or
pointer mapping is needed. The mode-4 bar supplies IR light and the USB bridge;
the remote's IR camera supplies pointer observations. Sensor-bar placement
remains the existing Batocera option.

## Isolation and exit

Only Embercade's Dolphin INIs below its emulator-config directory, Dolphin
saves/NAND below its saves directory, and its cache/logs are writable. The
plugin's existing child XDG environment selects those locations. Normal host
Dolphin profiles and external ROM/BIOS sources remain untouched. Reinstall is
not a purge and preserves Wii config/NAND as all other persistent user state.

Keep the normal gamepad connected for the configured Guide+Start or
Select+Start exit and frontend navigation. Dolphin's existing native Hotkeys
mapping owns that chord; Wii Home/+/− and essential game controls are not
hijacked. No Wiimote-specific global exit chord is invented.

For the **emulated** Wiimote on a normal desktop gamepad, Embercade's scoped
patch to the pinned Dolphin generator maps physical Start to Wii `+`,
Back/Select to Wii `−`, and Guide to Wii Home. The right shoulder supplies
shake; it no longer masquerades as Wii `+`. The GameCube generator and native
Real Wiimote `Source = 2` path are unchanged. The configured Player-1
Guide+Start/Select+Start exit remains separate and authoritative.

Wii titles that expect the remote held **sideways** need the existing
per-game `CUSTOMIZE EMULATED WIIMOTE & GAMEPAD → Wiimote Sideway` choice.
Without it, an upright D-pad mapping appears rotated in games such as
*New Super Mario Bros. Wii*. This is not a controller-wide SDL axis swap:
the generated normal mapping contains distinct horizontal and vertical
D-pad axes. The user confirmed the game's directions after selecting
Sideway for that title; upright games such as *Super Mario Galaxy* keep
their own setting. Do not rotate every Wii title globally or rename ROMs.

## Reconnect boundaries

The Wii launch decision is fresh for every game. Connecting/reconnecting a
remote after the frontend starts can therefore affect the next launch.
Dolphin's continuous scanner owns reconnect while a Real-mode game runs.
An already emulated game does not automatically switch to Real mode when a
remote appears: relaunch, or choose Off before launching for delayed pairing.
There is no mid-game input-source/config rewrite.

The receiver's HID nodes are bound when the frontend starts. Ordinary remote
off/on does not remove the DolphinBar's four nodes. **Unplugging/replugging the
USB receiver or attaching a new receiver after frontend start requires a
frontend restart** to expose its new nodes; this is distinct from Wiimote
wireless reconnect. No privileged host-device broker is introduced.

Direct host-Bluetooth Wiimotes and Bluetooth passthrough are not accepted by
the DolphinBar test. A conflicting kernel `wiimote` driver is reported, not
silently unbound; Auto falls back to gamepad. Off still permits Dolphin's
native scanner, subject to existing host permissions. Embercade does not
enable exclusive Bluetooth passthrough. Current Dolphin has None, Emulated
and Real sources, not a Source=3 hybrid mode.

## Upstream evidence

The installed test emulator is Dolphin 2609; this is a host observation, not
a new Embercade source pin. Batocera remains at its exact `upstream.lock` pin.

- [DolphinBar review](https://dolphin-emu.org/blog/2014/08/23/dolphinbar-review/): native synchronization/continuous scanning.
- [Controller guide](https://dolphin-emu.org/docs/guides/configuring-controllers/): Real versus Emulated and continuous scanning.
- [SDL Wii HID hint](https://wiki.libsdl.org/SDL3/SDL_HINT_JOYSTICK_HIDAPI_WII): disable the SDL driver before initialization; DolphinBar is not supported by that driver.
- [2609 HID transport](https://github.com/dolphin-emu/dolphin/blob/2609/Source/Core/Core/HW/WiimoteReal/IOhidapi.cpp): four receiver slots, status request/EPIPE and generic-HID versus kernel-driver conflict.
- [2609 source modes](https://github.com/dolphin-emu/dolphin/blob/2609/Source/Core/Core/HW/Wiimote.h): supported native source enum.
- [2609 Linux Bluetooth](https://github.com/dolphin-emu/dolphin/blob/2609/Source/Core/Core/HW/WiimoteReal/IOLinux.cpp): host HCI/L2CAP scanner, distinct from USB HID and exclusive passthrough.

## Acceptance

Implementation and structural tests alone do not establish gameplay or
peripheral READY. The user confirms **Super Mario Galaxy** on Garuda with
image/audio, real buttons, Nunchuk stick/C/Z, IR pointer, shaking/motion and
rumble. Turning the remote off/on inside Dolphin restores control. Turning
it off/on in the same frontend and relaunching also works. Guide+Start on the
ordinary gamepad returns to the same EmulationStation process. GameCube
**F-Zero GX** image/audio/gamepad/exit regression is confirmed. This supports
READY for that Garuda standalone route, not every Wii peripheral.

The same RVL-003/Nunchuk/DolphinBar is also user-accepted in **Super Mario
Galaxy** from the CachyOS Handheld's real interactive Steam/Gamescope session:
image/audio, real buttons, stick/C/Z, pointer, motion, rumble, wireless off/on
inside Dolphin and the frontend, relaunch and Select+Start return to the same
frontend. Process evidence verifies native Source 2, continuous scanning,
the receiver HID handle and clean launcher status 0. This is independent
second-host hardware acceptance, not inferred from Garuda or structural tests.

The later standalone-decoration extension also passes with the real Wiimote
in the CachyOS Handheld's Steam/Gamescope session: the existing console bezel is
visible around the 4:3 game while Nunchuk, pointer, buttons, image/audio and
Player-1 gamepad Select+Start still work. Garuda separately accepts the
emulated-gamepad +/−/Home mapping and Wii bezel; *New Super Mario Bros. Wii*
uses its per-game Sideway setting to orient the D-pad correctly. These checks
do not expand the accepted hardware set beyond the DolphinBar/Nunchuk route.

The second-host Xenia/gamepad regression works with Select+Start returning to
the same frontend on the repeat test. One earlier Xenia exit was followed by
SIGINT to the whole frontend/production wrapper, although the launcher had
returned status 0. No crash dump or signal sender establishes the cause.
The user stopped further investigation after the successful repeat and will
watch for recurrence during ordinary use. No speculative exit/signal repair
is included; this remains an intermittent, unresolved observation.

After the scoped SDL fix, PCSX2 recognizes only the ordinary Xbox pad as
SDL-0. The user confirms PCSX2 control/Guide+Start return and another real Wii
control/pointer/exit run; disabling SDL's Wii driver does not disable Dolphin's
native transport.

With the real remote off, Auto/gamepad emulation and the configured exit are
also user-confirmed. NES/Libretro, 3DO, PCSX2, Xenia and shadPS4 start/exit
regressions are accepted on Garuda; normal Quit Embercade returns to the
desktop with no remaining test frontend or emulator service. The native splash
is measured at 2,750 ms on the warm restart, with no branding/theme change.

Normal updates preserve the inventoried user config, saves/states, themes,
managed cores/providers/assets and Steam data. Normal Dolphin profiles remain
unchanged on both hosts. Final committed-payload parity is checked with the
same stage manifest and every installed file hash, not just the version label;
the second host does not need a Git checkout or Wii hardware for that check.

MotionPlus is unvalidated: the tested RVL-003 has only a Nunchuk attached,
no MotionPlus accessory. Multiple Wiimotes, Balance Board, third-party remotes
and direct Bluetooth remain outside this acceptance. Both hosts receive
the same verified production payload; the tested native DolphinBar/Nunchuk
route is gameplay-accepted on both.

The alternative Dolphin Libretro route is not implemented for GameCube/Wii.
A Garuda attempt with F-Zero GX aborts in Configgen with `MissingCore` before
RetroArch runs, even though the core is present: the standalone-oriented path
does not supply the central exact-core handoff for this alternative. That is
a separate diagnosed port, not a real-remote regression or a repaired route.

The full automated suite passes **516 tests**, including native pinned-plugin
Real/Auto/fallback/override generation, emulated Nunchuk, GameCube mapping,
config/host/source isolation, dynamic HID identity and reconnect state,
missing-hardware Doctor behavior, scoped SDL policy/restoration and production
device mounts. Synthetic content is used only for structural generation, never
emulator execution. Runtime, frontend-library and shader smokes pass (14
presets/142 dependency files), as do production staging and staged Doctor.

The repository stays PRIVATE. The paused bezel license review remains a
public-release blocker; no theme/shader/decoration asset is removed or replaced.

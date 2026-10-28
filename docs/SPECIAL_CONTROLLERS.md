# Special controllers — structural preparation (1.0)

**Lightguns, wheels and trackballs: PREPARED / UNVALIDATED.** No matching
hardware was available for a real game test. These labels describe routes in
the pinned source and fixture tests; they do not mean plug-and-play support,
calibration quality, force feedback, live reconnect or game compatibility has
been accepted. `READY` requires a separate physical-device E2E on a reference
host, with gameplay and normal exit/return.

## Shared desktop boundary

The production namespace passes the live `/dev/input` directory and read-only
`/run/udev` and `/sys` to the existing Batocera launcher. It does not bind a
fixed `eventXX` node or install host udev rules. EmulationStation's existing
player preferences remain authoritative for SDL game controllers; the central
exit chord remains Player 1's. The frontend's pointer and ordinary gamepad
paths are not replaced. The Batocera launcher rediscovers specialty devices at
each game launch, so a device added before the next launch may be seen; live
in-game hotplug is unvalidated.

Doctor reads udev event tags without opening devices. It counts explicitly
tagged gun, wheel and trackball nodes separately from ordinary mouse nodes.
No detected specialty device is informational, never a Doctor error; an
ordinary mouse is not called a trackball. Doctor cannot prove that a detected
device works in a specific emulator.

## Lightguns

The existing Batocera `Gun` discovery requires udev `ID_INPUT_MOUSE=1` plus
`ID_INPUT_GUN=1`. It retains the upstream mouse index, button capabilities and
gun-specific flags. Embercade now exposes Batocera's existing `use_guns` and
`lightgun_map` options rather than introducing a gun database. RetroArch keeps
`input_driver=udev` for mouse/keyboard/gun input, while ordinary pads continue
using the tested SDL2 joypad driver. The pinned Libretro generator has
lightgun-vs-mouse options for Nestopia/FCEUmm and selected arcade cores; PCSX2
has GunCon2 USB configuration, and standalone Dolphin has evdev gun mapping.
Those latter routes are source-level possibilities, not tested hardware
compatibility. No Sinden/AimTrak/Gun4IR/GunCon model is approved by this work.
Upstream precalibration, borders and game-specific gun controls remain
hardware-dependent. The standalone MAME/MESS port remains BLOCKED for its
separate appliance data/work-path issue.

## Wheels

The pinned Batocera launcher identifies wheels using `ID_INPUT_WHEEL=1` on a
joystick event device. Existing ES/SDL mapping and Batocera's `use_wheels`
option feed the upstream wheel route: `joystick1left` is steering and `l2` /
`r2` are brake/throttle in PCSX2's wheel mapping; Dolphin has its own wheel
generator. A wheel must be recognized/mapped as an SDL/ES controller to enter
Embercade's existing player handoff. Unknown raw HID wheels are **not**
automatically mapped or claimed supported. Upstream may prioritize a detected
wheel in the game's player order when `use_wheels` is enabled; normal gamepad
order with no wheel remains unchanged.

Embercade exposes `use_wheels` and PCSX2's upstream wheel type. It does not
expose Batocera's range/deadzone controls: on a normal desktop, their appliance
calibrator and sysfs writes are inappropriate. The desktop patch keeps the raw
wheel/pedal axes and skips physical `/sys` range writes and virtual-wheel
calibration, logging when a requested range cannot be applied. No host input
profile, physical range or device permission is changed. Steering/pedals and
force-feedback behavior still require physical-wheel tests; FFB is **not**
validated or guaranteed. Other buttons, clutch and shifter support depend on
the device's existing ES mapping and the emulator's upstream generator.

## Trackballs

A trackball is treated as a relative mouse/pointer, not as a second controller
class or a new slot database. The existing RetroArch `udev` input driver and
mouse-index/core mouse options are the structural route. A udev-tagged
trackball is shown distinctly by Doctor when the host supplies that tag;
otherwise Doctor reports only an ordinary pointer count. There is no claim
that arbitrary trackballs are auto-identified, mapped in every core, or safe
from desktop pointer focus/compositor differences. The MAME/MESS standalone
route remains BLOCKED independently of pointer passthrough.

## Evidence and next acceptance

Automated fixtures verify udev class separation, missing-hardware Doctor
behavior, exposed-but-bounded ES settings, Libretro lightgun/mouse slot
generation, PCSX2 steering/pedal axis translation, and the wheel desktop
no-host-calibration path. They never simulate a successful physical game test.
Normal gamepad and production smokes guard existing launch behavior.

To move any class to `READY`, attach a real device and test the exact model,
host/session, emulator/core, game, player assignment, controls, focus,
reconnect, exit/return and relevant calibration/FFB. A result for one model or
host does not promote the entire controller class.

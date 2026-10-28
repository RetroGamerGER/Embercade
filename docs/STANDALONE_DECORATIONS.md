# Standalone decorations: PCSX2, Xemu and Dolphin

This integration is restricted to `ps2/pcsx2`, `xbox/xemu`,
`gamecube/dolphin` and `wii/dolphin`. It does not
change any other emulator, Libretro shaders/overlays, firmware, saves or native
controller/exit behavior. No emulator binary or new decoration asset is shipped.

## Selection and lifecycle

The existing advanced-options Decoration setting remains authoritative.
Embercade asks the pinned Batocera runtime for `SystemConfig` and
`Emulator.bezel_files`: global/system/game precedence, user decorations,
game-specific images, standalone/system fallbacks and default images stay
upstream-owned. `none` starts no helper. Images and matching `.info` files are
read in place; validated paths must remain inside the configured installed or
user decoration roots. Invalid/missing images or unsupported rendering conditions
log a warning and do not prevent the emulator from starting.

The helper runs beside the unchanged synchronous launcher call. Only a focused
fullscreen window with the exact resolved executable **and** ancestry of that
specific Embercade launch can display the frame. Focus loss, workspace changes,
windowed mode and mismatched monitor geometry hide it. An EOF pipe couples its
lifetime to the wrapper, including wrapper crashes; parent identity is also
checked. The wrapper closes the pipe and waits for helper cleanup before returning
to ES. A cleanup timeout sends SIGTERM only to this helper; if the optional
renderer is wedged, it is force-reaped after another bounded wait. Neither step
uses a name-based process search or sends a signal to the emulator.

## Geometry

The renderer preserves the original image's aspect ratio and opacity. It draws
only in side bars outside **both** the centered game rectangle and the `.info`
aperture, with a one-pixel safety margin. It never changes emulator resolution,
scaling, EEPROM, firmware or the game's viewport. Images are not copied or resized
on disk. Top/bottom artwork is intentionally not drawn over letterboxed FMVs.

For the complete measured 4:3 frame select these existing Batocera options:

- PCSX2: Game Aspect Ratio = Standard (4:3), FMV Aspect Ratio = Standard (4:3).
- Xemu: Aspect Ratio = 4x3, scaling = Scale (the normal default).
- Dolphin GameCube/Wii: Aspect Ratio = 4:3 (or Auto with 4:3 TV mode).

Auto PCSX2 modes reserve up to 3:2; Auto Xemu reserves up to 16:9. This can narrow
or eliminate visible side artwork on a 16:9 monitor. It prevents a dynamic
aspect change from placing game content behind the decoration. Stretch/unknown
ratios fail closed rather than guessing. In-emulator aspect changes during a
launch are not tracked: use the frontend options and relaunch.

Dolphin uses the same Batocera aspect and TV-mode settings as its generated
configuration: forced 4:3 or Auto with 4:3 TV mode permits side artwork;
forced 16:9 or Auto with 16:9 TV mode reserves the entire widescreen game area.
Stretch or unknown settings omit the overlay. `Decoration=None` remains an
explicit opt-out for either Dolphin system. The layer is input-transparent and
does not move the game window or transform Wii pointer coordinates.

The MainRig's missing Xemu frame in the pre-AppImage check was not a missing
asset or Hyprland failure. Its preserved Xemu aspect setting was Auto, whereas
the WohnzimmerPC had an explicit 4x3 selection. Auto correctly reserves a
possible 16:9 Xemu game area and leaves no safe side strip on a 16:9 monitor.
Selecting 4x3 on the MainRig restored the existing frame in the normal
Hyprland path. Embercade does not silently change this user choice.

## Compositor backends

### KDE Plasma 6 / Wayland

The layer is anchored to all four edges with zero margins and exclusive zone
`-1`. This covers the entire logical output, including Plasma panel reservations,
without reserving space itself. The default zone `0` produced a 2560×1408
surface on the owner's 2560×1440 output; artwork was centered/scaled in that
smaller, offset surface. A native probe now measures 2560×1440. GDK/Cairo apply
Wayland buffer scaling; physical mode dimensions are never multiplied into
logical layer coordinates. During monitor reconfiguration, a mismatched surface
allocation remains transparent instead of painting a cropped frame. See the
[layer-shell protocol](https://github.com/swaywm/wlr-protocols/blob/master/unstable/wlr-layer-shell-unstable-v1.xml)
and [GTK layer-shell API](https://wmww.github.io/gtk-layer-shell/).
The same full-output policy applies on Hyprland; Gamescope's physical X11
external-overlay sizing is unchanged. Owned-window checks are automated evidence;
real Dolphin/GameCube, Dolphin/Wii and Xemu visual acceptance remains OPEN.

The same GTK3 layer-shell renderer follows a uniquely named, disposable KWin
script. It reads only active-window PID, fullscreen/minimized state and frame
geometry through KWin's public scripting API; it does not set window properties,
create rules or change KWin configuration. The script is supplied via a memfd,
run by its individual script object, and unloaded by name on cleanup. A private
D-Bus connection and NameHasOwner watchdog also unload it after helper crashes.
Updates are accepted only from KWin's bus owner. Stale/disconnected data hides
the layer and stops the optional helper. PID/executable/ancestry, logical monitor
geometry, side-bar clipping and input transparency are unchanged.

The existing optional host bootstrap offers `gtk-layer-shell` for KDE/Hyprland
Wayland. KWin service/owned fullscreen GTK fixture checks pass on Garuda/KWin
6.7.5; actual Xemu/GameCube/Wii game/exit acceptance remains OPEN. Gamescope
keeps precedence when desktop environment variables are inherited. See
[GLOBAL_GARUDA_AUDIT.md](GLOBAL_GARUDA_AUDIT.md).

### Hyprland / Wayland

Native GTK3 layer shell, keyboard mode NONE and empty input region. Production
exposes only the current Hyprland control/event sockets, not the entire runtime
directory. Focus/workspace events plus a 250ms safety check bind the otherwise
display-global layer to the emulator. Logical monitor coordinates are used;
unmatched geometries hide the layer. Optional host bindings: GTK3, PyGObject,
PyCairo and GtkLayerShell 0.1. Missing bindings leave the game functional.

### Gamescope

A separate X11 backend uses Gamescope's `GAMESCOPE_EXTERNAL_OVERLAY` plane on
the discovered root Xwayland server. It does not set `STEAM_GAME`, request
`STEAM_INPUT_FOCUS` or focus the helper. It follows `GAMESCOPE_FOCUSED_WINDOW`
and `GAMESCOPE_FOCUS_DISPLAY` across Xwayland servers and verifies PID ancestry.
Xemu's SDL window can omit the EWMH fullscreen atom. In Gamescope only, a
focused surface covering the exact logical output at (0,0) or Gamescope's
(1,1) origin also qualifies; smaller/offset windows do not. This does not
relax the desktop backend's fullscreen requirement.
It requires GTK3/PyGObject/PyCairo and Python Xlib, not gtk-layer-shell.
Gamescope renders this plane without scaling: Xwayland's 1080p game size must
not be used as a 4K TV's overlay size. Embercade reads the single active CRTC
from Gamescope's own DRM device using libdrm GET calls and a read-only file
descriptor. It never requests DRM master or changes a display mode. Unknown,
multiple, nested or rotated outputs fail safely instead of painting over the
game at an assumed size. A resolution change is rechecked during the launch.
The outer launcher discovers the compositor's DRM card before entering the
sandbox, using host Python; the pinned launcher venv does not need Xlib. A
PID-scoped, validated device hint crosses the boundary, not access to the host
process tree. Current mode queries still occur inside the sandbox. The overlay's
own X surface is explicitly sized in physical pixels: GTK's normal toplevel
resize can otherwise constrain it to the smaller logical Xwayland screen.
The game's logical 1080p resolution is intentionally left unchanged on a 4K TV.
An already occupied external-overlay slot fails safely rather than displacing
another overlay. Native xdg-shell-only game windows without an Xwayland focus
identity are not assumed safe. No global Gamescope properties are modified.

Steam's visible MangoApp performance overlay can occupy this external-overlay
slot even when the emulator and decoration resources are correct. This was
observed in the real second-host production session: the helper reported
`Gamescope external-overlay plane already occupied` and the game continued
without a bezel. Setting Steam's performance overlay to Off made its window
unmapped; after normal emulator exit and relaunch, Xemu's bezel was visible and
correctly proportioned on the 4K output. An already failed helper does not retry
merely because the slot becomes free. Embercade does not kill MangoApp, displace
its plane or change Steam settings. This remains a coexistence limitation,
not a missing-resource or automatic Steam-registration failure.

Check the effective system/game decoration setting separately: an existing
`ps2.bezel=none` correctly suppresses the overlay unless a more specific game
override selects a decoration. The same rule applies to GameCube and Wii;
reinstallation preserves these settings rather than turning bezels on
automatically.

The implementation was checked against the second host's Gamescope 3.16.25
[upstream compositor source](https://github.com/ValveSoftware/gamescope/blob/3.16.25/src/steamcompmgr.cpp).
Gamescope itself may change direct scanout/tearing behavior when compositing an
overlay. Embercade does not force HDR, VRR, VSync or display modes; no general
HDR/VRR performance claim is made.

### Other compositors

Generic X11 and unsupported Wayland compositors fall back without a decoration.
KDE Plasma 6 now has the scoped observer described above; its real-game
acceptance remains open. Do not use the failed generic X11 always-on-top
prototype as an automatic fallback.

## Acceptance

MainRig live prototypes for both PCSX2 and Xemu were user-confirmed: correct
4:3 proportions, workspace binding, input/audio and frame removal on exit.
On 2026-09-27 PCSX2's integrated fresh production start in Gamescope on the
second host's 4K TV was visually confirmed after correcting the external
overlay's physical surface size. Xemu's integrated decoration was subsequently
confirmed visible and correctly proportioned after handling its SDL fullscreen
surface without an EWMH fullscreen atom. Both updates used the normal installer.
After user exit, neither emulator nor decoration helper remained; the same ES
session stayed alive. The final Xemu launcher log reports status 0. Its existing
exit path still logs signal termination of the emulator; this change does not
claim a new graceful native Xemu shutdown mechanism or alter that exit path.

The full 294-test suite, runtime smoke, frontend-library smoke, production stage,
production Doctor and diff whitespace checks passed. `Decoration=None`, invalid
resources, helper failure, exact executable/ancestry, geometry, focus/workspace
visibility and bounded cleanup have automated coverage. None/failure fallback
are not claimed as additional manual Gamescope game tests. At that milestone,
integrated Hyprland retesting had not been repeated beyond the accepted live
prototypes; the later extension adds the targeted checks below.

The GameCube/Wii extension has separate current production acceptance. On
MainRig/Hyprland, the user confirmed the 4:3 GameCube frame around Mario Kart:
Double Dash!!, the Wii frame with gamepad input and normal exit, and the Xemu
frame after explicitly selecting 4:3. On WohnzimmerPC, the user confirmed
Xemu, GameCube and Wii frames from real Steam/Gamescope, including the Wii
DolphinBar/Nunchuk/IR-pointer game and Select+Start return. All frames disappear
with their emulator; Quit Embercade returns to Steam. The current 542-test suite,
runtime/frontend-library/shader smokes, Production Stage, staged and installed
Doctors pass. The two installed Stage manifests match byte-for-byte. These
results do not imply that an occupied Gamescope overlay plane will be displaced.

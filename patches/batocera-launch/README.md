# batocera-launch patches

These patches are applied only to the source snapshot under `.work/runtime/src`
by `scripts/runtime-prepare`. The sibling Batocera reference repository remains
untouched.

- `0001-embercade-desktop-paths.patch` redirects the launcher and Libretro
  generator to environment-provided desktop paths and checks the actual core
  library instead of requiring optional `.info` metadata.
- `0002-embercade-desktop-lifecycle.patch` disables Batocera display/hotkey
  services in desktop mode, avoids privileged negative niceness and provides a
  config-generating dry run that never starts RetroArch.
- `0003-embercade-desktop-errors.patch` makes unexpected launcher failures
  non-zero and redirects the error report into Embercade state.
- `0004-embercade-disable-special-hardware.patch` turns gun-help and Evmapy
  hotplug monitoring into desktop no-ops for the normal gamepad-only 0.1 path.
- `0005-embercade-recording-path.patch` keeps recordings in the dedicated
  Embercade XDG data directory.
- `0006-embercade-retroarch-controller-exit.patch` maps RetroArch's native
  player-one hotkey + start combination to a clean desktop exit without a
  Batocera hotkey service.
- `0007-embercade-libretro-visual-resources.patch` lets the desktop runtime
  expose immutable shader and decoration roots independently from launcher
  defaults, and rejects a selected shader preset before RetroArch is started
  when its file is missing. It also quotes the generated Libretro overlay path
  so project directories containing spaces remain valid RetroArch config.
- `0008-embercade-dolphin-host-executable.patch` passes the host-resolved
  Dolphin executable into the modern Dolphin plugin as an absolute path,
  redirects its library paths through Embercade's ROM root and treats a
  first-run missing Wii `SYSCONF` as expected while preserving Batocera's
  batch-mode launch and controller/config generation.
- `0009-embercade-dolphin-controller-exit.patch` maps the centrally selected
  Back/Select+Start or Guide+Start chord through Dolphin's native
  `Hotkeys.ini` when
  the appliance hotkey service is intentionally absent in desktop mode.
- `0010-embercade-xemu-desktop-paths.patch` routes Xemu's executable,
  firmware, writable disks, screenshots and XDG data/cache through Embercade,
  and removes the Batocera appliance's `/usr/share/xemu/data` copy fallback.
- `0011-embercade-pcsx2-desktop-paths.patch` routes the modern PCSX2 plugin
  through the host-resolved executable and read-only host resources/BIOS while
  keeping configs, saves, cache and logs inside Embercade. It also maps the
  central player-one exit chord to PCSX2's native `ShutdownVM` hotkey.
- `0012-embercade-rpcs3-desktop-paths.patch` routes the modern RPCS3 plugin
  through the host-resolved executable and isolated XDG tree. In desktop mode
  it disables the compatibility API request, global `rpcs3-exit`, OverlayFS
  requirement and system-wide `vm.overcommit_memory` mutation.
- `0013-embercade-libretro-exact-core-path.patch` lets the generic Libretro
  route consume the exact core selected by Embercade's central host resolver,
  while preserving Batocera's logical core name for generator-specific
  configuration and keeping core discovery read-only.
- `0014-embercade-desktop-bezel-scaling.patch` keeps RetroArch's custom
  viewport aligned with an aspect-preserving decoration resize when the
  desktop pixel size differs from the source bezel's dimensions.
- `0015-embercade-retroarch-quoted-paths.patch` quotes generator-owned
  RetroArch asset, cache, core-info, SaveRAM/memory-card and savestate paths so
  a desktop project directory containing spaces is parsed without truncation.
- `0016-embercade-amiga-bios-path.patch` preserves Batocera's required Amiga
  BIOS subdirectory while resolving it below Embercade's read-only `BIOS_ROOT`
  instead of the appliance-only `/userdata/bios` path.
- `0017-embercade-dolphin-library-paths.patch` refreshes Dolphin's Wii and
  GameCube library roots from the configured read-only `ROM_ROOT` on every
  generated launch, avoiding stale isolated paths after a root change.
- `0018-embercade-libretro-core-options.patch` keeps Batocera configgen's
  generated central core options authoritative in the isolated RetroArch
  profile, so stale per-core or per-game `.opt` files cannot suppress system
  controller mappings such as PUAE's Select-to-virtual-keyboard binding.
- `0019-embercade-xenia-edge-host-executable.patch` keeps Batocera 44's
  Xenia Edge configuration generator while replacing its appliance-only
  binary location with Embercade's already validated native or external
  AppImage provider path.
- `0020-embercade-xenia-edge-xdg-paths.patch` makes the external Linux
  AppImage consume configgen's generated Xenia configuration and writes its
  storage, content and cache roots as the corresponding host-visible
  Embercade paths.
- `0021-embercade-bounded-launch-logs.patch` caps launcher and emulator logs
  at 8 MiB per file with two retained backups, preventing a failing title
  from consuming unbounded disk space while preserving recent diagnostics.
# Standalone desktop decorations

`0022-embercade-standalone-decoration.patch` skips PCSX2/Xemu/Dolphin's appliance
overlay preparation in desktop mode. Embercade still asks the pinned
`SystemConfig` and `Emulator.bezel_files` for the selected read-only image;
the optional launch-scoped compositor helper owns rendering and cleanup.
Other providers and the Libretro overlay path are unchanged.

# Managed shadPS4

`0023-embercade-shadps4-desktop.patch` keeps the pinned built-in `Shadps4`
generator and replaces its appliance executable with the already resolved
user-supplied AppImage/host runner. Direct games use `-g`; `-b` is reserved
for the emulator interface. Saves, add-ons and configuration use Embercade's
owned paths rather than writable game content or a normal host profile.
Existing GPU/rendering/timing choices survive unless an explicit Batocera
option overrides them; invalid JSON is preserved and reported, not reset.

`0024-embercade-libretro-sdl2-joypads.patch` uses RetroArch's SDL2 joypad
driver in desktop mode, matching the SDL indices passed by Embercade for
multiple USB/Bluetooth controllers. Keyboard/mouse input remains on udev;
the upstream Batocera joypad choice is unchanged outside Embercade.

`0025-embercade-libretro-sdl2-mappings.patch` supplies SDL with the existing
EmulationStation controller mappings and writes normalized SDL2 button/axis
bindings for RetroArch. This keeps each player's customized face buttons,
triggers and D-pad functional without relying on host autoconfig profiles.
Unique vendor/product pairs are reserved per player for stable live reconnects;
identical-model pads retain SDL launch order rather than an ambiguous reservation.

`0026-embercade-dolphin-evdev-button-order.patch` translates each controller's
SDL button slots to Dolphin's evdev slots using the current read-only Linux
input capability bitmap. Some Bluetooth pads expose low-numbered extra keys,
which Dolphin counts before gamepad buttons while SDL counts them afterward.
The patch only applies on Embercade desktop and leaves the user's per-port
GameCube face-button rotation setting untouched.

`0028-embercade-wii-emulated-gamepad-buttons.patch` maps a desktop gamepad's
Start, Back/Select and Guide to Wii +, − and Home in the pinned emulated-Wiimote
generator. The former shoulder-button + mapping is removed; the right
shoulder remains available for shake. Native Real Wiimotes and GameCube pads
are untouched; sideways games still use Batocera's per-game controller mode.

`0029-embercade-dolphin-evdev-exit-buttons.patch` applies the same live
SDL-to-evdev button translation as `0026` to Dolphin's Player-1 exit chord.
Bluetooth pads with extra low-numbered Linux keys otherwise receive correct
game controls but an incorrect `Hotkeys.ini` exit binding. Generic pads and
non-desktop launch retain their original button numbers.

`0030-embercade-libretro-no-desktop-companion.patch` disables RetroArch's extra
Qt desktop browser during Embercade game launches. KDE's folder-icon lookup
otherwise scans the many scoped scraper mounts and can block the first frame
on a network library. Configgen refreshes old generated autostart settings;
the in-game menu, saves and explicit `retroarch.*` user overrides are preserved.
The patch applies only when `EMBERCADE_DESKTOP=1`.

`0031-embercade-desktop-graphics-and-shader-compatibility.patch` prefers available
Vulkan for desktop Auto selection, preserves manual renderers and pinned core
OpenGL constraints, and applies existing discrete-GPU selection to automatic
Vulkan. It adds availability-aware Dolphin/PCSX2 defaults. Unsupported/missing
selected shader formats use a launch-local disabled-effect append instead of
cancelling the game; a bounded notice is handed back to the same frontend.
`0032` extends detected desktop Vulkan preference to the pinned standalone
PPSSPP/Azahar writers. Preserve native OpenGL/software/raw overrides and their
non-desktop defaults; unsupported host Vulkan falls back to the existing
OpenGL path. No emulator or graphics driver is installed by this policy.

`0033` explicitly disables the desktop shader-enable flag for a None/null
rendering choice, so the off-by-default first-run setting also clears stale
enabled state. Explicit valid effects and non-desktop behavior are unchanged.

`0039-embercade-c64-optional-jiffydos.patch` stops forcing optional JiffyDOS
on C64 desktop launches. The stock embedded VICE ROMs remain the default,
including drive 8 for D64 content. Explicit `vice_jiffydos` selections and
existing `retroarchcore.vice_jiffydos` overrides retain their normal priority.
No media arguments, cartridges, tape paths, C128 or non-desktop defaults change.

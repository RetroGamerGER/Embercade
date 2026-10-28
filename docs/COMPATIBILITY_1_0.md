# Embercade 1.0 system coverage and compatibility additions

This records the complete pinned system catalog as well as targeted 1.0 game
acceptance. The [historical 0.1 host matrix](COMPATIBILITY_0_1.md) is not rewritten.
`READY` requires user-confirmed gameplay and normal exit/return, not an
installed core, a generator dry run, or Batocera support alone.

The owner accepted the current private candidate on all three reference systems
on 28 October 2026. The laptop's known 16:10 bezel cropping/proportion issue
remains. See [the exact artifact and owner result](PRIVATE_DEPLOYMENT_2026_10_28.md#owner-acceptance--28-october-2026);
this overall acceptance does not expand the per-game/per-format ledger below.

## Frozen private 1.0 packaging boundary

**Embercade 1.0 feature freeze reached.** The current private AppImage wraps the
same verified classic Stage and resolvers; it does not create new READY systems
or broaden peripheral acceptance. Visible identity is `EMBERCADE 1.0`, while
the package version remains `0.1.dev0`. Default Carbon/resources are included;
downloaded themes, content, cores, providers, system files and secrets remain
external. Supported-host dependencies and risk-based packaging regression
evidence are recorded in [APPIMAGE.md](APPIMAGE.md) and
[PROJECT_STATE.md](PROJECT_STATE.md). Generic distro/older-Python compatibility
is unproven, and the independent public-release licensing gate remains BLOCKED.

## C64 disk startup

The historical visible C64 acceptance covered T64 content. A later MainRig D64
failure was traced to forced optional JiffyDOS with missing external ROMs,
although media attachment was correct. The C64 desktop default now uses the
embedded stock ROMs; explicit choices and other formats keep their existing
paths. The actual Giana Sisters disk passes unattended loading/autostart in an
isolated comparison. The owner subsequently confirms that Giana Sisters D64
starts on MainRig and Start + Guide returns to the frontend in the new private
candidate. See [C64_STARTUP.md](C64_STARTUP.md); this accepts that visible
start/exit case without promoting every C64 format or host to a new gameplay
result.

## 3DO

| Contract | Verified implementation |
|---|---|
| Batocera system | `3do` |
| Default emulator/core | `libretro` / `opera` |
| Launch route | Existing Embercade resolver → Batocera Configgen → RetroArch |
| Frontend extensions | `.iso .chd .cue`, unchanged from pinned Batocera |
| CUE/BIN collection | Start the CUE; BIN tracks are not separate frontend entries |
| BIOS directory | Configured read-only BIOS root, not a new `3do/` subfolder |
| Controller/exit | Existing dynamic Player 1 mapping and configured exit chord |
| Graphics | Existing curated shaders and RetroArch console-overlay generation |
| MainRig | Two CUE games visibly accepted, with normal exit/return and frontend quit |
| WohnzimmerPC | CUE game accepted from interactive Steam/Gamescope, with normal exit/return and frontend quit |
| Result | **READY**, visibly validated on both reference hosts |

The targeted read-only MainRig collection audit found 673 CUEs and 673 BINs,
with no missing track references, unreferenced BINs or CUEs without a FILE
entry. These are collection counts, not 673 successful game tests. Two
explicit CUE dry runs resolve the existing managed `opera_libretro.so`,
one exact content argument, the configured BIOS root and isolated Embercade
configuration/saves/cache. No new emulator or core is installed or distributed.

### BIOS contract and evidence

Pinned Batocera `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48` provides the
Opera system/core metadata and Configgen options. Its BIOS checker lists
`panafz1.bin`, `panafz10.bin` and `goldstar.bin`; the MainRig currently has all
three with matching upstream MD5s. Opera requires one supported system BIOS,
not all three. The shared read-only Doctor/launch/dry-run check reuses the
BIOS inventory evaluator and accepts a checksum-verified BIOS at its exact
root-relative filename. Missing, wrong-case, wrong-location and corrupt
firmware are diagnosed without copying, moving or renaming source files.

The additional accepted filenames/hashes come from
[`libopera/opera_bios.c` at the core revision pinned by Batocera](https://github.com/libretro/opera-libretro/blob/a501a278d057b952d1ad6165549c59ab178ca497/libopera/opera_bios.c):
`panafz1j.bin`, `panafz1j-norsa.bin`, `panafz10-norsa.bin`,
`panafz10e-anvil.bin`, `panafz10e-anvil-norsa.bin`, `sanyotry.bin` and
`3do_arcade_saot.bin`. Availability does not guarantee a particular game is
compatible with every BIOS. Embercade does not override the core's own BIOS
selection. Japanese-font ROMs are a separate, title-dependent requirement,
not mandatory for the basic system route; see the
[official Opera documentation](https://docs.libretro.com/library/opera/).

The pinned 3DO catalog offers only Opera; no standalone alternative is added.
The existing Batocera feature metadata remains authoritative for resolution,
CPU clock, active-device count, game timing fixes and NVRAM storage. Per-game
NVRAM is the upstream default for ordinary names; names containing `disc`
can select shared NVRAM unless explicitly configured. These writes remain
under the existing Embercade save directory.

### Automated verification

The full suite passes **459 tests**, including 13 targeted 3DO tests:
system recognition/CUE filtering, managed-core resolution, BIOS one-of and
failure diagnoses, spaces in the CUE path, controller/exit presets, and
external-source immutability. A real pinned launcher/Configgen dry-run test
also verifies Opera options, console-overlay generation and the staged shader
chain without executing RetroArch. Runtime, frontend-library and shader
smokes (14 presets/142 dependency files), Production Stage, offline bundle,
staged/installed Doctor and `git diff --check` pass. MainRig's normal update
preserves the inventoried config, saves, themes, cores/providers, PPSSPP
resources, Steam artwork and normal host emulator profiles.

### Visible MainRig acceptance

The user confirms the 3DO system is visible without separate BIN entries and
two CUE games work with image, sound, controller input, `consoles` decoration,
correct proportions and `crt-easymode`. The process/log evidence verifies the
managed Opera core, the installation-local shader preset and RetroArch's
overlay path in isolated Embercade config. Both launcher runs end with status
0, returning to the same EmulationStation PID. The user then quits normally
to the desktop, leaving no frontend or RetroArch process. This E2E evidence,
not the dry runs, permits adding `3do` to the compatibility ledger.

### Visible WohnzimmerPC acceptance and update preservation

The normal offline installer updates the second host without purge. Its
existing read-only host Opera core is found by the same resolver's fallback
path; no managed-core copy or package installation is needed. Doctor verifies
the 3DO BIOS set and resolves all 29 cores required by the enabled collection.
The user starts Embercade from the real interactive Steam/Gamescope session
and confirms the CUE game's image, audio, controller, `crt-easymode`, console
bezel and proportions. Logs verify the loaded BIOS, compiled staged shader,
isolated overlay configuration, Select+Start mapping and launcher status 0.
The same frontend PID remains after the game; normal Quit Embercade then
leaves no frontend or RetroArch process, with Steam still running.

Before/after normal updates preserve all inventoried configuration, saves,
themes/active selection, managed resources and Steam artwork on both hosts.
Host emulator profiles remain unchanged after gameplay. The final offline
payload is installed on both hosts and verified by the same stage manifest
and all per-file hashes, rather than assuming that a matching version label
proves identical installations. An old second-host application's regenerated
Python cache initially blocks its strict update guard; the narrowly scoped
installer fix tolerates only runtime/application bytecode in an existing
installation. Source/resource and incoming-bundle verification stay strict,
with a regression test for rejected non-cache modifications and state retention.

### Remaining scope

Multiplayer, specialist peripherals, all BIOS/region combinations,
Japanese-font cases and shared-NVRAM multi-disc behavior are not inferred
from these automated checks. External ROM roots remain read-only, so ES
reports rejected `gamelist.xml` writes on quit; collection-side metadata/play
statistics persistence was deferred at the original 3DO acceptance; the later
ScreenScraper integration now grants only gamelist/media writes, never general
ROM-content writes. Embercade remains PRIVATE; this addition does
not resolve the existing third-party asset licensing/public-release blocker.

## PS4 / user-supplied shadPS4 (1.0)

| Contract | Verified implementation |
|---|---|
| System / runtime | Pinned Batocera `ps4` / built-in `Shadps4` generator |
| Content | `.ps4` directory with readable `eboot.bin`, or `.zar` archive |
| Provider | User-selected shadPS4 AppImage only; no download/link, bundled binary or PATH fallback |
| Identity | ELF/type-2/SquashFS and embedded `net.shadps4.shadPS4.desktop` fields |
| Import | Existing importer: copy, SHA-256 reuse, explicit ambiguity/conflict, untouched source |
| Setup | Optional own wizard step plus `setup --shadps4-from`; shared backend |
| Command | Resolved AppImage `-g <eboot.bin> --fullscreen true`; `-b` opens the browser only |
| State | Embercade-owned config/input/saves/addons/cache/logs; normal host profile untouched |
| Input / exit | Existing dynamic SDL selection and launch-scoped central configured exit bridge |
| MainRig | Actual gameplay, audio, controller, Guide+Start, exit 0, same frontend and normal quit: **READY** |
| WohnzimmerPC | Actual Steam/Gamescope gameplay/audio/controller, Select+Start, exit 0 and same frontend: **READY** |

The MainRig tested user-provided v0.19.0, revision
`c7e065d1b415be16c23e260a21f1dd8bbfc4cb57`, with its existing game and host
RADV/Wayland GPU stack. External AppImage/game and host-profile fingerprints
remain unchanged. No automatic 60-FPS/4K setup or patch is invented; existing
GPU/rendering/timing values survive generation unless explicitly overridden.
Fonts, system modules, keys, firmware and title compatibility remain
user/content-specific. No emulator runs on synthetic structural fixtures.
ZAR is inherited catalog/generator support, not a claimed real ZAR gameplay test.

The user approved transferring the same supplied AppImage to the second host
via SSH, separately from the Embercade payload. Its installed copy passes the
same identity and host-runtime checks. Separate real interactive second-host
acceptance confirms Bloodborne gameplay, image/audio/controller and
Select+Start, launcher status 0 and return to the same frontend. No provider
process or AppImage mount remains. MainRig evidence was not substituted for
this Gamescope test. The existing Xenia/Steam-return regression also passes.
The shared ledger records this tested route, not universal title performance.

The suite passes 505 tests, including identification, ambiguity, import reuse,
source protection, wizard retention, diagnostics, exact pinned-generator argv,
isolated configuration and scoped exit. Runtime/frontend-library/shader smokes
pass. Both installations' full payload hashes match; normal update and
identical-payload no-op checks preserve inventoried configuration, managed
providers/cores, saves, themes and Steam/scraper data. External AppImage/game
hashes and normal host-profile fingerprints remain unchanged. No asset/license
scope changes.

## Wii native controllers (1.0)

MainRig **READY** is supported by user-confirmed Super Mario Galaxy gameplay:
image/audio, RVL-003 buttons, Nunchuk stick/C/Z, IR, motion, rumble, wireless
reconnect inside Dolphin and the frontend, and Guide+Start return to the same
frontend. Hardware is Mayflash DolphinBar mode 4 / `057e:0306`, player 1.
The existing Batocera option controls Auto real/gamepad fallback, forced
emulation or forced Real. Native Dolphin owns extensions and scanning;
GameCube F-Zero GX launch/control/exit regression passes.

The same hardware is independently accepted in Super Mario Galaxy from the
WohnzimmerPC's real interactive Steam/Gamescope session: image/audio, real
buttons, Nunchuk, IR, motion, rumble, wireless reconnect in Dolphin/the frontend,
relaunch and Select+Start return. Native Source 2, continuous scanning, the
receiver HID handle and launcher status 0 are verified. The tested standalone
DolphinBar/Nunchuk route is therefore **READY on both reference hosts**.

MotionPlus, direct Bluetooth/passthrough and multiple remotes are
**UNVALIDATED**. Receiver USB unplug/replug requires restarting the frontend;
wireless reconnect is a separate, accepted case. Doctor does not require Wii
hardware. Dolphin Libretro is a separate unimplemented desktop path: its
present MainRig core is not handed to Configgen and that selection aborts
with `MissingCore` before RetroArch starts. No Libretro READY is inferred.
See [WII_CONTROLLERS.md](WII_CONTROLLERS.md) for scope, isolation and sources.

## Two-player gamepads (1.0)

The 1.0 input route retains EmulationStation's player preferences and Batocera
Configgen. MainRig/Hyprland visibly validates Xbox 360 USB-receiver Player 1
and Xbox Series Bluetooth Player 2 in NES Contra: independent D-pads and face
buttons, live reconnect of either player without losing the other's input,
P1-only exit and return to the same frontend. GameCube Mario Kart: Double
Dash!! separately validates standalone Dolphin two-player control. The
Bluetooth pad's extra Linux system key previously shifted Dolphin's evdev
button numbers relative to SDL; the current pinned compatibility patch maps
both devices to the same physical face-button behavior without changing the
GameCube face-button rotation option. These are tested titles and devices,
not a blanket multiplayer claim for every core or emulator.

The same live translation now applies to Dolphin's Player-1 exit binding.
On MainRig, an Xbox Bluetooth Player-1 GameCube launch generated matching
`Hotkeys.ini` and `GCPadNew.ini` evdev button slots, and Guide+Start returned
to the same frontend. This fixes the case where gameplay worked but the
Bluetooth pad's exit chord did not.

The WohnzimmerPC independently passed the same two titles from its real
Steam/Gamescope session with a generic USB Xbox-style P1 pad and an Xbox Series
Bluetooth P2 pad. Contra retained both players after P2 live reconnect; both
Mario Kart drivers had independent, matching controls. P1 exited each title
back to the same frontend. The second host's offline payload and the MainRig
installation have the same verified Stage manifest, and installed Doctor
passes on both. PCSX2 and Xenia single-player launch/input/exit regressions
also pass there. This does not establish P1 live reconnect on the second host.

Structural tests cover up to eight Batocera slots, player preferences,
duplicate GUIDs, current-device re-enumeration, P1 exit ownership, single-pad
fallback, RetroArch SDL2 configuration and Dolphin evdev translation. The
full suite passes 542 tests. Runtime and frontend-library smokes, Production
Stage and installed Doctor pass. P3/P4 hardware, two identical Bluetooth
controllers and live reconnect inside standalone Dolphin remain unvalidated.
See [MULTI_CONTROLLER.md](MULTI_CONTROLLER.md) for the device-resolution
contract and separate host results.

## Special controllers — structural only (1.0)

| Class | Status | Prepared route | Missing acceptance |
|---|---|---|---|
| Lightguns | **PREPARED / UNVALIDATED** | Batocera udev gun discovery, Configgen; RetroArch udev mouse/gun input, upstream PCSX2 GunCon2 and Dolphin evdev mapping | Physical device, game input, aiming/calibration, player order, focus and exit/return |
| Wheels | **PREPARED / UNVALIDATED** | udev wheel classification plus existing SDL/ES controller mapping; upstream PCSX2 steering/pedals and Dolphin wheel generator; raw axes in desktop session | Physical wheel/pedals/shifter, player order, FFB, game input and exit/return |
| Trackballs | **PREPARED / UNVALIDATED** | Relative mouse/pointer through existing `/dev/input` and RetroArch `udev` input driver, with core mouse options | Physical relative-motion device, focus, game mapping, hotplug and exit/return |

These are controller-class statuses, not additions to the 257-system catalog
counts below. No matching hardware E2E exists; neither a udev tag nor a
generator fixture earns READY. An arbitrary raw HID wheel without a usable
SDL/ES mapping is not claimed supported. Desktop wheel range/deadzone
calibration and FFB are not validated or promised. MAME/MESS remains BLOCKED
for its independent appliance data/work-path issue. The existing Player 1
gamepad exit chord and normal gamepad mapping remain authoritative. See
[SPECIAL_CONTROLLERS.md](SPECIAL_CONTROLLERS.md) for exact source routes,
limits and later acceptance criteria.

## Catalog preparation contract

The full catalog comes from Batocera's own pinned registry/builders, not a new
selection database. The previous launch capability covered 41 IDs (40 game-E2E
systems plus Wii); 216 of the 257 catalog IDs were outside that capability.
This preparation adds 50 generic Libretro capabilities, including Cassette
Vision's pd777; all 50 have successful pinned-generator structural evidence.
At that earlier preparation milestone the Wii plugin had structural proof
only. The later native-controller acceptance above now promotes the tested
standalone Wii route, not untested peripheral/provider alternatives.

Every active definition retains Batocera extensions and defaults. Matching
content added to the canonical directory becomes visible on the next normal
frontend discovery without a code change. Empty/companion-only systems stay
hidden. Archive/disc/M3U semantics are inherited from the pinned system/core;
a synthetic first-extension fixture is not proof of every media format,
multi-disc transition or title. No emulator is started with synthetic content.

Actual core checks require ELF Libretro exports and loader closure. Optional
.info metadata is reported separately and never blocks preparation or Doctor.
The pinned Batocera catalog supplies system/core mappings and extensions;
the existing exact-core RetroArch -L launch does not require .info files.
Missing or broken libraries are never waived. Neither metadata presence nor
a successful structural test establishes real game E2E.
Host paths are retained only in ignored local JSON. Firmware requirements,
expected upstream hashes, availability and core/provider findings are available
through the installed `system-coverage` command and verbose Doctor.

MAME/MESS and X68000 remain deferred isolation ports. The proven MAME 2003 Plus
route is retained. Other unimplemented routes remain explicitly BLOCKED, not
silently substituted with a different core. Ports/game engines, media/apps,
fantasy targets and modern community hardware are explicitly outside this
classical-system preparation. Existing accepted Mr. Boom/PrBoom routes remain.
No unknown binary/provider gains a supported route just by existing on PATH.

The active `es_systems.cfg` is customized for Embercade. The audit-only
`systems-catalog.xml` intentionally does not match ES's `es_systems_*.cfg`
autoload glob. Staging preserves all existing theme/shader/decoration assets,
ships the complete metadata and rejects stale generator-proof source digests.
Production does not depend on development `.work` paths or host shader packs.

This MainRig snapshot has no missing mandatory BIOS for PREPARED systems.
The pinned checker currently reports missing requirements for the blocked
coco, dragon64, gp32, mc10, namco2x6, supracan and triforce routes.
NONE_DECLARED is absence of a matching pinned requirement, not a guarantee
that every game is firmware-free. Host-specific counts can differ; this does
not change the identical-payload requirement for the reference hosts.

The pre-PS4 reference-host comparison matched every system's status/reason,
effective emulator/core, BIOS status, extensions and structural proof, not
just the totals. MainRig and real interactive Steam/Gamescope acceptance both
pass the existing NES, 3DO, PCSX2 and Xenia regressions (image/audio/controller,
configured exit and frontend return). Quit Embercade returns cleanly to the
desktop/Steam. No new PREPARED system acquires READY from those regressions.
The existing splash is measured at 2,750 ms on each host, with a user-confirmed
clean transition. Full suite: 484 passing tests; runtime/frontend-library/shader
smokes, Production Stage and Doctor pass. Normal update preservation and
matching per-file payload verification remain required on both installations.

## Complete pinned system coverage

Batocera `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`; all 257 catalog IDs.

READY is historical real game E2E. PREPARED is generator/ABI/dependency verification,
not gameplay acceptance. Missing BIOS remains an explicit setup requirement.
Optional Libretro .info companions never block a direct core launch or preparation.
Ports/apps/media and new fantasy platforms are outside this classical-system sprint.
An installed standalone without an implemented route remains BLOCKED.

| Status | Count |
|---|---:|
| READY | 42 |
| PREPARED | 50 |
| BLOCKED | 91 |
| UNSUPPORTED | 74 |

### READY

| System | Name | Emulator / core | BIOS | Extensions | Launch route | Reason |
|---|---|---|---|---|---|---|
| `3do` | 3DO Interactive Multiplayer | libretro / opera | SATISFIED | .chd .cue .iso | implemented | CONFIRMED_GAME_E2E |
| `3ds` | 3DS | libretro / azahar | NONE_DECLARED | .3ds .app .axf .cci .cia .cxi .elf .squashfs .zcci .zcia .zcxi | implemented | CONFIRMED_GAME_E2E |
| `amiga1200` | Amiga AGA | libretro / puae | SATISFIED | .adf .adz .dms .dmz .exe .hdf .ipf .lha .m3u .raw .scp .uae .zip | implemented | CONFIRMED_GAME_E2E |
| `amigacd32` | Amiga CD32 | libretro / puae | SATISFIED | .bin .chd .cue .iso | implemented | CONFIRMED_GAME_E2E |
| `atari2600` | Atari 2600 | libretro / stella | NONE_DECLARED | .7z .a26 .bin .zip | implemented | CONFIRMED_GAME_E2E |
| `atari5200` | Atari 5200 | libretro / atari800 | SATISFIED | .7z .a52 .atr .atx .bin .car .cas .cdm .rom .xex .xfd .zip | implemented | CONFIRMED_GAME_E2E |
| `atari7800` | Atari 7800 | libretro / prosystem | NONE_DECLARED | .7z .a78 .bin .zip | implemented | CONFIRMED_GAME_E2E |
| `c64` | Commodore 64 | libretro / vice_x64 | NONE_DECLARED | .7z .crt .d64 .d71 .d81 .g64 .m3u .nib .prg .t64 .tap .zip | implemented | CONFIRMED_GAME_E2E |
| `dos` | Dos (x86) | libretro / dosbox_pure | NONE_DECLARED | .cue .dos .dosz .iso .m3u .pc .squashfs .zip | implemented | CONFIRMED_GAME_E2E |
| `dreamcast` | Dreamcast | libretro / flycast | SATISFIED | .cdi .chd .cue .gdi .m3u | implemented | CONFIRMED_GAME_E2E |
| `gamecube` | GameCube | dolphin / dolphin | SATISFIED | .ciso .dol .elf .gcm .gcz .iso .json .m3u .rvz .wbfs | implemented | CONFIRMED_GAME_E2E |
| `gamegear` | Game Gear | libretro / genesisplusgx | NONE_DECLARED | .7z .bin .gg .zip | implemented | CONFIRMED_GAME_E2E |
| `gb` | Game Boy | libretro / gambatte | NONE_DECLARED | .7z .gb .zip | implemented | CONFIRMED_GAME_E2E |
| `gba` | Game Boy Advance | libretro / mgba | SATISFIED | .7z .gba .rar .tar .zip | implemented | CONFIRMED_GAME_E2E |
| `gbc` | Game Boy Color | libretro / gambatte | NONE_DECLARED | .7z .gbc .zip | implemented | CONFIRMED_GAME_E2E |
| `jaguar` | Jaguar | libretro / virtualjaguar | NONE_DECLARED | .7z .abs .cof .j64 .jag .rom .zip | implemented | CONFIRMED_GAME_E2E |
| `mame` | Mame | libretro / mame078plus | NONE_DECLARED | .7z .zip | implemented | CONFIRMED_GAME_E2E |
| `mastersystem` | Master System | libretro / genesisplusgx | NONE_DECLARED | .7z .bin .sms .zip | implemented | CONFIRMED_GAME_E2E |
| `megacd` | Mega CD | libretro / genesisplusgx | SATISFIED | .chd .cue .iso .m3u | implemented | CONFIRMED_GAME_E2E |
| `megadrive` | Mega Drive | libretro / genesisplusgx | NONE_DECLARED | .7z .bin .gen .md .sg .smd .zip | implemented | CONFIRMED_GAME_E2E |
| `mrboom` | MrBoom | libretro / mrboom | NONE_DECLARED | .libretro | implemented | CONFIRMED_GAME_E2E |
| `n64` | Nintendo 64 | libretro / mupen64plus-next | NONE_DECLARED | .7z .n64 .v64 .z64 .zip | implemented | CONFIRMED_GAME_E2E |
| `nds` | Nintendo DS | libretro / melondsds | SATISFIED | .7z .bin .nds .zip | implemented | CONFIRMED_GAME_E2E |
| `neogeo` | Neo-Geo | libretro / fbneo | SATISFIED | .7z .zip | implemented | CONFIRMED_GAME_E2E |
| `neogeocd` | Neo-Geo CD | libretro / neocd | SATISFIED | .chd .cue .iso | implemented | CONFIRMED_GAME_E2E |
| `nes` | Nintendo Entertainment System | libretro / nestopia | NONE_DECLARED | .7z .nes .unf .unif .zip | implemented | CONFIRMED_GAME_E2E |
| `ngpc` | Neo-Geo Pocket Color | libretro / mednafen_ngp | NONE_DECLARED | .7z .ngc .zip | implemented | CONFIRMED_GAME_E2E |
| `pcengine` | PC Engine | libretro / pce | SATISFIED | .7z .bin .pce .zip | implemented | CONFIRMED_GAME_E2E |
| `pcenginecd` | PC Engine CD | libretro / pce | NONE_DECLARED | .ccd .chd .cue .img .iso .pce | implemented | CONFIRMED_GAME_E2E |
| `prboom` | PrBoom | libretro / prboom | NONE_DECLARED | .iwad .pwad .wad | implemented | CONFIRMED_GAME_E2E |
| `ps2` | PlayStation 2 | pcsx2 / pcsx2 | SATISFIED | .bin .chd .cso .dump .gz .img .iso .m3u .mdf .nrg .zso | implemented | CONFIRMED_GAME_E2E |
| `ps3` | PlayStation 3 | rpcs3 / rpcs3 | SATISFIED | .iso .ps3 .psn .squashfs | implemented | CONFIRMED_GAME_E2E |
| `ps4` | PlayStation 4 | shadps4 / shadps4 | NONE_DECLARED | .ps4 .zar | implemented | CONFIRMED_GAME_E2E (both reference hosts) |
| `psp` | PlayStation Portable | libretro / ppsspp | NONE_DECLARED | .chd .cso .iso .pbp .zip | implemented | CONFIRMED_GAME_E2E |
| `psx` | PlayStation | libretro / mednafen_psx | SATISFIED | .cbn .ccd .chd .cue .img .iso .m3u .mdf .pbp .toc | implemented | CONFIRMED_GAME_E2E |
| `saturn` | Saturn | libretro / beetle-saturn | SATISFIED | .ccd .chd .cue .iso .m3u .mds .zip | implemented | CONFIRMED_GAME_E2E |
| `sega32x` | 32x | libretro / picodrive | NONE_DECLARED | .32x .7z .bin .chd .md .smd .zip | implemented | CONFIRMED_GAME_E2E |
| `snes` | Super Nintendo Entertainment System | libretro / snes9x | NONE_DECLARED | .7z .bsx .dx2 .fig .gd3 .gd7 .sfc .smc .swc .zip | implemented | CONFIRMED_GAME_E2E |
| `wii` | Wii | dolphin / dolphin | NONE_DECLARED | .ciso .dol .elf .gcm .gcz .iso .json .m3u .rvz .wad .wbfs | implemented | CONFIRMED_GAME_E2E (both hosts, DolphinBar/Nunchuk) |
| `wiiu` | Wii U | libretro / cemu | NONE_DECLARED | .rpx .squashfs .wua .wud .wuhb .wup .wux | implemented | CONFIRMED_GAME_E2E |
| `xbox` | Xbox | xemu / xemu | SATISFIED | .iso .squashfs | implemented | CONFIRMED_GAME_E2E |
| `xbox360` | Xbox 360 | xenia-edge / xenia-edge | NONE_DECLARED | .iso .xbox360 .xex .zar | implemented | CONFIRMED_GAME_E2E |

### PREPARED

| System | Name | Emulator / core | BIOS | Extensions | Launch route | Reason |
|---|---|---|---|---|---|---|
| `amiga500` | Amiga OCS/ECS | libretro / puae | SATISFIED | .adf .adz .dms .dmz .exe .hdf .ipf .lha .m3u .raw .scp .uae .zip | implemented | REAL_GAME_E2E_PENDING |
| `amigacdtv` | Amiga CDTV | libretro / puae | SATISFIED | .bin .chd .cue .iso .m3u | implemented | REAL_GAME_E2E_PENDING |
| `amstradcpc` | Amstrad CPC | libretro / cap32 | NONE_DECLARED | .7z .cdt .dsk .m3u .sna .tap .voc .zip | implemented | REAL_GAME_E2E_PENDING |
| `atari800` | Atari 800 | libretro / atari800 | SATISFIED | .7z .a52 .atr .atx .bin .car .cas .cdm .m3u .rom .xex .xfd .zip | implemented | REAL_GAME_E2E_PENDING |
| `atarist` | Atari ST | libretro / hatari | SATISFIED | .7z .dim .gemdos .hd .ipf .m3u .msa .st .stx .zip | implemented | REAL_GAME_E2E_PENDING |
| `atomiswave` | Atomiswave | libretro / flycast | SATISFIED | .7z .bin .dat .lst .zip | implemented | REAL_GAME_E2E_PENDING |
| `bk` | Elektronika BK | libretro / bk | SATISFIED | .7z .bin .bkd .dsk .img .zip | implemented | REAL_GAME_E2E_PENDING |
| `cassettevision` | Cassette Vision | libretro / pd777 | NONE_DECLARED | .bin777 .zip | implemented | REAL_GAME_E2E_PENDING |
| `channelf` | Channel-F | libretro / freechaf | SATISFIED | .bin .chf .rom .zip | implemented | REAL_GAME_E2E_PENDING |
| `colecovision` | ColecoVision | libretro / bluemsx | SATISFIED | .7z .bin .col .rom .zip | implemented | REAL_GAME_E2E_PENDING |
| `dice` | DICE | libretro / dice | NONE_DECLARED | .dmy .zip | implemented | REAL_GAME_E2E_PENDING |
| `fbneo` | Final Burn Neo | libretro / fbneo | NONE_DECLARED | .7z .zip | implemented | REAL_GAME_E2E_PENDING |
| `fds` | Family Computer Disk System | libretro / fceumm | SATISFIED | .7z .fds .zip | implemented | REAL_GAME_E2E_PENDING |
| `gameandwatch` | Game and Watch | libretro / gw | NONE_DECLARED | .7z .mgw .zip | implemented | REAL_GAME_E2E_PENDING |
| `gx4000` | GX4000 | libretro / cap32 | NONE_DECLARED | .7z .cpr .dsk .m3u .zip | implemented | REAL_GAME_E2E_PENDING |
| `intellivision` | Mattel Intellivision | libretro / freeintv | SATISFIED | .7z .bin .int .rom .zip | implemented | REAL_GAME_E2E_PENDING |
| `lynx` | Atari Lynx | libretro / mednafen_lynx | SATISFIED | .7z .bll .lnx .lyx .o .zip | implemented | REAL_GAME_E2E_PENDING |
| `msx1` | MSX1 | libretro / bluemsx | SATISFIED | .7z .cas .dsk .m3u .mx1 .ogv .openmsx .rom .zip | implemented | REAL_GAME_E2E_PENDING |
| `msx2` | MSX2 | libretro / bluemsx | SATISFIED | .7z .cas .dsk .m3u .mx2 .ogv .openmsx .rom .zip | implemented | REAL_GAME_E2E_PENDING |
| `msx2+` | MSX2+ | libretro / bluemsx | SATISFIED | .7z .cas .dsk .m3u .mx2 .openmsx .rom .zip | implemented | REAL_GAME_E2E_PENDING |
| `msxturbor` | MSX Turbo-R | libretro / bluemsx | SATISFIED | .7z .dsk .m3u .mx2 .openmsx .rom .zip | implemented | REAL_GAME_E2E_PENDING |
| `multivision` | Othello Multivision | libretro / gearsystem | NONE_DECLARED | .7z .bin .sg .zip | implemented | REAL_GAME_E2E_PENDING |
| `naomi` | Naomi | libretro / flycast | SATISFIED | .7z .bin .dat .lst .zip | implemented | REAL_GAME_E2E_PENDING |
| `naomi2` | Naomi 2 | libretro / flycast | SATISFIED | .7z .zip | implemented | REAL_GAME_E2E_PENDING |
| `ngp` | Neo-Geo Pocket | libretro / mednafen_ngp | NONE_DECLARED | .7z .ngp .zip | implemented | REAL_GAME_E2E_PENDING |
| `odyssey2` | Odyssey2 | libretro / o2em | SATISFIED | .7z .bin .zip | implemented | REAL_GAME_E2E_PENDING |
| `pc88` | PC-8800 | libretro / quasi88 | SATISFIED | .cmt .d88 .m3u .u88 | implemented | REAL_GAME_E2E_PENDING |
| `pc98` | PC-9800 | libretro / np2kai | SATISFIED | .2hd .88d .98d .cmd .d88 .d98 .dup .fdd .fdi .hdd .hdi .hdm .hdn .m3u .nhd .tfd .thd .xdf .zip | implemented | REAL_GAME_E2E_PENDING |
| `pcfx` | PC-FX | libretro / pcfx | SATISFIED | .7z .ccd .chd .cue .m3u .toc .zip | implemented | REAL_GAME_E2E_PENDING |
| `pico` | Sega Pico | libretro / genesisplusgx | NONE_DECLARED | .7z .bin .md .zip | implemented | REAL_GAME_E2E_PENDING |
| `pokemini` | Pokemon Mini | libretro / pokemini | NONE_DECLARED | .7z .min .zip | implemented | REAL_GAME_E2E_PENDING |
| `satellaview` | Satellaview | libretro / snes9x | SATISFIED | .7z .bs .sfc .smc .squashfs .zip | implemented | REAL_GAME_E2E_PENDING |
| `scv` | Super Cassette Vision | libretro / emuscv | SATISFIED | .0 .bin .zip | implemented | REAL_GAME_E2E_PENDING |
| `sg1000` | SG-1000 | libretro / genesisplusgx | NONE_DECLARED | .7z .bin .sg .zip | implemented | REAL_GAME_E2E_PENDING |
| `sgb` | Super Game Boy | libretro / mesen-s | SATISFIED | .7z .gb .gbc .zip | implemented | REAL_GAME_E2E_PENDING |
| `sufami` | SuFami Turbo | libretro / snes9x | SATISFIED | .7z .bs .fig .sfc .smc .st .zip | implemented | REAL_GAME_E2E_PENDING |
| `supergrafx` | Supergrafx | libretro / mednafen_supergrafx | SATISFIED | .7z .ccd .chd .cue .pce .sgx .zip | implemented | REAL_GAME_E2E_PENDING |
| `supervision` | Supervision | libretro / potator | NONE_DECLARED | .7z .sv .zip | implemented | REAL_GAME_E2E_PENDING |
| `systemsp` | Sega System SP | libretro / flycast | NONE_DECLARED | .7z .bin .dat .lst .zip | implemented | REAL_GAME_E2E_PENDING |
| `thomson` | Thomson - MO/TO (Theodore) | libretro / theodore | NONE_DECLARED | .fd .k7 .m5 .m7 .rom .sap .zip | implemented | REAL_GAME_E2E_PENDING |
| `tvc` | Videoton TVC | libretro / ep128emu-core | SATISFIED | .cas .dsk .img .tap .zip | implemented | REAL_GAME_E2E_PENDING |
| `uzebox` | Uzebox | libretro / uzem | NONE_DECLARED | .bin .uze .zip | implemented | REAL_GAME_E2E_PENDING |
| `vectrex` | Vectrex | libretro / vecx | NONE_DECLARED | .7z .bin .gam .vec .zip | implemented | REAL_GAME_E2E_PENDING |
| `videopacplus` | Videopac+ G7400 | libretro / o2em | SATISFIED | .7z .bin .zip | implemented | REAL_GAME_E2E_PENDING |
| `virtualboy` | Virtual Boy | libretro / vb | NONE_DECLARED | .7z .vb .zip | implemented | REAL_GAME_E2E_PENDING |
| `wswan` | WonderSwan | libretro / mednafen_wswan | NONE_DECLARED | .7z .ws .zip | implemented | REAL_GAME_E2E_PENDING |
| `wswanc` | WonderSwan Color | libretro / mednafen_wswan | NONE_DECLARED | .7z .wsc .zip | implemented | REAL_GAME_E2E_PENDING |
| `x1` | Sharp X1 | libretro / x1 | SATISFIED | .2d .2hd .7z .88d .cmd .d88 .dup .dx1 .hdm .tfd .xdf .zip | implemented | REAL_GAME_E2E_PENDING |
| `zx81` | ZX81 | libretro / 81 | NONE_DECLARED | .7z .p .tzx .zip | implemented | REAL_GAME_E2E_PENDING |
| `zxspectrum` | ZX Spectrum | libretro / fuse | NONE_DECLARED | .7z .dsk .rzx .scl .tap .trd .tzx .z80 .zip | implemented | REAL_GAME_E2E_PENDING |

### BLOCKED

| System | Name | Emulator / core | BIOS | Extensions | Launch route | Reason |
|---|---|---|---|---|---|---|
| `adam` | ADAM | mame / mame | SATISFIED | .1dd .7z .bin .col .cqi .cqm .d77 .d88 .ddp .dfi .dsk .hfe .imd .mfi .mfm .rom .td0 .wav .zip | missing | EMULATOR_MISSING |
| `advision` | Adventure Vision | mame / mame | SATISFIED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `apfm1000` | M-1000 | mame / mame | SATISFIED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `apple2` | Apple II | gsplus / gsplus | NONE_DECLARED | .2mg .7z .chd .dfi .do .dsk .edd .hdv .mfi .nib .po .rti .wav .woz .zip | missing | EMULATOR_MISSING |
| `apple2gs` | Apple IIGS | gsplus / gsplus | SATISFIED | .2mg .do .dsk .nib .po | missing | EMULATOR_MISSING |
| `arcadia` | Arcadia 2001 | libretro / mame | NONE_DECLARED | .7z .bin .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `archimedes` | Archimedes | mame / mame | SATISFIED | .1dd .360 .7z .adf .adl .adm .ads .apd .bbc .chd .cqi .cqm .d77 .d88 .dfi .dsd .dsk .hfe .ima .imd .img .ipf .jfd .mfi .mfm .msa .ssd .st .td0 .ufi .zip | missing | EMULATOR_MISSING |
| `astrocade` | Astrocade | mame / mame | SATISFIED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `atom` | Atom | mame / mame | SATISFIED | .1dd .40t .7z .atm .bin .cqi .cqm .csw .d77 .d88 .dfi .dsk .hfe .imd .mfi .mfm .rom .tap .td0 .uef .wav .zip | missing | EMULATOR_MISSING |
| `bbcmicro` | BBC Micro | mame / mame | NONE_DECLARED | .1dd .360 .7z .adf .adl .adm .ads .bbc .bin .cqi .cqm .d77 .d88 .dfi .dsd .dsk .fsd .hfe .ima .imd .img .ipf .mfi .mfm .ssd .tap .td0 .ufi .wav .zip | missing | EMULATOR_MISSING |
| `beena` | Advanced Pico Beena | libretro / mame | SATISFIED | .7z .bin .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `c128` | Commodore 128 | vice / x128 | NONE_DECLARED | .7z .d64 .d81 .lnx .m3u .prg .zip | missing | EMULATOR_MISSING |
| `c20` | Commodore VIC-20 | vice / xvic | NONE_DECLARED | .20 .40 .60 .7z .a0 .b0 .crt .d64 .d81 .m3u .prg .rom .t64 .tap .zip | missing | EMULATOR_MISSING |
| `camplynx` | Camputers Lynx | mame / mame | SATISFIED | .7z .ldf .tap .wav .zip | missing | EMULATOR_MISSING |
| `cave3rd` | Cave CV1000 | libretro / mame | NONE_DECLARED | .7z .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `cdi` | CD-i | mame / mame | SATISFIED | .cdr .chd .cue .gdi .iso .nrg .toc | missing | EMULATOR_MISSING |
| `cgenie` | Colour Genie | libretro / mame | SATISFIED | .7z .cas .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `chihiro` | Sega Chihiro | xemu / xemu | SATISFIED | .iso | missing | EMBERCADE_PORT_MISSING |
| `coco` | Color Computer | mame / mame | MISSING | .7z .cas .ccc .dsk .rom .wav .zip | missing | EMULATOR_MISSING |
| `cplus4` | Commodore Plus4 | vice / xplus4 | NONE_DECLARED | .7z .d64 .m3u .prg .tap .zip | missing | EMULATOR_MISSING |
| `crvision` | CreatiVision | mame / mame | SATISFIED | .7z .bin .rom .zip | missing | EMULATOR_MISSING |
| `ctvboy` | Compact Vision TV Boy | libretro / mame | NONE_DECLARED | .7z .bin .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `daphne` | Daphne | hypseus-singe / hypseus-singe | NONE_DECLARED | .daphne .squashfs | missing | EMULATOR_MISSING |
| `dragon64` | Dragon 64 | libretro / mame | MISSING | .7z .bin .cas .ccc .dmk .dsk .rom .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `electron` | Electron | mame / mame | SATISFIED | .1dd .7z .adf .adl .adm .ads .bbc .bin .cqi .cqm .csw .d77 .d88 .dfi .dsd .dsk .hfe .imd .img .mfi .mfm .rom .ssd .td0 .uef .wav .zip | missing | EMULATOR_MISSING |
| `enterprise` | Enterprise | clk / clk | SATISFIED | .128 .bas .cas .cdt .com .dsk .dtf .img .tap .trn .tzx .zip | missing | EMULATOR_MISSING |
| `fm7` | FM-7 | mame / mame | SATISFIED | .1dd .7z .cqi .cqm .d77 .d88 .dfi .dsk .hfe .imd .mfi .mfm .t77 .td0 .wav .zip | missing | EMULATOR_MISSING |
| `fmtowns` | FM-TOWNS | tsugaru / tsugaru | SATISFIED | .1dd .7z .bin .cdr .chd .cqi .cqm .cue .d77 .d88 .dfi .dsk .gdi .hfe .imd .iso .m3u .mfi .mfm .nrg .td0 .toc .xdf .zip | missing | EMULATOR_MISSING |
| `gaelco` | Gaelco | libretro / mame | NONE_DECLARED | .7z .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `gamate` | Gamate | mame / mame | SATISFIED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `gamecom` | Game.com | mame / mame | SATISFIED | .7z .bin .tgc .zip | missing | EMULATOR_MISSING |
| `gamepock` | Game Pocket Computer | mame / mame | SATISFIED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `gb2players` | Game Boy (2 players) | libretro / tgbdual | NONE_DECLARED | .7z .gb .gb2 .gbc2 .zip | missing | EMBERCADE_PORT_MISSING |
| `gbc2players` | Game Boy Color (2 players) | libretro / tgbdual | NONE_DECLARED | .7z .gb2 .gbc .gbc2 .zip | missing | EMBERCADE_PORT_MISSING |
| `gmaster` | Game Master | mame / mame | SATISFIED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `gp32` | GP32 | mame / mame | MISSING | .7z .smc .zip | missing | EMULATOR_MISSING |
| `hikaru` | Hikaru | demul / demul | SATISFIED | .7z .zip | missing | EMULATOR_MISSING |
| `jaguarcd` | Jaguar CD | bigpemu / bigpemu | NONE_DECLARED | .bigpimg .cdi .cue | missing | EMULATOR_MISSING |
| `laser310` | Laser 310 | mame / mame | SATISFIED | .7z .cas .vz .wav .zip | missing | EMULATOR_MISSING |
| `lcdgames` | LCD Games | mame / mame | NONE_DECLARED | .7z .mgw .zip | missing | EMULATOR_MISSING |
| `lindbergh` | Sega Lindbergh | linuxloader / linuxloader | NONE_DECLARED | .game | missing | EMULATOR_MISSING |
| `loopy` | Casio Loopy | libretro / mame | SATISFIED | .7z .bin .ic1 .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `macintosh` | Macintosh | mame / mame | NONE_DECLARED | .1dd .2mg .360 .7z .cdr .chd .cqi .cqm .cue .d77 .d88 .dc42 .dfi .dsk .gdi .hd .hdi .hdv .hfe .ima .imd .img .ipf .iso .mfi .mfm .nrg .td0 .toc .ufi .woz .zip | missing | EMULATOR_MISSING |
| `mc10` | MC-10 | libretro / mame | MISSING | .7z .bin .cas .rom .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `megadrive-msu` | MSU-MD | libretro / genesisplusgx | SATISFIED | .7z .md .squashfs .zip | missing | EMBERCADE_PORT_MISSING |
| `megaduck` | Mega Duck / Cougar Boy | mame / mame | NONE_DECLARED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `model2` | Model 2 | sm2-emu / sm2-emu | NONE_DECLARED | .7z .zip | missing | EMULATOR_MISSING |
| `model3` | Model 3 | supermodel / supermodel | NONE_DECLARED | .zip | missing | EMULATOR_MISSING |
| `mz2000` | Sharp MZ-2000 | libretro / mame | SATISFIED | .7z .d88 .dsk .m12 .mzf .mzt .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `mz2500` | Sharp MZ-2500 | libretro / mame | SATISFIED | .1dd .7z .cqi .cqm .d77 .d88 .dfi .dsk .hfe .imd .mfi .mfm .td0 .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `mz700` | Sharp MZ-700 | libretro / mame | SATISFIED | .7z .m12 .mzf .mzt .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `mz800` | Sharp MZ-800 | libretro / mame | SATISFIED | .7z .m12 .mzf .mzt .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `mz80k` | Sharp MZ-80K | libretro / mame | SATISFIED | .7z .m12 .mzf .mzt .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `n64dd` | Nintendo 64 Disk Drive | mupen64plus / glide64mk2 | SATISFIED | .7z .n64 .ndd .z64 .zip | missing | EMULATOR_MISSING |
| `namco22` | Namco System 22 | libretro / mame | NONE_DECLARED | .7z .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `namco2x6` | Namco System 246/256 | pcsx2x6 / pcsx2x6 | MISSING | .acgame | missing | EMULATOR_MISSING |
| `namco3xx` | Namco 3xx | rpcs3 / rpcs3 | NONE_DECLARED | .squashfs | missing | EMBERCADE_PORT_MISSING |
| `ngage` | N-Gage | eka2l1 / eka2l1 | NONE_DECLARED | .n-gage .sis .sisx .zip | missing | EMULATOR_MISSING |
| `oricatmos` | Oric Atmos | clk / clk | SATISFIED | .dsk .tap .zip | missing | EMULATOR_MISSING |
| `pc60` | PC-6000 | libretro / mame | SATISFIED | .1dd .2hd .7z .bin .cas .cqi .cqm .d77 .d88 .dfi .dsk .fdi .hdm .imd .mfi .mfm .p6 .td0 .xdf .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `pc80` | PC-8001 | libretro / mame | SATISFIED | .1dd .7z .bin .d77 .d88 .dsk .n80 .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `pcw` | Amstrad PCW | libretro / mame | SATISFIED | .1dd .7z .86f .cqi .cqm .d77 .d88 .dfi .dsk .imd .mfi .mfm .td0 .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `pdp1` | PDP-1 | mame / mame | NONE_DECLARED | .7z .drm .rim .tap .zip | missing | EMULATOR_MISSING |
| `pet` | Commodore PET | vice / xpet | NONE_DECLARED | .7z .a0 .b0 .crt .d64 .d81 .m3u .prg .t64 .tap .zip | missing | EMULATOR_MISSING |
| `psvita` | PlayStation Vita | vita3k / vita3k | SATISFIED | .psvita .zip | missing | EMULATOR_MISSING |
| `pv1000` | PV-1000 | mame / mame | NONE_DECLARED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `pv2000` | PV-2000 | libretro / mame | SATISFIED | .7z .bin .cas .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `rx78` | RX-78 | libretro / mame | SATISFIED | .7z .bin .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `samcoupe` | SAM Coupé | samcoupe / samcoupe | NONE_DECLARED | .cpm .dsk .mgt .sad .sbt .sdf .td0 .zip | missing | EMULATOR_MISSING |
| `sc3000` | SC-3000 | libretro / mame | NONE_DECLARED | .7z .bin .bit .cas .sg .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `scummvm` | ScummVM | scummvm / scummvm | SATISFIED | .scummvm .squashfs | missing | EMULATOR_MISSING |
| `segaai` | Sega AI Computer | libretro / mame | SATISFIED | .7z .bin .cas .flac .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `sgb-msu1` | Super Game Boy MSU1 | libretro / bsnes | NONE_DECLARED | .7z .gb .gbc .squashfs .zip | missing | EMBERCADE_PORT_MISSING |
| `singe` | Singe | hypseus-singe / hypseus-singe | NONE_DECLARED | .daphne .squashfs | missing | EMULATOR_MISSING |
| `snes-msu1` | Super Disc System (MSU1) | libretro / snes9x | NONE_DECLARED | .sfc .smc .squashfs | missing | EMBERCADE_PORT_MISSING |
| `socrates` | Socrates | mame / mame | SATISFIED | .7z .bin .zip | missing | EMULATOR_MISSING |
| `spectravideo` | Spectravideo SV-328 | openmsx / openmsx | NONE_DECLARED | .7z .cas .zip | missing | EMULATOR_MISSING |
| `supracan` | Super A'Can | mame / mame | MISSING | .7z .bin .zip | missing | EMULATOR_MISSING |
| `sv8000` | Super Vision 8000 | libretro / mame | NONE_DECLARED | .7z .bin .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `ti99` | TI-99 | mame / mame | SATISFIED | .7z .rpk .wav .zip | missing | EMULATOR_MISSING |
| `triforce` | Triforce | dolphin / dolphin | MISSING | .iso .rvz | missing | EMBERCADE_PORT_MISSING |
| `trs80` | TRS-80 | libretro / mame | SATISFIED | .7z .bas .cas .cmd .dmk .dsk .wav .zip | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `tutor` | Tutor | mame / mame | SATISFIED | .7z .bin .wav .zip | missing | EMULATOR_MISSING |
| `tvgames` | Plug and Play TV Games | mame / mame | NONE_DECLARED | .7z .zip | missing | EMULATOR_MISSING |
| `vc4000` | VC 4000 | mame / mame | NONE_DECLARED | .7z .bin .pgm .rom .tvc .zip | missing | EMULATOR_MISSING |
| `vemulator` | Dreamcast VMU | None / None | NONE_DECLARED | .bin .dci .vms | missing | EMULATOR_MISSING |
| `vgmplay` | Video Game Music Player | mame / mame | SATISFIED | .7z .vgm .vgz .zip | missing | EMULATOR_MISSING |
| `vis` | Tandy Video Information System | libretro / mame | SATISFIED | .cdr .chd .cue .gdi .iso .nrg .toc | missing | MAME_MESS_APPLIANCE_PATHS_AND_DATA_NOT_PORTED |
| `vsmile` | V.Smile | mame / mame | SATISFIED | .7z .bin .u1 .u3 .zip | missing | EMULATOR_MISSING |
| `x68000` | Sharp X68000 | libretro / px68k | SATISFIED | .2hd .7z .88d .cmd .d88 .dim .dup .hdf .hdm .img .m3u .xdf .zip | missing | PX68K_WRITABLE_BIOS_CONFIG_NOT_ISOLATED |
| `xegs` | Atari XE Game System | mame / mame | SATISFIED | .7z .atr .bin .car .dsk .rom .xfd .zip | missing | EMULATOR_MISSING |

### UNSUPPORTED

| System | Name | Emulator / core | BIOS | Extensions | Launch route | Reason |
|---|---|---|---|---|---|---|
| `abuse` | Abuse | abuse / abuse | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `arduboy` | Arduboy | libretro / arduous | NONE_DECLARED | .7z .hex .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `bennugd` | Bennu Game Development | libretro / bennugd | NONE_DECLARED | .dat .dcb | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `bstone` | Blake Stone | bstone / bstone | NONE_DECLARED | .bstone | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `cannonball` | Cannonball | cannonball / cannonball | NONE_DECLARED | .cannonball | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `catacomb` | CatacombGL | catacombgl / catacombgl | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `cavestory` | Cave Story | libretro / nxengine | NONE_DECLARED | .exe | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `cdogs` | C-Dogs SDL | cdogs / cdogs | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `cgenius` | Commander Genius | cgenius / cgenius | NONE_DECLARED | .cgenius | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `commanderx16` | Commander X16 | x16emu / x16emu | NONE_DECLARED | .bas .img .prg | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `corsixth` | CorsixTH | corsixth / corsixth | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `devilutionx` | Diablo | devilutionx / devilutionx | NONE_DECLARED | .mpq | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `doom3` | Doom 3 | dhewm3 / dhewm3 | NONE_DECLARED | .d3 | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `dxx-rebirth` | DXX Rebirth | dxx-rebirth / dxx-rebirth | NONE_DECLARED | .d1x .d2x | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `easyrpg` | EasyRPG | easyrpg / easyrpg | NONE_DECLARED | .easyrpg .squashfs .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `ecwolf` | ECWolf | ecwolf / ecwolf | NONE_DECLARED | .ecwolf .pk3 .squashfs | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `eduke32` | EDuke32 | eduke32 / eduke32 | NONE_DECLARED | .eduke32 | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `etlegacy` | Wolfenstein - Enemy Territory | etlegacy / etlegacy | NONE_DECLARED | .etl | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `fallout1-ce` | Fallout Community Edition | fallout1-ce / fallout1-ce | NONE_DECLARED | .f1ce | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `fallout2-ce` | Fallout 2 Community Edition | fallout2-ce / fallout2-ce | NONE_DECLARED | .f2ce | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `flash` | Flash Player | ruffle / ruffle | NONE_DECLARED | .swf | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `flatpak` | Applications | flatpak / flatpak | NONE_DECLARED | .flatpak | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `fury` | Ion Fury | eduke32 / fury | NONE_DECLARED | .grp | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `gametank` | GameTank | gametank-emulator / gametank-emulator | NONE_DECLARED | .gtr | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `halflife` | Half-Life 1 | xash3d_fwgs / xash3d_fwgs | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `hcl` | Hydra Castle Labyrinth | hcl / hcl | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `hurrican` | Hurrican | hurrican / hurrican | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `ikemen` | IKEMEN | ikemen / ikemen | NONE_DECLARED | .ikemen .pc | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `imageviewer` | Screenshots | None / None | NONE_DECLARED | .avi .bmp .gif .hdr .jpeg .jpg .mkv .mp4 .pdf .pgm .pic .png .ppm .psd .tga .webm | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `jazz2` | Jazz Jackrabbit 2 | jazz2-native / jazz2-native | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `jkdf2` | Jedi Knight - Dark Forces 2 | openjkdf2 / openjkdf2 | NONE_DECLARED | .jedi | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `jknight` | Star Wars - Jedi Academy | openjk / openjk | NONE_DECLARED | .jedi | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `library` | Library | None / None | NONE_DECLARED | .669 .avi .bmp .cbz .far .flac .gif .hdr .it .jpeg .jpg .mkv .mod .mp3 .mp4 .mtm .ogg .pdf .pgm .pic .png .ppm .psd .s3m .stm .tga .wav .webm .xm | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `lowresnx` | Lowres NX | libretro / lowresnx | NONE_DECLARED | .7z .nx .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `lutro` | Lutro | libretro / lutro | NONE_DECLARED | .7z .lutro .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `mohaa` | Medal Of Honor - Allied Assault | openmohaa / openmohaa | NONE_DECLARED | .mohaa | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `moonlight` | Moonlight | moonlight / moonlight | NONE_DECLARED | .moonlight | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `mugen` | MUGEN | mugen / wine-tkg | NONE_DECLARED | .pc | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `odcommander` | OD-Commander | odcommander / odcommander | NONE_DECLARED | .odc | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `openbor` | OpenBOR | openbor / openbor6412 | NONE_DECLARED | .pak | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `openjazz` | Jazz Jackrabbit | openjazz / openjazz | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `pico8` | Pico-8 | libretro / fake08 | NONE_DECLARED | .m3u .p8 .png | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `ports` | Ports | sh / sh | NONE_DECLARED | .sh .squashfs | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `pygame` | Pygame | pygame / pygame | NONE_DECLARED | .pygame | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `pyxel` | pyxel | pyxel / pyxel | NONE_DECLARED | .py .pyxapp | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `quake` | Quake | libretro / tyrquake | NONE_DECLARED | .quake | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `quake2` | Quake II | yquake2 / yquake2 | NONE_DECLARED | .7zip .quake2 .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `quake3` | Quake III | vkquake3 / vkquake3 | NONE_DECLARED | .quake3 | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `raze` | Raze | raze / raze | NONE_DECLARED | .raze | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `recordings` | Recordings | None / None | NONE_DECLARED | .avi .flac .mkv .mp3 .mp4 .ogg .wav .webm | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `reminiscence` | REminiscence | libretro / reminiscence | NONE_DECLARED | .rem | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `rott` | Rise of the Triad | taradino / taradino | NONE_DECLARED | .rott | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `rtcw` | Return To Castle Wolfenstein | iortcw / iortcw | NONE_DECLARED | .rtcw | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `sdlpop` | SdlPop | sdlpop / sdlpop | NONE_DECLARED | .sdlpop | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `solarus` | Solarus | solarus / solarus | NONE_DECLARED | .solarus .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `sonic-mania` | Sonic Mania | sonic-mania / sonic-mania | NONE_DECLARED | .sman | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `sonic3-air` | Sonic 3 A.I.R. | sonic3-air / sonic3-air | NONE_DECLARED | .s3air | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `sonicretro` | Sonic Retro Engine | sonic2013 / sonic2013 | NONE_DECLARED | .scd .son | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `steam` | Steam | steam / steam | NONE_DECLARED | .steam | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `superbroswar` | Super Mario War | libretro / superbroswar | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `theforceengine` | The Force Engine | theforceengine / theforceengine | NONE_DECLARED | .tfe | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `thextech` | TheXTech | thextech / thextech | NONE_DECLARED | .smbx .squashfs | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `tic80` | TIC-80 | libretro / tic80 | NONE_DECLARED | .tic | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `traider` | Tomb Raider I, II & III | trx / trx | NONE_DECLARED | .croft | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `tyrian` | Tyrian | tyrian / tyrian | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `uqm` | Ur-Quan Masters | uqm / uqm | NONE_DECLARED | .game | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `uzdoom` | UZDoom | uzdoom / uzdoom | NONE_DECLARED | .iwad .pwad .uzdoom .wad | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `vircon32` | vircon32 | libretro / vircon32 | NONE_DECLARED | .v32 .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `vpinball` | Visual Pinball X | vpinball / vpinball | NONE_DECLARED | .vpx | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `wasm4` | wasm4 | libretro / wasm4 | NONE_DECLARED | .wasm | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `windows` | Windows | wine / wine-tkg | NONE_DECLARED | .exe .pc .wine .wsquashfs .wtgz | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `windows_installers` | Install a new Windows game | wine / wine-tkg | NONE_DECLARED | .exe .iso .msi | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `xrick` | xrick | libretro / xrick | NONE_DECLARED | .zip | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |
| `zc210` | Zelda Classic | libretro / zc210 | SATISFIED | .qst | missing | NON_CLASSICAL_PORT_APP_OR_MEDIA |

### Setup/E2E still required

Every PREPARED system needs a legally supplied compatible game/ROM set,
the listed firmware and real image/audio/input/exit/return acceptance.
Computer keyboard/media layouts, arcade BIOS/software sets, peripherals,
multiplayer and uncommon formats are not proven by a generator-only fixture.
Missing per-system artwork uses the existing optional decoration fallback;
shader presets are installation-local. Nothing is downloaded or installed.

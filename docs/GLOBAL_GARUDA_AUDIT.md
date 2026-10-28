# Embercade 1.0: global Garuda audit and bilingual first run

This audit follows `5518c51` and keeps the exact `upstream.lock` pins. The owner
explicitly approved tasks 9 (German/English installer) and 10 (terminal lifecycle)
as 1.0 additions to the release freeze. Task 10 supersedes task 7's original
proposal to defer terminal completion to 1.1. No emulator package, firmware,
ROM, EEPROM, HDD, normal emulator profile or personal ScreenScraper login was
changed during implementation/testing. The owner separately approved and
locally authenticated installation of `gtk-layer-shell` for the KDE test.

Status update, 10 October 2026: the owner confirms ScreenScraper works in the
new MainRig AppImage after identifying a user-side issue. The findings below
retain this earlier audit's evidence. See [the current ScreenScraper status](SCREENSCRAPER.md#current-garuda-final-polish-status-2026-10-10)
for the resolved incident and the separate public provisioning gate.

## Findings, fixes and acceptance

| Finding | Root cause / evidence | Change | Automated evidence | Required manual acceptance | Deferred / external |
| --- | --- | --- | --- | --- | --- |
| 1. RetroArch viewport offset across GB/SFC and other cores | `current_resolution()` queried Hyprland only and otherwise supplied 1920×1080. Actual KScreen mode was 2560×1440; generated fullscreen/viewport coordinates used the smaller size. | Query KScreen's active physical mode on KDE, respecting rotation; use the logical Xrandr game output in Gamescope/X11. Explicit overrides retain precedence. No mode switch, core-specific viewport/shader workaround or saved aspect override. | Display unit checks, actual KDE query, 52 pinned generator structural routes and regression suite. | GB and SFC, borders, shaders and integer/aspect choices on MainRig; Gamescope resolution regression on Wohnzimmer-PC. | No core workaround. |
| 2. No Xemu/GameCube/Wii standalone frames on KDE | Shared helper selected only Hyprland/Gamescope. KDE was explicitly unsupported. MangoHud was absent and is not the diagnosis. | Reuse the layer renderer with a disposable KWin observer, exact executable/ancestry/fullscreen/monitor checks, focus hiding, owner EOF and crash cleanup. Offer `gtk-layer-shell` through existing bootstrap for KDE/Hyprland Wayland. | Actual KWin 6.7.5 normal/crash cleanup and owned GTK fullscreen→windowed fixture; selection, clipping and lifecycle regressions. | Real Xemu, GameCube and Wii, focus/workspace changes, exit/return/Quit on KDE; unchanged Gamescope route on second host. | Xemu Auto still conservatively reserves 16:9. Select existing 4x3/Scale option for a full frame; no forced user aspect changes. |
| 3. RPCS3 first-run firmware | GUI setup used noninteractive CLI input and therefore skipped its native firmware offer. Doctor recognized host firmware, but direct runtime resolution did not share that discovery. Owner's normal profile contains 4.90; the isolated tree was empty. | Share source discovery; preserve existing isolated firmware, reject conflicting replacements. Add an explicit wizard action opening RPCS3 in Embercade-owned XDG roots, then recheck. | Host-source import, missing/PUP-only firmware, isolated UI environment and no-overwrite checks. | Install own PUP or import existing firmware; real PS3 game/exit/return. | A 4.90 installed notice does not prove a successful game boot. |
| 4. ScreenScraper developer authorization | Developer secret absent; separate personal secret configured but authentication not exercised. Embercade intentionally does not embed extractable developer credentials. | Preserve runtime-only provisioning and personal login. Explain the separate developer requirement in localized installer checks. Compare exact pinned .mk/CMake/source chain. | Existing private-file, user migration, scraper boundary and payload tests. | Approved developer provisioning and real successful scrape on both hosts. | PUBLIC-RELEASE BLOCKER; provider approval/provisioning must be settled before distribution. No secret is baked into an AppImage. |
| 5. Xemu language not taken from edited EEPROM | Owner corrected the initial report: no rejection. Normal profile EEPROM has language 3 (German), Embercade's preserved isolated EEPROM has 1 (English); both are 256 bytes with valid factory/user checksums. | Explain the independent EEPROM and preservation in wizard/help. Read-only format/editor evaluation; no state replacement. | Existing native first-start/version and preservation tests; read-only language/checksum comparison. | Change language in the dashboard using the actual Embercade EEPROM; verify German game behavior and persistence. | Local offline language/region editor evaluated for 1.1, not implemented. |
| 6. shadPS4 false missing runtime warning | Doctor unconditionally required `libfuse.so.2`. Actual provider uses a static outer runtime and owner already confirmed Bloodborne through character creation and return. | Inspect the actual outer ELF dependencies; keep embedded payload inspection and systemd/FUSE cleanup requirements. Accept fusermount3 or fusermount like the runner. | Static runtime without FUSE2, genuinely missing dynamic dependency and helper fallback tests; actual installed outer runtime reports no missing dependencies. | Doctor and same Bloodborne launch/exit on new build; second-host gameplay remains unproven. | shadPS4 graphics defects remain provider issues. Dependency availability is not gameplay evidence. |
| 7/10. Terminal remains after successful host installation | Unconditional terminal `--hold`; GUI discarded the process and never received bootstrap's result. A terminal server/launcher exit cannot establish pacman success. Declining an install also returned zero. | Independent Konsole `--separate --nofork`; private per-invocation result from actual CLI child. Wait for pacman/AUR exit including hooks. Close only success; failure waits for Enter with output retained. Decline/interrupt is cancellation; missing result never means success. Refresh host status and restore retry controls. | Child/hook completion barrier; real PTY failure retention; cancellation/spawn failure/symlink guards; all-outcome GUI refresh; real separate Konsole success closes. | Actual approved package transaction, hooks, failure/retry, Ctrl+C and terminal-close cases on KDE and interactive Gamescope. | Implemented for 1.0 by task 10. No foreign terminal/window is killed or changed. |
| 8. Existing behavior | Existing controller/exit, shader, theme, state, Steam and reinstall implementations remain authoritative. Xenia path was corrected by owner, not a proven software bug. | Keep generators/resolvers and user state; run regression coverage and packaging checks. | Complete suite, runtime/frontend/shader smokes, structural routes and extracted-image audit. | Controllers/hotkeys, shader selection/persistence, successful scrape, theme changes, saves/states, exit/return, Steam, normal reinstall on both hosts. | No automated result is reported as fresh interactive acceptance. |
| 9. English/German setup | Installer strings were German literals; no stored preference or language page. | Initial language choice before Welcome, system default overridable, central catalog, atomic `[installer].language`, later Language setting without reset; translated buttons/dialogs/help/progress/status/errors and own terminal messages. Structured checks reuse existing backends. | Complete isolated GTK/CLI flow in English and German, saved preference/reopen, existing config preservation, catalog placeholders/coverage, modal controller checks and invalid-state guards. | Full visible English Reddit flow plus full German flow on both target hosts, including real optional installation and first frontend/game start. | External pacman/native-tool output stays native. Installer language does not change the independent frontend or Xbox console language. |

## Technical evidence and boundaries

### Display and KDE decorations

KScreen output `size` may be logical/scaled; the selected mode's pixel size is
used for Batocera/RetroArch configuration. KWin `activeOutputName` resolves
multiple enabled outputs; priority is the fallback when unavailable. Gamescope
precedes inherited KDE/Hyprland desktop variables and uses its logical game
output, not the physical DRM size used by its separate external-overlay plane.
Invalid query data is an explicit error instead of silently generating a wrong
1080p viewport. No compositor mode, viewport override or shader preset is saved.

The KWin observer uses the [public scripting API](https://develop.kde.org/docs/plasma/kwin/api/)
and the individually registered script object (see
[KWin implementation](https://invent.kde.org/plasma/kwin/-/blob/v6.7.5/src/scripting/scripting.cpp)).
A memfd supplies its source, so no persistent plugin/configuration is installed.
Only active PID/minimized/fullscreen/frame geometry is sent to the helper's
private D-Bus connection. No caption, key or application data is collected.
The sender must be KWin. A NameHasOwner watchdog unloads only this uniquely named
script if the helper dies. Missing GtkLayerShell/KWin fails safely with the
emulator unchanged. Existing `Decoration=None`, ratio safeguards, clipping,
transparent input and Gamescope plane occupancy checks remain in force.

### Firmware

The new `installer firmware` action uses existing RPCS3 discovery, preparation
and isolated native-UI backend. It never downloads firmware, automatically
upgrades existing firmware, imports normal saves or interprets a PUP file as
installed firmware. Choosing the GUI action is explicit authorization to open
RPCS3/install a user-selected PUP; the subsequent native steps remain interactive.

### ScreenScraper build comparison

Exact pinned Batocera `.mk`:
[batocera-emulationstation.mk](https://github.com/batocera-linux/batocera.linux/blob/9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48/package/batocera/emulationstation/batocera-emulationstation/batocera-emulationstation.mk),
SHA-256 `c9ec02d6b26973a802ab91097ced12efeb2a820d3185206492f211ba29326b5d`.
It passes its ScreenScraper developer-login build setting to CMake. Pinned
[CMakeLists.txt](https://github.com/batocera-linux/batocera-emulationstation/blob/1750dded8c0fdff70630026f756a69fcad0bb995/CMakeLists.txt)
turns that setting into a compile definition, consumed by
[ScreenScraper.cpp](https://github.com/batocera-linux/batocera-emulationstation/blob/1750dded8c0fdff70630026f756a69fcad0bb995/es-app/src/scrapers/ScreenScraper.cpp).
This is not authorization to reuse another project's credentials.

Embercade patch `0002-embercade-screenscraper.patch` enables the scraper via
`EMBERCADE_SCREENSCRAPER_RUNTIME`, sets software name Embercade, and reads an
owner-only runtime developer file. Personal credentials use a different private
file and the existing account menu. Build input/payload/argv/environment/logs
must not contain credential values. The audit inspected only secret status,
not contents or live authentication. No access credentials appear in this report.
Approved developer provisioning remains unresolved; see [SCREENSCRAPER.md](SCREENSCRAPER.md).

### EEPROM evaluation

Reference [offline-capable editor](https://eeprom.xboxarchive.org/) and
[editor source](https://github.com/Ryzee119/xbox_eeprom_online).
At the actual tested Xemu revision
[478b4f496102379c7eaa7f3ec10e714a703c4300](https://github.com/xemu-project/xemu/blob/478b4f496102379c7eaa7f3ec10e714a703c4300/hw/xbox/eeprom_generation.c),
the EEPROM is a 256-byte structure. Language is a little-endian word at 0x90
(English 1, German 3); video settings are in the factory section, while game
region and HDD key belong to the authenticated/encrypted security section.
Factory/user sections have separate complemented word-sum checksums; the
security section requires the matching version's HMAC/RC4 handling.

A local editor is technically feasible. A language-only change need not replace
the encrypted section, identity, HDD key or entire EEPROM; recompute only the
user checksum. A future implementation needs explicit preview/confirmation,
backup, exact validation, stopped-Xemu ownership and atomic replacement.
Region/video changes are independent of language and need separate handling.
Do not silently infer PAL or Europe from installer language. Xemu's
[FAQ](https://xemu.app/docs/faq/) notes that saves can depend on the HDD key;
emulation does not make every existing key irrelevant. This audit implements
no editor and changes no EEPROM bytes. The immediate issue is the active file
path, not a reproduced format rejection. See [GARUDA_BLANK_INSTALL.md](GARUDA_BLANK_INSTALL.md).

## Installer lifecycle

- Opening settings is read-only. No saved language means the language page is
  offered once, including existing installations. Unsupported locale defaults
  to English; `LC_ALL`, then `LC_MESSAGES`, then `LANG` controls the initial
  choice. Explicit saved German/English wins on restart.
- Language save changes only its TOML table/key through the existing atomic
  writer. Invalid TOML, incompatible table, symlink and application-local write
  targets are refused. Pending path fields and existing setup survive later
  language changes. Emulator/frontend settings are untouched.
- GUI `installer status` exposes structured availability/status, never credentials
  or raw English Doctor messages. Setup/import errors get localized actionable
  summaries; CLI remains available for detailed technical diagnosis.
- Each terminal owns a private 0700 result directory and 0600 result file.
  Bootstrap uses its existing package plan and confirmations; no shell command
  strings, repository enabling, unattended emulator installation or package
  download shortcut was introduced. German prompts accept j/ja and y/yes.
- The worker waits for the real bootstrap subprocess. Pacman/AUR adapters are
  synchronous, so post-transaction hooks finish before zero is published.
  Failed output stays in that terminal until Enter; retry can begin in the GUI
  after fresh assessment. Cancellation/missing result never produces success.
  Closing the GUI while an action is running is blocked; cancel in the terminal.
  No timer closes a terminal and no process-name/global-window action is used.

## Validation

Final source validation on 2026-10-10:

- **622 tests discovered: 611 pass, 11 opt-in checks skipped in the default run.**
  The 11 pass separately: eight real GTK checks (including complete English and
  German flows, modal input and bounded long-status dialogs), two actual KWin
  checks and one native Xemu probe. GTK passes in both Broadway and KDE Wayland.
- **52/52 pinned structural routes verified** using the owner's existing core
  backup read-only; the structure source digest matches staging inputs.
- `runtime-smoke`, `frontend-libs-smoke`, `shaders-smoke` and `git diff --check`
  pass. Existing controller, shader, theme, secrets, save/isolation, provider,
  exit, Steam and reinstall regression coverage remains green.
- Production Stage and a pre-commit AppImage pass packaging/extracted-payload
  verification. The actual image passes help, empty-profile Doctor (expected
  exit 1), English preference save, real isolated setup, structured checks and
  German preference change without losing paths/hotkey. Final delivery rebuilds
  from the clean committed source; exact commit/image/Stage hashes are in the
  delivered manifest and build-information sidecar.
- Logs are local under `.work/global-audit`; no credential values are logged.
  These are automatic checks and fixture transactions, not interactive host
  installation/gameplay acceptance.

GTK flows
use empty, private XDG roots and real setup/status CLI actions. Host transactions
are fake child processes, including a real PTY failure and separate Konsole
success; these tests never install emulator packages. The owned KWin fixture is
a GTK window, not a game/emulator fed synthetic content. Native Xemu evidence
uses only its supported version probe with an isolated config; it never boots
ROM/BIOS fixtures.

## Manual acceptance: OPEN on MainRig and Wohnzimmer-PC

Run both English and German sequences visibly, with a new isolated test profile
or a properly backed-up existing profile. Do not delete normal state to simulate
first run. Retain real legally supplied ROM/BIOS inputs read-only.

1. Language selection → Welcome → ROM/BIOS choice → controller → optional
   cores/providers/assets → optional host installation → checks → Finish → first
   frontend start. Repeat in the other language; restart and change language
   later without resetting any configured paths/imports/hotkey.
2. Approve an actual necessary package transaction, observe all hooks, terminal
   auto-close, success and refreshed status. Exercise decline/Ctrl+C, failure
   with output retained, terminal close before result, and retry. Repeat from
   the actual Steam/Gamescope session; automated/SSH checks do not accept it.
3. GB/SFC: centered correct-size image/bezel, shader selection/persistence,
   integer and aspect settings. Xemu/GameCube/Wii: existing 4:3 options,
   decorations, focus/workspace/windowed transitions, controller/hotkey exit
   and same frontend return. Quit leaves no helper/script/process behind.
4. RPCS3: isolated firmware 4.90 recognition/import or native PUP install,
   successful real game start and exit. Xemu: actual isolated EEPROM language
   change and persistence without replacing unrelated saved state. shadPS4:
   Doctor and Bloodborne launch/exit; graphics glitches are separately tracked.
5. ScreenScraper after approved developer provision: personal login retained,
   successful scrape into allowed original-system media/gamelist paths. Theme
   install/switch/persistence, saves/states, Steam and reinstall preserve data.

## Update and recovery

Keep the prior image and close Embercade/emulators before replacing its durable
AppImage filename. Existing XDG state and both scraper secret files remain
external and are preserved. Normal updates never purge them. The new optional
`installer.language` table is harmless to earlier code. Returning to `5518c51`
restores the older German-only/hold-terminal behavior and lacks KDE fixes.
Do not roll back emulator firmware/saves as part of an application rollback.
Back up stopped isolated emulator state before any manual EEPROM/firmware
maintenance; do not overwrite a normal profile or replace an EEPROM to address
an unrelated launch error. Public distribution remains blocked independently
of successful private packaging and these automated checks.

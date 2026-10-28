# Embercade 1.0: Garuda blank-install fixes

This records the initial `5518c51` fix. Its unconditional terminal-hold behavior
is superseded by task 10 in [GLOBAL_GARUDA_AUDIT.md](GLOBAL_GARUDA_AUDIT.md);
use that report for current bilingual setup and terminal acceptance.

Status on 2026-10-10: implementation and automated checks complete; new
Garuda MainRig and WohnzimmerPC interactive acceptance remains OPEN.
No host emulator was installed by this sprint. The owner explicitly approved
and installed the missing build-host `pugixml` library after the first Stage
attempt rejected it; package bootstrap itself has only been run in dry-run.

## Root causes established before edits

### Xemu

`xemu_source_environment()` required four source files, including `eeprom.bin`.
`prepare_xemu_files()` also required an EEPROM seed, `read_state()` counted its
absence as an incomplete Xemu setup, and `create_launch_plan()` rejected the
missing isolated EEPROM before Xemu could start. The GTK asset-page prose and
Production documentation repeated the incorrect requirement. The pinned
Batocera BIOS checker itself correctly lists only flash/MCPX as BIOS files.

Embercade integrates the resolved external native Xemu executable; it does
not pin, download or bundle Xemu. The examined Garuda package was
`xemu-git 0.8.136.r53.g478b4f4-1`, reporting
`0.8.136-53-g478b4f4961`, commit
`478b4f496102379c7eaa7f3ec10e714a703c4300`.
At that exact revision, [`system/vl.c`, `get_eeprom_path()`](https://github.com/xemu-project/xemu/blob/478b4f496102379c7eaa7f3ec10e714a703c4300/system/vl.c#L2909)
uses the configured EEPROM path and invokes `xbox_eeprom_generate()` only if
that file is absent. An empty configuration value selects Xemu's default path;
Embercade instead keeps its existing explicit isolated save path.
The [upstream EEPROM documentation](https://xemu.app/docs/eeprom/) also describes
native generation when no user image is supplied.

An isolated native `xemu -config_path CONFIG --version` probe exercised that
initializer without booting a game or synthetic ROM: Xemu produced 256 bytes
at the configured save path, and the next invocation preserved bytes and mtime.
This proves initialization for the examined build, not Xbox gameplay or all
past/future Xemu versions.

### Garuda / package sources

`SUPPORTED_DISTRO_IDS` explicitly contained only `arch` and `cachyos`, so the
correctly parsed `ID=garuda`, `ID_LIKE=arch` was rejected. The plan returned no
packages and immediately ended. Identity manipulation is unnecessary.

There was a second planning gap: known development variants were only queried
through `paru`/`yay`, even when already available in configured pacman sources.
Read-only queries on this host found:

| Component | Available package/source |
|---|---|
| RetroArch | `extra/retroarch` |
| Dolphin | `extra/dolphin-emu` |
| PCSX2 | `chaotic-aur/pcsx2-git`; `pcsx2` absent |
| RPCS3 | `chaotic-aur/rpcs3-git`; `rpcs3` absent |
| Xemu | `chaotic-aur/xemu-git`; `xemu` absent |

This is evidence about this host's sync database, not a promise about every
Garuda installation or future versions. Each plan probes its target anew.

### GTK and terminal lifetime: observed limits

The original `Gtk.MessageDialog` was held by a local reference throughout
`run()` and had the correct transient parent. Timed pre-change checks in a
GTK Broadway test display and native KDE/Wayland found it visible and modal
after 500–600 ms; it returned only after the injected No response. The
positional-constructor deprecation warnings occurred while it stayed open.
They do not explain the reported flash. The user's observation that something
flashes immediately after clicking Install could not be reproduced in these
signal-driven checks. Its exact spontaneous-dismissal cause remains OPEN.

Two concrete lifecycle defects were established independently: terminal
commands had no hold option, so the unsupported-distro command's immediate
return removed its output; and SDL polling continued during `Dialog.run()`
while routing input to the parent wizard. A native modal grab does not stop
that programmatic SDL path. Neither finding is claimed as proof of the exact
mouse-click disappearance reported by the user.

## Changes

- Firmware and HDD remain required sources. EEPROM absence is accepted by
  setup validation, preparation, wizard readiness and launch. Preparation
  creates its isolated parent directory but never fabricates EEPROM bytes.
- The existing generator still writes the explicit Embercade
  `saves/xbox/xemu_eeprom.bin` path into `xemu.toml`; native Xemu owns creation.
  Existing writable EEPROM/HDD are reused without replacement. A selected
  legacy EEPROM seed is optional, and a missing explicitly configured backup
  seed fails clearly rather than silently creating a different identity.
  Existing symlink destinations are preserved and rejected to protect isolation.
- Production/development host-source mounts no longer depend on an EEPROM.
  Doctor and the wizard describe first-start creation instead of missing BIOS.
- Exact `garuda` support joins `arch`/`cachyos`. Stable package candidates are
  probed first, then the existing exact development candidate through pacman,
  then optional existing AUR helpers. No repository/helper is installed or
  enabled. Repository development choices are labelled in the plan.
- GUI approval only opens a terminal. Package installation still needs the
  CLI's default-No confirmation and pacman's own transaction confirmation.
  Ctrl-C/EOF returns 130 clearly; a failed repository install stops further
  community installation and prints a retry/Doctor hint.
- Message dialogs use keyword properties, explicit transient/modal/parent
  lifetime, a retained active-dialog reference and dialog-scoped SDL input.
  No is the confirmation default; close/B cancel without leaving the wizard
  page. GTK constructor warnings are fixed, not suppressed. Unrelated
  PyGObject asyncio-policy deprecations remain upstream warnings.
- Konsole/kitty/foot/xterm retain terminal output with their hold option.
  Terminal startup errors return to the usable wizard with a message.
- Existing display/compatibility unit tests now mock their executable lookup;
  structural generator tests use never-executed exit-99 emulator sentinels and
  real user-supplied cores. No emulator boots synthetic fixture content.

No external-disk path is tracked as configuration or a code constant. Normal
update/reinstall, immutable AppImage/prefix and external XDG ownership are
unchanged. No normal emulator profile, ROM, BIOS, save or source core is a
mutation target of the fixes.

## Verification and build limits

The final complete suite discovered 595 tests in 124.802 seconds: 589 passed,
six opt-in tests skipped in that run. All five GTK lifecycle/approval tests
passed separately in both Broadway and native Wayland; the native Xemu
initializer/reuse test also passed. Thus all six opt-in checks were exercised.
Runtime, frontend-library and shader smokes passed, as did all 52 pinned
structural routes and `git diff --check`. The actual Garuda dry-run offered
`dolphin-emu`, `pcsx2-git`, `retroarch` and `rpcs3-git`, and printed
`NO CHANGES MADE`; Xemu was already installed on this host.

Initial broad checks exposed obsolete absolute development links/shebangs
after moving the repository and missing old-host test assumptions. The pinned
runtime was recreated inside `.work`, six disposable UI-resource symlinks were
refreshed to relative links, and the owner's existing core backup supplied
read-only structural inputs. No compatibility check was bypassed.

A combined native-GTK/full-suite attempt was deliberately interrupted after
the GUI assertions had passed: a test window remained visible while the
non-GUI suite continued and KWin reported it unresponsive. Test teardown now
drains GTK events and synchronizes window destruction; final native/Broadway
GUI checks run separately from the long suite. That test-harness incident is
not evidence about the original installer confirmation flash.

The initial Stage attempt correctly rejected the unresolved host dependency
**`libpugixml.so.1`**. This is an existing frontend host-library requirement and
Dolphin dependency. After explicit approval, the owner installed `pugixml
1.16-1`; the standard Stage build then passed with manifest SHA-256
`9c93317fda5a5366784a4ba178ca57632a5eb53c0d7ebab352bf0dfdbb03a959`.
No ELF-closure check was bypassed and no emulator was installed for the build.

The new private image is **`dist/Embercade-1.0-Garuda-fixes-x86_64.AppImage`**,
with adjacent `.manifest.json` and `.AppImage.sha256` files. Its distinct name
preserves the previous default image. Standard packaging verified the actual
extracted SquashFS payload, file hashes, library/content boundary and notices.
The manifest records the packaged source revision and final image hash.

The actual AppImage's `--help` returned 0 from an empty external HOME/XDG profile
with development variables removed and only `/usr/bin:/bin` on PATH. Its
`doctor --verbose` returned the expected 1 for that deliberately unconfigured
profile, reported Garuda and first-start EEPROM generation, and raised no
traceback. This proves CLI startup/diagnostics without the development
environment, not completion of the visible wizard or frontend/gameplay E2E.

Ignored operational evidence is under `.work/garuda-blank-install/`:
`full-tests.log`, `gtk-wayland.log`, `gtk-broadway.log`, `xemu-native.log`,
`host-plan.log`, the three smoke logs, `stage-build.log`, `appimage-build.log`,
`image-empty-profile.log`, `image-help.log` and `image-doctor-empty.log`.

Reproduce automated checks from the repository root:

```sh
EMBERCADE_LIBRETRO_USER_CORES="/path/to/existing/cores" \
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  python -B -m unittest discover -s tests -v
EMBERCADE_TEST_GTK=1 GDK_BACKEND=wayland PYTHONPATH=src \
  python -B -m unittest discover -s tests -p 'test_first_run_gtk.py' -v
EMBERCADE_TEST_XEMU_NATIVE=1 PYTHONPATH=src \
  python -B -m unittest discover -s tests -p 'test_xemu_native.py' -v
./scripts/runtime-smoke
./scripts/frontend-libs-smoke
./scripts/shaders-smoke
./scripts/stage-build
./scripts/appimage-build --output dist/Embercade-1.0-Garuda-fixes-x86_64.AppImage
```

## Recovery and rollback

Close Embercade and emulators before switching an image or restoring state.
Keep the previous image under a different filename; replace only the closed
application file at the durable launch location. External Embercade XDG
config/data/state/cache are not part of the image and must be retained.
For classic installs use the normal verified previous payload; never purge.
For source rollback create a normal revert commit, without reset/force-push.

Do not delete an EEPROM to repair a failed launch: its HDD key and identity
may matter to existing saves. Back up the entire matching Xbox save directory,
including EEPROM and HDD together, while stopped. Restore that matching pair
only after the user deliberately chooses recovery; never replace it with a
new generated file as a workaround. Firmware sources stay read-only.
Old pre-fix builds still require an existing EEPROM; rollback is suitable for
an already initialized profile, not for accepting a fresh EEPROM-free setup.

If pacman fails, leave its error output visible, close the terminal and re-run
Doctor/plan. Pacman may have completed an earlier transaction step; inspect its
own output/log before retrying. Do not automatically remove packages, edit
repositories, change the OS ID or reset configuration.

## Next manual Garuda blank-install acceptance

1. Use the new `dist/Embercade-1.0-Garuda-fixes-x86_64.AppImage` and its adjacent
   checksum/manifest; preserve the previous image. On another build host,
   satisfy the documented host-library contract through an explicit package
   decision, then use the unchanged Stage/AppImage tools above.
2. Use a separate empty test account or explicit empty XDG test roots; do not
   delete the existing production profile to manufacture a blank install.
   Supply real flash/MCPX/HDD sources, deliberately no EEPROM and no normal
   Xemu profile. Record Xemu version, image SHA-256 and package sources.
3. Start the image from the visible MainRig KDE/Wayland desktop. Complete the
   wizard; confirm Xbox setup advances without EEPROM, and reopening shows
   it prepared. Before a real Xbox start there should be no fabricated EEPROM.
4. Click optional host installation. Observe a persistent confirmation. Test
   No, close and controller B first: no installation/page change. Then choose
   Yes, review the held terminal's plan, test default-No/Ctrl-C, reopen and
   explicitly confirm the intended transaction. Read any unavailable-package
   error; the wizard must remain usable. Re-run the host check afterwards.
5. Launch a real user-owned Xbox game from the same frontend. Confirm native
   isolated EEPROM creation, image/audio/controller, configured exit/return
   and normal Quit. Relaunch and verify EEPROM reuse. Do not boot test fixtures.
6. Back up the stopped test profile; replace the image or perform a normal
   classic reinstall, verify EEPROM/HDD hashes before another launch, then
   repeat gameplay. Compare external content and normal host-profile hashes.
7. Repeat the existing representative Libretro/standalone, controller exit,
   frontend return and Quit regression on MainRig and the WohnzimmerPC's real
   interactive Steam/Gamescope session. No SSH-only or signal-driven run
   counts as visible acceptance. Both host results remain OPEN for this revision.
8. If the confirmation still flashes before any answer, retain terminal stderr
   and record whether a GTK response, unmap, parent destruction or terminal
   startup occurred. Reproduce that event sequence before another code change;
   the current automated lifecycle tests do not settle this observation.

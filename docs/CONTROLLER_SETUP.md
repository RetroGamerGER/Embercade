# Controller & Hotkeys setup

The bilingual installer has a separate Controller & Hotkeys step after Host
software. Existing installations can also open it from Welcome or Complete.
The same `back-start` and `guide-start` presets remain authoritative; saving
changes only `[controller].exit_hotkey`, through the existing atomic writer.
No emulator profile, ROM, firmware or controller mapping is reset.

## Observed problem and recovery

On Garuda/Garuda KDE, the owner's GuliKit NS39 used Bluetooth through xpadneo
0.10.4. The selected Guide + Start preset, SDL mapping and RetroArch hotkey
numbers were consistent, but xpadneo's enabled Guide shift mode withheld the
normal held Guide signal. Guide + Select also toggled the driver's mouse mode.
See the [upstream mouse-mode documentation](https://github.com/atar-axis/xpadneo#mouse-profile-support)
and the installed/upstream `xpadneo/events.c` and `xpadneo/mouse.c` sources.

The owner confirmed that disabling shift mode restored Game Boy exit to the
same frontend. A subsequent physical-mouse failure exposed a second issue:
the controller's synthetic mouse still reported BTN_EXTRA and BTN_FORWARD
pressed, while both physical mouse devices reported no held buttons. Leaving
mouse mode had not emitted releases. Disconnecting only this controller
removed that synthetic device, restored desktop clicks (owner-confirmed), and
reconnecting created fresh devices with no held keys. That manual adjustment
predates the new installer workflow; it is not acceptance of the new helper.

## Explicit and reversible host adjustment

Detection reads the actual xpadneo kernel bindings and current module parameter.
Controller names are display text, never model-specific rules. Merely opening
the page, selecting Guide, refreshing or testing input makes no system change.

An adjustment requires the installer's explanatory confirmation followed by
the desktop's administrator authentication. The confirmation identifies the
system-wide effect on all xpadneo controllers: Guide-based mouse/profile
switching is disabled. The dedicated helper accepts only `enable` or `undo`,
uses fixed paths and absolute host tools, and runs with isolated Python and a
restricted environment. For AppImage/FUSE compatibility, only the standalone
helper is copied byte-for-byte into a private 0700 directory under `/tmp`, with
0600 file permissions, for the lifetime of that authenticated call. The copy is
removed on completion or failure. No mount permissions are relaxed: root cannot
normally read an unprivileged FUSE mount (see the
[Linux FUSE access rules](https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse.html)).
It installs neither packages nor drivers.

1. Inspect all bound xpadneo Bluetooth controllers, verify their existing
   pairing and refuse ambiguous or unsupported identities.
2. Disconnect affected controllers and verify removal of their old HID/input
   nodes before touching the global parameter. This releases synthetic mouse
   state. No unrelated Bluetooth device, physical mouse or emulator is stopped.
3. Record the previous setting in a root-owned receipt and write only the
   dedicated `/etc/modprobe.d/90-embercade-controller-compat.conf`; apply the
   live setting while the affected devices are absent.
4. Reconnect only those controllers. Re-enumerate their fresh input devices and
   inspect synthetic mouse button state. Incomplete recovery is reported as
   pending, with instructions to power-cycle the controller and retest.

The receipt is `/var/lib/embercade/controller-compat/xpadneo.json`. Undo checks
exact file contents and ownership, follows the same disconnect-before-change
sequence, restores the prior live setting, and removes only its own files.
Foreign settings, including the earlier manual Garuda adjustment, are neither
adopted nor silently overwritten. A partially completed transaction retains an
ownership record for recovery. Authentication cancellation and reconnect
failure never become an unqualified success message.

Missing authentication/Bluetooth tools, unsupported drivers, conflicting host
configuration or declined consent leave Back/Select + Start available. No
global input daemon, mapping table, udev rule or permissive device access is
added. Normal emulator exit routing and Player-1 ownership remain unchanged.

## Live test and scope

The modal test identifies the controller opened by the existing wizard SDL
reader. It requires an initial release, at least 350 ms of simultaneous held
modifier + Start, then final release. A brief delayed Guide pulse cannot pass.
Disconnects or handle changes reset progress. Cancel, timeout and completion
consume pending controller input until release, so Start cannot activate a
wizard button underneath the dialog. Test success is limited to this session
and connection; changing the preset or reconnecting invalidates it.

The test observes input only; it never emits mouse/keyboard events or starts
or exits a game. The user can explicitly continue without a live test. Real
Player-1 game exit, frontend return and desktop mouse operation still require
interactive acceptance. Existing ES player preferences remain the authority
for game launches, including multi-controller setups.

## Validation record

The full source regression discovered 757 tests: 752 passed, including 24
opt-in GTK checks, and five unrelated native emulator/layer-shell checks were
skipped. Runtime, frontend-library and shader smoke checks passed; all 52
structural routes passed with read-only backup cores. All 88 focused tests also
passed against the verified AppImage payload,
including the 24 GTK checks. A real FUSE-mounted AppImage provided the helper
bytes for the private temporary-copy test, unprivileged invalid-operation check
and mocked authentication cancellation/cleanup; no admin command was executed.
The actual AppImage preference CLI was checked in an isolated profile. Build
identity and verified local/menu-copy replacement are in `PROJECT_STATE.md`.

An isolated KDE Plasma/Wayland preview visually passed in English and German:
all ten sidebar steps, conflict/ready pages and the complete administrator
confirmation are readable without clipping. This used synthetic controller
status, no driver calls and no saved user configuration. Evidence is under
`.work/controller-kde-visual-49b4qer_/`; source regression logs are under
`.work/controller-setup-xtv3fteh/`. Automated helper tests use synthetic
filesystems and Bluetooth responses; they never alter the actual host driver.

Owner-confirmed interactive acceptance on Garuda (10 October 2026): the new
AppImage was opened with the existing setup, Start + Guide passed its installer
live test, and the physical mouse continued to work normally. The host already
had the earlier manual driver adjustment. This confirms the actual installer
input test and mouse usability for that configuration; it does not imply that
the new privileged helper was applied or undone, or that another game-exit test
was performed during this session.

Fresh install/undo with real administrator authentication, interrupted Bluetooth
reconnection, multiple xpadneo pads and live Gamescope/Hyprland interaction
remain separate manual acceptance cases. Existing manual Garuda success must
not be presented as those additional tests.

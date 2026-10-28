# RetroArch startup on KDE with network media

## Cause and reproduction (25 October 2026)

The owner reported slow Game Boy, SNES and N64 starts on the Garuda KDE/Wayland
laptop while the same ROM share works quickly on CachyOS Handheld. Cores on the
laptop are managed local files on Btrfs; ROMs are on CIFS. The ROM share alone
does not explain the difference.

The original launch logs initialize the core, graphics and audio quickly, but
have no first-frame marker. Their later silent intervals were not counted as
measured startup latency. During a fresh owner-triggered reproduction, the
RetroArch main thread repeatedly waited in `wait_for_response`; the running
kernel identifies that symbol as belonging to CIFS. Qt's Wayland and KDE
platform-theme plugins were loaded.

An isolated comparison reproduced the delay with the same ROM, local Gambatte
core, host RetroArch 1.22.2 and KDE session. Existing library metadata/media
targets were bound **read-only**, using the production topology: 920 narrow
bind mounts across both aliases. No metadata directory or game file was created
or changed on the share.

| Generated companion settings | RetroArch initialization to first EGL buffer swap |
| --- | ---: |
| Existing Qt desktop autostart enabled | 43.135 seconds |
| Desktop companion disabled | 0.622 seconds |

These values exclude the test namespace setup and its deliberate cache-expiry
wait. They measure the first buffer swap, not a manually timed complete frontend
selection sequence. Both test runs exited normally and preserved the normal
configuration hashes.

Call stacks locate repeated `statx` requests in KDE's
`KMountPoint::currentMountPoints`, called through `KFileItem::iconName`, the
KDE platform theme and Qt's `QFileSystemModel` while constructing RetroArch's
additional desktop browser. The many scoped scraper mounts multiply those
network metadata requests before the first game frame. A preliminary comparison
that omitted the media mounts started quickly in both cases; it was insufficient
to reproduce the production topology. A stale saved network path is not needed
to reproduce this fault in a fresh profile.

## Change

Patch `0030-embercade-libretro-no-desktop-companion.patch` refreshes
`desktop_menu_enable`, `ui_companion_start_on_boot` and `ui_companion_toggle` to
false when `EMBERCADE_DESKTOP=1`. Existing generated configurations receive the
same defaults on their next ordinary game launch. The in-game RetroArch menu
driver and input bindings are retained. Batocera's explicit `retroarch.*`
overrides remain authoritative, including an intentional opt-in to the companion.

No host network mount, scraper permission, controller driver or system package is
changed. The fix does not remove saved configuration or user data and does not
modify CachyOS Handheld. Disabling the companion manually in the owner profile was
not required for diagnosis; comparisons used separate temporary XDG profiles.

## Validation and handoff

The targeted runtime suite passes 17 tests, including a real pinned configgen
dry run that replaces old enabled companion settings, preserves the in-game
menu and saves, and honors explicit per-system overrides. The full isolated
suite passes 768 of 773 tests, with five expected native opt-in skips, including
25 real GTK checks and all 52 structural system routes. Runtime smoke and
`git diff --check` pass.

Private evidence is under `.work/retroarch-startup-2026-10-25/`, including the
read-only owner-process observation, isolated comparison logs/call stacks,
configuration-preservation proofs and test scripts. It is not a release archive.
No public release or push is authorized.

The clean-source private AppImage was built from
`f1611829eb248a2dd6a72d8048516605bad57446`:
`Embercade-1.0-RetroArchStart-x86_64.AppImage`, SHA-256
`bcc5f45025e0fff3ac468305f099b108653da58427d971052a973adac4149bd2`.
The actual extracted runtime contains patch `0030`. Its frontend SHA-256 is
identical to the accepted ScreenScraper candidate, preserving that tested
application authorization and frontend implementation.

The resulting image was copied, at the owner's request, to the laptop's
`~/AppImages/` alongside its verified checksum and manifest. The development
artifact and sidecars remain in `dist/private-retroarch-start-2026-10-25/`.
The earlier backup-folder copy is still the previous ScreenScraper candidate;
that folder was not updated by this handoff.

Using the copied image and pinned launcher/configgen, with 920 read-only media
binds and no manual companion override, all three startup tests exited zero:

| System and core | Initialization to first EGL swap |
| --- | ---: |
| Game Boy / Gambatte | 0.728 seconds |
| SNES / Snes9x | 0.632 seconds |
| N64 / ParaLLEl N64 | 4.457 seconds |

All three regenerated the companion settings to false in the temporary profile.
These startup probes render five frames; they are not prolonged gameplay or
controller-exit acceptance. Normal owner-configuration hashes remained unchanged
by the probes. The owner then launched the new image with existing settings and
explicitly confirmed the Game Boy delay had disappeared. This is separate real
frontend acceptance, not a conclusion drawn from the isolated frame markers.

All six temporary remote diagnosis profiles/observer directories were removed
by exact recorded path after the logs/proofs were retained locally. No owned
probe processes remained; the delivered image was rehashed after cleanup and
its executable permission, checksum and manifest were verified again. No system
packages, drivers, saved games, original ROM/BIOS files or CachyOS Handheld were
changed by the diagnosis/fix. Documentation and source commits remain local;
no push or public release occurred.

# Embercade 1.0 final polish — 2026-10-10

This is preparation for the owner's interactive acceptance, not a public release.
The actual new-host game/display/Steam acceptance remains OPEN on Garuda
(Garuda KDE/Wayland) and CachyOS Handheld (CachyOS Gamescope). Historical gameplay
proof does not establish acceptance of this revision. The repository is PRIVATE;
the paused decoration licensing investigation is unchanged.

## KDE geometry

A native layer-shell probe on the 2560×1440 output measured 2560×1408 with
exclusive zone 0: Plasma's 32-pixel reserved area was reducing the anchored
surface. This explains the clipped top and side alignment. Exclusive zone −1
asks the existing layer renderer to cover the complete logical output without
reserving desktop space itself. All four anchors and zero margins now share
one configuration function. A native KWin test measures the actual allocation
against the full GDK monitor, not an assumed resolution.

Rendering follows GDK logical coordinates; Cairo/GDK apply buffer scale.
During output reconfiguration, a stale allocation is transparent until it
matches the selected monitor. Monitor positions and fractional logical sizes
are covered by geometry tests. Gamescope's existing separate output handling
is retained. No hardcoded panel offset, mode change or replacement artwork is
introduced. The existing conservative game-protection clipping remains: the
renderer does not stretch a game's chosen aspect ratio or cover its viewport.
Xbox artwork's small inner margins still depend on the actual game viewport.
See [STANDALONE_DECORATIONS.md](STANDALONE_DECORATIONS.md).

## ScreenScraper — production-build repair

The 2026-10-25 owner instruction supersedes the earlier runtime-file-only
provisioning design. Embercade's own application authorization is compiled
from a protected build source; personal login stays only in the frontend.
The binary authorization is extractable. No local developer setup/status is
shown in Installer/Doctor, and a personal account is optional for installation.
The October 10 owner-confirmed success remains historical; the new candidate's
laptop scrape/media/restart check is separate. See
[SCREENSCRAPER_PRODUCTION_FIX.md](SCREENSCRAPER_PRODUCTION_FIX.md).

## Installer and state contracts

The GTK3 assistant has a dark orange/red product design, original Embercade
icon, fixed ten-stage sidebar, progress indicator, scrollable content and
persistent navigation. Detailed game/core/provider/system-file
pages belong to stage 3; Controller & Hotkeys has its own stage after host software. No new logos or third-party placeholder assets were
introduced. English and German use the central catalog; first language choice
precedes setup and later changes retain fields and saved setup.

1. **Language**: locale preselection, explicit override, atomic preference save.
2. **Welcome**: existing configuration is recognized; check or change it.
3. **Games and BIOS**: read-only source selection; existing managed imports
   are retained. Optional PSP/Xbox/shadPS4 sources use existing setup backends.
4. **Host software**: effective pinned Batocera/user routes identify collection
   priorities. Required components appear first; other emulators are optional.
   The existing explicit package confirmation offers its complete optional
   package plan. Stable/development/AUR resolution and real transaction result
   handling remain unchanged. The actual bootstrap child, including Pacman
   hooks, must finish before success; only its own successful terminal closes.
   Failure stays visible until Enter; cancellation is distinct; all outcomes
   refresh checks. `gtk-layer-shell` remains in the desktop Wayland plan. Missing `readelf` is
   offered as `binutils`, because real ABI/closure checks require it.
5. **Controller & Hotkeys**: shared exit preset, read-only xpadneo check, explicit
   administrator-approved adjustment and ownership-checked undo. Affected pads
   disconnect before the global change; fresh input devices are checked after
   reconnect. The live chord test observes held buttons and final release. See
   [CONTROLLER_SETUP.md](CONTROLLER_SETUP.md) for safety and acceptance limits.
6. **Xbox**: native Xemu `--version` can initialize a missing EEPROM at the
   explicit isolated path without booting a game. Import requires a valid
   256-byte EEPROM. Edits validate both checksums and encrypted-region HMAC
   before writing. Language/video edits retain the encrypted security bytes;
   explicit region edits reauthenticate while preserving confounder and HDD
   key. Serial/MAC and all unrelated fields are retained. Full import intentionally copies the selected console identity/key; the
   confirmation states this and the HDD image stays unchanged. Existing state requires
   replacement confirmation; changed bytes get an owner-only unique backup and
   atomic save. A private lock and exact running-Xemu check refuse concurrent
   edits. No HDD image is rewritten, even when importing an EEPROM. The source
   and normal profile are read-only. Native-generated format-1.0 validation is
   tested; other supported format vectors are offline codec tests. Actual
   dashboard/game use of changed settings remains a manual acceptance.
7. **PS3**: select PUP, consent to official download, import existing installed
   firmware, or skip. Download resolves the current link from the authenticated
   [PlayStation support page](https://www.playstation.com/en-us/support/hardware/ps3/system-software/).
   Sony currently publishes an HTTP file link; forcing HTTPS fails hostname
   certificate verification. No TLS bypass is used. The content MD5 from that
   trusted page link is mandatory; size/header structure and local SHA-256 are
   checked. This is not a claim of a signed publisher manifest. RPCS3 validates
   its native package hashes during installation. The actual observed download
   is 206,197,916 bytes, SHA-256
   `158471fd834f8ea8036136b6aab43cd86c7ba73d79ca30e0af3c0fe0001cf365`.
   PUP data is external cache, never payload. Source terms are linked in the
   consent flow; no legal redistribution clearance is inferred. Native install
   uses a disposable isolated profile, then activates only complete firmware
   trees. A failed/cancelled attempt is removed, permitting retry. Existing
   firmware/profile/saves are never overwritten. The readiness check inspects
   actual isolated firmware, separately from an importable host source.
8. **Desktop**: Games menu on by default; optional desktop shortcut and Steam
   artwork. AppImage can copy itself to the stable external XDG location
   `$XDG_DATA_HOME/embercade/application/Embercade.AppImage`. Menu and Steam use
   that durable launcher. Standard desktop quoting, original icon, manifest
   hashes, idempotence, lock and rollback protect existing entries. A verified
   classic install keeps its existing launcher/manifest; the wizard does not
   upgrade a running classic install. Modified or unmanaged conflicting files
   are preserved and reported. Unchecking an option does not delete an existing
   entry. Desktop directory follows XDG configuration, including translated
   names; it is not guessed. Steam must be closed and retargeting the same
   shortcut requires confirmation. No development SSD path is hardcoded.
9. **Checks**: Ready / Optional / Setup required / Error have consistent symbols.
   Effective routes, actual core ABI/dependencies, pinned BIOS metadata, PSP
   assets, provider status, isolated EEPROM/firmware and installed frontend/
   launcher closure are checked. Missing optional emulators do not produce a
   false required failure. Scraper account/developer status is outside installer checks.
   “Ready” here describes setup availability, not a new gameplay compatibility
   claim. Per-game BIOS and interactive acceptance remain visible follow-ups.
10. **Complete**: component overview, remaining setup, revisit Xbox/PS3/Desktop,
   start, change settings, finish and later language change.

## Verification and remaining acceptance

Current validation: **646 discovered tests**, 633 default checks passing and
13 opt-ins passing separately (8 GTK, 3 native KWin, 2 native Xemu). All **52
structural routes** pass using the owner's existing cores read-only. Runtime,
frontend-library and shader smokes pass. Both full English/German GUI flows
preserve config and source directories. The final AppImage source revision,
SHA-256 and Stage identity are recorded in the delivery sidecars/report. Test logs are under
`.work/final-polish/` and are not distribution contents. GUI automation uses
private empty XDG state; package-manager success is a fake transaction fixture,
never a host installation. PS3 rollback tests mock the native boundary; the
real official download and native CLI option are separately verified. Native
Xemu probes create only disposable state using `--version`. Geometry tests do
not boot synthetic ROMs or establish visible game acceptance.

Deployment on 10 October 2026 puts **the same clean-source `bd3d2cb` build** on
both reference hosts. Image SHA-256:
`1361a9dccb33e8ec499b7d3e328bdfa27c96237763c3c93b3646e8ef623ca8f8`.
Stage manifest SHA-256:
`c9b3933751dfcf3793e4fbf117fbf7135a5aac09377b7c0ecf3b9c2c4f4a209a`.
Subsequent deployment-documentation commits do not change this build identity.

- Garuda: managed local AppImage plus Games-menu entry created through the
  existing desktop backend; installed Doctor exits 0. All 7,115 prior inventoried
  entries are unchanged; only four expected integration entries are added within
  Embercade XDG roots (local application directory/image, lock and manifest).
- CachyOS Handheld: actual SSH deployment updates both the existing Steam-target
  AppImage and classic Production. The new payload installer verifies the old
  installation before replacement; repeat dry-run reports ALREADY UP TO DATE.
  Installed Stage/image hashes match the delivery. Both actual launchers pass
  help and Doctor with exit 0. The old image and sidecars remain as rollback
  copies. Steam stays running; its existing shortcut is not rewritten, its appid
  remains `4059814080`, and shortcut/artwork bytes are unchanged.
- State comparison covers Embercade XDG roots, present RetroArch/Dolphin/PCSX2/
  RPCS3/Xemu config/data roots and Steam shortcuts/artwork. Remote: 201,168 entries with no additions,
  removals or changes; 183,418 readable files content-hashed. Garuda: 6,148
  prior readable files content-hashed. Files larger than 16 MiB and one unreadable
  remote RPCS3 cache log have metadata-only comparison. The classic install
  manifest is intentionally excluded. No permission changes or host package
  installations were made. ROM/BIOS sources were not written or re-imported.

OPEN on **both** hosts, using the exact same delivered image/revision:

- Full English flow, then independent German flow; restart and change language.
- Controller/mouse/keyboard navigation, scrolling and scaling; no hidden footer.
- Real host transaction and post-hooks: success closes its own terminal; failure
  retains output; cancel never reports success; retry refreshes actual status.
- GameCube/Wii/Xemu artwork at 2560×1440, 1920×1080 and 1280×800; scaled/multiple
  outputs where available. No clipped top, uncovered sides, distorted artwork,
  covered game or surviving overlay after exit. Hyprland/Gamescope regression.
- Native EEPROM initialization/import/edit; dashboard language/region/video,
  existing key/identity/HDD preservation, game launch/exit and reload persistence.
- Real RPCS3 PUP installation, existing-source import, cancellation/retry and
  isolated firmware status, then game launch/exit. Host profile unchanged.
- Menu/desktop launch after disconnecting the original image drive; same Steam
  shortcut/artwork after restart; no duplicate entry, no host-profile writes.
- ScreenScraper operation is user-confirmed on Garuda. For the detailed demo
  checklist, record one game's metadata, selected cover/screenshot/video when
  available, frontend display and restart persistence; current-build second-host
  confirmation remains open. The new build-provided authorization must be checked
  with a personal-account scrape in the candidate image. No bulk scrape.

## Clean-install and Reddit checklist

Use a fresh OS account or separate empty HOME/XDG roots; **do not delete or
reset your everyday Embercade profile**. Preserve the desktop session runtime
variables. Put the delivered executable AppImage at a durable local path and
compare its SHA-256 with its sidecar on both machines. Run it without arguments;
language must appear before Welcome. Use legally supplied collection/BIOS
sources and follow the nine stages. Missing optional components may be skipped
and must remain explicitly optional/incomplete. Keep a visible before/after
record of selected EEPROM settings and firmware isolation, with private keys
and credentials hidden. Restart from the Games entry, then test one known game
per required route and return to the same frontend. Repeat in the other language
with independent empty state. Film the English path only after these gates pass.
Keep the historical Garuda scraper result separate from the new candidate
image's pending personal-account/media/restart and game/display tests.

## Recovery / rollback

- Keep earlier images. Close Embercade and emulators, then launch the prior
  image or use the existing classic update procedure. No purge is needed.
  Language preference is additive; existing setup fields remain compatible.
- Before restoring an EEPROM, close Xemu and copy the current isolated file
  elsewhere. Select its sibling `xemu_eeprom.bin.backup-*` through Import EEPROM
  and confirm replacement; this creates another backup before restoring bytes.
  Never restore over a running emulator or alter the HDD image to fix language.
- Failed new PS3 native installs use temporary state and leave active firmware
  untouched. If preexisting partial `dev_flash*` trees are detected, stop and
  back up/inspect them rather than deleting them automatically. An existing
  complete version is deliberately preserved; upgrades require separate review.
- Desktop integration's external `desktop-integration.json` records managed
  hashes/launcher. Preserve user-modified files. Select the previous AppImage
  and re-run Desktop integration to retarget its owned stable launcher, or use
  the verified classic entry. Do not hand-edit the classic install manifest.
- Installer/secret/config changes do not touch normal emulator profiles or ROM/
  BIOS source contents. Secret files and downloaded PUPs remain outside images.

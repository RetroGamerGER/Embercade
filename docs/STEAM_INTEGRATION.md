# Optional Steam integration

Interactive first run offers `Add Embercade to Steam? [Y/n]`. It uses the
same implementation as `embercade steam`; it is not a separate installer.
Steam is optional and normal frontend startup never edits Steam metadata.
The private 1.0 AppImage reuses this registrar and the existing branding assets;
it does not introduce a second Steam integration path.
Declining or having no initialized Steam user profile makes no Steam changes.
A failure of this optional setup step does not invalidate Embercade installation.
The explicit command returns status 2 on an unsafe/failed registration.

```sh
embercade steam --dry-run
embercade steam
# Explicit opt-in for a noninteractive invocation:
embercade steam --yes --profile /path/to/Steam/userdata/ACCOUNT/config
```

## Discovery and identity

Discovery checks `$XDG_DATA_HOME/Steam`, `~/.local/share/Steam`,
`~/.steam/steam`, `~/.steam/root` and the conventional Flatpak Steam data root.
Canonical paths deduplicate native aliases. Numeric account directories must
already have a config directory. No account or Steam installation is created.
Multiple candidates require user selection or `--profile`; the most recent
login is not guessed. Flatpak profiles are detected but registration is
deferred: running the host-owned payload from that sandbox needs a separately
validated host-execution bridge. Current integration supports native Steam only.

Classic registration uses the normal installed user-local `embercade` launcher.
When invoked through the mounted Embercade AppImage, registration uses the
user-owned executable image file itself. Files inside temporary mounted or
extracted AppDirs and development harnesses are never Steam executable targets.
A matching launcher/image path identifies
an existing shortcut, including one renamed by the user. Its stored 32-bit
appid is authoritative and is retained, along with tags, play time, launch
options and other metadata. Explicit registration sets the visible `AppName`
to the central `EMBERCADE 1.0` product label, including legacy or renamed owned
entries; it does not derive a new ID from that name. Case variants of field
names are recognized without rewriting foreign nodes. Multiple matches,
duplicate appids, malformed VDF or
an Embercade entry targeting another executable are rejected unless the
explicit `--replace-existing` option selects the classic/AppImage switch.
Legacy `Embercade` and `EMBERCADE 0.5` names remain recognized.

For a new entry only, `CRC32(quoted Exe + "Embercade") | 0x80000000` yields a
deterministic 32-bit ID; collisions with another shortcut or existing artwork
are refused. The legacy `Embercade` identity seed stays separate from the
visible `EMBERCADE 1.0` name. This follows the established offline shortcut
convention, not a
promise of a stable Valve creation API. Existing Steam-assigned IDs are never
rederived. The relevant primary implementation references are
[Steam ROM Manager's ID helpers](https://github.com/SteamGridDB/steam-rom-manager/blob/master/src/lib/helpers/steam/generate-app-id.ts)
and [its shortcut editor](https://github.com/SteamGridDB/steam-rom-manager/blob/master/src/lib/vdf-shortcuts-file.ts).
The binary wire types are cross-checked against
[ValvePython VDF](https://github.com/ValvePython/vdf/blob/master/vdf/__init__.py).
Embercade's small byte-preserving implementation has no dependency on those
packages and does not use a lossy whole-file dictionary reserialization.

With Steam fully stopped, explicitly switch an existing classic shortcut to
the image at its stable file path:

```sh
/path/to/Embercade-1.0-x86_64.AppImage steam --dry-run --replace-existing
/path/to/Embercade-1.0-x86_64.AppImage steam --yes --replace-existing
```

The same option on the classic `embercade steam` command switches back. The
one existing appid, options, tags and artwork identity are retained; no duplicate
entry is created. Extracted AppDirs cannot register transient executable paths.
Start Steam yourself afterwards. See [APPIMAGE.md](APPIMAGE.md) for the image
runtime/update boundary and recorded live acceptance.

## Artwork targets

Under the selected `userdata/ACCOUNT/config/grid`:

| File | Existing installed resource |
| --- | --- |
| `<appid>_icon.png` | `branding/icon/embercade-512.png`; also written to the shortcut icon field |
| `<appid>p.jpg` | `branding/steam/embercade-grid-900x1800.jpg` |
| `<appid>.jpg` | `branding/steam/embercade-hero.jpg`, landscape cover |
| `<appid>_hero.jpg` | Same landscape resource |
| `<appid>_logo.jpg` | Same image with embedded Embercade wordmark |

The logo is a populated Steam logo slot, not a new transparent wordmark or a
claim that one was supplied. All images are existing pinned payload resources;
no graphics are generated, downloaded or taken from an EmulationStation theme.
Old conflicting PNG/JPEG/WebP variants are removed only for the one uniquely
identified existing Embercade appid, after backing them up. Other artwork and
shortcut entries remain byte-identical. Unchanged repeat runs write nothing,
create no new backup and add no duplicate shortcut.

## Safety and recovery

Close Steam fully before registration, including its web helper. Embercade
checks current-user process state before and during activation, never kills
Steam and never modifies metadata while a known Steam process is live. Start
Steam afterwards to reload the shortcut and pictures. Do not start Steam
concurrently with registration: Steam does not share Embercade's advisory lock.

Every target is validated before the first Steam write. Symlinked write targets,
unknown VDF types and non-user-owned target files fail closed. Original bytes
and POSIX permission modes of changed files are backed up under
`$XDG_STATE_HOME/embercade/steam-backups/registration-*`; `restore.json` maps each
original to its full destination and records previously absent files. Activation
uses same-directory temporary files, file fsync and atomic replacement. An
in-process failure rolls back the files already changed. A concurrent foreign
write is not overwritten by rollback; instead the backup location is reported.

This is not a filesystem-wide atomic transaction or a power-loss recovery
service. For manual recovery, stop Steam, review the chosen backup's
`restore.json`, and restore only its listed destinations with recorded modes.
A null original means that destination did not exist before registration.
Do not restore a backup over newer unrelated Steam changes without review.
Successful backups are retained; there is no automatic pruning.

Normal classic Embercade uninstall does not edit Steam profiles or remove shortcuts,
artwork or backups. A retained shortcut points at an absent launcher until
reinstall or manual removal in Steam; normal reinstall can reuse its identity.
An AppImage shortcut instead retains its chosen image path. Replacing a closed
image at that same path preserves the shortcut target; moving it requires an
explicit registration update.
ROMs, BIOS, saves, providers and normal emulator profiles are not registration
targets. Steam integration requires no network or package installation.

## Verification boundary

Tests cover absent Steam, decline, first registration, repeated registration,
existing identity/casing/options, multiple accounts, native/XDG discovery,
exact foreign-byte preservation, artwork mapping/update, malformed files,
collisions, symlink refusal, missing resources/launcher, process checks,
dry run, optional setup failures, CLI confirmation and activation rollback.
Current 1.0 verification: the full repository suite passes 578 tests, and the
runtime, frontend-library, shader and Stage Doctor smokes pass. Tests include
classic/AppImage switching with retained appid, legacy-name migration and
stable image-path registration. MainRig has confirmed the private image's
startup/menu, active external theme, ScreenScraper, Libretro and Xemu 4:3
bezel/exit. The owner has also confirmed the complete requested image E2E in
the WohnzimmerPC's real interactive Steam/Gamescope session. A subsequently
requested cosmetic change removes only the extra splash version line;
menu/footer, information, wizard, window title and Steam name retain
`EMBERCADE 1.0`. MainRig visibly confirmed the caption-free splash, and the
matching WohnzimmerPC update passed Doctor/status 0 and preservation checks
without another visible run at the owner's request. The previously completed
interactive E2E remains distinct from that diagnostic update check.
Packaging reproducibility and the supported-host private functional GO are recorded in
[APPIMAGE.md](APPIMAGE.md).

The following registration/gameplay evidence is historical installed-prefix
acceptance from the 0.5 development milestone. That full suite had 345 passing
tests. Runtime and frontend-library smoke also passed. `pytest` was not
installed on the development host; the complete
repository-defined `unittest` suite is the actual test runner, with no new
dependency installed to rename that result. Production Stage, staged/installed
Doctor, shader smoke and `git diff --check` also passed. A read-only check of the
captured second-host VDF preserved the existing Embercade ID and all eight
foreign entries byte for byte.

Fresh automatic registration was accepted on MainRig and WohnzimmerPC. Both
installed payloads were hash-verified against the same stage built from
`9ebdca3`; the second host uses the normal offline installer and manifest
verification, not a Git checkout. Its normal update preserved persistent
Embercade metadata, config hashes, collection references and normal host
emulator profiles without reading save contents.

With Steam stopped, the second host's installed registrar reused appid
`4059814080`, retained all eight foreign shortcut nodes and unrelated artwork
byte for byte, and populated five slots matching the installed branding files.
The repeat invocation was byte-identical, produced no duplicate and created no
extra backup. The user then launched Embercade from the real native
Steam/Gamescope session and accepted artwork, splash dismissal and the
controller-operable menu. Xemu and its bezel were also accepted there, followed
by Select+Start return to the same frontend process and helper cleanup.
Normal Quit Embercade then returned to Steam, with no frontend process left.
Steam's active performance overlay can occupy the Gamescope bezel plane; see
[STANDALONE_DECORATIONS.md](STANDALONE_DECORATIONS.md). This is separate from
shortcut/artwork registration.

Flatpak execution remains unvalidated. An SSH-triggered Steam launch is never
visual acceptance.

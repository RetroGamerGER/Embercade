# Garuda cleanup for the Reddit demo

On 10 October 2026 the owner reported personal 1.0 acceptance complete and
requested another clean user installation on Garuda/Garuda Mokka KDE. This
operation inventoried the current host, re-read the previous report and checked
current package provenance/dependencies before deletion. The normal shadPS4
profile was separately reconfirmed as test-only. CachyOS Handheld was not accessed.

## Removed files

Eleven explicitly bounded targets, containing 2,360 inventory entries and
2,866,836,703 logical bytes of regular files, were removed:

- `~/.config/embercade/embercade.toml`
- `~/.config/embercade/emulators`
- `~/.config/embercade/batocera.conf`
- `~/.local/share/embercade`
- `~/.local/state/embercade`
- `~/.cache/embercade`
- `~/.local/share/shadPS4`
- `~/.local/share/applications/embercade.desktop`
- `~/.local/share/icons/hicolor/512x512/apps/embercade.png`
- `$XDG_RUNTIME_DIR/embercade`
- The identified temporary Embercade portal-audit script under `/tmp`.

This included 232 managed Libretro cores, the managed shadPS4/Xenia AppImages,
isolated RPCS3 firmware and download cache, Xemu EEPROM, isolated emulator
configuration and saves/test data, and the managed user application image.
References to original BIOS/ROM files were unlinked without following them.
An abandoned read-only Embercade FUSE mount with no active app process was
specifically unmounted; only its then-empty user-owned directory was removed.
Logical sizes do not prove physically reclaimed Btrfs space.

## Removed packages and concurrent OBS installation

The fresh 18-package transaction used explicit `pacman -R`, without recursive,
cascade, dependency-bypass or orphan cleanup:

| Emulator / direct test component | Exclusive test dependency |
| --- | --- |
| `dolphin-emu` | `enet`, `libspng`, `sfml`, `mbedtls3`, `miniupnpc` |
| `pcsx2-git` | `kddockwidgets`, `spdlog`, `plutosvg`, `plutovg`, `rapidyaml` |
| `xemu-git` | `libslirp`, `tomlplusplus` |
| `retroarch`, `rpcs3-git`, `gtk-layer-shell` | — |

Current versions and the complete removal closure were checked immediately
before the transaction. Pacman exited zero after all nine post-transaction
hooks. Its immediate package diff contained exactly those 18 removals.

During final verification the owner independently installed OBS Studio for the
recording, then explicitly confirmed preserving it and its dependencies. That
transaction installed `obs-studio`, `libdatachannel`, `libjuice`,
`qrcodegencpp-cmake`, `rnnoise`, `simde`, `uthash`, and reinstalled `mbedtls3`.
Consequently 17 removed packages are currently absent; `mbedtls3` correctly
remains as an OBS dependency. It was not removed again.

FUSE 2 remains because independently installed AppImagePool actually loads
`libfuse.so.2`, despite missing package dependency metadata. Development
`pugixml`, DOSBox/Boxtron, Python/GTK, Bubblewrap, SDL, Mesa/Vulkan, Gamescope,
KDE/Steam and normal graphics/input drivers remain. Existing unrelated orphans
were only reported by Garuda's hook, never automatically removed.

## Protected data and verified secrets backup

The external development SSD, all repository branches/commits, builds and
working test evidence were preserved. Original ROM/BIOS collections, shared
scraper media/gamelists, installation material, the separate Bloodborne image,
original EEPROM source, Clonezilla/other backups, package caches and system
snapshots remain. Normal package-manager snapshots/hooks were allowed to run.
Other applications and their data, including OBS, were preserved.

`~/.config/embercade` remains solely for the protected `CachyOS Handheld` private
SSH key. Its bytes, metadata and 0600 permissions, other SSH keys and Git
configuration passed comparison. No Steam shortcut files/Embercade integration
were present; Steam data was not changed. No global KDE history/configuration
was erased; only the application menu cache was refreshed after removal.

No current ScreenScraper developer/user credential files were present in the
standard profile. The existing private AES256/GnuPG backup was verified again:
authenticated decryption recovered exactly the expected two regular UTF-8 files
with archive permissions 0600, only in memory. The ciphertext hash matches the
previous source-byte-verified archive. Backup directory remains 0700, archive
0600; no plaintext intermediate or restored profile was created. Recovery needs
the owner's local backup passphrase. No secret values are recorded here.

The backup does not implement the separately documented provider-approved
ordinary-user developer-access provisioning. Credentials are not silently
returned to the new profile for the demonstration.

## xpadneo remains prepared

The earlier owner-approved manual configuration
`/etc/modprobe.d/90-embercade-xpadneo.conf` and live
`/sys/module/hid_xpadneo/parameters/disable_shift_mode=Y` remain byte-for-byte
unchanged. The configuration sets `disable_shift_mode=1`. `xpadneo-dkms` remains
installed; no driver reset, controller disconnection or synthetic-input change
occurred in cleanup.

This is foreign/manual configuration, without the new installer's managed
configuration/receipt. Its Undo action cannot adopt this earlier change.
A future reset requires separate owner confirmation and removal of all affected
controllers' old input devices before changing the module-global parameter,
followed by reconnect and mouse-state verification. Never hot-switch the
parameter on connected devices.

The upcoming recording therefore starts with Guide compatibility already
prepared. It cannot establish fresh privileged installer apply/undo acceptance.
The earlier owner-confirmed installer chord test and normal mouse operation,
and the separate historical Game Boy exit, retain their documented scope.

## Verification and handoff

The actual read-only `read_state` check returned `configured=false`, no saved
language or ROM/BIOS selection, zero managed cores, no managed provider and no
prepared Xemu state; it created no user directories. All deletion targets and
old menu entries are absent. No emulator executable remains on PATH other than
the deliberately shared DOSBox. No portable AppImage `.home`/`.config` profile
exists. KDE's menu rebuild succeeded and Git object connectivity passed.

Protected files passed before/after byte/metadata checks. Local directory
identities and protected top-level entries were preserved. CIFS automounts can
expire/remount while auditing, so their device IDs and covered-root identities
were not treated as content changes. No writes to original collections/media
were made; no full ROM/media content hash scan is claimed.

The handoff image, checksum and manifest are preserved together:

- `~/AppImage/Embercade-1.0-FileChooser-x86_64.AppImage`
- Source: `e084416db1aa4fd30237d24f3bb2ca178db2a2fd`
- SHA-256: `14184e152a4030e84235cadc66c611352c8e1fe0b8f52475720df527dbaa40a3`

No application code changed, no new image was built, no image/emulator was
started and no automatic setup occurred. Filesystem/package/backup/Git checks
validate this cleanup; previous code regression results remain historical.
Full local inventory, execution journal, exact package snapshots, encrypted
backup proof and German report are kept in the task's
`outputs/Reddit-Final-Cleanup-2026-10-10/` directory.

The owner later opens the image and personally follows Language → Welcome →
ROM/BIOS → Host software → Controller & Hotkeys → Xbox → PS3 → Desktop → Checks →
Embercade → ScreenScraper → Emulator → Controller exit → Frontend return.
Shared media will remain visible. This cleanup is not an OS reinstall: retained
system prerequisites and the prepared xpadneo setting are explicit limits.
After the documentation push, stop; further installation belongs to the owner.

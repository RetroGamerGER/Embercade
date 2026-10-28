# Persistent state and secrets — AppImage handoff

This is the persistent-state boundary for the private 1.0 AppImage. The
application image and Production Stage are **read-only code and generic
resources**. They are never a
home directory, secret store or backup. Build/run behavior and image-specific
acceptance are tracked in [APPIMAGE.md](APPIMAGE.md). The original
state-and-secrets handoff below predates AppImage packaging.

## Writable path contract

| Class | Canonical host path (XDG defaults) | Examples | Normal update / non-purge reinstall | Explicit purge |
|---|---|---|---|---|
| Config | `$XDG_CONFIG_HOME/embercade` (`~/.config/embercade`) | `embercade.toml`, `batocera.conf`, controller mappings, ES preferences, emulator-specific settings, first-run selections | Preserve bytes and timestamps | Remove owned root after safety checks |
| Secrets | `$XDG_CONFIG_HOME/embercade/secrets` | Developer and personal ScreenScraper account files | Preserve; never copy into payload | Remove with config root only on confirmed purge |
| Data | `$XDG_DATA_HOME/embercade` (`~/.local/share/embercade`) | saves, states, screenshots, themes and active selection, managed cores/providers, PPSSPP resources, Xemu working firmware, scraper-adjacent user resources | Preserve | Remove owned root after safety checks |
| Cache | `$XDG_CACHE_HOME/embercade` (`~/.cache/embercade`) | generated caches/extractions | Preserve on normal operations; safely reproducible in principle | Remove owned root |
| State | `$XDG_STATE_HOME/embercade` (`~/.local/state/embercade`) | logs, install manifest, Steam backups/lock and other operation history | Preserve except the installer-owned manifest may change on a changed update; identical payload is a true no-op | Remove owned root |
| Session runtime | `$XDG_RUNTIME_DIR/embercade` | compatibility view, sockets and launch-scoped files | Recreated as needed; not backup data | Session cleanup only |
| External collection | user-configured ROM and BIOS roots | ROMs, BIOS, firmware; original-system `gamelist.xml` and selected scraper media directories | Never install, copy or delete; only the existing narrowly permitted scraper metadata/media writes | **Never purge** |
| Steam profile | the selected host Steam account | optional Embercade shortcut and artwork | Preserve; only the explicit Steam integration operation may update Embercade-owned entries | Not part of Embercade XDG purge |

`EmbercadePaths` resolves these roots from the active user's environment, not
the executable's location. The same rules apply to the installed prefix and a
mounted `$APPDIR`. Production rejects writable roots that resolve inside
its immutable prefix or `$APPDIR`; Doctor reports the separation. Do not write
beside an AppImage, into `$APPDIR`, or into a repository/`.work` path at runtime.
Bubblewrap's internal `/userdata` is only a compatibility view of the external
XDG roots. Configured ROM/BIOS roots remain externally owned and read-only,
apart from the established gamelist/media submounts for scraping.

## Secret backend and lifecycle

Owner-only local files are the selected backend. Requiring Secret Service or
KWallet would add a desktop/session dependency to KDE, Hyprland, headless
Doctor and Steam/Gamescope, so neither is mandatory. A future optional secure
store must preserve the same file fallback and must be separately validated on
both hosts before becoming authoritative.

| Secret | File / owner | Use and lifetime |
|---|---|---|
| ScreenScraper application authorization | Private two-field build source, builder owner | Authorized compiled frontend input; extractable from the distributed binary. Original file/header never shipped. A local developer override is only for explicit development builds. |
| Developer debug password | Not a production build input | Excluded from production, never sent by normal requests; debug mode stays off. |
| Personal ScreenScraper user name and password | `secrets/screenscraper-user.conf`, current user | Frontend Accounts UI loads/saves this file; retained until changed or confirmed purge. It is separate from Developer credentials. |
| Future API keys/tokens/passwords | a reviewed, named owner-only secret file or an approved optional store | No generic environment export or unreviewed embedding in normal configuration. |

The `secrets` directory must be owned by the user and mode `0700`; files must
be regular, owned by the user and mode `0600`. Symlinks, oversized or malformed
files are rejected. The developer file is frozen read-only in the frontend
namespace; the personal-account file remains writable only in the owner's
private config tree. The frontend disables ordinary process dumps before
reading credentials. Personal/debug values and loose source secret files never enter the Stage or
image. Production application authorization is intentionally compiled into the
frontend, and is extractable. CMake/argv carry only a private header path; no
values belong in build flags, cache, Doctor output or logs. HTTPS service
requests retain certificate checks and credential-safe errors. An unprivileged
process already controlling the same user session is outside this boundary.

Existing personal account fields in the old owner-only `es_settings.cfg` are
recognized. At the first new frontend start, the frontend writes the separate
private file atomically and only then replaces the settings file atomically
without those fields. A failed secret write leaves the legacy settings intact
and reports a value-free error in the frontend. Installer/Doctor do not expose
account or developer provisioning status. An existing
valid private account file takes precedence over stale legacy fields. Normal
no-op installation does not trigger migration. No actual credentials are
included in fixtures or documentation. Old filesystem snapshots/backups made
before migration are not silently rewritten or destroyed.

Secrets are excluded from ordinary unencrypted user-data backups. A future
backup tool may include config/data/state (including managed cores/providers)
only after separating `config/secrets`; secret export/restore requires a
separate explicit encrypted workflow. External ROM/BIOS roots and Steam's own
profile require their own backup plans. Normal update, reinstall and uninstall
preserve all four Embercade XDG roots; **only** `uninstall --purge --yes` removes
the exact owned roots after path/symlink/external-source checks. Purge is not a
backup or a credential-rotation mechanism.

## AppImage packaging boundary

The private image may contain Embercade code, pinned frontend/configgen runtime,
generic themes/shaders/decorations subject to their separate license gate,
generic configuration defaults and portable non-host-bound libraries. It must
not contain ROMs, BIOS/firmware/keys, personal settings or paths, saves/states,
screenshots, downloaded themes, scraped media, personal/debug or loose source
secrets, Steam account data,
imported Libretro cores or managed provider AppImages. Stage and transfer
audits reject known credential files and credential-bearing ES settings.

The image still expects compatible host graphics/display/audio/input facilities,
Bubblewrap and separately installed supported emulators; users supply legal
content, cores and provider AppImages. Build-time `.work` snapshots and source
archives are not runtime dependencies. The AppImage build must validate
its complete library closure, all writable paths and the same two-host state
preservation contract. This document does not clear the private repository's
third-party asset/license public-release blockers.

On 2026-10-25 the owner explicitly authorized the existing compile-time
application authorization pattern for Embercade. There is no claim that
compiled credentials are secret. No personal/debug credential is bundled, and
there is no additional blanket permission gate for that authorized integration.
Separate third-party/public-release licensing gates remain unchanged. See
[SCREENSCRAPER_PRODUCTION_FIX.md](SCREENSCRAPER_PRODUCTION_FIX.md).

## Historical verified handoff before AppImage packaging

The state-and-secrets Production handoff passed 541 unit/integration tests,
runtime, frontend-library and 14-preset shader smokes, Stage creation and
installed Doctor. A native-file test and a real Bubblewrap namespace test
confirm private permissions, Developer-file read-only mounting and personal
account writes. The Production Stage and offline bundle have the same manifest
on both reference hosts (`e827135bf082…`).

On MainRig/Hyprland and WohnzimmerPC/Steam-Gamescope, the existing personal
account was migrated locally to the private file with mode `0600`; the old ES
settings fields were removed only after the new file existed. The Developer
file and directory retained modes `0600` and `0700`. Real single-title
ScreenScraper access, frontend startup, a short emulator launch/exit and
return succeeded on each host. Both installed Doctors are green; normal
reinstall preserved the pre-install user-state fingerprint on each host, and
repeat identical installs were true no-ops. Later gameplay/scraping changes
to saves or media are ordinary user activity, not installer changes.

The final tracked/staged diff, full transfer bundle and host application/log
checks contain no actual password values or credential-bearing URL logs.
Identifier-only scan matches were independently traced to unrelated public
attribution/controller names; static frontend binaries contain generic URL
parameter names, not credentials. No host credential value is part of this
handoff. This verification established the path and persistence contract.
AppImage build results and two-host acceptance are tracked separately in
[APPIMAGE.md](APPIMAGE.md).

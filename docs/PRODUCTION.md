# Production launch architecture

Embercade 1.0 uses an install-shaped prefix shared by the private development
installer and AppImage packaging. The image consumes the same verified
Production Stage; its build/run contract and artifact-specific acceptance are
tracked in [APPIMAGE.md](APPIMAGE.md):

```text
PREFIX/
├── bin/
│   ├── embercade
│   └── embercade-provider-runner
└── share/
    ├── applications/embercade.desktop
    └── embercade/
        ├── app/                  Embercade Python package
        ├── frontend/             pinned EmulationStation binary
        ├── lib/                  payload-owned frontend libraries
        ├── licenses/             bundled-library notices and license texts
        ├── resources/            UI, policy, defaults, themes, shaders, bezels
        ├── runtime/              pinned batocera-launch/configgen environment
        └── stage-manifest.json
```

`scripts/stage-build` currently materializes this contract below
`.work/stage`. That directory simulates an installation prefix; no runtime
lookup is allowed to depend on `.work` itself. The entry point resolves every
application file relative to its active prefix. Inside the frontend sandbox
the prefix is mounted read-only at stable `/app`, so generated system commands
remain relocatable and contain no build-host path.

Private 1.0 AppImage packaging is implemented by `scripts/appimage-build`.
It wraps this verified Stage unchanged under `AppDir/usr`, delegates through
the existing launcher and keeps all mutable state external. The only bundled
theme is Carbon (`themes/es-theme-carbon`); downloaded themes and active
selection remain user XDG state. The full suite passes 578 tests, and runtime,
frontend-library, shader and Stage Doctor smokes pass. Garuda has confirmed
the image's startup/menu, active external theme, ScreenScraper, Libretro and
Xemu 4:3 bezel/exit. The owner has also confirmed the complete requested image
E2E in the CachyOS Handheld's real interactive Steam/Gamescope session. The later
requested removal of an extra splash version line is confirmed visibly on
Garuda. The matching CachyOS Handheld update passes Doctor with status 0 and
preservation checks, without another visible run at the owner's request.
The final updates preserve 16,161 Garuda entries with zero changes/additions
and 198,109 CachyOS Handheld entries with zero unexpected changes/additions;
only the owned install manifest is excluded. The classic Garuda game/exit/quit
regression also passes. Two fresh full packaging builds with identical Stage,
packaging inputs, source identity and epoch produce byte-identical images and
manifests. Private functional GO applies to the two tested AMD/CachyOS reference
hosts; general distribution portability and public release are not cleared.
Artifact details are tracked in [APPIMAGE.md](APPIMAGE.md).

Complete 1.0 system preparation uses `scripts/system-catalog-prepare` to invoke
Batocera's registry/builders from the existing source pin. Run the structural
integration tests before staging: the stage rejects missing/stale source-digest
evidence. The active `es_systems.cfg` contains only Embercade-supported routes;
the separate `systems-catalog.xml` is audit data, deliberately outside ES's
`es_systems_*.cfg` autoload glob. Pinned BIOS requirements and portable generator
proofs are installation-local; `embercade system-coverage` and verbose Doctor
verify each host's actual core ABI/dependencies without launching games.
Optional host Libretro `.info` metadata never blocks direct `-L` launches,
PREPARED status or Doctor, and is not copied into the payload.

The existing native splash stays visible at least 2,750 ms from its first
presented frame. Loading consumes that interval; slow loading adds no extra
fixed delay. The original artwork with its embedded Embercade logo and native
loading text are retained without an additional generated version line.
The `EMBERCADE 1.0` menu/footer and other product labels remain theme-independent.

## Current development-start classification

| Part | Classification | Production treatment |
|---|---|---|
| Embercade Python and batocera-launch/configgen runtime | production-required | Materialized below `share/embercade`; no startup install/build |
| EmulationStation binary, resources, locale and Carbon theme | production-required | Pinned/materialized below the prefix |
| FreeImage and SDL2_mixer frontend libraries | production-required payload dependencies | Staged below `share/embercade/lib`; exposed only to the frontend sandbox |
| `es_systems.cfg`, `es_features.cfg`, controller and savestate data | production-required | Production-specific stable `/app` and `/userdata/roms` paths |
| Batocera launch defaults, games database and rendering defaults | production-required | Read-only staged runtime resources |
| shaders | production-required | Complete official Libretro Slang tree from a commit- and SHA-256-pinned archive; curated mappings generated and dependency-validated at build time |
| decorations | production-required | Existing byte-pinned, read-only staged resources |
| desktop capability policy | production-required | Loaded from staged resources |
| XDG config, saves, cache, state and logs | production-required user state | External XDG directories bind-mounted into the sandbox |
| fake `/userdata` hierarchy | compatibility-only internal detail | Generated below Embercade runtime state from XDG; never a host `/userdata` contract |
| Bubblewrap | host-provided production dependency | Creates the desktop/Batocera compatibility namespace |
| python-evdev | host-provided input dependency | Loaded through a narrow ABI-matched adapter for the configured launch-scoped exit chord |
| graphics devices, Wayland/X11, PipeWire/Pulse and input devices | host-provided | Passed through narrowly from the current desktop session |
| emulator binaries, Libretro cores and external providers | user-/host-provided | Never bundled in the release payload; optional core and known AppImage imports become managed XDG user data |
| ROM and BIOS collections | user-provided read-only data | Configured centrally and mounted read-only |
| pinned source archives, compiler, CMake, `msgfmt` and Python dependency resolution | build-time-only | Used by prepare/stage, never by normal startup |
| selected test ROM links, `.work/e2e-xdg` and `launch-*-test` wrappers | dev-only | Absent from the production contract |
| `dev-prepare` and `dev-run` | dev-only | Retained for development regression work |

## User state and compatibility namespace

Persistent state follows XDG:

```text
$XDG_CONFIG_HOME/embercade
$XDG_DATA_HOME/embercade
$XDG_CACHE_HOME/embercade
$XDG_STATE_HOME/embercade
```

The host's `XDG_RUNTIME_DIR` continues to provide desktop sockets. Embercade's
private runtime state is below an Embercade-specific directory. Bubblewrap
maps those roots to an internal Batocera-compatible `/userdata` view; it does
not create or require `/userdata` on the host. ROM and BIOS roots are mounted
read-only both at their configured absolute paths and at the compatibility
locations used by generated system data.

The 1.0 ScreenScraper integration makes one precise exception: original-system
`gamelist.xml` plus upstream `images`, `videos`, `manuals`, `magazines` receive
writable submounts. Collection/system directory and ROM content mounts remain
read-only. Local Developer and personal-account secrets are separate owner-only
XDG files: only the Developer file is bound read-only in the frontend namespace;
the personal file is writable for the Accounts UI. Neither enters Stage/offline
payload, and normal updates preserve both. Production rejects writable roots
inside the immutable prefix or AppImage. See
[STATE_AND_SECRETS.md](STATE_AND_SECRETS.md).
Real two-host scrape, non-purge reinstall and true no-op update acceptance pass,
including the second host's interactive Steam/Gamescope session. See
[SCREENSCRAPER.md](SCREENSCRAPER.md).

When the desktop session supplies `XAUTHORITY`, Production validates the file
and bind-mounts it read-only at a stable path below the sandbox runtime
directory. This keeps Xwayland-aware host tools such as `vulkaninfo` working
inside a KDE Wayland session without exposing the home directory or copying
the session cookie. A delegated external provider receives the corresponding
validated host path rather than the namespace-only mount target.

PCSX2 is the one firmware consumer that creates mutable NVM/MEC companions
beside its selected BIOS name. Embercade therefore exposes the immutable BIOS
images as symlinks in `$XDG_DATA_HOME/embercade/bios/ps2` and keeps all NVM/MEC
state there; it never writes those companions into the external BIOS pack.
For unconfigured host resources it recognizes the two distribution spellings
`/usr/share/pcsx2/resources` and `/usr/share/PCSX2/resources`; an explicit
`[pcsx2].resources` value still takes precedence.

Xemu seeds private firmware/HDD copies from explicit source variables when
provided, otherwise from `Complex_4627.bin`, `mcpx_1.0.bin` and
`xbox_hdd.qcow2` at the configured read-only BIOS root. An EEPROM source is
optional: native Xemu generates a missing EEPROM at the explicit Embercade
`saves/xbox/xemu_eeprom.bin` path. Existing EEPROM/HDD state is never replaced.
An optional legacy `eeprom.bin` seed remains supported. Sources stay read-only;
subsequent writes remain in Embercade's private BIOS/save tree. Version/source
evidence, recovery and fresh Garuda acceptance: [GARUDA_BLANK_INSTALL.md](GARUDA_BLANK_INSTALL.md).

External AppImage providers delegated outside Bubblewrap receive host paths,
not namespace-only `/userdata` spellings. Translation is limited to the
explicit Embercade XDG/runtime, ROM and BIOS bind roots exported by production
startup.

Xenia Edge follows Linux's XDG data convention for its configuration rather
than configgen's generic config-directory convention. The delegated provider
therefore receives configgen's `emulators/Xenia` parent as `XDG_DATA_HOME`, so
both components address the same `Xenia/xenia-edge.config.toml`. Absolute
storage, content/save and cache values written to that file use the validated
host-visible Embercade roots; no namespace-only `/userdata` path reaches the
external AppImage.

For a requested Xenia exit, Production exposes only the existing host
`systemd/private` socket to the frontend namespace. The launcher uses the
host session runtime solely for `systemctl --user`; emulator XDG roots remain
private. The delegated transient service uses `KillMode=mixed`, allowing its
host runner to stop its own process group and unmount only AppImage mounts
created by that launch before the service exits. Select+Start has been
validated with launcher status 0, no remaining Xenia process or AppImage
mount, and return to the same frontend process on Garuda/Hyprland and the
CachyOS Handheld's real Steam/Gamescope session.

## Native Wii controller access (1.0)

The production namespace exposes only currently permitted Wii `hidraw`
character devices identified through sysfs, alongside its existing input
mount. Device numbers are discovered, never hardcoded. Dolphin owns real
Wiimote/Nunchuk/IR/motion interpretation and continuous scanning; Embercade
reuses the pinned plugin and existing EMULATE WIIMOTE option for Real/gamepad
selection. Auto/unset checks current remote liveness at game launch, On forces
emulation and Off selects Real. Existing user settings and GameCube mappings
are retained; neither Doctor nor structural dry runs send HID reports.
The session uses `SDL_JOYSTICK_HIDAPI_WII=0` so SDL does not interpret the
receiver slots as extra gamepads ahead of the user's PCSX2/RPCS3 controller;
Dolphin's own Real Wiimote transport remains enabled.
The desktop emulated-Wiimote branch maps Start/Back/Guide to Wii +/−/Home;
native Real Wiimote and GameCube generation stay unchanged. Sideways titles
use the existing per-game Wiimote Sideway setting, not a global axis swap.
Dolphin's Player-1 native exit binding uses the same SDL-to-evdev slot
translation as its game controls. This matters for Bluetooth pads with extra
Linux system keys; a different pad's exit chord remains intentionally inactive.

No host Bluetooth/udev service, permission or driver change is made. Config,
NAND, saves and caches remain in existing isolated Embercade locations.
Wireless remote reconnect uses the receiver's existing nodes; receiver USB
unplug/replug or attachment after frontend start requires restarting the
frontend to refresh namespace mounts. Direct Bluetooth and exclusive
passthrough are not established by the DolphinBar acceptance. Missing real
hardware is informational, not a Doctor failure. See
[WII_CONTROLLERS.md](WII_CONTROLLERS.md) for exact hardware and acceptance scope.

The optional standalone-decoration layer also supports GameCube/Wii Dolphin
using the already staged console art and pinned Batocera bezel selection.
`Decoration=None`, missing art, unsupported compositor and wide/unknown aspect
settings leave game launch functional. The helper is tied to the concrete
fullscreen emulator window and is removed before return to the frontend.
Garuda's earlier missing Xemu frame was caused by its preserved Auto aspect
setting, not absent assets; explicit 4:3 permits the existing frame.
Gamescope continues to require an unoccupied external-overlay plane. See
[STANDALONE_DECORATIONS.md](STANDALONE_DECORATIONS.md).

## Managed shadPS4 and PS4

The 1.0 PS4 route extends the existing AppImage backend used by Xenia; it is
not a second installer/provider framework. `embercade setup --shadps4-from`
accepts a user-selected file or folder containing one distinct shadPS4 build.
The graphical wizard has its own optional PlayStation 4 step, validates the
source before import, retains Back/Forward selections and shows the existing
selection on later visits. Skipping it never blocks ordinary setup.

Recognition checks bounded ELF64/x86-64/type-2 AppImage/SquashFS metadata and
`usr/share/applications/net.shadps4.shadPS4.desktop`: Name `shadPS4`, Exec
`shadps4`, matching StartupWMClass (a trailing desktop-entry semicolon is
accepted). A basename is not identity or an authenticity guarantee. SHA-256
deduplicates candidates and imports; different builds conflict rather than
overwriting. The source is never executed by inspection or modified by import.
The executable managed copy is
`$XDG_DATA_HOME/embercade/providers/shadps4/shadps4.AppImage`.
`[emulators.shadps4]` selects that copy with `provider = "appimage"`; PATH and
native/unknown shadPS4 providers are rejected. No downloads or provider links
are offered, and the binary is never part of the production payload.

Doctor differentiates managed/external, missing, invalid, unverified,
ambiguous/unselected and runtime-dependency-missing states. It reads the
embedded `usr/bin/shadps4` into an anonymous memfd and applies the existing
ELF loader-closure check without extracting files or executing the emulator.
This host-only dependency check is conservative; it does not claim that
arbitrary AppImage-private libraries satisfy a missing host closure. Metadata
inspection needs the existing bounded unsquashfs/7z reader; launch needs the
existing systemd user runner/FUSE support. Timeout/failure is a diagnosis, not
a traceback or successful runtime check. No GPU driver is bundled by Embercade.

Pinned Batocera supplies `ps4`, `.ps4 .zar`, `shadps4 / shadps4` and the built-in
`batocera_launch.emulators.shadps4:Shadps4` generator. `.ps4` is a directory
with readable `eboot.bin`, not a renamed ISO; `.zar` is its archive form.
The final game argv is `<managed AppImage> -g <eboot.bin-or-zar> --fullscreen true`.
`-b` is reserved for the emulator configuration/Big Picture interface; adding
it to direct launch would select the browser instead of the requested game.

The delegated host runner translates content to the configured real ROM root
and supplies isolated HOME/TMPDIR/XDG paths. `XDG_DATA_HOME` is the Embercade
emulator-config root because shadPS4 appends `shadPS4` itself. Therefore the
generator and emulator share
`$XDG_CONFIG_HOME/embercade/emulators/shadPS4/config.json`, input configs,
logs, caches, shaders, patches, trophy/user metadata and screenshots. Saves
use `$XDG_DATA_HOME/embercade/saves/shadps4`; add-ons use the Embercade-owned
`shadps4-addons/`, never a writable ROM collection. Existing rendering,
vblank and GPU selections are retained unless an explicit Batocera option
requests a change. Fullscreen and owned storage paths remain enforced.
Invalid JSON is not discarded. A migrated invalid GPU selection may require
user correction; preserving settings is not proof of their runtime validity.

The normal host shadPS4 profile is neither imported automatically nor modified.
Missing dumped fonts, system modules or trophy keys are title-dependent user
setup constraints; NONE_DECLARED in the Batocera BIOS checker is not a firmware
clearance. No firmware/keys/fonts are downloaded or bundled.

Dynamic SDL mapping and the existing configured exit bridge are reused. Exit
stops only the owned shadPS4 service/process group, waits for cleanup and unmounts
only AppImage mounts from that launch before returning to the same frontend.
The shared Steam host-runner input/window-tag policy is retained. For shadPS4,
Gamescope tagging also covers native helper dialogs by their `_NET_WM_PID` and
the launched provider's process group, never unrelated windows by dialog class.
This includes the emulator's save-migration question: Embercade makes no
migration choice and never silently copies/moves normal host-profile data.
The private runtime directory is translated to its host-visible Embercade
path for delegated helpers, not left as a sandbox-only path.
Garuda/Hyprland and the CachyOS Handheld's real interactive Steam/Gamescope
session both confirm Bloodborne gameplay, audio, controller and configured
exit back to the same frontend, with status 0 and complete process/mount
cleanup. This is acceptance for the tested user-supplied build/game, not
universal PS4 compatibility. The migration prompt did not recur during the
successful second-host run; helper-dialog ownership is regression-tested.
Normal reinstall/uninstall preserve the managed AppImage, config and saves;
only separately confirmed purge deletes owned user state, never the source.

## Theme Library and persistent user themes

Production prepares `$XDG_DATA_HOME/embercade/themes` and its `.tmp` workspace
before starting the frontend. `/userdata/themes` points at that directory
through the existing writable Embercade data bind. Carbon stays in the
read-only installed `resources/emulationstation/themes` tree. No normal
EmulationStation profile or host theme directory is exposed for writing.

The pinned frontend owns the complete workflow: `GuiThemeInstaller` and
`ContentInstaller` call `ApiSystem::getBatoceraThemesList` and
`installBatoceraTheme`. The catalogue defaults to the upstream `themes.json`;
previews use its screenshot URLs. Installation resolves the repository branch,
downloads a ZIP into `themes/.tmp`, extracts it with the frontend's ZIP reader
and moves the theme into `themes/<repository-name>`. `HttpReq` initially writes
`<repository-name>.zip.tmp` before renaming to `.zip`; the frontend removes
its extraction workspace on completion/failure. Production recreates `.tmp`
on the next start without clearing existing themes or partial files itself.
Embercade adds no downloader or catalogue and never patches downloaded themes.

The original I/O failure was a dangling `/userdata/themes` compatibility link:
its persistent target had not been created. The frontend's recursive mkdir
could not repair that symlink, and opening the download stream failed with
`IO Error (disk is Readonly ?)`. The existing data bind was writable; making
the immutable prefix writable or disabling the sandbox was not necessary.

Theme selection remains the frontend's persistent `ThemeSet` setting in
Embercade's isolated `emulators/emulationstation/es_settings.cfg`. Normal
update/uninstall owns neither that config nor downloaded theme files, so they
survive reinstall. Theme downloads require upstream network availability and
free user-data storage; third-party themes retain their own compatibility and
license terms. They are user downloads, not newly bundled release resources.

Themes may style the normal menus, system/gamelist views and game-art panels.
They cannot replace Embercade product branding. Under the desktop policy the
fullscreen startup/reload/loading splash bypasses theme and builtin splash XML,
including background overrides and extras, and uses Production's installed
Embercade image with the unchanged native loading text/lifecycle and no added
version line. The central `EMBERCADE 1.0` label supplies the frontend menu/footer, information
version, window title, wizard and desktop name. The frontend window title is
set after SDL window creation, preserving its existing class/app-id identity.
Desktop/Steam icons and
artwork are separate installed resources, not theme outputs. The prefix is
read-only in the frontend namespace; a same-named image inside a theme cannot
overwrite those resources. Missing product splash still uses the existing
no-splash fallback rather than a third-party replacement.

The following theme acceptance is historical installed-prefix evidence from
before the 1.0 branding and AppImage packaging change.

Automated checks cover path preparation, writable namespace/read-only branding,
theme-independent splash selection and preservation of downloaded themes,
partial downloads and active ThemeSet during reinstall. Garuda Hyprland
acceptance confirms an actual AI-Hypertocera download/install, activation,
Carbon round trip, controller navigation, Xemu launch/return and complete
restart with the unchanged Embercade splash. Theme/artwork hashes remain
separate. Normal Garuda offline reinstall preserves inventoried themes,
active selection, config, saves and provider data; the same theme and splash
load afterward without a fresh download.

The CachyOS Handheld's real interactive Steam/Gamescope acceptance also passes:
frontend download/install of AI-Hypertocera, activation and Carbon round trip,
controller navigation, Gambatte/Game Boy launch/exit/return, normal Quit
Embercade back to Steam, complete Steam restart and the unchanged product
splash. Its normal offline reinstall preserves the inventoried themes, active
selection, configuration, saves and providers; the next user-confirmed Steam
start loads the existing theme without downloading again. Both reference
installations are verified against the same offline payload manifest and
per-file hashes. This is acceptance for the tested environments/theme, not a
compatibility or license guarantee for the whole upstream catalogue.

## Build and runtime inputs

Batocera and EmulationStation source identities come from `upstream.lock`.
Static non-shader Batocera 44 resources not stored in those Git trees are
accepted only when their complete byte-tree matches
`resources/resource-bundle.lock`. Shaders come from the official Libretro
`slang-shaders` archive pinned by commit, source URL and SHA-256 in
`runtime/shaders.lock`. `resources/shaders/catalog.toml` is the independent,
small menu selection. Preparation copies the complete upstream tree, adds only
mapping presets/configs, and recursively verifies every dependency used by the
curated set. The host's RetroArch shader directories are neither read nor
mounted as a runtime requirement. `stage-manifest.json` records the final
relative file set, sizes, SHA-256 digests and upstream pins without timestamps
or installation-host paths.

Normal startup performs no network access, package installation, source build
or emulator probe execution. `embercade doctor` validates the installed
runtime/frontend/resources, collection roots, writable XDG destinations,
desktop session, controller visibility, native emulators, Libretro cores and
configured external providers without launching an emulator.

## Frontend shared-library closure

An executable bit alone is not evidence that the staged frontend can run.
Every stage build reads EmulationStation's direct ELF `NEEDED` entries and
runs a read-only loader-resolution check with only the staged frontend-library
directory added. Each direct dependency is explicitly classified as either a
payload dependency or a normal compatible-host dependency. The build fails on
an unknown direct dependency, any unresolved transitive dependency, or a
payload dependency that resolves outside the stage.

The current payload dependencies are `libfreeimage.so.3` and
`libSDL2_mixer-2.0.so.0`. Production launches expose
`/app/share/embercade/lib` through a process-scoped `LD_LIBRARY_PATH` inside
the Bubblewrap namespace. The host's value is deliberately not inherited; no
global environment, `/usr/lib`, loader configuration or system symlink is
changed. All other declared direct frontend dependencies remain
host-provided and are validated by the same closure check.

The payload's central license tree also carries Batocera's pinned root
`COPYING`, EmulationStation's pinned MIT `LICENSE.md` and Carbon's license and
attribution-bearing `readme.txt`. Shader provenance, pin, catalog and the
current per-selection attribution/license findings are copied into
`licenses/shaders`; all nested upstream notices remain in the shader resource
tree.

FreeImage 3.18.0 and SDL2_mixer 2.8.2 are prepared at build time from the
exact source URLs and SHA-256 values recorded in `runtime/frontend-libs.lock`.
Both unmodified upstream sources are compiled for generic x86-64. FreeImage
uses its bundled codecs, avoiding the development host's repository-specific
OpenEXR and JPEG-XR ABI dependencies. SDL2_mixer uses its built-in DR FLAC,
minimp3 and stb_vorbis decoders and has only SDL2 plus the C runtime as direct
dependencies. Their upstream license texts, the embedded decoders' original
license-bearing headers and build provenance NOTICE files are copied into the
payload. `scripts/frontend-libs-prepare` performs the
pinned source/license verification; `scripts/frontend-libs-smoke` validates
SONAMEs, CPU targets and the deliberately small ELF dependency sets.

The frontend itself is compiled with explicit generic x86-64 flags. Compiler
file-prefix mapping replaces source-root paths with `/embercade-source`,
including `__FILE__` strings. Post-link processing strips debug information
and scans the complete binary for personal `/home/...` paths; any remaining
match fails the build without printing path values. CachyOS
build-host startup objects advertise their repository's higher ISA tier even
when the generated application code is baseline, so the build removes that
host-specific GNU property note and verifies that no nonbaseline ISA
requirement remains. Stage and Doctor independently reject a frontend that
still declares x86-64-v2/v3/v4 as required.

Doctor uses this same inspection path for both a stage and an installed
prefix. It reports `binary present` and `shared libraries` separately and
lists unresolved SONAMEs without starting a GUI process.

## User-local installation

`scripts/install-user` is the development entry point. It verifies the
complete stage manifest and builds the pinned stage only when no valid stage is
available. The installer copies the payload to a sibling temporary tree,
verifies the copy and activates the payload, launcher, desktop entry and
manifest as one rollback-capable transaction.

```text
$HOME/.local/lib/embercade/                         immutable payload
$HOME/.local/bin/embercade                         launcher symlink
$XDG_DATA_HOME/applications/embercade.desktop      desktop entry
$XDG_DATA_HOME/icons/hicolor/512x512/apps/embercade.png application icon
$XDG_STATE_HOME/embercade/install-manifest.json    ownership metadata
```

The desktop `Exec` field contains the quoted absolute user-local launcher path,
so it does not depend on a graphical session's `PATH`. Reinstallation replaces
only a verified existing immutable installation and preserves all XDG user
state. The install manifest records payload files, hashes, pins and installed
targets, but no ROM, BIOS or provider paths. `update-desktop-database` is a
best-effort refresh, not an installation requirement.

Update/reinstall is refused while a process from the installed prefix is
running; replacing its mounted payload could crash the live frontend. After a
successful first interactive install in a desktop session the graphical
`embercade wizard` opens. Without a display, terminal `embercade setup` remains
available. A normal update does not reopen either flow, import providers/cores
or prompt for Steam registration.
If the launcher
directory is absent from the current `PATH`, the installer prints
shell-specific guidance (including `fish_add_path` for fish) without editing
shell startup files.

### Update and preview

The current private-development update source remains a verified Production
Stage or offline transfer bundle, not a network service. Build the stage before
the development dry run; `scripts/install-user --dry-run` refuses a missing or
invalid stage without building one. On the second host use the bundle's
`./install --dry-run` and then `./install`. The bundle verifies its checksum
list before delegating to the same installer. No sudo, system packages or
emulator installation is part of this operation.

Preflight verifies all incoming file hashes and the existing managed install.
The output separates the visible product label (`EMBERCADE 1.0`), internal
package version (`0.1.dev0`) and short SHA-256 of each Stage manifest. An
older install without a recorded product label is honestly shown as unknown;
no semantic-version ordering is inferred. A matching verified payload, desktop
entry and icon returns `ALREADY UP TO DATE` without rewriting files, creating
backups or touching persistent state. Dry-run performs the same read-only
checks and prints the planned immutable targets and preserved data.

For a changed payload, the existing sibling-copy/backup transaction is used.
Existing-install validation tolerates regenerated Python bytecode in the
runtime and the application's `__pycache__` directories, including caches
left by older acceptance tools. Real source/resources remain strictly verified.
Incoming bundles are always checked without that tolerance; a normal update
replaces the immutable prefix transactionally rather than manually deleting
user state or loosening payload integrity checks.
Before backup removal, the activated prefix, desktop entry, launcher, icon and
install manifest are verified again. A verification/activation failure restores
the previous managed targets and is not reported as success. The installed
manifest retains the full payload SHA-256 plus its pins and ownership metadata;
the offline bundle separately records the source Git commit. The user should
run `embercade doctor` after update to check collection and host requirements.
A Doctor warning is not silently called a successful host-health check, but
it does not imply that immutable application files failed verification.

Normal update never purges `$XDG_CONFIG_HOME/embercade`,
`$XDG_DATA_HOME/embercade`, `$XDG_CACHE_HOME/embercade` or
`$XDG_STATE_HOME/embercade` user data other than its owned install manifest.
This includes saves/states, screenshots, downloaded themes/selection, managed
cores/providers, PPSSPP assets and Steam shortcut/artwork/backups. External
ROM/BIOS references and host emulator profiles are not update targets. The
separate `uninstall --purge --yes` remains explicitly destructive. There is no
automatic downloader, version archive or general rollback/migration framework
in this implementation; broader recovery and graphical update UX remain later work.

The historical 0.5 `69da88c` update was accepted on both reference hosts from
the same verified offline payload: 9,658 staged files with Stage-manifest SHA-256
starting `bbfddb109650`. Each host completed a changed update, an identical
second run with no replacements, and a green installed Doctor. Pre/post
inventories of Embercade's configuration, data, cache and state roots (excluding
only the owned install manifest) were identical immediately after install;
Steam shortcut and grid-artwork hashes were unchanged. Garuda Hyprland and
the real CachyOS Handheld Steam/Gamescope session then passed user-visible splash,
product label, theme/controller menu, Xenia launch, Select+Start exit, return
to the same frontend and normal Quit Embercade. Launcher logs recorded status
0 on both hosts. The second host left no provider or AppImage mount. Gameplay
may naturally change saves or caches after this installer-only comparison.

## Branding and Steam presentation

The Desktop Entry uses `Icon=embercade`; the installer owns and hash-verifies
the hicolor icon alongside the immutable prefix. Runtime branding derivatives
are staged under `share/embercade/resources/branding`; the large source masters
are not part of the payload. Production passes the 3840x2160 startup image to
EmulationStation's native `--splash-image` option, which dismisses it when
frontend initialization finishes. Missing splash artwork falls back to
`--no-splash` without blocking startup.

The `branding/steam` directory contains the portrait grid and landscape hero.
Interactive setup offers `Add Embercade to Steam? [Y/n]` after the optional
firmware handoff and before Doctor/frontend launch. Registration is separate
from immutable payload activation: refusing or failing this optional step does
not invalidate the installed application. Normal runtime startup never writes
Steam metadata. `--no-setup` and noninteractive setup do not register Steam;
the explicit `embercade steam` command can do so later.

The shared `steam.py` integration discovers existing native Steam user profiles,
deduplicates aliases and requires account selection when there is more than one.
It uses the installed user-local launcher for classic registration, or the
user-owned executable image when invoked through the mounted AppImage.
Explicit `--replace-existing` switches the one shortcut between those stable
targets. Temporary mounted/extracted paths are refused. It preserves an
existing shortcut's appid/options/tags and foreign entries byte for byte, sets its visible name to
the central `EMBERCADE 1.0` label, and installs the existing
icon/portrait/landscape/hero/logo-slot resources for that one appid. Repeat runs
with unchanged resources do not rewrite files or add duplicates. The logo slot
uses the existing embedded-wordmark landscape image, not a newly designed
transparent wordmark.

Steam and its web helper must be stopped; no process is killed or automatically
restarted. Inputs are validated before writing, original bytes and POSIX modes
are backed up below Embercade XDG state, and individual replacements are atomic
with in-process rollback. Start Steam after registration to reload metadata.
Missing Steam is optional. Ambiguous/corrupt metadata and unvalidated Flatpak
host-launcher access are deferred without guessing. Steam metadata/artwork and
backups are user state, not immutable payload ownership; uninstall leaves them
alone. See [STEAM_INTEGRATION.md](STEAM_INTEGRATION.md) for precise targets,
recovery and remaining validation limits.

The following automatic-registration evidence is historical 0.5
installed-prefix acceptance. The path was accepted on Garuda and CachyOS Handheld.
The latter runs
CachyOS Handheld Edition with Steam/Gamescope and received a normal offline
update from `9ebdca3`. Both installed payloads match the same verified stage
manifest; the second host has no Git checkout and was deliberately validated
through the offline package's source-commit metadata and file hashes.

Before/after metadata comparisons proved the installer preserved persistent
Embercade user state, saves/states, providers and PPSSPP assets. Config hashes,
ROM/BIOS references and normal host emulator profiles stayed unchanged; save
contents were not inspected. Only the installation manifest was excluded from
the state comparison. No managed-core directory existed on the second host;
Doctor still resolves all 28 cores required by its collection.

With Steam stopped, automatic registration reused its existing shortcut/appid,
preserved all eight foreign entries and unrelated artwork, and populated all
five branding slots. The repeat run was byte-identical and added neither a
duplicate nor a backup. The user launched the shortcut in the real interactive
Steam/Gamescope session and accepted artwork, splash dismissal and controller
navigation. A representative Xemu launch, correctly proportioned bezel,
Select+Start exit and return to the same frontend PID also pass. An active Steam
performance overlay may occupy the bezel plane; turning it off and relaunching
the emulator restored the decoration without code or userconfig changes.
The subsequent normal Quit Embercade returned to Steam and left no frontend
process running.

At that historical milestone, the full 345-test suite,
runtime/frontend-library/shader smokes, Production Stage and installed Doctor
passed. Flatpak Steam launch remains unvalidated.
SSH-triggered launches are not visible acceptance evidence.

## Portable offline test payload

The 1.0 3DO addition is accepted through the existing Libretro/Opera production
route on Garuda/Hyprland and interactive Steam/Gamescope on CachyOS Handheld.
It adds no bundled core/BIOS or standalone emulator. Normal offline updates
preserve inventoried user state; both final installations match the same
manifest and per-file hashes. See [COMPATIBILITY_1_0.md](COMPATIBILITY_1_0.md)
for BIOS, CUE/BIN, tests and visible acceptance details.

`scripts/build-test-payload` first rebuilds the verified Production Stage and
then creates these ignored release-test artifacts:

```text
.work/dist/Embercade-0.1.dev0-test/
├── install
├── payload/                    exact verified Production Stage
├── manifest.json               version, source commit and per-file SHA-256
├── SHA256SUMS                  pre-install integrity input
└── README-FIRST-TEST.txt
.work/dist/Embercade-0.1.dev0-test.tar.gz
```

The archive is generated with sorted entries, normalized ownership, modes and
timestamps, and a zero-time gzip header. Repeated builds from the same source
commit and stage inputs therefore have identical file lists, manifests and
archive hashes. Neither the directory nor archive is tracked by Git.

The top-level `install` performs a read-only checksum verification and then
delegates to `payload/bin/embercade install --payload payload --no-setup`.
There is no second installer implementation. The target needs no repository,
Git, pip, upstream checkout, internet access or build tools; the embedded
Production Stage provides Embercade's application/runtime files. The normal
host requirements and emulators remain separate and are handled only by the
optional installed `embercade bootstrap` command.

The transfer payload excludes ROMs, BIOS, firmware, Libretro cores, emulator
binaries, external AppImages, personal configuration and logs. Xenia remains
user-supplied, with `$XDG_DATA_HOME/embercade/providers/xenia/` as the
recommended provider directory.

Second-host test sequence:

```text
1. Copy and extract Embercade-0.1.dev0-test.tar.gz.
2. Run ./install (no sudo).
3. Run embercade wizard (or embercade setup without a desktop).
4. Review the check and optionally run embercade bootstrap.
5. Run embercade doctor.
6. Run embercade.
```

Copying to a second host is a manual operation after the build; pass the
operator's own SSH target instead of storing it in the project:

```sh
scp ".work/dist/Embercade-0.1.dev0-test.tar.gz" "<ssh-target>:~/"
```

Packaging never connects to or installs on the second host.

## First run and diagnostics

PPSSPP Libretro needs the complete user-provided official `assets/` contents
at `$XDG_DATA_HOME/embercade/resources/PPSSPP` (default XDG data home:
`~/.local/share`). No extra config entry is needed there. An explicit
`[libretro].ppsspp_assets` path remains supported, with
`EMBERCADE_PPSSPP_ASSETS` taking precedence. Production exposes the validated
source read-only at a stable sandbox path; the launcher creates only an
Embercade-owned `system_directory/PPSSPP` symlink. Doctor checks the same
source for `ppge_atlas.zim`, `lang/` and `flash0/` without writing anything.
These user resources survive normal reinstall/uninstall and are not included
in the release payload. No normal RetroArch profile is changed.

`embercade setup` asks for existing readable ROM and BIOS directories and one
of the tested Back/Select+Start or Guide+Start exit presets. The collection
roots are only referenced, never copied or modified. For Libretro cores and
known external AppImages, interactive setup shows an auto-detected source
folder and offers detected, different or skip. If none is detected, it can
accept any readable source folder (for example USB or NAS). Non-interactive
`--cores-from` and `--providers-from` are also available. Existing TOML
comments, unrelated tables and settings are retained; consciously selected
values are written by same-directory atomic replacement with user-only
permissions.

The core importer scans the selected directory read-only for `*_libretro.so`,
checks ELF64 little-endian x86-64 shared-object structure, bounded load
segments and Libretro entry-point names, then copies every valid candidate to
`$XDG_DATA_HOME/embercade/cores`. It does not filter by current ROMs or keep a
second core mapping database. The central resolver searches managed cores
before host RetroArch directories, after any explicit Embercade override.
Known Xenia Edge AppImages are checked for ELF/AppImage and embedded desktop metadata, copied to
`$XDG_DATA_HOME/embercade/providers/xenia/`, made executable there and
configured automatically. Unknown AppImages are not executed or imported.
Imports are atomic, reuse byte-identical files and never silently overwrite
different provider content, even under a different filename. Source files stay unchanged. These managed
copies survive normal uninstall/reinstall and are absent from the offline
payload.

### Known AppImage safety

Only Xenia Edge is recognized for managed AppImage import. The existing
`EmulatorProvider`/executable resolver remains authoritative; no separate
provider selection catalogue was introduced. Recognition checks bounded
ELF64/x86-64 load metadata, the type-2 AppImage/SquashFS layout and the exact
embedded `usr/share/applications/xenia_edge.desktop` fields:
`Name=Xenia Edge`, `Exec=xenia_edge` with an optional `%f`/`%F`, and
`StartupWMClass=xenia_edge`. This identifies the application, not its
authenticity or trustworthiness. No provider is executed for identification
or a version query. No version is inferred from a filename.

The read-only metadata helper is an already installed `unsquashfs`, or
`7zz`/`7z`/`7za` with SquashFS support. It reads only the selected entry to
stdout through an inherited read-only file descriptor; no extraction directory
is created. ELF offsets, helper output (8 KiB) and time (5 seconds) are bounded.
If neither tool is available, the provider is **unverified**, not claimed to
be corrupt. Embercade neither installs nor bundles these tools. The reference
Garuda uses `unsquashfs`; the CachyOS Handheld uses its existing `7z`.

Setup/import outcomes:

- No import folder selected: retain the current provider configuration.
- Empty folder: no AppImages found; create no managed file.
- Unknown identity: ignore it, including deceptively named AppImages.
- Invalid/unreadable file: skip it and report the diagnosis.
- One valid distinct build: import atomically as
  `$XDG_DATA_HOME/embercade/providers/xenia/xenia_edge_linux.AppImage`.
- Several identical source files: one logical candidate and one managed copy.
- Identical existing managed copy: reuse its existing path, even if the new
  source was renamed; no copy, backup, or new random filename. A verified
  non-executable managed copy may have its executable permission repaired;
  the source's permissions are never changed.
- Several different source builds: import none rather than choosing by order,
  filename or guessed version. Select a folder containing only the intended
  build, or explicitly configure its external path.
- Different/damaged existing managed AppImage: keep it unchanged and create
  no backup/replacement. Inspect with `embercade doctor --verbose`; to replace
  it, deliberately move the old managed file to a safe location, then reimport.
  A missing managed file can be restored from a valid selected source.

Copies retain the existing same-directory temporary-file, checksum, `fsync`
and exclusive hard-link publication mechanism. Source changes during
inspection/hashing/copy are rejected; unfinished copies are cleaned up.
Sources, ROMs and BIOS directories remain read-only. Normal reinstall/update
and default uninstall preserve managed providers and configuration.

Configured precedence is unchanged:
`[executables].xenia-edge` → `[emulators.xenia-edge]` → `PATH`.
An invalid override is not hidden by managed discovery. Import can create a
managed copy while retaining an explicit override, but clearly reports that
it has not replaced the active selection. An unchanged repeated setup does
not rewrite the TOML file. Optional provider damage does not erase its path
or prevent collection setup.

Doctor uses the same inspection and reports `MANAGED`, `OVERRIDE`, `FOUND`
(external/native), `MISSING`, `INVALID`, `UNVERIFIED`, `AMBIGUOUS`, `OPTIONAL`
(not needed for the collection), or `UNSELECTED` (valid managed copy exists,
but setup has not selected it). An optional system gap is not installation
damage. Detailed paths and diagnosis are available with `--verbose`.
External legacy executable overrides receive the same read-only production
mount visibility as provider-configured files.

The current installer supports only Arch Linux, CachyOS and Garuda. Its
automatic host installation uses pacman and rejects other distro IDs before
package probes, confirmation or installation. ID_LIKE=arch alone does not
enable an unvalidated derivative. The supported first-run sequence is:

```text
./scripts/install-user        user-local payload; never sudo
embercade wizard              graphical paths, hotkey, optional imports and checks
embercade bootstrap           optional collection-aware package plan
embercade doctor              shared host/runtime verification
embercade                     frontend launch
```

### Graphical first run (1.0 development)

`embercade wizard` is a separate GTK 3 window using host Python and SDL2. The
backend remains the installed, pinned Embercade command: the window passes
argument vectors to `setup`, `doctor`, `bootstrap` and `steam`, rather than
writing TOML, copying sources or implementing a second provider/core resolver.
GTK/SDL2 are host GUI libraries, not added to the pinned launcher venv. A
missing graphical display or GTK binding produces a concise error and leaves
terminal `embercade setup` available. No wizard process is started during a
normal update/reinstall.

An already valid ROM/BIOS configuration is recognized read-only. The user can
go straight to Doctor without a setup write, or consciously review and change
the ROM/BIOS roots, exit shortcut and optional import sources. The folder
browser supports SDL gamepad navigation; typed paths remain available for
keyboard users. The existing CLI validates every path before it atomically
updates configuration and imports only into Embercade-owned user data. The
Wizard checks firmware/assets through Doctor and exposes its detailed result
on request. Optional host bootstrap is launched in a terminal only after an
explicit confirmation; its existing package plan and sudo confirmation still
apply. Steam integration first performs the existing dry-run and only then
offers confirmed registration; an active Steam session can safely defer it.

The separate system-files page accepts an existing official PPSSPP `assets/`
directory (`ppge_atlas.zim`, `lang/`, `flash0/`) for PSP play and an existing
Xemu source directory containing its flash/MCPX and HDD files. No EEPROM
source is required; Xemu initializes it on the first actual start. The
same runtime checks validate these selections before setup; the PPSSPP source
is read-only and Xemu makes isolated Embercade working copies through its
existing preparation path. PSP play is marked incomplete if PPSSPP assets are
missing. On reopening, the PSP selection and already managed core/Xenia/Xemu
status are shown. Core/AppImage import source fields stay empty intentionally:
managed copies survive updates, while one-time source folders are not stored.
Going Back and then Forward preserves text entered during the current session.

This GUI never purges data. External ROM/BIOS and selected Core/AppImage
source directories remain untouched. CLI setup remains fully supported for
automation and non-graphical sessions.

The installed Wizard's existing-setup/Doctor/controller route was accepted on
Garuda/Hyprland and CachyOS Handheld/KDE. On the latter, the normal Steam entry
was separately tested in the real Gamescope session through splash, controller
menu and return to Steam. The Wizard was not tested inside Gamescope; KDE is
its validated second-host desktop path. Both hosts retained their user state
through the normal update and installed the same verified Stage payload.
In the later Garuda-only clean-install test, a user completed the expanded
Wizard, Doctor passed for PSP and Xemu, and both Xenia and Libretro-PPSSPP
played and returned to the same frontend. A normal update preserved user data;
an identical-payload dry run reported no changes. The CachyOS Handheld was not
updated as part of that follow-up.

`embercade bootstrap --dry-run` detects the distribution from
`/etc/os-release`, uses the same executable/core discovery as Doctor and prints
the complete package plan without invoking `sudo`. Package availability is
determined with read-only queries against the repositories configured on the
current host. Neither the CachyOS name nor availability on another CachyOS
machine implies that Chaotic-AUR is enabled. A normal bootstrap defaults to no
and only an explicit `y` runs an argv-based
`sudo pacman -S --needed ...`. It never runs `pacman -Syu`, invokes an AUR
helper without the separate confirmations described below, downloads
cores/providers or guesses a package for an ambiguously mapped core. Unmapped
missing cores remain visible as `CORE MISSING`.

Stable repository candidates are probed first, including PCSX2, RPCS3 and
Xemu. If absent, their exact known `-git` variants are also queried through
pacman. Only if neither repository candidate exists may an existing `paru` or
`yay` query the community candidate; community installation needs a separate
default-no confirmation. The wizard's terminal stays open after completion or
failure so package-manager errors can be read. GTK confirmations explicitly
own their parent/modal lifetime and SDL input, with No as the default.
Embercade never installs an AUR helper,
enables Chaotic-AUR or edits `/etc/pacman.conf`. Standard output uses component names;
`bootstrap --verbose` adds exact packages and commands.

Automatic package installation is limited to the exact `arch`, `cachyos` and `garuda`
distribution IDs. Other distributions remain usable but receive diagnostics
and no package-manager mutation. Packages installed through the optional
bootstrap remain owned by pacman and are never removed by Embercade uninstall
or purge.

Xenia Edge remains user-supplied. Setup checks a configured provider first and
then `$XDG_DATA_HOME/embercade/providers/xenia/`; an explicit absolute AppImage
path remains supported. Optional import creates a validated, executable copy
inside the managed provider directory. Embercade never downloads it or changes
the external source.

An unconfigured start in a graphical desktop opens the wizard; a headless
start exits with a concise `embercade setup` hint. An invalid existing TOML
is never silently replaced: the graphical path explains that it needs manual
attention.
`embercade doctor` gives a concise default summary; `--verbose` reports paths,
runtime and resource details. Doctor separates fatal runtime
damage, required collection configuration, unavailable optional system
providers and a disconnected-controller warning. One missing emulator or core
does not make the entire installation invalid.

Doctor reports the selected exit chord, RPCS3 binary and installed PS3
firmware separately, and Xemu firmware separately from its mutable EEPROM/HDD
copies. A `PS3UPDAT.PUP` file is not treated as installed firmware. Xemu uses
copy-on-first-launch firmware/HDD seeding and native EEPROM initialization in
Embercade-owned paths. Launcher
and emulator logs rotate at 8 MiB with two retained backups.

When RPCS3 is installed, a conventional user-supplied `PS3UPDAT.PUP` is in the
selected BIOS root and firmware is absent, interactive setup can open RPCS3's
normal UI with an Embercade-owned HOME and XDG directories. The user installs
firmware through RPCS3's File menu, closes it, and setup rechecks `dev_flash`.
No firmware is downloaded or copied from the PUP by Embercade. This handoff is
automated-test coverage; a fresh-firmware live run remains unvalidated.

## Uninstall and purge

`embercade uninstall` validates the installation manifest and complete payload
before removing only the immutable prefix, launcher, desktop entry, managed
hicolor icon and install metadata. Configuration, saves, state and cache are
retained. `--dry-run`
prints the exact operation list.

`embercade uninstall --purge --yes` additionally removes only the exact
Embercade-owned XDG roots. Purge rejects symlink targets and any configuration
that places a protected external ROM, BIOS or provider path inside a proposed
purge root. External content is never an installed or owned asset.
System packages installed by the optional host bootstrap are never uninstall
targets.

## Historical acceptance before 1.0 AppImage packaging

The installer, setup, doctor, dry launch, uninstall and reinstall have passed
an isolated fake-HOME/XDG test below `.work/install-test`. An explicitly
approved real user-local installation has also launched at least one game with
every currently resolved standalone provider and multiple Libretro cores. The
normal exits returned to the same frontend session, and the recorded normal
host emulator profiles remained metadata-identical. The user-local reinstall,
Doctor and visible KDE-Wayland frontend start have also passed on a second
CachyOS desktop without changing that host's system packages. Broader emulator
coverage on that host remains separate validation.

The CLI source-selection and managed-import sprint passed 307 unit tests,
runtime/frontend-library smoke, Production Stage and Doctor, offline payload
build, and `git diff --check`. The user personally completed a Garuda install
with a visible, usable menu. The managed Core directory contains 232 logical
cores, including one previously imported Nestopia build retained after a safe
same-name conflict; the 231 other selected source cores were imported. All 28
collection-required logical cores resolve from the managed directory even when
the original source is excluded from discovery. The Xenia managed copy matches
its external source by SHA-256. The updated CachyOS Handheld retained its config
hash, passed Doctor (including PPSSPP, Xemu and RPCS3), and visibly started
under Steam/Gamescope.

Provider-management polish has since passed the complete **416-test** unit
suite, runtime/frontend-library/shader smoke, Production Stage, staged and
installed Doctor, and verified offline-payload builds. Both reference hosts
used normal committed-payload updates: the managed Xenia AppImage remained
byte-identical, repeat Setup reused it, and neither host required a new
provider download or import. The installed payloads matched all 9,658 Stage
files and the same Stage manifest. Garuda and CachyOS Handheld both completed a
visible Xenia run with Select+Start cleanup and return to the same frontend;
the latter then quit normally to Steam. Theme, provider, core and PPSSPP
resource metadata survived the second-host update. Config/save metadata
changed only during its subsequent visible Xenia session, so those entire
trees are not claimed byte-identical after gameplay.

## Deferred product work

The current installer is functional private infrastructure, not a stable
public installer claim. Private AppImage packaging is implemented as described
above; Embercade does not install into `/usr` or download providers. Its only automated package-manager path is
the separate, confirmed Arch/CachyOS/Garuda bootstrap described above.
Branding resources, desktop icon, native splash and optional native Steam
shortcut/artwork registration are integrated. Flatpak Steam host-launcher access
and public release packaging remain later work. The repository audit has been
completed;
`PUBLIC_RELEASE_AUDIT.md` records the unresolved project and resource-license
blockers that must be closed before publication.

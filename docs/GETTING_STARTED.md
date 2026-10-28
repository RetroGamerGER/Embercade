# Getting started with Embercade

Download the AppImage, complete matching sources and checksums from the
[Embercade 1.0 release](https://github.com/RetroGamerGER/Embercade/releases/tag/v1.0.0).
There is no automatic internet updater. This guide covers the AppImage and
user-local checkout installation.

## Before you start

**The installer currently supports Arch Linux, CachyOS and Garuda only.**
Automatic host-software installation uses `pacman`. Debian/Ubuntu, Fedora and
other distributions are not supported by the current installer. Other
Arch-derived distribution IDs are not automatically enabled either.

On unsupported systems the graphical installer explains the platform limit
before opening an installation terminal or asking for package confirmation.
The command-line package runner independently rejects unsupported distro IDs.

The current runtime targets x86-64 Linux and requires host CPython 3.14 at
`/usr/bin/python`, Bubblewrap and compatible desktop libraries. The graphical
wizard uses GTK3/PyGObject. The AppImage does not bundle Python or graphics drivers.
Read the [AppImage host requirements](APPIMAGE.md#bundle-and-host-boundary)
for the complete boundary; other distributions and GPUs are not yet confirmed.

Provide your own legally obtained games, BIOS and system files, plus compatible
emulators and Libretro cores. These are not included in Embercade. The optional
package helper can propose host packages on Arch, CachyOS and Garuda; importing
known external AppImages always requires your own copy. See
[provider requirements](PRODUCTION.md#known-appimage-safety).

## Reuse a RetroBat or Batocera library

Select your existing game collection in setup. For recognized system folders,
Embercade reads compatible `gamelist.xml` files and uses their supported game
metadata and artwork references. You do not need to scrape those entries again
when the referenced files are accessible to Embercade on Linux. Setup preserves existing
game lists and media rather than replacing them with an empty library.

Keep each system's game list and media with its games. Relative references such
as `./images/game.png` can remain valid when that folder moves together.
Windows drive letters and old absolute paths may need adjusting, and the system
folder names and game formats must match Embercade's supported catalog. This
does not promise automatic Windows-path conversion or compatibility with every
RetroBat-specific metadata field or setting. Check a representative system
before moving a whole collection. See [system compatibility](COMPATIBILITY_1_0.md).

The ROM and BIOS files themselves are not modified. The frontend can update
`gamelist.xml`, including metadata changes, and save scraped media in `images/`,
`videos/`, `manuals/` and `magazines/` where storage permissions allow it. Those
are the writable collection destinations; the surrounding game folders stay
read-only inside Embercade. See [metadata and media writes](SCREENSCRAPER.md#metadata-and-media-writes).

## Start a private AppImage

Keep the image, checksum and manifest together in a local folder. Use your
build's actual filename in place of the example below. If a network share does
not allow execution, copy the files locally first.

```sh
sha256sum -c Embercade-1.0-x86_64.AppImage.sha256
chmod +x Embercade-1.0-x86_64.AppImage
./Embercade-1.0-x86_64.AppImage
```

An unconfigured start opens the setup wizard in a desktop session. A configured
start opens your library. AppImage commands use the image as the launcher:

```sh
./Embercade-1.0-x86_64.AppImage wizard
./Embercade-1.0-x86_64.AppImage doctor
```

The wizard can create a Games-menu entry and a durable local AppImage copy.
Use desktop mode for setup; wizard usability inside Gamescope is unconfirmed.
The AppImage and classic install share Embercade user data by default, so use
them one at a time. See [AppImage state and coexistence](APPIMAGE.md#state-first-run-and-coexistence).

## Install from a checkout

This is the development installation path. It needs the pinned build inputs
and reference sources described in [upstream documentation](UPSTREAM.md).
Production builds also need the private ScreenScraper build input described
in the [production-build notes](SCREENSCRAPER_PRODUCTION_FIX.md). That is a
builder requirement, not something an AppImage user needs to configure.

From the repository root:

```sh
./scripts/stage-build
./scripts/install-user --dry-run
./scripts/install-user
```

The dry run checks the verified stage and previews the install. The installer
does not use sudo. Application files go under `$HOME/.local/lib/embercade`,
with the launcher in `$HOME/.local/bin` and desktop integration in your XDG
data directory. Follow the installer's PATH guidance if `embercade` is not
found by your shell.

After installation:

```sh
embercade wizard
embercade doctor
embercade
```

The first interactive install opens the wizard automatically. `embercade setup`
is the terminal alternative. For private AppImage packaging, use the separate
[build instructions](APPIMAGE.md#build-verify-and-reproduce).

## First-time setup

The English/German wizard records your existing game and BIOS locations,
offers core/provider imports and a controller exit shortcut, and checks the
result. It can also help with Xbox system files, isolated PS3 firmware setup
and optional desktop/Steam entries. The [installer guide](FINAL_POLISH.md#installer-and-state-contracts)
describes those steps and their limits.

- For PSP, supply the complete official PPSSPP `assets/` folder.
- For Xemu, supply your flash/MCPX and HDD files. A pre-existing EEPROM is not
  required; Xemu can initialize Embercade's isolated copy.
- Xenia Edge and shadPS4 use your own AppImages through the known-provider
  importer. They are not bundled or downloaded by Embercade.
- Enter an optional personal ScreenScraper account in the frontend Accounts
  menu. Installation and game launch do not require an account or developer file.
- Close Steam fully before registering or retargeting its shortcut. See
  [Steam integration](STEAM_INTEGRATION.md) for previews, backups and limits.

ROM and BIOS files stay read-only. Game lists and media can be updated in the
designated destinations described under [library reuse](#reuse-a-retrobat-or-batocera-library).
Generated settings and saves use Embercade's own directories, separate from
your usual emulator profiles. See [state and account storage](STATE_AND_SECRETS.md)
and [scraper writes](SCREENSCRAPER.md#metadata-and-media-writes).

On Arch, CachyOS and Garuda, you can preview and request a host package plan:

```sh
embercade bootstrap --dry-run
embercade bootstrap
```

This is separate from installing Embercade. It asks before changing packages,
does not run a system upgrade, enable repositories or install an AUR helper.
On other distributions it provides diagnostics only.

## Configuration and diagnostics

The configuration file is `$XDG_CONFIG_HOME/embercade/embercade.toml`, or
`~/.config/embercade/embercade.toml` when `XDG_CONFIG_HOME` is unset. A minimal
example is:

```toml
[paths]
roms = "/path/to/roms"
bios = "/path/to/bios"

[controller]
exit_hotkey = "back-start"
```

Use Doctor to check the runtime, collection paths, controllers, cores and
emulators. Optional systems can be missing without the application itself
being damaged.

```sh
embercade doctor
embercade doctor --verbose
embercade system-coverage --output system-coverage.json
```

Coverage inspects the pinned catalog and host runtime without launching games.
`PREPARED` describes a structurally checked route; only real gameplay and
exit/return evidence establishes `READY`. See [compatibility](COMPATIBILITY_1_0.md).
The [ScreenScraper production fix](SCREENSCRAPER_PRODUCTION_FIX.md) and
[RetroArch startup fix](RETROARCH_STARTUP_FIX.md) document the latest repairs
and the difference between automated probes and user-confirmed results.

## Updates and removal

Close Embercade before updating. For an AppImage, replace the closed executable
at its durable location, keeping the previous image and sidecars for rollback.
There is no built-in download service. See [AppImage updates](APPIMAGE.md#steam-and-update).

For a checkout installation, build the new stage, preview and apply it:

```sh
./scripts/stage-build
./scripts/install-user --dry-run
./scripts/install-user
embercade doctor
```

An offline bundle uses `./install --dry-run` and `./install`. An identical
verified payload is a no-op. Normal updates preserve configuration, saves,
themes, imported cores/providers and external collection references. They do
not repeat first-run setup. `EMBERCADE 1.0` is the product label; `0.1.dev0`
remains the internal packaging version, not a way to compare update age.
See [installation and update internals](PRODUCTION.md#user-local-installation).

For a classic installation:

```sh
embercade uninstall --dry-run
embercade uninstall
```

Normal uninstall removes managed program files and retains user data.
`embercade uninstall --purge --yes` is a separate destructive operation on
Embercade-owned XDG data; external collections and host packages are not its
targets. See [Production](PRODUCTION.md) for ownership and refusal rules.

## Development checks

With the runtime prepared, run these from the repository root:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
./scripts/runtime-smoke
git diff --check
```

For the isolated development frontend, copy `config/dev-roms.example.tsv` to
`.work/dev-roms.tsv` and replace its placeholders with your own content paths:

```sh
./scripts/dev-prepare
./scripts/dev-run
```

Host inventories, logs and development reports belong under ignored `.work/`;
they are not public compatibility claims. The [desktop UI](DESKTOP_UI.md),
[launcher runtime](RUNTIME.md) and [technical state](PROJECT_STATE.md) explain
the implementation. License and asset clearance remain separate from these
checks; see the [public-release audit](PUBLIC_RELEASE_AUDIT.md).

# Embercade 1.0

Embercade brings a familiar, controller-friendly emulation frontend to your
existing Linux desktop. It uses Batocera's EmulationStation and configuration
system while keeping emulator profiles, settings and saves in its own user
folders. Your Linux installation stays your Linux installation.

This is the first public release of Embercade.
[Downloads, matching sources and checksums](https://github.com/RetroGamerGER/Embercade/releases/tag/v1.0.0)
are provided together.

## What is included

- A German and English setup wizard with language selection first, native folder
  selection, ROM/BIOS configuration and optional host-software installation.
- Controller and hotkey setup, including the confirmed xpadneo compatibility
  flow and Start + Guide return to the frontend.
- Desktop and Steam integration that preserves existing settings during updates.
- ScreenScraper integration ready to use with your own ScreenScraper account.
- RetroAchievements login for supported emulators, plus an optional personal
  Web API key for frontend achievement lists and progress. The key is masked,
  supports Paste/Ctrl+V and is stored locally with owner-only permissions.
  No shared personal RetroAchievements key is distributed.
- Official RetroBat decorations, filtered to the choices available for each
  system. Original credits and notices are retained.
- Optional shaders supplied by the host's `libretro-shaders-slang` package.
  Effects are off by default. Compatible Linux routes prefer Vulkan while
  preserving manual settings and necessary core exceptions.
- Frontend game-video playback with the required host VLC decoder checks.
- Correct C64 D64 startup with VICE's embedded stock ROMs by default. Optional
  JiffyDOS is available through explicit configuration rather than forced on.

ROMs, BIOS/firmware, console keys, emulator binaries and Libretro cores are
user-supplied. Scraped media and downloaded themes stay in the user's library.

## Supported installer systems

**The current installer supports Arch Linux, CachyOS and Garuda only.**
It uses `pacman` for automatic host-software installation. Other distributions,
including Debian/Ubuntu and Fedora, are not currently supported. Other
Arch-derived distribution IDs are not automatically enabled. An unsupported
host cannot execute the package installation, even if pacman is present.

On unsupported systems the graphical installer explains the platform limit
before opening an installation terminal or asking for package confirmation.
The command-line package runner independently rejects unsupported distro IDs.

## Download files

The release assets contain:

- `Embercade-1.0-x86_64.AppImage`
- `Embercade-1.0-x86_64.AppImage.sha256` and `Embercade-1.0-x86_64.manifest.json`
- `Embercade-1.0-sources-and-notices.tar.gz` with complete matching covered sources
- `Embercade-1.0-public-source.bundle` with the clean, standalone project history
- `Embercade-1.0-sources.manifest.json`, `BUILD_INFO.json`, `RELEASE_NOTES.md`,
  `PUBLICATION_HANDOFF.md` and `SHA256SUMS`

Check the downloaded files, then run the AppImage:

```sh
sha256sum -c SHA256SUMS
chmod +x Embercade-1.0-x86_64.AppImage
./Embercade-1.0-x86_64.AppImage
```

A first start opens the setup wizard. Existing users keep their configuration.
Enter the optional RetroAchievements Web API key separately on each computer
if you want the frontend progress views. Normal emulator achievements use the
existing login independently.

## Tested systems and known limits

The owner accepted the functional build on Garuda KDE MainRig, the NVIDIA
Garuda KDE laptop, and CachyOS/Gamescope WohnzimmerPC. This establishes those
reported test environments, not every Linux distribution, GPU or game.

**The laptop's known 16:10 bezel cropping/proportion issue remains.** It affects
the artwork layout and has not been declared fixed. Keep this limitation in the
public release description. The confirmed 16:9 reference setups remain accepted.

The supported-host build requires compatible host CPython 3.14 at
`/usr/bin/python`, GTK3/PyGObject, Bubblewrap, FUSE 2, audio/graphics libraries,
and the documented optional host components. This is not a generic bundled
Linux runtime. The optional package installer supports configured Arch-family
repositories; it does not enable third-party repositories for you.

The public build updates privacy, release documentation, packaging and the
visible installer platform notice. Package commands and emulator behavior are
unchanged. The final build report records the exact source, payload comparison and package
checks against the accepted functional candidate. It does not claim a new
interactive acceptance run on the final packaging bytes.

## Licenses and source access

Independent Embercade code uses PolyForm Noncommercial 1.0.0. Original Embercade
text and branding use CC BY-NC-SA 4.0 for rights held. Batocera, EmulationStation,
RetroBat artwork, Carbon and other dependencies keep their individual licenses
and credits. The noncommercial terms do not restrict GPL/LGPL/MIT recipients'
upstream rights. Embercade is source-available; PolyForm is not an OSI
open-source license.

Keep the matching source/notice archive available beside the binary. The
automatic project-only GitHub source archive does not replace it. Full license
routing, original texts and rebuild/replacement instructions are included.

## Build identity

The AppImage and its complete corresponding source archive remain the verified
candidate built from [`cb00b093`](https://github.com/RetroGamerGER/Embercade/tree/cb00b093ff0e87d2462ee060bb4b7717afda43dc).
The release tag also includes the final publication-documentation update;
no runtime, emulator, shader, bezel or installer behavior changed after the
recorded 849 passing tests (five expected opt-in skips). The source bundle
contains the exact clean build source; BUILD_INFO records the separate
publication-documentation commit. Build/source manifests retain their original
preparation-time state as an immutable build record.

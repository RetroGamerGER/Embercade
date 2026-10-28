# Embercade 1.0 — historical private release

This document records the private 25 October build and its conditions at that
time. It is not the current public candidate or its clearance status. For the
prepared first public release, see [current release notes](PUBLIC_RELEASE_1_0.md).
Keep the old private tag/assets separate from that preparation.

Published on 25 October 2026:
[Release v1.0.0](https://github.com/RetroGamerGER/Embercade/releases/tag/v1.0.0).
Access requires permission to the private repository. All five uploaded asset
digests reported by GitHub match the verified local files; the two tagged
source archives are also available.

First **private** GitHub release for x86-64 Linux. This release uses the exact
AppImage tested and confirmed by the owner. The repository stays private;
public redistribution remains subject to the existing rights and license gates.

## Included

- English/German setup wizard with native folder selection, controller and
  hotkey setup, optional host-software installation, Xbox/PS3 preparation and
  desktop/Steam integration.
- Emulator settings and saves isolated from normal host profiles, with managed
  imports for user-supplied cores and supported external emulator AppImages.
- Working ScreenScraper application integration. Users enter their own account
  in the frontend; no local developer configuration is needed.
- Faster RetroArch startup on KDE by disabling its additional desktop companion
  by default, while retaining the in-game menu and explicit user overrides.
- Compatible automatic graphics selection: prefer detected Vulkan, retain
  necessary core exceptions and existing manual settings.
- Fourteen complete optional shader presets. **Shaders are off by default**
  and activate only after the user chooses one. Missing or incompatible preset
  formats no longer cancel the game before emulator startup.

ROMs, BIOS/firmware, console keys, emulator binaries and Libretro cores are not
included in this AppImage. Supply your own legally obtained files and supported
host emulators.

## Download and run

Download `Embercade-1.0-x86_64.AppImage` and its matching
`Embercade-1.0-x86_64.AppImage.sha256` into the same local folder:

```sh
sha256sum -c Embercade-1.0-x86_64.AppImage.sha256
chmod +x Embercade-1.0-x86_64.AppImage
./Embercade-1.0-x86_64.AppImage
```

A fresh profile opens the setup wizard. Normal application updates preserve
existing settings and data. Keep original game and BIOS folders separate from
Embercade's working data.

The supported-host build requires **CPython 3.14 at `/usr/bin/python`**,
GTK3/PyGObject, Bubblewrap, FUSE 2 and compatible desktop/audio/graphics libraries.
Python and GPU drivers are host-provided. See
[host requirements](APPIMAGE.md) and [getting started](GETTING_STARTED.md).
The existing optional host installer supports Arch, CachyOS and Garuda, asks for
confirmation and requires working configured package repositories.

## Verification and build identity

- Tag: `v1.0.0`.
- Exact build/tag source: `3430484d564d7ff58fa278c7e9de25391f5de754`.
- AppImage SHA-256:
  `233f17457379dd679eb8a4ef595999e273dd035d52fc88ce49a83c3b0a623efd`.
- Image size: 279,116,280 bytes.
- 781 automated tests: **776 passed, five intended skips**; all 52 structural
  routes and 25 GTK checks passed.
- Actual-image 3DO, Game Boy, SNES and N64 starts passed with effects off;
  optional shader activation was separately tested. All 14 presets and their
  142 dependencies are present, with GPU compilation evidence for every preset.
- The owner confirmed successful personal use of the delivered candidate.

The release image is a filename alias of the tested AutoGraphics build; its
bytes are unchanged. The external manifest changes only `image.filename` to
match the release asset. `BUILD_INFO.json` records the original manifest hash,
alias, source pins and validation. `SHA256SUMS` checks all four supplied files.
GitHub provides source ZIP/tar archives from the exact tag. Current `master`
also contains later acceptance/rollback documentation and a patch-context
formatting fix proven to generate identical program bytes.

The frontend product version is 1.0. The internal Python bridge keeps its
existing `0.1.dev0` identifier; this is not a PyPI package release.

## Known limits

The tests establish the recorded startup/rendering routes, not compatibility
with every game, GPU or distribution. Full NVIDIA, other-compositor,
standalone-emulator gameplay and exceptional-effect popup acceptance retain
their documented limits. See [graphics validation](LINUX_GRAPHICS_AND_SHADERS.md)
and [system compatibility](COMPATIBILITY_1_0.md).

A later fresh host-package installation attempt failed with exit 1 before
installing emulators and was rolled back at the owner's request. Its download/
repository failure has not been diagnosed or fixed by this release.

Public source/binary redistribution is **not cleared**. Project-license scope,
asset rights/attribution and complete source/notice delivery remain unresolved;
the decoration-rights investigation remains paused. This private release does
not activate a new blanket license. See [the public-release audit](PUBLIC_RELEASE_AUDIT.md).

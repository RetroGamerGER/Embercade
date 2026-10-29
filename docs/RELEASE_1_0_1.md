# Embercade 1.0.1 – Guided Setup Update

Embercade 1.0.1 makes the first setup easier to follow. The new [Getting Started guide](GETTING_STARTED.md) walks through the wizard with 13 real screenshots, from allowing the AppImage to run to opening your library. Existing installations keep their settings.

## What changed

- PSP and Xbox system-file folders can remain empty during general setup. **Skip for now** discards unfinished selections while preserving saved working settings. The games and BIOS folders still need to be selected first.
- Automatic host-software setup recognizes Arch ancestry from `ID`/`ID_LIKE` and checks for Pacman before package actions. It uses existing repositories and optional existing `paru`/`yay` helpers, with explicit installation confirmation. It does not configure Chaotic-AUR or another helper.
- The installer uses the shorter notice: **Installer supports Arch-based Linux distributions.**
- The graphical beginner guide now has a linked [advanced guide](ADVANCED_USAGE.md) for source installation, CLI checks, updates, removal and development.

## Download and update

Download **Embercade-1.0.1-x86_64.AppImage** from [release v1.0.1](https://github.com/RetroGamerGER/Embercade/releases/tag/v1.0.1). Follow [Getting Started](GETTING_STARTED.md) to allow execution and open it. Close Embercade before replacing a durable AppImage path; keep the old file for rollback. Normal updates preserve settings, saves, themes and managed user data.

The x86-64 supported-host AppImage requires CPython 3.14 at `/usr/bin/python`, GTK3/PyGObject and compatible host libraries. Games, BIOS/firmware, emulators and Libretro cores are not bundled. The UI keeps the **Embercade 1.0** product branding; **v1.0.1** identifies this update.

The functional baseline was accepted on Garuda KDE/Wayland and CachyOS Handheld with Steam/Gamescope. EndeavourOS/Arch-family recognition has automated coverage; it is not a new full installation or GPU/gameplay acceptance. The known **16:10 bezel cropping/proportion limitation** remains.

## Sources and licenses

The release includes the matching complete source/notice archive, exact source manifest and checksums. GitHub's automatic source ZIP alone does not include covered upstream sources. Independent Embercade code uses PolyForm Noncommercial 1.0.0; upstream GPL/LGPL/MIT and other terms remain unchanged. See [source access](SOURCE_ACCESS.md) and [licenses](../LICENSE).

The v1.0.0 release and its original assets remain available unchanged. This update does not install host packages or change controller drivers during publication.

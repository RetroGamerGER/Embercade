# Embercade 0.1 Compatibility Matrix

Batocera reference: `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`.

This is the historical 0.1 inventory/matrix. Targeted systems added during
1.0 development, including 3DO, are tracked separately in
[COMPATIBILITY_1_0.md](COMPATIBILITY_1_0.md); they are not silently counted as
part of the older full collection snapshot below.

This host snapshot combines the existing ROM, BIOS and Libretro-core inventories with PATH and configured external-provider discovery plus Embercade's explicit launch capability ledger. No emulator was started while generating this report. READY is reserved for manually confirmed end-to-end routes.

Duplicate collection directories for the same Batocera system ID are combined into one row. Host paths and local collection-directory names remain in ignored reports and are deliberately omitted here.

## Summary

- ROM-relevant systems: 45
- READY: 39
- UNTESTED: 1
- CORE_MISSING: 0
- EMULATOR_MISSING: 4
- EMBERCADE_PORT_MISSING: 0
- BIOS_MISSING: 0
- AMBIGUOUS: 0
- UNSUPPORTED: 1

## Systems

| System | Collection | Default emulator | Default core | BIOS | Host core | Host emulator | Embercade | Dry run | E2E | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| 3ds | ROM_PRESENT | azahar | azahar | NOT_REQUIRED | n/a | no | yes | yes | yes | **READY** |
| amiga1200 | ROM_PRESENT | libretro | puae | SATISFIED | yes | yes | yes | yes | yes | **READY** |
| amigacd32 | ROM_PRESENT | libretro | puae | SATISFIED | yes | yes | yes | no | yes | **READY** |
| atari2600 | ROM_PRESENT | libretro | stella | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| atari5200 | ROM_PRESENT | libretro | atari800 | SATISFIED | yes | yes | yes | no | yes | **READY** |
| atari7800 | ROM_PRESENT | libretro | prosystem | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| c64 | ROM_PRESENT | libretro | vice_x64 | NOT_REQUIRED | yes | yes | yes | yes | yes | **READY** |
| dos | ROM_PRESENT | libretro | dosbox_pure | NOT_REQUIRED | yes | yes | yes | yes | yes | **READY** |
| dreamcast | ROM_PRESENT | libretro | flycast | SATISFIED | yes | yes | yes | no | yes | **READY** |
| gamecube | ROM_PRESENT | dolphin | dolphin | SATISFIED | n/a | yes | yes | no | yes | **READY** |
| gamegear | ROM_PRESENT | libretro | genesisplusgx | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| gb | ROM_PRESENT | libretro | gambatte | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| gba | ROM_PRESENT | libretro | mgba | SATISFIED | yes | yes | yes | no | yes | **READY** |
| gbc | ROM_PRESENT | libretro | gambatte | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| jaguar | ROM_PRESENT | bigpemu | bigpemu | NOT_REQUIRED | n/a | no | yes | yes | yes | **READY** |
| mame | ROM_PRESENT | libretro | mame078plus | NOT_REQUIRED | yes | yes | yes | yes | yes | **READY** |
| mastersystem | ROM_PRESENT | libretro | genesisplusgx | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| megacd | ROM_PRESENT | libretro | genesisplusgx | SATISFIED | yes | yes | yes | no | yes | **READY** |
| megadrive | ROM_PRESENT | libretro | genesisplusgx | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| mrboom | ROM_PRESENT | libretro | mrboom | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| n64 | ROM_PRESENT | mupen64plus | glide64mk2 | NOT_REQUIRED | n/a | no | yes | yes | yes | **READY** |
| nds | ROM_PRESENT | libretro | melonds | SATISFIED | yes | yes | yes | yes | yes | **READY** |
| neogeo | ROM_PRESENT | libretro | fbneo | SATISFIED | yes | yes | yes | no | yes | **READY** |
| neogeocd | ROM_PRESENT | libretro | neocd | SATISFIED | yes | yes | yes | no | yes | **READY** |
| nes | ROM_PRESENT | libretro | fceumm | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| ngpc | ROM_PRESENT | libretro | mednafen_ngp | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| odcommander | ROM_PRESENT | odcommander | odcommander | NOT_REQUIRED | n/a | no | no | no | no | **EMULATOR_MISSING** |
| pcengine | ROM_PRESENT | libretro | pce | SATISFIED | yes | yes | yes | no | yes | **READY** |
| pcenginecd | ROM_PRESENT | libretro | pce | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| ports | ROM_PRESENT | sh | sh | NOT_REQUIRED | n/a | yes | no | no | no | **UNSUPPORTED** |
| prboom | ROM_PRESENT | libretro | prboom | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| ps2 | ROM_PRESENT | pcsx2 | pcsx2 | SATISFIED | n/a | yes | yes | no | yes | **READY** |
| ps3 | SPECIAL_LAYOUT_PRESENT | rpcs3 | rpcs3 | SATISFIED | n/a | yes | yes | no | yes | **READY** |
| psp | ROM_PRESENT | ppsspp | ppsspp | NOT_REQUIRED | n/a | no | yes | yes | yes | **READY** |
| psvita | ROM_PRESENT | vita3k | vita3k | SATISFIED | n/a | no | no | no | no | **EMULATOR_MISSING** |
| psx | ROM_PRESENT | libretro | pcsx_rearmed | SATISFIED | yes | yes | yes | no | yes | **READY** |
| pygame | ROM_PRESENT | pygame | pygame | NOT_REQUIRED | n/a | no | no | no | no | **EMULATOR_MISSING** |
| saturn | ROM_PRESENT | libretro | beetle-saturn | SATISFIED | yes | yes | yes | no | yes | **READY** |
| sdlpop | ROM_PRESENT | sdlpop | sdlpop | NOT_REQUIRED | n/a | no | no | no | no | **EMULATOR_MISSING** |
| sega32x | ROM_PRESENT | libretro | picodrive | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| snes | ROM_PRESENT | libretro | snes9x | NOT_REQUIRED | yes | yes | yes | no | yes | **READY** |
| wii | ROM_PRESENT | dolphin | dolphin | NOT_REQUIRED | n/a | yes | yes | yes | no | **UNTESTED** |
| wiiu | ROM_PRESENT | cemu | cemu | NOT_REQUIRED | n/a | no | yes | no | yes | **READY** |
| xbox | ROM_PRESENT | xemu | xemu | SATISFIED | n/a | yes | yes | no | yes | **READY** |
| xbox360 | ROM_PRESENT | xenia-edge | xenia-edge | NOT_REQUIRED | n/a | no | yes | no | yes | **READY** |

## Prepared capabilities

- `wii`: launch path **PREPARED**; special controller validation **PENDING**. Desktop Dolphin generation is isolated; real Wiimote, Nunchuk, MotionPlus, IR, Sensor Bar, DolphinBar and Bluetooth passthrough remain unvalidated.

## Missing standalone emulators

- `odcommander`: odcommander
- `pygame`: pygame
- `sdlpop`: sdlpop
- `vita3k`: psvita

## Missing Libretro cores

None among the ROM-relevant Batocera defaults.

## Likely small Embercade ports

None.

These conservative candidates use comparatively direct Libretro routes, have the currently known host prerequisites, and are closest to the proven NES path. They still require a real Embercade route and end-to-end validation; the label is a prioritization hint, not a compatibility claim.

## End-to-end proven

`3ds`, `amiga1200`, `amigacd32`, `atari2600`, `atari5200`, `atari7800`, `c64`, `dos`, `dreamcast`, `gamecube`, `gamegear`, `gb`, `gba`, `gbc`, `jaguar`, `mame`, `mastersystem`, `megacd`, `megadrive`, `mrboom`, `n64`, `nds`, `neogeo`, `neogeocd`, `nes`, `ngpc`, `pcengine`, `pcenginecd`, `prboom`, `ps2`, `ps3`, `psp`, `psx`, `saturn`, `sega32x`, `snes`, `wiiu`, `xbox`, `xbox360`

NES is implemented with Nestopia; `fceumm` remains the pinned Batocera catalog default shown in the table. Both host cores are present in this snapshot.

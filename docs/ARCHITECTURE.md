# Architecture

The intended 0.1 flow is:

```text
Batocera EmulationStation
  -> Embercade desktop runtime and path compatibility
  -> batocera-launch 44
  -> modern plugin or configgen fallback
  -> host-provided emulator
  -> synchronous return to EmulationStation
```

`paths.py` is the single source of truth for persistent locations.
`executables.py` resolves host emulators without fixed `/usr/bin` assumptions.
For generic Libretro launches, the pinned Batocera configuration stack selects
the logical emulator/core, Embercade resolves the exact host core library, and
the existing configgen path writes only isolated XDG configuration before
starting host RetroArch. `display.py` describes the inherited desktop session
and explicitly does not support resolution switching.

PlayStation uses this same route with Batocera 44's `mednafen_psx` identity,
resolved to the host's hardware-capable `mednafen_psx_hw_libretro.so` and
Vulkan. Batocera's pinned `pcsx_rearmed` default remains visible as an
alternative, but is not the validated Embercade route on this host. The 0.1
proof deliberately covers a single-disc CHD only. CUE/BIN, CCD/IMG/SUB, M3U,
multi-disc and SBI/LibCrypt content still require separate regression tests and
are not silently normalized by Embercade.

The development harness uses Bubblewrap solely to satisfy the current upstream frontend's compiled-in `/userdata` and `/usr/share/emulationstation` paths. It binds the sibling references read-only and maps `/userdata` to ignored project-local data under `.work/dev`. This is a development bridge, not the long-term architecture.

No TDP, power, rotation, DRM/KMS, update, service, storage, Kodi, wireless, special-controller or overlay filesystem feature is implemented.

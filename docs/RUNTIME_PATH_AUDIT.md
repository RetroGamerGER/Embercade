# Batocera 44 runtime path audit for the first NES test

This list covers the imported Launcher/Configgen/Libretro path, not every emulator plugin shipped by Batocera.

| Upstream path or assumption | Classification | Embercade action before NES |
| --- | --- | --- |
| `/userdata` and derived configs, saves, BIOS, ROMs, cache, logs | Path-provider replacement | Blocker: connect `batocera_common.paths` and Configgen string literals to Embercade XDG/ROM/BIOS roots. |
| `/usr/share/batocera/launch/defaults` | Package data | Blocker: materialize the minimal x86_64 launcher defaults in the project/runtime resource tree. |
| `/usr/share/batocera/configgen` | Package data | NES probably needs little or none; prove from the selected core before copying data. |
| `/usr/share/emulationstation/resources/gamesdb.xml` | Package data | Provide from the pinned ES reference or make metadata absence explicit. |
| `/usr/bin/retroarch` | Host executable resolver | Blocker: replace with the already implemented resolver result. |
| `/usr/lib/libretro` | Host resource discovery | Blocker: discover the selected host core location rather than assume Batocera layout. |
| `/usr/share/libretro/info` and `/usr/share/libretro/assets` | Host/package resource discovery | Blocker: resolve host paths or explicitly disable optional assets. |
| `/usr/share/batocera/shaders` | Package data / optional capability | No-op is acceptable for the first unshaded NES smoke test; later map to Embercade shader resources. |
| `/var/run/batocera-launch.perf` | Runtime path | Blocker for a real CLI invocation: route profiler output to Embercade runtime/state. |
| `/var/run/hud.config`, `/var/run/shader_bezels` | MVP no-op or runtime path | Disable HUD/bezel generation initially or map to Embercade runtime. |
| `/var/run/evmapy*`, `/usr/share/evmapy`, `/usr/bin/hotkeygen` | MVP no-op | Do not enter these paths for the first test; hotkeygen and evmapy are explicitly deferred. |
| `/var/run/squashfs`, `/var/run/overlays` | MVP no-op | Capability-disable; neither filesystem feature is needed for NES. |
| `/var/run/rk-rotation`, `/usr/bin/glxinfo`, video mode helpers | MVP no-op | Inherit the Wayland desktop geometry; do not invoke rotation or mode switching. |
| `/usr/bin/batocera-bezel-overlay` | MVP no-op | Disable external bezel compositor for the first test. |
| hard-coded `/userdata/...` strings written into RetroArch configuration | Path-provider replacement | Blocker: constants alone are insufficient; `libretroRetroarchCustom.py`, `libretroConfig.py`, and relevant generator branches need compatibility inputs. |

The imported package also registers every Batocera emulator plugin, including many hard-coded `/usr/bin` paths. Registration/import does not execute them. They are outside the RetroArch-only 0.1 path and must not drive broad premature patching.


# Batocera desktop UI layer

Embercade's development frontend is built from the pinned
Batocera-EmulationStation commit in `upstream.lock`; it is not ES-DE with a
synthetic system list. All generated and compiled artifacts stay below
`.work/ui`.

## Data provenance

- `es_systems.cfg` and `es_features.cfg` are generated from the pinned
  Batocera 44 `batocera-es-system` package and the real `_global`, `_shared`,
  libretro and the selected core descriptors for NES plus Embercade's simple
  generic Libretro test systems.
- Nestopia is marked as the desktop default. FCEUmm and Mesen remain visible as
  authentic Batocera core choices. Historical 0.1 acceptance used the installed
  Nestopia core; current routes are tracked in `COMPATIBILITY_1_0.md`.
- `es_input.cfg` and `es_savestates.cfg` come directly from the pinned Batocera
  commit.
- EmulationStation resources and locale sources come directly from the pinned
  EmulationStation commit. German and British-English message catalogs are
  compiled locally under `.work/ui`.
- The Carbon package selected by both the captured Batocera 43.1 bundle and the
  pinned Batocera 44 source is commit
  `b921e1734d88d6bc7b9e8cb97dd8f8b91ba2058a`. The captured theme is therefore
  reused read-only.
- The pinned and captured `gamesdb.xml`, `arcaderoms.xml` and `genres.xml` are
  byte-identical (SHA-256 respectively `344381877e9dc16140266f2be3a6f07c46d962d6b295361f945827e3e745ed1a`,
  `9efac5e042a4660a27d3aa430f6d86bbffe7bfd98572959bae10233debd40887`,
  and `cc8329fb7ac1b7e08bc2db2ba2a0efa57c71252cb8ae8d63099460c2cbd5927d`).
- The consoles decoration set remains exposed read-only from the captured
  Batocera bundle. Shader configuration sets are generated from Embercade's
  curated catalog over the complete official Libretro `slang-shaders` source
  pinned in `runtime/shaders.lock`. The staged tree is self-contained and does
  not use a host RetroArch shader directory. Generated emulator files and user
  choices remain in Embercade-owned paths.

## Data-driven menus

Batocera-EmulationStation builds emulator/core selection, Advanced System
Options and per-game options from `es_systems.cfg` plus `es_features.cfg`.
The generated system data includes the upstream aspect-ratio, shader,
smoothing, integer scaling, decoration, latency, controller and core-specific
options. All simple Libretro test systems share one system-aware Embercade
wrapper; their effective emulator and core are still resolved from Batocera's
configuration. The desktop generator removes appliance-only power, display
and special-hardware controls.

The development catalogue reads local test roots and selected Libretro paths
from the ignored `.work/dev-roms.tsv` manifest. It exposes read-only symlinks
below `.work/ui/libretro-test-roms`; ROM contents are neither copied nor
changed. `config/dev-roms.example.tsv` contains path-neutral placeholders. The
configured external ROM and BIOS roots are mounted read-only into the
Bubblewrap test session.

Shader and decoration selectors additionally use `ApiSystem` to enumerate
the directories exposed at `/usr/share/batocera/shaders/configs` and
`/usr/share/batocera/datainit/decorations`. They do not require a Batocera
service. The shader directory contains only the curated Embercade mapping
folders plus the default mapping, so the full upstream resource tree does not
turn into hundreds of menu entries. Update, install, network, Bluetooth,
audio-device, resolution,
overclock and service menus depend on Batocera helper executables and remain
unavailable in the isolated desktop environment.

The Theme Library is an exception to helper-driven appliance installers: its
pinned `ApiSystem` catalogue, preview, ZIP download and extraction code runs
in the frontend itself. Production prepares persistent writable XDG themes and
their temporary workspace while keeping Carbon and Embercade product branding
read-only. See [PRODUCTION.md](PRODUCTION.md#theme-library-and-persistent-user-themes)
for the installed path contract and current acceptance boundary.

Batocera's configuration-name model already supplies the hierarchy used by
the menus: global, system, folder and game values are written as keys in the
same `batocera.conf`. Embercade maps `/userdata/system/batocera.conf` to the
single launcher-owned file below `.work/e2e-xdg/config/embercade` so frontend
and configgen read and write the same configuration.

## Desktop policy

`resources/policy/desktop-capabilities.conf` is the source of truth for the
four states `supported`, `unsupported`, `hidden`, and `desktop-managed`.
`scripts/dev-run` exports the validated result to the frontend. The small
EmulationStation patch only handles policy that resources cannot express:
the appliance System Settings tree is hidden, Quit offers a normal
EmulationStation exit instead of reboot, suspend or shutdown, and the startup
splash stays independent of theme XML. The global menu footer/subtitle uses
the compile-time Embercade product label supplied by `scripts/ui-build` from
`src/embercade/version.py`, currently `EMBERCADE 1.0`. The same generated label
appears in the information menu and frontend window title. The existing
product splash retains its embedded logo and native loading text without an
extra version line. The title is set after SDL
window creation so its class/app-id identity is retained. Theme footer
fonts/colors remain theme-owned; its product text does not. Internal
Batocera/ES API and scraper versions and the `0.1.dev0` packaging version
are unchanged.

The patch is applied to a disposable archive in `.work/ui/es-source`; no
reference repository is modified.

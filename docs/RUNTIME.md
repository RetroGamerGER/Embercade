# Project-local launcher runtime

## Python decision

Batocera Common 44 declares `requires-python == 3.14.5`. The other two packages do not declare a Python constraint. Inspection of the pinned sources found:

- no check for Python 3.14.5 or `sys.version_info`;
- no API conditional on a 3.14 patch release;
- no C, C++, Cython, shared-library, or CPython-extension source in the three upstream packages;
- only ordinary Python 3.14 language and standard-library use.

Batocera's Buildroot recipe selects the image's Python and uses the exact metadata constraint for reproducibility. Embercade therefore uses host CPython 3.14.7 only as an explicit development-compatibility mode. It does not edit the pin. Installation uses `--ignore-requires-python` and records the mismatch in `runtime-info.txt`.

Third-party native wheels such as `uvloop`, `PyYAML`, `Pillow`, and `aiohttp` are installed in CPython-3.14 builds matching the running interpreter. They are not copied from another Python patch version.

## Upstream packages and entry points

| Package | Direct upstream metadata | Relevant entry points |
| --- | --- | --- |
| `batocera-common` 44.0 | typing-extensions, PyYAML, ruamel.yaml | none |
| `batocera-launch` 44.0 | uvloop, batocera-common | `batocera-launch`, `emulatorlauncher`, emulator plugin group |
| `batocera-configgen` 44.0 | batocera-launch, toml, evdev, pyudev, configobj, ffmpeg-python, pillow, requests, qrcode, pysdl2 | `batocera_launch.emulators: configgen` |

The effective target import graph additionally requires `aiohttp`, although it is not declared by Common or Launcher: `batocera_launch` imports `batocera_common.asyncio`, which imports `aiohttp`. `Pillow` is likewise required by the top-level launcher import through drawing modules. The Libretro import then requires `pyudev` and `qrcode` through controller and bezel utilities.

Batocera's Buildroot metadata adds dependencies beyond the Python metadata: Common adds the SDL3 shared library; Launcher adds evdev, pyudev, toml, Pillow and qrcode; Configgen repeats its full functional dependency set and bezel resources. These are image-composition dependencies, not evidence that every module is required by the import-only path.

The locked transitive dependency closure is explicit: Hatchling brings packaging, pathspec, pluggy, tomlkit and trove-classifiers; aiohttp brings aiohappyeyeballs, aiosignal, attrs, frozenlist, multidict, propcache and yarl; yarl brings idna. The remaining locked packages have no additional mandatory Python distributions in this environment.

The following Configgen-declared dependencies are deliberately not installed for this import-only sprint because the tested imports do not load them: `toml`, `evdev`, `configobj`, `ffmpeg-python`, `requests`, and `pysdl2`. Consequently `pip check` reports those declared dependencies as absent. They must be reassessed against the actual NES configuration and launch path rather than added blindly.

All installed third-party versions, including build-backend transitive dependencies, are pinned in `runtime/requirements.lock`.

## Layout

```text
.work/runtime/
├── home/                 isolated HOME used by tooling
├── pip-cache/            project-local download/build cache
├── runtime-info.txt      compatibility mode and source pin
├── src/                  git archive of the three upstream packages
└── venv/                 isolated CPython environment and entry points
```

`scripts/runtime-prepare` deletes and recreates only this tree. It reads the commit from `upstream.lock`, verifies the Git object, archives exactly the required source directories, builds the three unmodified wheels, and runs the smoke test. It requires network access for locked PyPI dependencies. After preparation, `runtime-smoke`, `embercade doctor`, and the test suite require no network.

Neither interactive `PYTHONPATH` nor user site-packages participate in the smoke test. `runtime-smoke` verifies six imports, the Configgen plugin entry point, and `batocera-launch --help`.

## Package data not contained in the wheels

Batocera's Buildroot recipes install additional files outside Python site-packages:

- `/usr/share/batocera/launch/defaults/config.yml` and `config-arch.yml`;
- launcher data and special-system TOML files;
- hotkey defaults under `/usr/share/evmapy`;
- launcher power/TDP/Nvidia scripts;
- Configgen data under `/usr/share/batocera/configgen`;
- RetroArch defaults and assets supplied by other Batocera packages.

The import/CLI smoke test does not need these resources. A real NES launch does need a minimal, Embercade-owned equivalent of launcher defaults plus host RetroArch core/info/assets discovery. Power, TDP, Nvidia, special-controller, SquashFS and OverlayFS resources remain excluded from 0.1.

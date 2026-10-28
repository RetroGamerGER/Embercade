# Isolated Batocera backend — 27 October 2026

The owner approved this targeted extraction and a separate private test version.
The working Gold artifact, the accepted RetroBat/shader image and all installed
images are protected. No automatic deployment or manual Garuda/Laptop/Gamescope
session test is part of this sprint; the owner performs those checks.

## Actual boundary

`integration/batocera/adapter.py` is a separately executable MIT-licensed own
integration program using the existing upstream packages under their original
terms. It never imports `embercade`. Original client software is separately
scoped under PolyForm; this does not restrict foreign GPL/LGPL/MIT rights.
The [corrected component table](BATOCERA_COMPONENT_LICENSES.md) supersedes the
older Buildroot-only GPL hypothesis. An LGPL library is not automatically a
GPL application requirement.

| Operation | Actual unchanged behavior |
| --- | --- |
| `resolve-system` | Same Arguments/SystemConfig call; same five response fields and 30-second caller timeout |
| `resolve-decoration` | Same config resolution, Emulator/Profiler and bezel_files; six options including both Dolphin values; 10-second caller timeout and fail-open rendering behavior |
| `probe-runtime` | Same eleven import targets and separate launcher help check; missing/error results remain diagnostic failures |
| `build-ui` | Raw pinned Registry/Defaults builders in selected or complete mode; existing client XML customization/filtering afterward |

Both `build_ui_data()` and `build_complete_catalog()` now use the backend.
`cli.py` retains its existing dispatch and error handling; it does not load
Batocera merely by importing its own client modules. The three existing runtime
process boundaries are reused; only raw UI generation adds a build-time child.
No daemon, general Python RPC, serialized class, callback, shared registry
object or copied API source string remains in the client. The brittle
`_PROBE.split()` composition is removed. Stdout is JSON only; upstream progress
uses stderr and the build client preserves its progress messages.

The independent client retains installation transactions, TOML helpers, menu
preferences, controller handling, file validation and overlay presentation.
The actual global/system/per-game settings are still read by Batocera's same
resolution logic and paths. No settings are migrated, reset or rewritten.
The selected/full builders produce the same menu descriptors; this extraction
adds/removes no frontend setting or game-specific menu.

## Installed layout

The source-shaped installed application carries `integration/batocera` beside
`app/embercade`. The client locates the backend relative to its own module,
then starts the chosen runtime Python with `-B -I` and an absolute script path.
The isolated child does not use the client PYTHONPATH. The build operation adds
only the pinned builder source, whose dependencies already exist in the prepared
runtime. Production execution needs no development `.work` directory.

Staging also includes the scoped root notice, full standard legal texts, original
upstream copies and current component/source guidance. Its own-file map is
filtered to actually installed client/backend files, with the canonical source
map SHA recorded. Source-only scripts/tests are not misrepresented as payload.
The existing private-path/development-launcher audit remains unchanged. Runtime-smoke tests the
isolated backend. The structure-proof digest now includes the adapter and the
modified clients so stale generator evidence cannot certify a changed backend.

## Verification and limits

The saved pre-change baseline is `efb7d3fab3e1626064c4024bc41497634c04b041`.
Ignored evidence is under `.work/adapter-separation-2026-10-27/`.

- Both real pinned builders: four generated CFG files byte-identical to the
  baseline, for selected and complete catalogs.
- Sixteen old/new API comparisons: identical selection/precedence results for
  PSX/SNES/N64 and PS2/Xbox/GameCube/Wii; test configuration bytes unchanged.
- Dedicated guards reject Batocera/Configgen imports in the client and client
  imports in the backend; static source checks include deferred/string imports.
- Independently copied installed-layout backend works under isolated Python
  even with hostile PYTHONPATH/CWD; malformed responses and timeout handling
  do not report false health or silently accept wrong builder outputs.
- Final full isolated suite: 820 tests, 815 passed and five expected skips,
  including GTK checks; all 52 structural generator fixtures verified. The ten
  backend and five license-scope checks pass. Runtime-smoke and shell syntax
  checks pass. After a package-map correction, 66 targeted package/production/backend/license
  checks also pass, including the fifth scope check. Final artifact verification
  is recorded after candidate creation.

No synthetic fixture is booted as a game. These checks do not replace the
owner's visible menu/game/controller acceptance on the three reference PCs.
The unchanged rendering/assets/core defaults and existing 16:10 limitation
are not given a new compatibility claim. Gold/installed hashes are checked
again before handoff; no remote image or host package is changed.

The independent-client assignment relies on own source history, functional
purpose and narrow data contracts, not merely separate processes. The backend
remains Batocera-specific, and no court/provider approval or universal GPL
exception is asserted. Public distribution still needs the independently
recorded API, branding, source-access and publication steps in
[LICENSING_1_0.md](LICENSING_1_0.md).

Final private artifact identity, actual packaged-operation checks and protected
baseline verification are in [the candidate report](ADAPTER_TEST_CANDIDATE.md).

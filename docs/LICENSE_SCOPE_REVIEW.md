# Historical license scope analysis

> Historical evidence retained unchanged below. The current effective assignment
> is [LICENSING_1_0.md](LICENSING_1_0.md), with the corrected
> [Batocera GPL/LGPL distinction](BATOCERA_COMPONENT_LICENSES.md) and implemented
> [backend separation](ADAPTER_SEPARATION.md). Earlier prospective grants,
> blanket-scope assumptions and old captured-resource blockers are not current
> release findings. The removed captured-bezel and bundled-shader inventories
> are not the new RetroBat/host-package payload. No previous full audit was repeated.

## Preserved original report

# License scope review — PolyForm Option A design, grants pending

## Current preparation update — 27 October 2026

The owner requests scoped license/publication preparation, with no separate
commercial licensing model. The [current report](LICENSE_PREPARATION_1_0.md)
and [component map](LICENSE_COMPONENT_MAP.csv) update this historical analysis
to 63 own-package modules, 35 Batocera patches and six ES patches. They retain
the concrete mixed API boundaries below and add the later modules/patches
without declaring them legally independent. Reference texts now exist in
[LICENSES/prepared](../LICENSES/prepared/README.md); preparing them is authorized,
applying a blanket license or restructuring the runtime is not. Earlier
44-module/23-patch counts and non-existing-text statements are baseline records.

The owner's public report of the Batocera team answer and the supplied Reddit
community comment are now recorded in the [bezel update](BEZEL_PROVENANCE.md#community-evidence-update--27-october-2026).
CC BY-NC-ND permits covered unchanged noncommercial sharing with its conditions;
it does not assign that license to unknown art. The prior technical comparisons
are reused, not repeated. Rights/source/notice gaps remain distinct from the
owner's RetroAchievements API clarification, which blocks any new AppImage.
No effective project grant, push, public release or artifact build occurs here.

The [RetroBat follow-up](LICENSE_PREPARATION_1_0.md#retrobat-reference-and-carbon-completion--27-october-2026)
now records its original project/component notices. Carbon's origin and
CC-BY-NC-SA theme license are documented and completed, with the owner's exact
credit retained. The targeted shader follow-up below supersedes the earlier
frame/texture/LUT gaps; identified licenses are not reset by differing hashes.
The later [bezel decision report](BEZEL_DECISION_1_0.md) and
[302-row table](BEZEL_DECISION_FILES.csv) separate observed licenses, general
grant/variant scope, missing grant mapping and technical data. They supersede
reading the old all-UNKNOWN matrix as a file-specific infringement finding.
The later [35-PNG source lookup](BEZEL_35_LICENSE_FOLLOWUP.md) adds a reasoned
RetroBat CC-BY-NC-SA-4.0 project-scope assignment for Spectravideo, explicitly
marked as an inference. Thirty-four of that cohort remain without a completed
applicable-file mapping; no unrelated completed entries are reopened.

## Historical scope analysis

Initial asset review baseline: `4a9fca25b0c4f0f474ee171da276b187c7f68620`.
File-boundary follow-up baseline: `9b3809d85864c76f8e5c8729d59caaac96054b19`.
Option A architecture baseline: `128eceb64a18686ba7e540ec62ea9f27215f24b1`.
PolyForm architecture review baseline: `1c8b7f33a9c6c942df4dec071b8e563932877ba2`.
This is an evidence record, **not a license grant or a completed file-level
redistribution clearance**. No assets, runtime code or packaging metadata were
changed. The repository remains PRIVATE.

The owner now selects **PolyForm Noncommercial 1.0.0**
(`PolyForm-Noncommercial-1.0.0`) for confirmed independent own software.
**CC-BY-NC-SA-4.0** remains the target for own documentation and cleared own
branding. This supersedes the earlier CC-software proposal, not third-party
grants. **Option A** remains the design direction and Non-Commercial a hard
owner goal; Option B is not pursued. The first-party/GPL integration boundary
still needs final approval before any root LICENSE, SPDX headers or packaging
License-Expression. This is not adapter implementation or an effective license
rollout. Exact ownership, combined-work/client scope and compatible terms for
GPL-bound contributions still require confirmation.

## Software-license choice and its limits

[PolyForm's official overview](https://polyformproject.org/licenses) identifies
Noncommercial as a software license; that makes it a more software-specific
target than CC for zone 1, not proof that the current mixed application qualifies.
The [official 1.0.0 text](https://polyformproject.org/licenses/noncommercial/1.0.0)
supports the following bounded reading:

- Copyright permission covers permitted use and changes; distribution has its
  own additional permission. Do not equate that clause with a universal resale ban.
- Noncommercial purposes are permitted; specified personal purposes exclude
  anticipated commercial application. Listed public-benefit organizations have
  broader permission regardless of funding. Edge cases need legal review.
- Recipients of any part must receive the terms or their URL and supplied
  `Required Notice:` lines. Copyright/attribution facts still need recording.
- It grants relevant licensable patent claims, with patent-defense termination.
  The first violation notice has a 32-day cure provision. Warranty/liability
  disclaimers apply.
- It has no CC-style explicit ShareAlike or mandatory source-offer clause.
  Preserve required terms/notices; do not invent CC obligations for software.

These are audit observations, not legal advice or clearance. Compared with
[CC's legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en),
CC has a different NC definition, explicit attribution/ShareAlike and excludes
patent/trademark rights. [CC advises against software licensing](https://creativecommons.org/faq/#can-i-apply-a-creative-commons-license-to-software).
Software patent treatment therefore improves; GPL compatibility, actual file
independence and third-party clearance do **not** improve automatically.
No compatibility exception, trademark grant or universal ban is inferred.

## Concrete GPL integration boundary

The Batocera pin is `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`.
Its root `COPYING` describes Buildroot under GPL-2.0-or-later with file exceptions;
`package/batocera/core/batocera-configgen/batocera-configgen.mk` explicitly
declares `BATOCERA_CONFIGGEN_LICENSE = GPL`. The inspected launcher/common
package directories have no separate package-local license grant. This is the
recorded repository/package evidence, not proof that every fetched asset or
every Python package has a self-contained GPL grant. Exact launcher/common/
plugin/batocera-es-system builder coverage should be confirmed before public
distribution.

These Embercade-authored payloads are not just external executable invocations:

| File / symbol at the follow-up baseline | Execution boundary and exact API | Functional dependence / independent usefulness |
| --- | --- | --- |
| `src/embercade/ui_data.py:305`, `build_ui_data()`; imports at 327–330 | Same interpreter as the Embercade UI builder: `batocera_es_system.es_features.build`, `es_systems.build`, `registry.Registry`, `shared.Defaults`. Calls `Registry.load_files`, `Defaults.for_directory`, `get_systems_metadata` and both builders (333–340). | This function needs the pinned Batocera registries/builders. Other functions in this mixed file perform XML filtering/merging/customization without importing Batocera. `scripts/ui-prepare:217–218` supplies the package path and starts `embercade ui-build`; calling the builder in that child does not separate its own code from the APIs within that interpreter. |
| `src/embercade/batocera_config.py:29`, `_PROBE`; executed at 108–109 | The outer module has only stdlib/own imports. Its embedded child program imports `batocera_launch.cli.arguments.Arguments` and `batocera_launch.config.config.SystemConfig`, constructs upstream arguments and calls `SystemConfig.load()`. JSON returns only the effective emulator/core and forced flags. | Closely tied to Batocera's configuration API and argument schema; not a generic independent resolver unchanged. The outer process boundary is real but does not remove the embedded program's API dependence. |
| `src/embercade/standalone_decoration.py:31`, `DECORATION_PROBE`; executed at 190–198 | Child program extends `_PROBE`, imports `batocera_launch.emulator.Emulator` and `batocera_launch.profiler.Profiler`, invokes private `Emulator._load_class()` and reads `bezel_files`. Returns JSON file paths/options. | Resolver depends on private upstream APIs. Own geometry, PNG/layout validation, compositor IPC and helper supervision are separate functions with potential independent reuse; the current file is mixed, not wholly independent. |
| `src/embercade/runtime.py:187`, `probe_runtime()` | Generates a child import script, executed at 215–216 with the pinned Python. `importlib.import_module()` loads the ten targets in `RUNTIME_IMPORTS:96–106`: `batocera_common`, `batocera_launch`, `configgen`, `configgen.launch`, `configgen.generators.libretro.libretroGenerator`, `batocera_launch_dolphin`, `batocera_launch_pcsx2`, `batocera_launch_rpcs3`, `batocera_launch.emulators.xemu`, `batocera_launch.emulators.xenia_edge`. Separate CLI `--help` call follows. | Health probe is specific to the integrated stack, but does not configure a game. `load_config()`, `executable_config()`, `emulator_provider_config()` and path/status classes in the same file are own TOML/config helpers; using those does not execute the probe. The earlier `runtime_status()` label was incorrect. |
| `scripts/runtime-smoke:19–102`, Python heredoc | Shell starts a child Python interpreter. Imports the same stack plus `batocera_launch.cli.main`, checks distribution/entry-point metadata, and directly imports `Xemu` and `XeniaEdge`. Reading entry-point metadata does not itself call `EntryPoint.load()`. | Development-only stack verification, not the production launcher, but own test code and upstream APIs share the child interpreter. |
| `tests/test_runtime.py:152`, logging test payload at 174 | Own `-c` child program imports `batocera_launch.logging.setup_logging` and enters/exits its context manager to test bounded logs. | Integration test only; payload needs this upstream logging API. Other tests in the file must not be assigned the same coupling merely by association. |
| `tests/test_visual_runtime.py:998–1053`, bezel test payload | Own child program imports `configgen.generators.libretro.libretroConfig.writeBezelConfig` and `libretroPaths.RETROARCH_OVERLAY_CONFIG`, supplies test doubles and calls the generator. | Integration test only, closely based on Configgen's function/config contract. Other tests mostly inspect files/commands or use mocks. |

Thus **four source modules, one smoke script and two test files** contain
direct Batocera API programs: seven paths, not seven whole-file legal findings.
Only `ui_data.py` has ordinary Batocera import statements in its own module AST;
they are deferred until the builder is called. The other three source modules
store the import programs in strings executed in children. An AST-only import
scan would miss them. `tests/test_standalone_decoration.py` also executes the
existing `DECORATION_PROBE`; it adds no separate Batocera import payload.

The outer Embercade programs often use subprocess/JSON boundaries, but inside
the identified API processes own payloads and upstream modules share an
interpreter. That distinction is observable in code; it must not be described as an
already established legal exemption. Whether each integration is an independent
work or a GPL-covered combined work remains a legal/scope review question, not
a conclusion that the entire Embercade tree automatically becomes GPL.

GPLv2 sections 2 and 6 distinguish independent aggregation from a combined
work and prohibit additional restrictions on recipients. Neither PolyForm NC
nor CC BY-NC-SA's NC condition can be assumed GPL-compatible for a combined
GPL work. Merely excluding
Batocera's directory from a root license does not resolve the own embedded
payloads' status. Review the actual program boundaries before assigning those
files a PolyForm-only license.

Primary references:

- [CC BY-NC-SA 4.0 legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- [Creative Commons software FAQ](https://creativecommons.org/faq/#can-i-apply-a-creative-commons-license-to-software)
- [GNU FAQ: interpreter bindings](https://www.gnu.org/licenses/gpl-faq.en.html#IfInterpreterIsGPL)
- [GNU FAQ: aggregation](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)
- [Pinned Batocera COPYING](https://github.com/batocera-linux/batocera.linux/blob/9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48/COPYING)

The owner has changed the intended own-software license, not resolved the GPL
scope gate. The preceding CC-software assessment remains comparison evidence;
CC is retained only for its separately confirmed prose/artwork scope.

**Owner direction / remaining gate:** Option A excludes GPL-bound integration
and target material from the intended independent-own-work NC scope. Final
boundaries and compatible grants for own contributions still need approval;
this audit does not issue any license automatically. No NC restriction is to
be added to recipients' existing GPL rights.

## File-group treatment matrix (A–L)

Groups describe technical functions, not mutually exclusive copyright scopes;
mixed files appear in more than one group. Proposed treatment is not an issued
license. This matrix uses `POLYFORM CANDIDATE` for potentially independent own
software awaiting positive rights/scope approval, `GPL-COMPATIBLE TERMS REQUIRED`
for API/target-bound own portions requiring such treatment under the confirmed
applicable GPL scope, `KEEP UPSTREAM LICENSE` for foreign material,
`NEEDS LEGAL REVIEW` for unresolved scope/terms and `UNKNOWN` for unestablished
origin/grants. A candidate is not a grant, and none clears the full payload.
The detailed foreign-asset tables below retain their narrower evidence labels.

For stage paths below, `R/` means `share/embercade/resources/` below the
installed prefix, not a tracked resource directory containing all upstream
files. `.work` audit caches are evidence only, never production dependencies.

| Group / concrete paths | Author / source evidence | Coupling and existing terms | PolyForm/CC boundary / recommended treatment | Status |
| --- | --- | --- | --- | --- |
| **A** — the seven API-bearing paths in the preceding table | Own integration history plus pinned Batocera APIs; complete rights chain for own additions not certified | Same-interpreter builder or child API programs; GPL repository/package evidence above | Zone 4 for confirmed GPL-bound portions; no PolyForm-only whole-file grant. Exact API/client scope and upstream version still need approval. | GPL-COMPATIBLE TERMS REQUIRED (bound portions); NEEDS LEGAL REVIEW (scope) |
| **B** — `patches/batocera-launch/*.patch` (22), `patches/emulationstation/0001-embercade-desktop-policy.patch` (1) | Own additions + retained/derived upstream code; exact targets below | Modified Batocera Python / MIT ES C++; target terms, no own additions grant in patch headers | Zones 4/5: preserve foreign grants and notices; approve own additions compatibly. PolyForm cannot override GPL target material or erase MIT context. | KEEP UPSTREAM LICENSE; GPL-COMPATIBLE TERMS REQUIRED (Batocera additions subject to coverage); NEEDS LEGAL REVIEW |
| **C** — independent functions/modules enumerated below, especially `paths.py`, `executables.py`, `exit_hotkey.py`, `policy.py`, `elf_runtime.py`, `version.py`, `installer.py`, `steam.py`, `transfer_payload.py` under `src/embercade/` | Introduced and evolved in this repository; Git author metadata is not proof of copyright ownership or no copied logic | No direct Batocera API imports in these modules; own grant not introduced | Zone 1 candidates after positive provenance/independence confirmation. Lack of imports alone is insufficient; indirect mixed-helper dependencies need review. | POLYFORM CANDIDATE |
| **D** — `launcher.py`, `libretro_dry_run.py`, `dolphin_dry_run.py`, `production.py`, `doctor.py`, `staging.py`, emulator/resource/import/inventory helpers below | Own code; upstream configuration schemas, metadata and runtime protocols are foreign inputs | Processes, argument vectors, TOML/INI/JSON/XML, files, native OS/library interfaces; some functions call A indirectly | Own independent routines may be zone 1 candidates; API-bound parts are zone 4. No automatic subprocess exemption; generated foreign descriptors retain source terms. | NEEDS LEGAL REVIEW; POLYFORM CANDIDATE (independent portions only) |
| **E** — `tests/test_*.py`, `scripts/runtime-smoke`, `scripts/frontend-libs-smoke`, `scripts/shaders-smoke`, `scripts/dev-*`, `scripts/launch-*-test`, `scripts/launch-system-test` | Own test/development history; upstream-derived assertions/fixtures must be distinguished | Two explicit API test payloads and smoke heredoc are A; other tests mostly own mocks, argv/files and existing probe execution | Own mock/file/argv tools are possible zone 1; bound API bodies zone 4; foreign fixtures keep their grants. Development-only execution does not clear licensing. | POLYFORM CANDIDATE (independent parts); GPL-COMPATIBLE TERMS REQUIRED (bound API parts); KEEP UPSTREAM LICENSE (fixtures); NEEDS LEGAL REVIEW |
| **F** — `README.md`, `AGENTS.md`, `ROADMAP.md`, `docs/*.md`, `LICENSES/README.md`, resource READMEs, own prose in `THIRD_PARTY_NOTICES.md` | Own documentation history; quoted notices/legal texts belong to their authors | Prose, no program linkage; owner-selected CC-BY-NC-SA-4.0 is still pending | Zone 2 own prose, not PolyForm software. Exclude copied notices/legal texts/graphics and review embedded code separately. | NEEDS LEGAL REVIEW (final CC scope/grant); KEEP UPSTREAM LICENSE (foreign text) |
| **G** — `resources/branding/source/embercade-{icon,portrait,landscape}-master.jpg`, `icon/embercade-{128,256,512}.png`, `splash/embercade-splash-3840x2160.jpg`, `steam/embercade-grid-900x1800.jpg`, `steam/embercade-hero.jpg` | User-supplied masters introduced in `d5e4deb`; creator/public rights chain not recorded | Masters/derivatives/symlink, not GPL code; no established grant. Only derivatives/link are staged. | Potential own-art CC treatment needs verified underlying rights; supplying a private image does not prove a public grant. Preserve images and branding behavior. | UNKNOWN |
| **H** — `R/emulationstation/themes/es-theme-carbon/**`; user themes at `$XDG_DATA_HOME/embercade/themes/**` | Fabrice Caruso, Eric Hettervik/Rookervik, Nils Bonenberger; maioni additions; original pin and RetroBat credits | CC-BY-NC-SA theme; retained readme has a 2.0 heading and 4.0 body; embedded resources retain their own terms | Carbon origin/theme license/credit DONE. Preserve original notices and handle foreign fonts/logos/audio separately. Downloaded user themes have their own authors/licenses. | DOCUMENTED (Carbon theme); SEPARATE COMPONENT REVIEW (embedded/user resources) |
| **I** — `R/batocera/shaders/**`; own `resources/shaders/catalog.toml`, `src/embercade/shaders.py` and generated aliases separately | Official Slang pin and per-file authors below; own menu/resolver history | Complete foreign shader tree is staged, not just 14 menu presets; heterogeneous original terms | Preserve each known grant and preset dependency. The exact remaining legacy-code gaps are named below; the remainder of the shipped tree is not newly audited here. Own mappings do not relicense code/images. | KEEP UPSTREAM LICENSE; EXACT OPEN FILES BELOW; NOTICE DELIVERY INCOMPLETE |
| **J** — `R/batocera/datainit/decorations/consoles/**` | Existing 302-path matrix: 150 PNG paths and 152 technical paths; concrete groups in BEZEL_DECISION_1_0.md | 8 PNGs with observed Duimon/ND notices; 107 further Duimon-linked PNGs with general grant sources and unmapped variant scope; 35 without concretely mapped grants, including 2 historical dispute cases | Keep positive grants/credits. Missing records, license conditions, technical data and proven violations are separate. No actual file-specific violation/denial established; no blanket project CC or publication approval. | SPECIFIC DECISION GROUPS N/D/H/M/F/L/U/T; NOT ONE ALL-UNKNOWN BLOCKER |
| **K** — bundled runtime wheels/site-packages, frontend libraries/resources/locales, `resources/ui/azahar-language.es_features.xml`, `resources/libretro/batocera-44-cores.txt`, generated `R/emulationstation/{es_systems,es_features,es_input,es_savestates}.cfg` and Batocera defaults | Pinned Batocera/ES and individually locked dependencies; respective authors | Copied/generated foreign text/code/data and native runtime linkage; per-component terms, details below | Zone 6: no own PolyForm/CC coverage. Account for every shipped component, not only root/lock hashes. Imported user cores/providers and host emulators are not bundled. | KEEP UPSTREAM LICENSE; NEEDS LEGAL REVIEW; UNKNOWN (unaccounted parts) |
| **L** — `pyproject.toml`, `packaging/linux/embercade.desktop`, `config/*`, `.gitignore`, `upstream.lock`, `runtime/*.lock`, `resources/resource-bundle.lock`, own policy/default/shim files; build/install scripts and generated entry points | Own packaging history; foreign pins/package names/notice contents are not newly owned | Metadata/templates, process-based build/install; `pyproject.toml` has no license/classifier/license-files claim; stage manifest records hashes/pins, not grants | Own scripts/templates can be zone 1 candidates; foreign data stays separate. Future metadata must describe each actual distribution, not label the full mixed payload PolyForm. Source delivery remains unresolved. | POLYFORM CANDIDATE (own independent parts); NEEDS LEGAL REVIEW (distribution scope) |

### Own source coverage, history and process boundaries

All **44** `src/embercade/*.py` files were classified, including deferred and
dynamic imports and embedded child code. Four contain the Batocera API programs
above; six others use nonstdlib Python/native libraries directly. The remaining
34 have stdlib/Embercade-only imports in the module AST. These counts do not
measure legal independence, transitive dependencies or copied code.

Introduction/history checks identify the repository's project author
`RetroGamerGER`, not a verified assignment of all copyrights. Representative
introductions: installer/setup/version `d4324b9`, Steam `9ebdca3`, managed
imports `cd4526b`, core resolver `28c0faa`, controller `4acf9fb`, provider runner
`07c7f26`, wizard `f9608f5`; `5296354` extends the wizard's system-file flow.
A bounded comparison against all 411 Python files at the Batocera pin found no
whole-file byte matches and no shared windows of eight normalized non-comment/
non-import lines with at least 200 characters. It does **not** exclude short,
transformed, translated or third-source copies. No complete per-contribution
ownership clearance is asserted. Explicit copied/derived patch and metadata
material is recorded separately, not counted as independent original work.

The following paths are all under `src/embercade/`; `C/D` indicates overlapping
own implementation and integration duties, not a new license label.

| Exact files | Observed behavior / independently reusable portion | Treatment boundary |
| --- | --- | --- |
| `__init__.py`, `paths.py`, `executables.py`, `exit_hotkey.py`, `policy.py`, `elf_runtime.py`, `version.py` | Own path/override validation, executable discovery, hotkey/policy values, ELF audit and central version. Stdlib only; no Batocera API execution. | POLYFORM CANDIDATE; positive authorship/independence still required, field conventions alone are not proof. |
| `installer.py`, `steam.py`, `transfer_payload.py`, `setup_flow.py` | Own transactions/copies/uninstall/update, VDF/artwork registration, payload verification and setup/import plans. Mixed-module TOML helpers are used, not its health probe. | POLYFORM CANDIDATE; NEEDS LEGAL REVIEW for shared-helper/whole-work scope. Generic routines can work without the Batocera probe; VDF/CRC32 does not prove authorship. |
| `first_run.py`, `host_requirements.py` | Own state/argv/setup/package-plan orchestration, shared TOML helper calls; host evdev discovery and downstream Doctor/CLI operations. | NEEDS LEGAL REVIEW for the complete workflow/import graph; reusable own routines remain possible PolyForm candidates. |
| `imports.py`, `cores.py`, `ppsspp.py`, `xemu.py`, `pcsx2.py`, `rpcs3.py`, `azahar.py`, `display.py` | User-file/config validation and isolation, external firmware UI, ELF-symbol inspection, sysfs/Hyprland/display processes. No emulator-code import or core execution. | POLYFORM CANDIDATE; schemas/snippets/foreign outputs require separate review and retained terms. |
| `controller.py`, `controller_exit.py`, `provider_runner.py`, `first_run_ui.py`, `drm_output.py`, `decoration_window.py` | SDL2 via ctypes, dynamic host evdev, Xlib/GTK/cairo/libdrm, Gamescope IPC/services. Renderer uses own geometry helpers, not the Batocera probe. Wizard starts existing CLI workflows. | NEEDS LEGAL REVIEW for native bindings, copied snippets and mixed-helper/whole-work scope; own independent portions potentially PolyForm. Controller XML copied at `controller.py:267–315` is foreign data, not newly owned mapping content. |
| `resources.py`, `shaders.py`, `rom_inventory.py`, `bios_inventory.py` | Own resource/preset dependency and inventory logic. BIOS source via `git show` and AST/literal parsing is **not imported/executed**; ROM rules are XML data. | POLYFORM CANDIDATE for own implementation; KEEP UPSTREAM LICENSE for covered copied/generated foreign content. Output is neither automatically GPL nor automatically original. |
| `launcher.py`, `libretro_dry_run.py`, `dolphin_dry_run.py` | External launch argv/dry-run files/synchronous wait; launcher calls config choice and decoration supervision, whose child API probes are A. | NEEDS LEGAL REVIEW; external-process boundary is real but the chain includes API-bearing programs. |
| `production.py`, `doctor.py` | Own environment/health orchestration; external frontend/CLI and files; own `probe_runtime` calls spawn the A child. | NEEDS LEGAL REVIEW for indirect/whole-program scope; not a new direct GPL import or blanket independent clearance. |
| `staging.py` | Copies foreign runtime/assets, generates wrappers and customizes XML; **does not** call `build_ui_data()`. Wrapper invokes upstream CLI externally. | NEEDS LEGAL REVIEW for complete program/distribution; own generic copy routines potentially PolyForm, copied/generated inputs retain original terms/source duties. |
| `compatibility.py`, `cli.py`, `__main__.py` | Own routing/assessment. `ui-build` enters A in the CLI interpreter; compatibility reads capability constants without starting a probe. | NEEDS LEGAL REVIEW at actual call sites; no whole-file automatic GPL or PolyForm classification. |
| `ui_data.py`, `batocera_config.py`, `standalone_decoration.py`, `runtime.py` | Four API payload/helper mixed modules; exact API parts and independent helpers are mapped above and below. | GPL-COMPATIBLE TERMS REQUIRED for confirmed bound portions; NEEDS LEGAL REVIEW for whole files. Remaining independent portions may be PolyForm candidates only after approval. |

### Patch-by-patch map

There are **22 Batocera diffs plus one ES diff, 23 total**, not 22 combined.
All were read, including context/deletions and additions. They touch 20 distinct
Batocera Python paths and three ES paths. Reference checkout HEADs need not
match the locks: evidence comes from pinned `git show`, not the current checkout.

Target prefixes are upstream repository-relative:

- `CG/`: `package/batocera/core/batocera-configgen/configgen/configgen/generators/libretro/`
- `L/`: `python-src/batocera-launch/batocera_launch/`
- `C/`: `python-src/python-batocera-common/batocera_common/`
- `D/`: `python-src/batocera-launch-dolphin/batocera_launch_dolphin/`
- `P/`: `python-src/batocera-launch-pcsx2/batocera_launch_pcsx2/`
- `R/`: `python-src/batocera-launch-rpcs3/batocera_launch_rpcs3/`

Patch names below are under `patches/batocera-launch/` except the last row.
`BC` means KEEP UPSTREAM LICENSE for retained/derived Batocera code, subject to
the GPL evidence/coverage qualification above; `ES` means KEEP UPSTREAM LICENSE
for retained MIT source/context. Own additions still need a scoped grant;
notice/source accounting is NEEDS ATTRIBUTION for both, not a clearance.

| Exact patch | Exact targets using the prefixes above | Introduced | Treatment |
| --- | --- | --- | --- |
| `0001-embercade-desktop-paths.patch` | `CG/libretroConfig.py`, `CG/libretroGenerator.py`, `CG/libretroPaths.py`, `CG/libretroRetroarchCustom.py`, `L/cli/main.py`, `L/paths.py`, `C/paths.py` | `208bbe9` | BC |
| `0002-embercade-desktop-lifecycle.patch` | `L/command.py`, `L/devices/hotkeygen.py`, `L/devices/video.py` | `208bbe9` | BC |
| `0003-embercade-desktop-errors.patch` | `L/launch.py` | `208bbe9` | BC |
| `0004-embercade-disable-special-hardware.patch` | `L/devices/evmapy.py`, `L/emulator.py` | `208bbe9` | BC |
| `0005-embercade-recording-path.patch` | `CG/libretroRetroarchCustom.py` | `208bbe9` | BC |
| `0006-embercade-retroarch-controller-exit.patch` | `CG/libretroControllers.py` | `4acf9fb` | BC |
| `0007-embercade-libretro-visual-resources.patch` | `CG/libretroGenerator.py`, `CG/libretroConfig.py`, `L/paths.py` | `24ba2cb` | BC |
| `0008-embercade-dolphin-host-executable.patch` | `D/emulator.py` | `7eb8bd9` | BC |
| `0009-embercade-dolphin-controller-exit.patch` | `D/emulator.py` | `7eb8bd9` | BC |
| `0010-embercade-xemu-desktop-paths.patch` | `L/emulators/xemu.py` | `4271028` | BC |
| `0011-embercade-pcsx2-desktop-paths.patch` | `P/emulator.py` | `62b55e4` | BC |
| `0012-embercade-rpcs3-desktop-paths.patch` | `R/emulator.py` | `5b5d60f` | BC |
| `0013-embercade-libretro-exact-core-path.patch` | `CG/libretroPaths.py`, `CG/libretroGenerator.py` | `28c0faa` | BC |
| `0014-embercade-desktop-bezel-scaling.patch` | `CG/libretroConfig.py` | `eff6291` | BC |
| `0015-embercade-retroarch-quoted-paths.patch` | `CG/libretroConfig.py` | `eff6291` | BC |
| `0016-embercade-amiga-bios-path.patch` | `CG/libretroConfig.py` | `c25b2d2` | BC |
| `0017-embercade-dolphin-library-paths.patch` | `D/emulator.py` | `2a6b088` | BC |
| `0018-embercade-libretro-core-options.patch` | `CG/libretroGenerator.py` | `2a6b088` | BC |
| `0019-embercade-xenia-edge-host-executable.patch` | `L/emulators/xenia_edge.py` | `07c7f26` | BC |
| `0020-embercade-xenia-edge-xdg-paths.patch` | `L/emulators/xenia_edge.py` | `26bf255` | BC |
| `0021-embercade-bounded-launch-logs.patch` | `L/logging.py` | `c59eed8` | BC |
| `0022-embercade-standalone-decoration.patch` | `L/emulator.py` | `c390aca` | BC |
| `patches/emulationstation/0001-embercade-desktop-policy.patch` | `es-app/src/guis/GuiMenu.cpp`, `es-core/src/Splash.cpp`, `es-app/CMakeLists.txt` | `4f84f59` | ES |

These patches modify **Batocera's** emulator integration, not Dolphin/PCSX2/
RPCS3/Xemu/Xenia source itself. Their target license is not inferred from each
emulator project's license. No target-file exception was found in the 20
Batocera files or three ES files inspected. ES root `LICENSE.md` is MIT,
copyright Alec Lofquist (2014), excluding independently licensed dependencies.

Patch files are separately distributable source diffs, but contain foreign
context/deletions and sometimes re-added source: ES patch lines 80–123 re-indent
upstream appliance quit entries; PCSX2 patch lines 134–146 reuse upstream
folder settings. They are not wholly original Embercade files. No patch carries
an explicit own author/copyright/SPDX/license grant. Buildroot's root paragraph
about its bundled target-bound patches does not automatically grant rights to
new Embercade additions. Resolve those additions compatibly; retain upstream
notices and verify source/change-notice delivery for the patched result.
An MIT-compatible own contribution license need not be MIT, but cannot erase
the MIT notice or pretend copied target material is solely Embercade-owned CC.

`scripts/runtime-prepare:64–77` archives the Batocera pin and applies its series;
`scripts/ui-build:68–69` archives the ES pin and applies its patch. Staging
retains root license texts. That is evidence of provenance/notice delivery,
not complete corresponding-source compliance for every bundled component.

### Carbon evidence and correction

The cached byte/OID comparison maps all 2,271 captured files exactly to the
recipe's Carbon commit; only `.gitattributes` and `.gitignore` are not staged.
The installed `theme.xml` credits Fabrice CARUSO, Eric Hettervik/Rookervik,
Nils Bonenberger and maioni and identifies CC-BY-NC-SA. RetroBat's linked
Carbon fork and published credits corroborate that attribution. The owner
now closes Carbon origin/theme-license identification and credit as DONE;
this theme is not of unknown origin or lacking a license statement.
`readme.txt` preserves a **2.0 heading followed by 4.0 legal text** and reserves
logos/trademarks to their owners. Retain the original text and record that
inconsistency without relabeling every embedded component CC-BY-NC-SA-4.0.
No theme change or new source comparison was needed for this completion.
Exact embedded paths needing separate rights accounting include
`art/fonts/Cabin-Bold.ttf`, `art/fonts/Cabin-Regular.ttf`, `art/fonts/players.ttf`
and `art/sounds/scroll.wav`; no separate grant for them was found at the pin.

### Curated shader findings, not whole-tree clearance

The existing inventory covers 14 menu presets and 142 distinct transitive files
(presets, code, includes and textures). It is reused, not regenerated. Only the
open notices below were followed through pinned Slang/GLSL files, original
authors and relevant history. Previously established grants remain established.
No blanket license is inferred for the remainder of the shipped Slang tree.

Paths below are relative to the pinned shader tree. Generated Embercade aliases
point into that unchanged tree, never a host RetroArch shader directory.

| Menu group / upstream path | Author evidence | Code license | Remaining exact-file issue | Status |
| --- | --- | --- | --- | --- |
| NewPixie, `crt/shaders/newpixie/` | Mattias Gustavsson (2016); hunterk Slang adaptation | MIT OR Unlicense; original embedded frame bitmap has the same explicit dual grant | Frame question CLOSED by the actual bitmap header and port history; preserve its copyright/permission notice | LICENSE IDENTIFIED — code and frame |
| CRT EasyMode, `crt/shaders/crt-easymode.slang` | EasyMode; rz5 Slang port, Arzed Five and Stuart Carnie compatibility changes | GPL header, no version stated; also retained by GLSL/Cg and RetroBat's FX port | GPL version/notice handling remains separate; no missing-grant claim | LICENSE IDENTIFIED — version unspecified |
| CRT Lottes, `crt/shaders/crt-lottes.slang` | Timothy Lottes | Public-domain statement | Keep provenance/header; no CC relabeling | CLEAR |
| CRT Lottes Fast, `crt/shaders/crt-lottes-fast.slang` | Timothy Lottes; hunterk adaptation | Unlicense/public-domain text | Keep original text | CLEAR |
| ZFast CRT, `crt/shaders/zfast_crt/` | Greg Hogan/SoltanGris42 | Shared implementation GPL-2.0-or-later | Pass header coverage and central GPL text accounting | NEEDS ATTRIBUTION |
| Mega Bezel, `bezel/Mega_Bezel/` base package | HyperspaceMadness, guest(r), TroggleMonkey and other credited contributors | Base README GPLv3; individual GPL-3.0-or-later and MIT helper headers | Do not extend base grant to independently licensed community packs; complete component notices still needed | NEEDS ATTRIBUTION |
| Sharp Bilinear, `pixel-art-scaling/shaders/sharp-bilinear-simple.slang` | **rsn8887** and community, per this exact header | Public domain | Catalog's Themaister-only credit needs correction after scope decision; no runtime change made here | NEEDS ATTRIBUTION |
| LCD Grid, `handheld/lcd-grid-v2.slangp` and `shaders/lcd-cgwg/lcd-grid-v2.slang` | cgwg original/revised algorithm; hunterk repository port; Arzed Five parameters, Monroe88 relocation, CatGreen90 rename, fishcu sampling fix | No explicit original-code grant found in this selected file, its pinned counterparts or original author post | Origin established; exact redistribution-grant question remains | IDENTIFIED ORIGIN — GRANT NOT FOUND |
| PSP/GBA/GBC Color, `handheld/shaders/color/` | hunterk original; Pokefan531 modifications/LUT data; crashGG GBA optimization; Flávio Sousa 2024 import | Main passes public domain; original author expressly places project shaders/LUTs in public domain | Six grey LUT-image questions CLOSED. Three inherited LUT helpers retain a separate earlier-code grant gap, listed below | LICENSE IDENTIFIED — main passes and six images; HELPER GAP SEPARATE |
| Advanced AA, `anti-aliasing/shaders/advanced-aa.slang`, bicubic passes | guest(r), Hyllian | GPL-2.0-or-later plus MIT | Preserve each pass's terms and provide complete license texts | NEEDS ATTRIBUTION |
| Bevel, `handheld/shaders/bevel.slang` | Hyllian/Jararaca | GPL-2.0-or-later | Complete license text/attribution accounting | NEEDS ATTRIBUTION |
| Simpletex, `handheld/shaders/simpletex_lcd/` | jdgleaver; Greg Hogan weighting code; Stephen Gilbert paper texture | GPL-2.0-or-later code; CC-BY-SA-3.0 texture | Paper-texture question CLOSED; credit original pattern, tone adjustment/tiling and license separately from code | LICENSE IDENTIFIED — code and texture |

### Targeted shader notice follow-up — 27 October 2026

The delivered source remains Slang
`84bcd19a854348c0e6a1d3db814a76f11fb6f011`; the comparison uses GLSL
`f8e23ff880668f0f0e837a05a316534d82a7f31b` from `runtime/shaders.lock`.
GLSL is a source/port reference, not a second shipped tree. The runtime catalog
is unchanged; this documentation supersedes its older open-notice observations.
SHA/blob values support integrity and lineage. Different line endings, paths,
bindings, language wrappers or PNG encodings are not by themselves new works
or new licenses; actual algorithm/data changes are recorded separately.

**NewPixie frame.** The author's [crt_frame.h](https://github.com/mattiasgustavsson/newpixie/blob/868202f2e949fadbcc52f821a3d5ab0923877e63/source/pixie/crt_frame.h)
contains the actual embedded 1024×1024 bitmap and its own MIT OR Unlicense text,
copyright 2016 Mattias Gustavsson. Decoding that bitmap reproduces the RGBA
pixels imported by hunterk in [3b6d56f](https://github.com/libretro/slang-shaders/commit/3b6d56f4962d59413d8dc4b6e7dbc6f7c502dbef).
The [original port discussion](https://github.com/libretro/slang-shaders/issues/134)
also connects these sources. [PNG optimization 2322a3f](https://github.com/libretro/slang-shaders/commit/2322a3fe48b2317ae218ad1c8e10a32d5de9a74d)
changes RGB at 82,143 fully transparent pixels; alpha and every nonzero-alpha
pixel remain identical. This is an encoding/transparent-colour optimization,
not an unidentified replacement drawing. Keep both licensing alternatives and
the frame author's notice; no inference from an unrelated shader header is needed.

**Simpletex paper.** The retained
[png/readme.txt](https://github.com/libretro/slang-shaders/blob/84bcd19a854348c0e6a1d3db814a76f11fb6f011/handheld/shaders/simpletex_lcd/png/readme.txt)
names Subtle Patterns. Its [original repository README](https://github.com/atlemo/SubtlePatterns/blob/bf8adf755f512b23e7ed58fad1cccf14f3413eb7/README.md)
explicitly supplies CC BY-SA 3.0; the [pattern page](https://www.toptal.com/designers/subtlepatterns/textured-paper/)
credits Stephen Gilbert for Textured Paper (23 March 2013).
The [shader creator's posts 12–13](https://forums.libretro.com/t/simple-textured-shader-for-non-backlit-lcd-systems-gbc-etc/15520)
describe brightness/contrast/grayscale processing and acceptance of that version.
Comparison with the original 500×500 pattern finds a consistent monotone
grey-value adjustment and exact repetition of that adjusted tile in both
2048×2048 and 4096×4096 images. Their subsequent PNG compression preserves
decoded pixels. The tonal change is an actual image adaptation and must be
credited, not described as mere whitespace/compression; CC BY-SA permits it
subject to its conditions. The selected preset uses the 2k image; the 4k sibling
has the same source and terms. The code's GPL does not replace the texture's CC.

**Handheld LUT images and code.** [Official import PR 655](https://github.com/libretro/slang-shaders/pull/655)
links Pokefan531's original project and says the imported shaders are unedited.
The [author's project page, Developer notice](https://pokefan531.tumblr.com/post/766008194709454848/handheld-lcd-shader-projects)
expressly places the shaders and LUTs in the public domain. The six
`handheld/shaders/color/lut/{psp,gba,gbc}-grey{1,2}.png` images entered together
in [2d01d39](https://github.com/libretro/slang-shaders/commit/2d01d3939b58442815211966a77fa053ca657ad4).
Their data/permission attribution is now resolved. This author's statement
also covers their own gamma modifications, but cannot alone grant rights in
earlier code borrowed into the separate helpers.

The three helper paths are `reshade/shaders/LUT/multiLUT.slang` and
`handheld/shaders/color/lut/GBA-LUT.slang`, `GBC-LUT.slang`. History traces the
base LUT sampler to hunterk's [5f93116](https://github.com/libretro/slang-shaders/commit/5f93116adaf29620929b604441730a53a03ee38e),
the two-LUT selector to [4ca30e9](https://github.com/libretro/slang-shaders/commit/4ca30e989e714db8ad636aefc0bed4b189ce6556),
and gamma additions/import to `2d01d39`. Type/binding wrappers are porting;
selector, depth and gamma changes affect behavior. No original base-code grant
was found in the pinned Slang/GLSL/Cg helper notices. In his [2018 developer post 6](https://forums.libretro.com/t/lightweight-lut-based-scanline-glow-concept-prototype-glsl/18336),
hunterk explains that the earlier LUT code lacked a license because its source
was an unlicensed forum example. That is a concrete inherited-code question,
not a reason to withdraw the six image grants or main-pass public-domain status.

**LCD Grid.** cgwg's [own revised shader post 95](https://forums.libretro.com/t/real-gba-and-ds-phat-colors/1540?page=5)
links the [original Cg listing](https://pastebin.com/wfM1ADCh). The characteristic
smear integrals, coefficient arrays, RGB/BGR subpixels and tone controls connect
it to common-shaders `f105229b` and Slang `762dfe1c`. The later parameter/path
work and `param`→`params` rename are identifiable port/maintenance changes;
fishcu's [4ecd485](https://github.com/libretro/slang-shaders/commit/4ecd48510e4a0f936617c5e899dd6c4fd50abbd7)
changes sampling to respect original size and is a functional correction.
No explicit original-code license appears in the checked original/pinned
listings or their applicable parent notices. Do not import the license of
cgwg's different CRT shader or of a later Mega Bezel adaptation into this file.

The remaining grant-not-found list in this targeted selection is therefore
**four code files: LCD Grid plus those three LUT helpers**. This records absent
evidence, not a legal finding that permission cannot exist. EasyMode's explicit
GPL-without-version notice is a separate version/notice issue, not a fifth
missing grant. Lottes, ZFast, Mega Bezel, Sharp Bilinear, AA and Bevel retain
their previously established findings above. Full-tree notice delivery remains
separate from this bounded follow-up. No shader, preset, texture or working
catalog was modified or removed.

### Decorations / Duimon evidence and limits

The pinned Batocera recipe installs `default_unglazed`, then overwrites with
`default_nocurve_night` and `default_standalone_night` entries. The cached
`final-resolved.tsv` maps 302 staged winning entries to those exact sources;
its 33 symlink OIDs are link-text hashes, not final image/layout hashes.
[BEZEL_PROVENANCE.md](BEZEL_PROVENANCE.md) and
[BEZEL_PROVENANCE.json](BEZEL_PROVENANCE.json) are the complete authoritative
matrix: 302 paths, 187 resolved content blobs, 144 overwritten paths and
separate winner/terminal histories. The surviving unglazed Amiga aliases
resolve to later standalone-night targets after the layers merge. Reference,
stage and Garuda installed content/link identity is verified.
The recipe and pinned root README supply install/customization information,
not a redistribution license. No root/subdirectory LICENSE/COPYING was found
at that bezel pin. Batocera's parent code COPYING is not proof that independent
fetched artwork is GPL.

File history establishes Duimon contributions, rather than assuming it from
appearance: `default_standalone_night/systems/ps2.png` follows back to Duimon's
`8061f0c` addition; Xbox standalone follows `6f097a2` (rename) and Duimon's
`b488bf3`; SNES night follows Duimon's `85b29ca` / `f5f454a`. Other history,
including `5f95003` naming artwork mostly from Mikael42, demonstrates that the
pack is not exclusively Duimon. A whole-pack Duimon license claim is invalid.

The independently cached, now canonical `Duimon/Retroarch-Overlays` repository at
`16b11e93a6e43b6b0e82bf1384f20dd6ea7da38a` explicitly supplies CC-BY-NC-ND-4.0
in LICENSE.md and README. Earlier November 2021 releases explicitly used
CC-BY-NC-SA-4.0. The exact source named in Duimon's May 2021 permission statement,
`Misc-Overlays-Borders-Bezels/Batocera`, also has an explicit SA4.0 release;
its `Batocera/decorations` subdirectory was renamed to `decorations_OLD`.
TheNamec's RC2 grant is historical SA4.0,
with later ND/watermark changes. A later change is not automatically revocation
of an effective earlier grant, but neither proves coverage of these adaptations.
No final content OID matched 6,160 known blobs in cached Overlay histories or
the compared Misc source trees. **This does not disprove derivation**; missing
blob contents and unexamined source versions are explicit comparison limits.

The full pinned histories record 466 source paths and 89 commits. Contributions
or specific source credits associate 231 staged paths with Duimon, 10 with
Mikael42, 17 with Fery65/Lorenzolamas, and leave 44 UNKNOWN; these are not
ownership assignments. Six XMP and two inspected raster ND/Duimon notices are
positive asset-specific hints, not complete versioned rights chains. All 302
applicable exact-file grants remain UNKNOWN; secondary ND/visible-attribution
review flags do not manufacture a permission denial. Contact drafts are not sent.

Static source images are not stripped or re-encoded by this audit. The existing
Libretro path creates scaled runtime images; the standalone renderer scales and
clips the frame in memory. Whether any transformed redistribution is covered
by an original grant or conflicts with ND needs permission/review. CC ND terms
allow necessary technical format modifications, but that is not blanket
permission for every visual adaptation. Preserve existing watermarks; no
per-file watermark-completeness certification is made here.
Transport confirms 302 unchanged contents and 33 preserved link texts, not
presence/legibility of every original creator's notice. Standalone side-only
clipping and Libretro fit/crop branches can hide notices; file integrity,
derivative rights and visible attribution are separate gates.

### Other foreign components and packaging limits

- `runtime/frontend-libs.lock` pins FreeImage 3.18.0 and SDL2_mixer 2.8.2.
  FreeImage's GPL2/GPL3/FIPL texts are preserved; selecting a distribution basis
  and accounting for its bundled codecs remains NEEDS LEGAL REVIEW. SDL2_mixer
  has zlib terms and retained decoder headers: DR FLAC offers Unlicense/PD or
  MIT-0, minimp3 supplies a public-domain dedication, stb_vorbis offers MIT or
  Unlicense/PD. Preserve those terms, not project CC; full notice/closure
  accounting remains NEEDS ATTRIBUTION. These are source/header findings, not
  certification of the whole compiled library payload.
- `runtime/requirements.lock` has 22 pinned dependencies. Batocera runtime
  site-packages, dependency code/notices and the separately supplied host Python
  must be distinguished. Hashes/version locks prove integrity, not license
  clearance. No umbrella license is assigned to that runtime.
- Pinned ES includes independent libraries/fonts, e.g.
  `external/libcheevos/rcheevos/LICENSE`, `external/id3v2lib/LICENSE`,
  `external/nanosvg/nanosvg_license.txt`, `resources/fontawesome-webfont.ttf`
  and compiled locales. Root MIT is not a complete nested-component audit.
- `resources/ui/azahar-language.es_features.xml` explicitly derives from
  Batocera, and `resources/libretro/batocera-44-cores.txt` is upstream metadata.
  Stage copies/customizes system/features/input/savestate descriptors and
  Batocera defaults. These are not automatically own material because an own
  tool wrote or copied them. Track provenance/terms at output-file level.
- Own default configuration, `resources/policy/desktop-capabilities.conf`,
  `resources/runtime/gamesdb.xml` (empty shim), examples, lock manifests and
  generated own entry points are separate own-work candidates, with embedded
  foreign content excluded. `scripts/runtime-prepare`, `ui-build`,
  `frontend-libs-prepare`, `shaders-prepare`, `stage-build`, `build-test-payload`,
  `install-user`, `run-external-provider`, `public-audit` and cleanup scripts
  use process/file operations, apart from the separately identified smoke
  payload. No license is granted by their shell boundaries; build scripts may
  also be relevant to GPL corresponding-source delivery.
- `pyproject.toml` advertises no license expression/classifier/license-files;
  `packaging/linux/embercade.desktop` makes no license assertion. The stage
  manifest stores file hashes/pins, not per-file owners/grants. Preserve that
  pending state; do not introduce a blanket PolyForm/CC label for a mixed payload.
- User ROM/BIOS/firmware, host emulators, imported cores/providers, PPSSPP
  resources and downloaded user themes retain their separate rights. They are
  not immutable Embercade release content and were not modified by this audit.

## Alternatives considered before the Option A decision

All options retain original third-party licenses and preserve working Carbon,
shaders and bezels. None resolves unknown asset rights, branding provenance,
GPL source/change notices or the publication/privacy decision by itself.
The owner now pursues A. B is retained below as comparison evidence, not a
recommendation to abandon NC; C is a contingency, not an approved refactor.

| Option | Proposed scope | Advantages | Disadvantages / additional-restriction risk | Maintenance / public-release complexity |
| --- | --- | --- | --- | --- |
| **A — scoped integration split** | Approved compatible terms for GPL-bound integration/patch additions; retained MIT ES material; PolyForm-Noncommercial-1.0.0 for confirmed independent own software, CC-BY-NC-SA-4.0 for own prose/cleared branding. | Retains the owner's NC goal and uses a software-specific license for independent software; not every own helper is GPL merely because it ships beside Batocera. | Mixed modules/import graphs need careful boundaries. NC cannot restrict a GPL combined work; subprocess/JSON does not establish independence. PolyForm terms/ownership require review. | Medium/high: positive contribution/scope manifest, perhaps later separation, distinct integration and own-software grants plus CC prose; repeated review. |
| **B — compatible software scope** | All verified own software under an owner-approved software license compatible with the applicable GPL versions; docs and cleared branding separately CC-BY-NC-SA-4.0; foreign material unchanged. | Simplest software boundary and contribution policy; minimizes mixed-function NC/GPL tension without rewriting the working architecture. | Changes the intended NC treatment of own software and therefore needs an explicit owner decision. Exact GPL versions and other dependencies still require compatibility review. Does not make third-party images/themes CC or resolve their blockers. | Lowest code-scope maintenance of the three; still significant third-party notice/source work for publication. |
| **C — stronger architectural separation if required** | Future compatible Batocera adapters/builders expose a narrow CLI/data interface; confirmed independent desktop tools/wizard/installer could use PolyForm. | Easier-to-audit boundaries and potential independent reuse; might preserve NC where separation is legally sufficient. | Moving imports is not a guarantee; semantics/private APIs may remain coupled, metadata/build duties remain, protocol regressions are possible. | Highest: extra packaging/protocol and two-host tests; contingency only, not implemented. |

**Current technical recommendation:** make A auditable with the small,
one-way adapter design below, positive path lists and mixed-file review.
The previous comparison found B simpler to maintain, but it does not meet
the owner's hard NC goal and is not pursued. A is technically maintainable,
not yet legally validated. C is considered only if substantive scope review
requires it. No LICENSE, SPDX or package metadata is activated.

Own generic path/integrity/VDF/setup logic, own tests/build tools and own prose
are candidates for separate licensing, **not yet CLEAR**. Foreign GPL source
and derived GPL patch material cannot be converted to PolyForm-only terms. Retained
MIT source must preserve its notice; own additions may have a compatible grant,
so this audit does not incorrectly claim that MIT forces every new line to MIT.
No unilateral Embercade grant can supersede third-party Carbon/shader/bezel/
font/codec rights or add an NC restriction to recipients' upstream GPL rights.

Before final scope/license approval, review: exact Batocera package grants/GPL
versions, the seven API programs' combined-work scope, own contribution rights,
mixed patches and generated data, native/runtime dependency closure, all shipped shaders,
Carbon's version/embedded rights, bezel/ND permissions and branding provenance.

## Option A: six prospective zones

This is an architecture and approval plan only. The current implementation,
all 23 patches, all resources and all existing runtime behavior stay unchanged.
The A–L matrix above remains the evidence inventory; these six zones describe
future treatment rather than replacing foreign provenance with directory labels.

| Zone | Exact current/proposed paths | Prospective treatment / unresolved boundary |
| --- | --- | --- |
| **1 — independent own software candidates** | The 23 lower-coupling modules listed below, potentially remaining clients/helpers in four mixed files and other reviewed own tools | PolyForm-Noncommercial-1.0.0 only after positive rights/independence approval. Native bindings/orchestration remain review cases; no present grant. |
| **2 — own prose** | Own text in `README.md`, `AGENTS.md`, `ROADMAP.md`, `docs/*.md`, `LICENSES/README.md` and own resource READMEs/notices | Intended CC-BY-NC-SA-4.0; foreign texts/images and embedded code are separately scoped. No present grant. |
| **3 — branding** | `resources/branding/source/`, `icon/`, `splash/`, `steam/` as mapped above | CC-BY-NC-SA-4.0 for cleared own artwork only; rights chain UNKNOWN. Name/source-identification policy is separate, no registration claim. |
| **4 — Batocera integration** | API portions of `src/embercade/{ui_data,batocera_config,standalone_decoration,runtime}.py`, `scripts/runtime-smoke`, two API test programs, all `patches/batocera-launch/*.patch`; proposed separate adapter package below | Approved compatible own-contribution terms where required, plus retained upstream terms. Exact GPL versions/coverage and combined-work scope pending; NC is never an extra GPL condition. |
| **5 — ES patch** | `patches/emulationstation/0001-embercade-desktop-policy.patch` and three MIT targets listed above | Retain foreign MIT grant/attribution; approve own contributions compatibly. Not a whole-file PolyForm claim or automatic MIT grant for every new line. |
| **6 — third party** | Pinned Batocera/ES, Carbon, complete Slang tree, console decorations, fonts, wheels/vendors, FreeImage/SDL2_mixer, copied/generated upstream descriptors | Keep exact original terms and source/notice obligations. UNKNOWN entries block redistribution; no Embercade license can fill missing rights. User content/host emulators/imported cores/providers are separately supplied, not own release assets. |

### Practical counts: candidates, not clearance

At the architecture baseline there are 44 own Python modules. For planning,
the following disjoint buckets total 44; all filenames are under
`src/embercade/`. No number below certifies ownership or legal independence.

| Count | Exact files | Meaning |
| ---: | --- | --- |
| 7 | `__init__.py`, `paths.py`, `executables.py`, `exit_hotkey.py`, `policy.py`, `elf_runtime.py`, `version.py` | POLYFORM CANDIDATE — generic own routines, pending positive rights/scope proof. |
| 4 | `installer.py`, `steam.py`, `transfer_payload.py`, `setup_flow.py` | POLYFORM CANDIDATE; NEEDS LEGAL REVIEW — mixed `runtime.py` helper imports require a valid portion boundary. |
| 12 | `azahar.py`, `bios_inventory.py`, `cores.py`, `display.py`, `imports.py`, `pcsx2.py`, `ppsspp.py`, `resources.py`, `rom_inventory.py`, `rpcs3.py`, `shaders.py`, `xemu.py` | POLYFORM CANDIDATE — file/config/resource logic; foreign schemas/snippets/generated content separately reviewed. |
| 6 | `controller.py`, `controller_exit.py`, `provider_runner.py`, `first_run_ui.py`, `decoration_window.py`, `drm_output.py` | NEEDS LEGAL REVIEW — native/controller/UI dependencies and copied content, not automatic Batocera GPL imports. |
| 11 | `__main__.py`, `cli.py`, `compatibility.py`, `doctor.py`, `dolphin_dry_run.py`, `first_run.py`, `host_requirements.py`, `launcher.py`, `libretro_dry_run.py`, `production.py`, `staging.py` | NEEDS LEGAL REVIEW — actual entry-point/orchestration/API workflow; only positively independent portions could be PolyForm. |
| 4 | `ui_data.py`, `batocera_config.py`, `standalone_decoration.py`, `runtime.py` | GPL-COMPATIBLE TERMS REQUIRED for confirmed bound API parts; NEEDS LEGAL REVIEW for whole files and candidate independent helpers. |

Thus **23 lower-coupling PolyForm candidates**, **17 additional review modules** and
**four mixed modules**, not 40 already-cleared NC files. There are currently
**29 Zone-4 handling paths**: four source modules + 22 Batocera patches + one
smoke script + two API-bearing test files. Zone 5 adds the separate ES patch.
These are mixed-path review counts, not 29 wholly GPL source modules.

The conservative own import graph, including deferred and type-check-only
edges, reaches a mixed module from 21 of the 44 files; this does not mean all
21 execute an upstream API. Concrete examples:
`installer` and `first_run` use `runtime.load_config`; `setup_flow` uses the
three own config readers; `steam` and `transfer_payload` reach them through
`installer`. `first_run_ui` and `host_requirements` reach setup helpers.
Consequently, declaring the entire current `runtime.py` GPL and its callers
independent NC without review would not be a clean boundary.

### Mixed files: exact extraction proposal

Whole-file Zone 4 treatment is a conservative review fallback, **not a grant**.
It unnecessarily sweeps in reusable helpers and their same-interpreter users;
function/payload extraction is preferable if the remaining scope is confirmed.

| Current mixed file | API-bound part proposed to move | Parts proposed to remain / coupling risk |
| --- | --- | --- |
| `ui_data.py` | `REGISTRY_PATHS:9–55`; raw part of `build_ui_data():327–340` loading Registry/Defaults and invoking both builders | `_write_xml`, `_customize_systems`, `_filter_desktop_features`, `merge_feature_overlay`, `load_system_provider_defaults`, `_ensure_system_provider`, `customize_production_systems`; outer `build_ui_data` becomes raw-builder client + existing customization. XML content remains foreign-derived where applicable. This changes the current build-time same-interpreter call, not a game-launch service. |
| `batocera_config.py` | `_PROBE:29–67`: Arguments construction, `SystemConfig.load` and primitive field extraction | `BatoceraConfigError`, `BatoceraSystemChoice`, `_probe_environment`, `resolve_system_choice` process/JSON validation. Current 30-second timeout and separate ROM argv preserved. Do not import an adapter's Python object or code-string constant back into this module. |
| `standalone_decoration.py` | `DECORATION_PROBE:31–44`: shared config construction, `_load_class`, Profiler and `bezel_files` | `Decoration`, `SUPPORTED`, `protected_ratio`, `validate_decoration`, `safe_margins`, backend/socket/ancestry/visibility/IPC helpers, `resolve_decoration` client and context-manager supervision. Existing 10-second timeout, None precedence, fail-open behavior and renderer cleanup stay. The current `_PROBE.split(...)` cross-file string coupling must not become a cross-zone adapter import. |
| `runtime.py` | `RUNTIME_IMPORTS:96–107`, child import-script implementation in `probe_runtime():192–207` | Config readers, `DevelopmentLayout`, `ProjectRuntime`, `RuntimeStatus`, `locked_requirements`, missing-runtime checks, transport/error handling and separate CLI `--help` probe. Missing-status labels must be own declarative protocol data, not an imported adapter constant. |

Relevant current caller edges are explicit: `cli.py:1024` calls the UI builder;
`launcher.py:270` calls config choice for its simple-Libretro branch, and
`:465` enters decoration supervision; `doctor.py:125` and
`production.py:107` call the health probe. `production.py:197` and
`decoration_window.py:20–23` use only own decoration/socket helpers.
`staging.py:19–24` uses XML helpers, never the raw builder;
`compatibility.py:19` reads launch-capability constants, not a launch plan.
These indirect users still need scope review after any future extraction.

### Adapter package and narrow contracts — not implemented

Prefer a separate top-level package over `embercade/adapters`: an isolated
adapter interpreter should not import the intended NC package initializer or
helpers just to load its entry point. A possible future layout is:

```text
src/embercade/                         # existing clients/helpers, pending scope
src/embercade_batocera_adapters/        # proposed compatible integration zone
  __init__.py                         # empty; no reverse client imports
  _system_config.py                   # shared Arguments/SystemConfig helper
  batocera_config_adapter.py
  batocera_ui_adapter.py
  batocera_decoration_adapter.py
  batocera_runtime_probe.py
```

The helper's proposed `load_configuration(system, rom)` constructs upstream
Arguments once and returns SystemConfig **inside Zone 4 only**. It replaces
the existing split-string reuse, not Batocera's config engine. The four public
adapter modules use stdlib/upstream/Zone-4 helper imports only, never
`EmbercadePaths`, `ProjectRuntime`, `LaunchPlan`, renderer or Wizard imports.

| Proposed adapter | Input / proposed operation | Result outside the child |
| --- | --- | --- |
| `batocera_config_adapter.py` | `system`, one ROM argv and existing scoped environment; `select_system` uses `_system_config.load_configuration` | JSON `system`, `emulator`, `core` strings and `emulator_forced`, `core_forced` booleans, exactly the current five-field response. Client reconstructs its own dataclass. |
| `batocera_decoration_adapter.py` | Same system/ROM/env; `select_decoration` uses config helper, Emulator/Profiler and bezel selection; no emulator configure/start | JSON `emulator`, nullable `png`/`info`, string options `pcsx2_ratio`, `pcsx2_fmv_ratio`, `xemu_aspect`, `xemu_scaling`. Client validates paths/PNG/layout and decides geometry. |
| `batocera_runtime_probe.py` | Health mode: current ten module targets; optional future smoke mode also preserves eleven smoke imports, dependency versions, four entry-point metadata checks and built-in class checks | Health JSON `python` and label-to-null/error-string `imports`; smoke mode keeps current success/failure checks. CLI `--help` remains a separate external command, not a replacement for import checks. |
| `batocera_ui_adapter.py` | Build-only source/defaults/output paths; `generate_ui_descriptors` uses the pinned registry list and builders | Writes existing `es_systems.cfg` / `es_features.cfg` in the supplied build directory, returns only output-path JSON; client applies existing filtering/customization afterward. No Registry/Defaults/XML Python object crosses interpreters. |

Use the already existing child boundaries for config, decoration and runtime;
no daemon or artificial relay chain. A one-shot UI raw-builder child has a
cohesive build-time purpose and permits independent output/helper tests. It
does not justify calling the whole product legally independent. No serialized
upstream class, pickle, callback or object graph is needed; own dataclasses
stay on the client side. JSON/argv/files clarify the mechanics, not the legal
classification of the semantics. [GNU's aggregation guidance](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)
requires considering that relationship as well.

Packaging must be designed before implementing this: current `-I` excludes
arbitrary source paths, and `runtime-prepare` does not install the
`batocera-es-system` builder. Current UI preparation supplies that source via
PYTHONPATH. Runtime adapters therefore need an adapter-only package discoverable
in the pinned child environment; the build-only UI operation needs its pinned
builder closure without adding the entire NC `src` to that interpreter.
Future staging must explicitly carry the package/source/notice mapping;
today's own-module copy does not automatically install this new namespace.
Installed execution must still have no `.work` dependency. These packaging
changes and source-delivery tests are future work, not changes in this sprint.

For this explicit six-file package, the planned Zone-4 integration inventory
is **six adapter/support source paths + 22 patches = 28 paths**, plus two
separately scoped API test programs = 30. If the smoke heredoc is retained
rather than moved into the runtime adapter's smoke mode, add one: 31. Empty
initializer/shared helper are included for conservative path accounting, not
because each necessarily imports an upstream API. Keeping all current modules
would yield 50 own Python source paths across the two packages; that is a
proposal, not the current count of 44. Counts do not decide combined-work scope.

In a future extraction, generic `paths.py`, `executables.py`, `exit_hotkey.py`,
`policy.py`, `elf_runtime.py` and `version.py` have no required functional change.
Other own config/file helpers can keep their implementations if the existing
client APIs remain stable. `launcher.py`/`doctor.py`/`production.py` callers could
keep those calls; that is not independent-license clearance. The four mixed
modules would change at their payload/transport boundaries. Adapter packaging,
`runtime-prepare`, build-only builder access, `staging.py` and API-test/smoke
wiring would need review/updates; do not promise every other file stays bytewise
unchanged. All 23 patch contents and all functional resource files can remain
as they are, with later compatible contribution/source/notice treatment.
None of these implementation changes occurs in this sprint.

Tests would move only the logging/bezel API bodies into compatible-zone
integration fixtures; surrounding process/file/helper tests can remain subject
to their own scope review. Registry-list tests in `test_ui_data.py` and
`test_3do.py` would become adapter/data-contract coverage. Future regression
gates include schema/version/error/malformed-output tests; existing isolation,
timeout, controller, None/fallback, geometry/workspace/cleanup, source and
installed execution tests; descriptor comparisons; all smokes/Stage/Doctor;
and real Garuda/Gamescope acceptance if runtime is actually refactored.
No test or payload has been moved now.

### Maintainability and future review guardrails

Option A is practical with four public API operations and a small shared helper,
but carries **medium/high licensing-review effort**, not the complexity of a
second launcher framework. Pin/API/schema changes, new generators, the private
bezel API and registry additions are the changes most likely to cross zones.
Generic installer/Steam/path fixes would normally stay local; new setup/Doctor/
launch features and visual changes may involve clients, adapters and tests.
No observed history justifies promising a numerical percentage of future sprints.

For every future sprint, review changed paths and import/call/data edges;
if it touches two zones, require explicit scope/rights review in addition to
normal regression checks. A prospective audit should:

- enumerate every source/patch/resource and actual stage file against a
  positive scope list; new or unmapped files fail the publication gate;
- scan normal/dynamic imports and embedded child programs, not only AST imports;
  detect NC-client imports of adapters and reverse adapter imports of NC code;
- keep upstream provenance for patch additions/context and generated metadata;
  AST/grep cannot establish ownership or legal independence;
- validate declared identifiers against the approved path/component map and
  retained notices; never auto-generate license headers by directory;
- keep adapters' protocol and isolation tests plus the existing runtime suite;
  require owner approval for boundary/identifier changes.

These are future checks, not an implemented license scanner or contribution
policy. If legal review finds the remaining planner/Wizard/clients form a
GPL-covered combined work, naming four adapters cannot preserve NC there.
Keep that scope UNKNOWN/blocked; seek permission or a justified substantive
boundary design. Do not override the owner's NC goal by silently choosing B,
or remove functional assets to make publication easier.

### Proposed license tree and root notice — non-effective draft

No paths in this proposed tree are created or activated by this review:

```text
LICENSE                               # future scope-routing notice, not umbrella
LICENSES/
  PolyForm-Noncommercial-1.0.0.txt    # approved independent own software only
  CC-BY-NC-SA-4.0.txt                 # approved own prose/cleared branding only
  GPL-2.0-or-later.txt                # only where that exact grant is confirmed
  MIT.txt                            # confirmed MIT material
  third-party/<component>/...        # original texts/notices, other versions too
docs/LICENSE_SCOPE.md                # future exact positive path/contribution map
THIRD_PARTY_NOTICES.md                # origin, notices and redistribution evidence
```

`GPL-2.0-or-later.txt` is a conditional example, not a selection for every
Batocera package; add the actually applicable version/license after review.
The prospective scope record needs source and stage paths, zone, copyright/
rights evidence, source pin/hash, own versus copied contribution scope,
approved license expression, notices, modification records, generated-from
sources, corresponding-source mapping and unresolved status. Mixed files need
portion-level explanation or approved separation; hashes are not grants.
Package/build metadata and machine-readable scope must agree with that record.

Illustrative **future** root notice below is deliberately a conditional design
draft, **NOT A LICENSE GRANT** and not a text to install as LICENSE now:

```text
NON-EFFECTIVE DRAFT — pending ownership, scope and license approval.

After approval, only independent Embercade-owned software explicitly
identified in LICENSE_SCOPE would be offered under PolyForm Noncommercial 1.0.0.
Own documentation and cleared own artwork explicitly identified there would
be offered under CC BY-NC-SA 4.0, not the software grant.
GPL-bound integration contributions and patches would follow their approved
compatible terms and retained upstream terms. The EmulationStation patch
would preserve its MIT-covered source and the separately recorded terms of
own contributions. Third-party software, themes, shaders, decoration artwork,
fonts, libraries and copied/generated upstream data would retain their
respective original terms and notices.

No project notice would add Non-Commercial restrictions to upstream GPL/MIT
rights or override another rights holder's grant. Unmapped or unresolved
material would receive no permission from this draft. The exact scope and
third-party evidence would be recorded in LICENSE_SCOPE and
THIRD_PARTY_NOTICES. Copyright grants would not grant product-name,
trademark or endorsement permissions; those require a separate identity policy.
```

Do not write an unconditional "all Embercade is NC" or "everything except
vendor directories is PolyForm" fallback. The NC allowlist must be positively cleared;
new/unknown files do not inherit a grant. A root routing notice is not a
custom NC exception to GPL and does not replace full applicable license texts.

### Future SPDX and contribution strategy — no headers/policy introduced

The [official SPDX record](https://spdx.org/licenses/PolyForm-Noncommercial-1.0.0.html)
lists exactly `PolyForm-Noncommercial-1.0.0`. For its unmodified standard text,
no `LicenseRef` is needed. Listing is not an OSI/compatibility certification.
Only after approval, independent own software paths could use
`SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0`; own prose/cleared art
could use `CC-BY-NC-SA-4.0`; confirmed compatible adapters
could use the specifically approved software identifier. Do not infer
`GPL-2.0-or-later` from a Buildroot notice alone. Preserve foreign identifiers
and notices; review patches/derived data with per-contribution mapping or
approved sidecars before choosing a whole-file expression. UNKNOWN is an
audit status, not a fabricated SPDX license or a reason to add PolyForm.
Keep unresolved files unmapped/blocked. A real custom unlisted license would
need a reviewed `LicenseRef`, not an invented PolyForm identifier or a label
that conceals missing permission. No headers or whole-file expressions are added.

`OR` offers an actual license choice; `AND` records simultaneous applicable
requirements, not an incompatibility fix. A blanket `MIT OR PolyForm-Noncommercial-1.0.0`
would permit choosing MIT, contrary to the intended NC restriction on that
same owned material. `GPL AND PolyForm` does not reconcile a GPL-covered
combined work with NC. Never invent a GPL `WITH` NC exception.
[SPDX expression specification](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/)
explains these operators. Wheel/payload metadata must describe the actual
mixed scope, not advertise everything as PolyForm; no metadata changes now.

Recommended future lightweight contribution rule: require the contributor to
identify touched zones, authorship/right to submit, exact source/license for
borrowed material, and agreement to the **approved** terms for those portions.
Confirmed independent own software contributions would follow PolyForm;
own prose/cleared artwork CC-BY-NC-SA-4.0; bound API/patch contributions would
follow the approved compatible terms. Retained MIT/foreign content keeps its
original terms. Mixed-zone changes
need separate scope records; undocumented third-party imports are not accepted.
No blanket permission to relicense past contributions is assumed.

A custom CLA is not justified by current needs; consider it only if actual
rights-assignment or future relicensing requirements arise. DCO-style origin
attestation could help, but [DCO 1.1](https://developercertificate.org/) includes
open-source wording that needs review for the NC zone. It is not a substitute
for a license grant or retrospective relicensing authority; its unchanged text
may be copied, not rewritten into an NC DCO. A separate origin/right-to-submit
attestation and express contribution-grant acceptance need review instead.
No CONTRIBUTING/CLA/DCO policy is activated in this sprint.

### Packaging metadata proposal — no activation

Current `pyproject.toml` uses `setuptools>=77` and `setuptools.build_meta`,
with no license/classifier/license-files claim. Its package discovery includes
all of the current mixed `src/embercade` tree. [Setuptools supports modern
SPDX and license-files fields since 77.0.0](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html);
no backend change is needed. Scope approval, not syntax, is the blocker.

An example for a **future confirmed independent-software-only distribution**:

```toml
# NON-EFFECTIVE EXAMPLE — not the current mixed Embercade package.
[project]
license = "PolyForm-Noncommercial-1.0.0"
license-files = [
    "LICENSE",
    "LICENSES/PolyForm-Noncommercial-1.0.0.txt",
    "docs/LICENSE_SCOPE.md",
    "THIRD_PARTY_NOTICES.md",
]
```

This is not a proposal to paste that value into today's package. Different
licensed contents within an actual archive require the corresponding honest
expression and positive file map; including license/notice texts does not
relicense the software described by them. A separate approved adapter package
or a genuinely mixed distribution could be designed later. `AND`/`OR` cannot
solve a combined-work incompatibility or silently offer an NC escape route.

[PyPA Core Metadata](https://packaging.python.org/en/latest/specifications/core-metadata/#license-expression)
defines License-Expression per wheel/sdist, not per repository or entire offline
runtime. Metadata 2.4+ is needed; do not emit both modern License-Expression and
legacy License. A static [project].license is appropriate only if the backend's
distributions share that expression. [License-file paths](https://packaging.python.org/en/latest/specifications/pyproject-toml/#license-files)
are project-relative globs and must match delivered files. [PEP 639](https://peps.python.org/pep-0639/)
places wheel texts under `.dist-info/licenses/` with relative subpaths retained.
No such own wheel is the current Production delivery mechanism.

`staging.py:235–244` instead copies own source to `share/embercade/app/embercade`
beside the runtime venv; `pyproject` license-files would not automatically become
stage notices. The complete offline payload therefore needs an explicit
component/source/stage scope manifest and notice-delivery design. Never relabel
foreign dist-info metadata, copied descriptors or bundled assets PolyForm.
Integrity manifests prove hashes, not grants. Before activation, test archive
expressions, license-file existence in sdist/wheel/install, absence of conflicting
legacy metadata, and equivalent source/stage notice delivery.

### NC scope and separate product identity

The durable owner goal is that Embercade not be commercially used or exploited,
insofar as actual rights and the applicable grants permit. The intended NC scope
is confirmed independent own software (PolyForm), own prose and cleared artwork
(CC). It is a copyright-license restriction within that scope, not
a claim of technological enforcement, ownership of all APIs, or a universal
ban on every commercial act involving the mixed product. GPL rights include
commercial redistribution; upstream MIT and other grants likewise remain
unmodified. Necessary exceptions and rights outside the owner's control stay.
[GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html), PolyForm and CC
are distinct grants; final scope/compatibility needs legal review. In particular,
PolyForm's organization allowances and separate distribution permission need
review before claiming that every commercial distribution/exploitation is
forbidden. Those limits are recorded, not silently changed with custom wording.
No CC ShareAlike/source obligation is transplanted into the software license.

The terminology review found no existing misleading Embercade OSI/open-source
marketing claim in the reviewed README, AGENTS, ROADMAP, docs, LICENSES, notices,
resource/packaging metadata. The durable target wording is **non-commercial
source-available**; before grants are active, describe it as an intended model.
The [OSI definition](https://opensource.org/osd) does not allow excluding business
use and includes free commercial redistribution. Public source visibility would
not make this NC software OSI open source. Upstream projects may of course retain
their own open-source descriptions. Nothing is publicized by this audit.

Separately map the name **Embercade**, icon/logo, splash and Steam artwork as
product-identification assets. First document creators, permissions/assignments,
third-party elements, intended copyright grant and intended source-identifying
uses. No trademark registration, jurisdictional protection or exclusive naming
right has been established by this audit; no registered-mark symbol is justified.
The code license and any applicable name/logo rights are different layers.
An eventual identity policy could clarify accurate attribution versus falsely
presenting a modified product as the original, without changing upstream code
rights. Artwork CC licensing itself needs review where an image also identifies
the product: [CC's logo/trademark guidance](https://creativecommons.org/faq/#could-i-use-a-cc-license-to-share-my-logo-or-trademark)
warns against assuming copyright licensing preserves every identity-control goal.
No such policy, registration or artwork grant is introduced now.

### Third-party/source delivery and publication gate

The normal Stage copies the runtime venv, selected central upstream notices,
frontend binary/libraries/resources and generated descriptors. It does not
ship the full archived source snapshots, the 23 diffs or all build scripts as
an offline corresponding-source package. Python `.py` presence and a source
commit/hash do not establish complete source delivery for native binaries,
extensions, changes and build/install inputs. A future source-provision plan
must be verified under each applicable grant; no binary release here.

The actual venv also contains pip 26.2.1 (not one of the 22 locked requirements)
and vendored components; Pillow's wheel includes native codec/font libraries
beyond the 22 requirement-lock entries.
Inventory actual `dist-info`, vendored notices, `.so`/wheel libraries and
generated payload files, not just top-level pins. Per-source/per-stage mapping
must retain all original terms. Carbon, all shaders and textures, bezels,
fonts and compiled resources remain unchanged; user-supplied content is not
reclassified as shipped Embercade-owned work.

Public release remains blocked until at least: final GPL/API and client scope;
own rights/per-path contributions; approved root routing/full license texts;
Carbon version/embedded rights; complete shader notices/unknown file grants;
bezel rights/attribution; branding rights chain and identity treatment; GPL
source/change notices and actual dependency/payload obligations. The owner
selecting A closes the design-choice question only, **not these release gates**.

## Checks and unfinished work

The PolyForm architecture review against baseline `1c8b7f3` passes all
**459 unit tests** (24.347 seconds), including the documentation/context tests,
runtime smoke, frontend-library smoke and shader smoke (14 presets / 142
distinct dependency files). All 30 local Markdown links across the eight changed
documents resolve; fences and the complete 44-module/23-patch map pass.
`git diff --check` passes. Only eight Markdown paths change; runtime, patches,
assets, `pyproject.toml`, effective licenses and installed user state are unchanged.
No adapters, headers, contribution requirements, build/install or E2E are introduced.
GitHub visibility is verified PRIVATE.

At this pre-commit baseline all refs contain **69 commits / 811 blobs**:
803 UTF-8/no-NUL text blobs checked and eight binary/nontext blobs skipped,
with no bounded credential-pattern hit. Added documentation lines also have no
hit; values are never printed. This is not universal secret/privacy clearance.
Public-audit exits 1 with the same missing root LICENSE and three preserved
oversized branding masters, not a new finding. All legal release gates stay open.

Earlier evidence, retained with its exact baselines:

The Option A documentation review against baseline `128eceb6` passes all
**459 unit tests** (23.964 seconds), runtime smoke, frontend-library smoke and
shader smoke (14 presets / 142 distinct dependency files). All 14 local Markdown
links across the six changed documents resolve. The module-map check matches
44 distinct actual modules without omissions/duplicates, and patch counts are
22 Batocera plus one ES. `git diff --check` passes. Only the six documented
Markdown paths change; no effective LICENSE, adapter package, Python code,
patch, asset or packaging metadata is added/modified. The owner-confirmed
untracked duplicate of THIRD_PARTY_NOTICES was removed; its canonical root
document remains. No stage, install/update, host change or emulator E2E was
needed for this architecture-only review. GitHub visibility is still PRIVATE.

At that baseline all refs contain **68 commits / 805 blobs**: the bounded
credential-pattern scan checks 797 UTF-8/no-NUL text blobs and skips eight
binary/nontext blobs, finding no hits. New documentation additions likewise
have no hit. Values are never emitted. This is the same bounded category of
check below, not a universal secret/privacy clearance. Public-audit exits 1
as intended: missing effective root LICENSE and the three retained oversized
branding masters; no new finding. License/asset/source publication gates remain.

At the file-boundary follow-up, the unchanged runtime again passes all
**459 unit tests** (23.899 seconds), runtime smoke,
frontend-library smoke and shader smoke (14 presets / 142 distinct dependency
files). Documentation/context tests and the 26 Production unit tests also pass.
All 10 local Markdown links in the four changed documents resolve; `git diff --check`
passes. The scope gate deliberately leaves license/SPDX metadata unchanged.
No fresh Production Stage, install/update or interactive emulator run was
performed for this documentation-only review; existing installed runtimes and
user state were not changed.

At the initial asset-review baseline, all reachable refs contained 66 commits /
791 blobs. The follow-up at `9b3809d` contains **67 commits / 801 blobs**;
the refreshed scan covers all 793 UTF-8/no-NUL text blobs, skipping eight
binary/nontext blobs. A read-only text-blob scan found no private-key marker, GitHub/AWS token shape,
credential-bearing URL or nonempty anchored ScreenScraper developer credential,
DebugPassword/API-key/access-token/client-secret assignment. Only counts and
paths would have been emitted. This bounded pattern check is not proof that no
possible secret exists. Historical personal paths/test names remain a separate
publication/privacy decision; history was not rewritten.

`scripts/public-audit` remains expected-red: no root LICENSE has been introduced,
and three retained branding masters exceed its 5-MiB artifact-policy limit.
That size policy is separate from licensing; do not remove assets to hide it.

Pending final scope and grant approval, do not change `pyproject.toml` to
advertise a blanket PolyForm License-Expression. It presently makes no
license/classifier assertion.
After scope approval: complete a tracked per-file ownership/license manifest,
correct remaining credits, retain exact upstream license texts in source and
payload, verify GPL corresponding-source/change notices, review fonts/codecs/
all shipped shaders, confirm branding provenance, resolve bezel permissions,
then add the scoped root grant and consistent packaging metadata/tests.
No public-release blocker is closed by this file-boundary review.

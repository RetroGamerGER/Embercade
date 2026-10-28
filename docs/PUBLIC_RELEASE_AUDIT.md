# Public release audit — current scope

The adapter is implemented and scoped first-party grants are active; see
[LICENSING_1_0.md](LICENSING_1_0.md), [scope.json](../LICENSES/scope.json) and
[the implementation report](ADAPTER_SEPARATION.md). Batocera's LGPLv3 default,
explicitly GPL Configgen and individual exceptions are documented separately;
the old Buildroot-only licensing inference is superseded.

The previous captured bezels and embedded full shader collection are absent
from the new candidate. Their historical open-entry counts are not blockers
for the official RetroBat replacement or host shader package. Original credits
and individual notices remain. Carbon origin/theme-license identification and
attribution stay resolved; no completed resource audit was restarted.

The owner confirmed Canva AI creation of the branding on 27 October 2026.
[The origin record](BRANDING_ORIGIN.md) closes the prior missing-creator entry;
CC BY-NC-SA 4.0 is scoped to rights actually held. No new theoretical blanket
AI-rights blocker is substituted for that resolved question.

Public release remains **not authorized**. Local public preparation is now
authorized: sanitize the project tree and prepare an AppImage/source kit and
clean standalone Git export without publishing or changing the private history.
The original private repository must not simply be switched public: its older
versions and release assets are not part of the clean export.

The personal paths in the tracked private-sprint report are sanitized in the
current tree. The public export has a fresh root commit and contains no private
parent history. The three cleared original branding masters stay intact, with
exact size/hash exceptions in `compliance/public-source-files.json`; unreviewed
large files still fail the source audit. AppImage/source metadata identify a
public candidate prepared locally, never a completed publication.

Remaining actual publication actions after review:

- New frontend/build code uses protected per-user RetroAchievements keys and
  rejects the old compiled shared-key mode. [Implementation and verification](RETROACHIEVEMENTS_USER_KEYS.md)
  are complete automatically. The owner now accepts the deployed candidate on
  all three reference systems, with the known laptop 16:10 bezel limitation
  [explicitly retained](PRIVATE_DEPLOYMENT_2026_10_28.md#owner-acceptance--28-october-2026).
  That functional acceptance is no longer an outstanding gate. Older key-bearing
  private images remain private and are not candidates for publication. No
  extra application/shared-key grant is assumed.
- Matching source/notice preparation is complete locally for the frozen private
  candidate: original archives, patched covered sources, nested notices and
  LGPL rebuild/replacement instructions. [The delivery review](THIRD_PARTY_DELIVERY.md)
  records the result. Include these legal files in the eventual authorized
  public artifact and publish its matching source kit alongside it; this actual
  public delivery and approval remain unperformed.
- Publication hygiene is separate: use only the clean export or bundle. Keep the original
  private history, older release assets and private backup bundle private.
  No history rewriting or remote replacement is performed by preparation.

No specific new RetroBat-PNG license contradiction was established here. The
process/data architecture supports the reasoned independent-client assignment;
it is not a universal legal exemption or a provider/court clearance. No source
or binary was published, pushed, tagged or deployed during this sprint.

## How to read older findings

Everything below is a preserved older baseline. Its missing-root-LICENSE,
pre-grant, old resource counts and broad GPL hypotheses do not override the
current root notice/component assignment. Original evidence remains available
without treating completed/replaced cases as current unresolved resources.

## Historical audit and supporting evidence

Original audit scope: the complete tracked tree and all 37 commits reachable before this
audit from `master` at `c59eed8`. The review used `git ls-files`, full-history
object enumeration, path-only credential-pattern searches, MIME inspection and
manual review of public documentation, packaging inputs and pinned upstream
licenses. Secret values would not have been printed if found.

## Decision

**NOT READY**

The codebase is suitable for continued private release-candidate review, but a
public source or binary release remains blocked by the unresolved scope of the
owner-selected PolyForm own-software / CC prose-branding grants and unclear
redistribution rights for the captured console-decoration set. The precisely
pinned official Libretro shader bundle also needs a complete file-level notice
manifest before public binary distribution.

The repository remains **PRIVATE** while these questions are resolved. The
working theme, decorations and shader resources stay in the private runtime.
Removing required assets or features to force publication is not the release
policy. Any necessary replacement requires approval and validation of the
complete runtime before publication.

No release tag, version bump, binary release or repository-visibility change is
authorized by this audit.

The owner has made **Non-Commercial a hard goal** and selected **Option A** as
the design direction: compatible integration/patch terms,
PolyForm-Noncommercial-1.0.0 for confirmed independent own software,
CC-BY-NC-SA-4.0 for own prose/cleared branding, and unchanged third-party terms.
This supersedes the earlier CC-software proposal. Option B is not the current
goal. The intended own-software model is non-commercial source-available, not
OSI open source. This closes the design choice only, not ownership,
combined-work scope or redistribution gates. No
effective LICENSE, SPDX, contributor policy or adapter implementation is added.

## Clean

The following clean findings are historical results at `c59eed8`, not a claim
that later branding binaries or every current dependency were cleared.

- No ROM, BIOS, firmware, key, AppImage, emulator, Libretro core, shared
  library, executable or archive file is tracked at the audited tip.
- All tracked files inspected at the audited tip were text.
- No `.work`, build or distribution output is tracked.
- No private-key marker, GitHub-token shape, AWS access-key shape or
  credential-bearing URL was found in the current tree or historical blobs.
- No historical object name has a known ROM, firmware, provider, executable,
  library, credential or archive extension.
- No tracked file exceeds 5 MiB; the largest historical blob is approximately
  51 KiB.
- `.work` remains the boundary for host-specific JSON inventories, generated
  reports, runtime environments, stages and release-test payloads.
- Version remains `0.1.dev0`.

## Fixed in this audit

- Added a public, scope-based root roadmap and linked it from the README.
- Reworked the README around the user installation/setup/Doctor/start flow and
  limited platform claims to the environments actually tested.
- Added an explicit independent-project/no-affiliation statement.
- Added an explicit content policy: no ROMs, BIOS, firmware, keys, emulator
  binaries, Libretro cores, Xenia AppImage or provider download links.
- Clarified that the 39 `READY` rows are representative end-to-end launch-path
  evidence, not all-game compatibility claims.
- Removed tracked ROM and BIOS host-inventory snapshots. Future inventory
  Markdown defaults to ignored `.work/reports` alongside host-specific JSON.
- Removed local collection-directory names from generated compatibility
  documentation while retaining detailed evidence in ignored host reports.
- Replaced personal development paths and named commercial test titles in the
  active development harness with an ignored local manifest and a path-neutral
  example.
- Generalized personal paths and named-title evidence in current handoff and
  test material.
- Added targeted ignore rules for common game-content, firmware, credential
  and AppImage extensions/directories.
- Expanded third-party notices with the license facts established from the
  exact pinned upstream trees.
- Added Batocera, EmulationStation and Carbon license/attribution texts to the
  central staged license directory.
- Added `scripts/public-audit` for repeatable current-tree checks. It is
  expected to remain red until a root project license is selected and added.

## Remaining blockers

### Embercade project license

The owner has selected PolyForm Noncommercial 1.0.0 for confirmed independent
Embercade-owned software, and CC-BY-NC-SA-4.0 for own prose/cleared branding.
Neither grant is introduced. The requested conflict gate was reached:
`ui_data.py::build_ui_data()` imports Batocera builders in the caller
interpreter; own payloads in `batocera_config.py`, `standalone_decoration.py`,
`runtime.py::probe_runtime()` and `scripts/runtime-smoke` import Batocera
modules within child interpreters. Two explicit integration-test payloads in
`tests/test_runtime.py` and `tests/test_visual_runtime.py` do likewise. These
are seven API-bearing paths, not a finding that every line in those files or
the entire tree is GPL. Exact GPL repository/package coverage remains part of
the review. External subprocess invocation does
not automatically establish that these payloads are independent works. Their
final scope and compatible contribution terms require approval before a scoped
root grant, SPDX headers or packaging license metadata are added. No alternative
license beyond the owner's new decision is selected by the audit. Exact
evidence and the updated A–L file-group matrix
are in [LICENSE_SCOPE_REVIEW.md](LICENSE_SCOPE_REVIEW.md).

This is a potential combined-work compatibility conflict requiring review,
not a legal finding that every Embercade source file is GPL. PolyForm is a
software-specific target, not automatic GPL compatibility or proof of independence.
Its official text/SPDX, NC/notices/patent review and CC comparison are documented
there. No project-license blocker is closed.

The follow-up at `9b3809d` classifies all 44 own Python modules and all
**22 Batocera plus one ES patch (23 total)**. It distinguishes same-interpreter
API use, embedded child programs, external command/file interaction and reusable
own helpers. Git introductions and a bounded comparison with the 411 Python
files at the Batocera pin support provenance investigation but do not prove
complete authorship or legal independence. Three possible structures remain
documented, with the latest owner choice updating the first: scoped compatible
adapters plus independent PolyForm software/CC prose; compatible software plus
separate CC prose/cleared branding; or stronger separation if
needed. The owner now selects the first as Option A; the second is not pursued,
and stronger separation is only a contingency requiring substantive review.
No structure has been implemented. Original asset/runtime behavior and pending
license/SPDX/package metadata remain unchanged.

The Option A design from `128eceb6`, updated for PolyForm against `1c8b7f3`,
specifies six zones and four narrow API adapters in a separate Python namespace,
with a shared SystemConfig helper and empty initializer. The current 44 modules
are grouped into 23 lower-coupled PolyForm candidates, 17 with additional
interface/dependency review, and four mixed
API-bearing modules. This is not a clearance of 40 NC files. A six-file future
adapter package plus 22 Batocera patches would be 28 Zone-4 integration
paths, plus two API test programs (30, or 31 with a separate smoke program).
The currently counted source/patch API inventory is 29 paths. These are technical
inventories, not automatic legal scope. Root-notice/license-tree, SPDX and
contributor designs remain prospective and explicitly non-effective.
The six zones are now independent own software, own prose, cleared branding,
GPL-bound integration, MIT ES material and third party, in that order.
The current mixed package is not eligible for an unreviewed blanket PolyForm
License-Expression. Modern packaging support is available; wheel/sdist scope
and complete offline payload scope/notices require separate positive mappings.
No actual LICENSE, pyproject/SPDX or contributor policy is activated.

### Minimum Option A publication gates

- Final API/client/program boundaries and exact upstream package-license coverage.
- Independent PolyForm allowlist and scope/terms review, including distribution
  and organization allowances versus the owner's commercial-exploitation goal.
- Per-path/per-contribution ownership and compatible grants, including copied and
  generated source/data rather than an import-only classification.
- Approved scoped root notice, full license texts, SPDX and packaging metadata.
- Preserve Carbon's documented CC-BY-NC-SA credit and original mixed-version
  notice; account separately for embedded third-party fonts/logos/audio.
- Complete shader dependency/notice mapping and unresolved exact-file grants.
- Decoration rights and required attribution/watermark/derivative permissions.
- Branding creator/rights chain and separate product-identity treatment.
- GPL corresponding-source/change notices and actual payload dependency coverage.

The normal offline payload contains runtime Python, selected central notices,
frontend binaries/resources and generated metadata, not a verified complete
source/patch/build-input delivery package. A commit/hash alone is not evidence
of fulfilled corresponding-source obligations. Inventory actual venv contents,
pip-vendored components and Pillow/native wheel libraries as well as the 22
top-level locked requirements; keep their original grants/notices. No binary
release or notice completeness is approved by this design.

### Carbon and branding coverage

The completed 2,271-file comparison already establishes the recipe's Carbon
origin. The exact theme's CC-BY-NC-SA notice and Fabrice Caruso / Eric Hettervik /
Nils Bonenberger credit are confirmed by RetroBat's linked sources; the owner
closes that theme-license/attribution item as DONE. The theme also credits maioni.
Its 2.0 heading and 4.0 legal body remain unmodified as an upstream notice
inconsistency, not grounds to label the theme unlicensed. Independently licensed
fonts/logos/audio retain separate rights; the completion does not relicense them.
Embercade branding's user-supplied masters/derivatives have a separate recorded
creator/public-rights gap. Neither theme nor foreign embedded material receives
an Embercade-owned SPDX identifier.

### Console-decoration redistribution rights

**Current status: specific decision cases documented; no publication approval.**
The owner requested a bounded interpretation of the completed audit, not a new
technical investigation. See [the decision report](BEZEL_DECISION_1_0.md) and
[complete path/reason table](BEZEL_DECISION_FILES.csv). There are 8 PNGs with an
observed Duimon/ND notice, 107 further Duimon-linked PNGs with known general
permission sources but unmapped variant scope, and a 35-path follow-up cohort.
Within that cohort, Spectravideo now has a reasoned project-license assignment;
34 final-file mappings remain open, including two preserved V31-import files
linked to the historical dispute. The 152 INFO/LAY paths are not another 152 unlicensed
pictures. No file-specific infringement or denial is demonstrated by the
audit. No complete publication clearance or permission to contact contributors,
change assets or publish follows from this distinction.

The staged `consoles` decoration set originates from Batocera's pinned
`batocera-bezel` input. Its Batocera package file declares no license, and the
captured subset contains no separate license or attribution file. This does
not mean no embedded notices or historical grants exist.
[BEZEL_PROVENANCE.md](BEZEL_PROVENANCE.md) and its
[per-file history/hash companion](BEZEL_PROVENANCE.json) inventory all 302
actual paths, 33 preserved symlinks and 187 resolved content blobs. The recipe
has 144 overwritten paths; winning-entry and merged-tree link targets are
distinguished and match reference, stage and MainRig installed content.

Recorded contributions or specific source credits associate 231 paths with
Duimon, 10 with Mikael42 and 17 with Fery65/Lorenzolamas; 44 lack that
creative-source association. These are path-based evidence-routing counts,
not sole-original-author or permission clearances. Full introductions,
changes, heuristic renames/copies and author/committer records are retained.

Duimon's original May 2021 statement and historical explicit SA4.0 grants in
Retroarch-Overlays and the exact Misc/Batocera source project are positive
permission evidence; later source releases use ND4.0. No final content OID
matches the compared source trees/history; this does not disprove derivation.
Six PNGs contain unversioned ND/Duimon XMP text and two further inspected PNGs
show raster labels. TheNamec's historical SA and later ND releases also need
exact-version/derivation mapping. All 302 exact-file coverage statuses remain
UNKNOWN, with no complete redistribution clearance. The historical attribution
dispute is recorded as a dispute, not a verdict.

Transport preserves all bytes/link texts. Libretro may generate transformed
PNGs; standalone only scales/clips in memory. Clipping can conceal a credit,
so unchanged bytes do not certify visible attribution or blanket ND compliance.
Clarification drafts are prepared, not sent. Public payloads must establish
the applicable rights/terms and include the required notices.
If rights cannot be established, an approved, functionally validated replacement
is required. Because bezels are part of the intended scope, this remains a
release blocker; removing them without a working replacement is not acceptable.

### Shader notice completeness

The previous Batocera-captured mixture has been replaced by the official
Libretro `slang-shaders` tree at commit
`84bcd19a854348c0e6a1d3db814a76f11fb6f011`, verified from its source archive
with SHA-256. The complete tree and its nested notices are preserved, while
`resources/shaders/catalog.toml` retains its original observations. The current
[targeted follow-up](LICENSE_SCOPE_REVIEW.md#targeted-shader-notice-follow-up--27-october-2026)
updates the open entries using pinned Slang/GLSL sources, authors and actual
port/data differences. NewPixie's frame has an explicit MIT OR Unlicense source,
Simpletex's adapted Stephen Gilbert texture is CC-BY-SA-3.0, and the six handheld
grey LUTs have the author's public-domain declaration. Four named legacy-code
grant gaps remain (LCD Grid and three LUT helpers); EasyMode's known GPL notice
has no specified version. Already established licenses remain established.
This is not a blanket UNKNOWN for the collection or a new whole-tree audit.
Future public delivery still needs the applicable notices/source for its actual
contents. No shader, preset or texture is removed or modified.

### Historical personal development data

No secret or protected binary was found, so this audit did not rewrite history.
Nevertheless, 36 historical blobs across `AGENTS.md`, `docs/PRODUCTION.md`,
`docs/PROJECT_STATE.md`, `resources/defaults/es_systems.cfg`,
`scripts/ui-prepare` and `tests/test_production.py` contain old local usernames,
mount paths or a second-host nickname. Historical test material also names
commercial titles. Current files are generalized, but the owner must decide
before making the repository public whether to publish that history or create a
clean public history. Rewriting the existing private remote requires explicit
approval and coordinated force-push handling.

## Manual review before publication

- Resolve the scope of the selected PolyForm software and CC prose/branding
  grants with awareness of direct GPL/Python integration and target-bound patches.
- Establish the console decoration terms and notices; if that proves impossible,
  obtain approval for a replacement and validate the complete runtime.
- Produce and verify a complete shader attribution/license manifest.
- Decide whether the complete current history may be public or whether a clean
  public history is required for privacy; 37 commits was the original audit scope.
- Verify that public release artifacts contain the Batocera, EmulationStation,
  Carbon, FreeImage, SDL2_mixer and applicable shader license texts/notices.
- Confirm source-availability obligations for every GPL component in any
  published binary payload.
- Clarify Carbon's conflicting CC-BY-NC-SA version statements and embedded
  font/artwork rights, then review NC/SA terms against the distribution model.
- Review the selected user-supplied branding masters and their derivatives in
  `resources/branding` before publication. Their source/use map is recorded in
  that directory's README; being supplied for the private build is not itself
  an explicit public-redistribution license grant.

## License findings

| Component | Evidence at pinned input | Audit result |
|---|---|---|
| Embercade original work | `LICENSES/README.md`, `LICENSE_SCOPE_REVIEW.md` | Option A: independent software PolyForm target; own prose/cleared branding CC target; scoped grants not introduced; ownership/client scope pending |
| Batocera launcher/common/plugins/builders | Batocera root `COPYING` describes Buildroot GPL-2.0-or-later; inspected packages lack separate grants | Recorded repository evidence, subject to exceptions; confirm exact package coverage rather than assuming an umbrella for all fetched sources/assets |
| Batocera configgen | Buildroot metadata says `GPL`; Batocera root `COPYING` | Treat as GPL-covered; exact notices/source obligations apply |
| Embercade Batocera patches (22) | Diffs include retained/derived upstream code; exact targets in Scope Review | Preserve target terms and approve own additions compatibly; the Buildroot-bundled-patches paragraph is not an automatic grant for new Embercade additions |
| Embercade ES patch (1) | Three MIT ES target files, retained source/context plus own changes | Preserve MIT notice; own additions' grant pending; embedded dependencies separate |
| Batocera EmulationStation | pinned root `LICENSE.md` | MIT; root notice must accompany binary distribution |
| Carbon theme | exact upstream file match, theme metadata/readme | CC-BY-NC-SA grant present but 2.0 heading/4.0 body ambiguity and embedded rights remain; retain attribution/text and NC/SA conditions |
| FreeImage 3.18.0 | hash-locked source and three license texts | Payload preparation includes verified notices/texts |
| SDL2_mixer 2.8.2 | hash-locked source/license and decoder headers | Payload preparation includes verified zlib/decoder notices |
| Libretro shader bundle | Official `libretro/slang-shaders` commit and archive hash, nested notices, curated per-selection metadata | Exact provenance is established; heterogeneous and incomplete per-asset notice accounting remains a blocker for public binary payload |
| Batocera console decorations | exact 302-path pinned recipe/history matrix | No pack-level grant; eight observed ND hints; exact-file coverage UNKNOWN, blocker |
| ES controller/savestate data | pinned Batocera/EmulationStation trees | Covered by authoritative upstream repository/file terms; retain upstream notices |
| Generated system/features/defaults | generated from pinned Batocera descriptors | Record pin/source and preserve applicable Batocera terms |
| Empty `gamesdb.xml` shim and Embercade policy/config | tracked Embercade files | Part of still-unlicensed Embercade original work |

## History audit

The PolyForm review against `1c8b7f3` refreshes the bounded scan: **69 reachable
commits / 811 blobs**, including 803 UTF-8/no-NUL text blobs and eight skipped
binary/nontext blobs. No defined credential-pattern hit in history or added
documentation lines; only counts/object IDs, never values, would be printed.
All 459 unit tests, runtime/frontend-library/shader smokes, 30 local links,
44-module/23-patch coverage and `git diff --check` pass. Only eight Markdown
paths change. Public-audit is expected-red with the unchanged absent root
LICENSE/three preserved oversized masters. Runtime/assets/installed user state,
license metadata and PRIVATE visibility stay unchanged. No legal gate is closed.

Follow-up at `4a9fca2`: all reachable refs comprised **66 commits / 791 blobs**.
A path/count-only text-blob scan found no private-key marker, GitHub/AWS token
shape, credential URL or nonempty anchored ScreenScraper developer credential,
DebugPassword/API-key/access-token/client-secret assignment. This bounded check
does not certify absence of every possible secret. No values were printed and
no history was rewritten. The counts below belong to the earlier audit.

The file-boundary follow-up at `9b3809d` refreshes that same bounded scan:
**67 reachable commits / 801 blobs**, including 793 UTF-8/no-NUL text blobs
and eight skipped binary/nontext blobs. No credential-pattern hit was found;
only counts/paths were emitted. Current-tree public-audit still reports exactly
the missing root LICENSE and three retained oversized branding masters, not a
new source or credential finding. No visibility/history change was made.

The Option A design review against baseline `128eceb6` refreshes the bounded
scan again: **68 reachable commits / 805 blobs**, 797 UTF-8/no-NUL text blobs
checked and eight binary/nontext blobs skipped. No category above matches;
new documentation additions likewise contain no match. Only counts/object IDs,
never values, would be reported. All 459 unit tests, runtime/frontend-library/
shader smokes, 14 local documentation links, complete 44-module/23-patch map
checks and `git diff --check` pass. Public-audit remains expected-red with the
same absent root LICENSE/three oversized retained branding masters. No runtime,
resource, installed user state, visibility or history change is made.

- Reachable commits reviewed before the audit commit: 37.
- Private-key/token/credential-shaped historical blobs: 0.
- Historical risky-extension object names: 0.
- Historical generated `.work`, build or distribution paths: 0.
- Historical personal-identifier blobs: 36, limited to the files listed under
  the privacy blocker above.
- Historical named-test-content blobs: 57 versions across project-state,
  development-harness and test files; no game content itself was present.

The 20 largest historical blobs before this audit were:

| Size | Object | Path |
|---:|---|---|
| 51 KiB | `a650599e` | `docs/ROM_INVENTORY.md` |
| 47 KiB | `79365b0f` | `tests/test_visual_runtime.py` |
| 47 KiB | `d2ddc2d3` | `tests/test_visual_runtime.py` |
| 47 KiB | `cbaf0592` | `tests/test_visual_runtime.py` |
| 46 KiB | `314f5e89` | `tests/test_visual_runtime.py` |
| 45 KiB | `b94e4971` | `tests/test_visual_runtime.py` |
| 45 KiB | `4db49288` | `tests/test_launcher.py` |
| 44 KiB | `b5dea0f4` | `tests/test_visual_runtime.py` |
| 43 KiB | `69a65660` | `tests/test_launcher.py` |
| 43 KiB | `8d250d03` | `tests/test_launcher.py` |
| 42 KiB | `e911735b` | `tests/test_launcher.py` |
| 36 KiB | `b58c8405` | `tests/test_launcher.py` |
| 36 KiB | `3d8c2c67` | `tests/test_launcher.py` |
| 35 KiB | `6765fa58` | `src/embercade/cli.py` |
| 35 KiB | `7612b71f` | `tests/test_launcher.py` |
| 35 KiB | `842a37f5` | `tests/test_launcher.py` |
| 34 KiB | `87942902` | `tests/test_visual_runtime.py` |
| 33 KiB | `6a066503` | `src/embercade/cli.py` |
| 33 KiB | `39e3dde2` | `docs/PROJECT_STATE.md` |
| 33 KiB | `9004ad1a` | `src/embercade/compatibility.py` |

These are all text source, test or documentation blobs. The deleted host
inventory remains in private history but contains metadata only, not ROM data.

## Repeatable checks

Run:

```sh
./scripts/public-audit
```

The check covers required public documents, forbidden tracked extensions,
generated-tree leakage, personal host paths, common private-key/token shapes
and tracked files above 5 MiB. Full-history and third-party license review remain
manual release-gate steps.

On the current tree this check reports the absent root `LICENSE` and three
retained branding masters above its 5-MiB limit: the icon, landscape and portrait
JPEGs in `resources/branding/source/`. The size finding is an artifact-policy
check, not a license finding. The historical clean-file/size results above
describe the earlier audited tip; they do not describe these later additions.

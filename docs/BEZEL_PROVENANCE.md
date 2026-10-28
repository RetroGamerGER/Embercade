# Historical captured-bezel evidence

> Historical evidence retained unchanged below. The current effective assignment
> is [LICENSING_1_0.md](LICENSING_1_0.md), with the corrected
> [Batocera GPL/LGPL distinction](BATOCERA_COMPONENT_LICENSES.md) and implemented
> [backend separation](ADAPTER_SEPARATION.md). Earlier prospective grants,
> blanket-scope assumptions and old captured-resource blockers are not current
> release findings. The removed captured-bezel and bundled-shader inventories
> are not the new RetroBat/host-package payload. No previous full audit was repeated.

## Preserved original report

# Console bezel provenance and redistribution review

**Later targeted source lookup:** [35-PNG follow-up](BEZEL_35_LICENSE_FOLLOWUP.md)
and [individual results](BEZEL_35_LICENSE_FILES.csv). Spectravideo has a reasoned
CC-BY-NC-SA-4.0 RetroBat project-scope assignment, marked as an inference;
34 final-file mappings remain open. The 35-path groups below are the retained
decision baseline, not a claim that this new source chain does not exist.
No graphic bytes, image hashes or whole histories were newly examined.

**Current decision detail:** [file-by-file interpretation](BEZEL_DECISION_1_0.md)
and [302-row decision list](BEZEL_DECISION_FILES.csv), 27 October 2026. The old
uniform UNKNOWN field below is historical, not a finding of 302 unlicensed
images. Current dimensions: 8 PNGs with observed Duimon/ND notices, 107 further
Duimon-linked PNGs with general author-permission sources and unmapped variant
scope, 35 PNGs without a concretely mapped grant, and 152 technical INFO/LAY
entries. Two of the 35 have a specific historical V31 dispute link. No actual
file-specific violation/denial is established. The new interpretation reuses
this audit and the stored RetroBat receipt; no new asset/hash/history scan.

**Historical evidence update:** On
27 October 2026 the owner authorized reusing this completed audit and recording
the received Batocera/community information for license preparation. This
supersedes the previous pause only for that bounded documentation work. No
technical asset comparison was repeated, contributor contacted or functional
asset/watermark removed or replaced. A covered CC BY-NC-ND license allows
unchanged noncommercial redistribution with its conditions; the ND term is
not itself a redistribution ban. Unknown art does not inherit that grant.

## Community evidence update — 27 October 2026

The owner's [public Reddit post](https://www.reddit.com/r/batocera/comments/1xf9tyu/)
reports the Batocera team's response: many people contributed the artwork, the
team cannot establish the exact provenance/license of every image, and Duimon
was the last major contributor, with watermarked CC BY-NC-ND artwork. This is
a public owner summary of the team reply, not a copy of the private original
or a pack-wide grant by the team.

The owner supplied [derik-for-real's comment](https://www.reddit.com/r/batocera/comments/1xf9tyu/comment/19rqignohx4pv/),
readable on 27 October. It relays another community member's explanation that
ND restricts derivatives rather than forbidding noncommercial redistribution.
That distinction is supported by [CC BY-NC-ND 4.0 sections 2(a) and 3(a)](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en):
covered material can be shared noncommercially with attribution and notices;
sharing adapted material is restricted. Section 2(a)(4) separately permits
necessary technical format modifications, so the comment's size-change example
is not a rule that every resize is a prohibited derivative.

This community explanation is not a verified rights-holder permission for all
files. The exact coverage of originals, inherited night/standalone variants,
other contributors and retained/visible credits remains separate. An applicable
public grant does not require redundant individual permission merely because
it contains ND. Historical UNKNOWN rows below remain evidence of unresolved
mapping, not a denial or a claim that ND forbids sharing. No per-file result
was silently changed to CLEAR from the comment alone.

The [current scope preparation](LICENSE_PREPARATION_1_0.md) records the planned
license split and remaining decisions. Existing comparisons and their limits
below are reused. RetroAchievements is a separate owner-handled API question;
there will be no new AppImage until it is clarified.

## RetroBat reference — 27 October 2026

[RetroBat's official decoration README](https://github.com/RetroBat-Official/retrobat-bezels/blob/5ce1f6ed32eb9f3df8ae14483afc4d1e3ef35d65/README.md)
explicitly identifies its sets as a Batocera fork bundled with each install.
RetroBat's [build configuration](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/build.ini)
and decorations submodule link that repository. This confirms a real shared
distribution lineage outside Batocera and is retained as positive evidence.

Only the new RetroBat tree metadata was compared with terminal source paths
already recorded in this matrix. Of the 302 existing rows, 256 have the same
terminal source path in that RetroBat revision; 156 also share the Git blob.
The other 100 present paths differ, while 46 paths are absent there (including
30 resolving through Embercade's standalone-night layer). These are row counts,
not distinct artworks or permission counts. Different bytes/paths are not a
finding of different authorship, a new license or missing permission.
No PNG was fetched, rescanned or modified for this comparison.

The complete RetroBat bezel tree at `5ce1f6e` contains the README but no separate
LICENSE/COPYING/credits document. Its parent project's [license](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/license.txt)
preserves upstream terms and describes its project work under CC BY-NC-SA 4.0;
it does not supply a named grant for every foreign image or undocumented
permission agreement. Keep applicable known author grants and credits. The
existing historical matrix is not rewritten to infer either blanket clearance
or a redistribution prohibition from RetroBat's use. No team contact occurred.

## Completed technical evidence — historical baseline

Audit baseline: `044b59c3f0bd16b321c3d4ab0b120f83b89b7932`.
Scope: the **302 actual console-decoration paths**, not the entire upstream
collection. This is an evidence inventory, **not a license grant, legal opinion
or public-release clearance**. The repository remains PRIVATE. No image,
layout, watermark, runtime code, installed profile or reference checkout is
changed during that audit. No contributor was contacted by that audit.

## Exact payload and recipe

The Batocera pin is `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`.
Its [bezel recipe](https://github.com/batocera-linux/batocera.linux/blob/9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48/package/batocera/emulators/retroarch/batocera-bezel/batocera-bezel.mk)
fetches `batocera-linux/batocera-bezel` at
`77a3239f3f0682fcf9e6050f07b40677395e5db7` (**P** below).
The recipe copies in this order, replacing same-path entries:

1. `default_unglazed/*`.
2. `default_nocurve_night/default.*`.
3. `default_nocurve_night/systems`.
4. `default_standalone_night/systems`.

The recipe also installs other packs, but they are **not** in this captured
Embercade console subset and are not evaluated here. The sibling captured
resource bundle is a read-only input. Its decoration-tree digest in
`resources/resource-bundle.lock` is
`3dd818e528e8889f414de83deafcbebd205a92a028c1c46be424c489b4f43a52`;
this is an integrity pin, not a Git commit or license.

All matrix paths have the installed/staged prefix
`share/embercade/resources/batocera/datainit/decorations/consoles/`.
The audit compares the existing `.work/stage`, captured reference bundle and
MainRig user installation; production does not read this audit cache.

| Measurement | Verified result |
| --- | ---: |
| Paths | 302 |
| PNG / INFO / LAY paths | 150 / 151 / 1 |
| Regular paths / symbolic links | 269 / 33 |
| PNG / INFO symbolic links | 6 / 27 |
| Distinct resolved content blobs | 187 |
| Winning entries: unglazed / nocurve-night / standalone-night | 73 / 201 / 28 |
| Resolved content: unglazed / nocurve-night / standalone-night | 71 / 201 / 30 |
| Paths overwritten by a later layer | 144 |
| Total replacement events across those paths | 164 |
| Stage / reference / installed content identity | 302 / 302 |
| Preserved link texts | 33 / 33 |

A link's Git blob contains its target text, not the image/layout bytes.
Links resolve **after** the layers merge. For example, unglazed
`systems/amiga.png → amiga500.png` and `amiga.info → amiga500.info`
remain as links, but their targets are the later standalone-night files.
The old `final-resolved.tsv` is a correct winning-entry list, not a resolved
content hash list. Treating its 33 link OIDs as PNG/INFO hashes was inaccurate.

[BEZEL_PROVENANCE.json](BEZEL_PROVENANCE.json) records each winning entry,
every overwritten layer, link text/resolution, terminal content path, source
commit, full Git OIDs and resolved SHA-256. The table below contains every
staged path exactly once; the JSON is its detailed evidence companion.

## Evidence and confidence rules

A Git author/committer proves a recorded contribution, **not** ownership of
all pictured art, authority to relicense it, or permission from earlier authors.
An explicit file/group credit is stronger than a broad “mostly from” import
message. Appearance is never used to assign creators. Author names and
committer names are retained separately; private/contact email fields are not
needed in this matrix.

Per-source histories record introductions, subsequent changes, old/new paths,
authors, committers, messages and explicit source references. Copy/rename
following uses Git similarity detection; it is **heuristic**, not proof of
original creation. A copy is recorded as an introduction at the destination
and separately as a possible predecessor. Direct contribution counts stop at
a copy boundary; earlier claimed/heuristic lineage is not silently added.

The Duane Huseby spelling in raw Git metadata is associated with Duimon by
the public [commit-account association](https://github.com/batocera-linux/batocera-bezel/commit/75d07c0291951c5ad33577bfbf9b0944e3f42d58?diff=split), the exact contribution in [PR #57](https://github.com/batocera-linux/batocera-bezel/pull/57)
and merge `c3f5fefcf7f1d1d1024372172bf30f3e3b9ddcc1`
from `Duimon/Duimon`, not by guessing from a name.

### Contribution/source routing — not rights clearance

| Exclusive final-path category | Paths | Evidence and limit |
| --- | ---: | --- |
| D — Duimon named / publicly corroborated PR account | 231 | 147 raw Duimon names and 86 Duane/PR-line associations overlap in two paths; Git account/contribution, not sole-original-creator evidence |
| M — Mikael42 account or specific group credit | 10 | One account contribution plus ten concrete group credits overlap; broad “mostly Mikael42” is excluded from positive counts |
| Other explicit source credits | 17 | Fery65 16; Lorenzolamas one (`spectravideo.png`, [`d634f16d`](https://github.com/batocera-linux/batocera-bezel/commit/d634f16d53a8c29a5520629241b0a9b8824206a9)) |
| UNKNOWN creative source | 44 | Maintainer changes/history exist, but no positive original-art source assignment |
| Total | 302 | 258 positively contribution/source-associated; zero sole-rightsholder clearances |

These are **staged path** counts including layouts and aliases, not distinct
artworks or mutually exclusive creators. Other contributors can occur within
a D/M history. Fery65 appears in five additional heuristic copy ancestries;
Genetik57 has a historical joint-credit statement beyond a copy boundary,
not another positively assigned final path. The 466 source-path histories
and 89 commit records (1,811 events) preserve these distinctions. An earliest
followed Git event is not proof of where the underlying artwork originated.

The final 150 PNG paths resolve to 35 unglazed, 100 nocurve-night and 15
standalone-night contents. The original audit left complete clearance unresolved
for all 302 rows, including INFO/LAY without deciding protectability. That
uniform field does not mean every row lacks permission or is an image.
The [current decision groups](BEZEL_DECISION_1_0.md) distinguish observed licenses,
general grant sources, concrete missing mapping and technical data. The old
night/standalone scope flags are questions, not an automatic ND violation.

## License evidence, version chronology and exact-file limits

**E0 — Batocera input.** At P, root/subdirectory LICENSE, COPYING and NOTICE
searches establish no pack-level grant. The root README describes installation.
The parent Batocera code COPYING and package's download/install instructions
do not license separately fetched artwork. No package license declaration
covers these exact images. This does not prove that no rights holder ever
gave permission elsewhere.

**E1 — Duimon's original public statement.** The author's
[1 May 2021 post #1220](https://forums.libretro.com/t/duimon-hsm-mega-bezel-graphics-and-presets-feedback-and-updates/28146?page=61)
offers broad use of his graphics/source and mentions a 43-system Batocera
pack in `Misc-Overlays-Borders-Bezels/Batocera`. This is real permission
evidence, not just somebody else's quotation. It still needs identification
of covered originals, later versions and other people's contributions.

**E2 — Duimon repository grants.** The canonical public source is now
[Duimon/Retroarch-Overlays](https://github.com/Duimon/Retroarch-Overlays);
the old `Duimon/Overlays` URL is not the current canonical source.
README at `aef93777dde609795723099ae2ee14528c83f0dd` (5 November
2021) explicitly applies **CC-BY-NC-SA-4.0** to its assets/code/documentation;
`3399a18baff8cb3928f1d0d67cb0faace54802f1` confirms it.
`34aeb6cd5e53be437464f7e7d6d4d3720dec8218` (11 November) removes
that text; it does not add ND. README at
`2a6f71f24ccf1fc591de5f0c51dd342ee216887f` (14 December) adds
**CC-BY-NC-ND-4.0**. `524ae6580046307f32c231ad5668778365bdfaff`
adds LICENSE.md in March 2022. Both README and
[LICENSE.md at reviewed revision](https://github.com/Duimon/Retroarch-Overlays/blob/16b11e93a6e43b6b0e82bf1384f20dd6ea7da38a/LICENSE.md)
`16b11e93a6e43b6b0e82bf1384f20dd6ea7da38a` contain ND4.0.
A later change/removal is not automatically a retrospective revocation of a
valid CC grant for material previously licensed under it.

The cached Duimon history includes a promisor clone with missing **blobs**.
All cached commit trees are traversable: 6,160 distinct reachable blob OIDs,
3,371 absent blob contents, no missing trees in that traversal. Comparing
the 187 actual final content OIDs with those known OIDs gives **zero matches**.
This is stronger than comparing only the old 3,621-object list, but limited
to the cached reachable history; it is not proof of non-derivation, completeness
of deleted/private repositories, or a comparison of all underlying PSD layers.

**E3 — Historical attribution dispute.** The
[November 2021 discussion](https://forums.libretro.com/t/duimon-hsm-mega-bezel-graphics-and-presets-feedback-and-updates/28146?page=101)
contains conflicting interpretations of permission and TheNamec's claim about
Commodore derivatives/removed credits. It records a dispute, not a verdict.
Current `amiga1200.png` and `amigacd32.png` are identical to Batocera's
`5f95003` V31 import entries mentioned in that discussion. This identifies
a surviving import group, not exact identity to TheNamec originals or proof
of infringement.

**E4 — TheNamec.** The original
[Commodore pack](https://github.com/TheNamec/megabezel-commodore-pack)
has a historical [RC2 README](https://raw.githubusercontent.com/TheNamec/megabezel-commodore-pack/RC2/README.md)
at `a0cc1c4813ad8b67edb8b367103b2ba96a34a704`
with an explicit **CC-BY-NC-SA-4.0** grant, section 6.1.2; later releases
use ND4.0 and add watermark restrictions. These conditions apply to actually
covered releases, not automatically every Batocera adaptation. The exact
original version/derivation chain for the claimed staged Commodore art remains
unverified. TheNamec is a clarification contact, not an assigned sole creator
for every Commodore-themed image.

**E5 — Embedded hints.** A read-only inspection of all 150 PNGs finds 127
Adobe-XMP blocks, one Software entry and no standardized author/rights/license
fields. Six XMP TextLayers contain an unversioned Duimon CC-BY-NC-ND label:
`arduboy`, `gamegear`, `gb2players`, `gp32`, `macintosh`, `wasm4`.
Visible equivalent side labels were inspected in the actual PS2 and SNES
night PNGs. These eight observed files have asset-specific attribution/license
**hints**; lack of a standard metadata field does not mean lack of a notice.
The exact version, applicable original grant and complete underlying rights
still need confirmation. Other raster-only labels may exist: this is not an
OCR/visual certification of every PNG.

**E6 — Exact original Misc/Batocera source.** The publicly accessible
[Misc repository at inspected HEAD](https://github.com/Duimon/Misc-Overlays-Borders-Bezels/tree/899d17c645934c7c705ca8f4bd732e83bf2952da/Batocera)
is the actual project named by E1. `0d898dd9dd0982d4dc2cf99838b6ddc4252ee61a`
introduced `Batocera/decorations` on 1 May 2021;
`dfa4cf00a528447901e77145959c9bda6b068904` renamed it to
`decorations_OLD` on 5 January 2022. Its 98-blob tree
`cddb9846345138ce21f38f4fcce53fe5ab183f89` is unchanged at introduction,
the historical SA release and inspected HEAD
`899d17c645934c7c705ca8f4bd732e83bf2952da`.
[LICENSE.md at `e10167d97a03055e995788897f122d3cb507947e`](https://raw.githubusercontent.com/Duimon/Misc-Overlays-Borders-Bezels/e10167d97a03055e995788897f122d3cb507947e/LICENSE.md)
(7 November 2021) and README expressly grant **CC-BY-NC-SA-4.0** for
assets/code/documentation. Later releases declare ND4.0. This establishes
the original path and its real historical grant, rather than calling it
inaccessible or generically unlicensed. Read-only API tree/OID comparisons
at introduction (167 whole-tree blobs), SA release (263) and inspected HEAD
(273) give **zero** matches with the 187 final Embercade content blobs.
No asset bytes were downloaded. These three trees are not every historical
version; modified/composited-source coverage still needs review.

### Status and terms

- **CLEAR / CLEAR WITH ATTRIBUTION:** only a demonstrated exact-file grant
  with resolved obligations; none awarded here.
- **NEEDS PERMISSION:** known terms demonstrably exclude the intended act;
  do not fabricate a denial where the grant is unknown.
- **NEEDS LEGAL REVIEW:** an evidenced grant/scope/terms issue needs review.
- **UNKNOWN:** exact-file applicable grant/version/rights are not established.

An UNKNOWN record is not a claim that the author prohibited redistribution.
It requires rights clarification before public delivery. Being noncommercial
alone is not permission. INFO/LAY data is included without assuming copyright
protection or lack of protection from its simplicity.

| Evidence group | Redistribution / commercial | Modification / ND | Attribution / source / watermark |
| --- | --- | --- | --- |
| E0 or untraced import | Not established / not established | Not established | Required credits/terms unknown; preserve all existing notices |
| E1 historical public statement | Broad permission evidence; exact scope/version unresolved | Broad wording, later variants/other authors unresolved | Ask author to confirm file list and credit form |
| E2 / E6 historical SA4.0 | NC redistribution if covered and conditions satisfied; no commercial grant under that license | Covered adaptations require SA; not ND | Credits, license link and change records; revision-clause scope needs review |
| E2 later ND4.0 | Unchanged covered material may be shared NC; no commercial grant under that license | Covered adapted material cannot be shared under ND alone | Retain supplied credits/notices/links; separate watermark instructions must be established |
| E4 historical SA / later ND | Release-specific, not a grant for imported Batocera files | Determine original and adaptation rights separately | Source/changes/author notices; later watermark clause is not automatically retroactive |
| E5 embedded unversioned ND | License-family hint, exact applicable version/grant unresolved | ND hint; not a versioned blanket clearance | Duimon label/link present in inspected metadata/raster; visible preservation is separate |

The bounded CC analysis is based on the
[official ND4.0 legal code](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en):
NC reproduction/sharing of licensed material differs from sharing adapted
material; necessary technical format modifications are addressed separately.
Attribution includes supplied creator/notices/license/source information and
change indication. The grant is limited to rights the licensor controls and
does not grant trademark rights. Scope, technical-modification exceptions,
historical terms and compliance need legal review; this is not legal advice.

## Stored variants versus runtime transformations

**Shipped images:** every actual image/layout byte and link target matches the
pinned recipe result. Embercade's `staging.py:60–68,284` and
`installer.py:174–209,527–530` preserve bytes and links.
Production read-only resource mounts are in `production.py:403–410,448`.
This proves no Embercade transport resize/recolor/crop/recompression/export.
It does **not** prove Batocera's night/standalone versions are unmodified
original artwork. Their history and different blobs are recorded; Git cannot
identify which pixels were cropped/recolored/composited or whether an earlier
creator licensed each adaptation.

**Libretro:** `libretroConfig.py::writeBezelConfig` uses PNG/INFO, not LAY.
Patch `0014-embercade-desktop-bezel-scaling.patch` places separate adapted
PNGs under the isolated RetroArch config's `overlays/` directory when required;
overlay.cfg refers to original or generated image. `bezels.py::padImage`
uses PIL fit (possible crop) or pad/centering; non-RGBA `alphaPaste` can
crop side edges on narrower output. It resizes and re-encodes **generated**
PNGs, never the immutable source. Lower target resolution can force stretch.
Optional tattoo/QR/gun branches composite output; they were inspected, not
executed here, and are not an all-path output-isolation certification.

**PCSX2/Xemu standalone:** patch `0022-embercade-standalone-decoration.patch`
skips the appliance image generator. `standalone_decoration.py:87–130` reads
original PNG/INFO and computes protected margins. `decoration_window.py:180–195`
uniformly scales/centers, clips to left/right safe sidebars and paints opacity
in memory. No cropped/scaled PNG is stored. Top/bottom and inward artwork are
intentionally not drawn over the game; wider protected ratios can hide all
side artwork. Hyprland workspace and Gamescope physical-output handling do
not change the source file.

Local generation/runtime display is not automatically redistribution of a
stored derivative. Nor does “runtime only” automatically exempt public display,
attribution or license-defined sharing. Whether a crop, resized export,
night recoloring or combined design is a legally relevant adaptation depends
on the applicable grant and actual transformation. No blanket ND violation
or approval is concluded.

## Watermark findings and limitations

All 302 file contents and 33 link texts are unchanged from the verified
recipe result in reference, stage and installed MainRig. Thus any watermark
already embedded in that payload survives the **transport** unchanged.

Existing PS2 standalone day/night and nocurve day/night variants retain the
visible Duimon side label at top-left; night darkens it. Existing SNES nocurve
day/night retains the lower-left label, also with reduced contrast. Unglazed
PS2/SNES use different layouts with no corresponding side label observed;
that is not proof of removal from the same predecessor. Current Xbox
standalone-night shows no comparable Duimon side label in the visual sample.
Commodore samples do not establish complete original-author attribution.

A watermark present in source bytes may be hidden by Libretro fit/side crop,
standalone side-only clipping, opacity, interpolation or optional compositing.
Existing geometry/isolation/lifecycle tests do not test every watermark's
bounding box and legibility. Complete original-watermark preservation and
visible runtime compliance are **not certified**. No asset was edited to
add, remove or restore anything.

## Clarification templates — drafts, not sent

Attach the exact relevant matrix/JSON subset with paths, P, resolved SHA-256,
original/winning source, introductions and later changes. Ask for a reply
identifying specific files/releases; a generic “fine to use my work” must not
be silently extended to other creators.

### Duimon

Hello Duimon, we are auditing Embercade, a private desktop-Linux emulation
frontend. Our exact list identifies your recorded contributions and possible
earlier adaptations from Batocera-bezel at P. May we redistribute these specific
PNG/INFO files unchanged as part of a noncommercial public release? Please
confirm which grant/version applies, including your historical public
permission/SA releases versus later ND releases, and whether the night,
nocurve and standalone variants are covered. What author credit, source/license
links, modification history and watermark preservation do you require?
Libretro may create local resized/padded/cropped images; our standalone renderer
only scales and clips the original in memory. Are these uses acceptable, and
how should attribution remain available if clipping hides part of a watermark?
Please identify any underlying third-party artwork requiring another grant.

### Mikael42

Hello Mikael42, our attached exact list separates your named adaptations from
the broad V31 “mostly” import credit. Could you identify the original sources,
creators and versions, and supply any permissions for your modifications?
May your own contributions to these unchanged files be redistributed NC with
Embercade, and under which license? Please clarify night/standalone variants,
required credits/source/license links, watermark treatment, and local runtime
resize/crop/clipping. We will ask original creators separately; your import or
adaptation is not assumed to grant their rights.

### TheNamec

Hello TheNamec, our audit found Batocera's historical Commodore import group and
your November 2021 concerns. The attached hashes identify the exact files we
currently have, not a claim that all are yours. Could you confirm which originals
and licensed releases they derive from, including historical SA versus later
ND terms? May the unchanged listed adaptations be redistributed NC, or does
any specific modification require separate permission? Please specify author
credit, change/source/license links and watermark requirements, including
night/standalone layouts and local scaling/clipping. No files or watermarks
have been modified by this audit.

### Other explicitly credited creators: Fery65, Lorenzolamas; historical Genetik57

Hello, a Batocera contribution in the attached list credits your work.
The attachment distinguishes final-path credits from earlier copy-ancestry
credits; please confirm which applies to you.
Could you identify which artwork you created, its original repository/version,
any embedded third-party content and the applicable license? May these exact,
unchanged files be redistributed NC with Embercade, including listed
night/standalone versions? What attribution/source/license/watermark notices
are required, and are local resizing/padding/cropping and in-memory sidebar
clipping permitted? We do not assume an importer can license your original work.

### Batocera-bezel maintainers / import authors

Hello, we reconstructed the 302-path consoles payload at P, including layer
overwrites and symlinks. Could you provide original-source/file mappings and
archived permissions for the untraced imports, especially V31's broad credit,
the pre-existing `default` artwork, rotated/duplicated variants and image
components? Does any grant explicitly cover the fetched pack's exact files,
or only individual contributions? Please identify creators, applicable versions,
derivative permissions and required notices/watermarks. We need evidence before
a public release and will not replace/remove assets merely to hide the gap.

## Release decision and checks

The outstanding gate is exact rights/terms mapping, not image functionality.
Required next evidence: covered original releases, adaptation permissions or
valid historical SA coverage, complete creator/component credits, notice
delivery and visible-attribution review. Contributor metadata alone does not
close these gates. No fallback replacement or public release is approved.

All 459 unit tests pass; runtime, frontend-library and shader smokes pass
(14 shader presets / 142 dependencies). No build, install/update or emulator
E2E was required/performed. `scripts/public-audit` remains expected-red for
the absent effective root LICENSE and three retained oversized branding masters.
These existing findings are not repaired by stripping assets.

## Exact file matrix

**P** means the full pinned source commit stated above. **A0** means attribution
requirements/complete creator chain unresolved, preserve existing notices.
**U0** means public redistribution not established. **T1** means the stored
upstream variant plus the runtime transformation review above; **T0** means
layout/link data, no independent image transform. **W0** means bytes preserved
but original/visible watermark completeness unknown; **W1** adds the observed
unversioned Duimon label; **WN** is non-image data. History IDs refer to the
machine companion, not to a license grant.

D/M have the limited meanings in the contribution table; named other credits
are shown literally. E0 applies to every path; E1/E2/E6 on D rows are possible
source-family evidence, **not grants assigned to that row**. E3/E4 on the two
surviving V31 PNGs record a historical claim, not identity to original artwork.
Full history IDs, all recorded introductions/change messages, raw author and
committer fields, Git blob OIDs and overwrite/link histories are in the JSON.
Repeated resolved hashes are intentional aliases/identical data, not duplicate
staged-path rows.

| Staged path | Final source (winner → terminal where different) | Source commit | Content SHA-256 | Contributor / history | License evidence | Attribution | Redistribution | Modification/ND | Watermark | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `default.info` | `default_nocurve_night/default.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H001 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `default.png` | `default_nocurve_night/default.png` | P | `6568a2878bb0e6a9820f0c962656b6f3411d84b399a781c10bca03ca8ff90566` | D; H002 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/3do.info` | `default_nocurve_night/systems/3do.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H003 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/3do.png` | `default_nocurve_night/systems/3do.png` | P | `f43aaf98c7d13083ed07001478669dcd5b08b3d5f02ebe111dac3aebdd6307a2` | D; H004 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/3ds.info` | `default_nocurve_night/systems/3ds.info` | P | `9b7fb6fa8e1f32558727a97a6d37418bf983d9611c230b82692e0b6dc5204e6d` | D; H005 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/3ds.png` | `default_nocurve_night/systems/3ds.png` | P | `caecb446a1a51ec2bfa20a2891a54091d943c4f2450ef360a73d4425b47f071a` | D; H006 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/adam.info` | `default_nocurve_night/systems/adam.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H007 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/adam.png` | `default_nocurve_night/systems/adam.png` | P | `d9febe8e27da10473e422f8184b265e14a7d5febbc1b1ad21d044d62b7ae02ed` | D; H008 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/advision.info` | `default_nocurve_night/systems/advision.info` | P | `da1c11d2b8add77b31b15bce364fd6d2e37f48594c942d0df8f6acd96b581536` | D; H009 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/advision.png` | `default_nocurve_night/systems/advision.png` | P | `ee65926e7643c00bb5ee94de94ad7bd2be7d1bbca7d4d52c82cd8dd2e941b361` | D; H010 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/amiga.info` | `default_unglazed/systems/amiga.info → default_standalone_night/systems/amiga500.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H258 → H224 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/amiga.png` | `default_unglazed/systems/amiga.png → default_standalone_night/systems/amiga500.png` | P | `5423f8cda5fbda37b6bdc68a2aad70d3fbf148ce6f0837c4cb9ad75ca452ef0b` | D; H259 → H225 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/amiga1200.info` | `default_unglazed/systems/amiga1200.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H260 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/amiga1200.png` | `default_unglazed/systems/amiga1200.png` | P | `9dc12ee13d9e4f2c883d1b1824d875cf494fcca7b86716d438bbcd564a415429` | ?; H261 | E0,E3,E4 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/amiga500.info` | `default_standalone_night/systems/amiga500.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H224 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/amiga500.png` | `default_standalone_night/systems/amiga500.png` | P | `5423f8cda5fbda37b6bdc68a2aad70d3fbf148ce6f0837c4cb9ad75ca452ef0b` | D; H225 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/amiga600.info` | `default_unglazed/systems/amiga600.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H264 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/amiga600.png` | `default_unglazed/systems/amiga600.png` | P | `ccdb3ad03d4ac1ed0270442d9f6d073770ff87988836794bf11d4036888c123d` | ?; H265 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/amigacd32.info` | `default_unglazed/systems/amigacd32.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H266 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/amigacd32.png` | `default_unglazed/systems/amigacd32.png` | P | `7a6399838b277d8657ec67a89d61b23d39a10293854d85974997c47590e985a6` | ?; H267 | E0,E3,E4 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/amigacdtv.info` | `default_unglazed/systems/amigacdtv.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H268 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/amigacdtv.png` | `default_unglazed/systems/amigacdtv.png` | P | `2652f2e3090ead56e8bf3198b7546e655f6fbfdaa92031049a98543bd0f38f75` | M; H269 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/amstradcpc.info` | `default_nocurve_night/systems/amstradcpc.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H013 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/amstradcpc.png` | `default_nocurve_night/systems/amstradcpc.png` | P | `59f1d344a09fa51bb5392206293ed8a62a6bf0315e2a4c64951c850c4ec5ae76` | D; H014 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/apple2.info` | `default_standalone_night/systems/apple2.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H226 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/apple2.png` | `default_standalone_night/systems/apple2.png` | P | `d44c09092b0181f7f5b6cc6d5b46d942ca09262b116642dd18b451aeced3a653` | D; H227 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/apple2gs.info` | `default_standalone_night/systems/apple2gs.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H228 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/apple2gs.png` | `default_standalone_night/systems/apple2gs.png` | P | `6a63770e3ddbb8729d20ba2ac8305183112692f9c03aa7901ac83f40785bb8e7` | D; H229 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/arcadia.info` | `default_nocurve_night/systems/arcadia.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H019 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/arcadia.png` | `default_nocurve_night/systems/arcadia.png` | P | `f81ffc09bbf0974067d06c20b066922da15fd6c0c02d64ed76b2aa173a25c278` | D; H020 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/archimedes.info` | `default_nocurve_night/systems/archimedes.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H021 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/archimedes.png` | `default_nocurve_night/systems/archimedes.png` | P | `8384a99a455b842bbe754f289a4de513c37e9f928fc4851d974e1a5c6d3cdd45` | D; H022 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/arduboy.info` | `default_nocurve_night/systems/arduboy.info` | P | `56910f99240588d4faa5ca9738ac689abb883709d4f4e01b2f2ab48bae0a6839` | D; H023 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/arduboy.png` | `default_nocurve_night/systems/arduboy.png` | P | `1bf685ac7a4dcf914b849fffa1bb6e6391c2059787a9040b4d1bebd36b3dd71e` | D; H024 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/astrocade.info` | `default_nocurve_night/systems/astrocade.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H025 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/astrocade.png` | `default_nocurve_night/systems/astrocade.png` | P | `84ba249836d889fdabe995bc4b8455fe713620a303549d89cf8240c2edcdbee4` | D; H026 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/atari2600.info` | `default_nocurve_night/systems/atari2600.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H027 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/atari2600.png` | `default_nocurve_night/systems/atari2600.png` | P | `478ecd03bac08fa0e4fc1395bd7739181308ecb1efcbfc191b4b16457c0d0df7` | D; H028 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/atari5200.info` | `default_nocurve_night/systems/atari5200.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H029 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/atari5200.png` | `default_nocurve_night/systems/atari5200.png` | P | `031414ab15de45b275e92206d93103638804a4f370ee11decf7b78ffadccb118` | D; H030 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/atari7800.info` | `default_nocurve_night/systems/atari7800.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H031 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/atari7800.png` | `default_nocurve_night/systems/atari7800.png` | P | `14fa2c320873f191bda24a63db5d0493722f85a4b1e61be9cf44a3b7d1c740fd` | D; H032 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/atari800.info` | `default_nocurve_night/systems/atari800.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H033 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/atari800.png` | `default_nocurve_night/systems/atari800.png` | P | `33f27436b2ca66c77fb5b6b4fc5e854e7799bea1b3575da0da46e86742187577` | D; H034 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/atarist.info` | `default_nocurve_night/systems/atarist.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H035 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/atarist.png` | `default_nocurve_night/systems/atarist.png` | P | `b86f76b23464ffac619b58062737b842aaa00f8d92853e5ab5522e08412bcae5` | D; H036 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/atom.info` | `default_nocurve_night/systems/atom.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H037 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/atom.png` | `default_nocurve_night/systems/atom.png` | P | `32cdbd64b347b1e75c618fd78932968f6c9cd24782f5e7b58515cc7186529a84` | D; H038 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/atomiswave.info` | `default_unglazed/systems/atomiswave.info` | P | `231b288ff58664d28dc0047b7e67ef0bd06d2023b9a9e36fbc74064302c9ebb4` | fery65; H286 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/atomiswave.png` | `default_unglazed/systems/atomiswave.png` | P | `30e05bf26eedde0dbc3bed1c2b43a990020bd6e7ab82c264c6b48bdaf602b677` | fery65; H287 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/bbcmicro.info` | `default_nocurve_night/systems/bbcmicro.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H039 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/bbcmicro.png` | `default_nocurve_night/systems/bbcmicro.png` | P | `8a9dd04b4bdd07d6ea178f8f2adf92b71aed53e3831c31ffc15882f172c6db60` | D; H040 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/c128.info` | `default_unglazed/systems/c128.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H288 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/c128.png` | `default_unglazed/systems/c128.png` | P | `fe07df23b0c3ae0e00d9d068788d8e67d6d840fbb9c229253de1644ff16d92f1` | ?; H289 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/c64.info` | `default_standalone_night/systems/c64.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H230 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/c64.png` | `default_standalone_night/systems/c64.png` | P | `4419cde69d354970f96b39002c7eed9042acdc525720ec2964471efb86bb55d9` | D; H231 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/camplynx.info` | `default_nocurve_night/systems/camplynx.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H043 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/camplynx.png` | `default_nocurve_night/systems/camplynx.png` | P | `65a739a8ba829cd8f8c47782f15e029deb4e4b6095d8281bec67758040b7aa25` | D; H044 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/cdi.info` | `default_nocurve_night/systems/cdi.info` | P | `61731e2d03f1a4f412daa38c8071ae589a1007f54c91bf267b1f9dacf32330b1` | D; H045 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/cdi.lay` | `default_nocurve_night/systems/cdi.lay` | P | `9da76c755e8664697aa85fb96e28ce083e16ffcc36213a5de4e543ce4c876610` | D; H046 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/cdi.png` | `default_nocurve_night/systems/cdi.png` | P | `dc5b0824bfc2e098bc09e862864bdf954212988a7aea2b278eeaf8c988bbc75a` | D; H047 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/channelf.info` | `default_nocurve_night/systems/channelf.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H048 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/channelf.png` | `default_nocurve_night/systems/channelf.png` | P | `c0a9fa9e0ab71264f67717d3c74656135a7528d74a98845969920e034484ff21` | D; H049 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/coco.info` | `default_nocurve_night/systems/coco.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H050 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/coco.png` | `default_nocurve_night/systems/coco.png` | P | `0e0a866b385d8caa2cf2aa3e8cba28465d0c7eb56d787d964e2715e90163b861` | D; H051 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/colecovision.info` | `default_nocurve_night/systems/colecovision.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H052 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/colecovision.png` | `default_nocurve_night/systems/colecovision.png` | P | `c5a08535be5f3ae2923091e74c10fae2ff30fa949d19770771fcff9534a47d0a` | D; H053 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/crvision.info` | `default_nocurve_night/systems/crvision.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H054 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/crvision.png` | `default_nocurve_night/systems/crvision.png` | P | `220881b6d061c3b204d721f8c7fffb593976aed1fe6167c1c76a5d349bb0f4df` | D; H055 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/default_4_3.info` | `default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/dice-270.info` | `default_unglazed/systems/dice-270.info → default_unglazed/systems/mame-270.info` | P | `fdc73a3fff739eaa0a1381b8db6d527ebf363f9ec2251fefaa407ffaf2a1e087` | fery65; H297 → H347 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/dice-270.png` | `default_unglazed/systems/dice-270.png → default_unglazed/systems/mame-270.png` | P | `88973f5f49a3203e824af2d6d71e8617c7eba2303e0568da726d8f066340700c` | fery65; H298 → H348 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/dice-90.info` | `default_unglazed/systems/dice-90.info → default_unglazed/systems/mame-270.info` | P | `fdc73a3fff739eaa0a1381b8db6d527ebf363f9ec2251fefaa407ffaf2a1e087` | fery65; H299 → H347 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/dice-90.png` | `default_unglazed/systems/dice-90.png → default_unglazed/systems/mame-270.png` | P | `88973f5f49a3203e824af2d6d71e8617c7eba2303e0568da726d8f066340700c` | fery65; H300 → H348 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/dice.info` | `default_unglazed/systems/dice.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H301 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/dice.png` | `default_unglazed/systems/dice.png` | P | `b08e16cd97df4b86cafb34b589e370f86adb7af3aa42b9146b731dc016595863` | ?; H302 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/dos.info` | `default_unglazed/systems/dos.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H303 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/dos.png` | `default_unglazed/systems/dos.png` | P | `f4a1dd015b92ffc0e91447c2c4815ba1ff07bc59ca6cc3d5d1b824be3b57ca77` | ?; H304 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/dreamcast.info` | `default_nocurve_night/systems/dreamcast.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H056 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/dreamcast.png` | `default_nocurve_night/systems/dreamcast.png` | P | `3de31d0f55809a35018d8241129dd30d3124851268b32677624586b49733d854` | D; H057 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/easyrpg.info` | `default_unglazed/systems/easyrpg.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H307 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/easyrpg.png` | `default_unglazed/systems/easyrpg.png` | P | `4e6878ebd750f52b46fb62e33008cdec681b41b97f1f887f0bfc16c46e8083f9` | M; H308 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/electron.info` | `default_nocurve_night/systems/electron.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H058 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/electron.png` | `default_nocurve_night/systems/electron.png` | P | `cc57fb44b33abb8bf9d30a8e1777127aab300f1eaf03f8667d167badc8ffc007` | D; H059 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/fbneo-270.info` | `default_unglazed/systems/fbneo-270.info → default_unglazed/systems/mame-270.info` | P | `fdc73a3fff739eaa0a1381b8db6d527ebf363f9ec2251fefaa407ffaf2a1e087` | fery65; H309 → H347 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/fbneo-270.png` | `default_unglazed/systems/fbneo-270.png → default_unglazed/systems/mame-270.png` | P | `88973f5f49a3203e824af2d6d71e8617c7eba2303e0568da726d8f066340700c` | fery65; H310 → H348 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/fbneo-90.info` | `default_unglazed/systems/fbneo-90.info → default_unglazed/systems/mame-270.info` | P | `fdc73a3fff739eaa0a1381b8db6d527ebf363f9ec2251fefaa407ffaf2a1e087` | fery65; H311 → H347 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/fbneo-90.png` | `default_unglazed/systems/fbneo-90.png → default_unglazed/systems/mame-270.png` | P | `88973f5f49a3203e824af2d6d71e8617c7eba2303e0568da726d8f066340700c` | fery65; H312 → H348 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/fbneo.info` | `default_unglazed/systems/fbneo.info` | P | `2057f2d5ee36028d19672cd7c32942c8aa760e699012bddc48c400292e1e7df8` | ?; H313 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/fbneo.png` | `default_unglazed/systems/fbneo.png` | P | `b08e16cd97df4b86cafb34b589e370f86adb7af3aa42b9146b731dc016595863` | ?; H314 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/fds.info` | `default_unglazed/systems/fds.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H315 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/fds.png` | `default_unglazed/systems/fds.png` | P | `f37762bd74d95a9b0c3cfe0c190a9210345e19a68a5c8f9db73ca8e721df2339` | M; H316 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/fm7.info` | `default_nocurve_night/systems/fm7.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H060 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/fm7.png` | `default_nocurve_night/systems/fm7.png` | P | `cb9b5b4221939a2c3229792f294197b916a5d0ebb5d60aa37a319845ff073e71` | D; H061 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/fmtowns.info` | `default_standalone_night/systems/fmtowns.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H232 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/fmtowns.png` | `default_standalone_night/systems/fmtowns.png` | P | `d4e9bcecd3671a7b0068187a6f4d25ca11a376e45d7c440299236da2e9e37920` | D; H233 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gamate.info` | `default_nocurve_night/systems/gamate.info` | P | `7701e4cae5cb9acc7ed718aeda1971a665b9d59ffa5d690c1d5691461185a461` | D; H064 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gamate.png` | `default_nocurve_night/systems/gamate.png` | P | `11eb36da32626d63769ae4a33a1af013bcb9a2b2c41b67ac41c2b5a22c7e38a7` | D; H065 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gamecom.info` | `default_nocurve_night/systems/gamecom.info` | P | `1d48643fadab4bd58951bbe658acde8745696b5b38d5344ef23edbf0facfdbb2` | D; H066 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gamecom.png` | `default_nocurve_night/systems/gamecom.png` | P | `b5606082ee5a768ab3ef816441925d80d90a0373db5cb3a00e6037d7cb48c5db` | D; H067 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gamecube.info` | `default_standalone_night/systems/gamecube.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H234 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gamecube.png` | `default_standalone_night/systems/gamecube.png` | P | `d5401ac0779bf096c00e3b9e93e9d28189f97b049b26bfa48c561b65cce1d7ad` | D; H235 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gamegear.info` | `default_nocurve_night/systems/gamegear.info` | P | `12d3891d2c518dea942e59643c0213a4a01bbd71cf82faa54dc4ee11caf27906` | D; H070 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gamegear.png` | `default_nocurve_night/systems/gamegear.png` | P | `76bcca30a2e9078ec2575b1aa1425786efc39d8b9b3538fd3f38f86750639074` | D; H071 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/gamepock.info` | `default_unglazed/systems/gamepock.info` | P | `f48ef192c9e3ad74461680bef439d49b21c81f86c0acac4805336fb8a054bfbc` | M; H325 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gamepock.png` | `default_unglazed/systems/gamepock.png` | P | `b6426751b87d0bad1e0f554377b9e1ac287674f1568024ce9b1a6b248416ff29` | M; H326 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gb.info` | `default_nocurve_night/systems/gb.info` | P | `3bf8aae34bf703399250e5a502dc5aa2dc7305b8f298dd4d6e04a483a2ef6490` | D; H072 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gb.png` | `default_nocurve_night/systems/gb.png` | P | `3060b49a18f4505a9f8be73048605d85720c7da561fb7b8ca8685159a8d3e086` | D; H073 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gb2players.info` | `default_nocurve_night/systems/gb2players.info` | P | `c7d91ed23f59fc6244d1052ed6ac53534f1e10db2af5ce3503074ae2e255228d` | D; H074 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gb2players.png` | `default_nocurve_night/systems/gb2players.png` | P | `fbdb12d5c93e0ef146a5ff7da108bd05eddcaeaa2aa397ecc8d28b638e45c6d5` | D; H075 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/gba.info` | `default_nocurve_night/systems/gba.info` | P | `d78eb5239f279b53edb14b79f97c71eb2cdd1d7e5006c2a606420e476209430a` | D; H076 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gba.png` | `default_nocurve_night/systems/gba.png` | P | `73964394edf16a4cb367da4291e6f8278e71f0605ef913a25b8336e8a2268ee1` | D; H077 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gbc.info` | `default_nocurve_night/systems/gbc.info` | P | `c7fc6cc8dd9cfa0fa04078165d4695f1f9182c9b660c6dcdd4d0ddf90379b30a` | D; H078 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gbc.png` | `default_nocurve_night/systems/gbc.png` | P | `d16c50ac7a624d324e6f59c5099bb68887744f90c0ec0f7a9fd9922122d09f49` | D; H079 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gbc2players.info` | `default_nocurve_night/systems/gbc2players.info` | P | `c7d91ed23f59fc6244d1052ed6ac53534f1e10db2af5ce3503074ae2e255228d` | D; H080 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gbc2players.png` | `default_nocurve_night/systems/gbc2players.png` | P | `6fd8e056d21856a57bdb54e0d2663b894720dcdae4d0b421f2788a6b790ff1d0` | D; H081 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gmaster.info` | `default_nocurve_night/systems/gmaster.info` | P | `8e652c63c5e65a4440de82245e42812f07806c6c55bf1ef24dcaf551abc8ab8c` | D; H082 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gmaster.png` | `default_nocurve_night/systems/gmaster.png` | P | `856986796aeb033ec73c609c0066340c0560e85f1aeac3baa61959dabbbba4e1` | D; H083 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/gp32.info` | `default_nocurve_night/systems/gp32.info` | P | `52c23cccba05b84817f41b02b15fe773ea472e048fa30beac0eb2a5347338d97` | D; H084 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gp32.png` | `default_nocurve_night/systems/gp32.png` | P | `02db056bf686b8eb1211db68b073f9c277b32a5cd4b3251a16b0270eb7a26670` | D; H085 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/gx4000.info` | `default_nocurve_night/systems/gx4000.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H086 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/gx4000.png` | `default_nocurve_night/systems/gx4000.png` | P | `a27e0371265d4753402c59c67d0d4b6b8a82c9711c67fc9f1969681912b06230` | D; H087 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/intellivision.info` | `default_nocurve_night/systems/intellivision.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H088 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/intellivision.png` | `default_nocurve_night/systems/intellivision.png` | P | `d192d94865ffb278b63b5bf9e648673c4360a82f770cbc9b7cf73a4d785e8510` | D; H089 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/jaguar.info` | `default_standalone_night/systems/jaguar.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H236 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/jaguar.png` | `default_standalone_night/systems/jaguar.png` | P | `374831ceaa735ef7e677568d084bf8cf9a5dc0eb250cd0f58d36e370e7dd51cc` | D; H237 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/laser310.info` | `default_nocurve_night/systems/laser310.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H092 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/laser310.png` | `default_nocurve_night/systems/laser310.png` | P | `1b577f3bae5cfe2039e9f51d666bdbb31aee9699c2a4b349f224e1734f3bc8b4` | D; H093 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/lightgun.info` | `default_unglazed/systems/lightgun.info` | P | `79404eb41689869003f0012981fc3a151f227945d8fad6e9e8b8045f1176d763` | ?; H343 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/lightgun.png` | `default_unglazed/systems/lightgun.png` | P | `0bc12edfacbb08355b09a5e4a8807302ba1c86501f77346e874d252c34b74580` | ?; H344 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/lowresnx.info` | `default_nocurve_night/systems/lowresnx.info` | P | `985741ef42231233395229edd33923594555795eb3b57dae4b980831bcdfa837` | D; H094 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/lowresnx.png` | `default_nocurve_night/systems/lowresnx.png` | P | `1adef0bbe4c13a2f58f54499da7dc3309fc8ca40ac6c507aba72342b22332cd8` | D; H095 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/lynx-270.info` | `default_nocurve_night/systems/lynx-270.info` | P | `53685c8ea6ae6a2f5a3d29bb77c8b1f5a5f7c78da40ce70e1968eb14d4986f5b` | D; H096 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/lynx-270.png` | `default_nocurve_night/systems/lynx-270.png` | P | `41f18fdd8417060c16b6297b290b272b68c12da4e836fb339e321c6187a1b15b` | D; H097 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/lynx-90.info` | `default_nocurve_night/systems/lynx-90.info` | P | `53685c8ea6ae6a2f5a3d29bb77c8b1f5a5f7c78da40ce70e1968eb14d4986f5b` | D; H098 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/lynx-90.png` | `default_nocurve_night/systems/lynx-90.png` | P | `dc929138859d0ec7bc61797f8ab40d65cd9ca814e9dfb6c3d4276c39ce96a60a` | D; H099 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/lynx.info` | `default_nocurve_night/systems/lynx.info` | P | `9e100bea16d48992afe1048ddd0ebb0c66338e9143d5a24ff864af484d548b11` | D; H100 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/lynx.png` | `default_nocurve_night/systems/lynx.png` | P | `4ca7aa2e26e54e5631ee9404946ec82f2130f1c57e6d7e9f7ec371fe9b900be5` | D; H101 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/macintosh.info` | `default_nocurve_night/systems/macintosh.info` | P | `dea78a3d732fc0f25ea9eb29da0ce9540303ebaf5c4357e328060a3e158f6e23` | D; H102 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/macintosh.png` | `default_nocurve_night/systems/macintosh.png` | P | `d205e00b55b48e06b685dad02636ac77463718bc3b657561d7393d780c5306d1` | D; H103 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/mame-270.info` | `default_unglazed/systems/mame-270.info` | P | `fdc73a3fff739eaa0a1381b8db6d527ebf363f9ec2251fefaa407ffaf2a1e087` | fery65; H347 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/mame-270.png` | `default_unglazed/systems/mame-270.png` | P | `88973f5f49a3203e824af2d6d71e8617c7eba2303e0568da726d8f066340700c` | fery65; H348 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/mame-90.info` | `default_unglazed/systems/mame-90.info → default_unglazed/systems/mame-270.info` | P | `fdc73a3fff739eaa0a1381b8db6d527ebf363f9ec2251fefaa407ffaf2a1e087` | fery65; H349 → H347 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/mame-90.png` | `default_unglazed/systems/mame-90.png → default_unglazed/systems/mame-270.png` | P | `88973f5f49a3203e824af2d6d71e8617c7eba2303e0568da726d8f066340700c` | fery65; H350 → H348 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/mame.info` | `default_unglazed/systems/mame.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H351 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/mame.png` | `default_unglazed/systems/mame.png` | P | `b08e16cd97df4b86cafb34b589e370f86adb7af3aa42b9146b731dc016595863` | ?; H352 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/markIII.info` | `default_nocurve_night/systems/markIII.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H104 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/markIII.png` | `default_nocurve_night/systems/markIII.png` | P | `c8024231cde0216c8262959ae7419822012b0a67b6b7575c6e4cb017eff2f661` | D; H105 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/mastersystem.info` | `default_nocurve_night/systems/mastersystem.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H106 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/mastersystem.png` | `default_nocurve_night/systems/mastersystem.png` | P | `3274a2b65d0da65f8dc90600b44c522d6c59c16df2d9106e194df1ca4eef0da9` | D; H107 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/megacd.info` | `default_nocurve_night/systems/megacd.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H108 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/megacd.png` | `default_nocurve_night/systems/megacd.png` | P | `87b84840e874d16db87134f16db9566caa407596ca16b0e1a86e23273f52e43b` | D; H109 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/megadrive.info` | `default_nocurve_night/systems/megadrive.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H110 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/megadrive.png` | `default_nocurve_night/systems/megadrive.png` | P | `7e92f446653009ca8a951ce7624d6507949bdffc39ebe2a07f55b7cf1123e54a` | D; H111 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/megaduck.info` | `default_nocurve_night/systems/megaduck.info` | P | `7ceab904df877ad0db4dd9ba4073af6ef60c2dd05b58e5ba99fb07443484b87b` | D; H112 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/megaduck.png` | `default_nocurve_night/systems/megaduck.png` | P | `5b853ec7bc9b6dd09be3d471567bca57614ae3e3a2dae869d2aa2c8ecc773c7c` | D; H113 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/msx.info` | `default_unglazed/systems/msx.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H359 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/msx.png` | `default_unglazed/systems/msx.png` | P | `a92791ae464f864e7c519a21254ba80a15ec794bf7e343aa70618829e31b8722` | ?; H360 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/msx1.info` | `default_nocurve_night/systems/msx1.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H114 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/msx1.png` | `default_nocurve_night/systems/msx1.png` | P | `a3f02f37fec8276bd109f5a6b34f5036081be298acccb10158fb60a90ab8a69d` | D; H115 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/msx2+.info` | `default_unglazed/systems/msx2+.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H363 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/msx2+.png` | `default_unglazed/systems/msx2+.png` | P | `68ed00c8c61101aa154dd5ebef2f0c33dde9bba0abf5f04a31acac75e71d4b71` | ?; H364 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/msx2.info` | `default_nocurve_night/systems/msx2.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H116 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/msx2.png` | `default_nocurve_night/systems/msx2.png` | P | `99a4d298701671bd573f444ba73a27cf03034e45f7f42d34b0fcd0442cfea5bc` | D; H117 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/msxturbor.info` | `default_unglazed/systems/msxturbor.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H367 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/msxturbor.png` | `default_unglazed/systems/msxturbor.png` | P | `d04d7c12291681936d97c6b1c65dddb6606694f0138a01436dd08c0abf6004a1` | M; H368 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/n64.info` | `default_standalone_night/systems/n64.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H238 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/n64.png` | `default_standalone_night/systems/n64.png` | P | `d9c851214f669334ee53080a7903f2c246b7c36d39258db8c2765d66558b400f` | D; H239 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/naomi.info` | `default_unglazed/systems/naomi.info` | P | `d3122af5bf98e4a44ee0dabf0699c7ab92b573aa29e028baa9875041ac351607` | fery65; H371 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/naomi.png` | `default_unglazed/systems/naomi.png` | P | `ad5a722a2158e828421e553e34aa7ea976dd084a5f1c78e6e47c7357c7e9d411` | fery65; H372 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/nds.info` | `default_unglazed/systems/nds.info` | P | `00d9a0d13a3d4692814daf5e0d4ab40bcb34a8fe8d4f56ce27576d021b457d59` | M; H373 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/nds.png` | `default_unglazed/systems/nds.png` | P | `9c0cdc184271fc10ea70e755e2f0c2385e785889ebcdfe03abd46dad442b811b` | M; H374 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/neogeo.info` | `default_nocurve_night/systems/neogeo.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H120 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/neogeo.png` | `default_nocurve_night/systems/neogeo.png` | P | `ede559a75895a78469c55b20e065c6e3529d038e83dcd55bb990313f2492fd39` | D; H121 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/neogeocd.info` | `default_nocurve_night/systems/neogeocd.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H122 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/neogeocd.png` | `default_nocurve_night/systems/neogeocd.png` | P | `642449066319892ad928992900e457360fe477597f79f9de68c0df26266b94fc` | D; H123 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/nes.info` | `default_nocurve_night/systems/nes.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H124 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/nes.png` | `default_nocurve_night/systems/nes.png` | P | `332d9c0815c8b486bd609ccf9d2ff2dca70b53e2592a5c8890a17031fa54cc7d` | D; H125 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/ngp.info` | `default_nocurve_night/systems/ngp.info` | P | `0097ae731d633ff46a4a340e547ce7986eb134d932df5bb9c9f9ae8e9e3b2a73` | D; H126 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/ngp.png` | `default_nocurve_night/systems/ngp.png` | P | `2e098c934e66d4c4fc81a5aa060cdf7d465dbef37261796b32b3efdd704f9a32` | D; H127 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/ngpc.info` | `default_nocurve_night/systems/ngpc.info` | P | `7ed7373412d0d0abd4aba4395fc1f0f4d354ec8b7063ac860bd7dfb1695d477b` | D; H128 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/ngpc.png` | `default_nocurve_night/systems/ngpc.png` | P | `5329740ed9d0b3adab2fd182d91e2a18da91cbaed9b90d34db9f72fd563a7ea4` | D; H129 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/odyssey2.info` | `default_nocurve_night/systems/odyssey2.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H130 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/odyssey2.png` | `default_nocurve_night/systems/odyssey2.png` | P | `4ae2b3955f4087962007309dbce2ca49c13e5e12ff8df6e9ccaf514f41a0f948` | D; H131 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pc.info` | `default_standalone_night/systems/pc.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H240 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pc.png` | `default_standalone_night/systems/pc.png` | P | `52a6b6ee091edc463c5b6ee055117dbe0417369ba1507f706c843d8fb9fb63ad` | D; H241 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pc88.info` | `default_nocurve_night/systems/pc88.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H134 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pc88.png` | `default_nocurve_night/systems/pc88.png` | P | `b89e3c4af5cbc0c30c413a41396db9f8f7843ed74da77a6d6df7435eee002147` | D; H135 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pc98.info` | `default_nocurve_night/systems/pc98.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H136 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pc98.png` | `default_nocurve_night/systems/pc98.png` | P | `6ac0085e5e5f8a89281405a9ea3211d798422d925846bb86a628ebd2735f5a2e` | D; H137 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pcengine.info` | `default_nocurve_night/systems/pcengine.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H138 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pcengine.png` | `default_nocurve_night/systems/pcengine.png` | P | `e18824e1c62e070e8101485603d934297ba3081199c177495cd844998b4d56ce` | D; H139 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pcenginecd.info` | `default_nocurve_night/systems/pcenginecd.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H140 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pcenginecd.png` | `default_nocurve_night/systems/pcenginecd.png` | P | `86cfca53c0ef238f8bceca29aac4972bbca2f99604fcc9627bd3df903d0bc00f` | D; H141 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pcfx.info` | `default_nocurve_night/systems/pcfx.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H142 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pcfx.png` | `default_nocurve_night/systems/pcfx.png` | P | `f502a2bc90b4e0a866a2716fa9aeabbf06c07964267bd4fcb05bce4548bb74e5` | D; H143 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pdp1.info` | `default_nocurve_night/systems/pdp1.info` | P | `f949117991dc55b88122e6d48de421eceb9b64034ff279b27f90a662313055d9` | D; H144 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pdp1.png` | `default_nocurve_night/systems/pdp1.png` | P | `d9e62f4e0e847418dbdc92d76584e82e36efdf1f956a513917f06ce1d03cd43b` | D; H145 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pico8.info` | `default_nocurve_night/systems/pico8.info` | P | `05eec44180bdb445674562f32d5a074afad037c9533f4d387fdc1f2e1b88f11f` | D; H146 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pico8.png` | `default_nocurve_night/systems/pico8.png` | P | `d7fc39ecb99afd193785951e7eb80951e662772008fe1eb6a844a94f714b0b6a` | D; H147 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pokemini.info` | `default_nocurve_night/systems/pokemini.info` | P | `500863c3dddb11d9235b5604e9f1613af541edbdbcbee01fd0f10019692ca203` | D; H148 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pokemini.png` | `default_nocurve_night/systems/pokemini.png` | P | `9838fb802930ce4ec654164ef2f57e7de16c31c99a9d366d881a8ddf1bedb269` | D; H149 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/prboom.info` | `default_unglazed/systems/prboom.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H401 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/prboom.png` | `default_unglazed/systems/prboom.png` | P | `1f851121103ff9a39236008e50552c8eebafd55112acf1e70974152f8f7953eb` | ?; H402 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/ps2.info` | `default_standalone_night/systems/ps2.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H242 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/ps2.png` | `default_standalone_night/systems/ps2.png` | P | `5d089a4f69425ae1879630a85b3bee6cce9df3c9cdf9d5fd2802b826ed8fa785` | D; H243 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/ps3.info` | `default_unglazed/systems/ps3.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H405 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/ps3.png` | `default_unglazed/systems/ps3.png` | P | `2d99afc9f433c5de0b7fef0b06aa79ae7e03021ab6839c0939850d26097614b1` | ?; H406 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/psp.info` | `default_unglazed/systems/psp.info` | P | `073267b12231cc1b9716e853c5b744fdd79b3a2cc91eb0a64ad968a51e7e5525` | M; H407 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/psp.png` | `default_unglazed/systems/psp.png` | P | `7512b8bd2e517c2dea268b910e76e43bacc113b7c42649f99f0f926a0d526e2c` | M; H408 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/psx.info` | `default_standalone_night/systems/psx.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H244 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/psx.png` | `default_standalone_night/systems/psx.png` | P | `47d054d87635e0a9267ba22cded53ebb6d294e78d93b40494c91fc439b6ac803` | D; H245 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/pv1000.info` | `default_nocurve_night/systems/pv1000.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H154 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/pv1000.png` | `default_nocurve_night/systems/pv1000.png` | P | `5e9aa32bee837abcd1d132f210829f83d00653858294439b2e841d24d9c2cf36` | D; H155 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/satellaview.info` | `default_unglazed/systems/satellaview.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H411 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/satellaview.png` | `default_unglazed/systems/satellaview.png` | P | `261056b87bcf5a4ed0a2a758b3fefdb1ba2d48623ea3ffbf207e490b95950748` | ?; H412 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/saturn.info` | `default_nocurve_night/systems/saturn.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H156 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/saturn.png` | `default_nocurve_night/systems/saturn.png` | P | `3382daeb70f6a2188e9c682337fb147d7b50f9ac618ee7277ef11322a6bc803d` | D; H157 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/scummvm.info` | `default_nocurve_night/systems/scummvm.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H158 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/scummvm.png` | `default_nocurve_night/systems/scummvm.png` | P | `818ef174408131a0f6bf147040b7ddc1f4efa0cb56c739ffb92796d85cb720c9` | D; H159 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/scv.info` | `default_nocurve_night/systems/scv.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H160 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/scv.png` | `default_nocurve_night/systems/scv.png` | P | `fa26ff6138eeb4b01c83dc936a099073effe65e8378e60ce205122fa18cb0d99` | D; H161 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/sega32x.info` | `default_nocurve_night/systems/sega32x.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H162 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/sega32x.png` | `default_nocurve_night/systems/sega32x.png` | P | `bc79d93374536f7631b06da58ad416bb03e4faf84eabb858ec9d81022fb6ab9d` | D; H163 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/segapico.info` | `default_nocurve_night/systems/segapico.info` | P | `eca25bcbe460a170d87e800bada4c5f39353597c15f7bfbf80faf496be4df851` | D; H164 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/segapico.png` | `default_nocurve_night/systems/segapico.png` | P | `5b0f77173798ef0afd5df35b727f99bd9945ed693fd3f68f27e7dc34a28367cd` | D; H165 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/sg1000.info` | `default_nocurve_night/systems/sg1000.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H166 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/sg1000.png` | `default_nocurve_night/systems/sg1000.png` | P | `050a28c37f4812c10fb64d876e971af0c846b67dc5f4ae61b31f332710512627` | D; H167 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/sgb.info` | `default_nocurve_night/systems/sgb.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H168 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/sgb.png` | `default_nocurve_night/systems/sgb.png` | P | `883242994625094c1295c0734210b000302eac789a0cd9ec0cf01c6d13f46343` | D; H169 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/snes-msu1.info` | `default_unglazed/systems/snes-msu1.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H425 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/snes-msu1.png` | `default_unglazed/systems/snes-msu1.png` | P | `aec470dbc84c194653779a5485b7616f83924f4d92ebf7ffa31ad54d20615ec2` | ?; H426 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/snes.info` | `default_nocurve_night/systems/snes.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H170 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/snes.png` | `default_nocurve_night/systems/snes.png` | P | `d772ed5d865d889c3dd0b683c5efa3998a5e567135a8a8959749d837f96166b4` | D; H171 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/snes_msu-1.info` | `default_nocurve_night/systems/snes_msu-1.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H172 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/snes_msu-1.png` | `default_nocurve_night/systems/snes_msu-1.png` | P | `7fb3ab42a8cc99fc296038f7814e7da76e6f21d4f11359b8b5721be86ac9b7c2` | D; H173 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/socrates.info` | `default_nocurve_night/systems/socrates.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H174 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/socrates.png` | `default_nocurve_night/systems/socrates.png` | P | `f7c1a2e90e44af2613508ec4b398519123f47cd7573fac938a396930e96a4ca8` | D; H175 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/spectravideo.info` | `default_unglazed/systems/spectravideo.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H429 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/spectravideo.png` | `default_unglazed/systems/spectravideo.png` | P | `97aca6736f667e256adaf926a827ae56eeb4795f5617be3874c11914d1062bd2` | Lorenzolamas; H430 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/sufami.info` | `default_unglazed/systems/sufami.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H431 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/sufami.png` | `default_unglazed/systems/sufami.png` | P | `894472a985e15956a39d2e7e493d0fe8898c23812f8ff6817ec5cf7b85cf6c71` | ?; H432 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/supergrafx.info` | `default_nocurve_night/systems/supergrafx.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H176 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/supergrafx.png` | `default_nocurve_night/systems/supergrafx.png` | P | `dc18510beb2979067e5551405d042aeb9c61b75f9dcabcda8e492e72c3cfc31b` | D; H177 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/supervision.info` | `default_nocurve_night/systems/supervision.info` | P | `72ec436ebbfc258d345beb0d93fc507408a8127c197b2ec3b65560a5eb524da2` | D; H178 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/supervision.png` | `default_nocurve_night/systems/supervision.png` | P | `6237793d7891997ade65d9ad9b440876be2629012a755cd574f1413c6ebf43ad` | D; H179 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/supracan.info` | `default_nocurve_night/systems/supracan.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H180 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/supracan.png` | `default_nocurve_night/systems/supracan.png` | P | `8d847c6ca93bacd5ea3d2d3c4813901f835ef51f878b845f0999c4f6a2c93170` | D; H181 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/thomson.info` | `default_nocurve_night/systems/thomson.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H182 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/thomson.png` | `default_nocurve_night/systems/thomson.png` | P | `6cf71a6bcbf2db51dcf7793cf914efa667fef5d632184db95117b7f936d262b9` | D; H183 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/ti99.info` | `default_nocurve_night/systems/ti99.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H184 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/ti99.png` | `default_nocurve_night/systems/ti99.png` | P | `fe0b5cf069851b9c869ea654e9ca7f5a6e168d48649f2aabcb555ee66e91ff04` | D; H185 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/tic80.info` | `default_nocurve_night/systems/tic80.info` | P | `93fa112eccace350423f70cf4eb5f9a049ede24bdbe827a8dd9389f534dad1ab` | D; H186 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/tic80.png` | `default_nocurve_night/systems/tic80.png` | P | `bfe6b37caf8705568faf406d160281f20674e10da431e5649f4a3836b85dd060` | D; H187 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/triforce-standalone.info` | `default_standalone_night/systems/triforce-standalone.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H246 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/triforce-standalone.png` | `default_standalone_night/systems/triforce-standalone.png` | P | `88a09a75d09863890356c574ac786a84e4a2aa45557d30a63556a2076227fdc2` | D; H247 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/tutor.info` | `default_nocurve_night/systems/tutor.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H188 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/tutor.png` | `default_nocurve_night/systems/tutor.png` | P | `c2a44660c2b906adb27cceec67726cea5b5a3583ba286c3a4a80dabcbd98871b` | D; H189 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/tvgames.info` | `default_nocurve_night/systems/tvgames.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H190 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/tvgames.png` | `default_nocurve_night/systems/tvgames.png` | P | `63291a455924fc2795f3e6cd4dbd30aab360b960efdf42092b2f90dd754da6a4` | D; H191 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/uzebox.info` | `default_nocurve_night/systems/uzebox.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H192 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/uzebox.png` | `default_nocurve_night/systems/uzebox.png` | P | `ad463f32eb50a8b074c50ff87a3a5ba6eba9696286a47012911a9ec91fa6d2be` | D; H193 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/vc4000.info` | `default_nocurve_night/systems/vc4000.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H194 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/vc4000.png` | `default_nocurve_night/systems/vc4000.png` | P | `d41560db9c8614fc924fd8359af31ff225243b87f51ccdb6ca270728dc3e1066` | D; H195 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/vectrex.info` | `default_nocurve_night/systems/vectrex.info` | P | `c68bc9a3f51ec938036860f816705436f74e8bbb7bcf671d29995fcbe24e11e1` | D; H196 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/vectrex.png` | `default_nocurve_night/systems/vectrex.png` | P | `9166d031fd34e83f11606c2e3fd8ba738493d76c1be513861a4becf5b6b64b65` | D; H197 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/vemulator.info` | `default_nocurve_night/systems/vemulator.info` | P | `2e894c7618f72e30349f1879cb0f8db68a88e250d28dacb60edb1532816211f5` | D; H198 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/vemulator.png` | `default_nocurve_night/systems/vemulator.png` | P | `7dfbb7a8809aec5213fb1901ff8dd9bfa2fa6e671db60cedc33b2971b6690a7c` | D; H199 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/vic20.info` | `default_unglazed/systems/vic20.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H445 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/vic20.png` | `default_unglazed/systems/vic20.png` | P | `43ff1ad7358055521117db8bf3562841be8204d81fe3a4a9b4479ec403f3c267` | ?; H446 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/videopacplus.info` | `default_nocurve_night/systems/videopacplus.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H200 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/videopacplus.png` | `default_nocurve_night/systems/videopacplus.png` | P | `9c21d3ef6c4129c8c7cbc69066a7113789b1224f5ce755d3cc97322e09ebcef0` | D; H201 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/virtualboy.info` | `default_nocurve_night/systems/virtualboy.info` | P | `cf6570d01c40e865dcf052f5c280f2cf197e25fec398751370e1083e864c76b1` | D; H202 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/virtualboy.png` | `default_nocurve_night/systems/virtualboy.png` | P | `feb212d6d08b8baeb5383cd80b1fb7aa1284793720c88d379953b6ca78895f75` | D; H203 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/vsmile.info` | `default_nocurve_night/systems/vsmile.info` | P | `50d5462921dd871826b7a140ff34802421d277a0362ed2f41e084dd490460651` | D; H204 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/vsmile.png` | `default_nocurve_night/systems/vsmile.png` | P | `01d248c96b7943e37795bf0310221a7338c689a11d0e1d392c6d2f687ba771c8` | D; H205 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/wasm4.info` | `default_nocurve_night/systems/wasm4.info` | P | `cc4fad924b357b217f6f925a3dce63122aa820d4b23301c110ec5c20bba0df71` | D; H206 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/wasm4.png` | `default_nocurve_night/systems/wasm4.png` | P | `08b9afdfc645ca714688eb103dc6dcc9a928a0fcbe3a6a2b1c64532d6586becb` | D; H207 | E0,E1,E2,E6,E5 | A0 | U0 | T1 | W1 | UNKNOWN |
| `systems/wii.info` | `default_standalone_night/systems/wii.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H248 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/wii.png` | `default_standalone_night/systems/wii.png` | P | `4784c0f1959ca16cb54efec79184351365e417ec54a0d22c6a3d1079022cc2c2` | D; H249 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/wiiu.info` | `default_unglazed/systems/wiiu.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H451 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/wiiu.png` | `default_unglazed/systems/wiiu.png` | P | `31ac8b4c2d37bf90d39fe1ba5ca09a2d1924daedf03d39a1d1d0f9f26a1777f9` | ?; H452 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/wswan-90.info` | `default_nocurve_night/systems/wswan-90.info` | P | `f2a0fe9cc696874681803e6e0416c2b110205f9111fa99fb8354194adb2510d5` | D; H208 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/wswan-90.png` | `default_nocurve_night/systems/wswan-90.png` | P | `b98a82259e4777400d56437baa34250909bc44c60e1088928e763e24af816030` | D; H209 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/wswan.info` | `default_nocurve_night/systems/wswan.info` | P | `eb24bb59de36559eb9697df427a56a961dd888150fe823545e0e3e7ba167b012` | D; H210 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/wswan.png` | `default_nocurve_night/systems/wswan.png` | P | `431493614ef953140d3693c4a91220e845ce93b8587d243a065d8abbe5f223e4` | D; H211 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/wswanc-90.info` | `default_nocurve_night/systems/wswanc-90.info` | P | `f2a0fe9cc696874681803e6e0416c2b110205f9111fa99fb8354194adb2510d5` | D; H212 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/wswanc-90.png` | `default_nocurve_night/systems/wswanc-90.png` | P | `025c48abd77e00b6e41d344661a13252e42cbb50045cc15c482462b97d2b77c0` | D; H213 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/wswanc.info` | `default_nocurve_night/systems/wswanc.info` | P | `eb24bb59de36559eb9697df427a56a961dd888150fe823545e0e3e7ba167b012` | D; H214 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/wswanc.png` | `default_nocurve_night/systems/wswanc.png` | P | `c1203c6c4d4d5cd1b3bccf607d3079c7a539af38de7684f804edd8db20962a2c` | D; H215 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/x1.info` | `default_nocurve_night/systems/x1.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H216 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/x1.png` | `default_nocurve_night/systems/x1.png` | P | `c1958eb525a42b4d8b586ba099d4e75521500723c2f6020e381969f099b93140` | D; H217 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/x68000.info` | `default_nocurve_night/systems/x68000.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H218 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/x68000.png` | `default_nocurve_night/systems/x68000.png` | P | `4f10f78b544ab0b5bb04d0e22ce655efca84eac3bef486057e235220253f0165` | D; H219 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/xbox-standalone.info` | `default_standalone_night/systems/xbox-standalone.info` | P | `420ad0d41bab18c07e92720509fccbd8fce0ffaffdced25ab795103edaaacb38` | D; H250 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/xbox-standalone.png` | `default_standalone_night/systems/xbox-standalone.png` | P | `a3b0ca8cf5d0080d5844e4041f2d767b84598443f52a500e611074f8ee05f987` | D; H251 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/xbox.info` | `default_unglazed/systems/xbox.info → default_unglazed/systems/default_4_3.info` | P | `82072a39e058985cfdf665f2da2c3d4a19caf66b247cec6d35b00dd7a0549bca` | ?; H461 → H296 | E0 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/xbox.png` | `default_unglazed/systems/xbox.png` | P | `49a63fa1a33f0c908eb9a53778243289f2e96abd4c46fadb95b8a54662a26247` | ?; H462 | E0 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/zx81.info` | `default_nocurve_night/systems/zx81.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H220 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/zx81.png` | `default_nocurve_night/systems/zx81.png` | P | `3f17a15605db8eef23885f6fff982e66b22efa59ab9782a0fcee2af0c6ddd5f6` | D; H221 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |
| `systems/zxspectrum.info` | `default_nocurve_night/systems/zxspectrum.info` | P | `27aafb7ded6775915a558c454766f5121c554216b28bb7a9e6fcc43ef30b66e7` | D; H222 | E0,E1,E2,E6 | A0 | U0 | T0 | WN | UNKNOWN |
| `systems/zxspectrum.png` | `default_nocurve_night/systems/zxspectrum.png` | P | `b5ee0daf3b29ef2646578056bd1ffc5e8ab14fd4758f6698a7c5085027c02c18` | D; H223 | E0,E1,E2,E6 | A0 | U0 | T1 | W0 | UNKNOWN |

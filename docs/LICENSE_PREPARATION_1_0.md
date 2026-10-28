# Historical license preparation

> Historical evidence retained unchanged below. The current effective assignment
> is [LICENSING_1_0.md](LICENSING_1_0.md), with the corrected
> [Batocera GPL/LGPL distinction](BATOCERA_COMPONENT_LICENSES.md) and implemented
> [backend separation](ADAPTER_SEPARATION.md). Earlier prospective grants,
> blanket-scope assumptions and old captured-resource blockers are not current
> release findings. The removed captured-bezel and bundled-shader inventories
> are not the new RetroBat/host-package payload. No previous full audit was repeated.

## Preserved original report

# Embercade 1.0 licensing preparation — 27 October 2026

## RetroBat and host shader integration — 27 October 2026

The owner's new instruction authorizes targeted source/resource integration,
superseding the earlier resource freeze for the next candidate. The accepted
Gold image and all installed copies stay unchanged; the AppImage build hold,
no-push/publication rule and personal Web API boundary remain in force.
[Implementation, coverage and test matrix](RETROBAT_AND_HOST_SHADERS.md) describes
the pinned complete RetroBat source, 13 regular menu sets plus unsupported
animation data, and 26 validated host-package shader mappings. Old captured
bezels are excluded from future staging. Saved `consoles` choices resolve to
RetroBat `default_unglazed` without rewriting saved preferences or using old art.
The current coverage has 138 exact-name replacements and 11 missing dedicated
variants, explicitly listed; only RetroBat generic/base fallbacks are used.

The owner adopts CC BY-NC-SA 4.0 for that RetroBat collection. Original credits
and individual/ND notices remain unchanged; this is the owner's distribution
decision, not a newly received artist statement. The historical 302/35-file audit
is retained as evidence, not repeated or used as the new payload inventory.
The full shader collection stays in the official optional host package rather
than the next image. Existing resolved shader/Carbon credits remain resolved.
Own-code GPL/PolyForm scope and RetroAchievements distribution remain separate.

**Preparation only. No public release is cleared.** Baseline: `8a5ce6d`.
The owner requests a permanently free, noncommercial community project with
publicly readable source, with no paid edition, subscription or separate
commercial-licensing business. The current repository and AppImages stay private.
No new AppImage may be built until the owner finishes the RetroAchievements
discussion. No push, visibility change, publication or history rewrite is authorized.

This report updates the existing [scope review](LICENSE_SCOPE_REVIEW.md),
[publication audit](PUBLIC_RELEASE_AUDIT.md) and
[bezel evidence](BEZEL_PROVENANCE.md). Their historical counts are not current
clearance. Completed artwork byte/hash/history comparisons were not repeated.
No code, rendering, emulator, resource, user profile or existing image was changed.

## Intended scope

| Material | Intended treatment | Preparation status |
| --- | --- | --- |
| Confirmed independent Embercade-owned software | Unmodified PolyForm Noncommercial 1.0.0 | Full reference text prepared; positive ownership/independence mapping still required before a grant |
| Own documentation and branding whose underlying rights are established | CC BY-NC-SA 4.0 | Full reference text prepared; third-party quotations, code, notices and images excluded |
| Batocera launcher/configgen/common/builders and covered modifications | Exact applicable upstream terms; compatible own-contribution terms | Root GPL-2.0-or-later-with-file-exceptions evidence retained; package coverage and mixed client scope not resolved by a root label |
| Batocera EmulationStation and its modified MIT-covered source | Retain MIT copyright/permission notice; compatible treatment for additions | Exact pinned MIT notice prepared; independent embedded dependencies remain separate |
| Covered Duimon/other third-party art | Its established original license and credits, including CC BY-NC-ND where applicable | ND text and new community evidence recorded; unknown artwork receives no inferred grant |
| Themes, shaders, fonts, native libraries and Python dependencies | Their individual original terms | Existing pins/notices retained; complete distribution mapping remains incomplete |
| AppImage as delivered collection | Component-by-component notices and obligations | No single PolyForm/CC blanket license; aggregate versus combined-program issues must be resolved |

The reference texts under [LICENSES/prepared](../LICENSES/prepared/README.md)
do not activate a project grant. No root LICENSE, SPDX source headers,
`pyproject.toml` license expression or contribution policy is introduced here.
The owner authorizes preparing these texts now; this supersedes the older
instruction to prepare no license files, without licensing unresolved code.

## Current code boundary

The current tree contains **63 own-package Python paths**, **35 Batocera
patches** and **six EmulationStation patches**. The older review's 44 modules
and 22+1 patches describe an earlier baseline. The current
[component map](LICENSE_COMPONENT_MAP.csv) enumerates all 63 modules and
41 patches, plus integration-test and resource groups. It is a technical
review map, not a positive legal allowlist or a statement that all files are
copyrightable. Unmapped material has no automatic PolyForm/CC fallback.

The concrete API boundaries from the earlier audit still exist:

- `ui_data.py::build_ui_data()` imports and calls the pinned Batocera system
  and feature builders in its interpreter.
- `batocera_config.py::_PROBE` runs an own child program importing
  `batocera_launch` argument and SystemConfig APIs.
- `standalone_decoration.py::DECORATION_PROBE` extends that program and calls
  upstream Emulator/Profiler APIs. Other routines in the same file implement
  own geometry and supervision; this is a mixed file.
- `runtime.py::probe_runtime()` dynamically imports the runtime packages in a
  generated child program. A scan only for static imports misses this case.
- `scripts/runtime-smoke`, the payloads in `tests/test_runtime.py` and
  `tests/test_visual_runtime.py`, and the source-based native API regression in
  `tests/test_retroachievements_native.py` require separate integration/fixture review.

Examples of potentially independent own routines include `paths.py`,
`exit_hotkey.py`, `policy.py`, `version.py` and the installer/Steam/filesystem
helpers described in the earlier review. They are candidates, not automatically
cleared by having only standard-library imports. Clients, transitive calls,
copied logic and generated descriptors must be considered as well.

Nineteen modules were added after the old 44-module review. The component map
includes them without retroactively treating them as approved independent code.
In particular, `xbox_eeprom.py` names Xemu's EEPROM implementation at an exact
revision as its format reference. Format facts/standard algorithms are not by
themselves proof of copied protected expression, but neither is this enough
evidence to label the whole implementation PolyForm without origin review.
No personal EEPROM or keys were opened for this licensing work.

Batocera patches modify the Batocera integration, not the host emulators just
because those emulators appear in target filenames. Their target terms apply
to retained/derived code; own additions need compatible grants. The six ES
patches include MIT-covered code/context and foreign text. Copyright and notice
preservation must cover each actual modification, not just one historic patch.

## Compatibility findings

The [pinned Batocera COPYING](https://github.com/batocera-linux/batocera.linux/blob/9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48/COPYING)
and [GNU aggregation guidance](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)
distinguish a collection of independent works from a combined program. A
GPL-covered combined work cannot acquire an additional noncommercial condition.
Placing files in different folders or invoking an API child with JSON does not
alone settle that boundary. Conversely, sharing an AppImage does not by itself
turn every independent artwork or unrelated program into GPL software.

**Concrete unresolved compatibility issue:** some own embedded API programs and
the builder share an interpreter with GPL-relevant Batocera packages. Applying
PolyForm to those portions while distributing them as a GPL-covered combined
work would conflict. Applicable coverage and client boundaries need a scoped
decision; this report does not declare the entire repository GPL or independent.
The earlier adapter design remains a proposal. No adapter extraction or runtime
refactor was authorized or performed to make licensing appear simpler.

LGPL and permissive dependencies likewise keep their own terms. LGPL conditions
depend on the actual library/version/linkage and replacement/source delivery;
the word LGPL is not an automatic incompatibility or a blanket exemption.
The [runtime metadata snapshot](LICENSE_RUNTIME_METADATA.csv) records 29
prepared-runtime distributions, including pyudev's LGPL-2.1+ declaration and
pip's vendored notice paths. Metadata is an inventory aid, not a completed
review of bundled native wheel libraries, vendored code or a public artifact.
The existing FreeImage, SDL2_mixer and static AppImage-runtime notices remain
unchanged. A lockfile/version/hash cannot replace their applicable obligations.

The owner does not plan commercial licensing. That policy is not an additional
license clause. The standard
[PolyForm text](https://github.com/polyformproject/polyform-licenses/blob/1.0.0/PolyForm-Noncommercial-1.0.0.md)
has its own distribution permission and specified organizational uses regardless
of funding; it should not be advertised as an absolute prohibition on anyone
ever receiving money in connection with the project. Upstream GPL/MIT commercial
rights also remain intact. No custom resale prohibition, altered PolyForm text
or commercial-license offer has been added.

## Batocera and Reddit evidence

The owner's [public post](https://www.reddit.com/r/batocera/comments/1xf9tyu/)
reports the Batocera team's answer: the artwork came from several contributors;
the team cannot reconstruct every image's exact origin/license; Duimon was the
last major contributor, with CC BY-NC-ND artwork and watermarks. This is a
documented **owner report of the team's answer**, not the original private
correspondence or a team-authored pack-wide permission. It corroborates the
existing distinction between Duimon material and unidentified community art.

The owner supplied [derik-for-real's comment](https://www.reddit.com/r/batocera/comments/1xf9tyu/comment/19rqignohx4pv/),
which was readable on 27 October. The commenter relays another community member's
reading that ND restricts derivatives rather than prohibiting noncommercial
redistribution. This is community interpretation, not a verified copyright
holder's new grant or legal clearance for the entire collection.

The [CC BY-NC-ND 4.0 legal code](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en),
sections 2(a)(1), 2(a)(4) and 3(a), supports the relevant distinction:
unadapted licensed material may be shared noncommercially with the required
credits/notices/license information; sharing adapted material is restricted.
Necessary technical format modifications are expressly treated separately.
Therefore the comment's blanket suggestion that every resize necessarily
violates ND is too broad. Applicability to particular authored adaptations,
watermarks and presentation still depends on the actual licensed material and
conditions. An applicable public license need not be replaced by individual
permission merely because it is ND.

Embercade transports the captured art unchanged; the existing audits already
record that fact. It is distinct from whether Batocera's inherited night or
standalone variants were previously adapted with permission. Existing runtime
scaling/clipping and generated RetroArch artwork are also documented, not
silently represented as byte-identical copies. No new technical artwork
comparisons, artistic edits, removals or contributor contact were performed.

The completed 302-path matrix, 33 preserved links and 187 resolved blobs remain
the evidence baseline. Historical UNKNOWN records are unresolved exact-file
coverage, not denials and not a claim that CC BY-NC-ND prohibits redistribution.
Known covered grants must be honored; unknown images do not inherit Duimon's
terms solely from being in the same pack. Existing watermarks and credits stay.

## RetroBat reference and Carbon completion — 27 October 2026

The owner's new reference was checked directly in RetroBat's official sources.
This reuses the existing Embercade inventories; no installed resources were
replaced and no completed artwork/authorship search was repeated.

| Official source / checked revision | Finding and scope |
| --- | --- |
| [RetroBat license.txt](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/license.txt), `48ff054` | LGPLv3 for RetroBat-authored code unless upstream terms apply; CC BY-NC-SA 4.0 for the project work, particularly its written/graphic material. These are not new grants by every third-party author. |
| [RetroBat bezel README](https://github.com/RetroBat-Official/retrobat-bezels/blob/5ce1f6ed32eb9f3df8ae14483afc4d1e3ef35d65/README.md), `5ce1f6e` | Explicit Batocera fork, bundled with RetroBat. The checked complete tree has a README but no separate LICENSE/COPYING or asset attribution document. This is useful lineage/distribution evidence, not proof of undocumented private permissions. |
| [Build configuration](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/build.ini) and [.gitmodules](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/.gitmodules) | Explicitly link the Carbon fork and bezel repository; the decorations submodule points to the inspected bezel revision. |
| [NewPixie mapping](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/system/shaders/configs/crt-new-pixie/rendering-defaults.yml), [handheld mapping](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/system/shaders/configs/handheld/rendering-defaults.yml) and [EasyMode source](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/system/shaders/configs/zfast/CRTEasymode.fx) | RetroBat uses the same shader families, including NewPixie and LCD Grid/color presets. Its EasyMode port retains the author's GPL notice. Preset use is not a different license for the Libretro code/images. |

**Carbon: DONE for origin, theme-license identification and author credit.**
The exact Embercade theme was already mapped to Fabrice Caruso's
`b921e1734d88d6bc7b9e8cb97dd8f8b91ba2058a`; it is not unknown material.
RetroBat's [credits](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/README.md)
and linked [Carbon theme header](https://github.com/RetroBat-Official/es-theme-carbon/blob/6d197a7a682f395e3704c38e8d736d30eb1ce177/theme.xml#L2-L9)
confirm the owner's supplied notice:

> Carbon Theme (c) Fabrice Caruso (CC BY-NC-SA Licence). Originally based on the work of Eric Hettervik (Original Carbon Theme) and Nils Bonenberger (Simple Theme).

The pinned theme also credits maioni for language/system additions. Preserve
these authors and the original readme. Its older 2.0 heading and full 4.0 legal
body are recorded as an upstream notice inconsistency; this does not make the
origin or the stated CC-BY-NC-SA license unknown. No universal 4.0 label is
added to embedded third-party fonts, logos or audio, or to Embercade's own code.
Those resources keep their separate coverage questions.

The [bezel follow-up](BEZEL_PROVENANCE.md#retrobat-reference--27-october-2026)
records the overlap with RetroBat without repeating the artwork scan. The
[targeted shader findings](LICENSE_SCOPE_REVIEW.md#targeted-shader-notice-follow-up--27-october-2026)
close the NewPixie frame, Simpletex texture and six LUT-image questions using
original-author evidence. Four specifically named legacy shader files remain
without an established original-code grant; EasyMode has a GPL notice, with
version/notice handling kept as a separate issue. Known licenses are not reset
to UNKNOWN because a port or image encoding has a different hash.

## Remaining release decisions

| Item | Specific remaining work |
| --- | --- |
| Own software / GPL boundary | Approve the positive independent-code scope and compatible terms for API-bound/derived contributions; resolve the identified same-interpreter cases |
| Own branding/prose rights | Confirm authority for supplied masters, derivatives and poster; exclude third-party images/notices/quotes from the own CC scope |
| Bezel scope/credits | [Decision baseline](BEZEL_DECISION_1_0.md): 8 PNGs with ND notices, 107 further Duimon-linked variants and 152 separate technical paths. [Targeted 35-path follow-up](BEZEL_35_LICENSE_FOLLOWUP.md): Spectravideo has a reasoned RetroBat CC-BY-NC-SA-4.0 project-scope assignment, explicitly marked as an inference; 34 final-file mappings remain open, including the 2 historical V31 dispute cases. No demonstrated file-specific violation/denial. |
| Carbon | Theme origin/CC-BY-NC-SA credit DONE; preserve its original mixed-version notice. Handle independently licensed fonts/logos/audio separately, without reopening the theme as unknown. |
| Shaders | Preserve identified grants and newly completed texture/LUT attribution; resolve the four exact legacy-code grant gaps and EasyMode version/notice handling below. Complete future payload notice delivery without treating the whole tree as unlicensed. |
| Libraries and source delivery | Match the actual future artifact to original notices, license choices, source/build instructions, GPL corresponding source and any LGPL replacement/relinking obligations |
| API permissions | Owner handles RetroAchievements in Discord: whether the personal Web API key may be redistributed or a different identity is required. Keep the original Batocera path and functional login unchanged; no public permission inferred from a working request |
| Publication privacy and approval | Review current/history exposure without rewriting it; receive explicit permission for any push, visibility change or release |

The accepted private image contains the owner's personal Web API key. The
[official API documentation](https://api-docs.retroachievements.org/#api-access)
describes an account API key, not redistribution permission. It does not license
that private candidate for public delivery. API access/credentials and the
software's copyright licenses are separate questions. ScreenScraper's existing
working integration is retained; its granted application use must be recorded
for the actual public distribution without exposing authorization values.

Next, apply an approved component-specific grant and complete notices/source
delivery against the eventual public candidate. Recheck the actual artifact
only after the owner's RetroAchievements clarification and later build/release
approval. There is no new image, public source publication or changed behavior
in this preparation.

## Validation of this preparation

The later RetroBat/targeted-shader follow-up changes eight documentation/map
files only. Its fresh isolated regression passes 792 tests (787 successful,
five expected skips), and runtime smoke passes. All 74 checked local links,
nine unique referenced source commits, the five unchanged prepared-text hashes,
component-map coverage and diff checks pass; the bounded new-text credential
scan has no hits. The existing private image hash below is unchanged. Research
receipts are under `.work/retrobat-license-2026-10-27/` and
`.work/shader-rights-2026-10-27/`; no build, push or contact occurred.

The scope/text checks verify the 63 module and 41 patch map, 29 runtime
metadata rows, five exact license/notice hashes and local documentation links.
Only documentation, metadata inventories, prepared reference texts and a
scoped repository whitespace attribute for exact CC-source copies change;
no production source, patch, resource or package metadata changes. The accepted
private candidate retains SHA-256
`b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`.
Full isolated regression passes: 792 tests, 787 successful and five expected
native opt-in skips, including 25 GTK checks and all 52 structural routes.
Runtime smoke, 102 local documentation links, all five reference-text hashes,
the complete component map and `git diff --check` pass. A bounded added-text
credential-pattern scan reports no hit. These checks do not certify licensing.

The publication audit remains red for the deliberately absent effective root
LICENSE, pre-existing host identifiers in private documentation and three
retained large branding masters. Missing rights/grants and API permission are
substantive gates even if those static checks were green. No history rewrite,
asset removal or blanket license was used to bypass them.

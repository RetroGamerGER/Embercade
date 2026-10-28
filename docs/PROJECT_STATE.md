# Embercade Project State

## Installer support made explicit — 28 October 2026

The current installer supports Arch Linux, CachyOS and Garuda only. Pacman
installation is guarded by the exact distro-ID allowlist; ID_LIKE=arch alone
does not enable another derivative. Welcome and Host software now display the
restriction in German/English, and README/release/getting-started requirements
state it prominently. An additional execution test rejects even a prepopulated
package/AUR plan on unsupported hosts. The graphical action now explains the
restriction before confirmation or terminal creation; the independent backend
execution guard remains in place. No package command or support allowlist is
changed. The earlier public candidate is retained while a separate updated
public package/source export incorporates this informational clarification.
No push/release, deployment or host change is authorized.
The final isolated suite passes 854 tests (849 passed, five expected native
opt-in skips), including GTK and all 52 structural routes. The 75 targeted
host/first-run tests, three GTK flow/restart checks, runtime smoke and public
audit pass. Normal profiles and installed images are not used or changed.

## Public candidate prepared locally — 28 October 2026

The owner-authorized preparation is complete: personal paths are sanitized,
a separate public AppImage and complete matching sources are frozen at clean
public root `e28f90b1f56b36cb4250d2fe458a559979335d0e`. The ten review files are
under dist/public-preparation-2026-10-28. Image SHA is
`204253d5b1a514d38e3bd57bdf26862cb525af127a0df7baf5ac4ec61e87302e`.
The standalone source bundle has one root commit and no private history/tags.
Original private history, non-master refs and all 17 inventoried older images
are preserved. Runtime/native frontend/resources match the accepted candidate
including file modes; only legal/packaging material changes. Full isolated
suite: 852 tests, 847 passed/five expected skips; 1,810 source checksums and
all final asset hashes pass. No old personal RA key or known owner path/address
is found in checked release/source contents. The 16:10 limitation remains.
No publication, push, release/tag, deployment or normal-profile start occurred.
See [frozen identities and verification](PUBLIC_PREPARATION_RESULT_2026_10_28.md).

## Public preparation authorized — 28 October 2026

The owner authorizes a sanitized public source export, separate public AppImage,
complete matching sources/notices and release notes, preserving all previous
builds and the original private Git history. The existing three-host functional
acceptance remains; the laptop 16:10 bezel limitation stays documented.
Only privacy, packaging metadata and documentation change. A fresh public Git
root omits historical private data instead of rewriting the original repository.
Public means prepared for review, never already published. No push, release/tag,
visibility change, deployment, normal-profile start or host change is authorized.
The final isolated regression passes 852 tests (847 passed, five expected
skips), including GTK and 52 structural routes. The 36 targeted packaging,
source-delivery and license checks, runtime smoke and public-tree audit pass.

## Three-system owner acceptance — 28 October 2026

The owner accepts the current private candidate on MainRig, EmbercadeLaptop
and WohnzimmerPC and reports successful operation on all three. The existing
laptop 16:10 bezel cropping/proportion issue remains the explicitly accepted
limitation; no fix or wider aspect-ratio compatibility is claimed. This closes
the remaining overall three-host functional acceptance for the tested candidate.
The report is broad owner acceptance, not a new per-game/per-format test matrix.

The deployed artifact stays at d2194fc, SHA
`a3348017d24d1fa6d8b96118a591da1bcb3e77130a73fa7c5eda05b2c809c130`,
with the existing verified matching source kit and recovery receipts. Only
documentation changes record this result. No host/runtime change, new build,
push, public release/tag or visibility change is authorized. See
[three-host acceptance and limitation](PRIVATE_DEPLOYMENT_2026_10_28.md#owner-acceptance--28-october-2026).

## Private three-host replacement completed — 28 October 2026

The owner explicitly authorized replacing the current AppImage on all three PCs
under the existing filenames and takes responsibility for remaining manual
tests. All five active copies now match the MainRig-accepted d2194fc candidate,
SHA `a3348017d24d1fa6d8b96118a591da1bcb3e77130a73fa7c5eda05b2c809c130`.
Fresh inventories, atomic replacements, matching alias manifests/checksums,
image-ownership records and verified rollback receipts preserve current links.
All three installed images pass disposable CLI help checks; protected settings,
SSH/secret files, Desktop/wrappers/Steam routes and older canonical artifacts
remain unchanged. No frontend/game/session was started or stopped, no host
package/driver change occurred and no loose key was transferred. At deployment
inventory the optional personal RA Web API key file was absent on the laptop
and living-room PC; later acceptance does not expose or verify key values. No new build, push or public release. See
[private deployment and recovery](PRIVATE_DEPLOYMENT_2026_10_28.md); deployment
verification does not constitute remote manual gameplay/visual acceptance.

## C64 drive-8 startup correction — 28 October 2026

The owner reports Giana Sisters D64 failing with DEVICE NOT PRESENT. Its real
launch log proves correct media delivery/attachment; Configgen forces optional
JiffyDOS without the external ROMs and VICE cannot initialize the 1541-II drive.
Patch 0039 defaults only C64 desktop to stock ROMs while retaining explicit
JiffyDOS/core overrides and other media/core defaults. An isolated A/B run with
a read-only private copy of the actual disk reproduces the failure when enabled
and reaches Loading/Ready/Starting program/Done when disabled; both final runs
exit zero after 12,000 frames. Original ROM/BIOS collections and profiles stay
unchanged. See [C64_STARTUP.md](C64_STARTUP.md) for the exact evidence, test
environment limits and exact owner acceptance. No installed image
replacement, push/public release, host/driver change or remote deployment.
Final isolated regression: 848 tests, 843 passed and five expected skips,
including GTK and all 52 structural routes. Three targeted C64 checks, runtime
smoke, license-scope and diff checks pass. The owner confirms that Giana Sisters
D64 now starts and Start + Guide returns to the frontend on MainRig. This is
the actual visible start/exit acceptance for that game; other hosts and media
formats have no new manual acceptance claim.
The separate private candidate from `d2194fc` is built and package/source-kit
verified, SHA `a3348017d24d1fa6d8b96118a591da1bcb3e77130a73fa7c5eda05b2c809c130`.
Packaged Configgen confirms the correction; per-user RA/paste remain present,
with no old private key in the 5,685 files. Seven protected images and Stage
remain intact. Only this chat’s idle preview was restarted into the candidate
with existing MainRig settings; no game auto-start or deployment occurred.

## Native key-editor paste correction — 28 October 2026

The owner found that the first per-user-key candidate could not paste the key
copied from the website. The pinned TextEditComponent has no clipboard shortcut
handler; this is not evidence of a truncated website key or missing host package.
A narrow tenth frontend patch adds SDL clipboard paste on explicit Ctrl+V /
Shift+Insert and Paste buttons in both masked dialogs. Entire strings/cursor
positions and masked cache updates are preserved. Unusable data keeps the old
draft; no clipboard read/log/export occurs during diagnosis. Tests use synthetic
data. Current installed/Gold images and the first API candidate stay intact;
a new separate private candidate supports owner retesting. No publication/push,
host settings or provider authentication changes are authorized.
The correction passes 70 targeted checks and 845 complete isolated tests
(840 passed, five expected skips), including 52 structural routes. The native
frontend build, runtime smoke and diff checks pass. The owner has now accepted
the MainRig paste flow and supplied a screenshot of the live account overview
showing per-game achievement progress. Other-host acceptance and the remaining
restart/Cancel/Reset/key-absent gameplay cases remain pending; this screenshot
is not evidence of those separate checks.
A separate candidate from `fd337ec` is verified and opened on MainRig for
the requested retest. SHA is `827457baba71cd2700840801274778bc4d67d9203c7c11b36a885a5ac31f4777`;
its matching source kit and all six preserved image hashes are verified.
See docs/RETROACHIEVEMENTS_USER_KEYS.md. No installed image is replaced.

## Per-user RetroAchievements implementation — 28 October 2026

The owner approved implementation after the targeted review. The existing RA
settings now have one optional field masked in both editors, with protected
0600/0700 runtime storage, account binding, atomic save and Reset/Cancel. Existing
Batocera Web API views/parsers use the current user key; missing/rejected/limited
keys receive localized messages. Normal login source and emulator token handoff
are unchanged. Legacy compiled key inputs are rejected before being read, and
new packaging rejects the legacy native marker or missing per-user identity.
ScreenScraper, controllers, generators and user profiles remain unchanged.

[Implementation/acceptance guide](RETROACHIEVEMENTS_USER_KEYS.md): full isolated
843-test run passes (five expected skips), including GTK/52 structural routes.
After fixing one translated button argument in the full native build, 68 final
targeted checks pass, as do the complete frontend build and runtime smoke.
Private candidate preparation preserves the installed/Gold images and original
Stage. Actual entry/display/gameplay acceptance on all three PCs belongs to the
owner and remains pending. No deployment, push, public release, source upload or
provider message is authorized. The frozen d8e6ca6 source kit is unchanged and
never relabelled as matching a later image.

The separate private per-user candidate is now built from clean source
`010f5e857e9bdda02faebd621ca14977961c362b`, image SHA
`599663de6aa860ea113181fc40d84cb7b44b8848ea9017f77bfabf14f086d52c`. The extracted package audit,
AppImage/native help probes and old-key comparison over all 5,684 payload files
pass. Its matching source kit verifies 1,810 regular-file checksums. The Stage
and four local protected image hashes are unchanged. [Candidate/acceptance details](RETROACHIEVEMENTS_USER_KEYS.md#separate-private-acceptance-candidate).
No deployment or physical three-host acceptance is implied.

## RetroAchievements response and targeted assessment — 28 October 2026

The owner supplied Hexadigital's recommendation that each user use their own
Web API key rather than a shared key, due to rate limits and reset/ban risk.
Official docs independently describe account keys, secret handling and limits.
[The code-path assessment](POLISH_1_0_PRIVATE.md#per-user-web-api-recommendation--28-october-2026)
separates normal login/emulator tokens from the frontend's per-game progress
and user-summary Web API calls. A rank helper also uses the Web API but has no
caller at the pin. Keep the existing Batocera requests/views and add an optional
protected runtime key in existing RA settings as the recommended direction.
No documented normal-login exchange for the Web key was found; no emulator-API
substitution is proposed. Implementation/acceptance are still pending. No code,
secret, normal profile, image or frozen source-kit artifact changed; no build,
authenticated test, deployment, provider contact, push or publication occurred.

## Local source and notice preparation completed — 28 October 2026

The owner authorized completing licensing preparation and reports requesting
RetroAchievements guidance on Discord. No provider answer/permission is inferred.
[Source and notice delivery](THIRD_PARTY_DELIVERY.md) records the matching local
kit for the frozen d8e6ca6 private adapter image, with a separately identified
current legal supplement. It contains 33 original source archives, complete
patched Batocera/EmulationStation sources, all exact patch/build/install inputs,
34 indexed supplemental notices, and LGPL rebuild/replacement instructions.
The final archive under dist/license-preparation-2026-10-28/final has SHA-256
`6b4d73aa8a08d5d9552af9e97b960489daffa9078a88229e0cfa121ac477ec7d`;
all 1,809 internal file checksums pass, and all 314 installed Batocera Python
source files match. The supplement is frozen at 955fe49, independently of this
later verification receipt. All four protected image hashes remain unchanged.
The 29-distribution runtime record now distinguishes prepared sources/notices
from original license metadata. Pillow already supplied its 22-section native
wheel notice; missing libuv/libyaml, embedded frontend and font notices are
supplemented. No specific new license conflict was established.

No old bezel/shader provenance audit was repeated. Existing mixed upstream
terms, the reasoned client/adapter scope, Carbon credit and owner-confirmed
Canva origin remain intact. The only production-code edit copies legal files
during future staging; no runtime, resources, upstream patches, user/host state
or existing AppImage was changed. There is no new build, deployment, push,
release or source publication. The eventual public artifact must include these
notices and be matched to its sources, after the provider decision and explicit
publication approval; privacy/size review and manual tests remain separate.

## Branding origin resolved by owner declaration — 27 October 2026

The owner confirms the images were created in Canva and the background/arcade
graphics self-generated with Canva AI; the editor screenshot supports that
creation context. [Origin and grant scope](BRANDING_ORIGIN.md) now document the
existing ten master/derivative paths. The missing-creator entry is resolved;
CC BY-NC-SA 4.0 covers rights actually held, without inventing exclusive copyright
in AI output or rights in unprotected/foreign material. No certificate or fresh
full artwork audit is demanded. Actual provider/publication/source-delivery
steps remain separate. No image or user state was changed and no new AppImage,
deployment or push occurred. The private adapter artifact/source identity is
unchanged; its embedded notices retain the source snapshot at packaging.

## Separate private adapter image verified — 27 October 2026

[Private candidate and handoff](ADAPTER_TEST_CANDIDATE.md): exact source
`d8e6ca6f194e24d21d1bf8e80e8449f0310aeddd`, clean tree at packaging; image SHA-256
`a26055ca0aa3e921de3e559af3c5a32337de92f1826c3e4e549bf7781e79ae87`.
One new private image is under dist/private-adapter-2026-10-27; nothing was
deployed. The original Stage and all four checked canonical/installed image
hashes are preserved. No remote PC, host package/driver, normal profile or
shortcut was changed.

Final package audit and CLI help pass. Actual packaged code exercises all four
backend operations and both builder modes, eleven healthy backend-only imports,
zero upstream imports in the client, and four byte-identical builder outputs.
The frontend binary is unchanged from the accepted prior candidate. Complete
standard notices and a filtered actual-payload legal map accompany the new image.
Normal global/system/per-game settings/precedence are retained; owner manual
menu/game/controller tests on the three PCs remain pending. No push/release,
public API permission or complete public source-delivery claim is implied.

## Backend separation and effective component grants — 27 October 2026

The owner authorized the targeted adapter implementation, both UI builder modes,
automated regressions and one separate private test image. All four operations
now live in an independently executable backend; the client no longer imports
Batocera APIs or embeds their Python programs. Existing configuration precedence,
settings files, menu customization and rendering behavior are retained.
Full isolated regression: 820 tests (five expected skips), 52/52 structure
fixtures, ten backend guards and the initial four scope checks, builder/API parity and
runtime-smoke passed. A fifth actual-payload scope check and 66 targeted
packaging/production/backend/license checks pass after correcting source-only
rows in the packaged map, without relaxing the privacy audit. See
[implementation and validation](ADAPTER_SEPARATION.md).

The official Batocera team policy establishes LGPLv3 as its own-code default,
with explicit GPL Configgen and per-file/upstream exceptions; the old deduction
from Buildroot COPYING alone is corrected. [Component evidence](BATOCERA_COMPONENT_LICENSES.md)
records the actual pinned paths. Independent original client code now has the
scoped PolyForm grant, own prose CC BY-NC-SA 4.0, and original backend/integration
contributions MIT-compatible terms. Foreign context/material is excluded.
[The root notice and assignment](LICENSING_1_0.md) supersede previous prospective
no-grant statements. A process/JSON boundary is not a blanket legal exemption.

Gold, the accepted RetroBat/shader artifact and installed images remain protected;
no deployment, push, release or manual host-session test is authorized. The
owner's manual tests are pending separately. Private API inputs remain intact.
Matching public covered source/notice delivery and publication approval remain
actual separate steps; the later owner branding-origin answer is recorded above. Historical old captured-bezel
and bundled-shader audit entries are not blockers for the replacement payload.

## Private candidate built and deployed — 27 October 2026

The owner's explicit "Abgenommen, Appimage bauen und verteilen" has been fulfilled.
[Private candidate / deployment report](PRIVATE_RETROBAT_SHADERS_1_0.md): artifact
source `87cc521f58e0cc2b3e0db51f8dfb1300e7c219bf`, clean tree at packaging; SHA-256
`938df3ab6a33de069baab4b8f9dfac876693a9efaa40f4b952d0519c916027d5`.
Five active copies on MainRig/Laptop/Wohnzimmer were replaced under existing
names, with verified rollback copies, sidecars and ownership receipts. Profile,
SSH, Desktop and Steam hashes/routes are unchanged. Installed CLI starts pass
on all three hosts. MainRig packaged None/NewPixie real 120-frame runs and the
AppDir audit pass. ScreenScraper and the existing private owner Web API build
mode are preserved; no credentials entered source/logs/manifests. No push,
release/tag, visibility change or public-distribution clearance occurred.
Remote visible gameplay/16:10/Gamescope/controller acceptance remains deferred
to the owner; no automatic remote session start or driver change was made.

## MainRig acceptance and private candidate authorized — 27 October 2026

The owner accepted None/NewPixie/additional shader, bezel, Start + Guide and
frontend-return testing in the isolated MainRig test. Xbox initially lacked its
private EEPROM/HDD and PSP lacked its assets reference in that deliberately
separate test profile; the normal installation was complete. Private copies and
RO asset exposure corrected the test without resetting normal state. The owner
then confirmed Xbox/PSP start and the revised PSP menu work.

The system/game bezel menu now offers matching PNG+INFO resources only, prefers
the owning set over exact symlink aliases, and preserves hidden/legacy saved
choices when merely opened. PSP has one real Default Unglazed choice plus
None/Auto. Global selection retains 13 regular sets. New native C++ policy tests
and the rebuilt frontend pass. Full suite: 806 tests, 801 passed, five expected
skips, plus the prior 52/52 structural proof and package/GPU checks.

The owner explicitly lifted the old build hold for a new PRIVATE owner AppImage
and authorized replacement on all three PCs at their existing paths, with verified
rollback copies. Existing ScreenScraper/RetroAchievements private build inputs
remain unchanged. No push, public release/tag/visibility change is authorized.
The other hosts' manual tests remain deferred. Artifact/deployment identities
will be recorded after building and verifying; no remote visual pass is inferred.

## Host shader package installed — 27 October 2026

After the owner's explicit approval, `libretro-shaders-slang`
`20260620.024025.g8ec4c82cf61a-1` is installed on MainRig, EmbercadeLaptop and
WohnzimmerPC. Each native package transaction completed successfully, including
its post-transaction hooks. Read-only checks through the central provider code
find `/usr/share/libretro/shaders/shaders_slang` and all 26 complete preset graphs
on every host, including NewPixie's frame and the selected texture/LUT chains.
No additional dependency package was required. Passwords were entered through
system authentication/SSH terminals and never stored in reports or tool input.

All installed images remain at the accepted Gold hash. No shader was enabled,
profile/driver/session changed, new AppImage built/deployed, or push performed.
The package is ready for later tests of the new selection; three-host rendering
and interactive acceptance remain separate. Receipts and before/after probes are
in ignored `.work/retrobat-integration-2026-10-27/host-package-install/`.

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

> This is a technical handoff, not a replacement for the implementation. When
> information conflicts, use this priority: (1) code and tests, (2) current Git
> commits, (3) observed installed/runtime behavior, (4) current `.work`
> inventories, (5) `COMPATIBILITY_0_1.md`, (6) this document, and (7) older
> chat or session information.

Validation for this integration: 801 tests (796 passed, five expected skips),
25 GTK checks, 52/52 structural routes, runtime/resource smoke, credential-free
frontend compilation and 108 checked local documentation links. Isolated real
RetroArch probes: 31/31 (five default-off systems plus 26 effects) and 13/13
regular-set overlay runs, 120 frames each. An install-shaped production namespace
probe confirms the host provider is readable, resources read-only, all 26 menu
mappings present and user shaders visible. These do not replace native standalone
or three-host visual/manual acceptance. Both remote hosts now pass read-only
preflight and retain the Gold hash; their initially missing optional shader
package was subsequently installed with explicit owner approval (above). See the integration report for versions and limits.
The disposable development frontend is credential-free; no new AppImage exists.

## Targeted 35-PNG source lookup — 27 October 2026

The owner then authorized looking for suitable public license evidence for
only the 35 previously open PNG paths. [Follow-up](BEZEL_35_LICENSE_FOLLOWUP.md)
and [35-row result list](BEZEL_35_LICENSE_FILES.csv): Spectravideo's explicit
Lorenzolamas source credit, RetroBat graphics-role credit, matching stored
content and own-graphics project grant justify a CC-BY-NC-SA-4.0 project-scope
assignment, explicitly marked as an inference. No separate PNG consent message
is claimed, nor is this applied to other artists. Thirty-four paths retain
unresolved final-file mapping. Three have the known TheNamec RC2 SA4.0 original-
project source but no completed derivation mapping; Lightgun has additional
Orions Angel/Fery65 Changelog credit; 30 yield no suitable added grant.

The stored RetroBat evidence covers 28 of these 35 source paths, 27 with the
same recorded content; six vertical aliases/base paths and plain DICE are not
at the same recorded path, SNES-MSU1 differs. These are reused observations,
not new hash criteria or license denials. Public source/credit text and seven
relevant commit-comment endpoints were checked, not a whole history or image
collection. All resources, profiles, image bytes, original 302-row decision
CSV/JSON and the 267 non-target cases remain unchanged. No build, push,
publication or outreach. Raw source receipts are ignored under
`.work/bezel-35-license-2026-10-27/`.
Document/data checks pass: exactly 35 target rows, original source/alias fields,
explicit inference tagging, 102 local links and unchanged old 302-row CSV/JSON.
No functional test rerun is claimed for this documentation/source lookup.

## Concrete bezel decision basis — 27 October 2026

The owner requested exact remaining files/reasons using only existing audits
and RetroBat evidence. [BEZEL_DECISION_1_0.md](BEZEL_DECISION_1_0.md) and the
[302-row companion](BEZEL_DECISION_FILES.csv) now separate 150 PNG paths from
152 technical INFO/LAY paths. Eight PNGs have directly observed Duimon/ND
notices; 107 further PNGs have Duimon contribution association and known general
author-grant sources with variant scope not finally mapped. Thirty-five PNGs
have no concretely mapped applicable grant in these records: 7 Mikael42,
8 Fery65, 1 Lorenzolamas, 17 other community files and 2 preserved V31 files
(amiga1200.png/amigacd32.png) linked to the historical attribution dispute.
No actual file-specific violation/denial is established. Zero historical full
clearance records does not mean zero licenses. No proven pure missing-credit-
only case was isolated. The report lists all 150 PNG paths and all 302 CSV
rows, preserving positive notices and the original historical JSON unchanged.

No new asset reads/hashes/history scans, resource/profile changes, builds,
outreach, push or publication. Only derived documentation/data/link checks
are relevant to this read-only decision follow-up; the earlier functional
regression result is not represented as newly rerun. The image build hold and
explicit-publication-approval boundary remain.
Derived-data validation passes: 302 unique rows, all 150 PNG names in the
report, consistent source/alias fields, 90 local links and unchanged original
JSON. Receipts are under `.work/bezel-decision-2026-10-27/`.

## RetroBat and targeted shader notices — 27 October 2026

The owner supplied RetroBat as a licensing reference and explicitly closes
Carbon's origin/theme-license/credit item. The original Fabrice Caruso / Eric
Hettervik / Nils Bonenberger notice is retained, plus the pinned theme's maioni
credit. Carbon is documented under CC-BY-NC-SA, not unknown. Its original 2.0
heading/4.0 legal body remains unchanged; foreign embedded resources keep their
own terms. RetroBat's pinned project notice preserves upstream licenses, and
its official bezel README confirms a Batocera fork bundled with each install.
No separate asset grant was found in that bezel repository. New tree metadata
was matched to the existing matrix; no artwork/authorship scan was repeated.
See [the RetroBat reference](LICENSE_PREPARATION_1_0.md#retrobat-reference-and-carbon-completion--27-october-2026).

The existing 14-preset/142-file shader inventory is reused. Targeted original
source/history checks close NewPixie's frame (Mattias Gustavsson, MIT OR
Unlicense), Simpletex paper (Stephen Gilbert, CC-BY-SA-3.0; jdgleaver tone/tiling
adaptation) and six Pokefan531 public-domain LUT images. Differing hashes alone
do not reopen known provenance/rights. Four selected legacy code files still
lack an established original grant: LCD Grid and three LUT helpers; EasyMode
already has GPL, with unspecified-version/notice handling kept separate.
Exact paths, author/port history and primary links are in the
[shader follow-up](LICENSE_SCOPE_REVIEW.md#targeted-shader-notice-follow-up--27-october-2026).

Only documentation changes. Source, patches, functional catalog, shaders,
artwork, profiles and accepted AppImage remain unchanged. Regression: 792
isolated tests, 787 successful and five expected skips. No new build, push,
release or contributor contact. RetroAchievements clarification and the
existing build hold remain in force. Runtime smoke, 74 local links, nine
referenced source commits, all five retained reference-text hashes and scoped
diff checks pass; the new-text credential scan reports no hits. Ignored
research receipts are in `.work/retrobat-license-2026-10-27/` and
`.work/shader-rights-2026-10-27/`.

## Licensing preparation and build hold — 27 October 2026

The owner requests preparation for a permanently free noncommercial community
project with public source, without a paid edition or separate commercial
license model. Intended PolyForm covers only positively cleared independent
own software; CC BY-NC-SA covers only own prose/cleared own artwork. Upstream
rights, including commercial permissions, remain unchanged. Five full unchanged
reference texts/notices and current technical component/runtime metadata maps
are prepared; no blanket project grant, source header or package-license
metadata is activated. See [LICENSE_PREPARATION_1_0.md](LICENSE_PREPARATION_1_0.md).

Current source scope is 63 own-package modules and 41 patches (35 Batocera,
six ES), with the earlier mixed API boundaries still requiring scoped review.
Completed bezel comparisons are reused. The owner's public summary of the
team response and the supplied Reddit community comment are recorded with
their provenance limits. ND permits covered unchanged noncommercial sharing;
it does not assign rights to unknown artwork. Existing runtime/assets/profiles
remain intact. The older paused status is superseded only for this bounded
documentation update, not new artwork investigations or contributor contact.

The owner handles RetroAchievements in Discord, including whether the personal
Web API identity may remain or must be replaced. Existing authentication and
private inputs stay unchanged. **No new AppImage until that is clarified.**
No push, visibility change, public source/binary release, tag/release or history
rewrite is authorized by this task; the previous completed push instruction
does not authorize publishing these new changes. Existing Gold artifacts remain.

Validation: 792 isolated tests (787 successful, five expected skips), 25 GTK
checks and 52/52 structural routes; runtime smoke, 102 local links, all five
reference-text hashes, component-map coverage and diff checks pass. Changes
are documentation/reference material only; the existing private image SHA is
unchanged. Static publication audit still flags the absent effective root
LICENSE, pre-existing private host identifiers and three large source masters.

## Laptop standalone decorations — 26 October 2026

The Xbox/PS2 missing-artwork report on EmbercadeLaptop was traced to absent
`python-cairo`: the real PS2 launch's shared helper exited before drawing with
No module named 'cairo'. Both laptop copies match the accepted private image;
layer-shell, KWin fullscreen observation and logical monitor geometry work.
The native Cairo library and Mesa do not provide the Python binding. The owner
separately approved installing python-cairo 1.29.2-1; its import, drawing types
and PyGObject bridge now pass. No driver/emulator settings or AppImage bytes
changed. Source host assessment now offers this independent optional dependency
on KDE/Hyprland Wayland and Gamescope; that prevention awaits a future image.
The owner confirmed restored visibility, then reported cropped proportions in
both standalone and RetroArch bezels. Real laptop captures and offscreen stock
palette/RGBA comparisons isolate a 16:10 geometry limitation. At the owner's
request the README records it. Rendering/viewport/cache/shader behavior and
the working MainRig/WohnzimmerPC installations remain unchanged. Correct 16:10
proportions are OPEN, not accepted by the visibility retest. Dependency changes
pass 792 tests (787 successful, five expected skips), 25 GTK checks, 52/52
structural routes and runtime smoke. No image was rebuilt or published.
See [LAPTOP_STANDALONE_BEZELS.md](LAPTOP_STANDALONE_BEZELS.md) for evidence,
regression and manual acceptance limits.

## Current Git handoff authorization — 25 October 2026

After the accepted private candidate and verified three-host deployment, the
owner explicitly requested pushing the current source and documentation to
origin/master. This supersedes the earlier no-push instruction for Git commits
only. The new AppImage remains private; no new release/tag or asset upload is
authorized. Existing v1.0.0 and its assets remain unchanged. The artifact and
private build files stay ignored. Validation remains 790 tests: 785 passed,
five expected skips, plus 52/52 structural routes and the recorded host checks.
No runtime source changed after that validation; this handoff updates documents.

## Current private polish sprint — 25 October 2026

The owner requested five bounded fixes after the successful Reddit installation:
frontend RetroAchievements lists, KDE window identity/icon, G7 Pro autoconfig,
compact RetroArch notifications and library video playback. Current MainRig is
installed and protected. Earlier unconfigured/cleanup instructions are historical.
No push or publication is permitted; one private candidate will cover the package.
See [POLISH_1_0_PRIVATE.md](POLISH_1_0_PRIVATE.md) for evidence and the test matrix.

The private candidate is built from `935eacf508ab18c369091d8bfbd9023b0d9ed7fd`:
`dist/private-polish-2026-10-25/Embercade-1.0-Private-Polish-x86_64.AppImage`,
SHA-256 `b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`.
The owner confirmed the actual achievement list/progress, video with sound and
KDE icon in Carbon, then working external-theme switching, game start/exit,
Start+Guide/frontend return, notification size, normal mouse and RetroAchievements.
Packaged GB/SNES/3DO/N64 runs show correct G7 Pro autoconfig and rendered frames.
Real Wayland app_id is embercade; XWayland class is embercade. The video cause is
missing distro VLC FFmpeg modules, proven with identical media bytes and isolated
before/after on MainRig. The owner approved installing only vlc-plugin-ffmpeg
3.0.24-1 there; the installer now checks dynamic modules/ABI too. The independent
GameSir driver/service was not changed. Normal config and both prior AppImage
hashes match preflight. Remote hosts remain unchanged and have not accepted the
new candidate; separate 1080p/4K visuals, extra controller inputs/modes, Steam
grouping and an independently verified in-game achievement unlock remain open.
The candidate contains a personal Web API key and is owner-private testing only.
Do not publish/push it or replace the released v1.0.0 bytes/tag. The private input
is under `.work/polish-2026-10-25/private-build/` (0600 in 0700), excluded from Git;
never print its values or copy them into reports. Detailed test counts are in
the sprint report.

RetroAchievements must retain the original Batocera Web API/CHEEVOS_DEV_LOGIN
mechanism, per the owner's explicit correction. Its personal key is build-only,
never a user-installer field. Owner z / Web API key y are separate from queried
frontend user u. Public reuse permission remains unresolved. Working frontend
login and ScreenScraper account behavior are unchanged.

## Private candidate deployed to three PCs — 25 October 2026

The owner subsequently authorized replacing all three hosts' active AppImages
while retaining their link targets. This is complete: two copies on MainRig,
two on EmbercadeLaptop and one on WohnzimmerPC share candidate SHA
`b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`.
Names and individual paths are in the sprint report. Wohnzimmer's menu now calls
the same AppImage as its unchanged Steam shortcut; the old classic prefix/wrapper
is retained for recovery. MainRig/Laptop managed-image ownership hashes and the
Wohnzimmer desktop ownership hash were updated. Config/preferences/input/SSH
and Steam shortcut hashes match fresh inventories. Old files and relevant
metadata were independently verified in each host's private
`~/.local/state/embercade/image-backups/polish-2026-10-25-ac2578b8/`.
The owner also installed the approved missing laptop VLC plugin through SSH;
all three hosts now have working decoder-module ELF closures. The installer
already includes vlc-plugin-ffmpeg under "Install optional host software".
All five image/manifest aliases and actual packaged Python/native --help checks
pass in temporary XDG roots. No normal frontend/wizard was launched, user data
reset, controller driver changed, image rebuilt or GitHub push/release performed.
Remote visual/gameplay acceptance remains separate from these deployment checks.

## Purpose

**Embercade 1.0 feature freeze reached.** The validated classic user-local
Production installation is the golden reference for private AppImage packaging
and final product branding. New features/systems/assets are out of scope.
This does not clear the separate public-release licensing blockers.

## ScreenScraper production-build repair (25 October 2026)

The owner authorized Embercade's own developer authorization in the compiled
frontend, following the public RetroBat build principle. Earlier blanket
runtime-only/provisioning-gate statements below are historical and superseded
for this integration. This authorization does not clear other licensing gates
or authorize a public release, publication or push.

Root cause: `ui-build` enabled only `EMBERCADE_SCREENSCRAPER_RUNTIME`, never
provided `SCREENSCRAPER_DEV_LOGIN`, and packaged that credential-free frontend.
Both request construction and the account check required the local developer
file. The installer and Doctor exposed those private deployment details even
though they were not prerequisites for ordinary installation.

Production now validates a private two-field build file, generates a private
forced-include header defining the existing upstream macro, and compiles the
application authorization into the actual pinned frontend. CMake/argv contain
only the header path, no values. Application credentials are extractable from
the binary; no obscurity/secrecy claim is made. Personal/debug values and loose
secret files are excluded. A value-free frontend hash/mode receipt is verified
through Stage and AppImage; unconfigured production fails, and development
without authorization requires explicit selection and is labelled accordingly.
The compiled branch works independently of local override files. Personal
account entry/storage stays in the existing frontend menu/private user file.
Installer/Doctor account status fields and setup instructions are removed.

RetroBat `master` was inspected at
`37d70f3e46282ba431a64813347cf5b0431bbbfb` (the three requested source files).
A single developer-only official `ssinfraInfos.php` check with Embercade software
identity returned HTTP 200 and the expected infrastructure response. This is
not a full personal-account scrape/media/restart test. The user supplied laptop
Pacman excerpt shows one invocation at 12:22:50, transaction complete at
12:22:54 and last hook starting at 12:22:55 (+0100); its completion and total
wizard time are unknown. Duplicate pasted lines do not establish a second
transaction. The owner dropped further investigation of perceived duration.
No speculative speed optimization was made. New private phase/timing events
cover host checking, confirmation, repository/AUR work and completion; the UI
shows the current localized phase and elapsed time. Actual child exit including
hooks remains authoritative, failure diagnostics/retry are preserved, and a
value-free timing summary survives transaction cleanup.

All tests/builds use development workspaces and isolated XDG roots. MainRig's
prepared profile, handoff AppImage, packages, original collections/backups and
WohnzimmerPC remain unchanged. Source inspection also exposed relocated CMake
cache paths and a missing pinned FreeImage build header; these were corrected
using existing bundled libraries and checksum-verified source, without host
package installation. The final source run passed 767 of 772 tests (five native opt-ins skipped),
including 25 GTK checks and all 52 structural routes. Full validation/build identity is recorded in
[SCREENSCRAPER_PRODUCTION_FIX.md](SCREENSCRAPER_PRODUCTION_FIX.md).

Private candidate built from clean local source
`622c3cf4268321a994703adff0e409098ff24a66`; image SHA-256
`9295a73400eb846a891fd986bb0046ea1f88c69fc3352c79df8a8c9e6a1e5228`.
All 73 focused checks passed against the actual packaged modules. The real
FUSE-mounted image passed isolated English/German CLI status checks; its native
frontend `--help` ran with no home/build-source access. Authorization read from
that binary passed a second developer-only infrastructure API check (HTTP 200),
without runtime developer environment or source. This does not exercise the
personal-account menu/game/media/restart flow; that remains laptop acceptance.
A verified image/checksum/manifest copy is in the owner's requested laptop
backup folder. The CIFS share lacks executable permissions, so copy locally and
mark executable before starting on the laptop. No share policy was changed.
MainRig roots/packages and encrypted backup are unchanged. The owner explicitly
confirmed moving/removing the old demo image during this work; it was not
restored. Code/documentation are local commits only; no push or release.

The owner subsequently confirmed that ScreenScraper works without problems in
this AppImage. This is user-reported functional acceptance; individual media
types and persistence after restart were not separately described.

The laptop startup issue was subsequently reproduced with the owner-provided
SSH access. Managed cores are local Btrfs files; ROMs remain on CIFS. RetroArch's
extra Qt desktop browser asks KDE for directory icons, repeatedly scanning the
many scoped scraper bind mounts. With 920 read-only media/metadata bindings in
an isolated comparison, its first EGL buffer swap took 43.135 seconds; disabling
the unused companion reduced this to 0.622 seconds with the same ROM and core.
The earlier log silence was not itself a first-frame measurement. A stale
profile path is not needed to reproduce the problem. Patch `0030` applies the
companion defaults through pinned configgen only on Embercade desktop, refreshing
old generated flags while retaining the in-game menu, saves and explicit user
overrides. No network mount policy, system package, driver or normal owner
profile was changed by the probes. See [RETROARCH_STARTUP_FIX.md](RETROARCH_STARTUP_FIX.md)
for the reproduction, limits and current validation/handoff status.

The fix passes 768 of 773 tests (five expected skips), 25 GTK checks, all 52
structural routes and runtime smoke. The clean-source image from `f161182`
was verified and copied to the owner's requested laptop AppImages directory
with checksum/manifest. Actual packaged Game Boy, SNES and ParaLLEl N64 startup
probes pass with the full read-only media topology; the ScreenScraper frontend
is byte-identical to the accepted candidate. The owner subsequently confirmed
that the Game Boy delay has disappeared when opening the new image with existing
settings. Temporary remote test profiles were removed; no normal profile reset,
driver/package change, Wohnzimmer-PC update, public release or push occurred.

## Private GitHub 1.0 release (25 October 2026)

**Published:** [Embercade 1.0 / v1.0.0](https://github.com/RetroGamerGER/Embercade/releases/tag/v1.0.0),
marked Latest inside the private repository. Master and the annotated tag were
pushed successfully. The release contains all five prepared assets plus
GitHub's two source archives. Every GitHub-reported asset SHA-256 matches its
local file, including the original tested AppImage hash `233f1745…`.
The owner selected the files through GitHub's normal picker after the browser
extension declined automatic local-file upload. No extension permission or
repository visibility change was made. Final publication and digest checks
were verified through the authenticated browser; no API token was created.

The owner authorized the pending master push and a tagged AppImage release in
the existing private repository. `v1.0.0` targets the exact tested image source
`3430484d564d7ff58fa278c7e9de25391f5de754`; later master changes retain acceptance
and rollback evidence. Release assets are the byte-identical image renamed
`Embercade-1.0-x86_64.AppImage`, its checksum, an external manifest whose sole
semantic change is the filename alias, `BUILD_INFO.json` and `SHA256SUMS`.
The AppImage hash remains `233f1745…`. Source archives come from the exact tag.

The 781-test result and actual-image evidence remain applicable. A final patch
context whitespace cleanup generates byte-identical Libretro configuration
code; no binary rebuild or reset of the recently cleaned host is needed.
The public audit remains expected-red for the absent effective root license
and three retained large branding masters; unresolved rights/source-delivery
gates and the paused decoration investigation remain open. Private release
authorization does not change visibility or clear public redistribution.
Preparation, limitations and user instructions are in [RELEASE_1_0.md](RELEASE_1_0.md).

## Linux graphics and shader selection (25 October 2026)

The owner confirmed 3DO starts after selecting Vulkan. The original failure
requested a GLSL Newpixie preset although the curated catalogue supplies Slang.
Desktop automatic graphics now prefers detected Vulkan, preserving explicit
choices and pinned OpenGL exceptions. Dolphin/PCSX2 receive availability-aware
desktop defaults; follow-up patch `0032` also covers standalone PPSSPP/Azahar
with their existing probes and manual overrides. Incompatible or missing effects no longer cancel a game before
emulator startup. A localized, game-specific frontend notice follows the return
from that game. The persistent choice remains unchanged.

The owner explicitly clarified that shaders must remain optional and OFF by
default: the existing shipped profile keeps `global.shaderset=none`, with no
system/game effect preset. Vulkan preference does not select a shader. Patch
`0033` also explicitly clears stale desktop shader-enable state when None is
selected; the actual pinned dry run checks fresh and previously enabled state.
Existing explicit user effects remain preserved on update.

All 14 curated shader graphs are checked before staging; the catalogue is
included in packaged metadata for an actual-image empty-profile provision check.
The installer completion page receives no technical graphics hint, per the
owner's corrected requirement. See [LINUX_GRAPHICS_AND_SHADERS.md](LINUX_GRAPHICS_AND_SHADERS.md)
for the current validation and handoff state. Development is isolated from
parallel README/getting-started edits; no system package/driver installation or
Wohnzimmer-PC change is part of the repair.

The initial packaged laptop candidate passed 21 distinct GPU start/render cases
across 3DO/Game Boy/SNES/N64 and all 14 curated effects. Every effect's Slang
passes compiled on the Intel GPU; empty-profile image validation finds all
14/142 resources. The incompatible-effect fallback captured the 3DO boot logo
without changing the saved selection. This is launch/render evidence, not full
gameplay, controller exit or visible localized-popup acceptance. Standalone
PPSSPP/Azahar writers pass 35 automatic/manual/fallback scope combinations.

The compatibility candidate from source `333b43b` passes 780 tests (775 pass, five intended skips), all
52 structural routes and runtime/shader smokes. That private
`Embercade-1.0-AutoGraphics-x86_64.AppImage`, SHA-256
`d1d478bfd8cb687fcf3349295453050a6012d0858712ff9ff8343073b6e7dfe8`,
is verified on the development SSD and in the requested laptop AppImages
folder with checksum/manifest. The actual image passes 600-frame
3DO/Game Boy/SNES/N64 starts, with inspected boot/game images and zero exit.
Its unchanged shader/frontend/Libretro payload retains the 14-effect GPU
compilation evidence, and empty-profile provision again validates 14/142.
Normal laptop configuration hashes are unchanged; all four owned remote
temporary probe roots are removed. Visible popup/full gameplay/controller-exit,
standalone gameplay and other compositor/GPU acceptance remain separate.
No normal MainRig setup, driver/package change, menu image replacement, push
or publication is performed. Explicit-None validation follows in
[LINUX_GRAPHICS_AND_SHADERS.md](LINUX_GRAPHICS_AND_SHADERS.md).

The current handoff includes the explicit-None guard: source `3430484`,
781 tests (776 pass, five intended skips), all 52 structural routes and smokes.
Current AutoGraphics image SHA-256:
`233f17457379dd679eb8a4ef595999e273dd035d52fc88ce49a83c3b0a623efd`.
The verified SSD/laptop image passes actual 600-frame 3DO/GB/SNES/N64 starts
with the shipped defaults and shaders explicitly OFF, no shader argument or
effect compilation. A separate chosen Newpixie GB test enables/compiles all
four passes and exits zero. Complete provision again validates 14/142. All
three additional owned probe roots are removed and normal configuration hashes
remain unchanged. Optional effects are not first-run presets; only compatible
renderer selection is automatic. No manual choice is reset on update.

On 25 October 2026 the owner confirmed the delivered current AutoGraphics
candidate was tested and works as intended. This adds owner-confirmed operation
to the recorded automated/startup evidence. The response does not enumerate
individual games, hosts, controller-exit or exceptional-effect popup scenarios;
their detailed acceptance limits remain as documented in the graphics report.

## MainRig aborted setup rollback (25 October 2026)

After a later setup attempt failed while installing host emulators, the owner
requested rollback on MainRig, explicitly included older normal RetroArch/shadPS4
data and restricted removal to this local PC. A fresh inventory identified six
local Btrfs targets, with no symlinks or nested mounts. Per-entry identity checks
preceded removal of 414 entries (323 regular files, 2,215,167,556 logical bytes):

- `~/.config/embercade/embercade.toml`
- `~/.local/share/embercade`
- `~/.local/state/embercade`
- `~/.config/retroarch` (empty directory tree)
- `~/.local/share/shadPS4`
- `~/.local/share/shadPS4QtLauncher`

This removed 232 copied cores, managed shadPS4/Xenia images, isolated Xbox
flash/MCPX/EEPROM/HDD files and installer timing state, plus the explicitly
approved older shadPS4 settings/data/cache and launcher backend cache. The host
worker recorded failure/exit 1 after 34.286 seconds. No new emulator package
transaction completed; relevant emulator packages and `gtk-layer-shell` were
already absent. No packages were removed, and the complete installed package
snapshot remained identical. Existing OBS, shared dependencies, FUSE 2,
development pugixml and Vulkan/KDE tools are retained.

Read-only `read_state` confirms `configured=false`, no saved language or
ROM/BIOS selection, zero managed cores/providers and no prepared Xemu state.
All six targets are absent; no Embercade cache, classic prefix/launcher,
application-menu/desktop entry or Steam shortcut remains. The check creates no
new profile and does not start the AppImage or an emulator.

The config parent remains solely for the protected `WohnzimmerPC` SSH key.
Its bytes/permissions, the owner's current AppImage (the verified AutoGraphics
payload `233f1745…`), encrypted ScreenScraper backup and manual xpadneo file
pass before/after identity checks. No live ScreenScraper credential files were
present in the removed profile; the existing encrypted archive is preserved,
with no new decryption or credential restoration claimed. The owner separately
chose to KEEP the controller setting; no module/device change or disconnect was
performed. This is a user-state reset, not a fresh controller-driver baseline.

Network drives, original collections/PPSSPP assets, shared scraped media,
installation material, external development SSD/repository/builds and backups
are outside every deletion target. Other applications, Steam data and the
Wohnzimmer-PC are unchanged. No source change, build, new package install,
system-update rollback, push or automatic setup is part of this operation.
Exact inventory, plan, removal journal, protected identities, package snapshots
and German report are retained in the private development audit folder
`.work/mainrig-rollback-2026-10-25-m2dy1awr/`. Logical bytes do not establish
physical space reclaimed from Btrfs snapshots.

## MainRig Reddit-demo cleanup (10 October 2026)

The owner reports personal Embercade 1.0 acceptance complete and requested a
new clean user setup for the recording. Fresh inventory, dependency checks and
an explicit new confirmation of the normal shadPS4 test profile preceded cleanup.
Eleven bounded targets were removed: 2,360 inventory entries, 2,866,836,703 logical
regular-file bytes, including 232 managed cores, two managed provider AppImages,
isolated emulator profiles/firmware/EEPROM/saves, the managed menu-launcher image,
logs/caches and desktop entries. An abandoned Embercade FUSE mount was detached
and its empty directory removed. Development SSD content was preserved in full.

All 18 reinstalled test packages were removed successfully through the end of
Pacman's nine hooks, with no recursive dependency/orphan removal. The immediate
package diff was exact. The owner then installed OBS Studio independently and
explicitly confirmed its preservation; it reinstalled `mbedtls3`, now required
by OBS. Thus 17 of the removed packages remain absent. FUSE 2 is retained for
AppImagePool's actual runtime requirement; `pugixml` for development, DOSBox for
Boxtron/Steam, normal desktop dependencies and OBS remain installed.

The read-only first-run state is unconfigured: no saved language/ROM/BIOS paths,
zero managed cores, no managed providers or prepared Xemu files. No normal test
profiles, old desktop/Steam entries or portable AppImage profiles remain. KDE's
menu cache was refreshed. The config parent contains only the preserved private
`WohnzimmerPC` SSH key. Git object connectivity passed; protected SSH/Git files,
installation material and final image passed a byte/metadata comparison. Shared
ROM/BIOS/media and backups received no writes. Network-root checks account for
CIFS automount identity changes; local roots and protected top-level entries
remain unchanged.

The existing AES256 ScreenScraper archive was authenticated and both credential
files recovered only in memory; its hash matches the previously source-verified
backup. No current standard credential files were present, no plaintext copy was
written and nothing was restored. Ordinary-user developer provisioning remains
the separate documented release limitation. The manual xpadneo configuration
and live `disable_shift_mode=Y` were preserved with no controller disconnection
or reset: the recording host already has the Guide-mode prerequisite prepared.
Fresh privileged helper apply/undo remains a distinct acceptance case.

The final FileChooser-named AppImage remains at its handoff location with its
checksum and manifest: source `e084416db1aa4fd30237d24f3bb2ca178db2a2fd`, SHA-256
`14184e152a4030e84235cadc66c611352c8e1fe0b8f52475720df527dbaa40a3`.
No image launch/build, emulator installation, application source change or
WohnzimmerPC access occurred in this cleanup. Only documentation is committed;
the user performs the next installation personally. See
[REDDIT_DEMO_CLEANUP.md](REDDIT_DEMO_CLEANUP.md) for removals, recovery and limits.
The following installation/build records are retained as historical evidence.

## Private 1.0 AppImage and final product identity

The owner approved a separate bilingual Controller & Hotkeys step, now after
Host software in the ten-stage installer. It retains the existing two exit
presets and adds live xpadneo detection, explicitly confirmed administrator
adjustment, ownership-checked undo, and a modal held-button exercise. The host
helper must remove all affected controllers' old input devices before changing
the Guide shift parameter, then reconnect and inspect synthetic mouse buttons.
Foreign host settings and normal emulator profiles remain untouched. See
[CONTROLLER_SETUP.md](CONTROLLER_SETUP.md) for the transaction and test scope.

On MainRig, the owner confirmed Game Boy Guide + Start exit after a manual
xpadneo shift-mode adjustment. A subsequent blocked physical mouse was traced
to two held keys on the driver's synthetic mouse; targeted controller
disconnect/reconnect restored clicks and cleared all keys. The owner confirmed
recovery. This is the root cause for the new safe reconnect sequence, not a
claim that the new installer helper has already passed real host apply/undo.

Controller-step source validation: 757 tests discovered, 752 passed and five
unrelated native emulator/layer-shell opt-ins skipped. This includes 24 actual
GTK checks on a private display and 33 synthetic backend checks. All 52
structural routes and runtime/frontend-library/shader smoke checks passed.
An isolated KDE Plasma/Wayland preview visually passed both languages, conflict
and ready states, all ten sidebar steps and the full driver confirmation, with
no configuration writes or host adjustment calls. The privileged helper is
staged temporarily outside the user FUSE mount, with private permissions, so
AppImage authentication does not depend on root access to that mount. Source
and visual evidence are under `.work/controller-setup-xtv3fteh/` and
`.work/controller-kde-visual-49b4qer_/`. Fresh-host administrator apply/undo,
interrupted or multi-pad Bluetooth recovery, actual game exit and live
Gamescope/Hyprland remain manual acceptance cases.

The controller AppImage was built from clean commit
`e084416db1aa4fd30237d24f3bb2ca178db2a2fd`; its SHA-256 is
`14184e152a4030e84235cadc66c611352c8e1fe0b8f52475720df527dbaa40a3`.
All 88 focused tests passed against its verified extracted Python modules,
including all 24 GTK checks. Seven changed implementation modules were compared
byte-for-byte with source. The actual FUSE-mounted image supplied the helper
for a verified private temporary copy and unprivileged invalid-operation check;
a fake authentication cancellation confirmed cleanup. This made zero admin or
host-mutation calls. Its real preference CLI saved only the chosen exit preset
in an isolated profile, preserving the language and unrelated fixture settings.
The local FileChooser-named image and existing managed copy behind the menu
launcher were replaced with identical verified builds; desktop ownership hashes
were refreshed through the existing updater. The user configuration's bytes and
modification time, the existing driver setting and the set of desktop targets
were unchanged. Packaging/deployment evidence is in
`.work/controller-setup-xtv3fteh/` (`packaged-tests.log`,
`fuse-controller-evidence.json`, `deployment.json`). The new helper's privileged
apply/undo is still explicitly awaiting fresh-host interactive acceptance.

On 10 October 2026, the owner tested the new Controller & Hotkeys live test
in this AppImage on MainRig with the existing configuration and confirmed that
Start + Guide works and the physical mouse remains normally usable. This is
real interactive acceptance of the installer chord test and continued desktop
mouse operation on the already adjusted host. It does not establish fresh-host
privileged apply/undo or a new in-game exit test; those scopes remain separate
from the earlier confirmed Game Boy exit.

The following message-layout and chooser records describe earlier builds;
their functionality and regression tests are retained by this controller change.

Every installer launch now begins with Language, even when a language or complete
setup is already saved. The saved choice is preselected; the system locale is
only the initial fallback. Saving and continuing opens Welcome while preserving
the existing configuration. Later language changes still return to their prior
wizard page. This changes installer entry, not normal configured frontend startup.

Installer message dialogs now share explicit wrapped-text sizing for information,
errors and confirmations. The old scroll container requested the secondary
label's one-line natural height even when its narrow viewport required multiple
lines, clipping even the short PS3 success message. Dialogs now open at a readable
width within the monitor's work area. Normal messages retain GTK's native wrapped
layout; only long reports use a viewport, remeasure its wrapped height and show
a scrollbar. German/English rendered-text
regressions check the exact PS3 message, longer errors/confirmations and the last
line of an 80-line report; confirmation still defaults to No.
An explicit label width also prevents GTK/Wayland from sizing the initial window
as if word/character wrapping had only a single character of horizontal space.
Validation: 664 regular tests and 16 opt-in GTK checks passed; runtime,
frontend-library and shader smoke checks passed. Isolated KDE/Wayland previews
validate the actual localized success, error, confirmation and long-report
layouts without invoking firmware installation or writing normal user settings.
The corrected private AppImage is built from clean source commit
`2e92f6406fbe07c0e3cc306209d28ee5d688032e`; its SHA-256 is
`22dc652a216d8f019937f3ee3480ce4c0abebfc07673f680bc434686265629a1`.
All 16 GTK checks also passed against the verified extracted image's actual
Python module, including the saved-language restart cases. The final ordinary
suite discovered 685 tests: 664 passed and 21 opt-ins skipped (16 subsequently
run; five unrelated native emulator/layer-shell checks remain unrun).
The local image and the existing managed copy behind the menu launcher were
updated; the desktop updater recorded the new ownership hash. The setup config
remained byte-identical with unchanged modification time. Local evidence is
under `.work/message-layout-krjtpqpd/`; the personal emulator/clean-install
acceptance remains separate from these isolated GUI and packaging checks.
The following chooser evidence describes the earlier build; its functionality
and regression tests remain preserved in this newer image.

The first-run source browser now uses a shared Gtk.FileChooserNative/desktop
portal path for all six directory and three file fields. The previous custom
list interpreted an empty string as `Path(".")`, so the launch working directory
(usually the AppImage folder) became its initial location. Blank/unavailable
fields now start at Home; existing directories and files are preselected.
The desktop supplies places, drives, bookmarks and hierarchical navigation.
A bounded portal-version check, conventional GTK fallback and cancellation-safe
modal lifetime preserve setup/import behavior. Gamescope keeps an in-process
GTK chooser. Mounted network paths are accepted; URI-only remote locations need
a filesystem mount. Native dialog chrome, including KDE's Cancel button,
follows the desktop language; Embercade titles and the accept label follow the
chosen installer language. Source, packaged portal and visual evidence are
recorded separately in
[INSTALLER_FILE_CHOOSER.md](INSTALLER_FILE_CHOOSER.md).

Chooser validation on 2026-10-10: 664 ordinary tests plus 13 opt-in GTK tests
passed, including all 52 structural routes. The actual clean-built AppImage
`c638d2e` opened the KDE portal on Wayland in isolated English and German
profiles. Visual screenshots confirm Home, native hierarchy and named mounted
drives/network places. A configured CIFS ROM path also opened correctly and
survived cancel/reopen with unchanged test configuration. Native selected-path
acceptance and live Hyprland/Gamescope checks remain manual; the owner retains
the full personal clean-install test. At the owner's request, the old local
Final-polish image and sidecars were replaced by the verified FileChooser build
under `~/AppImage/`, with existing profile metadata unchanged.

After the historical deployment recorded below, the owner explicitly approved
removal of MainRig's previous test installation/profiles and its test-only host
emulators. Original sources, development data, shared system dependencies,
encrypted ScreenScraper backup and WohnzimmerPC were preserved. New chooser
validation uses disposable development profiles; it must not reinstall host
emulators or consume the owner's personal clean-install acceptance.

The global Garuda audit fixes central KDE physical-mode detection (previously
1080p even on a 1440p output), adds a disposable KWin observer to the existing
standalone layer renderer, aligns RPCS3 firmware source discovery between
Doctor and launch, and checks shadPS4's actual outer ELF dependencies instead
of requiring FUSE 2 unconditionally. Desktop Wayland bootstrap offers
`gtk-layer-shell` and display-query tools through the existing package plan.
The owner approved and authenticated installation of `gtk-layer-shell` on this
host; no emulator package was installed for testing.

The owner explicitly approved German/English installer localization and terminal
completion as 1.0 additions. The initial language page precedes Welcome; saved
`[installer].language` overrides the locale and can be changed without resetting
setup. One central catalog covers the UI and Embercade terminal messages.
Structured GUI diagnostics reuse existing assessment; external Pacman/RPCS3
output and the frontend's independent language setting remain native.
A private per-invocation result identifies the actual bootstrap child's exit
(after package-manager hooks), closes the extra terminal only on success,
retains failure output until Enter, and refreshes status for success/failure/
cancellation/missing result. Konsole runs separately with `--nofork`; no foreign
terminal is touched. PS3 firmware can now be installed from an explicit isolated
RPCS3 action in the wizard.

The owner approved the final-polish exception: the existing GTK assistant now
has a nine-stage dark orange/red layout, persistent sidebar/navigation, original
branding and central English/German localization. Xbox setup validates/imports/
backs up/authenticates offline EEPROM edits and preserves identity/HDD key;
native Xemu initializes missing state. PS3 setup offers consent-based official
PUP retrieval and native installation in disposable isolated state, then
activation without replacing existing firmware. Desktop integration offers a
stable external local AppImage, Games menu by default, optional XDG desktop
shortcut and existing Steam artwork. Its manifest/rollback preserves classic
ownership and conflicting user-modified entries. Readiness checks prioritize
effective collection routes and inspect actual isolated firmware, core ABI,
BIOS metadata and installed runtime closure. See [FINAL_POLISH.md](FINAL_POLISH.md)
for state contracts, recovery and explicit two-host English/German acceptance.

Native KDE evidence identifies Plasma's reserved 32-pixel area: layer-shell
exclusive zone 0 allocated 2560×1408 on a 2560×1440 output. Zone −1 now covers
the full logical monitor, with stale-allocation guards and no hardcoded offset.
The Gamescope route and existing conservative viewport clipping are preserved.
Actual GameCube/Wii/Xemu artwork/game acceptance remains OPEN on both hosts.

The owner report was EEPROM settings not being used, not file rejection.
Earlier read-only comparison found English in the isolated profile and German
in normal Xemu. A later read-only inspection during final polish found both
files valid and German: the owner had changed the active state. Neither normal
nor active user EEPROM/HDD was modified by this work; tests use disposable state.
The format editor is implemented and validated offline against native-generated
EEPROM; visible dashboard/game acceptance remains separate.

ScreenScraper is **working, user-confirmed on MainRig (10 October 2026)** in
the new AppImage. The owner identified the reported problem as a user-side issue
and explicitly confirmed successful operation; the incident is closed without
a code change. The earlier developer-only API success and personal-login
HTTP 403 remain historical diagnostic evidence, not the current status. No new
automated API probe, individual media-type/restart checklist or second-host
acceptance is inferred from this confirmation. Safe ordinary-user application
authorization remains a separate public-release blocker until provider-approved
redistribution/provisioning is agreed. No shared application password is embedded.

The previous audit passed 622 discovered tests and all 52 structural routes.
Final-polish validation passes 646 discovered tests (633 default plus 13
separately exercised GTK/KWin/native-Xemu opt-ins), all 52 structural routes
and runtime/frontend/shader smokes. Current build evidence, source revision and image/Stage hashes
are recorded in the delivery report and sidecars. Two-host interactive tests
remain OPEN; public release and the paused decoration licensing gate remain
separate. The complete prior findings table remains in
[GLOBAL_GARUDA_AUDIT.md](GLOBAL_GARUDA_AUDIT.md).

Both reference hosts now have the final-polish AppImage built from clean source
`bd3d2cb4db67eb8b34948e3007c73e743c2b2acf` (10 October 2026). MainRig uses the
new managed local AppImage and Games-menu integration; its installed Doctor
passes. WohnzimmerPC's existing Steam-target AppImage was replaced at the same
durable filename, and its classic installation was updated through the verified
payload installer. Both remote start paths pass Doctor; classic verification
reports ALREADY UP TO DATE. Steam's appid, shortcut bytes and artwork are
unchanged, with the prior image retained for rollback. Preservation checks cover
201,168 unchanged remote entries and 7,115 unchanged existing MainRig entries;
MainRig adds only its four expected integration entries within Embercade XDG
roots. Profile comparison includes the present RetroArch/Dolphin/PCSX2/RPCS3/
Xemu config/data roots. Small readable files were content-hashed; large files and one unreadable
remote cache log were checked by metadata. No host packages, normal emulator
profiles or game sources were changed. These deployment checks do not establish
new interactive acceptance; see [FINAL_POLISH.md](FINAL_POLISH.md).

The Garuda blank-install follow-up removes the erroneous EEPROM-source
requirement and extends the existing optional host bootstrap to Garuda.
Native Xemu creates absent EEPROM state at the existing isolated save path;
updates/reinstalls preserve it. Stable and known development package variants
are probed in configured pacman sources before optional AUR fallback. GTK
dialogs now explicitly own modal lifetime/SDL input. The initial fix retained all
terminal output; the global audit supersedes that with success-only auto-close. The reported spontaneous confirmation disappearance was
not reproduced in timed GTK/Wayland checks; those checks do not establish
interactive acceptance. Current evidence, remaining two-host tests and recovery
are in [GARUDA_BLANK_INSTALL.md](GARUDA_BLANK_INSTALL.md).
The follow-up passes 595 discovered tests (six opt-in GTK/Xemu checks exercised
separately), all 52 structural routes and the required smokes. After the owner
installed the missing build-host `pugixml` prerequisite, Stage and AppImage
packaging passed. The separately named Garuda-fixes image passes actual CLI
startup/Doctor with empty external XDG roots; visible wizard/gameplay acceptance
on both hosts remains OPEN for this revision.

The private AppImage wraps the verified classic Production Stage unchanged at
`AppDir/usr`, then delegates through the same `bin/embercade`, path API, wizard,
Doctor, Bubblewrap launch, core/provider resolvers and lifecycle cleanup. No
emulator, controller, scraper or setup backend is replaced. The visible product
label is centrally **`EMBERCADE 1.0`**; Python/package version **`0.1.dev0`**
deliberately retains its existing semantics.

Only the pinned default **es-theme-carbon** is included. The existing active
downloaded theme is read from external XDG user data; it is not a build input.
ROMs/BIOS, saves/states, screenshots, media, both ScreenScraper secret files,
managed cores/providers, user PPSSPP/Xemu resources and Steam user metadata are
excluded. No portable image-adjacent profile is created. CLI mutation rejects
prefix/AppDir-local state/write targets; Production diagnostic defaults use
external XDG state. Normal classic update and replacement of a closed AppImage
preserve user state. Shared default state is for sequential use, not concurrent
frontend sessions.

The image includes the existing FreeImage/SDL2_mixer closure, not a host GPU
stack. CPython 3.14, host GTK3/PyGObject for the wizard, Bubblewrap and the
existing frontend/desktop/audio/graphics dependencies remain explicit host
requirements. This is a supported-reference-host build, not proof of generic
distribution or older-Python portability. Steam registration reuses the existing
idempotent backend: explicit `--replace-existing` switches the existing entry
to the durable image filename while preserving its appid and unrelated fields.

Build tools/runtime bytes are pinned; ordinary packaging is offline. The
builder audits actual extracted output and emits source/Stage/file hashes,
dependency boundaries and a scoped notice index. Frontend prefix mapping/debug
stripping and removal of local pip PEP610 origin records from the Stage copy
prevent private build-source URLs from being shipped; package identity,
license notices and the development source/runtime remain unchanged.

MainRig AppImage acceptance is user-confirmed: 1.0 splash/menu, preserved active
theme and controller navigation, one ScreenScraper request, Libretro,
Xemu/Dolphin 4:3 bezels, Xenia and shadPS4 with image/audio/input, exit to the
same frontend and Quit Embercade. No frontend/provider process or FUSE mount
remained after quit. The classic path also passes a user-confirmed game/exit/
quit regression and installed Doctor. The initial normal updates preserved
16,062 MainRig and 198,102 WohnzimmerPC inventoried XDG entries (only the
owned install manifest is excluded). WohnzimmerPC's AppImage start from the
real interactive Steam/Gamescope session is also user-confirmed: branding,
splash, preserved theme/controller menu, Libretro and standalone game with
decoration, Player-1 exit/return and Quit to Steam. No frontend/provider process
or FUSE mount remains after quit. Steam retained appid `4059814080`; all foreign
nodes and non-target fields are byte-identical, and existing artwork is unchanged.
The owner subsequently confirmed the caption-free splash on MainRig. At the
owner's request, the same cosmetic update was applied to WohnzimmerPC without
another visible test: its Doctor returned status 0, and preservation checks
covered 198,109 inventoried entries with zero unexpected changes or additions.
The final MainRig update preserved 16,161 inventoried entries with zero changes
or additions. These update/diagnostic checks are separate from the previously
completed interactive AppImage E2E on both hosts and the classic MainRig
game/exit/quit regression.

At the original AppImage milestone, the source suite passed **578 tests**; runtime, frontend-library, shader
and Stage Doctor smokes pass. The verified Production Stage SHA-256 is
`a8612d6def70b249785964bb2e51be82965dc15bf7d856e4afa4b23494bce033`.
Packaging reproducibility passes: two fresh complete builds with identical
Stage, packaging inputs, source identity and epoch produce byte-identical
images and manifests. A separate focused fixture also checks different build
umasks. This is packaging reproducibility, not a cross-machine compiler-rebuild
claim. **Private functional GO** applies to the two tested AMD/CachyOS reference
hosts; generic distribution portability and public release are not cleared.
The loading screen
intentionally keeps its existing logo, progress and minimum duration without
an extra version caption; other visible product text stays `EMBERCADE 1.0`.
See [APPIMAGE.md](APPIMAGE.md) for the build/usage,
read-only contract, host requirements and independent public-release gates.

Embercade is building a Batocera-/RetroBat-like integrated emulation experience
inside a normal Linux desktop session. It is not a dual-boot distribution and
does not replace the host operating system. Development targets CachyOS/Hyprland
and a second SteamOS-style CachyOS host running Steam/Gamescope. KDE Wayland
frontend startup has also been tested; that does not establish generic KDE
standalone-bezel support.

The frontend is a desktop-adapted build of Batocera's EmulationStation fork.
The backend is Batocera 44's `batocera-launch` architecture. Emulator binaries
remain separately installed host software. Libretro cores are user-/host-supplied
and may be copied into Embercade-managed user data; they are not bundled.

## Product scope

> **If you can still walk into a store and buy the console new, Embercade is not meant to replace it.**

Embercade focuses on older consoles and computers, preservation, classic gaming
and users' legally obtained content. It is not positioned as a replacement for
consoles still sold as current products. This is a durable product philosophy
and scope rule, not a legal classification of emulation. Future system/provider
work must follow this scope; the existing compatibility matrix and confirmed
launch evidence are unchanged by this documentation decision.

## Upstream pins

`upstream.lock` is authoritative:

- `batocera.linux`: `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`
- `batocera-emulationstation`: `1750dded8c0fdff70630026f756a69fcad0bb995`
- architecture: `batocera-launch-44`

Reference clones are read-only. Runtime and frontend scripts archive pinned
sources into ignored `.work` trees and apply project patches there.

## Architecture

The proven launch lifecycle is:

```text
Batocera EmulationStation
  -> Embercade desktop runtime and path compatibility
  -> batocera-launch 44
  -> modern emulator plugin or configgen
  -> separately installed host emulator and user-/host-supplied core
  -> synchronous process wait and cleanup
  -> the same EmulationStation process
```

Batocera `SystemConfig` reads upstream defaults and the shared `batocera.conf`.
Embercade asks that stack for the effective emulator/core choice and passes it
through; it does not maintain a competing selection database. For Libretro,
the central resolver maps Batocera's logical core name to an actual readable
`*_libretro.so`. Managed cores take precedence over host RetroArch discovery
unless an explicit Embercade override is configured. Standalone executables
are resolved from an explicit config override and then `PATH`. The provider
layer accepts a user-supplied AppImage path or a managed copy imported from a
user-chosen folder; Embercade does not bundle or download that binary.

The original Bubblewrap frontend harness remains a development bridge for
upstream's compiled `/userdata` and `/usr/share/emulationstation` assumptions.
Production now uses the same isolation model through an install-shaped,
relocatable Embercade prefix rather than through `dev-run`.

The desktop EmulationStation policy exposes **QUIT EMBERCADE** as its quit
action and invokes the frontend's normal `QUIT` mode. Appliance reboot,
shutdown and suspend actions remain hidden by that policy. The product label
is verified in the pinned frontend patch and policy test; translation coverage
for the new label has not been separately validated.

The global frontend menu footer/subtitle is branded `EMBERCADE 1.0`.
`GuiMenu::addVersionInfo()` previously combined `BATOCERA.LINUX ES V` with
`ApiSystem::getVersion()`, which fell back to the compiled ES version `42`
in the installed namespace. This was generated frontend text, not theme
metadata. The frontend patch now selects a compile-time product label passed
by `scripts/ui-build` from the central frontend product constants in
`src/embercade/version.py`. Theme changes affect styling, not that label; Carbon
and downloaded themes are not modified. Packaging remains `0.1.dev0`, and
upstream Batocera/ES API, scraper and diagnostic versions are unchanged.
The existing theme-independent product splash policy remains in place; the
product label is also used by About/system information,
window title, wizard, desktop metadata and new/explicitly updated Steam entries.
The former `EMBERCADE 0.5` label was user-confirmed with both Carbon and AI-Hypertocera on
MainRig/Hyprland and in the WohnzimmerPC's real interactive Steam/Gamescope
session. Theme styling follows the selected theme without changing the
product text. The second-host acceptance used the user's manual Steam launch,
not an SSH-only startup. Product splash and controller menu remain accepted
on both hosts. Normal Quit Embercade closes the frontend; the second host
returns to Steam with no remaining frontend process. The normal offline
update preserves installed user themes, config, saves, providers and artwork.
That historical branding milestone passed 353 tests, including central-version/build/patch
contracts. The built Production frontend contains the exact product label and
no former `BATOCERA.LINUX ES V` footer literal; runtime/frontend-library/shader
smokes, Production Stage and staged Doctor pass.

## Filesystem model

`src/embercade/paths.py` owns the persistent path model. Config, data, cache,
state and runtime use isolated Embercade XDG roots. Generated emulator configs,
saves, states, screenshots, recordings, caches and logs stay there. The pinned
Libretro shader tree and Batocera decoration resources are consumed read-only.

Development collection roots are configured per host, for example:

```text
ROM_ROOT=/path/to/roms
BIOS_ROOT=/path/to/bios
```

They are local configuration, not application constants, and are always treated
as read-only. Normal host RetroArch, Dolphin, PCSX2, RPCS3 and Xemu profiles must
not be modified.

## Current inventory facts

The current ignored host inventories report:

- ROMs: 265 top-level directories, 45 distinct ROM-relevant Batocera system
  IDs, 465,819 regular files and 4.11 TiB of indexed file metadata.
- Libretro: 232 distinct installed cores at 233 locations; 117 of 124 pinned
  Batocera logical core names resolve on this host.
- BIOS: 3,823 files (1.31 GiB). All 17 ROM-relevant systems with Batocera BIOS
  requirements are satisfied; there are zero relevant BIOS gaps.

Inventories are metadata evidence, not verified game counts. Host-specific JSON
under `.work` remains untracked.

## Current compatibility matrix

The historical 0.1 matrix covers 45 ROM-relevant systems:

- `READY`: 39
- `UNTESTED`: 1
- `EMBERCADE_PORT_MISSING`: 0
- `EMULATOR_MISSING`: 4
- `UNSUPPORTED`: 1
- `CORE_MISSING`, `BIOS_MISSING`, `AMBIGUOUS`: 0 each

See [COMPATIBILITY_0_1.md](COMPATIBILITY_0_1.md) for the per-system evidence.
Targeted 1.0 additions and the separate complete pinned catalog are tracked in
[COMPATIBILITY_1_0.md](COMPATIBILITY_1_0.md). The older whole-collection matrix
above remains historical evidence, not a fresh inventory.

## Complete 1.0 system preparation

The authoritative catalog is generated by Batocera's own registry/builders
from every emulator/core definition at the existing pin: **257 unique IDs**,
not merely the captured 253-system reference or the current ROM collection.
Batocera defaults and user `batocera.conf` still select emulator/core; the
Embercade allowlist is a desktop capability boundary, not another selection
database. Classical generic Libretro routes reuse the central core resolver,
Configgen, controller/exit handling, staged shaders and optional decoration
fallback. No emulator/core/BIOS/game is downloaded or installed by preparation.

The pre-PS4 preparation snapshot distinguishes **40 READY, 51 PREPARED,
92 BLOCKED and 74 UNSUPPORTED**. Forty historical game-E2E systems stay READY;
50 newly prepared classical routes and the existing Wii route have structural
evidence only. The complete ID/core/extension/BIOS/reason tables are in
`COMPATIBILITY_1_0.md`; host-specific machine-readable output is produced by
`embercade system-coverage --output FILE`. Host counts may differ according to
their actual cores, binaries and firmware, even with an identical payload.

PREPARED requires actual ELF Libretro exports, resolved shared libraries and
a successful real pinned-generator dry run. Synthetic fixtures exercise
config/command generation only, never an emulator process. Optional `.info`
companions are descriptive diagnostics, not a runtime/Doctor prerequisite:
the existing exact-core `RetroArch -L` path does not require them. Batocera's
pinned catalog supplies system/core mappings and extensions. Missing,
incomplete or unreadable `.info` never blocks READY or PREPARED; missing core
libraries, unverified ABI and unresolved dependencies still do.

The MainRig's 291 `.info` files are unchanged files of the signature-validated
Arch `extra` package `libretro-core-info 1.22.2-1`, installed as a dependency of
Nestopia on 2026-09-24 (package database, integrity check and transaction log).
They are not a manual Embercade import or setup residue. The second host has
no corresponding metadata package. The production Libretro info directory is
empty on both hosts, and these host files are not needed by Embercade's proven
direct launches. No new metadata pack is copied or bundled solely to equalize
host package inventories; both receive the same Embercade payload and policy.
Missing BIOS can remain an explicit PREPARED setup requirement. NONE_DECLARED
means the pinned checker has no matching requirement, not a universal claim
that every game needs no firmware. Specialist peripherals and real game
compatibility remain unproven for PREPARED systems.

MAME/MESS default paths need isolated command/data/work handling; X68000/px68k
needs isolation of writable `keropi` BIOS-side configuration. These stay BLOCKED
and are deliberately deferred, without touching the proven `mame078plus` route.
Unintegrated standalones stay BLOCKED even if a binary is present. Ports,
apps/media/fantasy targets and modern community-hardware additions are not
automatically enabled; the already accepted Mr. Boom/PrBoom routes are retained.

Production ships `systems-catalog.xml`, pinned BIOS metadata and portable
structural evidence beside the customized active `es_systems.cfg`.
**Do not name the audit catalog `es_systems_*.cfg`**: ES automatically merges
those files, overriding Embercade commands with appliance commands. The live
regression identified that precise cause of an initial Xenia launch failure;
the audit filename is now outside ES's additional-config glob. Staging rejects
stale structural source digests; build/test intermediates remain in `.work`,
but installed launches and Doctor use installation-local resources only.

New system definitions are present even without ROMs. Empty/companion-only
systems remain hidden; matching content added later is detected without code
changes. Doctor reports missing games as information, never an installation
failure. Coverage diagnostics distinguish missing runtime, missing route,
missing assets and missing BIOS. ROM content, BIOS and provider/core sources
remain protected. Repository privacy, paused bezel licensing and the public
release blocker are unchanged; no working assets are stripped.

Acceptance at this preparation milestone: **484 tests pass**, including real
pinned-generator structural checks for all 50 new Libretro routes and Wii,
optional/missing/malformed/unreadable core-info diagnostics, discovery and
native splash deadlines. Runtime, frontend-library and shader smokes,
Production Stage/offline payload and installed Doctor pass. Both reference
hosts report the same 40/51/92/74 coverage; comparison of every system's
status/reason/effective emulator/core/BIOS/extensions/proof also matches.

MainRig real regression acceptance covers NES/Libretro, 3DO, PCSX2 and Xenia:
image, audio, controller, configured exit and return to the existing frontend.
The corresponding real interactive Steam/Gamescope tests pass on the second
host, including Quit Embercade back to Steam and no remaining frontend/game
or Embercade launch service. The checked normal host emulator profile trees
on the second host are unchanged. Normal updates preserve inventoried user
config, themes, saves/states, managed resources, Steam identity and external
content references; gameplay-generated changes are inventoried separately
before the final update. Per-file payload verification and matching manifests
establish installation parity, not identical user/host package inventories.

## Wii native controllers (1.0)

The existing isolated Dolphin route now prefers a responding real Wiimote
under the existing `emulatedwiimotes` Auto/unset setting. On retains the
gamepad emulation generator; Off retains Real with native continuous scanning.
Existing user overrides are preserved, not rewritten during update. No second
input backend/settings database, Bluetooth passthrough, host pairing, udev
rule or normal Dolphin-profile change is introduced. GameCube mapping remains
unchanged. Production/dev namespaces expose only permitted Wii generic HID
character nodes discovered dynamically through sysfs; structural dry runs and
Doctor do not probe live hardware. Missing hardware is informational.

Embercade's scoped `SDL_JOYSTICK_HIDAPI_WII=0` policy keeps receiver HID slots
out of SDL while Dolphin handles them natively. A live PCSX2/SDL3 regression
enumerated four Wii slots ahead of the ordinary gamepad, shifting it to SDL-4
and invalidating SDL-0 bindings. The hint applies to production/dev sessions,
launch plans and temporary discovery (caller environment restored); other
SDL drivers and normal host profiles are not changed.
The corrected PCSX2 run recognizes the Xbox pad as SDL-0; user-confirmed
control/Guide+Start return and another real Wii control/pointer/exit test pass.

MainRig user acceptance in **Super Mario Galaxy** confirms image/audio,
RVL-003 buttons, Nunchuk stick/C/Z, IR pointer, motion and rumble through a
Mayflash DolphinBar in mode 4 (`057e:0306`), synchronized as player 1.
Wireless disconnect/reconnect succeeds within Dolphin and within the same
frontend before relaunch. Guide+Start on the normal gamepad exits cleanly;
the same frontend remains. GameCube **F-Zero GX** regression is confirmed.
This real evidence permits Wii READY for the tested standalone route,
not universal peripheral support.

The same hardware is independently accepted in **Super Mario Galaxy** on the
WohnzimmerPC, started from the real interactive Steam/Gamescope session:
image/audio, real buttons, Nunchuk stick/C/Z, IR, motion, rumble, wireless
reconnect inside Dolphin/the frontend, relaunch and Select+Start return to the
same frontend. Native Source 2, continuous scanning, a receiver HID handle and
launcher status 0 are verified. The DolphinBar/Nunchuk route is READY on both
hosts; other peripherals/transports do not inherit that acceptance.

Second-host Xenia/gamepad exit regression passes on repeat: Select+Start
closes only Xenia and preserves the frontend. An earlier run ended the whole
frontend/production wrapper with SIGINT just after launcher status 0; the
signal sender/cause is unknown, not a proved Wii regression or repaired bug.
The owner stopped investigation after the successful repeat and will observe
normal use. Keep this unresolved intermittent observation explicit.

MotionPlus is **UNVALIDATED**: the tested remote has only Nunchuk attached.
Direct Bluetooth, Bluetooth passthrough, multiple remotes and Balance Board
remain unvalidated. Dolphin owns reconnect during Real-mode gameplay; an
emulated game does not change source mid-game. USB receiver unplug/replug or
attachment after frontend start requires restarting the frontend to expose
new HID nodes. See [WII_CONTROLLERS.md](WII_CONTROLLERS.md) for the exact policy.

The Dolphin Libretro alternative is not an implemented desktop route:
MainRig's core is present, but selecting it for GameCube reaches Configgen
without the central exact-core handoff and aborts with `MissingCore` before
RetroArch starts. Standalone Dolphin remains the validated choice. This is
a diagnosed separate port, not repaired or substituted in this sprint.

The current complete catalog snapshot is **42 READY / 50 PREPARED / 91 BLOCKED /
74 UNSUPPORTED**, 257 IDs. Wii's E2E ledger entry is explicitly scoped to the
tested DolphinBar/Nunchuk route on the two reference hosts.
The full automated suite passes **516 tests**, including pinned real/fallback/
Nunchuk/GameCube generation, dynamic HID identity/access/reconnect, no live
hardware probe in structural tests, scoped SDL policy/restoration, source and
host-profile isolation, optional hardware Doctor and production device mounts.
Runtime, frontend-library and shader smokes (14 presets/142 dependency files),
Production Stage/offline payload, staged and installed Doctor pass.
MainRig also confirms the Auto/gamepad Wii fallback with the remote off,
NES/Libretro, 3DO, PCSX2, Xenia and shadPS4 launch/exit regressions, and normal
Quit Embercade to the desktop. The warm native splash is measured at 2,750 ms.
Normal updates preserve inventoried user config, saves/states, themes, managed
cores/providers/assets and Steam state; normal Dolphin profiles remain
unchanged on both hosts. The second host uses the verified offline payload and
per-file/manifest parity check, not a required Git checkout. Second-host Wii
hardware acceptance comes separately from its real interactive gameplay test.

## Special-controller structural preparation (1.0)

Lightguns, wheels and trackballs are **PREPARED / UNVALIDATED**, not READY:
no matching physical hardware has been tested. The existing production input
namespace exposes live `/dev/input` plus read-only udev/sysfs metadata.
Embercade has unhidden pinned Batocera `use_guns`, `lightgun_map`, `use_wheels`
and PCSX2 wheel-type choices; there is no second input database or host udev
rule. The existing RetroArch `udev` mouse/gun driver remains separate from
the SDL2 ordinary-gamepad driver. Upstream Configgen provides gun/mouse core
options, PCSX2 GunCon2 and wheel steering/pedal routes, and Dolphin evdev gun/
wheel routes. Wheel discovery depends on a mapped SDL/ES controller and udev
`ID_INPUT_WHEEL`, while gun discovery requires udev `ID_INPUT_GUN` and mouse
tags. Trackballs use the relative-pointer/mouse route; an ordinary mouse is
never presented as a confirmed trackball.

The desktop wheel patch skips Batocera's physical sysfs range write and
virtual-wheel calibrator, preserving raw steering/pedal axes without host-wide
mutation. Its range/deadzone controls remain hidden. Force feedback,
calibration, pointer focus, device-model compatibility and live gameplay
hotplug remain unvalidated. Optional Doctor udev-tag counts never fail merely
because hardware is absent and never promote detected hardware to READY.
MAME/MESS keeps its independent BLOCKED appliance path status. See
[SPECIAL_CONTROLLERS.md](SPECIAL_CONTROLLERS.md) and the scoped compatibility
ledger for the exact routes and remaining physical-device tests.
The 535-test unit suite, runtime/frontend-library/shader smokes, Production
Stage and installed Doctor passed for this structural preparation; none is a
substitute for physical-device gameplay acceptance.

## Startup loading polish

The existing native, theme-independent Embercade splash now stays visible for
at least **2,750 ms from its first presented frame**. Actual frontend loading
consumes this same interval: a longer load gets no additional fixed delay.
The already presented frame stays in place until the normal frontend handoff;
there is no extra splash process, blank swap or new startup path. A fade is
deliberately not added to avoid another rendering/lifecycle mechanism.
Startup error/quit bypasses the minimum and cleans up normally. SDL tick
wraparound, short/long loads and failure cleanup are covered by native timing
tests. One non-secret startup diagnostic records the measured visible time.
Product branding remains `EMBERCADE 0.5`; theme changes do not replace it.
Native diagnostics measure **2,750 ms on both reference hosts**. MainRig and
the real Steam/Gamescope session visibly confirm the clean transition without
black intermission, desktop flash or duplicate splash. Longer-load behavior
and failure cleanup are structural/native timing tests, not invented live
measurements of a deliberately slowed host.

## Proven READY systems

The E2E ledger contains 41 systems: the 39 historical 0.1 routes below plus
the 1.0 3DO and PS4 additions documented separately in `COMPATIBILITY_1_0.md`.
PS4 gameplay acceptance is host-specific; the ledger does not establish
gameplay on a host lacking a configured, verified provider.

- 3DO
- Atari 2600, Atari 5200, Atari 7800
- Game Gear, Game Boy, Game Boy Color, Game Boy Advance
- Master System, Mega Drive, Sega 32X, SNES
- NES, Mr. Boom, Neo Geo, Neo Geo Pocket Color, PC Engine, PrBoom
- Nintendo 64, Atari Jaguar
- Commodore 64, Nintendo DS, Nintendo 3DS
- PlayStation, PlayStation Portable
- Amiga 1200, Amiga CD32, Dreamcast, Mega CD, Neo Geo CD, PC Engine CD, Saturn
- MS-DOS, MAME/Arcade
- GameCube, PlayStation 2, PlayStation 3, PlayStation 4, Xbox, Wii U, Xbox 360

`READY` means a user-confirmed real launch, working input/audio where applicable,
normal emulator exit and return to the same frontend session. It must never be
inferred merely from a successful dry run.

## Proven launch paths

### Generic RetroArch / Libretro

The 1.0 3DO addition enables the pinned `3do` / `libretro` / `opera` route in
the existing catalog and generic launcher. Its `.iso .chd .cue` extensions
already exclude companion BIN files; no new disc filter or launcher framework
is introduced. Doctor, launch validation and dry-run checks share a read-only
one-of BIOS validator based on the existing inventory evaluator. The user's
BIOS must have an exact upstream filename/hash directly in the configured
BIOS root; files are never copied or renamed. Existing core resolution,
controller mapping/exit presets, curated shader staging and console-overlay
generation are reused. The full suite passes 459 tests and both explicit CUE
dry runs are clean. MainRig's user-confirmed two-game acceptance includes
image, sound, input, `consoles`, correct proportions, `crt-easymode`, Guide+Start
and return to the same frontend process, followed by normal Quit Embercade.
Both launcher runs exit 0, and no emulator/frontend remains. The real
interactive Steam/Gamescope second-host CUE acceptance also passes image,
sound, input, staged shader, console bezel/proportions and Select+Start;
its launcher exits 0 and returns to the same frontend, followed by normal
Quit Embercade. This permits adding 3DO to the READY ledger. Normal updates
preserve inventoried user state and host profiles; both final installations
are verified against the same offline payload manifest and file hashes.
Detailed contracts, pinned sources and limitations are in the 1.0 compatibility
document. The visible label remains `EMBERCADE 0.5`; 0.5 is still frozen and
this system addition belongs to 1.0 development.

Batocera selects the logical Libretro core; Embercade resolves the host library
and lets Configgen produce isolated RetroArch configuration. The generic route
now covers cartridge/simple content, the proven disc systems, PUAE/A1200,
VICE x64/C64, DOSBox Pure, MAME 2003 Plus and melonDS DS/NDS. ROM arguments
remain separate process arguments, including paths with spaces.

For A1200, the pinned Batocera PUAE settings select the A1200 model, the
read-only `amiga` Kickstart directory and WHDLoad/LHA handling. Embercade keeps
Configgen's central core-options file authoritative, preventing stale isolated
per-core `.opt` files from suppressing mappings such as Select opening PUAE's
virtual keyboard. DOSBox Pure receives the archive as content and keeps its
mutable state below Embercade XDG. Batocera's `mame078plus` identity resolves
through the central alias table to the host `mame2003_plus` core; ROM-set
compatibility remains a content property rather than a launcher workaround.

The C64 route uses Batocera's `vice_x64` core configuration. Its tested T64
content boots with PAL auto-detection, Player 1 input reaches VICE's joystick
port and Select opens the virtual keyboard. The Nintendo DS route uses the
`melondsds` identity with a top/bottom layout, software rendering and joystick
touch mode.

PSP and Nintendo 3DS retain Batocera's standalone providers as catalog
defaults, while the proven desktop overrides use `libretro/ppsspp` and
`libretro/azahar`. PPSSPP reads the user-provided official assets through an
Embercade-owned `system_directory/PPSSPP` link; the source is mounted read-only
and is not copied into the normal RetroArch profile. Azahar uses the existing
dual-screen options and the tested default layout. Both routes have verified
audio, Xbox-controller input, correctly proportioned console bezels,
Guide+Start exit, isolated saves and return to the same frontend session.
Installed `citra` and `citra2018` cores remain available alternatives but were
not needed for the successful 3DS E2E test.

The installed PSP path now discovers user-provided PPSSPP assets in Embercade's
XDG data `resources/PPSSPP` directory, with config/environment overrides.
Production mounts the selected source read-only at a stable sandbox location;
Doctor and launch share the same validation. This closes the gap where the
development profile supplied an asset path but the installed profile and
Production namespace did not. The assets remain separate user resources,
preserved during normal reinstall, rather than emulator or firmware payload.
User-local updates on both tested hosts passed Doctor and PSP generation inside
their actual Production sandbox, including a read-only mount check and the
final PPSSPP RetroArch command. Later visible PPSSPP play was confirmed on the
second host, and a subsequent development-host Production log records a PSP
launch through the installed core and isolated configuration. These observations
are separate from the asset-mount and command-generation checks.

The production feature catalogue overlays Batocera 44.dev's pinned 3DS region
and language definitions when the older byte-pinned base catalogue does not
contain them. Production system metadata is aligned with the emulator/core
pairs selected by Embercade's `batocera.conf`, so EmulationStation can resolve
the `libretro/azahar` feature set. The normal advanced-options flow writes
`3ds.3ds_system_language`; Configgen translates that value to Azahar's existing
`citra_language_value` core option. No separate Embercade language setting is
introduced. Azahar Libretro currently applies that language setting only while
its region option remains `Auto`; forcing a fixed region bypasses the core's
language-application path. The core also fails to expose the selected language
reliably through the persisted CFG block read by commercial titles. Embercade
therefore synchronizes only that one validated byte in its private Azahar NAND
copy before and after a real 3DS launch; the write is atomic and never targets
a normal emulator profile or game save.

The production installation on the second host was validated with a European
multi-language 3DS title. With region left at `Auto` and language set to
`German` in EmulationStation, `batocera.conf` contained
`3ds.3ds_system_language=German`, the generated core options contained
`citra_language_value = "German"`, and the running game displayed German text.
This confirms the complete UI-to-game language path, including the private CFG
block synchronization, outside the development checkout.

Nintendo 64 keeps Batocera's standalone `mupen64plus/glide64mk2` catalog
default visible in the matrix, while the proven desktop override uses the
logical `mupen64plus-next` Libretro core. The resolver maps Batocera's dashed
name to the installed upstream `mupen64plus_next_libretro.so`. The accepted
E2E path used GLCore, GLideN64 RDP, HLE RSP, the dynamic recompiler and a
Memory Pak. Atari Jaguar likewise retains Batocera's `bigpemu` catalog default
but uses the installed `virtualjaguar_libretro.so` desktop route. Both systems
have verified audio, Xbox-controller input, console bezels, Guide+Start exit,
isolated saves and return to the same frontend session.

### Dolphin / GameCube

The modern `batocera-launch-dolphin` plugin uses the resolved `dolphin-emu`
binary. Dolphin configuration, saves and controller data are isolated. The
desktop route skips appliance display/power hooks and uses Dolphin's native
mapping for the centrally selected exit chord.

### PCSX2 / PlayStation 2

The modern `batocera_launch_pcsx2:Pcsx2` plugin uses resolved `pcsx2-qt` and
reads configured BIOS images and host resources in place. BIOS images appear
in a private writable PCSX2 BIOS workspace through read-only source symlinks;
mutable NVM/MEC companions are seeded or created only below Embercade. Config,
memory cards, states, cache and logs are likewise isolated. This avoids PCSX2's
MEC permission failure while keeping the external BIOS pack unchanged.
The central exit preset maps to PCSX2's native shutdown hotkey.

### RPCS3 / PlayStation 3

The modern RPCS3 plugin resolves the host executable and uses an isolated RPCS3
profile. Existing firmware is copied once into that writable isolated profile;
the source profile remains read-only. Network compatibility lookup, global exit
helpers, OverlayFS requirements and system-wide sysctl mutation are disabled in
desktop mode. The launch-scoped exit bridge closes the emulator normally.

### Xemu / Xbox

The built-in Batocera Xemu generator uses the resolved host executable. Read-only
flash/MCPX/HDD sources seed Embercade-owned writable copies; native Xemu
generates an absent EEPROM at the explicit isolated save path. Existing
EEPROM/HDD and optional legacy EEPROM seeds remain preserved; screenshots,
configuration and mutable disks stay isolated. The launch-scoped exit bridge
implements the central exit preset without global `pkill` or `kill -9` behavior.

On the second host, the central BIOS pack supplied the conventional flash and
MCPX filenames but no pre-existing normal Xemu profile. Source resolution now
falls back to the configured read-only BIOS root for the conventional
filenames while retaining explicit environment overrides. In that historical
acceptance, user-approved EEPROM and HDD seeds were copied into Embercade's
isolated save tree; EEPROM seeding is now optional. Configgen then
generated the host-specific `xemu.toml`. The tested Xbox title launched
fullscreen with the correct content and controller, exited through Select+Start
with launcher status 0, and returned to the same frontend process.

### Cemu Libretro / Wii U

The Batocera catalog still identifies Cemu as the default provider. The proven
desktop override uses the separately installed `cemu_libretro.so` through the
generic Libretro route. Cemu's MLC tree and saves are generated below
Embercade's isolated save root; the normal RetroArch profile and source game
directory remain read-only. The tested Wii U title loaded with audio and Xbox
controller input, exited with Guide+Start and returned to the same frontend
process. The accepted host run selected RetroArch GLCore/OpenGL 4.6 despite the
Batocera Vulkan preference; documentation describes that observed renderer
rather than claiming Vulkan.

### Xenia Edge / Xbox 360

The modern `batocera_launch_xenia_edge:XeniaEdge` plugin uses a configured,
user-supplied Xenia Edge AppImage. The AppImage and ISO stay read-only and are
passed as distinct process arguments. Configuration, content/saves, shader and
module caches, scratch data, logs, HOME and TMPDIR all resolve below Embercade's
isolated XDG tree. The tested Xbox 360 title loaded through Vulkan with working audio
and Xbox-controller input; Guide+Start closed Xenia normally, batocera-launch
returned status 0 and the same frontend process resumed.

The development frontend runs inside Bubblewrap, where an AppImage cannot make
its FUSE mount. A small generic runner therefore delegates only this external
provider to a synchronous transient user service outside the mount namespace.
It forwards the scoped display/audio/controller environment, preserves process
wait and exit status, and removes only AppImage mounts newly created inside the
private Embercade TMPDIR. A normal unsandboxed desktop launch needs no such
namespace bridge.

The installed production sandbox additionally translates only a fixed
whitelist of internal Embercade config/data/cache/state/runtime, ROM and BIOS
paths back to their explicit host roots before delegating the provider. This
keeps `systemd-run` from receiving namespace-only `/userdata` paths while
leaving arbitrary provider arguments untouched.

Second-host validation exposed that the Linux AppImage searches for
`Xenia/xenia-edge.config.toml` below `XDG_DATA_HOME`, while configgen writes it
below Embercade's emulator-config root. The provider now points its XDG data
lookup at that generated directory and configgen writes host-visible Embercade
storage, save and cache roots into the file. The verified retest loaded that
exact file with `fullscreen = true`, opened as a borderless 1920x1080 KWin
fullscreen window, exited through Select+Start with status 0, and returned to
the same frontend process.

### shadPS4 / PlayStation 4 (1.0)

PS4 is an explicitly approved older-platform addition, not permission to add
PS5/current platforms. The pinned Batocera `ps4` system and built-in
`Shadps4` generator retain `.ps4 .zar`; a `.ps4` game directory must contain
a readable `eboot.bin`. The existing managed AppImage importer, executable
resolver, CLI/installer, GTK/SDL first-run wizard, Doctor and launch-scoped
host runner are reused. No parallel provider or controller framework, binary
download/link, PATH fallback or bundled emulator/GPU driver is introduced.

Identity uses bounded ELF/type-2 AppImage/SquashFS inspection and the embedded
`net.shadps4.shadPS4.desktop` product/Exec/window-class fields, not the source
filename. A user-selected source is copied to the XDG data
`providers/shadps4/shadps4.AppImage` location; SHA-256 identifies equal copies.
Different candidates/conflicting managed content are never silently selected
or overwritten. Source bytes/permissions remain unchanged. Doctor separates
managed/external, missing, invalid, unverified, ambiguous, unselected and
missing-runtime-dependency states. Existing host inspection tools inspect the
embedded ELF with the shared dependency checker; host-only closure is
conservative and does not treat an arbitrary filename as a working runtime.

The optional PlayStation 4 wizard page reuses CLI setup and the existing
controller-friendly browser. Back/forward retains the unsubmitted selection;
an existing provider is shown as already configured and an empty new source
field does not remove it. Other systems/setup continue without shadPS4.
`setup --shadps4-from FILE_OR_FOLDER` uses the same atomic importer.

Direct launch uses the resolved AppImage with `-g <eboot.bin> --fullscreen
true`; `-b` is only the emulator's Big Picture browser/configuration action.
The host runner translates the existing fixed namespace path whitelist and
supplies Embercade-owned HOME, TMPDIR and XDG roots. The generated
`config/emulators/shadPS4/config.json`, input config, game saves, addons,
shader caches, logs and other mutable state remain outside the AppImage and
normal host shadPS4 profile. Existing rendering/timing choices are preserved
unless an explicit Batocera option changes them; invalid JSON is reported and
kept, not reset. Synthetic generator tests isolate every XDG root and never
boot fixture content or write real user configuration.

MainRig's user-supplied shadPS4 v0.19.0 build
`c7e065d1b415be16c23e260a21f1dd8bbfc4cb57` reaches actual PS4 gameplay with
image, audio and controller input on host RADV/Wayland. The configured
Guide+Start chord returns launcher status 0 to the same frontend PID; the
provider process and AppImage mount are gone, followed by normal frontend
quit. Source AppImage, game executable and normal host profile fingerprints
are unchanged. This permits MainRig PS4 **READY**, not universal PS4/title
compatibility. Title-specific fonts, modules, keys, firmware and patches remain
user-supplied requirements; warnings do not imply that those files are bundled.
The known initial invalid GPU index came from an incorrectly isolated test
fixture, not the user's host profile; fixture isolation is now regression-tested.

The WohnzimmerPC received the same user-approved AppImage via SSH and the
same managed importer; its identity/hash/runtime dependencies pass. Actual
Bloodborne gameplay, image, audio and controller input are user-confirmed in
the real interactive Steam/Gamescope session. Select+Start returns status 0 to
the same frontend PID, with no remaining emulator process or AppImage mount.
PS4 is therefore **READY on both reference hosts for this tested build/game**,
not a general claim about arbitrary PS4 titles. The existing Xenia Gamescope
regression and configured Select+Start/return to Steam are also user-confirmed.
The shared Gamescope window policy now includes shadPS4-owned native helper
dialogs using their window PID and the launched process group. Unrelated
dialogs are excluded, and save-migration decisions remain explicitly with
the user. Delegated helpers receive the host-visible private runtime path.
An initial save-migration helper was hidden by Steam; the corrected game
start succeeded without that prompt recurring. Ownership/foreign-dialog
filtering is automated coverage, not a claimed visible repeat of that prompt.
The complete automated suite passes **505 tests**; runtime, frontend-library
and shader smokes pass. Normal update/uninstall preserves managed provider,
config, saves, themes and Steam/scraper state; explicit purge removes only
Embercade-owned copies, never external sources. PRIVATE status, paused bezel
licensing/public-release blocker and retained working assets are unchanged.
Both production installations pass Doctor with the same catalog totals:
41 READY / 51 PREPARED / 91 BLOCKED / 74 UNSUPPORTED. Full installed-payload
hash verification and matching stage manifests pass on both hosts; normal
updates and identical-payload no-ops preserve the inventoried persistent state.

With multiple gamepads, the exact tested shadPS4 v0.19.0 source
(`c7e065d1b415be16c23e260a21f1dd8bbfc4cb57`) enumerates
`SDL_GetGamepads()` and assigns the first unclaimed device to the first free
player slot, retaining occupied slots across reconnect. Its declared
`default_controller_id` setting is not read by that gameplay assignment path.
Embercade has no supported per-launch shadPS4 selector that guarantees its
frontend Player 1 device, so this is a known upstream-limited multi-controller
behavior. No fragile SDL reordering, global input change or host-profile edit
is introduced. Single-controller Bloodborne acceptance remains valid; a
deterministic two-pad shadPS4 P1 mapping is not claimed.
The shared runner's Xenia regression also passes after the Gamescope helper
fix, including Select+Start and normal Quit Embercade back to Steam.
See [PRODUCTION.md](PRODUCTION.md#managed-shadps4-and-ps4) for the path contract.

## Important desktop overrides

### PlayStation

Batocera's pinned default is `pcsx_rearmed`. It loaded the tested CHD and BIOS
but failed inside recompiled code on this desktop. SwanStation ran but showed
game-visible graphics corruption that persisted across Vulkan, disabled PGXP
and its software renderer.

The proven, data-driven desktop route is:

```text
logical core: mednafen_psx
host core:    mednafen_psx_hw_libretro.so
renderer:     Vulkan
```

This remains a `batocera.conf`/resolver choice, not a system branch in the
launcher.

### NES

The accepted NES route uses Nestopia through a desktop `batocera.conf` choice;
the pinned Batocera catalog default `fceumm` remains visible in the matrix.

### Nintendo DS

Batocera's pinned default is `melonds`. The installed host library requests an
executable stack and the current CachyOS loader rejects it before core startup.
The proven data-driven desktop override is Batocera's `melondsds` identity and
the installed `melondsds_libretro.so`; no core was patched, copied or bundled.

The central BIOS root remained read-only. This melonDS DS build treats its
external firmware as optional and looked for a private `melonDS DS`
subdirectory, whereas the inventoried pack exposes the relevant files at the
BIOS root. The successful E2E test therefore used the core's fallback firmware.
That path-layout mismatch remains recorded and must not be described as loaded
external firmware.

### RPCS3 controller naming

RPCS3's SDL handler needs the live SDL name. For the MVP Xbox 360 device that is
`Xbox 360 Controller`; its kernel/evdev name is `Microsoft X-Box 360 pad`.
Other generators still receive the kernel name. A global rename would regress
one of these paths.

### Amiga CD32 firmware path

Patch `0016-embercade-amiga-bios-path.patch` preserves Batocera's required
`amiga` firmware subdirectory while resolving it under the configurable,
read-only `BIOS_ROOT`, not `/userdata/bios`.

### Desktop lifecycle and paths

The patch series redirects Batocera paths into Embercade, resolves host
executables, disables appliance-only display/power/special-hardware hooks, fixes
quoted RetroArch paths containing spaces, and scales bezel viewports to the
actual desktop pixel size. These patches apply only to disposable pinned source
snapshots.

## Proven disc support

Real E2E tests cover CHD, CDI and CUE/BIN multitrack content across several
systems. CUE-relative track references are preserved by exposing their original
read-only collection directory. This is not a claim that every theoretical
disc format works. The current inventory contains no real `.m3u` playlist, so
multi-disc playlist behavior has not been validated.

## Bezel and shader support

Batocera EmulationStation's feature UI remains the selector. Its values flow
through `batocera.conf` to Configgen. `Decoration = consoles` resolves static
read-only resources, generates `overlay.cfg` and calculates the RetroArch
viewport. The generic bezel path was visually proven at the development display
size of 2560x1440; that resolution is test evidence, not a product hardcode or
requirement.

Shaders now resolve from the complete official Libretro `slang-shaders` source
tree pinned in `runtime/shaders.lock`, not from the former captured Batocera
shader copy and never from a host RetroArch installation. A separately tracked
catalog generates the small menu-facing set: NewPixie, CRT EasyMode, CRT
Lottes, CRT Lottes Fast, ZFast CRT, Mega Bezel, Sharp Bilinear, LCD Grid, PSP
Color, GBA Color, GBC Color, Advanced AA, Bevel and Simpletex. `None` and the
existing `Auto` behavior remain available; no visual preset is forced globally.
Every generated mapping and its recursively referenced preset, shader, include
and texture files are checked before staging. The production set targets the
Vulkan/GLCore Slang path used by the supported hosts; the official GLSL tree is
recorded as an audited reference but is not staged. Visible Production-Stage
tests confirmed NewPixie and CRT EasyMode on SNES, LCD Grid on Game Boy, and
Mega Bezel on Nintendo 64. All four returned cleanly to the same frontend
session; Mega Bezel's `noBezel` mapping also disabled the external decoration
overlay as intended. Mega Bezel remains an optional, GPU-heavier style rather
than a default.

The pinned archive is `libretro/slang-shaders` at
`84bcd19a854348c0e6a1d3db814a76f11fb6f011`, verified by its recorded
SHA-256. Preparation stages that tree and the generated menu mappings in the
Embercade payload; the host's RetroArch shader collection is not a runtime
dependency. The selected presets' transitive files are validated before stage
creation.

### Standalone decorations: PCSX2, Xemu, GameCube and Wii

PCSX2, Xemu and standalone Dolphin's GameCube/Wii routes use one optional desktop decoration supervisor in the
regular launch path. Selection remains pinned Batocera `SystemConfig` plus
`Emulator.bezel_files`, including game overrides and `none`. No static assets,
other emulator routes, firmware or saves are changed.
The helper protects the game rectangle, follows only the concrete launched
emulator and is reaped before ES resumes. Missing resources or a failed helper
do not change the emulator's launch/exit result.

Hyprland uses a native input-transparent layer tied to focus/workspace events.
Gamescope is a required target and has its own external-overlay-plane backend;
its physical DRM output size is separate from the Xwayland game resolution.
The latter distinction was exposed by a 1080p game on the second host's 4K TV.
MainRig's PCSX2/Xemu Hyprland prototypes were visually accepted, including
workspace binding and cleanup. On 2026-09-27 both integrated production routes
were visually accepted on the second host under Gamescope, including fresh
PCSX2 startup and Xemu's SDL surface without an EWMH fullscreen atom. The
external overlay uses the physical 4K surface while the game remains at its
logical 1080p resolution. The final Xemu run returned launcher status 0;
emulator and decoration helper were gone while the same frontend remained.
The MainRig's later missing Xemu frame was traced to its preserved `Auto`
aspect setting: the helper reserves a possible 16:9 game frame and cannot
draw safe side art on a 16:9 display. The second host had explicit 4x3.
Choosing 4:3 on the MainRig restored the existing frame without changing the
windowing code or decoration asset. The Dolphin extension uses the same helper,
existing GameCube/Wii console art and Batocera's generated aspect/TV mode;
wide/unknown modes fail closed. It neither moves Dolphin nor changes Wii
pointer coordinates. The original PCSX2/Xemu milestone remains complete;
this is not a generic KDE or all-emulator bezel support claim. See
[STANDALONE_DECORATIONS.md](STANDALONE_DECORATIONS.md) for geometry, dependencies,
session limitations and acceptance details.

The GameCube/Wii extension and current Xemu 4:3 route now have visible
production acceptance on both reference hosts. MainRig/Hyprland confirms
GameCube and Wii frames, Xemu's restored frame, gamepad +/−/Home in emulated
Wii mode, and Player-1 return. WohnzimmerPC's real Steam/Gamescope session
confirms Xemu, GameCube and Wii frames, native DolphinBar/Nunchuk/IR pointer,
gamepad Select+Start and Quit Embercade back to Steam. GameCube on MainRig
also passes the translated Bluetooth-Player-1 exit chord. Missing art,
`Decoration=None` and unsupported aspect/compositor conditions remain
non-blocking. The full 542-test suite, runtime/frontend-library/shader smokes,
Production Stage, staged/installed Doctors and diff check pass. Both normal
updates preserved their inventoried XDG user-state file hashes; the installed
Stage manifests are byte-identical
(`cea51a9be72ada848532d186aabec9273c35a83ffd8b617845a5abb0ecd610a0`).

## Theme Library and branding boundary

Production now creates the persistent XDG data `themes/` directory and the
frontend-owned `themes/.tmp/` download/extraction workspace before ES starts.
The existing `/userdata/themes` link and writable data bind remain the path
contract; the missing link target, not a read-only data mount, caused the
recorded Theme Library I/O errors. The upstream frontend still owns catalogue,
previews, ZIP download/extraction, installation and activation. Carbon remains
an immutable installed default. Downloaded themes and the active `ThemeSet`
in isolated ES settings survive normal reinstall; no host ES profile is used.

The desktop-policy patch additionally prevents theme/builtin splash XML from
replacing the fullscreen Embercade startup/reload image, layout or extras.
Normal game-art panels and menu/system/gamelist theming retain upstream
behavior. Product splash, Desktop/Steam icon and artwork resources remain
separate from writable themes. No downloaded theme is rewritten or bundled.
The Theme Library milestone passed 350 tests, including an actual Bubblewrap
writable-theme/read-only-branding check and theme/selection reinstall coverage.
Runtime, frontend-library and shader smokes, Production Stage and staged/
installed MainRig Doctor pass. MainRig Hyprland acceptance confirms the real
AI-Hypertocera download/install, Carbon round trip, controller navigation,
Xemu launch/return and complete restart with the unchanged Embercade splash.
Theme selection persists across restart and Desktop/Steam artwork hashes stay
unchanged. Normal offline reinstall preserves all inventoried theme/config/
save/provider data and the active theme, with another visible splash/theme
restart accepted afterward.

Second-host acceptance from the real Steam/Gamescope session also passes:
AI-Hypertocera was downloaded by the frontend, activated and switched through
Carbon; controller navigation, Gambatte/Game Boy with the pinned LCD shader,
emulator exit/return and normal Quit Embercade back to Steam work. Complete
Steam restarts retain the selected theme and the same Embercade splash.
Normal offline reinstall preserves the inventoried theme/config/save/provider
data and active selection; a subsequent user-confirmed Steam start loads the
theme without another download. Both reference hosts use the same verified
offline payload, not incremental runtime patches. Theme Library acceptance
is complete for these two tested environments, not every upstream theme or
distribution. Network/catalogue availability, third-party theme compatibility
and licensing remain external constraints. This does not resolve the existing
PRIVATE/public-release asset licensing blocker or authorize asset stripping.
See [PRODUCTION.md](PRODUCTION.md#theme-library-and-persistent-user-themes).

## ScreenScraper (1.0 integration accepted on both hosts)

The detailed two-host acceptance below is historical. For the current
production-build design and acceptance, see [SCREENSCRAPER.md](SCREENSCRAPER.md#acceptance-and-preservation).

The existing pinned Batocera ES ScreenScraper provider is enabled by a
credential-free build flag rather than embedded application credentials. A
native integration helper reads an owner-only local XDG secret file; developer,
developer-debug and personal UI-account credentials remain distinct. Normal
requests never transmit the debug password. Credentials are not Stage inputs;
HTTPS verification, safe service errors and disabled frontend process dumps
protect the normal request/log path. Doctor distinguishes configured access
from authentication; no live authentication or scrape is inferred from a file.

For the 1.0 AppImage handoff, the personal account now lives in a distinct
owner-only XDG secret file. The frontend migrates legacy ES account fields only
after the private file has been written, and removes those fields from the XML;
failed migration preserves the old owner-only file. Developer secrets are
read-only in the frontend namespace, personal account secrets remain writable
for its Accounts UI, and neither is staged or transferred. Production/Doctor
reject writable XDG roots inside the immutable prefix or `$APPDIR`. See
[STATE_AND_SECRETS.md](STATE_AND_SECRETS.md). This is a state/security
boundary, not a resolution of public-release licensing.

MainRig and the real WohnzimmerPC Steam/Gamescope session both migrated the
personal account, passed a live single-title ScreenScraper check and a short
emulator start/exit. Their installed Doctors are green, 541 tests and the
runtime/library/shader smokes pass, and normal update plus identical no-op
preserved inventoried state. The same Stage manifest is installed on both;
at that earlier state/secret milestone the AppImage had not yet been built.
Current packaging acceptance is recorded separately below.

Production retains read-only collection/BIOS mounts and grants only original
system gamelist plus four upstream media destinations writable submounts. The
upstream relative-media/XML model, provider UI, system mapping and quota/retry
behavior remain in use, not a second scraper or database. Existing lists,
media and normal update state are preserved. MainRig visibly validates two
individual 3DO games, descriptions/previews/images/video/manuals, controller
launch/exit/return and original-system gamelist with relative, existing media.
Non-purge reinstall and subsequent true no-op update preserve fingerprinted
metadata/media and inventoried user data. Media requests permit HTTPS service
shards inside ScreenScraper's DNS namespace (observed `neoclone.screenscraper.fr`);
certificate verification remains on and credential redirects stay disabled.
The second host visibly validates `Cannon Fodder (Europe).cue` from its real
interactive Steam/Gamescope session: description, previews, images, video,
manual, game launch, controller exit and return all pass. Its non-purge
uninstall/reinstall and true no-op update preserve all 5,544 post-scrape
user-state entries and nine gamelist/media/CUE fingerprints (seven media).
Doctor and all 473 unit/integration tests, runtime/library/shader smokes and
production stage pass. Both reference hosts use the same verified production
payload; host-specific credentials remain outside it. See
[SCREENSCRAPER.md](SCREENSCRAPER.md). Server quotas/access/network and title
matching remain external constraints, not locally repaired guarantees.
The reference hosts share collection metadata; a scrape on one is visible on
the other. Avoid concurrent writes to the same system gamelist: this integration
does not introduce cross-host locking or merging.
PRIVATE/public-release blockers and the paused bezel investigation remain
unchanged.

## Controller state

The original 0.1 test device was one USB Xbox-style SDL controller. The 1.0
multi-controller route now enumerates up to eight live SDL devices at every
launch, applies EmulationStation's existing player preferences and passes each
player's current index, GUID, name, event node and input counts to Batocera's
generators. It adds no parallel input database or host-wide mapping. Earlier
E2E evidence used Guide+Start. The current
desktop policy deliberately uses Select/Back+Start instead because Guide is
reserved by the second host's SteamOS-style desktop. RetroArch and Dolphin use
the controller's Select mapping, PCSX2 uses SDL Back, and the launch-scoped
native bridge reads SDL Back; the Guide button is no longer part of Embercade's
exit chord.

When Embercade is started through Steam/Gamescope, it does not inherit Steam's
virtual-gamepad opt-in or controller ignore lists. Those variables can hide the
physical USB device and expose only a virtual controller without a stable
USB/sysfs identity, causing every emulator route to fail before launch.
Discovery temporarily disables that policy and restores the caller environment;
the production sandbox applies the same isolated SDL policy for the frontend and
each launch.

Indices and `/dev/input/eventXX` nodes are dynamic and must never be stored as
device constants. The frontend harness exposes the live `/dev/input` directory.
The launcher re-enumerates and resolves P1/P2 (and structurally up to P8) at
every game start. RetroArch now uses matching SDL2 slots/mappings and reserves
unique vendor/product identities per player for stable live reconnects. Same-
model controllers have no ambiguous reservation and remain unvalidated for
identity-stable reconnect. Dolphin translates SDL button slots to its evdev
numbering for Bluetooth pads with extra system keys, without changing the
user's GameCube `Rotate Face Buttons` setting.
The same translation now covers Dolphin's Player-1 `Hotkeys.ini` exit chord;
the earlier Bluetooth case had working game controls but mismatched exit
button slots. MainRig's installed Bluetooth-Player-1 GameCube launch generated
matching hotkey/gamepad slots and Guide+Start returned to the same frontend.

Visible MainRig/Hyprland acceptance uses an Xbox 360 USB-receiver pad as P1 and
an Xbox Series Bluetooth pad as P2. Both work in EmulationStation. NES Contra
has independent P1/P2 input with correct D-pads/face buttons; reconnecting
either player during gameplay restores both to their previous figures. P2
cannot trigger the central exit, while P1 exits to the same frontend. GameCube
Mario Kart: Double Dash!! has independent two-player control and matching
physical face-button behavior after the Dolphin correction. Single-player 3DO
and Wii/gamepad start/control/exit regressions also passed. See
[MULTI_CONTROLLER.md](MULTI_CONTROLLER.md) for the exact scope and limits.

The WohnzimmerPC's real Steam/Gamescope session separately validates a generic
USB Xbox-style P1 pad and Xbox Series Bluetooth P2 pad in Contra and GameCube
Mario Kart: Double Dash!!: independent input, correct face buttons, P2 live
reconnect in Contra, P1 exit and return to the same frontend. Its normal offline
update and the MainRig installation have the same verified Stage manifest;
installed Doctor is green on each host. PCSX2 and Xenia single-player
launch/input/exit regressions passed there as well. Identical-model pad
reconnect and standalone in-emulator reconnect remain unvalidated.

Real Wiimote wireless reconnect inside Dolphin is E2E validated on both hosts
as described above; RetroArch's two-player live reconnect is now separately
validated on MainRig. Dolphin, PCSX2, RPCS3 and Xemu retain their native
in-game hotplug behavior, which this test does not certify. Embercade adds no
second input daemon or global remapping layer.

## Remaining `EMBERCADE_PORT_MISSING`

None among the current ROM-relevant systems whose host provider is installed.

## Prepared but `UNTESTED`

The historical 0.1 Wii entry remains UNTESTED in its old inventory snapshot.
The 1.0 standalone route now has real two-host Wiimote/Nunchuk/DolphinBar E2E
acceptance; see the Wii section above. MotionPlus, direct Bluetooth/passthrough
and multiple remotes are not accepted by that evidence.

## Matrix `EMULATOR_MISSING` scope

The matrix reports four absent host providers. They are deferred and outside
the current 0.1 acceptance scope:

- `vita3k` — PlayStation Vita
- `odcommander` — OD-Commander
- `pygame` — Pygame launcher
- `sdlpop` — SDLPoP

This inventory state is not authorization for Embercade to install any of
them, and deferred does not mean that a system or provider is broken.
The required external-provider blocker count for the active 0.1 scope is zero;
this is separate from the four deferred catalog entries above.

## Unsupported

`ports` remains `UNSUPPORTED`. A Batocera ports collection can dispatch
arbitrary per-game shell scripts; finding `/bin/sh` does not provide a safe or
meaningful generic desktop implementation.

## Known issues and constraints

1. In-game controller reconnect remains emulator-native. Two-player RetroArch
   reconnect and real Wiimote wireless reconnect in Dolphin are validated on
   their tested hardware; identical-model pad identity, standalone-gamepad
   reconnect and P3/P4 hardware remain unvalidated.
2. Wii DolphinBar/Nunchuk is accepted on both hosts; MotionPlus, direct Bluetooth,
   passthrough and multi-Wiimote remain unvalidated.
   One second-host Xenia exit also ended the frontend with SIGINT; repeat exit
   passes, cause unknown, further investigation stopped by the owner.
3. Real `.m3u` multi-disc behavior has no collection sample and is untested.
4. Four matrix providers remain absent on this development host. Standalone
   Cemu, Azahar, PPSSPP, Mupen64Plus and BigPEmu are optional alternatives
   because tested Libretro providers satisfy the current desktop routes.
5. The development runtime explicitly uses host CPython 3.14.7 against
   Batocera Common's exact 3.14.5 metadata pin. Static inspection found no
   patch-level dependency, but this is a recorded compatibility mode rather
   than an upstream support claim.
6. The user-local installer is functional development infrastructure and has
   passed isolated fake-HOME/XDG install, setup, dry-launch, uninstall and
   reinstall tests plus an explicitly approved real-profile installation.
   Every currently resolved standalone provider and multiple Libretro cores
   have been visibly exercised from the development-host installation. A
   second CachyOS host has passed offline reinstall, Doctor, KDE frontend
   startup and later Steam/Gamescope Production launches, including PCSX2/Xemu
   bezels. This remains development acceptance rather than a stable public
   installer claim.

## Production staging and launch

Both 0.5 and 1.0 are now feature-frozen. Only packaging/release-finalization
and regression fixes are in scope; proven READY routes remain regression gates.

`scripts/stage-build` materializes a relocatable Linux application tree below
`.work/stage` with `bin/embercade`, the pinned launcher runtime, the pinned
desktop EmulationStation binary, system/feature/controller data, Carbon,
locales, shaders, decorations, defaults and desktop policy. It includes no
ROMs, BIOS, firmware, cores, emulator binaries or external provider binaries.
The byte-pinned static resource bundle, the independently pinned official
Libretro shader source and all upstream source pins are recorded in a
deterministic manifest.

The staged entry point resolves its prefix, reads normal XDG configuration,
validates ROM/BIOS roots and starts the frontend through the production
Bubblewrap path. The prefix is exposed internally at stable `/app`; persistent
user data remains in Embercade XDG directories. `/userdata` exists only as an
internal compatibility view derived from those directories. Runtime startup
does not invoke `dev-run`, access `.work` as an application contract, build
sources, run pip or require network access. See [PRODUCTION.md](PRODUCTION.md).

`embercade doctor` recognizes a staged/installed prefix and checks its runtime,
frontend, resources and writable XDG destinations in addition to existing host
emulator/core/provider diagnostics. Missing first-run collection configuration
is reported as `CONFIGURATION REQUIRED`; missing individual providers are
`OPTIONAL SYSTEM UNAVAILABLE` and a disconnected controller is a warning.

## User-local installation and first run

The verified Production Stage is now the sole installer payload. The
transactional development installer activates it below
`$HOME/.local/lib/embercade`, creates `$HOME/.local/bin/embercade`, installs a
user-local desktop entry and hicolor application icon under the user's XDG data
root, and writes a manifest below Embercade's XDG state root. It never requests
`sudo`, writes to `/usr` or bundles emulator binaries. Reinstall replaces only
verified immutable program files and the hash-verified Embercade icon while
retaining user XDG state.

The 0.5 update-UX implementation uses that same verified Stage/offline-payload
installer. A read-only preview reports current/incoming product and package
labels separately from their Stage-manifest SHA-256 revisions and lists exact
immutable targets versus preserved state. Identical verified payload, desktop
entry and icon are a no-op with no backup, timestamp change or repeated setup.
A changed payload is checked before copying and verified again after activation,
before backups are removed; activation errors restore the previous managed
installation. Normal updates preserve config, saves/states, themes, managed
cores/providers, PPSSPP assets, Steam metadata/artwork and external collection
references. Purge remains separate and explicit. The updated installer does not
download releases or implement version archives/general rollback. The verified
`69da88c` offline payload (`bbfddb109650` Stage-manifest prefix; 9,658 files)
passed changed-update and repeated-identical no-op on MainRig and WohnzimmerPC.
Pre/post metadata inventories of all four Embercade XDG roots, excluding only
the owned install manifest, were identical on both hosts immediately after
update. Steam shortcut/artwork file hashes were also unchanged. Both installed
Doctors passed. The user then confirmed branding, theme, controller, Xenia
play/Select+Start/return and Quit Embercade on MainRig/Hyprland and from the
real interactive WohnzimmerPC Steam/Gamescope session; both launcher traces
ended with status 0 and the second host retained no provider or AppImage mount.
No SSH-only startup is counted as visible acceptance.

**Embercade 0.5 is feature-complete and in feature freeze.** Remaining 0.5
changes are bug/regression fixes only; new product features move to 1.0+.
The first 1.0 development feature is a graphical, controller-friendly first-run
wizard. It runs as a GTK3 window with SDL2 gamepad navigation and delegates
setup, collection validation, optional core/provider import, host bootstrap,
Doctor, Steam registration and frontend start to the existing Embercade CLI.
The wizard creates no parallel configuration format. A valid existing setup is
recognized without rewriting it, and edits or optional actions require an
explicit choice. The installed `embercade wizard` command also permits a
manual recheck; the CLI setup path remains available for headless use. The
central Embercade icon and `EMBERCADE 1.0` label now identify the wizard;
the earlier development label was `EMBERCADE 0.5`. Packaging remains `0.1.dev0`.
The subsequent MainRig clean-install acceptance expanded that same wizard with
a dedicated PSP/Xemu system-files step. It validates the user-selected official
PPSSPP assets (`ppge_atlas.zim`, `lang/`, `flash0/`) with the runtime validator
and stores a read-only source path; Xemu's existing preparation backend makes
isolated firmware/HDD working copies from a selected source without
changing that source. EEPROM is optional and generated by Xemu when absent.
Missing PSP assets are now reported as unavailable for
PSP play, not as a harmless optional extra. Reopening the wizard shows the
configured PSP path and read-only status for managed cores, Xenia and Xemu;
import source fields deliberately remain blank because the sources are not
persisted. Back/forward navigation retains unsubmitted field values.

The user completed a true zero-installed MainRig setup, including external
ROM/BIOS roots, controller shortcut, managed cores/Xenia, PSP assets, Xemu
files and optional Steam registration. Installed Doctor passed all checks;
real Xenia and Libretro-PPSSPP games had image, sound, controller exit and
return to the same frontend. Splash, `EMBERCADE 0.5`, theme, controller menu
and Quit-to-desktop were confirmed. The subsequent changed-payload user-local
update preserved the configuration and managed Xenia/Xemu file hashes and the
config/data inventories; an identical-payload update preview was a no-op. The
445-test suite, runtime/frontend-library/shader smokes and Production Stage
passed for this change. The WohnzimmerPC was deliberately not modified or
revalidated in this MainRig-only follow-up; prior two-host wizard evidence
below is for the earlier feature revision.
The installed MainRig build confirmed the branded window, controller
navigation, existing-setup/Doctor completion and normal frontend splash,
theme, controller menu and quit-to-desktop. On the WohnzimmerPC, the installed
wizard's same controller/Doctor route was visibly accepted in KDE Wayland;
the existing Steam shortcut then passed splash, theme, controller menu and
quit-back-to-Steam in the real interactive Gamescope session. This does not
claim that the wizard itself was tested inside Gamescope. The implementation's
435-unit-test run, runtime smoke, frontend-library smoke, shader smoke, Stage
build and Stage Doctor passed. Both installed Doctors passed. Both hosts have
the same `d521c0557eb7` Stage-manifest SHA-256 prefix. The normal second-host
update retained the pre-update config hashes and file counts for config,
saves, themes, providers and PPSSPP assets; MainRig's normal update likewise
retained its inventoried user data. The source checkout remains private.

HTPC/External Apps and the Batocera-ES GLES3 renderer optimization are not 0.5 blockers.
This private feature freeze is not a public release: unresolved third-party
asset licensing and the unresolved scope of the selected project license still
block publication. Working theme/decoration/shader assets will not be stripped
to force it.

## Branding resources

The selected user-provided masters are retained in `resources/branding/source`:
the 4688×4688 arcade icon, 10800×21600 portrait artwork and 8000×4500 landscape
artwork. Downscaled derivatives preserve aspect ratio: 128/256/512px icon PNGs,
a 900×1800 Steam grid image and a 3840×2160 startup splash. The Steam hero is a
relative link to the same 4K landscape derivative. The installed Desktop Entry
uses the hicolor icon name `embercade`. Production passes the splash to
EmulationStation's built-in `--splash-image` option, which closes the splash
after frontend initialization; if the artwork is missing, startup uses
`--no-splash` and continues. The separate square and 4:3 loading variants were
not staged because their fixed German progress text and geometry do not fit the
16:9 startup path. No separate transparent wordmark was supplied.

Steam artwork is included for optional native Non-Steam shortcut registration.
Interactive first run now offers `Add Embercade to Steam? [Y/n]`, and the explicit
`embercade steam` command uses the same integration. Normal frontend runtime
never edits Steam metadata. Declining, absent initialized profiles, running
Steam or ambiguous metadata do not block Embercade installation. Native/XDG
Steam aliases are deduplicated; multiple profiles require an explicit selection.
Flatpak Steam is detected but its host-launcher bridge remains unvalidated and
is deferred without modifying that profile.

The branding assets and integrations were implemented in commit `d5e4deb`:
a hicolor application icon, EmulationStation's 4K startup
splash with missing-asset fallback, and Steam grid/hero artwork resources. The
Desktop Entry uses `Icon=embercade`. Those commits implemented and accepted
branding before automatic Steam registration was added; the earlier one-off
host-local artwork assignment is superseded by the registrar acceptance below.

The current shared `steam.py` registrar reads installed branding resources,
identifies the installed launcher, retains an existing Steam-assigned appid and
writes only that shortcut's executable/start-directory/icon fields plus its artwork. All
foreign shortcut nodes are preserved byte for byte; existing options, tags and
play-time fields are retained. New shortcuts receive deterministic collision-
checked IDs. Icon, portrait, landscape, hero and logo slots are populated; the
logo slot uses the existing embedded-wordmark landscape artwork, not a new
transparent logo. Unchanged repeat runs produce neither duplicates nor writes.

Registration requires Steam and its web helper to be stopped, validates all
targets, keeps recoverable original bytes/POSIX modes in Embercade XDG state,
and uses atomic file replacement plus in-process rollback. It does not kill or
restart Steam; users start Steam afterwards to load the metadata. Corrupt,
unsupported, symlinked or conflicting data fail closed. Steam metadata is not
owned by immutable uninstall and is retained for reinstall/manual removal.
See [STEAM_INTEGRATION.md](STEAM_INTEGRATION.md) for file names, account selection,
recovery, offline-format references and limits.

Automatic native Steam registration is now validated on both reference hosts.
MainRig passed its normal reinstall and user-operated Steam launch. The
WohnzimmerPC, running CachyOS Handheld Edition with Steam/Gamescope, received the
normal offline update built from `9ebdca3`. It has no Embercade Git checkout;
the user explicitly chose payload/manifest verification rather than a new clone.
Both installed payloads were fully hash-verified against the same stage manifest
and transfer source commit `9ebdca3f493da822a8176f2363325384b2fc2627`.
The later acceptance documentation does not change this runtime code.

The second-host update preserved the metadata fingerprints of Embercade config,
data, saves/states, cache, screenshots/recordings, providers and PPSSPP assets.
State comparison excluded only the intentionally updated installation manifest.
Userconfig hashes, ROM/BIOS references and normal host emulator-profile metadata
were unchanged. Save contents were not read. No managed-core directory existed
on this host; its absence was preserved, and Doctor resolved 28/28 collection
cores from the existing host setup. Steam was stopped for registration. The
existing appid `4059814080` was retained, all eight foreign shortcut nodes and
unrelated artwork stayed byte-identical, and all five Embercade artwork slots
matched the installed resources. Repeating registration changed neither metadata,
artwork nor backup state and produced no duplicate shortcut.

The user started the updated shortcut in the real interactive Steam/Gamescope
session and confirmed artwork, splash appearance/dismissal and a visible,
controller-operable menu. This is fresh automatic second-host acceptance, not
an SSH-triggered background launch. A representative Xemu run also confirmed
the console bezel at correct 4:3 geometry; its overlay surface was measured at
3840×2160 on the 4K output. Select+Start returned to the same frontend PID,
with launcher status 0 and no remaining Xemu or decoration helper. The existing
Xemu exit route still terminates the emulator by signal; this is not a new
graceful-native-shutdown claim. The user then quit Embercade normally and
confirmed return to Steam; the frontend process was no longer running.

The apparent missing bezels did not require a code fix: the checked PCSX2
selections retained `ps2.bezel=none`, while Steam's visible MangoApp performance
overlay occupied Gamescope's external-overlay slot during Xemu. Turning that
performance overlay off and relaunching Xemu restored the bezel. Embercade does
not displace another overlay or override Decoration=None. MainRig's user also
reported the bezel concern resolved; no fresh MainRig emulator-matrix acceptance
is implied. See [STANDALONE_DECORATIONS.md](STANDALONE_DECORATIONS.md).

The full 345-test suite, including the Steam/first-run tests, runtime and
frontend-library smoke and shader smoke pass. `pytest` is not installed on the
development host; the repository-defined full `unittest` runner was used
without adding a package. Production Stage passes, and installed Doctor passes
on both hosts; Flatpak Steam execution remains unvalidated.

The earlier branding milestone passed its then-complete 312-test suite, runtime and
frontend-library smoke, Production Stage, staged and installed Doctor, and
Desktop Entry validation on both hosts. The repository remains private; these
checks do not resolve the public-release licensing gate.

`embercade setup` atomically updates the production TOML with existing ROM and
BIOS roots, one of the proven Back/Select+Start or Guide+Start exit presets,
and an optional Xenia Edge provider. Interactive setup offers an automatically
detected Core/AppImage source, a different user-chosen directory, or skip.
When nothing is detected, either source can be entered manually. It scans
sources read-only and copies all valid ELF64/x86-64 Libretro cores, not just
those needed for current ROMs, to `$XDG_DATA_HOME/embercade/cores`. Known Xenia
Edge AppImages can be copied to the managed provider directory and configured
automatically. Provider identity is now established from bounded ELF/type-2
AppImage/SquashFS metadata and exact embedded Xenia desktop fields, never
filename substrings. An existing `unsquashfs` or `7z`-family tool reads the
entry without executing/extracting the provider; neither is installed or
bundled by Embercade. Missing inspection support is `UNVERIFIED`, not proved
corruption. Equal provider content is reused across source filenames and
source folders without copies/backups. Different managed content is retained
unchanged and explicitly reported; several distinct valid source builds are
refused rather than automatically selected. Identical source candidates
collapse to one copy. Invalid/unknown files are skipped without source changes.
The normal managed filename is `xenia_edge_linux.AppImage`; valid older managed
names are retained on identical reimport. Configured override priority is
preserved, including invalid overrides; import never silently switches an
explicit override. Unchanged repeated setup does not rewrite TOML. Optional
provider failures retain their configured path and do not block ROM/BIOS
setup. Doctor distinguishes managed, external/override, missing, invalid,
unverified, ambiguous, optional and not-yet-selected managed states.
Emulator/core selection still belongs to Batocera's config and the existing
resolver, not to an import-side database. Every emulator route receives the
same central exit preset. Setup preserves unrelated user configuration and
never owns the referenced external ROM, BIOS, Core or provider sources. Default
uninstall is manifest-based and retains configuration, saves, state and cache;
explicit confirmed purge is limited to exact Embercade-owned XDG roots and
still excludes ROMs, BIOS and external providers.

The optional `embercade bootstrap` is a separate Arch/CachyOS/Garuda host
operation. It reads `/etc/os-release`, shares emulator and core discovery with
Doctor, determines collection-relevant Libretro requirements from the staged
ES system definitions plus the merged Batocera configuration, and offers only
verified repository package mappings that are available through the current
host's configured pacman repositories. Distribution identity is not treated as
evidence that Chaotic-AUR or any other third-party repository exists.
`--dry-run` performs no mutation; the normal command displays a
component-level plan,
defaults to no, and uses exactly
`sudo pacman -S --needed` after explicit confirmation. It never performs
`-Syu`, guesses substitute cores or downloads software. Exact packages are
shown only with `--verbose` and in Doctor.
The user-local installer still never invokes sudo or installs packages, and
uninstall never removes package-manager-owned dependencies.

A fresh CachyOS/KDE second-host test without Chaotic-AUR and without
preinstalled emulators proved that package availability differs between two
systems using the same distribution. In particular, development variants
available to pacman on the development host were only available through AUR on
the fresh host. Embercade therefore keeps stable repository candidates and
`-git` community candidates separate. PCSX2, RPCS3 and Xemu are queried in
current pacman repositories first, followed by their known `-git` repository
candidates. Only when both are absent may an already installed `paru` or `yay`
query the optional community candidate,
with a separate default-no confirmation.
Embercade will not install an AUR helper, enable repositories or edit
`/etc/pacman.conf`. Development-package preference is local user policy.

Doctor's default CLI output is a concise component summary; `--verbose` shows
technical paths and complete diagnostics. Doctor distinguishes RPCS3's
executable from genuinely installed firmware; a PUP file alone is not counted.
If RPCS3 and a user-provided PUP are available but firmware is absent, setup
can open RPCS3's UI with Embercade-owned HOME/XDG paths, wait for the user to
install firmware there and recheck. This workflow is unit-tested, not yet a
fresh-firmware live acceptance. Doctor also separates Xemu flash/MCPX firmware
from mutable EEPROM/HDD state and reports native first-start EEPROM creation
separately from HDD seeding. Reinstall is blocked while an installed Embercade process is
live. Launcher/emulator logs rotate at 8 MiB with two retained backups.

The same second-host run exposed a separate Production frontend packaging
fault: the staged EmulationStation binary had been linked to the development
host's Chaotic-AUR FreeImage package, retained a build-tree RUNPATH, and failed
where `libfreeimage.so.3` was unavailable. With the intended payload library
path applied, `libSDL2_mixer-2.0.so.0` was already staged and FreeImage was the
only unresolved frontend dependency. Copying the development-host FreeImage
binary was rejected because it pulled repository- and ABI-specific OpenEXR and
JPEG-XR libraries, including an x86-64-v4 package set unsuitable for the
second host.

Production now builds unmodified FreeImage 3.18.0 from a SHA-256-pinned
upstream source for generic x86-64 with its bundled codecs. The resulting
library has only the normal C/C++ runtime closure, and its upstream license
texts plus a provenance NOTICE are included in the payload. The frontend is
rebuilt without a development RUNPATH; FreeImage and SDL2_mixer resolve from a
process-scoped Embercade library directory. Every direct frontend SONAME is
classified as payload- or host-provided, Stage rejects missing, unknown or
host-escaped dependencies, and Doctor reports binary presence separately from
shared-library health. The updated user-local install and Doctor have passed
on the second host without adding a system package or changing `/usr`.

The transfer run also found that old stages shipped relocation-sensitive
Python bytecode. Staging now strips all bytecode and every Python production
entry point uses no-bytecode mode. Reinstall tolerates drift only for bytecode
from the older immutable payload, verifies every other existing file, and then
transactionally replaces the complete prefix. This is a one-way compatibility
rule for updating old test installs, not a general integrity bypass.

The first visible second-host start then proved a distinct CPU-portability
fault before the UI appeared: the higher-tier CachyOS build host had embedded
an x86-64-v4 requirement in EmulationStation, while the second host supports
through x86-64-v3. The bundled SDL2_mixer binary also came from the v4 package
set. Embercade now builds SDL2_mixer from its pinned upstream source with
generic x86-64 flags, builds EmulationStation explicitly for generic x86-64,
removes the build-host startup object's distro ISA property, and makes the ELF
audit reject nonbaseline frontend requirements. After reinstall, the same
second host reported a healthy Doctor and visibly opened the installed
frontend in its local KDE-Wayland session.

The first emulator pass on that host exposed two narrow desktop-distribution
differences. Its PCSX2 package installs `GameIndex.yaml` and `patches.zip`
below case-sensitive `/usr/share/PCSX2/resources`, so the fallback resolver now
accepts that location as well as `/usr/share/pcsx2/resources` while preserving
explicit configuration precedence. Its KDE Wayland session keeps the Xwayland
cookie in `XAUTHORITY`; without that file in the frontend namespace,
`vulkaninfo` failed its XCB/Xlib surface probes and crashed before Xenia's
Vulkan check. Production now validates and exposes only that file read-only at
a private runtime path. Replaying `vulkaninfo` in the otherwise identical
Production namespace then returned success and identified the host RADV GPU.
The updated payload passed visible PCSX2 and Xenia launches. RPCS3 initially
remained configuration-required because only the firmware update PUP was
present; after the user installed firmware through RPCS3's normal UI, the
isolated Embercade launch also passed without Embercade adding firmware-install
behavior.

A later SteamOS/Gamescope package update exposed two inherited-session
boundaries. Steam's SDL policy hid the physical controller and exposed only a
virtual device without USB identity; Embercade now isolates controller discovery
from those variables. Gamescope's Vulkan WSI layer also requires the Unix socket
named by `GAMESCOPE_WAYLAND_DISPLAY`. Production validates and passes through
only that socket, rather than exposing the full host runtime directory. Because
emulators retain Embercade's private `XDG_RUNTIME_DIR`, the sandbox exports the
validated socket as an absolute display name.

The updated Gamescope WSI layer works for PCSX2 but aborts current RPCS3 builds
inside its own `vkroots` queue-dispatch assertion. The PS3 launch plan therefore
disables only that optional bypass layer and retains RPCS3's normal X11/Vulkan
presentation path; other emulators keep the validated Gamescope socket.

Gamescope does not guarantee that a synthetic Alt+F4 is delivered to the
emulator window. The launch-scoped Select+Start bridge therefore signals only
the synchronous launcher process; it can no longer close EmulationStation when
focus remains on the frontend. Delegated AppImage providers use a named
transient service and stop that exact service if their waiting launcher is
interrupted, preventing a headless Xenia process from surviving a frontend
restart.

SteamOS Gamescope only promotes X11 windows carrying a numeric `STEAM_GAME`
property. An AppImage delegated through the user service no longer has Steam's
process ancestry, so the Xenia host child tags each matching Xenia window with
the inherited numeric `SteamAppId`, including replacement windows created
during a game. The external exit bridge reads Select/Guide plus Start directly
from the selected physical evdev node. In a Steam/Gamescope session it also
reads Valve's forwarded `28de:11ff` Xbox gamepad: Steam may exclusively consume
the physical node even though games continue receiving its virtual output. This
keeps the chord usable when the emulator window is unfocused or its event loop
is hung without changing controller selection outside Steam. Xenia's delegated
host provider owns the Steam-session watcher because that is the first boundary
where the forwarded node is live-reliable. A chord terminates only the provider's
new process group, allows a short SIGTERM grace, then escalates that group if the
emulator is hung; an intentional chord exit is reported as success.

The installed Production namespace exposes only the host user manager's
`systemd/private` socket for launch-scoped Xenia service control. Emulator
configuration and its private XDG runtime remain isolated. The transient
provider unit uses `KillMode=mixed`: on a requested stop the host runner first
stops only its owned Xenia process group, then completes its existing scoped
AppImage/FUSE cleanup before the unit exits. An earlier control-group stop
could time out and leave an AppImage mount; the MainRig retest with the updated
runner returned launcher status 0, kept the same frontend process and left no
Xenia process or mount. The real WohnzimmerPC Steam/Gamescope test also returned
launcher status 0, kept the same frontend process, left no mount and quit back
to Steam normally.

The first updated Xenia attempt passed the in-sandbox Vulkan probe but exposed
one further namespace boundary: the external AppImage service inherited the
private sandbox `XAUTHORITY` spelling, which does not exist in the host mount
namespace. The provider runner now translates that single variable back to the
already validated host cookie path, just as it already translates the fixed
Embercade XDG/ROM/BIOS whitelist. A subsequent run exposed a second narrow
provider mismatch: Xenia loaded its configuration from `XDG_DATA_HOME/Xenia`
instead of configgen's emulator-config directory. Both paths are now aligned,
the file contains host-visible Embercade storage roots, and the visible
fullscreen/Select+Start/return-to-frontend retest passed with launcher status
0.

The Xenia convention is
`$XDG_DATA_HOME/embercade/providers/xenia/`, searched after an already
configured provider. Arbitrary explicit paths remain supported. Setup retains
native PATH/override executables and validates recognized regular executable
Xenia Edge AppImages, handles spaces as path data and never downloads or changes
the external source. Optional import copies a validated
known AppImage into the managed user-data directory and sets executable mode
on that new copy.

Provider-management polish uses the existing importer, resolver and setup;
it adds no provider framework, downloads, links or emulator binaries. Safe
copy publication remains atomic/exclusive, and changed sources cannot leave a
partial target. A normal install/update/uninstall preserves imported provider
and config bytes, modes and mtimes, covered by a direct regression test. The
reference-host metadata probes pass using unsquashfs on MainRig and existing
7z on WohnzimmerPC. Both hosts passed normal committed-payload updates, setup
reuse and Doctor without reimporting the byte-identical managed Xenia provider.
Visible Xenia play, controller exit and return to the same frontend passed on
MainRig/Hyprland and in the WohnzimmerPC's real Steam/Gamescope session.
Provider, theme, core and PPSSPP resource metadata survived the second-host
update; subsequent game-generated config/save writes are not attributed to the
installer. No compatibility/READY status is changed by this provider-polish
acceptance.

A transportable `Embercade-0.1.dev0-test.tar.gz` can now be built below the
ignored `.work/dist` tree. It contains the exact verified Production Stage,
per-file integrity metadata, a deterministic archive and a thin install entry
point that delegates to the existing transactional user installer. The target
requires no Git repository, source checkout, network, pip or build step.
ROMs, BIOS, firmware, Libretro cores, emulator binaries, user configuration,
logs and external provider binaries are excluded. Offline reinstall,
setup/Doctor continuity and a visible local KDE-Wayland frontend start have
passed on the second CachyOS host; packaging itself performs no SSH or remote
installation.

The launch-scoped configured exit bridge uses the host's ABI-matched
`python-evdev` package through a narrow import adapter. The pinned launcher
runtime does not enable unrestricted system site-packages; Doctor reports the
native bridge separately.

The development version is currently `0.1.dev0`; no `v0.1.0` release is
claimed. The earlier update milestone's complete unit suite passed **422 tests**;
the pinned launcher runtime smoke, frontend-library smoke, Production Stage, installed
Doctor and offline payload build also pass. The installed standalone-decoration
modules on both tested hosts match the current source byte for byte. Both
user-local installations contain the
pinned shader and console-decoration resources; the second host's PPSSPP
assets are present. Its installed Production Doctor passes in a headless SSH
check, including frontend libraries, launcher runtime, provider discovery,
firmware and PPSSPP assets. The updated second-host installation has also
visibly started and remained operable in Steam/Gamescope, as confirmed by the
user. On the development host the user completed a fresh application install,
the menu was visible and operable, 232 managed Libretro cores resolve without
their original source folder, and the managed Xenia AppImage is byte-identical
to its source. Source checksums remained unchanged. One previously managed
Nestopia binary differs from the later selected source file of the same name;
the importer preserved the existing file and reported the conflict. At
least one game has launched through each available standalone provider, and
multiple Libretro cores have also run without a reported regression. Broader
clean-machine acceptance is still pending.

## Roadmap

The public, non-date-based direction is maintained in `ROADMAP.md`. The 1.0
feature set is frozen for private packaging/finalization; the roadmap is not a
delivery promise and public licensing gates remain separate.

## Packaging and provider direction

The current executable provider supports:

1. native executable/`PATH`
2. explicit executable override
3. user-supplied AppImage

Flatpak remains a possible later provider type. Xenia Edge is the proven
AppImage test case; Wii U currently uses the proven Cemu Libretro core instead
of a standalone provider. The private Embercade AppImage packages Embercade,
its frontend, pinned runtime packages and default resources, but not emulator
binaries, imported cores, downloaded themes or copyrighted game content. The
host interpreter/library boundary and packaging evidence are documented in
[APPIMAGE.md](APPIMAGE.md).

## Public project rules

Embercade does not include or provide ROMs, BIOS files, firmware, keys, or other
copyrighted game content. Users must provide their own legally obtained files.
It does not distribute emulator binaries; it integrates compatible emulators
installed separately by the user.

Embercade is independent and must not claim official affiliation with Batocera
or RetroBat. The tracked tree and full private history were audited for public
release preparation. Current files no longer contain personal development
paths or named commercial test titles, and host inventory reports default
to ignored `.work/reports` in development or external XDG state diagnostics in
Production, rather than tracked documentation or the immutable application.

`docs/PUBLIC_RELEASE_AUDIT.md` is authoritative for the public-release gate.
The GitHub repository is currently **PRIVATE**, as confirmed by the remote's
visibility setting. The public-release decision is `NOT READY`: the owner has
made Non-Commercial a hard goal and selected **Option A** as the design
direction: compatible terms for GPL-/upstream-bound integration and patches,
PolyForm Noncommercial 1.0.0 (`PolyForm-Noncommercial-1.0.0`) for confirmed
independent own software, CC-BY-NC-SA-4.0 for own prose/cleared branding, and
original terms for third parties. This supersedes the earlier CC-software
proposal; Option B is not the goal. No effective
grant, LICENSE rollout, SPDX header or package-license assertion is introduced.
The own UI builder imports Batocera modules in its
caller interpreter; three own source-module probes, a development smoke and
two test payloads do so in children. These seven API-bearing paths and all
22 Batocera plus one ES patch are mapped separately from process/file-only
interfaces and reusable own helpers. Final combined-work/client scope, ownership
and compatible contribution terms require approval; absence of imports or a
subprocess boundary alone is not ownership or license clearance.
The precise files and evidence are in
[LICENSE_SCOPE_REVIEW.md](LICENSE_SCOPE_REVIEW.md). Its six-zone Option A design
maps the current 44 own modules to 23 lower-coupled PolyForm candidates, 17 requiring
additional interface/dependency review, and four API-mixed modules. These are
technical review groups, not 40 cleared NC files. Proposed extraction uses four
API adapters plus a shared helper and empty initializer in a separate Python
namespace; no extraction, new package, contribution policy or license scanner
has been implemented. Current API-bearing source/patch inventory is 29 paths;
the explicit six-file design would give 28 Zone-4 integration paths plus
two separately scoped API test programs (30, or 31 if smoke stays separate).
Path counts do not decide legal scope. The draft root notice/license tree and
SPDX/contributor strategy are non-effective future designs.
Zones now follow the owner-requested order: 1 independent own software,
2 own prose, 3 cleared branding, 4 GPL-bound integration, 5 MIT ES material,
6 third party. The seven API programs/22 Batocera patches need compatible
portion-level treatment under the confirmed upstream scope, not a blanket
PolyForm declaration for mixed files. Shared `runtime.py` config helpers and
their callers still need actual independence review.

The verified standard SPDX identifier needs no custom LicenseRef. This
software-specific choice does not make PolyForm GPL-compatible or resolve
copyright/asset/source-delivery gates. Commercial redistribution and permitted
organization uses need review before promising a universal commercial-use ban.
The intended own-software model is non-commercial source-available, not OSI
open source, and is not an active grant yet. `pyproject.toml` remains unchanged:
modern setuptools can support scoped metadata later, but today's mixed package
and the separately copied offline runtime must not be labelled wholly PolyForm.
Contribution/DCO/CLA policies remain proposals; no requirements are activated.

The PolyForm documentation-only architecture review against `1c8b7f3` passes
all 459 unit tests, runtime smoke, frontend-library smoke, shader smoke
(14 presets / 142 dependency files), all 30 local links in eight changed
documents and the complete 44-module/23-patch-map checks. No runtime or installed
user state changes, new E2E claim, license activation or asset replacement is
part of it. Public-audit stays expected-red; bounded secret-pattern checks find
no hit, not a universal privacy/security clearance.

NC may not override upstream GPL/MIT/other rights. Branding copyright and
product-identity treatment need separate rights evidence; no trademark
registration is established. Corresponding-source/change notices and actual
staged dependency/vendored/native-library coverage also remain release gates.
No further alternative license is automatically selected. Console-decoration
permissions, Carbon's version and embedded-rights questions, branding provenance
and complete shader notice accounting must also be resolved. The shader source
is precisely pinned and preserves upstream notices, but several selected
assets still have no separate explicit notice. The current functional Carbon
theme, decorations and shader assets remain in the private build; stripping
them merely to pass a public audit is not the chosen release path. Publication
waits for rights/notice resolution or an approved, functionally validated
replacement where rights cannot be established. Old personal paths and
test-title names remain in private Git history; no secrets or protected binaries
were found, so history was not rewritten without explicit approval.

**Bezel licensing review: PAUSED / PUBLIC-RELEASE BLOCKER.** The owner has
paused further bezel/decoration licensing investigation. Exact artwork-origin,
applicable-license and attribution questions remain unresolved; pausing does
not clear those questions or permit public redistribution. Retain the existing
evidence, functional assets and watermarks. No contributor contact, asset
replacement or removal is authorized by this decision. Resume the investigation
only on an explicit owner instruction. Embercade remains PRIVATE; private
development and the proven runtime behavior are not suspended by this status.

The complete console-decoration provenance evidence is now durable in
[BEZEL_PROVENANCE.md](BEZEL_PROVENANCE.md) and
[BEZEL_PROVENANCE.json](BEZEL_PROVENANCE.json): 302 exact shipped paths,
150 PNG / 151 INFO / one LAY, 33 retained links and 187 resolved content blobs.
Recipe overlay winners and final symlink targets match the captured reference,
existing stage and MainRig installation. Pinned histories cover 466 source
paths and 89 commits, with introductions, changes, heuristic copy/rename
boundaries and separate author/committer metadata. Contributions/specific
credits associate 231 paths with Duimon, 10 with Mikael42 and 17 with
Fery65/Lorenzolamas; 44 remain creatively unassociated. This is not a sole-author
or license-clearance count.

Duimon's original historical permission and explicit SA4.0 grants in the
actual Misc/Batocera and Retroarch-Overlays source releases are recorded alongside
later ND4.0 terms and TheNamec's historical SA/current ND evidence. Six PNGs
contain ND/Duimon XMP text; two further inspected PNGs show raster labels.
No final blob matches the compared source trees/history; that does not rule out
derivation. All 302
exact-file grant statuses stay UNKNOWN, requiring rights/source clarification.
No blanket Duimon, Batocera-code or project NC license is assigned to the pack.
All bytes and existing watermarks are preserved in transport, but rendered
clipping may hide notices; complete original/visible-attribution compliance
is unverified. Contact templates exist and have not been sent.

This documentation-only bezel audit passes all 459 unit tests and runtime,
frontend-library and shader smokes (14 presets / 142 dependencies). Matrix
coverage/link integrity is checked against the actual payload. No asset,
runtime, reference checkout or installed user state changed; no new E2E or
public clearance is claimed. Public-audit remains expected-red for the absent
effective root LICENSE and three retained oversized branding masters. PRIVATE
status and the prohibition on stripping functional assets remain unchanged.

# Embercade Agent Instructions

## Installer platform clarification (28 October 2026)

The owner emphasizes that the current installer supports Arch-family systems
because it uses pacman. State the actual allowlist precisely: Arch Linux,
CachyOS and Garuda; other distro IDs and unvalidated Arch derivatives stay
disabled. The graphical install action must show a localized explanation
before confirmation/terminal creation on unsupported hosts; the CLI guard
independently refuses even prepopulated plans. Add a translated label on Welcome and Host software
and prominent README/getting-started/release wording. Preserve the existing
guard, package commands and all other runtime behavior. Prepare a separate
updated public candidate/source export, retaining the earlier preparation and
all other builds. No push/release/tag, deployment or host changes.
The corrected isolated full suite reports 854 tests: 849 passed, five expected
native opt-in skips. All 75 host/first-run checks, three GTK flow/restart tests,
52 structural routes, runtime smoke and public-tree audit pass. This is
automated evidence, not a new interactive host acceptance run.

## Public preparation approved, publication still held (28 October 2026)

The owner authorizes personal-data cleanup, a separate public-distribution
AppImage, matching complete sources/notices and release notes. Preserve every
existing build, installed file/profile, original Git history/branch/tag and
reference repository. Prepare a parentless public Git export with the clean
current tree instead of rewriting the original history. The publication export
must contain no old private refs/releases or loose keys. Public artifact metadata
means prepared, never already published or permission to publish. Keep the tested
runtime/native frontend/resources unchanged; only privacy, packaging and release
documentation are in scope. The known 16:10 limitation remains. No push, GitHub
release/tag/visibility change, deployment or host package/driver change.
The final isolated regression passes 852 tests (847 passed, five expected
skips), including GTK and 52 structural routes. The 36 targeted packaging,
source-delivery and license checks, runtime smoke and public-tree audit pass.
The separate public preparation is now frozen at source e28f90b and image
SHA `204253d5b1a514d38e3bd57bdf26862cb525af127a0df7baf5ac4ec61e87302e`.
See docs/PUBLIC_PREPARATION_RESULT_2026_10_28.md. Ten files are ready locally;
no upload/push/tag/release/deployment occurred. All 17 pre-existing images and
original private history are preserved. Use the clean public bundle for later
publication, never silently expose or rewrite the original private history.

## Three-host owner acceptance complete (28 October 2026)

The owner now accepts the deployed d2194fc candidate on MainRig, EmbercadeLaptop
and WohnzimmerPC and reports that it works perfectly except for the previously
known laptop 16:10 bezel cropping/proportion issue. Record the three-host
functional acceptance as complete with that explicit limitation; do not reopen
it as an outstanding gate from older pending notes. This is the owner's broad
acceptance, not an instrumented claim about every game/format or checklist case.
Do not infer a 16:10 fix, change configurations/drivers, rebuild, redeploy or
start troubleshooting that known limitation from this confirmation alone.
Keep the artifact/source-kit identities unchanged. No push, public release/tag
or visibility change is authorized; the owner's publication hold remains.

## Current private candidate replacement approved (28 October 2026)

The owner explicitly requests replacing the active AppImages on MainRig,
EmbercadeLaptop and WohnzimmerPC under their existing filenames, preserving
Desktop/Steam links and settings. This supersedes the earlier no-deployment
limits for this exact private C64/per-user-RA candidate from d2194fc only.
Keep the canonical source/Gold/previous private artifacts; prepare verified
rollback copies, re-inventory targets/processes and update matching sidecars
and applicable image-ownership receipts. No loose keys/config profiles are
transferred. Do not stop unrelated apps, install packages or change drivers.
The owner performs remaining manual tests; deployment/CLI checks are not
three-host gameplay acceptance. No push, public release/tag or visibility change.
The authorized replacement is complete: five active files match SHA
`a3348017d24d1fa6d8b96118a591da1bcb3e77130a73fa7c5eda05b2c809c130`.
All three CLI probes, image/sidecar/rollback and unchanged profile/SSH/link
checks pass. Recovery receipts are in each host’s image-backups directory under
user-api-c64-2026-10-28-a3348017. No interactive process/session or package/driver
was changed. The optional per-user RA key file was absent on the two remote
PCs at deployment inventory; no current key state is inferred from acceptance
and the MainRig key must not be copied silently. See docs/PRIVATE_DEPLOYMENT_2026_10_28.md.

## C64 disk-start correction (28 October 2026)

The owner reports DEVICE NOT PRESENT for Giana Sisters D64 on MainRig and
authorizes scoped C64 launch diagnosis/repair. The real log shows the D64 is
attached; forced JiffyDOS without optional external ROMs disables the emulated
1541-II drive. Correct the desktop default, keep explicit overrides, other
systems, UI/authentication and media formats intact. Use isolated profiles and
a private copy of the real selected disk for execution; never boot synthetic
fixtures or write original ROM/BIOS collections. Preserve installed/Gold and
accepted candidates. A separate private repair candidate may be prepared for
owner testing; no push/publication, remote/host/driver changes or deployment.
The correction passes 848 isolated tests (843 passed/five expected skips),
52 structural routes, the real-disk A/B autostart comparison and packaged
Configgen/help/privacy audits. A separate d2194fc candidate is now open on
MainRig for owner retesting, after safely closing only this chat’s idle preview.
Seven protected image hashes remain unchanged. The owner now confirms that
Giana Sisters D64 starts and Start + Guide returns to the frontend on MainRig.
This accepts that disk/start/exit case only; do not infer other-host or
all-format gameplay acceptance. See docs/C64_STARTUP.md for candidate/source-kit
identities. The accepted image remains private; no push/release/deployment.

## Key-editor clipboard follow-up (28 October 2026)

The owner reports paste failing in the per-user API field. Fix the missing
native clipboard handling with explicit SDL paste shortcuts and visible Paste
controls while keeping the value masked. Do not read, replace or log the real
desktop clipboard/key during diagnosis; use synthetic test data. Preserve normal
profiles, authentication, installed/Gold images and the first private candidate.
Prepare a separate private correction for owner retesting; no publication/push,
remote deployment or host changes. Restart only this chat's own test frontend
after verifying no game is active; never terminate unrelated applications.
The separate correction from fd337ec is now package/source-kit verified and
opened on MainRig with existing settings; all six protected image hashes remain
unchanged. The owner now confirms successful entry and supplies a screenshot
of the live account overview with per-game progress on MainRig. This accepts
paste and overview rendering on MainRig only; other hosts and the remaining
restart/Cancel/Reset/key-absent gameplay cases are not inferred. See
docs/RETROACHIEVEMENTS_USER_KEYS.md. No push/deployment/publication is authorized.

## Per-user RetroAchievements implementation approved (28 October 2026)

The owner now approves the existing-settings masked Web API field, protected
runtime storage, missing-key guidance, unchanged normal emulator login and
automatic regression checks. This supersedes the earlier analysis-only limit
for this scoped frontend/build-safety change. Keep Batocera's Web API requests,
parsers and views; no emulator-API replacement or second login architecture.
No shared personal key may enter a new frontend/repository/payload. Build-time
RA input is rejected and old private binaries cannot pass new packaging checks.
Keep ScreenScraper and controller/emulator behavior unchanged. Prepare only a
separate private acceptance candidate; preserve Gold, installed images, profiles
and the frozen source kit. Manual three-host acceptance belongs to the owner;
never claim it from automated checks. No deployment, push/public release/tag,
visibility change, provider contact or host installation is authorized.

The separate private candidate is built from 010f5e8 with SHA
`599663de6aa860ea113181fc40d84cb7b44b8848ea9017f77bfabf14f086d52c`. Package/privacy audits and
both isolated help probes pass, with no old key in the 5,684 payload files.
Matching sources are under dist/private-user-api-2026-10-28/source-kit; Stage
and protected local images remain unchanged. See docs/RETROACHIEVEMENTS_USER_KEYS.md.
Owner three-host entry/rendering/gameplay acceptance remains pending; no
deployment or publication approval is implied.

## RetroAchievements per-user Web API direction (28 October 2026)

The owner supplied Hexadigital's advice to use each user's own Web API key,
avoiding shared-key rate limits/reset/ban exposure. Official docs independently
require an account-specific key and password-like handling. The targeted
read-only review is in docs/POLISH_1_0_PRIVATE.md. Normal login/emulator token
handoff is separate from frontend Web API list/summary calls. An optional
masked field in existing RA settings and a protected runtime user file is the
recommended narrow change; keep existing Batocera Web API views/parsers and
personal login. No documented login-to-Web-key exchange was found. This review
does not authorize implementing that runtime change or silently removing the
private build input. Do not distribute the shared personal key. Existing images,
frozen source kit, normal profiles and ScreenScraper remain unchanged; no new
build, deployment, push/publication or provider message is authorized here.

## Source and notice delivery prepared locally (28 October 2026)

The owner authorized completing the remaining licensing preparation while
personally requesting RetroAchievements guidance. Record that inquiry as
pending, not permission. See docs/THIRD_PARTY_DELIVERY.md, docs/SOURCE_ACCESS.md
and compliance/README.md. The kit targets the frozen d8e6ca6 adapter image,
preserving its source/hash, with a separately committed legal supplement.
Original sources, fully patched covered trees, exact build/install inputs,
nested native/Python/font notices and LGPL replacement/relinking instructions
are prepared. Do not reintroduce blanket native/vendor or old resource blockers
without new concrete evidence; do not claim that a local kit is public delivery.

Only legal-copy staging changes and source-preparation tooling/tests are in
scope. No runtime/emulator/controller behavior, upstream patches, resources,
normal profiles, hosts or existing images change. No new AppImage, deployment,
push, release, tag, visibility change or source upload is authorized. A future
public artifact must include these notices and be bound to its own actual
manifest/source kit after provider resolution and explicit publication approval.
Never archive unfiltered build trees/credential headers. Original LGPL/GPL
commercial/modification/debugging rights and all per-component terms remain.

## Owner-confirmed Canva AI branding origin (27 October 2026)

The owner states the branding was made in Canva and explicitly confirms the
background/arcade graphics were generated by the owner with Canva AI; an editor
screenshot was supplied. See docs/BRANDING_ORIGIN.md. The prior missing-creator
entry is resolved by this direct declaration. No formal certificate, new asset
comparison or further blanket AI-rights blocker is required by this record.
Apply CC BY-NC-SA 4.0 only to rights actually held, without claiming exclusive
copyright in all AI output, new rights in unprotected material or foreign rights.
The ten source/master/derivative paths are explicit in LICENSES/scope.json;
packaged maps retain only images actually included. No artwork, existing image,
source identity, user state or remote host is changed; no new build or push.

## Private adapter candidate identity (27 October 2026)

The new separate PRIVATE adapter image has source d8e6ca6f194e24d21d1bf8e80e8449f0310aeddd
(clean tree at packaging) and SHA a26055ca0aa3e921de3e559af3c5a32337de92f1826c3e4e549bf7781e79ae87.
See docs/ADAPTER_TEST_CANDIDATE.md. It passed the final package audit, all four
packaged backend operations, both builder modes and guarded client imports.
Gold/the accepted RetroBat image, installed images/links and prior Stage remain
unchanged. Do not deploy or infer manual acceptance; the owner tests all three
PCs. Preserve its private API mode, source identity and no-push/publication rule.

## Approved backend extraction and scoped grants (27 October 2026)

The owner explicitly approved implementing all four independent executable
backend operations and BOTH UI builder entry points, preserving settings,
priority, errors and user-visible behavior. This supersedes the older
proposal-only/no-license-files restrictions for this scoped implementation.
The effective root LICENSE, LICENSES/scope.json and docs/LICENSING_1_0.md now
assign the original independent client to PolyForm Noncommercial 1.0.0, original
prose to CC BY-NC-SA 4.0 and original upstream integration contributions to MIT.
No foreign code/context is relicensed. The process/JSON split alone is not a
legal exemption; retain the documented code-origin/purpose/contract basis.

The owner supplied the official Batocera LGPLv3 default policy; it was verified
against the pinned package paths. Do not label every Batocera package GPL from
Buildroot COPYING. Configgen is explicitly GPL; individual exceptions and MIT
EmulationStation keep their terms. See docs/BATOCERA_COMPONENT_LICENSES.md.
Own compatible integration grants do not change upstream commercial rights.

Build ONE new separate PRIVATE adapter test image after automated checks; never
overwrite Gold, the accepted RetroBat/shader artifact, or installed images. The
owner performs manual acceptance on all three PCs. No push/release/tag/visibility
change, deployment, normal-profile start or host package/driver change is allowed.
Preserve existing private frontend/API inputs and image identity; no new provider
permissions or public source-delivery clearance is implied. Never archive an
unfiltered build workspace containing credential headers. The old resource
audits are historical, not current blockers for the replacement payload.

## Current private image identity (27 October 2026)

The accepted source `87cc521f58e0cc2b3e0db51f8dfb1300e7c219bf` was built and
privately deployed at the five existing image paths. Current SHA is
938df3ab6a33de069baab4b8f9dfac876693a9efaa40f4b952d0519c916027d5;
verified rollback originals are under each host's
.local/state/embercade/image-backups/retrobat-shaders-2026-10-27-938df3ab.
See docs/PRIVATE_RETROBAT_SHADERS_1_0.md. Keep original profiles/SSH/Desktop/Steam
and the prior Gold canonical image/history intact. This completes the explicit
private build/deploy request, not public publication/push or remote visual
acceptance. The image's source identity does not move with later docs commits.

## Accepted MainRig test and private replacement authorized (27 October 2026)

The owner accepted the MainRig shader/None/exit tests, then the corrected Xbox
and PSP starts and the system-specific bezel menu. The owner explicitly requests
one new PRIVATE AppImage and replacement on all three PCs under their existing
filenames. This supersedes the earlier no-new-AppImage hold for this private
owner candidate. Retain the existing private ScreenScraper and personal
RetroAchievements build-input flow; no public distribution, push, new release,
tag or repository visibility change is authorized. Verify packaged behavior,
manifest/SHA, rollback copies, ownership receipts and unchanged profiles/links.
Do not kill unrelated emulators or change host drivers/sessions. Remote visual
acceptance remains deferred to the owner; do not infer it from deployment.

The initial separate MainRig test omitted the existing Xbox EEPROM/HDD and the
PSP-assets reference. Those were test-profile omissions, repaired using private
copies/RO asset binds; existing profiles were never reset. System/game menus now
show matching PNG+INFO pairs, deduplicate exact source aliases and retain one
real option plus None/Auto. The global menu keeps all 13 regular sets. Preserve
stored settings merely opened in a filtered menu; map the old consoles ID only
for display unless the owner actually changes the choice.

## Owner-approved shader package installation (27 October 2026)

The owner subsequently explicitly approved installing libretro-shaders-slang on
MainRig, EmbercadeLaptop and WohnzimmerPC. This supersedes the earlier no-package
installation rule for this one package on these three hosts only. All three now
have 20260620.024025.g8ec4c82cf61a-1; native transactions completed with zero exit,
including hooks. The central resolver finds all 26 complete preset/include/texture
graphs on each host. Existing images retain the Gold hash; no shader was enabled,
no profile/driver was changed and no image was built/deployed or pushed. This
package preparation is not three-host rendering/gameplay acceptance.

## RetroBat decorations and host shader resources (27 October 2026)

The owner's new integration request supersedes the older documentation/resource
freeze for this scoped implementation. Use the pinned official RetroBat bezel
collection exclusively in the next payload; never merge the old captured
Batocera/consoles artwork into it. Legacy `consoles` selections may resolve to
RetroBat `default_unglazed`, preserving the stored choice without using old art.
Report missing system/variant coverage explicitly. The owner adopts CC BY-NC-SA
4.0 for the RetroBat collection; record that as the owner's distribution decision
and retain individual embedded notices/credits, including ND notices, unchanged.
Do not repeat the completed provenance audit or turn that decision into a new
rights-holder statement. The Gold image remains unchanged as rollback evidence.

Prepare the official host libretro-shaders-slang provider, validated menu
mappings, optional host installation and safe missing-shader behavior. Shaders
stay OFF by default, manual graphics/shader choices persist, and existing core
exceptions and standalone/Gamescope rendering guards remain intact. Use isolated
tests; do not install packages, overwrite existing host profiles or deploy images.
No new AppImage until the owner explicitly lifts the build hold after technical
acceptance. No push/publication, repository visibility change or API-key changes.
Keep the independent GPL/own-code licensing question separate from resources.

The implementation now passes 801 tests (five expected skips), 52/52 structure
routes and the credential-free frontend compiler check. All 26 official-package
shader graphs and real frame-limited effects pass on MainRig, plus 13 regular
bezel overlay runs. Both remote hosts were read-only checked after boot and
initially lacked libretro-shaders-slang; the later approved installation above
is complete. Existing Gold image hashes are unchanged.
The new development frontend is not a deployment candidate; preserve production
build identity/authorization checks. See docs/RETROBAT_AND_HOST_SHADERS.md for
actual coverage gaps and remaining three-host manual acceptance. Do not turn
fixture lookup/GPU short runs into standalone/controller/gameplay acceptance.

## Targeted 35-PNG license-source lookup (27 October 2026)

The owner's later request authorizes a targeted license/credit lookup only
for the 35 H/M/F/L/U PNG paths, superseding the prior documentation-only rule
for those source lookups. See docs/BEZEL_35_LICENSE_FOLLOWUP.md and its 35-row
CSV. Spectravideo now has a reasoned RetroBat CC-BY-NC-SA-4.0 project-scope
assignment based on the explicit Lorenzolamas file credit, team graphics role
and identified distributed content. Mark this as a scope inference, not a
new individual artist message or a grant for other community art. Thirty-four
paths still lack a final applicable-file mapping. TheNamec's known RC2 SA4.0
source is positive evidence without establishing these exact variants; the
Lightgun Changelog adds Orions Angel/Fery65 credit, not a blanket grant.
Preserve the old 302-row baseline and all 267 non-target entries. No image/hash
or full-history inventory, asset/profile changes, contact, new build, push or
publication is authorized. No unrelated completed cases are reopened.

## Bezel decision detail from existing evidence (27 October 2026)

The owner requests an exact decision basis, not another provenance/hash audit.
Use docs/BEZEL_DECISION_1_0.md and its 302-row CSV beside the unchanged historical
JSON. Separate 8 PNGs with observed Duimon/ND notices, 107 further Duimon-linked
PNGs with general permission sources but unmapped variant scope, and 35 PNGs
without a concretely mapped grant (including two historical V31 dispute cases).
The remaining 152 entries are technical INFO/LAY paths. No actual file-specific
violation or denial was established; no pure missing-credit-only case is proven.
Do not equate old uniform UNKNOWN with 302 unlicensed pictures or treat missing
hash identity as a rights condition. Preserve positive author grants/notices.
This authorizes derived documentation only, not new asset/history scans,
resource changes, outreach, new builds, push or publication.

## Targeted shader and RetroBat reference follow-up (27 October 2026)

The owner authorizes using RetroBat's published component notices alongside
the existing pinned Libretro evidence. Carbon's origin and CC-BY-NC-SA theme
license are DOCUMENTED/DONE: retain Fabrice Caruso, Eric Hettervik and Nils
Bonenberger, plus the exact theme's additional maioni credit. Keep the original
mixed-version readme unchanged; separately licensed fonts/logos/audio are not
relicensed by this completion. Do not reopen Carbon's authorship as unknown.

For shaders, reuse the existing 14-preset/142-dependency inventory and examine
only open notices. Hashes establish integrity, not the sole test for provenance
or license continuity. Trace substantive code, ports, presets, embedded bitmaps,
textures and author grants; preserve previously established findings. NewPixie's
frame, Simpletex's paper texture and six handheld LUT images now have identified
grants. Keep the four exact legacy-code grant gaps separate from EasyMode's
known GPL notice with no version specified. See the current scope review.
RetroBat's project license is not an automatic license for every foreign asset.
No functional catalog/resource change, removal, contact, new AppImage, push or
publication is authorized. The earlier build hold remains in force.

## Licensing preparation and build hold (27 October 2026)

The owner authorizes updating license/provenance documentation and preparing
unchanged reference license texts, scoped candidates and notices for a permanently
free noncommercial community project. No paid/commercial licensing model is
planned. This supersedes the earlier no-license-files rule only for reference
preparation, not a blanket grant, SPDX source headers or packaging metadata.
Preserve original upstream rights, including commercial permissions; no single
NC label for the mixed AppImage. See docs/LICENSE_PREPARATION_1_0.md.

Reuse completed artwork comparisons. The earlier bezel-audit pause is superseded
only for recording the supplied Reddit/community evidence and the owner's public
summary of the team answer. No new artwork comparison, contributor contact,
resource removal/replacement, source refactor or functionality change is in scope.
The Reddit interpretation is not a pack-wide rights-holder grant.

The owner personally handles RetroAchievements with the provider on Discord:
whether the existing personal Web API key may remain or another identity is
needed. Keep the existing integration/login and private inputs untouched.
NO NEW APPIMAGE until that is clarified. No push, public repository visibility,
source/binary publication, tag/release or history rewrite is authorized by this
task; this supersedes the older completed Git-push permission for the new work.
Keep the tested Gold image, runtime, all host profiles and artwork unchanged.

## Laptop standalone-decoration dependency (26 October 2026)

The owner authorized diagnosing Xbox/PS2 decorations on EmbercadeLaptop and
separately approved installing the confirmed missing python-cairo there. The
shared renderer failed before drawing with No module named 'cairo', despite
available gtk-layer-shell/PyGObject/native Cairo. Preserve the accepted private
AppImage, all driver settings and existing emulator/media state. Host checks
must independently test Pycairo drawing types and its PyGObject bridge, and
offer python-cairo through the existing optional host-software flow on supported
KDE/Hyprland/Gamescope routes. Do not infer general NVIDIA compatibility from
package presence or a KWin snapshot. The visible retest restored artwork but
revealed a separate 16:10 proportion/cropping limitation, including RetroArch.
The owner allows a README limitation instead of a risky geometry change and
requires preserving MainRig/WohnzimmerPC. Do not remove clipping guards, force
aspect/FMV options, alter shaders or relabel visible artwork as correct 16:10
presentation. No geometry fix is implemented. See docs/LAPTOP_STANDALONE_BEZELS.md.

## Source/documentation push authorized (25 October 2026)

The owner's latest explicit instruction authorizes pushing the current source,
tests and documentation to origin/master. The earlier sprint no-push restriction
is superseded for those Git commits only. Keep the accepted AppImage private:
no image upload, new tag, new release, replacement of existing release assets,
or repository visibility change is authorized. Ignored dist/.work artifacts and
all private build credential files remain outside Git. Preserve the accepted
image/source identity and the existing v1.0.0 tag. No new build is required.

## Private five-part polish sprint (25 October 2026)

The owner now authorizes targeted RetroAchievements, KDE identity, GameSir
3537:109c SDL2 autoconfig, RetroArch notification sizing and frontend-video
repairs, isolated tests and ONE new private AppImage candidate. No push,
publication or release is authorized for this sprint. Preserve the released
v1.0.0 tag/assets, the original image in verified rollback copies, and user profiles/media.
The MainRig installation is active again; historical cleanup handoffs below
must not be applied. Existing GameSir Native Linux drivers/services, controller
configuration and other hosts' normal profiles are outside the writable scope.

For RetroAchievements the owner's explicit correction is authoritative: use
Batocera's existing CHEEVOS_DEV_LOGIN Web API path, with z=key-owner and
y=Web-API-key supplied through an owner-only ignored build file. The queried
user u remains the frontend login. Do not replace this with an emulator-token
API, add a login dialog, or change working personal authentication. This is a
PERSONAL account key, extractable from the binary, allowed for PRIVATE owner
TESTING ONLY. Distribution permission/dedicated application access is unresolved;
never carry this key silently into a public or unrelated build. The build
receipt must identify this private mode and reject stale/unlabelled binaries.
No values or authenticated URLs belong in output, logs, commits or reports.

The owner separately approved installing the verified missing vlc-plugin-ffmpeg
on MainRig for visual testing. Keep host libVLC and its distro-matched plugins
together; add the dynamic decoder/colour-conversion dependency to setup checks.
The owner has now accepted the real private candidate's Carbon and external-theme
list/video/icon and game/exit/mouse/notification flows on MainRig. Preserve the
candidate hash/source identity and record limits; this is no remote-host or
public-distribution approval. Original videos/gamelists/scraper media remain read-only. A successful decoder
probe is not itself proof of a rendered theme video or A/V synchronization.
Record each host/build/session/theme and manual acceptance limit separately.

## Three-host private image replacement authorized (25 October 2026)

The owner's later explicit request authorized installing the accepted candidate
on MainRig, EmbercadeLaptop and WohnzimmerPC under their existing AppImage names.
That deployment is complete; it is not public distribution/push/release approval.
Five active copies share SHA b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8.
Menu/Steam targets remain valid; Wohnzimmer's menu now targets its existing
AppImage instead of the preserved classic wrapper. Corresponding ownership
receipts were updated. Preserve private rollback originals under each host's
.local/state/embercade/image-backups/polish-2026-10-25-ac2578b8 and the protected
prior repository/release payload. Do not restore old filenames automatically.
Existing user config/Steam hashes are unchanged. The owner installed the approved
laptop VLC decoder personally; all three host module closures now pass. The
installer already offers vlc-plugin-ffmpeg in its existing optional host-software
flow. No new build, normal-profile start, driver change or remote visual acceptance
is implied. See docs/POLISH_1_0_PRIVATE.md for paths, verification and rollback.

## Release freeze

On 25 October 2026 the owner explicitly authorized pushing the completed work
and creating a GitHub release with tag/AppImage. Scope is the existing PRIVATE
repository: `v1.0.0` points to the tested image's exact build commit `3430484`.
Do not change repository visibility or mark unresolved public rights cleared.
The release filename is an alias of the verified image; keep its bytes and
original build source identity. See `docs/RELEASE_1_0.md`. This authorization
does not resume the paused decoration-rights investigation.
Release `v1.0.0` is now published and marked Latest in that private repository,
with all five verified assets and two source archives. Its tag remains at
`3430484`; do not move/recreate it or silently replace released assets. The
owner completed native file selection; no browser file-access grant was changed.

**Embercade 1.0 feature freeze reached.** Classic user-local Production is
the golden reference. Only release-finalization, packaging and regression fixes
are in scope; no new systems, controller features, assets or license decisions.
The repository remains PRIVATE and public-release blockers remain separate.

## Read first

Before changing anything, read:

- `AGENTS.md`
- `docs/PROJECT_STATE.md`
- `docs/COMPATIBILITY_0_1.md`
- the latest relevant Git commits
- the implementation and tests relevant to the requested change

Always run this preflight:

```sh
git status --short
git log --oneline -15
```

Do not start work on an unexpectedly dirty tree. Preserve user changes and ask
before touching overlapping work.

## Writable boundary

Only make persistent changes inside this repository. Sibling reference
repositories are read-only. ROMs, BIOS files and normal host emulator profiles
are read-only.

## Reddit-demo cleanup handoff

MainRig's owner-authorized final test cleanup completed on 2026-10-10; see
`docs/REDDIT_DEMO_CLEANUP.md`. The remaining Embercade config directory contains
only the protected `WohnzimmerPC` SSH key. Never delete that parent directory
as a setup reset. Preserve the final AppImage, checksum/manifest, installation
material, development SSD, original collections, shared scraper media and backups.
The existing encrypted ScreenScraper backup was authenticated and recovered only
in memory; no credentials were restored into the fresh user profile.

The manual xpadneo modprobe setting and live `disable_shift_mode=Y` remain
unchanged. MainRig is already prepared for Guide + Start; do not count its next
clean user setup as fresh privileged helper apply/undo acceptance. Any driver
reset still needs separate user confirmation and the safe disconnect/input-device
removal/reconnect sequence. Preserve independently installed OBS Studio and its
now-shared `mbedtls3`, FUSE 2 for AppImagePool, development `pugixml`, DOSBox/Boxtron
and normal desktop dependencies. No recursive orphan cleanup. This handoff ends
without launching or rebuilding the image, installing emulators, or accessing
WohnzimmerPC; further installation belongs to the user.

## ScreenScraper repair scope (2026-10-25)

The owner's later MainRig setup attempt on 25 October failed during host package
installation. The owner authorized local rollback, explicitly including older
normal RetroArch/shadPS4 data and excluding network drives. Six freshly checked
local targets (414 entries, 2,215,167,556 logical bytes) were removed: the new
config file, managed data/state, empty normal RetroArch tree and normal shadPS4/
QtLauncher data. No emulator package had installed; no package was removed.
Read-only first-run assessment is unconfigured with zero managed cores/providers
and no prepared Xemu state. The owner separately chose to KEEP the existing
xpadneo setting. Preserve the protected config parent/SSH key, current AppImage,
encrypted ScreenScraper backup, installation material, development data, original
collections and network drives. See the new rollback section in PROJECT_STATE;
do not repeat deletion from historical plans or start setup automatically.

The owner authorized source changes, isolated tests and a new private AppImage
candidate after the earlier cleanup. Preserve MainRig's prepared normal profile,
its handoff AppImage, system packages, SSH, original media and encrypted backups;
never re-run setup or update the menu-owned image there. Use disposable XDG
profiles inside development workspaces. No proxy/service or new user signup.
The owner subsequently confirmed moving/removing the old MainRig handoff image;
do not restore it automatically. The new candidate copy in the requested laptop
backup folder is not a MainRig installation/update.
Do not publish, release or push this work without new explicit approval. The
earlier perceived host-package installation delay is no longer being pursued;
keep truthful progress and safe package/result handling. The owner has since
confirmed working ScreenScraper in the candidate and reported a separate slow
RetroArch game-start issue on the laptop (Game Boy/SNES/N64, already in dock).
Investigate that issue without altering MainRig's prepared profile or drivers.
The owner authorized scoped SSH diagnosis on the laptop with separate test
profiles. The Qt/KDE desktop browser was confirmed to scan scoped scraper mounts
for folder icons: 43.135 seconds to the first EGL swap with 920 read-only media
binds, versus 0.622 seconds with the companion off. Preserve the narrow scraper
mount contract and in-game menu; patch `0030` disables only the extra companion
by desktop defaults and retains explicit user overrides. The delivered corrected
image passed isolated packaged Game Boy/SNES/N64 starts and the owner confirmed
the Game Boy delay gone with existing settings. Remote temporary probes were
removed; keep that acceptance distinct from full gameplay/exit testing.
Do not infer measured
startup latency from old log silence. See `docs/RETROARCH_STARTUP_FIX.md` and
`docs/SCREENSCRAPER_PRODUCTION_FIX.md`.

## Linux graphics/shader repair (25 October 2026)

The owner requests automatic compatible graphics selection, preserved manual
choices and core exceptions, and complete bundled shader provision. Do not add
a generic technical note to installer completion. Patch `0031` prefers detected
Vulkan on desktop, retains pinned OpenGL rules and explicit overrides, and
starts games without an incompatible/unavailable selected effect. A fixed-code
notice is shown by the same frontend on return, localized through the native
catalogues. Do not rewrite the saved shader/backend or enable a network command
listener to deliver notices. See `docs/LINUX_GRAPHICS_AND_SHADERS.md`.
Patch `0032` extends the same desktop preference to standalone PPSSPP/Azahar
using their native writers/probes, preserving manual/software/raw overrides
and non-desktop defaults. Packaged GPU-start evidence must remain distinct
from configuration-only standalone tests and full interactive gameplay/exit.
The private AutoGraphics image/source identities and verified laptop
600-frame 3DO/GB/SNES/N64 starts are recorded in that report. All 14 effects
compiled on the laptop; curated shader files and the frontend remain identical.
The subsequent Libretro None guard has explicit off/on regression coverage.
Owned remote probes are removed and normal config hashes are
unchanged. Do not turn these frame-limited captures into full gameplay,
controller-exit, standalone gameplay or other-compositor acceptance.
Shaders are optional and OFF in a fresh profile (`global.shaderset=none`);
only compatible renderer selection is automatic. Do not turn the explicit
shader regression fixtures into default user settings. Patch `0033` explicitly
clears the desktop shader-enable state for None, including stale enabled state,
while preserving valid user-chosen effects and non-desktop behavior.
Final source `3430484` passes 781 tests (five intended skips); its packaged
3DO/GB/SNES/N64 default starts explicitly disable effects. A separate chosen
Newpixie start enables and compiles the effect. The current image/hash and
handoff are at the end of `docs/LINUX_GRAPHICS_AND_SHADERS.md`.
The owner subsequently confirmed the delivered AutoGraphics candidate works
in personal testing. Record that acceptance separately from the automated
evidence; the response does not enumerate games, hosts or every open scenario.

## Upstream contract

Use the exact pins in `upstream.lock`:

- Batocera: `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`
- Batocera EmulationStation: `1750dded8c0fdff70630026f756a69fcad0bb995`
- architecture: `batocera-launch-44`

Never silently derive behavior from another upstream revision. Apply Embercade
patches only to disposable source snapshots under `.work`, not reference clones.

## Architecture contract

The launch model is:

```text
EmulationStation
  -> Embercade desktop integration
  -> batocera-launch
  -> Batocera SystemConfig/configgen/plugin
  -> host emulator or Libretro core
  -> cleanup
  -> the same EmulationStation session
```

Batocera's defaults plus `batocera.conf` decide emulator, core and features.
Do not recreate a parallel selection database in Embercade. Embercade resolves
desktop-specific executable/core paths, XDG isolation, compatibility and
controller handoff.

## Core contract

Never hardcode `/usr/lib/libretro/...`. Always use the central
`LibretroCoreResolver`:

```text
Batocera logical core -> Embercade resolver -> actual *_libretro.so
```

## Path and isolation contract

`ROM_ROOT` and `BIOS_ROOT` are configurable and read-only. Host-specific paths
must not become Python constants, tracked configuration or documentation.

For the existing ES scraper, only original-system `gamelist.xml` and upstream
`images/`, `videos/`, `manuals/`, `magazines/` may be writable. Never grant a
writable collection/system mount. The owner explicitly authorized compiling Embercade's own application
authorization from a private, unversioned two-field build source. The original
source/header, personal account and debug password never enter Git, argv, logs
or payload; only the compiled frontend contains application authorization,
which is extractable. CMake receives a private header path, never values.
Production validates the newly built frontend identity before staging/packaging;
missing build values must fail, while credential-free development is explicit.
End users need no developer file; account setup belongs only in the frontend.
Do not display developer/personal account status in Installer or Doctor. Debug
is off; use real provider E2E evidence before claiming scraper completion. See
`docs/SCREENSCRAPER.md`.

The personal ScreenScraper account is a separate owner-only XDG secret, not an
ES settings value or payload input. Migrate legacy account fields only after
the private file is saved successfully; normal reinstall/update must preserve
both secret files. The application prefix and AppImage are immutable:
all writable state stays in external Embercade XDG roots. See
`docs/STATE_AND_SECRETS.md`.

AppImage wraps the unchanged verified Production Stage under `AppDir/usr` and
delegates through the existing launcher/CLI. Its host CPython 3.14, desktop
libraries and GPU stack remain deliberate supported-host requirements; never
bundle host GPU drivers or invent another setup/provider backend. Only default
Carbon is packaged; downloaded themes, cores, providers and secrets are external.
Reject writable targets inside the prefix/AppDir before mutation. Production
diagnostic reports belong in XDG state, not an application-local `.work`.
Classic/AppImage share state only sequentially by default. With Steam fully
stopped, explicit `steam --replace-existing` may retarget the same shortcut to
the durable AppImage filename, preserving its identity; never register a mount
path or infer visible Gamescope acceptance from an SSH launch. See
`docs/APPIMAGE.md`.

Emulator configs, saves, states, caches and logs belong in Embercade's isolated
XDG/`.work` tree. Never silently write to normal RetroArch, Dolphin, PCSX2,
RPCS3 or Xemu profiles.

Production runtime and resource lookup must never depend on `.work`. `.work`
is only a build, test and development area; install-shaped runtime content is
addressed relative to the active Embercade prefix and user state uses XDG.

Never treat an ELF binary as production-ready merely because it exists and is
executable. Verify its shared-library runtime closure, classify every direct
dependency as payload-bundled or host-provided, and reject unexplained or
unresolved dependencies during staging.

## Content and distribution policy

Future system/provider scope decisions must follow the durable product rule in
[`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md#product-scope).

Embercade does not include or provide ROMs, BIOS files, firmware, keys, or
other copyrighted game content. Users must provide their own legally obtained
files.

Embercade does not distribute emulator binaries; it integrates compatible
emulators installed separately by the user.

PS4 is an explicitly approved older-platform 1.0 addition, not permission to
add PS5/current platforms. shadPS4 is user-supplied AppImage only: use the
existing managed importer, embedded identity, SHA-256 reuse/conflict policy,
resolver and scoped host runner. Never download/link/bundle it or fall back to
PATH. Direct games use `-g <eboot.bin>`; `-b` opens only its Big Picture UI.
Keep configuration/saves outside the AppImage and normal host profiles.
MainRig gameplay evidence does not establish second-host PS4 gameplay.

## Licensing boundary

Non-Commercial is a hard owner goal. Option A is the selected component model:
compatible treatment for GPL-/upstream-bound integration and patch contributions,
PolyForm Noncommercial 1.0.0 (`PolyForm-Noncommercial-1.0.0`) for confirmed
independent own software, CC-BY-NC-SA-4.0 for own prose/cleared branding, and
original terms for third-party material. This supersedes the earlier proposal
to use CC for own software. Option B (all own software under a non-NC compatible
license) is not the goal. The effective zones are: 1 own software, 2 own prose,
3 cleared branding, 4 GPL-bound integration, 5 MIT ES material, 6 third party.

The earlier scope review is retained as history. The approved extraction is
implemented in docs/ADAPTER_SEPARATION.md; the effective file scope is the root
LICENSE and LICENSES/scope.json. New software files need explicit mapping.
Neither client nor backend may import each other's implementation. Review data,
code origin, object/callback coupling and generated foreign output as well as
imports; separate processes alone do not establish independence. Preserve all
GPL/LGPL/MIT rights and original notices. Do not place a blanket NC license on
the mixed AppImage or claim OSI open-source status for PolyForm.

The supplied branding now has a direct owner-confirmed Canva AI origin and a
rights-scoped CC grant; retain that record and its limits. Public provider/API permission,
source/notice delivery and publication/privacy review remain separate. The
repository and new test candidate stay private; no push without explicit approval.

## Controller rules

Never hardcode SDL indices, `/dev/input/eventXX` nodes or device names. Re-enumerate
after reconnect because all can change. RPCS3 requires the SDL name (for the
current MVP device, `Xbox 360 Controller`); most other generators use the
kernel/evdev name (`Microsoft X-Box 360 pad`). Do not globally rename the device.

The development harness exposes the complete live `/dev/input` directory to
EmulationStation. ES handles SDL device add/remove events, and every launch
must enumerate the controller again. Do not regress to a session-start snapshot
or a Bubblewrap mount of one fixed `eventXX` node.

For multiple gamepads, reuse EmulationStation's player preferences and pinned
Batocera generators. Pass every live player slot at launch; keep the configured
exit chord owned by Player 1. RetroArch's SDL2 slot and mapping handoff must
stay aligned with the launcher, and unique-device reservations must not be
applied ambiguously to duplicate controller models. Dolphin's evdev button
order can differ from SDL when a pad exposes extra system keys; translate from
the live read-only device capabilities, never a model-name table. Preserve the
user's independent GameCube face-button rotation settings. Real E2E scope and
limits are recorded in [docs/MULTI_CONTROLLER.md](docs/MULTI_CONTROLLER.md).

Wii uses Dolphin's native Real Wiimote transport and the existing
`emulatedwiimotes` option, not another input/mapping backend. Auto probes
permitted, dynamically identified generic Wii HID slots at game launch;
structural dry runs and Doctor never probe hardware. On forces gamepad
emulation, Off selects Real with native continuous scanning. Preserve existing
user overrides and GameCube mappings. Expose only matching permitted hidraw
nodes; never rebind drivers, pair Bluetooth or change host permissions silently.
Wireless Wiimote reconnect and USB-receiver unplug/replug are distinct: the
latter currently requires frontend restart.
Keep `SDL_JOYSTICK_HIDAPI_WII=0` scoped to Embercade: SDL must not compete with
Dolphin for the receiver or shift PCSX2/RPCS3 gamepad numbering.
In emulated-Wiimote mode on desktop, preserve the scoped Start→Wii +,
Back/Select→Wii − and Guide→Wii Home mapping; the configured Player-1 exit
chord remains authoritative. Sideways-Wiimote games need their existing
per-game controller-mode setting rather than a global D-pad rotation. Never
apply this mapping to Dolphin's native Real-Wiimote mode or to GameCube.
Peripheral E2E is per feature and host; DolphinBar/Nunchuk acceptance never
implies MotionPlus or Bluetooth passthrough acceptance. See
`docs/WII_CONTROLLERS.md`.

Standalone GameCube/Wii decorations reuse the existing PCSX2/Xemu supervisor
and Batocera's bezel selection; `Decoration=None` and unsupported/wide aspect
settings must fail safely without blocking Dolphin. Do not introduce another
overlay engine or make a decoration mandatory for game launch. See
`docs/STANDALONE_DECORATIONS.md`.

Lightguns, wheels and trackballs are structural **PREPARED / UNVALIDATED**
routes, not hardware READY. Reuse pinned Batocera udev/Configgen and
EmulationStation preferences; do not add a device whitelist, parallel input
database, global udev rules or host-wide wheel calibration. Desktop wheel
range writes and the Batocera virtual-wheel calibrator are disabled; raw axes
remain available. An ordinary mouse is not proof of a trackball. Keep P1 exit
ownership and MAME/MESS's separate BLOCKED status. See
`docs/SPECIAL_CONTROLLERS.md` before changing these paths.

## Status discipline

`READY` requires a real successful end-to-end test. A dry run alone is at most
`UNTESTED` or a prepared port. Do not inflate compatibility status from an
installed binary or core.

The complete 1.0 catalog uses READY / PREPARED / BLOCKED / UNSUPPORTED.
PREPARED requires a verified runtime/core, an implemented isolated route and
successful pinned-generator structural evidence; missing BIOS is an explicit
setup requirement. NO_ROM is informational and empty systems remain hidden.
Never start an emulator with a synthetic structural fixture. Run the complete
structural integration tests before staging; their source digest must match.
`system-coverage` inspects the installation's pinned catalog and actual host
runtime without selecting a different emulator or launching a game.
Optional Libretro `.info` companions are diagnostic metadata, never a hard
runtime/Doctor or PREPARED prerequisite. Verify actual core ABI/dependencies;
use the pinned Batocera catalog for system/core mappings and extensions.

## Change discipline

- The owner approved a separate bilingual Controller & Hotkeys installer step.
  Detect xpadneo by its live kernel binding, not controller model names. Driver
  changes require explicit UI confirmation and administrator authentication.
  Disconnect all affected xpadneo devices and verify their old input nodes are
  gone BEFORE changing the global Guide shift parameter; reconnect and check
  synthetic mouse buttons afterward. Never hot-switch it on connected devices.
  Preserve foreign modprobe settings; undo only exact receipt-owned changes.
  The live chord exercise consumes modal input, requires sustained simultaneous
  buttons and final release, and resets on reconnect. It never launches a game
  or substitutes for Player-1 emulator-exit acceptance. Keep Back/Select + Start
  available when adjustment is declined or unavailable. See
  `docs/CONTROLLER_SETUP.md` for the observed mouse regression and recovery.
- Every installer launch starts on Language, including a configured profile.
  Preselect the saved language (system locale only when absent), then continue
  to Welcome. Opening the installer must not reset existing setup or state.
- Installer information, error and confirmation dialogs share wrapped text
  sizing based on the actual viewport width. Short messages must be fully
  visible; long reports scroll while actions remain visible. Test rendered
  text/viewport geometry in both languages, not just overall window height.
- Installer source selection uses the shared standard desktop chooser, not a
  custom filesystem list. Empty/unavailable fields start at Home, never the
  AppImage working directory; existing directories/files are preselected.
  Prefer Gtk.FileChooserNative with the session FileChooser portal and use the
  conventional GTK chooser for unavailable portals or Gamescope. Preserve entry
  text on cancellation, consume modal controller input, and accept only usable
  local paths (including mounted network shares). Test the actual AppImage's
  portal request separately from automated GTK lifecycle tests; never change
  desktop language/settings or install emulators just to validate selection.
  See `docs/INSTALLER_FILE_CHOOSER.md`.
- The owner approved the final-polish installer exception: nine-stage GTK
  redesign, offline Xbox EEPROM setup, explicit official PS3 PUP download and
  native isolated installation, and user-local Desktop/AppImage integration.
  Keep all user-facing text in the central catalog and reuse existing setup,
  bootstrap, native emulator, Steam and production backends. See
  `docs/FINAL_POLISH.md` for contracts, rollback and mandatory manual acceptance.
  EEPROM edits require full format/checksum/HMAC validation, backup and atomic
  save; preserve HDD key/identity and refuse concurrent native processes. New
  PS3 installs run in temporary isolated state before activating complete
  firmware, never over an existing version. Desktop manifests must not replace
  classic ownership or overwrite user-modified files. Downloads remain external
  user data, never redistributed firmware or emulator payload.
- Readiness must distinguish actual isolated PS3 firmware from an importable
  host source and prioritize effective pinned/user collection routes. Setup
  availability is not per-host gameplay READY. On 2026-10-10 the owner confirmed
  ScreenScraper works in the new MainRig AppImage after identifying a user-side
  issue; the earlier personal-authentication failure is historical. Record this
  as user-confirmed operation, without inventing new automated, media-specific
  or second-host tests. The owner's 2026-10-25 instruction authorizes the existing build-time application
  authorization pattern with Embercade credentials. Compiled values are
  extractable; do not invent a further blanket approval gate. Keep personal/
  debug values and loose source files out of the payload. Actual full frontend
  scraping/restart acceptance is distinct from a developer-only API check.
  No public release, publication or push without explicit owner approval.
- Fullscreen layer-shell decorations use exclusive zone -1, four anchors and
  zero margins: zone 0 respects Plasma reservations and clips the full artwork.
  Keep logical GDK/Cairo scaling, selected-monitor allocation guards, existing
  game-protection clipping and the separate Gamescope contract.


- Xemu requires user-supplied flash/MCPX and an HDD image, never an EEPROM
  source. Let native Xemu initialize the absent EEPROM at the explicit isolated
  save path; preserve existing EEPROM/HDD on setup, update and reinstall.
  Optional legacy EEPROM seeds must never replace existing state. See
  `docs/GARUDA_BLANK_INSTALL.md` for version/source evidence and acceptance.
- Host bootstrap supports exact `arch`, `cachyos` and `garuda` IDs. Probe stable
  candidates first, then known `-git` candidates in the target's configured
  pacman sources, then an existing AUR helper. Every install requires explicit
  confirmation. The terminal worker waits for the actual bootstrap child and
  transaction hooks. Close only its own terminal on zero exit; retain failed
  output until acknowledgment, classify cancellation separately, and always
  refresh host status. Terminal-launcher exit alone never proves success.
  Modal GTK input belongs to the dialog, including SDL polling inside its nested loop. GTK signal tests and
  native Xemu `--version` probes do not replace two-host interactive E2E.
- The owner explicitly approved the German/English first-run exception to the
  1.0 freeze. Keep installer text in the central `i18n.py` catalog; persist only
  `[installer].language` through the existing atomic config writer. A language
  change must preserve setup, emulator state and frontend language choices.
  Structured installer diagnostics reuse Doctor/bootstrap assessment and expose
  no secrets. External package-manager/native emulator output is not translated.
- Query KDE's active physical output mode and Gamescope's logical game output
  before config generation; do not assume 1080p or set a display mode. KWin
  decorations reuse the existing layer renderer, exact executable/ancestry and
  fullscreen guards. Only load/run/unload a uniquely named disposable observer;
  never change persistent KWin settings/rules or start other scripts. Include
  optional `gtk-layer-shell` in the supported-host package plan for desktop
  Wayland, not Gamescope. See `docs/GLOBAL_GARUDA_AUDIT.md`.
- Interchangeable EmulationStation themes must never replace persistent
  Embercade product branding; the startup/loading splash remains theme-independent.
- Keep changes minimal and special cases data-driven.
- Normal application updates preserve Embercade-owned persistent user state;
  they must never behave like purge.
- Do not refactor proven launch paths without a concrete reason.
- Do not install or bundle emulator packages as an implementation shortcut.
- Never infer package availability from a distribution name or another host.
  Probe the target's currently configured package sources, never assume
  Chaotic-AUR, and never enable a repository or modify `/etc/pacman.conf`.
- Keep large milestones in separate commits.
- After each sprint run the full test suite, `./scripts/runtime-smoke`, and
  `git diff --check`.
- Update `docs/PROJECT_STATE.md` only when a durable architecture, compatibility,
  provider, override, limitation or roadmap fact changes.
- Visible Steam/Gamescope acceptance must be validated from the real interactive
  session; an SSH-triggered Steam launch is not sufficient evidence of
  successful presentation.

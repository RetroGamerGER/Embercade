# RetroBat decorations and official host shaders

Prepared on 27 October 2026. This implementation supersedes the older resource
freeze for the next candidate. The accepted Gold AppImage and installed copies
are unchanged. The later explicit MainRig acceptance authorizes one new private owner AppImage
and replacement on all three PCs; no push or public publication is authorized.

## Decoration source and selection

The next payload uses only the official
[RetroBat decoration collection](https://github.com/RetroBat-Official/retrobat-bezels),
also referenced by [RetroBat build.ini](https://github.com/RetroBat-Official/retrobat/blob/main/build.ini).
Pin: `5ce1f6ed32eb9f3df8ae14483afc4d1e3ef35d65`.
The source archive SHA-256 is
`083ef02bd71ed8b4f9fd3fd6e884a2d4efa73138daa9cfb8e78e15c661dbd54e`.
`runtime/decorations.lock` and `scripts/decorations-prepare` reproduce the input.
The old sibling/reference `consoles` tree is no longer copied by UI preparation
or staging. Historical audit files and the protected Gold image remain evidence.

The existing ES directory discovery and Batocera configuration precedence remain
authoritative. Global, system and game choices reach both Libretro's lookup and
the standalone Xemu/PCSX2 lookup; user overrides in supported current sets retain
priority. Existing saved `consoles` choices resolve to `default_unglazed`, without
rewriting batocera.conf or ever loading artwork from the old user `consoles`
folder. The compatibility menu alias contains exclusively RetroBat files.
Fresh defaults use the actual new set name; shaders remain off.

Linux adaptations are limited to paths/configuration links:

- Supply the upstream links' missing `default` directory as an alias of
  `default_unglazed`; retain the original links and artwork.
- Expose `arcade_vertical_default/system` through a `systems` directory alias.
- Materialize 94 filename-only PNG/INFO link stubs as real relative symlinks.
  Without this, the Linux reader attempts to parse e.g. `default_4_3.info` as JSON.
- Add 80 same-system/generic/alternate-name fallback links, drawing exclusively
  from official RetroBat resources. This completes the unglazed legacy choice
  from `default_nocurve` where that contains additional systems/rotations, and
  resolves the upstream `segacd`/`megacd` link spelling. No remaining dangling links.
- Keep all animation data but mark `animated` unavailable for the current PNG
  renderer. Both the menu and launch lookup respect this marker; it is not
  advertised as working animation. Do not alter the rendering architecture.
- Missing official PNG/INFO pairs omit the optional decoration instead of
  blocking the emulator or drawing an opaque preview without a valid layout.

Preparation writes a collection receipt with all normalized links, fallbacks,
coverage and pin. Image pixels, embedded credits and original notices stay intact.

| Official set | Usable system/variant PNG+INFO pairs | Automated status |
| --- | ---: | --- |
| ambiance_broadcast | 22 | prepared; native lookup tested |
| ambiance_gameroom | 22 | prepared; native lookup tested |
| ambiance_monitor_1084s | 22 | prepared; native lookup tested |
| ambiance_night | 22 | prepared; native lookup tested |
| ambiance_vintage_tv | 22 | prepared; native lookup tested |
| animated | 0 | retained; hidden/unsupported |
| arcade_1980s | 19 | prepared; native lookup tested |
| arcade_1980s_vertical | 19 | prepared; native lookup tested |
| arcade_vertical_default | 63 | prepared; native lookup tested |
| default_curve | 110 | prepared; native lookup tested |
| default_curve_night | 110 | prepared; native lookup tested |
| default_nocurve | 113 | prepared; native lookup tested |
| default_nocurve_night | 113 | prepared; native lookup tested |
| default_unglazed | 152 | prepared; native lookup tested |

These counts include prepared integration links, not rendered-game acceptance.
`ambiance_broadcast` has no upstream generic default.info; an unsupported system
there gets no generic overlay. All 13 regular sets have native lookup tests for
SNES, Xbox and PS2 using selection fixtures. Actual visual differences, rotation,
opacity, monitor geometry and gameplay still require the manual matrix below.

## Exact coverage gaps

The existing audit supplies the 149 previous system/variant PNG names; no new
hash/provenance audit was performed. [Path comparison](RETROBAT_RESOURCE_COVERAGE.csv)
records 138 exact-name replacements from official RetroBat resources and these
11 missing individual variants across the entire regular collection:

| Missing individual PNG | Available behavior |
| --- | --- |
| `systems/dice.png` | Generic RetroBat fallback; no dedicated DICE artwork |
| `systems/dice-90.png`, `systems/dice-270.png` | No dedicated rotated DICE artwork |
| `systems/pc.png` | Generic fallback; no exact PC PNG |
| `systems/snes_msu-1.png` | Generic fallback; no exact MSU-1 PNG; normal SNES exists |
| `systems/fbneo-90.png`, `systems/fbneo-270.png` | Normal FBNeo exists; no exact rotated variants |
| `systems/mame-90.png`, `systems/mame-270.png` | Normal MAME exists; no exact rotated variants |
| `systems/triforce-standalone.png` | Normal Triforce exists |
| `systems/xbox-standalone.png` | Normal Xbox exists and is used by the existing standalone lookup |

PSP, DS, PS3, Wii U and Amiga variants are present in `default_unglazed`.
The owner's Xbox-preview acceptance applies to that original RetroBat Xbox PNG,
not to a live Xemu/compositor test. Generic/base fallback is not a claim that a
missing dedicated or rotated variant has been recreated. No old art fills gaps.

## Host shader provider

Future stages contain only the small curated catalogue, mappings and notices;
they do not copy the full Libretro collection or its textures into the AppImage.
The old pinned full shader tree/Gold artifact remain untouched as references.
The distribution's optional `libretro-shaders-slang` package supplies shaders,
includes, frames and LUTs under
`/usr/share/libretro/shaders/shaders_slang` on the verified Arch package.
Discovery also checks supported alternative layouts and the installed package's
own file list rather than assuming a user's mountpoint or copying a network tree.

The existing confirmed optional host-software plan offers this package on Arch,
Garuda and CachyOS, with German/English labels. No package was installed during the initial implementation phase; the owner
subsequently approved the three-host installation recorded below. The official package was downloaded and extracted into disposable project
state for read-only testing. GPG verification against the existing Arch keyring
confirmed Maxime Gauduin's signature.

Verified package: `20260620.024025.g8ec4c82cf61a-1`.
SHA-256: `027bfb1362cc1425f832b254d2ef95e86e8fd74a8cc16403eb731d874653529b`.
[Official package](https://archlinux.org/packages/extra/any/libretro-shaders-slang/)
and [file list](https://archlinux.org/packages/extra/any/libretro-shaders-slang/files/).
The package has 2,526 presets; Embercade offers 26 curated entries, not an
unvalidated menu containing every arbitrary upstream preset.

Existing IDs retained: NewPixie, CRT EasyMode, CRT Lottes, CRT Lottes Fast,
ZFast CRT, Mega Bezel, Sharp Bilinear, LCD Grid, PSP/GBA/GBC Color, Advanced AA,
Bevel and Simpletex. Additional RetroBat-inspired mappings: CRT Royale, CRT Geom,
ScaleFX, ScaleFX AA, ScaleFX Hybrid, NTSC S-Video, NTSC VCR, TV Out, Game Boy LCD,
GBA/GBC LCD and Color, Flatten Glow. See `resources/shaders/catalog.toml` for
exact official paths and original component notices. No Windows .fx preset or
missing RetroBat shorthand path is offered as though it were a Linux preset.

Each session and game launch validates the transitive preset/include/texture/LUT
graph and generates only available menu entries in private runtime state. Read-only
binds make the same host provider accessible inside the production namespace.
User shader directories and manual backend/effect selections are retained.
Removed/incomplete package or unsupported backend: the existing localized launch
notice explains that the selected effect was skipped; the game starts without
it and the saved choice is not rewritten. Both the modern SystemConfig and
legacy configgen loaders handle a missing selected mapping. None remains off,
including stale enabled state. Existing Vulkan preference and core-specific
OpenGL exceptions are unchanged. Mega Bezel keeps its noBezel convention.

## Licensing and independent questions

The owner adopts CC BY-NC-SA 4.0 for the RetroBat collection and explicitly
excludes the old captured collection from the next payload. Record that project
decision without presenting it as a newly received individual artist message.
Keep all embedded author credits/individual notices, including ND notices, with
their original scope. The next stage includes the official README, collection
receipt/lock, project resource notice and full unchanged CC BY-NC-SA 4.0 text.
The historical 302/35-file audit remains historical evidence, not the new shipped
resource inventory or a newly repeated blanket blocker.

Host Libretro components retain their individual upstream terms. Arch's package
metadata GPL label does not relicense every shader/texture. Already resolved
NewPixie frame, Simpletex paper and Pokefan531 LUT credits stay resolved; the
small catalogue now reflects those findings. New mappings retain upstream
notices through the unmodified official host package. Carbon's completed credit
item stays completed. Own-code PolyForm/GPL boundary review and permission to
distribute a personal RetroAchievements Web API identity remain separate. No
new blanket software grant or public-release clearance is activated.

## Validation and remaining manual acceptance

Final automated results: 801 tests, 796 successful and five expected opt-in
skips; 25 GTK checks and 52/52 structural routes. Runtime smoke, shell syntax,
resource preparation and diff checks pass. The credential-free development
frontend compiles successfully with the new menu patch. This is a compiler
check, not a new private/public AppImage. A pre-existing incomplete one-operand
copy command in UI preparation was removed so fresh source preparation succeeds;
no RetroAchievements authentication code or secret input changed.

The official package passed all 26 complete dependency graphs. Real read-only,
private 120-frame runs passed GB/SNES/GBA/N64/3DO with effects off, plus all
26 selected shaders (31/31); shader passes compiled and frames were produced.
A further 13/13 Game Boy runs generated/enabled overlays for all regular sets
and returned zero after 120 frames. These use generated test display geometry,
not native Xemu/PCSX2 visual acceptance. The production namespace probe found
all 26 mappings, readable host includes/textures, writable isolated user-shader
state and read-only provider/template mounts. No full shader tree was copied
into that install-shaped test prefix. The real host filesystem/media were
mounted read-only for the emulator probes; synthetic fixtures were never booted. Functional fixtures
never execute synthetic ROMs/cores. Real frame-limited tests use existing legal
content read-only, private configuration/saves and a read-only host filesystem;
no normal user profiles, driver settings or installed images are changed.

| Host/session | Prepared checks | Remaining manual acceptance |
| --- | --- | --- |
| MainRig / Garuda KDE Wayland / AMD | Host-package graph, native route/selection tests, real 120-frame RetroArch runs | New candidate menu, 13-set appearance, Xemu/PCSX2 geometry, game/exit/frontend return |
| WohnzimmerPC / CachyOS Gamescope / AMD | Existing separate compositor route and test checklist retained | Optional package detection/install, Gaming Mode selection, RetroArch + standalone appearance/return; no SteamOS Manager/session changes |
| EmbercadeLaptop / Garuda KDE / NVIDIA | Same provider/menu/setup regressions prepared | Package detection/install, effects, game launch, 16:10 known limitation; no driver changes |

After the owner started both hosts, read-only SSH preflight succeeded. The
same provider-discovery/dependency code initially reported no installed shader
provider on either host. Following the owner's subsequent explicit approval,
`libretro-shaders-slang` 20260620.024025.g8ec4c82cf61a-1 was installed on all three
PCs. Every transaction returned zero after hooks; all 26 complete preset graphs
now resolve on each host. No extra dependency was required. The optional installer
continues to offer this package on fresh hosts where it is missing. Existing Gold images still contain their embedded
shaders and remain unchanged. Laptop has gtk-layer-shell 0.10.1-1, python-cairo
1.29.2-1, vlc-plugin-ffmpeg 3.0.24-1 and RetroArch 1.22.2-5. Wohnzimmer has
python-cairo 1.29.2-1.1, vlc-plugin-ffmpeg 3.0.24-1.1 and RetroArch 1.22.2-5;
layer-shell is not required by its separate Gamescope route. Cairo is importable
on both. Both active image hashes still match the accepted Gold SHA below.
The later authorized package installation is the only remote system change;
profiles, drivers, sessions and images remain unchanged. They are not claimed
visually tested. Known laptop 16:10 cropping/proportions remain documented;
MainRig/Wohnzimmer 16:9 renderer guards remain unchanged.

For the eventual candidate: inspect None and a chosen shader, switch games,
check global/system/game settings, test each used regular bezel, Xemu and PCSX2,
Start + Guide, normal mouse input and return to the same frontend. Check no effect
is enabled by default and simulate an unavailable optional shader provider.
The owner must first accept the technical changes and explicitly lift the
AppImage hold. Then build exactly one private candidate with manifest/SHA-256;
keep the accepted Gold and all existing installations until separately approved.
No push or publication follows implicitly.


## Receipts and rollback

Ignored receipts: `.work/retrobat-integration-2026-10-27/` contains the final
regression summary, 52-route proof pointer, shader/bezel GPU results and logs,
namespace result, remote read-only package/image preflight and compiler log.
The generated collection records all integration links. The code/catalogue and
path-coverage CSV are versioned; package archives, binaries, test content,
screenshots and credential material are not.

Accepted Gold image SHA-256 remains
`b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`.
The repository canonical image and both remote active images were checked.
Its source identity remains `935eacf508ab18c369091d8bfbd9023b0d9ed7fd`.
No current installation was replaced. A precompile frontend/identity reference
was saved inside ignored project state; the newly compiled development frontend
is explicitly credential-free and must not be deployed as the accepted private
candidate. The existing build authorization/identity checks require the proper
private production build after the owner lifts the hold.


## System-aware choices and MainRig acceptance

The owner confirmed the initial shader/None/exit tests and then requested that
per-system selection show only resources available for that system. New native
policy code checks the matching PNG+INFO pair, omits generic-preview-only choices,
and merges exact canonical image/layout aliases while preferring the source set.
Different images or layouts remain distinct; there is no new content-hash audit.
Global selection retains all 13 regular sets. One matching set remains selectable
with None/Auto. Merely opening a filtered list does not rewrite a hidden saved
choice, and the legacy consoles selection is normalized only for display.
Five native C++ tests cover PSP's unique choice, global completeness, missing
layouts, alias ownership and preservation of distinct layouts. Full regression:
806 tests (801 passed, five intended skips). The updated native frontend compiles.

The separate test originally omitted Xbox's existing EEPROM/HDD and PSP's asset
reference. These were missing test inputs, not evidence of a broken normal
installation. They were supplied as private test copies/read-only asset binds.
Xbox and PSP then passed pinned launch-generation preflight; the owner confirmed
actual starts and the corrected PSP menu. Original EEPROM/HDD, settings and media
were preserved. The owner explicitly authorizes the new private AppImage and
five existing image-path replacements after this acceptance. Keep the existing
private application/Web API build mechanisms; no public release or push follows.

# Current public source preparation

The current public candidate is prepared from the clean standalone project
export, with a matching complete source/notice kit. The delivered manifests
and BUILD_INFO identify its exact source and hashes. All current patches and
public helper headers are included; older patch counts/receipts below are
historical. Publication and upload remain unperformed and require approval.

The previous license/source research is reused. No completed bezel, shader,
theme or authorship investigation is reopened. Original component terms and
LGPL rebuild/replacement access stay intact.

## Earlier delivery preparation and frozen evidence

# Source and notice delivery for Embercade 1.0

The remaining delivery preparation was completed locally on 28 October 2026
against the actual private adapter payload. It does not reopen the completed
RetroBat, host shader or Carbon provenance work. No new license conflict or
denial of permission was found in this follow-up. The provider decision for the
personal RetroAchievements Web API identity has now received a concrete
recommendation: use each user's own key. [The targeted follow-up](POLISH_1_0_PRIVATE.md#per-user-web-api-recommendation--28-october-2026)
records the supplied response and official docs. The subsequently approved
[runtime implementation](RETROACHIEVEMENTS_USER_KEYS.md) is now automatically
verified. Manual three-host acceptance is pending; no shared key is approved
for public distribution. The frozen kit below still identifies its original
private binary and legal supplement.

## What is prepared

The final local source kit is under `dist/license-preparation-2026-10-28/final/` with its
own manifest and SHA-256 file. It identifies the private binary by hash and
retains its exact source commit, rather than claiming it was rebuilt from newer
documentation. It contains 33 original source archives, an exact Embercade
source snapshot, a separately identified current legal supplement, fully patched
Batocera/EmulationStation source trees and all indexed supplemental notices.
The archive's `SHA256SUMS` covers its regular source/notice files. It is local
preparation, not a public download or a three-year written offer.

Verified archive: `Embercade-1.0-sources-and-notices.tar.gz`, 410,843,235 bytes,
SHA-256 `6b4d73aa8a08d5d9552af9e97b960489daffa9078a88229e0cfa121ac477ec7d`.
Its manifest identifies the legal supplement at `955fe49` and the binary source
at `d8e6ca6`; it does not claim the later receipt was built into the binary.
All 1,809 archived regular-file checksums passed. All 314 installed Batocera
Python sources match the archived modified sources, with none missing or changed.
All four checked protected canonical/installed image hashes remain unchanged.
The 35 archive entries comprise 33 original upstream archives plus the exact
Embercade source and committed legal supplement. Earlier attempts under the
parent directory are preparation history, not the final kit.

Inputs and original notices are recorded in
[the source lock](../compliance/sources.lock.json) and
[notice lock](../compliance/notices.lock.json).
[Rebuilding instructions](../compliance/REBUILDING.md) cover source installation,
dynamic library replacement and rebuilding/relinking the static AppImage loader.
The preparation tool uses immutable Git archives and verified source archives;
it never captures an unfiltered private build workspace or credential header.
Original upstream commercial, modification and debugging rights remain intact.

| Actual delivered component | Source / notice disposition |
| --- | --- |
| Six Batocera Python distributions, UI builder and generated descriptors | Pinned upstream Python and selected core/emulationstation/emulator package sources; complete Embercade patches applied using the existing build recipe, with results recorded; original GPL/LGPL/file exceptions and build/install inputs retained |
| EmulationStation and its compiled-in dependencies | Complete pinned source, all eight patches and four public helper headers; nested MIT/BSD/zlib/public-domain notices preserved separately from the frontend's own MIT notice |
| FreeImage 3.18.0 | Complete original source, embedded codec sources, original FIPL/GPL alternatives, LibRaw copyright/LGPL/CDDL and other embedded library notices; exact compile command recorded |
| SDL2_mixer 2.8.2 | Complete original source, zlib notice and original dr_flac/minimp3/stb_vorbis headers; feature choices remain the existing recipe's choices |
| 23 other installed Python distributions | Matching sdists for every actual version, including pip, pyudev and pathspec; installed original dist-info/vendor notices retained |
| pip's vendors | Original pip vendor tree/notices retained; certifi 2026.6.17 source separately supplied for its MPL certificate bundle; no blanket MIT assertion for all vendors |
| Pillow 12.3.0 native wheel | Original aggregate copied unchanged, with 22 dependency notice sections; all 18 bundled `.so` library paths map to those sections, including static subcomponent notices |
| uvloop's static libuv | Original MIT and LICENSE-extra notices added; uvloop sdist includes its vendor source; externally maintained ISC/BSD parts retain the additional notices |
| PyYAML's static libyaml | Observed library version 0.2.5; matching source and original MIT notice added |
| AppImage type-2 runtime / static libfuse | Complete MIT runtime source, LGPL 2.1 libfuse 3.15.0 and squashfuse 0.5.2 sources, actual libfuse patch, build recipes and retained static-library notices; source form enables rebuilding/relinking the work using libfuse |
| Host interpreter, desktop/GPU stack, libVLC/plugins, emulators, cores and shader package | Installed separately by their providers; their binaries are not redistributed in this AppImage |

FreeImage's own FIPL alternative is used without relicensing its embedded
libraries. LibRawLite's LGPL 2.1 is respected independently. FreeType uses its
FTL alternative and zstd its BSD alternative; the unmodified alternatives are
retained. This software is based in part on the work of the FreeType Team.
Native wheel source notices do not imply that every permissive dependency
requires source publication. All relevant copyleft source/replacement paths
are provided; there is no blanket noncommercial condition on third-party rights.

Pillow's wheel already carries the AOM, Brotli, bzip2, dav1d, FreeType,
HarfBuzz, LCMS2, libavif, libjpeg, liblzma, libpng, libtiff, libwebp, libyuv,
OpenJPEG, Raqm, Tcl/Tk, Xau, XCB, XDMCP, zlib and zstd notices. Those sections
can include static or platform-specific sources; their presence is not a claim
that every listed optional library is a separate Linux shared object. Its
18 actual bundled libraries are covered by that preserved aggregate.

## Fonts and small audio resources

The actual font name tables and their original copyright/license strings are
preserved in [EMBEDDED-NOTICES.txt](../LICENSES/third-party/fonts/EMBEDDED-NOTICES.txt).
The corresponding OFL, Apache and Ubuntu license texts now accompany them.
No font bytes or audio files were changed.

| Payload path, relative to `resources/emulationstation` | Attribution / retained terms |
| --- | --- |
| `resources/DroidSansFallbackFull.ttf` | Google Corporation, 2006; embedded Apache 2.0 notice |
| `resources/opensans_hebrew_condensed_light.ttf` and `resources/opensans_hebrew_condensed_regular.ttf` | Open Sans Hebrew Condensed; Google, 2011, Yanek Iontef, 2012–2013; Light embeds Apache 2.0, Regular identifies the same family/version but lacks its own rights name fields; retain the family attribution and Apache text, not a new unknown-license classification from missing fields |
| `resources/ubuntu_condensed.ttf` | Canonical Ltd., 2011; original Ubuntu Font Licence 1.0 from the pinned frontend |
| `resources/fontawesome-webfont.ttf` | Font Awesome 4.3.0, Dave Gandy, 2015; original release font grant OFL 1.1, separately from its MIT code and CC documentation |
| `resources/Rubik-Regular.ttf` | The Rubik Project Authors, 2015; embedded OFL 1.1 |
| `resources/Vazirmatn-Regular.ttf` | The Vazirmatn Project Authors, 2015; embedded OFL 1.1 |
| `resources/PyeojinGothic-Medium.ttf` | Suh Ji-hwan / 서지환, 2025; embedded OFL 1.1; original copyright is preserved with the full standard license |
| `themes/es-theme-carbon/art/fonts/Cabin-Bold.ttf` and `Cabin-Regular.ttf` | The Cabin Project Authors, 2018; embedded OFL 1.1, with the original project OFL notice retained |
| `themes/es-theme-carbon/art/fonts/players.ttf` | Internal name rvgm, original RVGM notice; Fontello is the recorded generation tool, not proof that its software license covers this font. No separate conflicting font notice was identified; retain the supplied Carbon project grant and credit rather than inventing an OFL grant |
| `themes/es-theme-carbon/art/sounds/scroll.wav` | Supplied Carbon resource under its existing project grant; original theme authors/readme retained, with no separate contrary sound notice identified |
| `resources/checksound.ogg` | Supplied frontend resource; preserve the pinned project's MIT notice and contribution history, with no separate contrary sound notice identified |

The last three scope statements are reasoned uses of the applicable repository
grant, not new individual artist declarations. A missing per-file text is not
itself a conflicting license where the containing project already supplies its
grant. Carbon's original mixed 2.0 heading / 4.0 body remains untouched and
documented; its attribution is not reopened. Foreign logos/trademarks retain
their rights and are not assigned Embercade CC terms.

## Remaining publication steps

For the inspected candidate there is no outstanding identified source archive
or notice gap after this preparation. The AppImage loader's original unpinned
Alpine package revisions remain a reproducibility limit, not a newly established
license conflict; libfuse's exact source/patch and the complete loader source
are supplied, without demanding identical rebuilt hashes.

Automated validation: 828 tests completed (823 passed, five intentional native
opt-in skips), including isolated GTK checks and the 52-route structural matrix.
Runtime smoke passed. After completing the final supplemental notice copies,
the 63 targeted source/license/production/AppImage checks passed again. This is
automated source/delivery validation, not a new manual gameplay or display
acceptance on any of the three hosts. The source-kit receipt separately records
archive verification and unchanged protected image hashes.

This does not authorize releasing the current private image. After the owner
resolves RetroAchievements, the eventual public build must contain these legal
files, use the approved provider arrangement and have a source kit rebound to
its actual manifest. Check that final artifact and make its matching sources
available alongside it when publication is expressly approved. This is a final
delivery step, not a request to repeat the old artwork audits. Privacy/large-file
publication hygiene and the owner's manual gameplay acceptance remain separate
from these licensing assignments. No build, deployment, host change, push or
publication was performed during this completion.

# Third-party notices

Current assignment: [LICENSE](LICENSE), [component map](docs/LICENSE_COMPONENT_MAP.csv)
and [licensing guide](docs/LICENSING_1_0.md). Original foreign copyrights,
notices and permission texts remain unchanged. No Embercade PolyForm or CC
grant replaces them; commercial rights granted upstream remain intact.

## Batocera, Configgen and EmulationStation

Batocera-team code has an express LGPLv3 default with upstream exceptions.
Configgen has an explicit GPL package declaration, and individual source files
can specify different terms. The pinned Buildroot COPYING is retained, but is
not a license assignment for every package or asset. The
[component-by-component correction](docs/BATOCERA_COMPONENT_LICENSES.md) records
the exact package paths, source pin, GPL hook exception and evidence.

Batocera EmulationStation at `1750dded8c0fdff70630026f756a69fcad0bb995` retains
its MIT notice: Copyright (c) 2014 Alec Lofquist. Original Embercade contributions
to the frontend and other upstream integration use a compatible MIT grant;
foreign context and independently licensed nested dependencies retain their
own terms. The separate backend does not import the Embercade client.

## RetroBat decorations

Source: [RetroBat-Official/retrobat-bezels](https://github.com/RetroBat-Official/retrobat-bezels),
commit `5ce1f6ed32eb9f3df8ae14483afc4d1e3ef35d65`.
The owner adopts RetroBat's published CC BY-NC-SA 4.0 project basis for this
collection. The [published project notice](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/license.txt)
and the collection's original README remain source references. Original artist
credits, watermarks and individual notices, including ND notices, remain in
place with their own scope. This is not a relicensing of foreign artwork.

The new payload contains the official collection, technical Linux link/legacy
aliases and an adaptation receipt, with original image pixels retained. It
contains no merged old captured console collection. The historical 302/35-path
reports concern that previous payload and are not open blockers for this
replacement collection. No new all-PNG audit or artwork change was performed.
See [resource integration](docs/RETROBAT_AND_HOST_SHADERS.md) for coverage gaps.

## Host-provided Libretro shaders

The current image contains only original small mappings/catalog metadata.
Actual programs, presets, frames and LUTs come from the official optional
`libretro-shaders-slang` host package, normally at
`/usr/share/libretro/shaders/shaders_slang`, under their original mixed terms.
No complete Slang/GLSL tree or shader texture is bundled in this candidate.
The old locks/audits are provenance history, not the host package's version claim.

Sources remain [Libretro Slang](https://github.com/libretro/slang-shaders) and
[GLSL reference](https://github.com/libretro/glsl-shaders). Existing identified
credits are retained: Mattias Gustavsson (2016), hunterk — NewPixie code/frame,
MIT OR Unlicense; Stephen Gilbert/Subtle Patterns, jdgleaver and mudlord —
Simpletex paper texture, CC BY-SA 3.0 separately from shader code; Pokefan531
and Flávio Sousa — identified public-domain handheld LUT data. Those findings
are not a uniform grant for every host shader. Previously recorded legacy-code
notice questions are historical external-source findings, not missing grants
for shader programs bundled by the new image. Shaders remain off by default.

## Themes

Only Carbon is shipped. Source: `fabricecaruso/es-theme-carbon`, commit
`b921e1734d88d6bc7b9e8cb97dd8f8b91ba2058a`.
Carbon Theme (c) Fabrice Caruso (CC BY-NC-SA Licence), originally based on
Eric Hettervik/Rookervik's Carbon and Nils Bonenberger's Simple Theme; the exact
theme additionally credits maioni. Its original header, readme and legal text
are retained in the theme and central notices. Origin, theme-license
identification and author credit are resolved.

The original readme has a 2.0 heading but 4.0 legal body. This inconsistency is
recorded, not silently rewritten or used to invent a new license grant. Foreign
logos/trademarks and separately licensed fonts/audio keep their own rights.
The recorded embedded-resource paths are `art/fonts/Cabin-Bold.ttf`,
`Cabin-Regular.ttf`, `players.ttf` and `art/sounds/scroll.wav`; the own CC grant
does not relicense them. Cabin's OFL notice/text and the actual fonts' original
copyrights now accompany them under `LICENSES/third-party/fonts`. The internal
RVGM player font and supplied scroll sound retain the Carbon project grant;
no separate conflicting notice was identified. Fontello identifies the font
generation tool, not an automatic license for the generated font. The
[delivery review](docs/THIRD_PARTY_DELIVERY.md) records the precise scope.
Downloaded user themes are not shipped by Embercade.

## Native libraries, Python packages and AppImage runtime

FreeImage 3.18.0 and SDL2_mixer 2.8.2 come from the exact source archives/hashes
in `runtime/frontend-libs.lock`. Their source/build notices, original FreeImage
GPL2/GPL3/FIPL alternatives, SDL2_mixer zlib license and original DR FLAC,
minimp3 and stb_vorbis decoder-license headers accompany the built libraries
under `share/embercade/licenses`. These are not Embercade NC components.

Python dependencies retain their original distribution/vendor notices.
[Runtime metadata](docs/LICENSE_RUNTIME_METADATA.csv) records the actual
29-distribution snapshot and its completed source/notice preparation. Pillow's
original wheel aggregate includes 22 dependency notice sections covering its
native codec/font/X11 libraries and static subcomponents. It is retained
unchanged; Pillow is not uniformly MIT-CMU. Libuv's additional MIT/ISC/BSD
notices, original embedded libuv/FreeImage source notice blocks, and libyaml's
MIT notice are now supplied separately, as are the
frontend's nested dependency and font notices. FreeType uses its FTL alternative;
this software is based in part on the work of the FreeType Team. Zstd uses its
BSD alternative; FreeImage's own FIPL alternative does not replace LibRaw's
LGPL 2.1 or any other codec's original terms. The complete source and rebuild/
replacement records are in the [delivery review](docs/THIRD_PARTY_DELIVERY.md).
The host CPython interpreter, GPU stack and desktop libraries are separately
provided rather than repackaged.

The AppImage runtime and static-library notices remain under
`packaging/appimage/licenses` and the payload's `packaging-notices`; the pinned
build lock and notice index record their source identities. Full covered source,
modification, library-replacement and notice obligations remain applicable.
[Source access](docs/SOURCE_ACCESS.md) distinguishes the completed local source
kit from actual public delivery, which still requires express approval.

## Own material and excluded user content

The original independent Embercade client uses the scoped PolyForm grant;
original prose uses CC BY-NC-SA 4.0. The owner confirmed Canva AI creation of
the branding on 27 October 2026; [the origin record](docs/BRANDING_ORIGIN.md)
resolves the earlier missing-origin entry. Its CC grant covers rights actually
held, with no exclusive AI-copyright or foreign/trademark ownership claim.

ROMs, BIOS, firmware, keys, saves, emulator binaries, Libretro cores and user
provider AppImages are not release assets supplied by Embercade. Their owners
and providers retain their rights. API credentials and private build inputs are
not source/notice assets. The current RetroAchievements identity remains for
the explicitly private owner build; no public-distribution approval is inferred.

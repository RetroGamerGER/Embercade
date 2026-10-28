# Source access and redistribution

## Embercade 1.0 public source delivery

The [public release](https://github.com/RetroGamerGER/Embercade/releases/tag/v1.0.0) provides the AppImage together with
`Embercade-1.0-sources-and-notices.tar.gz`, its manifest, checksums and a clean
project Git bundle. The complete archive includes covered upstream sources,
actual modifications, build/install inputs, notices and LGPL replacement
instructions; the automatic GitHub source ZIP alone is insufficient.

The binary's exact project source is
[`cb00b093`](https://github.com/RetroGamerGER/Embercade/tree/cb00b093ff0e87d2462ee060bb4b7717afda43dc).
The release tag also contains the final publication-documentation update.
Image/source manifests retain the original preparation-time state; the release
BUILD_INFO identifies the publication separately. No shared personal
RetroAchievements key is distributed. The known laptop 16:10 bezel limitation
remains documented.

The original private repository and older private builds remain separate.
Only the sanitized root and publication documentation appear in public history.

## Existing source-delivery contract and historical receipts

The following records describe earlier private preparation, not the current
public release. Its complete matching source delivery is linked above.

The matching source kit and supplemental notices are prepared locally for the
frozen private adapter candidate. This is not an issued three-year written
offer or a claim that a private GitHub URL is publicly accessible. Nothing has
been uploaded or published. The [delivery review](THIRD_PARTY_DELIVERY.md) and
[preparation inputs](../compliance/README.md) describe the completed local work.

The project source is [RetroGamerGER/Embercade](https://github.com/RetroGamerGER/Embercade).
For a public binary, publish the exact manifest's Embercade source commit,
its complete patches, build/install scripts, locks and applicable notices,
together with the complete corresponding upstream source versions. An automatic
Embercade GitHub source archive alone omits external sources and is insufficient.
Private credential input files and personal/user content are not source assets.
Do not archive an unfiltered build workspace that contains credential headers.

| Covered component | Exact source reference / build and notice record |
| --- | --- |
| Batocera runtime and UI builder | [9d2f7fc](https://github.com/batocera-linux/batocera.linux/tree/9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48), `upstream.lock`, all `patches/batocera-launch` and `scripts/runtime-prepare`; retain individual terms and original COPYING |
| Batocera EmulationStation | [1750dde](https://github.com/batocera-linux/batocera-emulationstation/tree/1750dded8c0fdff70630026f756a69fcad0bb995), all `patches/emulationstation`, included public helper headers and `scripts/ui-build`; embedded libraries/fonts keep their original notices |
| Backend | Complete `integration/batocera` source and MIT notice, already included beside the installed client |
| FreeImage 3.18.0 | `runtime/frontend-libs.lock` source URL/SHA and `scripts/frontend-libs-prepare`; original GPL2/GPL3/FIPL texts and build notice already in the payload |
| SDL2_mixer 2.8.2 | Same lock/recipe, original zlib notice and retained decoder-license source headers in payload |
| Python runtime packages | Exact `runtime/requirements.lock`, all 23 matching non-Batocera sdists, separately supplied certifi source, original installed/vendor notices, complete Pillow wheel aggregate and added libuv/libyaml notices; `docs/LICENSE_RUNTIME_METADATA.csv` records the completed preparation |
| AppImage runtime/static libraries | `packaging/appimage/build.lock` and `packaging/appimage/licenses/index.json`; retain the pinned runtime's notice/source record and every static dependency's terms |
| RetroBat collection | `runtime/decorations.lock`, upstream source README, preserved credits and collection adaptation receipt; no previous captured art |
| Carbon | Exact source pin and original readme in `docs/LICENSING_1_0.md` and central payload notices |
| Host-only shaders/emulators/Python/GPU stack | Separately installed host components, not binaries redistributed in this AppImage; their own providers handle their distribution terms |

For an Internet binary release, make complete corresponding covered sources
available alongside it by the applicable license's permitted method. Include
actual modifications and build/install inputs, not merely a moving master link
or a pointer that omits code carried in a native wheel. Preserve LGPL library
replacement/relinking opportunities and any required notices; do not impose an
NC condition on those rights. The read-only application layout is a runtime
policy, not permission to deny recipients their upstream modification rights.

Current local set: `dist/license-preparation-2026-10-28/final/` contains the source/
notice kit, manifest and checksum. Original archives, complete modified covered
sources, patches, build/install inputs and LGPL replacement/relinking
instructions are provided. The kit retains binary source
`d8e6ca6f194e24d21d1bf8e80e8449f0310aeddd` and a separately identified legal
supplement; the private image was not rebuilt. No identified source archive or
notice gap remains for that inspected candidate. The original loader recipe's
unfixed Alpine APK revisions remain a reproducibility limit, not a proven
missing license or a demand for identical rebuilt binary hashes.

The private candidate and manifest remain explicitly private. For any approved artifact, bind it to its actual sources/notices and offer
its matching kit alongside the binary when publication is expressly approved. That future delivery cannot be claimed as performed
merely because the local archive is complete. Publication/privacy hygiene and
the owner's manual function tests remain separate.

## New per-user RetroAchievements candidate

The later private candidate from `010f5e857e9bdda02faebd621ca14977961c362b` has
its own matching sources under `dist/private-user-api-2026-10-28/source-kit/`.
[The current key guide](RETROACHIEVEMENTS_USER_KEYS.md#separate-private-acceptance-candidate)
records the image/source SHA-256 and verification. That kit includes the ninth
frontend patch and new MIT helper; the d8e6ca6 kit above stays frozen for its
original image. Neither source kit nor binary has been published or pushed.

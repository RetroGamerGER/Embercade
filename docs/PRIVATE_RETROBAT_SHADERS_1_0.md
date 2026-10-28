# Private RetroBat / shader candidate — 27 October 2026

The owner accepted MainRig's shader/None/exit tests, then the corrected Xbox/PSP
starts and per-system bezel menu, and explicitly requested building and replacing
the image on all three owner PCs. This lifts the earlier build hold for this
private candidate. No push, public release, tag or visibility change occurred.

## Artifact

- Image: `dist/private-retrobat-shaders-2026-10-27/Embercade-1.0-Private-RetroBat-Shaders-x86_64.AppImage`
- Manifest: same directory, `Embercade-1.0-Private-RetroBat-Shaders-x86_64.manifest.json`
- Checksum: same image filename plus `.sha256`
- SHA-256: `938df3ab6a33de069baab4b8f9dfac876693a9efaa40f4b952d0519c916027d5`
- Exact source: `87cc521f58e0cc2b3e0db51f8dfb1300e7c219bf`; source tree clean at packaging.
- Frontend authorization: embedded ScreenScraper application identity and existing
  private owner RetroAchievements Web API build mechanism; distribution is
  explicitly `private-owner-test-only`. No new authentication architecture,
  personal-login dialog, credential source edit or public permission is implied.

The image contains only the official pinned RetroBat collection and small host
shader mappings. No old captured bezel collection or full Libretro shader tree
was copied into it. Original notices and prepared CC text accompany the resources.
The optional official shader package is installed on all three hosts; effects
remain off by default and saved manual graphics/shader settings are preserved.
Details, exact 11 missing dedicated variants and original pins are in the
[integration report](RETROBAT_AND_HOST_SHADERS.md).

## Verification

- Full regression: 806 tests, 801 passed and five expected opt-in skips; 52/52
  structural routes, native C++ menu-policy tests and runtime smoke pass.
- Native frontend compilation and the private build-identity checks pass.
- Extracted final AppImage passes the AppDir/payload identity audit; its resource
  shader root contains zero `.slang`/`.slangp` files. The runtime uses the host
  provider and all 26 complete preset/include/texture graphs are available.
- Final packaged runtime: actual private read-only Game Boy runs with None and
  NewPixie, 120 frames each, zero exit and captured frames; the chosen effect
  compiles. This supplements the prior 31 shader/default-system and 13 regular
  bezel overlay runs; it is not full gameplay/controller acceptance on every host.
- The installed AppImage's `--help` exits zero on all three hosts in disposable
  profiles. Every installed file/sidecar and every rollback copy is hash-verified.
- Normal configuration, frontend settings/input, protected SSH key, Desktop
  entries and Steam shortcut files/routes match their predeployment hashes.
  No firmware, EEPROM, saves, original ROM/media, driver or session was reset.

The isolated MainRig test initially omitted the existing Xbox EEPROM/HDD and PSP
assets reference. Private copies/read-only binds fixed those test inputs; the
owner confirmed actual starts. These were not missing data in the normal setup.
Per-system/game menus now show actual matching image/layout resources and merge
exact symlink aliases; PSP has Default Unglazed once, plus None/Auto. Global
selection retains all 13 regular sets. Opening a filtered list preserves saved
preferences; legacy consoles choices continue to resolve to RetroBat resources.

## Installed paths

All five active image copies have the SHA above. Existing filenames and start
routes were retained; manifests/checksums and applicable ownership receipts
were updated atomically with verified backups.

| Host | Existing path retained | Copies |
| --- | --- | ---: |
| MainRig | `~/AppImage/Embercade-1.0-Release Candidate-x86_64.AppImage` | 1 |
| MainRig | `~/.local/share/embercade/application/Embercade.AppImage` | 1 |
| EmbercadeLaptop | `~/AppImages/Embercade-1.0-AutoGraphics-x86_64.AppImage` | 1 |
| EmbercadeLaptop | `~/.local/share/embercade/application/Embercade.AppImage` | 1 |
| WohnzimmerPC | `~/Applications/Embercade/Embercade-1.0-x86_64.AppImage` | 1 |

No emulator/frontend was active at the guarded exchange. Unrelated applications
were not stopped. The older Wohnzimmer pre-polish image was not a target.

## Rollback and acceptance limits

Each host retains verified originals and its `deployment.json` under:

`~/.local/state/embercade/image-backups/retrobat-shaders-2026-10-27-938df3ab/`

The receipt records exact original filenames, SHA values, modes and backups for
the images, sidecars and applicable ownership metadata. Recovery should restore
that complete recorded set with the frontend/emulators stopped; restoring only
an image without its matching ownership metadata would leave a stale record.
The prior Gold image SHA remains
`b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`.
The canonical old private artifact and its Git/source history remain available.

MainRig's manual functional acceptance preceded packaging. Final package tests
above are recorded separately. Laptop/Gamescope visible gameplay, aspect/overlay
checks and controller return remain for the owner in the coming days. The known
laptop 16:10 limitation is unchanged. No new three-host visual acceptance,
network-provider/API interaction, public redistribution right or release is
claimed from CLI/hash/dependency verification.

Ignored receipts: `.work/retrobat-integration-2026-10-27/` and
`.work/deploy-retrobat-shaders-2026-10-27/`. No secrets or loose credential files
were distributed, logged, committed or placed in the artifact manifest. As before,
compiled private frontend authorization is extractable and owner-private only.

# Private adapter candidate — 27 October 2026

Later on the same date the owner confirmed Canva AI creation of the branding;
[the current origin record](BRANDING_ORIGIN.md) resolves the earlier missing
answer. This documentation correction does not rebuild or alter the candidate
or its embedded source-revision snapshot.

The owner approved the targeted backend separation, scoped grants and a separate
private test version. This candidate was built and checked without replacing
Gold, the accepted RetroBat/shader image, existing installed images or shortcuts.
The owner performs the visible tests on the three reference systems.

## Artifact identity

- Image: `dist/private-adapter-2026-10-27/Embercade-1.0-Private-Adapter-x86_64.AppImage`
- SHA-256: `a26055ca0aa3e921de3e559af3c5a32337de92f1826c3e4e549bf7781e79ae87`
- Size: 414280184 bytes.
- Exact source: `d8e6ca6f194e24d21d1bf8e80e8449f0310aeddd`; source tree clean at packaging.
- Manifest: same directory, `Embercade-1.0-Private-Adapter-x86_64.manifest.json`.
- Checksum: same image filename plus `.sha256`.
- Authorization remains `embedded` ScreenScraper and `private-owner-web-api`
  RetroAchievements, explicitly `private-owner-test-only`. No credential source
  was changed or loose secret distributed. Public permission is not inferred.

Source changes are in local commits `8bba590` and `d8e6ca6`; later documentation
commits do not change this artifact's exact source identity. No push, tag,
release, visibility change or deployment occurred.

## Changes and licensing

[The adapter report](ADAPTER_SEPARATION.md) describes the four executable
operations and both UI-builder modes. Existing settings, their global/system/
per-game precedence, frontend menu entries, controller paths, rendering and
emulator functionality are retained. The frontend executable itself is unchanged
from the accepted RetroBat/shader image: SHA-256
`26e21a96ac8129cce8ef1475a63d8b9c02a4eecb7c7496fc0d10ad9df82898dc`.

[The root license assignment](LICENSING_1_0.md) now scopes original independent
client implementation to PolyForm Noncommercial 1.0.0, original prose to CC
BY-NC-SA 4.0, and original backend/integration additions to MIT. Copied foreign
context, data and resources retain their own terms. The
[Batocera component correction](BATOCERA_COMPONENT_LICENSES.md) distinguishes
the team's LGPLv3 default, explicit GPL Configgen and individual exceptions;
it does not label every Batocera file GPL or LGPL.

The source map enumerates 65 client modules. The actual payload contains 63,
with development-only appimage/transfer tooling excluded as before. Its legal
map contains exactly those files and the single backend implementation, plus
the canonical source-map SHA. Original standard texts and upstream notices are
unchanged. The existing private/development-path audit was not relaxed when
source-only tool names caused the first pre-build inventory check to reject
an overly broad source-map copy. No AppImage was produced by that rejected check.

The new payload retains the official RetroBat resources and host-only shader
architecture. The removed captured-art/full-shader audits are historical,
not new unresolved payload blockers. No art, shader, theme or renderer audit
or modification was repeated in this adapter sprint.

## Automated verification

- Full isolated suite: 820 tests, 815 passed and five expected opt-in skips;
  GTK tests used the isolated display, with no normal user profile/UI session.
- Structural generators: 52/52 verified; no synthetic fixture booted as a game.
- After the actual-payload-map correction: 66 targeted package, production,
  backend and license checks passed, including the new fifth scope check.
- Runtime-smoke, shell syntax, diff/credential-pattern checks and source-document
  links passed. The ten backend checks cover forward/reverse imports, both
  builders, installed layout, hostile PYTHONPATH, malformed results and timeout.
- Source parity: four CFG files byte-identical for both real pinned builder
  modes; sixteen old/new system/bezel priority cases identical, configuration
  bytes unchanged in the isolated fixtures.
- Final extracted AppImage audit passed. The actual AppImage `--help` exits 0
  in disposable HOME/XDG roots; no ordinary frontend profile was opened.
- Actual packaged code: all four operations checked, including both builder
  modes, eleven healthy upstream imports only in the backend, zero upstream
  imports in the guarded client, expected SNES selection and PS2 None result.
  Four packaged-builder CFG files also match the pre-change baseline bytewise.
- All standard legal-text copies match their recorded bytes; source-map identity
  retained; the backend has its own complete MIT notice. Actual shader programs
  remain outside the image. The frontend binary is byte-identical to the prior
  accepted candidate.

Ignored evidence: `.work/adapter-separation-2026-10-27/`, including builder/API
parity, package verification, full/targeted logs, protected-image and stage
receipts. Logs contain no secret values.

## Protected baseline and manual handoff

Four canonical/MainRig-installed image hashes match their pre-work records.
The Gold artifact remains
`b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`;
the accepted RetroBat/shader artifact and active MainRig copies remain
`938df3ab6a33de069baab4b8f9dfac876693a9efaa40f4b952d0519c916027d5`.
The prior build Stage was parked for each guarded build and restored with the
same manifest SHA. Neither remote PC was accessed or changed. No package,
driver, normal profile, firmware/EEPROM, ROM/media or shortcut was modified.

For MainRig acceptance, close the existing frontend and manually open the new
file above. It uses the usual existing settings; it does not reset setup.
Check global/system/per-game options and priority, one RetroArch and standalone
start, decorations and Start + Guide return with normal mouse behavior. The
owner repeats the relevant visible checks on Laptop and Wohnzimmer-PC. These
manual results have not been claimed by the automated backend/package tests.
The installed shortcuts still point to the previous image for ordinary use.

## Actual public-release limits

No new specific resource-license contradiction was established. Public release
still requires the owner's RetroAchievements identity arrangement and matching
full covered source/remaining nested notice delivery described in
[SOURCE_ACCESS.md](SOURCE_ACCESS.md). The read-only public-tree hygiene check still reports personal host identifiers
and tracked files over 5 MiB. The root LICENSE check now passes. Those remaining
privacy/size findings are separate from copyright/license conflicts; no masters
or history were deleted to force a green result. Publication approval remains
separate. The component grants and process architecture are not a universal
legal exemption or a certification of the full mixed binary's public release.

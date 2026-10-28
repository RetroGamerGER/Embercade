# First-install and ScreenScraper production-build repair

Date: 25 October 2026. This is local development and private artifact validation;
no publication, release, push, MainRig installation or WohnzimmerPC change is
authorized by this work. The prepared MainRig handoff image/profile is preserved.

## Confirmed cause

The old `ui-build` supplied only `EMBERCADE_SCREENSCRAPER_RUNTIME=ON`. It did not
supply the upstream application authorization macro. The existing patch chose
a runtime-only reader, returned an empty request without the local developer
file, and independently required that file before the account check. Packaging
copied exactly that frontend; this was not a lost embedded key or merely an
incorrect Installer status. Installer/Doctor additionally exposed developer
and personal-account configuration even though neither was an installation
prerequisite.

The retained verified extraction of the previous image was also inspected
without starting it. Its frontend hash
`19e23d259cff07b32475a5fbeded3409da78c38dd26f5f67781274ba0f287673`
matches that old image's complete manifest, and the old local-file setup guard
is present. The new frontend has a different verified hash and embedded-build
marker. This corroborates the source/build-path diagnosis against the actual
previously packaged artifact (`old-image-inspection.json`).

The public RetroBat `master` reference was inspected at
`37d70f3e46282ba431a64813347cf5b0431bbbfb`:

- [CMakeLists.txt](https://github.com/RetroBat-Official/emulationstation/blob/37d70f3e46282ba431a64813347cf5b0431bbbfb/CMakeLists.txt)
  takes `SCREENSCRAPER_DEV_LOGIN` and `SCREENSCRAPER_SOFTNAME` as definitions.
- [ScreenScraper.cpp](https://github.com/RetroBat-Official/emulationstation/blob/37d70f3e46282ba431a64813347cf5b0431bbbfb/es-app/src/scrapers/ScreenScraper.cpp)
  uses the application query independently of URL-encoded personal settings.
- [ScreenScraper.h](https://github.com/RetroBat-Official/emulationstation/blob/37d70f3e46282ba431a64813347cf5b0431bbbfb/es-app/src/scrapers/ScreenScraper.h)
  gates the existing provider on the application macro.

The three reference files do not establish a private release pipeline or secret
management scheme. `keys.txt` is not read by those CMake definitions and was
absent in the inspected Embercade/reference roots. This implementation uses
only the owner's Embercade credentials; no foreign credentials were copied.
The pinned Batocera/ES revisions and emulator routes remain unchanged.

## Actual production path

1. The developer supplies a protected, unversioned file through
   `EMBERCADE_SCREENSCRAPER_BUILD_SECRET_FILE` (path only). It contains exactly
   `SCREENSCRAPER_DEV_ID` and `SCREENSCRAPER_DEV_PASSWORD`. Missing/empty,
   malformed, duplicate, unsafe or personal/debug fields fail production.
2. `frontend_build.py` generates a 0600 forced-include header under a 0700 build
   tree. It defines the existing upstream macro using URL-encoded values.
   CMake/cache/compiler arguments see only the header path, never values.
   Compiler output is additionally redacted. No debug password is included.
3. `ui-build` configures and builds the actual pinned frontend. It verifies
   that this binary contains the intended authorization and public build-mode
   marker, then records only software/mode/binary hash in `frontend-build.json`.
   Source/mode/authorization changes cannot silently reuse an old frontend.
4. Stage validates this identity before replacing its tree; it copies the
   frontend and value-free receipt. Exported nonsecret resources have normal
   readable payload permissions despite the private build workspace.
5. AppImage preparation/extraction verifies the same mode/hash and frontend.
   Missing authorization is rejected for production. The original source and
   generated header are forbidden loose payload files, as are personal secrets.
6. The production request path uses the compiled authorization independently
   of a local developer file. The build-source environment variable is removed
   from the frontend namespace. Explicit credential-free development can use
   the existing local override; absence cannot block a compiled production build.

Compiled application credentials are **extractable**. Compilation, private
build directories and redaction do not make the distributed authorization
secret. The owner explicitly authorized this application integration; no
concrete contrary provider condition was supplied or found in the referenced
mechanism. No proxy, new infrastructure or additional user registration exists.
Other asset/license/public-release gates remain independent and unchanged.

Personal login is still entered exclusively in EmulationStation's existing
account menu and stored in the existing separate owner-only user file. It is
not a builder input. The existing atomic migration/persistence and narrow
ROM/BIOS/media isolation remain. Installer, details, completion and Doctor no
longer expose developer or personal-account status/setup instructions. Missing
personal login cannot cause installation failure. Genuine scrape/account,
service, network and quota errors retain value-free user feedback.

Development without authorization must be selected explicitly using
`--development-without-screenscraper` for frontend/Stage/AppImage. Its filename,
build output and manifest label it development; it is not a complete candidate.
Production packaging can use an already verified self-contained Stage without
re-reading a target-machine secret file.

## Build and first-install observability

The relocated old CMake cache referenced a former source directory, and a clean
configure exposed a missing FreeImage development header. The build now uses a
fresh configure plus the existing prepared libraries and a header from the
checksum-verified locked source archive. No host package was installed.

The supplied laptop log excerpt contains one Pacman command at 12:22:50,
transaction completion at 12:22:54 and last hook start at 12:22:55 (+0100).
It contains duplicate pasted fragments, not evidence of another invocation.
The final hook's completion time and total wizard duration are absent. The
owner asked to drop the perceived-delay investigation. No speculative package,
download, hook, timeout or error-handling shortcut was added.

The host transaction now publishes fixed private phase events for checking,
confirmation, repository installation, optional community build, and completion.
The localized GUI shows phase and elapsed time without fabricated percentages.
External package-manager output remains native in the terminal. Actual child
exit after hooks still determines success and terminal closure; failure output,
cancellation, retry and dependency refresh remain. A value-free
`host-install-*-timings.json` persists under Embercade's installer state after
temporary transaction cleanup. It measures host work, not the entire wizard.

## Executed validation and remaining acceptance

The source suite discovered 772 tests: 767 passed, five unrelated native
emulator/layer-shell opt-ins skipped. It includes 25 opt-in GTK checks with
isolated XDG roots/private display, bilingual flows/details/progress, synthetic
build inputs, encoding, missing configuration, stale binary/production guards,
private account/namespace/transport regressions and safe errors. All 52 pinned
structural routes passed using the owner's relocated core source read-only.
Runtime, frontend-library and shader smoke checks passed. No test game or
package-manager install ran on MainRig.

One sparse, real developer-only `ssinfraInfos.php` request returned HTTP 200
and the expected authenticated infrastructure response with software identity
Embercade. No personal account, game/media request, authenticated URL or raw
response body was logged. This confirms API authorization, not frontend E2E.

The artifact identity, package checks and preservation proof are appended after
build below. Full personal-account game identification, metadata plus one
available medium, frontend display and restart persistence in the same fresh
image remain the explicit Garuda-laptop manual acceptance. The user enters the
personal account in the frontend only. No developer file/environment/build
source fallback may be accessible in that test. New candidate success is not
inferred from historical MainRig/two-host scraper confirmations.

## Verified private artifact and laptop copy

- AppImage source: `622c3cf4268321a994703adff0e409098ff24a66` (clean local commit).
- Repository artifact: `dist/private-screenscraper-2026-10-25/Embercade-1.0-ScreenScraper-x86_64.AppImage`.
- SHA-256: `9295a73400eb846a891fd986bb0046ea1f88c69fc3352c79df8a8c9e6a1e5228`.
- Frontend SHA-256: `1294f902b9a8d53eb3ca983466e049043c57ba0734dff98725b77c97763c5acc`.
- Manifest reports `production-candidate`, `embedded`, `Embercade`; public release
  remains blocked by the independent existing project gates.

The image was built and extracted with complete manifest verification. Nine
changed runtime modules match source byte-for-byte; all 73 selected tests passed
against its actual extracted Python payload, including the 25 GTK checks.
Actual image CLI language/status calls passed in fresh English/German XDG roots,
without a local developer file/account or exposed scraper status fields.

A further isolated probe mounted the actual image, hid the host home/SSD/build
source, cleared the environment, and ran its real frontend `--help` successfully.
It read the exact application-authorization constant from that packaged binary
using verified binary offsets (no values in argv) and made one official
infrastructure request: HTTP 200, expected authenticated response. This is an
artifact-authorization/network check, **not** an automated menu-driven scrape.
Together with the earlier source-input check there were two sparse successful
developer-only infrastructure calls, no personal/game/media requests.

Source, generated CMake cache/command files and logs were scanned without
printing values: no actual password, encoded password or full authorization
query appeared outside intended private inputs/header/objects and authorized
frontend binaries. Loose build-source/header and personal files are absent
from the image. AppImage/Stage identities and public resource permissions pass.

At the owner's explicit request an identical image, checksum and manifest were
copied to the designated backup folder for the laptop. Existing files were not
overwritten. That CIFS share presents files without executable permission;
the user must copy the image locally on the laptop and mark it executable in
file properties. No mount policy was changed to bypass that limitation.

MainRig's normal Embercade roots and package list remain unchanged; its only
normal config entry remains the protected SSH key. The encrypted backup's hash
and modification time are unchanged. The previous demo image disappeared from
its old path during work; the owner explicitly confirmed moving/removing it.
It was not restored/replaced by the agent. No original collections, scraper
media or WohnzimmerPC were modified. No public release or push occurred.

Local evidence is under `.work/screenscraper-production-2026-10-25-m66s8hcd/`:
full/packaged test logs, Stage/module/safety proofs, the two API proofs,
`actual-image-authorization-proof.json`, `laptop-copy-proof.json` and
`preservation-proof.json`. Private build material is not a public report archive.
The owner subsequently reported that ScreenScraper works without problems in
the AppImage. Record this as user-confirmed functional acceptance, not as an
individually observed media/restart checklist. RetroArch startup is a separate
open laptop issue: Game Boy, SNES and N64 launches are slow, while RetroArch is
already visible in the dock. No cause or measured duration is established.
ROMs are on a network share; the owner expects imported local cores, whose
actual selected path still needs verification from the laptop launch log.
The existing verbose emulator and launcher logs in `$XDG_STATE_HOME/embercade/logs`
(default `~/.local/state/embercade/logs`) are the next diagnostic evidence. No
runtime changes, new build or host changes were made for this report.

The subsequently supplied logs contain eight sessions and confirm selection of
managed core copies. Core/video/audio initialization is mostly within one
second (three seconds for one N64 route). Later 22–23 second gaps do not identify
the waiting call or prove first-frame latency; gameplay can also be silent.
The Qt companion remains a hypothesis, and headless probes do not replace a
comparison on the affected laptop. The owner is preparing SSH access. See the
current investigation entry in `PROJECT_STATE.md`; no runtime fix is claimed.

The subsequent scoped SSH comparison confirmed the separate startup cause:
RetroArch's extra Qt/KDE desktop browser scans the many scoped scraper mounts
for folder icons. Disabling that unused companion reduces first EGL swap time
from 43.135 to 0.622 seconds with the same network ROM and local core. The
scraper's narrow writable mount contract is retained. See
[RETROARCH_STARTUP_FIX.md](RETROARCH_STARTUP_FIX.md) for validation and handoff.

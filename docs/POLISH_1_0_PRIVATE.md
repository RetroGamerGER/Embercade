# Embercade 1.0 — private polish candidate

Status: private candidate built and Garuda owner acceptance completed, 25 October 2026. No push,
publication or release is authorized. The existing private v1.0.0 release and
installed reference AppImage (SHA-256
`233f17457379dd679eb8a4ef595999e273dd035d52fc88ce49a83c3b0a623efd`)
remain protected. Acceptance below is limited to the named host, modes and owner-reported checks.

## RetroAchievements

### Per-user Web API recommendation — 28 October 2026

The owner subsequently approved implementation. See the current
[per-user key guide and verification](RETROACHIEVEMENTS_USER_KEYS.md). The
review below records the rationale before implementation; old installed
private images and the frozen source kit retain their original identities.

The owner supplied Hexadigital's Discord response advising each user to use
their own Web API key: a shared identity concentrates rate-limit traffic and
may be reset or banned. This is an owner-supplied response, not an independently
verified role/permission statement or approval to distribute the private key.
The official [API access guide](https://api-docs.retroachievements.org/)
independently documents account-specific keys, rate limiting and responsible
caching; [getting started](https://api-docs.retroachievements.org/getting-started.html)
directs users to their control panel and treats the key as a password.

The targeted code review found these separate paths at the existing pin:

| Function / UI | Actual authentication and code path |
| --- | --- |
| Normal frontend account login | `RetroAchievements::testAccount()` calls `dorequest.php?r=login` and reads `Token`; it does not read or obtain a Web API key |
| RetroArch achievements, hardcore and leaderboard settings | Existing Configgen writes the normal account name and login token to `cheevos_username` / `cheevos_token`; no Web API key is needed by this handoff |
| Supported standalone emulator achievement settings | Existing native generators likewise hand off the player name/token; their support/acceptance scope does not expand because of this review |
| Per-game achievement list, details and user progress | `GuiGameAchievements` calls `getGameInfoAndUserProgress()` and `API_GetGameInfoAndUserProgress`; the current compile-time guard rejects a build without `CHEEVOS_DEV_LOGIN` before making the request |
| Frontend profile/score, recently played games and recent achievements | `GuiRetroAchievements` calls `getUserSummary()` and `API_GetUserSummary`; it also relies on the common Web API URL builder |
| Rank/score helper | `getUserRankAndScore()` calls `API_GetUserRankAndScore`; no caller was found in the pinned frontend. It still needs consistent handling if activated later |
| Game hashing / index lookup | Local hashing and the existing `hashlibrary` / `officialgameslist` requests use a different path without the shared Web API query; do not make these depend on the optional user key |

The official [game-progress endpoint](https://api-docs.retroachievements.org/v1/get-game-info-and-user-progress.html)
and [summary endpoint](https://api-docs.retroachievements.org/v1/get-user-summary.html)
both require `y`, the Web API key; `u` is the queried player. The old Batocera
`z=<key owner>&y=<key>` query is not a separate application credential. Current
direct HTTP docs list `y` rather than requiring `z`; a narrow compatibility
change can still use the existing account name for the legacy `z` field without
asking for another username. The normal login token must not be substituted
for the Web API key. No documented supported login-to-Web-key exchange was
found in the reviewed sources; this is not proof that no provider-supported
future mechanism exists. The owner may ask the provider that focused question.

Recommended implementation, not yet authorized or implemented by this review:

- Keep the existing Batocera Web API requests, response parsing, achievement
  views and normal personal login. Replace compiled shared authorization with
  runtime per-user authorization for the frontend Web API calls only.
- Add one optional masked **personal Web API key** field to the existing
  RetroAchievements settings, reusing the already configured account name.
  Link to the official control panel/help. No second account/login dialog or
  mandatory installer step is required.
- Store the key separately from ordinary shared/exported settings in an
  owner-only file/directory (0600/0700), with an atomic save and an explicit
  clear action. Associate it with the existing account so changing accounts
  cannot silently reuse another account's key. Never hand it to emulators,
  exports, reports, logs, build definitions or release assets.
- Replace the per-game compile-time early return with a runtime credential
  check; apply it to summary and the rank helper too. Without a key, give a
  specific German/English setup message when a Web API view is requested.
  Normal emulator achievements and game starts must continue to work.
- Preserve credential-safe HTTPS/error handling. Bound duplicate requests and
  retries, cache where appropriate, and handle HTTP 429 without a retry loop.
  The official documentation also warns that `API_GetUserSummary` is slow;
  this does not justify replacing all existing API/view code in this change.
- Rebuild the frontend without the personal `CHEEVOS_DEV_LOGIN` definition and
  verify that the public candidate contains no shared/private key or private
  authorization marker. Existing private/Gold images remain unchanged.

Before a future candidate, test absent/valid/invalid/cleared keys, account
changes, restart persistence, protected file permissions, error/log redaction,
rate-limit failures and unchanged normal login/token generation without a Web
key. Test the real game list/progress view after those automated checks. No
implementation, live authenticated request, new build, deployment, source-kit
replacement, push, provider contact or publication was performed by this review.

### Original private-build implementation and acceptance

Pinned Batocera `1750dded8c0fdff70630026f756a69fcad0bb995` has a compile-time
`CHEEVOS_DEV_LOGIN` guard that returns before the achievement-list HTTP request
when no definition exists. CMake normally defines that string; `getApiUrl`
prepends it to the original `API_GetGameInfoAndUserProgress.php` request.
`getHttpOptions` extracts z for its existing user-agent convention.

The owner explicitly chose this existing Web API implementation. Build input
contains exactly `RETROACHIEVEMENTS_WEB_USERNAME` and
`RETROACHIEVEMENTS_WEB_API_KEY`, in a 0600 file under a 0700 ignored directory.
The generated private forced-include header defines the original macro as
`z=<URL-encoded key owner>&y=<URL-encoded Web API key>`. Only a path reaches
CMake/argv, and stale CMake credential definitions are unset. The query's u
still comes from the personal frontend login; no installer account field or
additional login flow is introduced. The previous experimental emulator-token
replacement was withdrawn and is absent from the candidate source.

The existing private frontend authorization helper also validates/redacts the
Web API input. Its value-free receipt labels this `private-owner-web-api` and
`private-owner-test-only`, checks the binary hash and rejects stale or unlabelled
personal-key binaries. The packaging already labels all artifacts PRIVATE and
public_release BLOCKED. A compiled key remains extractable; the receipt is not
a secrecy guarantee. No personal key may be redistributed publicly without
separate permission and rights review. ScreenScraper's authorization/login
mechanism remains as before.

A protected live request to the original endpoint returned HTTP 200 for game 1,
Sonic the Hedgehog: 35 achievements, 0 normal and 0 hardcore awards for the
queried account. This established service access and response shape before the GUI test. The
owner subsequently confirmed the actual list/progress display in the packaged
Carbon test and working RetroAchievements with the external theme. This does
not independently demonstrate an in-game achievement unlock. Native parsing now checks object/collection
shape, supports an empty achievement collection, and reports fixed localized
errors without reflecting service bodies/URLs. Login logic remains unchanged;
HTTP privacy enforces TLS, blocks credential redirects/cookies and uses fixed
value-free RetroAchievements failures. Badge/image requests use HTTPS.

Primary references:
- [Batocera source](https://github.com/batocera-linux/batocera-emulationstation/blob/1750dded8c0fdff70630026f756a69fcad0bb995/es-app/src/RetroAchievements.cpp)
- [Batocera CMake](https://github.com/batocera-linux/batocera-emulationstation/blob/1750dded8c0fdff70630026f756a69fcad0bb995/CMakeLists.txt)
- [Official Web API access](https://api-docs.retroachievements.org/getting-started.html)

## KDE identity and icon

The previous native SDL window was created with EmulationStation identity;
only its title was subsequently changed. Its embedded window icon remained
upstream's image and generated desktop files had no StartupWMClass.
The native builder now uses the existing original Embercade PNG for the window
resource. SDL application identity is embercade for X11/Wayland/SDL2-compat;
application title remains the existing product label. Managed desktop entries
advertise StartupWMClass=embercade. Steam IDs/artwork logic is unchanged.
The candidate actually ran natively over Wayland on Garuda. Protocol trace
shows xdg_toplevel.set_app_id("embercade"). A separate XWayland run reported
WM_CLASS instance emulationstation / class embercade and title EMBERCADE 1.0.
The owner explicitly confirmed the correct KDE icon in the real candidate.
Steam artwork/IDs were preserved by source/regression checks; actual Steam
launch/task grouping is not separately accepted.

## GameSir G7 Pro

Current Garuda SDL discovery reports GameSir G7 Pro, decimal 13623/4252,
GUID `03004535373500009c10000053010000`, corresponding to USB 3537:109c.
The gs_native driver and gamesir-native service were observed, not changed.
The motion sensor appeared before the main gamepad; after the owner's connection
confirmation the normal gamepad was available. Existing Embercade uses udev for
mouse/keyboard and sdl2 for joypads, with per-launch ES SDL controller mappings.
The isolated joypad_autoconfig_dir had no matching profile.

One targeted SDL2 autoconfig file supplies normalized face/direction/shoulder/
stick/trigger inputs for this name and pair. It is seeded only when absent;
existing user profiles are not replaced. Start/Back/Guide exit handling remains
in the existing mapping/hotkey bridge; no Guide-alone menu action is added.
The real packaged GB/SNES/3DO/N64 logs now show successful GameSir
autoconfiguration and no fallback warning. RetroArch 1.22.2 SDL2 first connects
enumerated pads and also processes queued SDL_JOYDEVICEADDED events through
the same sdl_pad_connect routine, explaining the duplicate startup autoconfig
messages seen in these controlled runs. There is no second gamepad in SDL
discovery; notifications were not hidden. The owner confirmed gameplay, exit
and normal mouse operation with the candidate. A separate passive read observed
A/B/X/Y, Back/Start, all D-pad directions and both triggers over 0..32767.
Stick travel, shoulder/L3/R3 and Guide were not independently sampled during
that 90-second window; the broad owner confirmation must not be presented as a
full event-by-event trace. Other hardware modes/IDs and extra buttons remain
unvalidated. No native driver, DKMS, service, firmware or udev rule was changed.

## Notification sizing

The generated Garuda configuration had widgets enabled, automatic scaling and
both scale factors at RetroArch's untouched 1.0 defaults; menu driver was ozone.
RetroArch's upstream widget path uses display metrics/menu scaling rather than
the legacy video_font_size setting alone. It is not established that KDE reports
incorrect DPI. Patch 0034 migrates only the untouched automatic defaults to
separate 0.6 fullscreen/windowed widget factors. RetroArch retains its normal
resolution/DPI scaling, notification visibility and achievement widgets.
Existing non-default saved widget preferences and explicit retroarch.* values
remain authoritative. No shader/backend/bezel change is part of this patch.
The actual writer was tested at 1920x1080, 2560x1440 and 3840x2160, with
widgets still enabled. The owner accepted the real notifications during the
Garuda run (2560x1440 desktop). Separate 1080p/4K visual legibility remains
open; configuration tests are not visual acceptance.

## Frontend video

The actual pinned frontend uses libVLC, RGBA decode callbacks, double-buffered
surfaces and the existing OpenGL texture renderer. libVLC is a host dependency;
its dynamically loaded decoder was not covered by frontend ELF inspection.
Garuda and NVIDIA laptop had vlc-plugins-base 3.0.24 but no vlc-plugin-ffmpeg.
CachyOS Handheld had the matching VLC FFmpeg decoder, demux and conversion plugins.

Identical untouched GB/Monopoly H.264/MP3 clip on both machines:
SHA-256 `294dd2713b239576b96d409bb7b67b2490fdd5f0f019c285d4f775121478d002`.
Five-second libVLC callback probe: Garuda before repair 0 frames (explicit
unsupported H.264 decoder error); Wohnzimmer 138 decoded/displayed frames,
130 distinct frame hashes. Adding only the distro-matched plugin in an isolated
Garuda probe gave 149 frames, 141 distinct hashes. After the owner's approved
system installation, Garuda gave 150 frames, 142 distinct hashes.
The transaction and all seven post-transaction hooks completed with exit 0.
No original clip was converted or rewritten. No video player/rendering rewrite
was required. These initial figures prove decoding. Subsequent real AppImage GL probes and
owner theme/audio acceptance are listed below.

Setup now checks actual libavcodec, libswscale and vmem modules plus their ELF
closure, and offers vlc-plugin-ffmpeg through the existing confirmed package
installation flow. Matching distro plugins stay with host VLC/FFmpeg rather
than bundling an incompatible plugin against arbitrary host ABIs. No laptop or
Wohnzimmer system package was changed.

## Shared acceptance matrix

| Area | Automated/source evidence | Actual packaged/manual acceptance |
| --- | --- | --- |
| RA list/progress/errors | Live original Web API HTTP 200; private build/receipt/redaction tests; real native request/parser tested enabled/disabled, malformed/missing/empty/unavailable replies | Owner confirmed actual list/progress in Carbon and RetroAchievements with external theme; in-game unlock not independently verified |
| KDE icon/identity | Real Wayland app_id and XWayland WM_CLASS; original branding; desktop/Steam regression tests | Owner confirmed KDE icon; actual Steam grouping remains open |
| G7 Pro | Real 3537:109c SDL2 autoconfig in four packaged starts; profile preservation; passive button/trigger observations | Owner confirmed gameplay/Start+Guide/frontend return and normal mouse; unobserved inputs/modes documented above |
| OSD | Original/default/custom/override cases plus real writer at 1080p/1440p/4K; actual generated factor 0.6 | Owner accepted Garuda notification size; separate 1080p/4K visuals open |
| Video | Same clip SHA; decoder A/B; actual GL framebuffer changes and texture uploads with packaged frontend over Wayland/XWayland | Owner confirmed picture+sound in Carbon and AI-HYPERTOCERA-THE-MINI-CAKE-TV, including game changes after restart |
| Regression | Full suite with native GTK; 52/52 structural routes; runtime smoke; 20 packaging checks | Packaged GB/SNES/3DO/N64 render; owner game start/exit/return; no repeat of unused Qt companion startup |

## Packaged rendering and startup evidence

A short reference playback of the same existing clip through ffplay completed
outside Embercade. Garuda's original released/reference AppImage then rendered
moving pictures after installing the decoder, without a frontend video-code
change. An initial diagnostic run with upstream --videoduration stopped too
early: its playVideo loop accumulates elapsed time rather than per-frame deltas.
That probe artifact was corrected by using the existing unlimited playback and
terminating only the task-owned diagnostic process. No product timer change was
made or needed for library videos.

The candidate's existing VideoVlcComponent pipeline over native Wayland showed
378 decoded/displayed frames, 756 texture uploads and 74 changing nonblack GL
framebuffer samples in the bounded run. XWayland gave 379 frames, 757 uploads
and 73 changes. Native Wayland Carbon and external-theme library runs continued
with thousands of decoded frames/texture uploads and changing nonblack output.
The same candidate was restarted into the external theme; the owner confirmed
both theme playback and clean switching with audio. Original media were neither
converted nor replaced. Existing H.264/MP3 clips and a H.264/AAC 3DO clip were
inspected; native rendered tests used the GB/MD clips. Other video codecs were
not independently rendered in this sprint.

The actual candidate launched Game Boy/Gambatte, SNES/Snes9x and 3DO/Opera with
Vulkan, shaders disabled, and N64/Mupen64Plus-Next with its retained GL Core
exception. Qt companion flags stayed false. Each exited normally after a
bounded frame run and generated the expected SDL2/notification settings. Short
N64 core screenshots were initially black; a longer run plus direct EGL
framebuffer capture proved changing nonblack output (900 frames), while the
short core screenshot alone was inconclusive. This was not labelled a Vulkan
failure or fixed by changing the retained core exception. N64's direct EGL
probe observed a 2560x1408 window and over 2.6 million nonblack pixels late in
the run. No backend/shader selection was changed by this sprint.

CachyOS Handheld currently has older AppImage hashes than Garuda's released
reference, and no ES process was running during the read-only inventory. The
comparison is therefore not advertised as an identical-build Gamescope E2E
acceptance. Identical media bytes and the decoder-module difference were
verified; the controlled same-build Garuda before/after test isolated the
missing dependency. Laptop has the same missing decoder in its inventory, but
its installed managed image is older. Neither remote system was changed, no
candidate was installed there, and no AMD/NVIDIA/Gamescope-wide compatibility
claim is made. Further remote visual checks remain open.

## Artifact and test record

- Exact candidate build source: `935eacf508ab18c369091d8bfbd9023b0d9ed7fd`.
  Functional implementation is commit `8f24bc5`; the following commit adds the
  dynamic video dependency to the manifest. Later audit/test documentation does
  not change the image payload.
- Image: `dist/private-polish-2026-10-25/Embercade-1.0-Private-Polish-x86_64.AppImage`
- SHA-256: `b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`
- Size: 279108088 bytes. Matching .sha256 and .manifest.json are adjacent.
- Native frontend SHA-256: `dcfb2ac509458986fc3b3f24d3e0b5edc81f49b86ca9d3a1925d86558c306e54`.
- Manifest: PRIVATE / public_release BLOCKED; RetroAchievements authorization
  private-owner-web-api / private-owner-test-only. Artifact parent is mode 0700.
- Final full suite: **790 tests, 785 passed, 5 expected native opt-ins skipped,
  0 failures** (159.141 seconds), including 25 GTK checks and 52/52 structural
  routes. It includes actual patched Web API/parser failure boundaries and
  notification writer resolution gates. An earlier run used a disappeared
  external Core-backup path and failed structural core discovery; the final
  run used existing managed Garuda cores read-only, without installing/copying
  cores or changing owner data.
- 20 focused AppImage packaging checks passed after the manifest addition;
  pinned native patch replay and runtime smoke passed. One new AppImage candidate
  was built, with post-extraction audit and frontend authorization/hash matching.

The original Garuda batocera.conf hash and both reference/managed AppImage
hashes still match the preflight inventory. Scoped probes used separate private
XDG/saves/config roots and read-only collection/media mounts. The owner-completed
test frontend was closed; no normal application session was terminated. The
original desktop entry/profile was not upgraded, the release tag was not moved,
and no push/publication was performed. Preserve the ignored owner-only Web API
build file; do not copy its contents into issues, reports or Git. The generated
private input/header and test profiles contain protected material and remain
outside version control.

Final repository verification: origin/master remains
`54c45e89552ff6f007ac79d7e31c524346a3880e`; annotated v1.0.0 still dereferences
to `3430484d564d7ff58fa278c7e9de25391f5de754`. The sprint commits are local only.
Recovery: start the protected prior AppImage to return to the reference; do not
reset the owner's profile or remove the decoder to switch builds. The newly
seeded autoconfig is restricted to the candidate's isolated profile during these
tests. No system controller rollback is needed or authorized.

## Owner-authorized deployment to all three PCs — 25 October 2026

After the private sprint acceptance, the owner explicitly requested replacing
all three PCs' active AppImages while preserving the names expected by their
links. This supersedes the preceding no-deployment statements for these named
private hosts only; it is not permission to push, publish or replace v1.0.0
release assets. No new image or source-code build was made.

All five active copies now contain exactly the accepted candidate bytes:
SHA-256 `b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`,
source `935eacf508ab18c369091d8bfbd9023b0d9ed7fd`.

| Host | Updated path | Existing start route |
| --- | --- | --- |
| Garuda | `~/AppImage/Embercade-1.0-Release Candidate-x86_64.AppImage` | Manual AppImage selection, same name |
| Garuda | `~/.local/share/embercade/application/Embercade.AppImage` | Menu and existing Steam shortcut |
| Garuda laptop | `~/AppImages/Embercade-1.0-AutoGraphics-x86_64.AppImage` | Manual AppImage selection, same name |
| Garuda laptop | `~/.local/share/embercade/application/Embercade.AppImage` | Existing menu entry |
| CachyOS Handheld | `~/Applications/Embercade/Embercade-1.0-x86_64.AppImage` | Existing Steam shortcut; menu now targets this same image |

Wohnzimmer's menu previously called the classic `.local/bin/embercade` wrapper,
while Steam already used the AppImage. Only that menu Exec field was redirected
to the existing AppImage filename; its classic install ownership receipt's
expected desktop hash was updated consistently. The classic prefix and command
symlink remain unchanged as a recovery route. Garuda/Laptop desktop integration
ownership hashes were updated for their managed image copies. Steam shortcuts,
IDs, start directories and artwork were not edited, and no Steam restart was
required. Historical ScreenScraper/RetroArchStart laptop images and Wohnzimmer's
before-final-polish image were retained unchanged.

Each old file was copied to a private verified backup before any replacements.
New images were copied into same-directory temporary files, hashed, flushed and
atomically renamed. Matching checksum sidecars preserve the local image name;
external manifest aliases change only image.filename while retaining binary
hash/source identity. Images are owner-readable/executable only (0700), and
manifests/checksums are 0600, because the candidate includes the personal Web API
key. No build credential file was transferred to another host.

Backups on each host are under
`~/.local/state/embercade/image-backups/polish-2026-10-25-ac2578b8/`.
The owner-private `deployment.json` records each original path, old/new hash,
original mode and verified backup file, including relevant integration metadata.
Independent readback verified 3 original backup files on Garuda, 5 on the laptop
and 5 on Wohnzimmer. Restore the recorded image/sidecars/metadata together if a
rollback is needed. The repository's original released/reference payload also
remains preserved. Transfer-only temporary image copies were removed after
successful verification; installed images and rollback backups remain.

Wohnzimmer became unreachable during the first upload because the owner had
switched it off. No active file had yet been replaced. After the owner powered
it on, a fresh inventory confirmed the same target images/links and no running
emulator; the private staged transfer was repeated and verified before activation.
No frontend/emulator or Gamescope session was stopped or started for deployment.

Post-deployment verification on all three hosts:
- Five image hashes, alias manifests and checksum names match.
- The actual AppImages pass CLI --help under separate temporary HOME/XDG roots.
- Their FUSE-mounted native frontends pass --help; frontend SHA-256 is
  `dcfb2ac509458986fc3b3f24d3e0b5edc81f49b86ca9d3a1925d86558c306e54`,
  and the private-owner authorization receipt matches the accepted manifest.
- Menu targets exist; Steam entries are byte-identical to the fresh inventories.
- Hashes of existing user config, frontend preferences/input mappings and the
  protected SSH file where present remain unchanged. No ROM, BIOS, saves,
  scraper media, controller driver/service, firmware or normal emulator profile
  was replaced or reset.
- The owner additionally authorized the laptop VLC decoder and installed it
  personally through SSH after desktop authentication did not appear. Readback
  confirms vlc-plugin-ffmpeg 3.0.24-1 on the laptop and 3.0.24-1.1 on Wohnzimmer.
  Decoder, swscale and vmem modules exist with no missing ELF dependencies on
  every host. The installer already offers this package through "Install optional
  host software" when missing; no future build is required for that integration.

These are deployment/CLI/dependency checks, not new remote visual/gameplay
acceptance. The earlier laptop/Gamescope visual test limits remain. No automatic
first-run wizard, profile migration/reset, GitHub push or release was performed.


## Source/documentation push authorization — 25 October 2026

The owner subsequently approved pushing the current source, tests and
documentation to origin/master. The earlier sprint no-push statements above
record their original scope; this latest authorization supersedes them for Git
commits. The accepted AppImage stays private, with no new tag/release, artifact
upload, replacement of v1.0.0 assets or repository visibility change. There is
no new build. The artifact, credentials, private headers, build objects and
deployment inventories remain in ignored dist/.work locations. The push contains
only the implementation, regression tests and value-free project documentation.
The existing 790-test result and three-host deployment evidence remain the
validation baseline; only documentation changes follow those checks.

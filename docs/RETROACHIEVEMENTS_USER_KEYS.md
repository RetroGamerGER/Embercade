# Personal RetroAchievements Web API keys

The current deployed candidate was subsequently accepted by the owner on all
three reference PCs on 28 October 2026, with only the known laptop 16:10 bezel
limitation reported. See the [current overall acceptance](PRIVATE_DEPLOYMENT_2026_10_28.md#owner-acceptance--28-october-2026).
Earlier candidate-specific pending notes below remain historical; they no longer
make overall three-host acceptance an outstanding gate. This broad confirmation
does not invent separate observations for every error/Reset/restart case.
The image remains private and the publication hold is unchanged.

Embercade keeps Batocera's normal RetroAchievements login and emulator token
handoff. Sign in with your usual account in the existing RetroAchievements
settings. RetroArch and supported standalone emulators continue to use that
login; a Web API key is not required for their achievement integration.

Open **Game Settings → RetroAchievements Settings**. Directly below Password,
the optional **Personal Web API key** field enables
the frontend's achievement lists, profile and user-progress views. Obtain your
own key from the [RetroAchievements control panel](https://retroachievements.org/controlpanel.php),
then paste it into this field. The existing account name is reused. The menu
and both keyboard editors mask the key. **Reset** in that editor removes it;
Cancel preserves the saved value. No second login or installer step is added.

The first private candidate exposed a pre-existing editor gap: there was no
clipboard paste handler. The follow-up adds Ctrl+V / Shift+Insert and a visible
Paste button to both masked editors, using SDL's clipboard API only after an
explicit user action. The full value is inserted in one operation with the
cursor after it; it stays masked. Empty/unavailable, oversized and single-line
control-character data is rejected without changing the existing draft. No
clipboard contents are logged, saved automatically or inspected by diagnosis
tools. Regression probes use synthetic clipboard data, not the owner's clipboard.
RetroAchievements' shortened website display is expected: use its Copy button
for the full key, then Paste in Embercade and confirm with OK.

Without a matching key, opening a Web API view explains how to configure it.
Missing, rejected and rate-limited keys have distinct German/English messages;
they do not block game starts or disable normal emulator achievements.
Changing the configured account does not reuse another account's saved key.
No automatic exchange of the normal login token for a Web API key is assumed.

The key is stored only in
`$XDG_CONFIG_HOME/embercade/secrets/retroachievements-user.conf`, with owner-only
file/directory access (0600/0700). Saves are atomic and synced. Unsafe links,
nonregular files, hardlinks, foreign ownership and permissive secret-file/
directory permissions are refused. This is local file protection, not encryption.
The key is never placed in ordinary frontend/Batocera settings or handed to
emulators, build arguments, exports or diagnostics. HTTP errors do not echo
keys, request URLs or service error bodies. RA requests retain verified HTTPS,
no credential redirects/cookies and no automatic retry loop.

## Existing upstream integration

The actual `API_GetGameInfoAndUserProgress`, `API_GetUserSummary` and rank helper
requests, parsers and views remain the Batocera code paths. Their common URL
builder reads the current user's protected key at request time, reusing the
existing account for legacy `z`, the personal key for `y`, and the queried
player for `u`. There are no requests when credentials are missing/mismatched.
Normal `testAccount()` source and Configgen/native emulator handoff are unchanged.

This follows the owner's supplied Hexadigital advice and the official
[account-key guidance](https://api-docs.retroachievements.org/getting-started.html)
and [rate-limit guidance](https://api-docs.retroachievements.org/).
The frontend does not ship a shared account key. The old private build-input
option is rejected before reading the file or launching a compiler. Old forced
headers are regenerated without `CHEEVOS_DEV_LOGIN`; defining that macro now
fails compilation. New build receipts require the per-user implementation marker
and reject the old private marker, even if someone relabels the metadata.
ScreenScraper's separately approved build authorization remains unchanged.

## Verification and acceptance

The clipboard correction passed all 70 targeted checks and the complete isolated
suite: 845 tests, 840 passed and five expected native opt-in skips, including
the GTK lifecycle and 52 structural routes. The complete native frontend build,
runtime smoke and diff checks also pass. New executable probes exercise the
actual paste method and shortcut handler with synthetic clipboard stubs: full
length, mid-string insertion, UTF-8 byte cursor, masking, explicit-action-only
reads, freed SDL allocations and failure preservation. Both masked dialogs use
the same method. The owner’s separate MainRig acceptance is recorded below.

The full isolated suite ran 843 tests: 838 passed, five native opt-ins skipped.
It included the existing GTK and 52-route structural checks. After a translated
button argument was corrected in the complete native build, all 68 targeted
storage, parser/login, build, packaging, ScreenScraper and license checks passed
again. The complete frontend build, runtime smoke and shell syntax pass.

Native tests use the actual new helper and freshly patched pinned source.
They cover 0600/0700, fresh-process restart, clearing only this key, account
binding, control/NUL/oversize rejection, symlink/hardlink/FIFO refusal, write
failure preservation, absent-key request suppression, valid list/progress and
summary parsing, 401/403/429/500 failures without automatic retries, unchanged
normal login/token response and opt-in masked rendering in both editors.
Synthetic values are used; no live authenticated request is claimed here.

The separately named PRIVATE candidate is for the owner's acceptance. Existing
installed/Gold images and the frozen d8e6ca6 source kit remain unchanged. The
owner still needs to check MainRig, EmbercadeLaptop and WohnzimmerPC: masked
entry with keyboard/controller, Cancel/Reset, restart persistence, actual list
and progress display, and a game start/achievement flow with the optional key
absent. Do not infer those physical checks from native stubs or a successful
build. No deployment, public release, tag or push is authorized by this work.

The older source kit remains valid only for its frozen private adapter binary.
A future source bundle must match the new candidate's actual manifest; the
original key-bearing private images remain private and must never be uploaded
as the public candidate.

## Separate private acceptance candidate

- Image: `dist/private-user-api-2026-10-28/Embercade-1.0-Personal-RA-Test-x86_64.AppImage`
- Exact clean source: `010f5e857e9bdda02faebd621ca14977961c362b`. Later receipt-only commits do not change this identity.
- Image SHA-256: `599663de6aa860ea113181fc40d84cb7b44b8848ea9017f77bfabf14f086d52c` (414,456,312 bytes).
- Matching sources: `dist/private-user-api-2026-10-28/source-kit/Embercade-1.0-sources-and-notices.tar.gz`; SHA-256 `0f59f48503479045561d463473f4948eef97e80e0a48480bf1b303edc5731da0`. All 1,810 internal regular-file checksums pass, including the new native helper.

The actual extracted image passes its complete package audit and both AppImage
and native frontend help probes in a disposable profile. Its manifest reports
`per-user-web-api`, with no legacy private marker in the native frontend. An
integrity-only comparison found no old private key in any of the 5,684 payload
files, the new native executable, tracked sources or reachable Git blobs; no
values were logged. The original Stage is restored and all four checked local
canonical/installed image hashes are unchanged. During package verification no normal user session was
started, and no remote installation was touched. This candidate has not been
deployed or manually accepted on the three PCs.

## Clipboard correction candidate

- Image: `dist/private-user-api-paste-2026-10-28/Embercade-1.0-Personal-RA-Paste-Test-x86_64.AppImage`.
- Exact clean source: `fd337ecab37b4ea32d7914e15fcd797b4e67df7c`.
- SHA-256: `827457baba71cd2700840801274778bc4d67d9203c7c11b36a885a5ac31f4777` (414,456,312 bytes).
- Matching source kit: `dist/private-user-api-paste-2026-10-28/source-kit/Embercade-1.0-sources-and-notices.tar.gz`, SHA-256 `348744870bee9d2117b8745033f145d5445f1f674d83f87ce04059cd097f0661`. All 1,810 internal checksums pass; the nested own-source archive contains patch 0010 and the patched editor matches the build source.

The extracted candidate passes the full package audit and both disposable help
probes, contains the clipboard entry points and per-user API marker, and has no
old private key in any of its 5,684 files. All six checked Gold,
canonical, installed and first per-user image hashes remain unchanged. The
previous Stage is restored. After confirming no frontend/game was active, this
separate correction was opened on MainRig with the owner's existing settings
for the requested visible retest. No installed image was replaced, no remote
host was accessed and no clipboard/key value was inspected by diagnostic tools.
No push/publication.

### MainRig owner acceptance — 28 October 2026

The owner confirms the corrected flow works and supplies a screenshot showing
the actual account overview with games, points and individual achievement
progress. This confirms successful personal-key entry and live overview
rendering on MainRig with the corrected candidate. The key itself is not
recorded. Restart persistence, Cancel/Reset, key-absent emulator gameplay and
the laptop/living-room acceptance remain separate checks; none is inferred
from this screenshot. Existing installed images remain unchanged and the
candidate stays private.

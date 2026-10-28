# ScreenScraper integration

## Current production-build design (2026-10-25)

The owner authorized compiling Embercade's own issued application authorization
into the pinned existing scraper. See [SCREENSCRAPER_PRODUCTION_FIX.md](SCREENSCRAPER_PRODUCTION_FIX.md)
for the root cause, reference revision, build checks and acceptance limits.
End users need only the completed image and, optionally, their personal account
entered in EmulationStation. No developer file/registration belongs on the
target. Installer/Doctor never display developer or personal-account setup.

Production `scripts/ui-build` reads the private file named by
`EMBERCADE_SCREENSCRAPER_BUILD_SECRET_FILE`. It must be a private owner-only
regular file under a private directory, containing exactly these two fields:

```ini
SCREENSCRAPER_DEV_ID=
SCREENSCRAPER_DEV_PASSWORD=
```

These are build inputs, not target-machine configuration. Values are never
placed in argv/CMake definitions/cache. A generated 0600 header under the 0700
build tree defines the existing `SCREENSCRAPER_DEV_LOGIN` macro with correctly
encoded fields; CMake sees only its path. `SCREENSCRAPER_SOFTNAME` identifies
Embercade. Compiled application credentials are inherently extractable; this
is authorized integration, not secure secret storage. The optional debug
password is rejected as a production input, never included or sent.

The frontend mode/hash receipt travels with the Stage and is checked against
the actual packaged binary. Production fails on absent/invalid build inputs,
stale binaries or missing authorization metadata. Credential-free development
requires `--development-without-screenscraper` at frontend/Stage/AppImage build
steps and is explicitly labelled. Only that development path can use the
legacy private runtime developer-file override; a missing override cannot
block embedded production authorization. No proxy or additional signup exists.

The personal account is entered only in the existing frontend Accounts menu,
URL-encoded independently as `ssid`/`sspassword`, and saved in the external
owner-only `secrets/screenscraper-user.conf`. Its existing atomic migration from
legacy ES settings remains intact; failed migration retains the old settings.
It is never read by the frontend builder or included in the image. No account
is required to install, launch or play. The state contract is in
[STATE_AND_SECRETS.md](STATE_AND_SECRETS.md).

HTTPS certificate verification, service-domain validation, redirect refusal
for credential-bearing requests, private account persistence and disabled
process dumps are retained. URLs/raw response bodies are not logged. Access,
quota, account and network errors remain truthful with value-free user messages.

The October 10 owner-confirmed MainRig scraper success and earlier two-host
records below describe the old runtime-file deployment. They are historical;
they do not establish the new image's clean personal-account/media/restart
acceptance, which remains a separate laptop check.

## Metadata and media writes

The pinned frontend writes `gamelist.xml` directly via pugixml. Its downloads
write a temporary file and rename it inside the destination media directory.
`Scraper::getSaveAsPath()` uses exactly `images`, `videos`, `manuals` and
`magazines`; screenshots, covers, wheel/marquee, thumbnail, fanart, maps and
bezel pictures share `images` rather than requiring new writable directories.

Production prepares those destinations only for existing system directories
listed in its staged catalog. It preserves existing gamelists and media. If a
system has no original gamelist but an existing upstream fallback in isolated
ES config, that list is retained by copying it to the system directory without
changing the fallback. Otherwise an empty valid gamelist is created exclusively.
The system directory itself is **not** mounted writable. Only the gamelist file
and four media directories receive writable binds at both collection aliases;
ROM contents, other files, BIOS and immutable resources remain read-only.

Escaping paths and symlinked/nonregular metadata destinations are refused.
Unavailable collection permissions do not prevent frontend/game launch; that
system remains read-only and the existing scraper reports its write failure.
Collection storage must allow creation/writing of these specific metadata
destinations by the user. Root/system folder-wide write mounts are not used.

Upstream continues serializing media relative to the ROM-system root, e.g.
`./images/game-image.png`; `gamelist.xml` stays in the original collection.
No metadata is relocated to a second XDG database. Custom frontend system paths
outside the staged catalog are not automatically granted write access.

## Acceptance and preservation

Use one small system and scrape two or three individual games through the
existing frontend UI, not a whole collection. Verify names/descriptions/media,
relative XML paths and unchanged ROM content. Video/manuals are checked only
when selected and actually available upstream. Server quotas, access grants,
network availability and title matching remain external conditions.

Normal install/update/uninstall owns only immutable program files. Local
credentials and user settings remain in XDG; gamelist/media remain in the
external collection. No-op update must not rewrite these files. Purge is a
separate destructive action and is not used by this integration.

Tests exercise the native credential reader/security helpers, Python status and
mount policy, a real Bubblewrap write-protection boundary, relative metadata,
existing/fallback-list preservation, normal installer preservation and rejection
of a credential file in Stage. They use invented fixture values only.

### Historical two-host evidence

The detailed checks below describe earlier working installations. The current
MainRig confirmation and its scope are recorded at the top of this document.

MainRig acceptance covers two individual 3DO titles, `Alone In The Dark 2`
and `Road Rash (Europe).cue`: description, preview, selected images, video and
manual are confirmed visible. Both saved entries have relative media paths;
all 14 media files exist. Game launch, controller exit and return also pass.
A normal non-purge uninstall/reinstall preserves the 1,970-entry post-scrape
user-state inventory (only the install manifest changes), the original-system
gamelist and all media hashes/timestamps. An identical-payload update is a true
no-op, including the manifest. The selected nine CUE/ROM fingerprints are
unchanged; the first game's fingerprint was taken after its scrape, so this
is not a claimed pre-first-scrape content hash. Actual namespace write-protection
tests and production mounts keep ROM/BIOS files read-only throughout.

The same payload was installed normally on the second host, preserving
all 5,611 inventoried user-state entries except its expected install manifest;
Doctor passes. The user explicitly approved separate encrypted SSH transfer of
the private developer file, not inclusion in the package. Its real interactive
Steam/Gamescope acceptance covers `Cannon Fodder (Europe).cue`: description,
preview, seven selected media files (image, thumbnail, marquee, video, manual,
fanart, boxback), controller game launch/exit/return and normal frontend Quit.
All saved media paths are relative and their files exist. Non-purge
uninstall/reinstall preserves all 5,544 post-scrape user-state entries except
the expected install manifest. Nine gamelist/media/CUE fingerprints, including
timestamps, are unchanged. A subsequent identical-payload update is a true
no-op, including the manifest. The CUE baseline is post-scrape; no pre-scrape
content-hash claim is inferred from it. Both hosts receive the final documented
revision through the supported installer, with manifest/file-hash verification.

The two reference hosts currently share the external collection. The second
host's successful scrape therefore also updates the MainRig-visible gamelist
and media. The final preservation baseline is taken after both tests, not
before that intended metadata change; all 14 earlier MainRig media files and
nine selected ROM/CUE fingerprints still match. Do not run simultaneous
scrapes/frontend sessions writing the same system gamelist from different hosts:
upstream saves its session's list, without a cross-host merge or locking layer.

## Failure boundaries

In explicit development builds, missing/invalid local overrides fail before an
API request. Production uses compiled application authorization; unsafe permissions,
symlinks, duplicates, oversized files and malformed data are rejected in tests.
The real initial developer rejection (HTTP 403) is diagnosed without displaying
credentials. Invalid user access, closed/restricted service and quotas map to
safe messages in the native helper; quotas are not deliberately exhausted and
user-account failures are not artificially forced against the live service.
HTTPS/host/redirect rejection and unavailable metadata writes are automated
failure tests. An actual refused media-shard request exposed the original
preview/download failure; the scoped DNS fix is now verified by real downloads
on both hosts. Network failures, no match, write/download failure and partial
results retain upstream handling; this is not a claim that every remote failure
mode was induced in a live E2E session.

## Sources

- Pinned ES `1750dded8c0fdff70630026f756a69fcad0bb995`:
  `scrapers/ScreenScraper.*`, `scrapers/Scraper.cpp`, `GuiScraperStart.cpp`,
  `Gamelist.cpp`, `SystemData.cpp`, `HttpReq.cpp`, `Settings.cpp`.
- [Official ScreenScraper API](https://screenscraper.fr/webapi2.php?alpha=0&numpage=0).
- Project patch `0002-embercade-screenscraper.patch` and its development-override/personal-account native
  helper `EmbercadeScreenScraper.h`; sibling reference sources are unchanged.

Original ScreenScraper-sprint automated baseline: 473 unit/integration tests
passed; the later state/secret handoff passes 541 tests. Production stage,
runtime smoke, frontend-library smoke, 14-preset shader smoke and
stage/installed Doctor pass. Native tests include the real media-shard host and
reject deceptive hosts,
plain HTTP and credential-bearing URLs outside the approved DNS namespace.
The full tracked/untracked/build/cache/`.work` credential scan finds no passwords
or new credential disclosures. Four identifier-only matches are preexisting
public ownership/game-profile references, not scraper requests or secret values
introduced by this integration; they were inspected with the identifier redacted.

No third-party licensing/public-release gate is cleared by scraper integration.
Embercade remains PRIVATE; bezel licensing review remains paused.

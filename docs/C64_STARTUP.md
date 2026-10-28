# C64 disk startup without optional JiffyDOS ROMs

Giana Sisters reached the C64 BASIC screen with `?DEVICE NOT PRESENT ERROR`
because Configgen forced JiffyDOS on a fresh desktop installation. The D64
itself was passed correctly and attached by VICE; no quoting, file-extension
or missing-media workaround is needed.

The 28 October Garuda log identifies VICE x64 3.10 (`9d79838`, built
24 September 2026). It records the exact D64 as one content argument, successful
image detection/attachment, missing JiffyDOS C64/1541-II ROMs, `Failed to set
drive type`, and the aborted autostart. The
[official VICE Libretro documentation](https://github.com/libretro/vice-libretro#jiffydos-support)
requires external ROMs for JiffyDOS; the core's embedded stock ROMs do not
satisfy that optional setting. The targeted upstream reference checked here is
`6cbc44add8b0a03791b343712dc63dc1edad2675`; the actual runtime build remains
identified separately above.

Patch `0039-embercade-c64-optional-jiffydos.patch` changes only the C64 desktop
default to `vice_jiffydos = "disabled"`. It retains the embedded stock ROMs,
true-drive/core autostart behavior and original media arguments. Explicit
`c64.vice_jiffydos=enabled` remains available for an intentionally configured
JiffyDOS installation; the existing `c64.retroarchcore.vice_jiffydos` override
still has final priority. No BIOS download, mandatory extra firmware, automatic
ROM conversion, fixed `LOAD` command or installer step is introduced. C128 and
non-desktop Batocera behavior keep their original defaults.

## Verification

A private copy of the owner's selected D64 was run with the actual managed
VICE core in two disposable profiles, with no external system ROMs. The final
comparison used SDL dummy video/audio, a short private runtime path, disabled
desktop companion and a read-only host namespace with hidden input devices.
Only each test profile was writable; the disk copy was read-only and VICE disk
write protection was enabled. Original collections/profiles were not changed.

- JiffyDOS enabled: the same drive-type failure, `NO Loading` and autostart abort.
- JiffyDOS disabled: drive 1541 retained, `Loading`, `Ready`, `Starting program`
  and `Done`. Both final runs completed 12,000 frames and exited zero.

Earlier headless setup attempts stopped before an actual loading comparison:
null audio was unsuitable, and the long private XDG runtime path exceeded the
Wayland socket path limit. They are not counted as successful runtime tests.
The final comparison resolved those test-environment limits without host changes.

Automated generator checks cover the C64-only desktop default, unchanged other
options/C128/non-desktop behavior, explicit setting and final core override
priority, replacing the stale generated value, and preserving a single complete
media argument for D64 (uppercase extension), D81, CRT, T64, TAP, PRG, M3U and
ZIP paths with spaces/punctuation. Those synthetic files are used only in
config-generating dry runs; they are never booted as games. Cartridge/tape
execution and visible gameplay/controls/exit are separate owner checks. The
successful unattended D64 autostart is not a claim of complete game acceptance.

The final isolated regression suite passes 848 tests (843 passed, five expected
native opt-in skips), including GTK lifecycle checks and all 52 pinned
structural routes. All three targeted C64 tests pass (including eight media
format dry runs and five explicit-override cases). Runtime preparation/smoke,
license-scope checks and diff checks pass.

Private diagnostic evidence is kept under `.work/c64-jiffydos-2026-10-28/`.
Existing installed/Gold and previous accepted images are preserved. No push,
public release, host package/driver change or remote deployment is authorized.

## Separate private correction candidate

- Image: `dist/private-c64-start-2026-10-28/Embercade-1.0-C64-Start-Test-x86_64.AppImage`.
- Exact clean source: `d2194fc8b591dff05d953e1c3a27f15995c2432e`.
- SHA-256: `a3348017d24d1fa6d8b96118a591da1bcb3e77130a73fa7c5eda05b2c809c130` (414464504 bytes).
- Matching sources/notices: `dist/private-c64-start-2026-10-28/source-kit/Embercade-1.0-sources-and-notices.tar.gz`. SHA-256: `a54227f8dab480f2b66950c47c76557e1c7d0d798e322bd0ca230aee0230d77c`. All 1,810 internal regular-file checksums pass; patch 0039 is in the own-source archive and the fully patched generator matches the build input.

The extracted package passes its full audit and both disposable help probes.
The actual packaged Python/Configgen confirms the stock-ROM C64 desktop default.
Per-user RetroAchievements and native clipboard entry points remain present;
the old private key is absent from all 5,685 payload files. Seven protected
Gold/canonical/installed/earlier candidate image hashes remain unchanged, and
the original Stage is restored.

Only the previous test frontend owned by this chat was closed, after verifying
its process identity, ancestry, executable hash and absence of running games.
The separate corrected candidate is open on Garuda with existing owner settings
for the requested troubleshooting flow. No game was started automatically, no
installed AppImage was replaced and no remote host was accessed.

## Garuda owner acceptance — 28 October 2026

The owner confirms that Giana Sisters D64 now starts successfully and that
Start + Guide returns to the same frontend. This accepts the visible disk
startup and controller-exit/return case on Garuda with the candidate above.
Other C64 games/formats and the laptop/living-room systems are not inferred
from that result. The frozen image/source-kit identities stay unchanged, and
no push, release or deployment is authorized by this acceptance.

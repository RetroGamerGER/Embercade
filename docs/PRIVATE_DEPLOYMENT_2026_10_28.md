# Private per-user RetroAchievements and C64 update — 28 October 2026

The owner explicitly requested replacing the active AppImages on all three
reference PCs under their existing filenames, retaining links and settings.
The remaining manual tests belong to the owner. This authorizes private file
replacement only; no push, public release, tag or visibility change occurred.

The deployed file is the already-built and MainRig-tested C64 correction
candidate. No new build or runtime/source change was needed for deployment.

- Canonical image: `dist/private-c64-start-2026-10-28/Embercade-1.0-C64-Start-Test-x86_64.AppImage`.
- Exact clean build source: `d2194fc8b591dff05d953e1c3a27f15995c2432e`.
- SHA-256: `a3348017d24d1fa6d8b96118a591da1bcb3e77130a73fa7c5eda05b2c809c130`.
- Matching source kit remains beside the canonical image under `source-kit/`; its SHA is `a54227f8dab480f2b66950c47c76557e1c7d0d798e322bd0ca230aee0230d77c`.
- Manifest remains PRIVATE / BLOCKED for public release, with protected per-user
  RetroAchievements Web API handling. No personal shared build key is embedded.

## Retained active paths

| Host | Existing filename/path retained |
| --- | --- |
| MainRig | `~/AppImage/Embercade-1.0-Release Candidate-x86_64.AppImage` |
| MainRig | `~/.local/share/embercade/application/Embercade.AppImage` |
| EmbercadeLaptop | `~/AppImages/Embercade-1.0-AutoGraphics-x86_64.AppImage` |
| EmbercadeLaptop | `~/.local/share/embercade/application/Embercade.AppImage` |
| WohnzimmerPC | `~/Applications/Embercade/Embercade-1.0-x86_64.AppImage` |

All five active copies have the SHA above. Matching manifest/checksum sidecars
use each retained filename; applicable image-ownership hashes are updated.
Desktop entries, wrapper files and Steam shortcut files/routes retain their
original hashes. The older living-room rollback image was not a target.

## Verification and recovery

A fresh inventory found all three PCs reachable, the five active targets at
the prior `938df3ab` image hash, user ownership, sufficient local storage and
no running frontend/emulator. Replacement was guarded against concurrent image
changes and process starts. Each original image, sidecar and applicable
ownership record was backed up and hash-verified before atomic replacement.

On every host, originals and `deployment.json` are under:

`~/.local/state/embercade/image-backups/user-api-c64-2026-10-28-a3348017/`

The receipt records the exact paths, old/new hashes, original modes and verified
rollback files. Recovery restores that complete recorded set with the relevant
frontend/emulators stopped; image and ownership metadata must stay consistent.
The separate private transfer input remains in the matching `image-staging/`
directory for this deployment. Canonical Gold/older artifacts and the current
matching source kit remain unchanged.

All three hosts pass installed image/sidecar and rollback checksum checks and
an AppImage `--help` probe using disposable HOME/XDG directories (exit zero).
Protected config/input/controller/SSH and existing secret-file hashes remain
unchanged. No user profile, firmware, EEPROM, save, ROM/BIOS/media collection,
driver or package was reset or installed. No interactive frontend/game or
remote display session was stopped or started for this replacement.

The personal RA Web API file already existed on MainRig and is preserved.
It was absent on the laptop and living-room PC. No credential/config file was
copied between machines. The owner can enter the personal key in the existing
optional settings field on each of those PCs for frontend views; normal
emulator login remains available independently.

This is deployment/hash/CLI verification, not new visual/gameplay acceptance
on the remote hosts. MainRig's previous personal-key/paste/progress and Giana
Sisters startup/Start + Guide acceptance remain documented separately. That
deployment-time pending status is superseded by the owner acceptance below;
specific unreported checklist actions are not invented from the broad result.
Private receipts and host-specific inventories are in ignored
`.work/deploy-user-api-c64-2026-10-28/`; no secrets or host addresses are included
in this report.

## Owner acceptance — 28 October 2026

After testing the deployed version, the owner accepts all three reference
systems and reports that everything works perfectly except for the known
16:10 bezel issue on the laptop.

| Host | Owner result | Remaining known limitation |
| --- | --- | --- |
| MainRig | Accepted | None reported in this acceptance |
| EmbercadeLaptop | Accepted with known limitation | 16:10 bezel cropping/proportions |
| WohnzimmerPC | Accepted | None reported in this acceptance |

This closes overall three-host functional acceptance for the artifact identified
above. It does not assert every possible title/format or independently enumerate
all setup/error-path tests. The 16:10 issue remains documented and is not treated
as repaired. No runtime, driver, host, artifact or source-kit change follows
from this confirmation. The private publication hold remains: no push, public
release, tag or visibility change without the owner's further instruction.

# Public distribution preparation

The owner authorized a separate public candidate, source cleanup and release
notes. Upload, push, tags, releases and repository visibility changes remain
on hold. The accepted functional behavior and known laptop 16:10 bezel issue
are unchanged.

The current installer supports Arch Linux, CachyOS and Garuda only; host
packages use pacman. The visible German/English platform notice states that
existing restriction. An early localized explanation now prevents unsupported
hosts from opening the installation terminal; the independent backend guard
still blocks package execution. Supported package commands and the allowlist
are unchanged.

The prepared files use a clean standalone project history. The original private
repository retains all branches, tags, old reports and builds; it must stay
private unless its separate historical contents are deliberately reviewed.
Changing the original repository's visibility is not equivalent to publishing
the clean export.

## Files for publication review

The prepared directory contains the AppImage, its manifest/checksum, complete
matching source/notice archive, clean project Git bundle, release notes, build
identity/verification record, handoff and one SHA256SUMS file covering the set.
Use only that explicit set. Private history backups, `.work`, credentials, old
private images, machine inventories and deployment receipts are not uploads.

The Git export has one new root commit and a `main` branch, with no old branches,
tags or remote configuration. The AppImage and source kit identify this same
public commit. Its tree matches the sanitized preparation tree. The original
private `v1.0.0` tag is retained and is not moved to the new build. A later public
repository/tag choice belongs to the publication review.

A recipient can inspect the complete project history from the bundle:

```sh
git clone --branch main Embercade-1.0-public-source.bundle Embercade-public
git -C Embercade-public log --oneline --all
```

The bundle contains project sources and notices, while the larger matching
source/notice archive additionally supplies covered upstream sources and
rebuild/replacement instructions. Keep the latter available beside the binary;
the project bundle or automatic GitHub source ZIP alone is insufficient.

## Verification boundary

The artifact's metadata says PUBLIC / PREPARED_NOT_PUBLISHED. The source receipt
also states that publication approval is false. These labels describe local
preparation and never claim that uploading has occurred. Default developer
packaging remains private. Production and per-user RetroAchievements checks
apply to public preparation; dirty or development inputs are rejected.

The existing three original branding masters are retained byte-for-byte. Their
exact path, size and hash entries in `compliance/public-source-files.json` make
the earlier general 5-MiB rule explicit; changed or unrelated large files still
fail. The scope/attribution and rights limits of that artwork do not change.

The final verification records hashes, matching source identity, one-root Git
history, source/archive integrity, no known owner paths or old personal RA key,
no personal state/content, complete notices and isolated help probes. The
runtime/native frontend/resources are compared with the accepted private
candidate. Packaging changes do not imply a new interactive acceptance run;
no normal profile or remote host is used for preparation.

## After approval

Choose the public repository and tag without exposing the old private history
or release assets. Upload only the reviewed set, keep the complete matching
sources accessible, include the release notes/16:10 limitation, and verify the
server-side asset checksums. No remote destination is preconfigured and no
push/release action is executed by this preparation.

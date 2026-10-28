# Local source and notice preparation

This directory prepares matching source/notice material for a later approved
Embercade release. It does not publish anything or change an installation.
The current public preparation uses the same sanitized parentless source commit
for the AppImage, project bundle and complete source kit. Its manifest records
`PUBLIC_CANDIDATE_NOT_PUBLISHED`, with publication approval still false. Nothing
is uploaded automatically. Older private kits retain their exact old identities
and must not be relabelled as sources for the new candidate.

`sources.lock.json` identifies 33 collected original source archives, including
all 23 non-Batocera installed Python distributions, the separately vendored
certifi release, native source libraries and pinned upstream trees. The six
Batocera distributions and UI builder come from the pinned Batocera archive.
Permissively licensed sources are included as a convenience; that does not
assert a source-disclosure duty for every dependency.

`notices.lock.json` identifies original supplemental notices by source/extent
and integrity hash. Existing notices inside distributions, resource collections
and `packaging/appimage/licenses` remain in place. The hashes protect these
copies; hash identity is not the legal test for source origin or permission.

To prepare another local kit, use the exact binary and its manifest, matching
source locks/cache, and a clean committed preparation tree:

```sh
python compliance/prepare_sources.py \
  --cache /path/to/verified-source-archives \
  --image /path/to/Embercade.AppImage \
  --manifest /path/to/Embercade.manifest.json \
  --output /path/to/a-new-private-output-directory
```

The tool verifies inputs, uses immutable Git archives, applies the complete
original patch sets with the existing build recipe's patch semantics, records
the patch results, and writes a source kit, manifest and checksums.
It never archives an unfiltered `.work` tree, follows user content, reads secret
build inputs, modifies the binary or uploads files. Output must not exist.
Source extraction rejects traversal and links escaping its extraction root.
The binary's original source commit is retained even when legal docs are newer.

For a future different binary, refresh source/version/notice correspondence;
do not relabel this kit as matching an unexamined build. The owner's separate publication approval is still required. The frontend
uses per-user RetroAchievements keys rather than a shared personal build key.
Publish the matching source kit and notices alongside the authorized binary
with equivalent download access, without an NC condition on upstream rights.
Do not rely on an automatic Embercade-only GitHub source archive or an unissued
written offer. Keep the source download available for the binary distribution.

See [rebuilding and replacement](REBUILDING.md) and
[the delivery review](../docs/THIRD_PARTY_DELIVERY.md).

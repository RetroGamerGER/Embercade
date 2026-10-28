# Prepared public distribution — 28 October 2026

The requested local preparation is complete. No files were uploaded, no refs
pushed, no release/tag created, no repository visibility changed and no host
installation replaced. The accepted functional runtime is preserved, including
the documented laptop 16:10 bezel cropping/proportion limitation.

## Identities

- Clean standalone public source: `e28f90b1f56b36cb4250d2fe458a559979335d0e` (one root commit on main; no remote or tags).
- AppImage: `dist/public-preparation-2026-10-28/Embercade-1.0-x86_64.AppImage`.
- AppImage SHA-256: `204253d5b1a514d38e3bd57bdf26862cb525af127a0df7baf5ac4ec61e87302e`.
- Complete matching sources SHA-256: `31cfcb7aeeab99ea4f4c74f6c6f3df5d093c2450f47c7e161c160afd82104233`.
- Ten review files, including source Git bundle, source/image manifests, release
  notes, handoff, BUILD_INFO and SHA256SUMS, are in the same prepared directory.

The original private history is retained and backed up privately. The public
bundle is a fresh independent root, not a rewrite or clone exposing the old
private branches, commits, tags or release assets. Its tree matches the clean
preparation tree at 04d4eb6. Receipt-only changes in this original repository do
not change the frozen public source or artifact identities above. Use the clean
public bundle for the later approved publication, not a visibility change of
the original private repository.

## Verification

- Full isolated suite: 852 tests, 847 passed and five expected native opt-in
  skips; includes GTK and all 52 structural routes. All 36 targeted packaging,
  source-delivery and license checks, runtime smoke and public-tree audit pass.
- Actual AppImage extraction/package audit, isolated AppImage/frontend help and
  packaged Configgen C64 stock-ROM probe pass. Metadata is PUBLIC /
  PREPARED_NOT_PUBLISHED, with per-user RA authorization and no legacy marker.
- Functional program contents, permissions, symlinks, native frontend, runtime
  and resources match the three-host accepted private candidate exactly. Only
  five legal-document/Stage-manifest paths differ; outer release metadata also
  changes. This is not a new interactive acceptance claim for packaging bytes.
- Complete sources: 1,810 internal file checksums pass. The public Git bundle
  clones independently to one root commit; public-tree audit passes, with no
  old tags. Binary source and source-preparation commit are the same public ID.
- 2,291 source/notice files are checked for the known owner paths/network
  identifiers and old personal RA key; none matches. Every packaged regular
  file is also checked for the old key. Credential headers/user state are absent.
- The three original artwork masters are retained unchanged under exact
  path/size/hash exceptions. Their metadata was inspected without decoding or
  changing the original images. Unreviewed large files still fail the audit.
- All 17 pre-existing inventoried images, including local installed copies,
  retain their original hashes. Original non-master refs/tag remain unchanged;
  original master history remains an ancestor and its private backup verifies.

The first packaging pass had different generated file modes under a restrictive
umask. That intermediate package/source kit was retained privately and excluded
from the final review set. The corrected pass uses the accepted mode baseline
and is the one identified above. All nine data-file entries in final SHA256SUMS
verify; SHA256SUMS itself is the tenth file.

Upload/push/release, public repository destination and tag remain for explicit
owner approval. The original private v1.0.0 release/tag is not moved. Detailed
local evidence, the isolated source checkout and private history backup remain
under ignored `.work/public-preparation-2026-10-28/`, outside the upload set.

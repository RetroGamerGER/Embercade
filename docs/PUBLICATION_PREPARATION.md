# Embercade 1.0 release contents

The public repository is [https://github.com/RetroGamerGER/Embercade](https://github.com/RetroGamerGER/Embercade); the release is
[v1.0.0](https://github.com/RetroGamerGER/Embercade/releases/tag/v1.0.0). The private development history and older private builds
remain separate and are not part of this release.

## Verify the downloads

Keep the ten release files together and run `sha256sum -c SHA256SUMS`.
The checksum file covers the other nine files. Make the AppImage executable,
then run it to open the setup wizard. The installer supports Arch Linux,
CachyOS and Garuda only and uses pacman for optional host packages.

## Sources and licenses

`Embercade-1.0-sources-and-notices.tar.gz` supplies the complete matching covered
sources, patches, build/install inputs, notices and LGPL replacement/relinking
instructions. Keep it available alongside the AppImage. The project Git bundle
and GitHub's automatic source ZIP alone do not contain all covered upstream
sources and do not replace the complete archive.

The binary source commit is `cb00b093ff0e87d2462ee060bb4b7717afda43dc`.
The clean source bundle contains that exact build source. The public repository
adds the final publication-documentation commit, identified in BUILD_INFO.
No program behavior or AppImage bytes changed for publication. The original
build/source manifests retain their preparation-time metadata; publication
approval and destination are recorded separately in BUILD_INFO.

The functional baseline was accepted on all three reference systems. The known
16:10 laptop bezel cropping/proportion limitation remains. See RELEASE_NOTES
for requirements, tested environments and per-component license terms.

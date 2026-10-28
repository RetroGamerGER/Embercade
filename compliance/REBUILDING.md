# Rebuilding and replacing covered components

The source kit contains original archives, the exact Embercade source archive,
fully patched Batocera/EmulationStation trees, all patch/build/install inputs and
a separately identified legal supplement. Original notices and terms apply.
GPL/LGPL components may be studied, modified, rebuilt, replaced and redistributed
under their own terms, including commercial permissions. Embercade's PolyForm
scope adds no restriction to those rights or to reverse engineering needed to
debug modifications to the LGPL components. No signing key or activation is
required for a modified upstream component. Credentials are access parameters,
not a withheld program implementation; supply your own authorized provider input
or build without that provider for local development.

## Batocera and the Python packages

The six installed Batocera packages and UI builder are supplied at the pinned
commit, with all Embercade changes applied under `modified/batocera/batocera`.
`python-src` and the relevant core/emulationstation/emulator package directories
are included; unrelated OS/buildroot sources and emulator binaries are not
part of this AppImage. `scripts/runtime-prepare` in the exact Embercade archive
records package selection, patch order and installation. Pyudev's LGPL source,
pathspec's MPL source, certifi's MPL-covered certificate source and all remaining
Python sdists are included at the installed versions. Pip's source includes its
vendored dependency tree and original vendor notices.

Extract the AppImage to a directory you control (`--appimage-extract`) and make
the extraction writable. The installed editable Python sources are at
`squashfs-root/usr/share/embercade/runtime/venv/lib/python3.14/site-packages`.
Replace/reinstall the desired package there using a compatible CPython 3.14
environment, or modify its source, then start the extracted `AppRun`. This does
not require changing the original read-only image. The separate backend remains
MIT; it is supplied as source beside the independent application.

## FreeImage and its LibRaw component

The complete unmodified FreeImage 3.18.0 source archive includes all embedded
codec sources, interfaces and makefiles. Its original FIPL/GPL alternative
notices are retained; Embercade uses the FIPL alternative for FreeImage's own
code, with LibRawLite's independent LGPL 2.1 and the other embedded libraries'
original terms. This is not a grant over every codec under FIPL. The original
LibRaw copyright also preserves its unused CDDL alternative.

`scripts/frontend-libs-prepare` records the exact generic x86-64 compilation
flags and SDL2_mixer feature selection. Build the included FreeImage sources
with that make invocation, modifying LibRaw as desired. The complete library
sources are supplied so the combined library can be relinked. Its dynamic
`libfreeimage.so.3` is replaceable in the extracted application's
`usr/share/embercade/lib`; preserve its SONAME/ABI and symlink. The frontend's
complete MIT source, embedded dependencies, patches and CMake inputs are also
provided, permitting rebuilding the caller if necessary. Nothing requires an
exact byte-for-byte reproduction of the distributed binary.

## AppImage runtime and static libfuse

The AppImage loader is the MIT type-2 runtime at
`dd6cebedcbddde9c82f89b011e8e1d40b6e43868`. Its static libfuse 3.15.0 library
retains LGPL 2.1. Both complete source archives, the actual `mount.c.diff`,
squashfuse 0.5.2 source and upstream Docker/Makefile recipes are supplied.
This supplies the source form of the program using the library, allowing a
modified library to be rebuilt and relinked under LGPL 2.1 section 6(a), rather
than claiming a static binary alone satisfies replacement rights.

To rebuild, unpack the type2-runtime tree. Its
`scripts/docker/Dockerfile` lists the Alpine 3.21 build toolchain, static
zstd/zlib/mimalloc development dependencies and system headers. In a separate
build environment, follow `scripts/common/install-dependencies.sh`: unpack the
supplied libfuse archive, apply the supplied `patches/libfuse/mount.c.diff`, make
your own changes, then use Meson/Ninja with `--default-library static`. Unpack
squashfuse, run `autogen.sh`, `configure LDFLAGS=-static`, build/install it and
its headers. The included archives replace the script's two download steps.
The remaining compiler/system dependency packages can come from the build
environment, without changing the user's desktop installation.

Write the recorded runtime commit to `src/runtime/version` (upstream's workflow
normally does this), then run `make` in `src/runtime`. Its complete linker
command is in that Makefile. For a local repack, use the pinned appimagetool
with `--runtime-file /path/to/your/rebuilt/runtime` against the extracted
AppDir, as shown in Embercade's AppImage build implementation. Appimagetool is
a separate build tool, not a shipped runtime dependency. A recipient may also
use the extraction directly and bypass the loader.

The original runtime recipe does not fix exact Alpine APK revisions or an
immutable container digest. That recorded reproducibility limit remains;
permissive musl/zstd/zlib/mimalloc notices are retained. It does not change the
identified libfuse version/patch or require identical rebuilt binary hashes.
No new runtime or AppImage was built during this license-only preparation.

## SDL2_mixer, native wheels and font resources

SDL2_mixer's source/build recipe and the complete three included decoder
headers are supplied. Preserve its zlib/MIT/public-domain alternatives as
recorded; other codecs disabled in the recipe are not claimed as bundled.
Pillow's wheel aggregate includes the notices for its native codec/font/X11
libraries and static subcomponents; the package is not uniformly MIT-CMU.
FreeType is used under FTL, and zstd under BSD, with their required notices
retained. This software is based in part on the work of the FreeType Team.
The uvloop/libuv and PyYAML/libyaml notices are separately included. These
permissive components do not acquire a new source obligation from this kit.

The font OFL, Apache and Ubuntu Font Licence notices accompany the unchanged
fonts, with their embedded original copyrights retained. Font reserved names,
individual terms and trademark exclusions remain applicable. Theme CC terms
do not replace the fonts' own licenses. No font, sound or other resource was
converted, altered or replaced by this preparation.

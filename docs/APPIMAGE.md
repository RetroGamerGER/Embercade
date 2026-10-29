# Embercade AppImage

**Installer supports Arch-based Linux distributions.**

Automatic package installation recognizes `ID=arch` or an exact `arch` token in
`ID_LIKE` and checks that Pacman is available. Existing repositories and optional
existing AUR helpers are reused with explicit consent; no repositories or helpers
are installed automatically. Non-Arch systems remain ineligible for automatic
Pacman installation. The v1.0.1 update includes this installer behavior; v1.0.0 and earlier builds remain unchanged. Broader
distro recognition does not establish new runtime, GPU or gameplay compatibility.

PSP/Xbox source folders are optional for setup, with an explicit Skip for now
button and preserved existing settings. Missing files still need attention before
using those systems; the general BIOS folder is not silently selected as a source.

**Embercade 1.0 feature freeze reached.** This packages the frozen Production
runtime; it is not a new launch/setup/controller architecture. The classic
user-local installation remains the golden reference. The repository and image
remain PRIVATE. Functional acceptance is separate from public release rights.

## Bundle and host boundary

`AppRun` resolves its own directory and delegates to `usr/bin/embercade`.
`usr/` is an unchanged, hash-verified Production Stage. The existing prefix API,
Bubblewrap namespace, first-run wizard, Doctor, core/provider resolvers, Theme
Library and launch-scoped cleanup are reused. Startup works independently of
the checkout, `.work`, classic prefix and current directory.

Included: Embercade Python modules, pinned launcher/configgen venv packages,
generic x86-64 frontend, launch helpers, existing default Carbon/resources,
pinned shaders/decorations, branding, production metadata, FreeImage and
SDL2_mixer. The static type-2 AppImage runtime and scoped upstream notices are
also included. No runtime-wide license is asserted.

Carbon is the only packaged theme. The build refuses additional theme folders,
download workspaces or a replaced theme symlink, even with a valid Stage manifest.
Downloaded/active themes remain exclusively in the user's persistent data.

**The interpreter is deliberately host-provided CPython 3.14 at `/usr/bin/python`**,
including its stdlib and the ABI-compatible evdev adapter. `AppRun` checks the
interpreter implementation and major/minor version `(3, 14)`, rather than one
fixed patch release. A separately named Python executable does not satisfy
that check if `/usr/bin/python` points to a different version.
The image supplies the existing pinned Python packages, not a separately
rebuilt interpreter. AppRun reports
missing/incompatible Python before launching. This preserves the golden Stage;
it is a private supported-host build, not a generic all-distribution AppImage.
The first-run wizard additionally uses host GTK3/PyGObject. Its German/English
language preference is external XDG configuration and survives normal updates.
For standalone decorations on KDE/Hyprland Wayland, optional host
`gtk-layer-shell` is offered through the existing bootstrap. Every standalone
decoration renderer also needs host `python-cairo`, including Gamescope's
external-overlay renderer. The host check exercises Pycairo's drawing/input-region
types and PyGObject's Cairo bridge without opening a window; an installed
layer-shell typelib or native Cairo library alone is insufficient. Missing
`python-cairo` is offered through the existing optional host-software flow.
See [LAPTOP_STANDALONE_BEZELS.md](LAPTOP_STANDALONE_BEZELS.md).
Display queries use
KDE's `kscreen-doctor`, Hyprland's `hyprctl`, or X11/Gamescope's `xrandr`; these
are host tools, not bundled drivers. See [GLOBAL_GARUDA_AUDIT.md](GLOBAL_GARUDA_AUDIT.md).

The runtime/ABI checks use host `readelf`; missing `binutils` is detected and
offered through the existing host bootstrap.

Host dependencies remain Bubblewrap, SDL2, FreeType, FriBidi, curl/TLS, VLC and
its codecs, udev, ALSA, GL/GLU, pugixml and the normal C/C++ runtime. The complete
direct frontend SONAME classification is recorded in the manifest and checked
by existing Stage/Doctor library inspection. Wayland/Xwayland, audio sockets,
input/DRI devices and permitted Wii HID nodes use the existing narrow mounts.
Delegated Xenia/shadPS4 need the host systemd user manager and their own runtime
requirements. No Mesa, Vulkan ICD, NVIDIA/AMD userspace driver or libdrm stack
is copied. Graphics use the host stack on the two tested AMD reference hosts.
Compatibility with older glibc/Python or other distributions is not established.

## State, first run and coexistence

Writable state is unchanged: external Embercade XDG config/data/cache/state
and private session runtime. See [the state/secret contract](STATE_AND_SECRETS.md).
All CLI actions reject state/write targets inside the prefix/AppDir before
mutation. The mounted image is read-only; bytecode writes are disabled.
Image-adjacent `.home`/`.config` portable sidecars are refused, not created.
No folder beside the image is used as a replacement home or configuration root.

ROM/BIOS sources stay externally owned/read-only. Scraping retains only the
existing `gamelist.xml` and media-submount exception. Imported cores/providers,
PPSSPP assets, Xemu working files, downloaded themes/selection, saves, screenshots
and personal ScreenScraper account data remain external. Production application
authorization is supplied only to the frontend builder from its private source;
only the compiled frontend contains it, and it is extractable. No loose source
file, debug password or personal account enters the image.
Host emulator profiles and source core/provider folders are never modified.

An unconfigured start opens the existing wizard in a desktop session. A valid
configuration proceeds directly to the same frontend without repeating setup.
Arguments such as `doctor`, `wizard` and `setup` remain the same CLI operations.
The wizard is desktop-tested; Gamescope wizard usability is not required by
the owner. Gamescope frontend acceptance is a separate real Steam-session test.

Classic and AppImage intentionally share the same XDG state by default, for
**sequential use only**. Concurrent sessions can race settings, saves and
gamelists; no concurrency or cross-host merge mechanism is introduced.
Explicit existing XDG overrides can provide separate profiles. Neither runtime
overwrites the other's application tree.

## Build, verify and reproduce
Production builds require the owner-only two-field source named by
`EMBERCADE_SCREENSCRAPER_BUILD_SECRET_FILE` (path only; never values in argv).
The builder generates a private forced-include header and verifies the actual
frontend mode/hash through Stage and image extraction. Missing production
configuration fails. Explicit `--development-without-screenscraper` builds are
labelled development and cannot silently stand in for a complete candidate.
See [SCREENSCRAPER_PRODUCTION_FIX.md](SCREENSCRAPER_PRODUCTION_FIX.md).


```sh
./scripts/appimage-tools-prepare       # explicit one-time network preparation
./scripts/stage-build                 # normal verified Production build
./scripts/appimage-build              # offline packaging of that Stage
```

Output: `dist/Embercade-1.0-x86_64.AppImage`, accompanying `.manifest.json` and
`.AppImage.sha256`. The locked official appimagetool release asset is 1.9.1
(its internal banner calls itself a continuous build), source `8c8c91f…`, SHA-256
`ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0`.
The explicit type-2 runtime is 20251108, source `dd6cebe…`, SHA-256
`2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d`.
Exact URLs/revisions are in `packaging/appimage/build.lock`.
No latest-runtime download occurs during packaging.

The tool's own mksquashfs 4.6.1, zstd, root ownership, one processor, fixed
timestamps and disabled xattrs are used. The default epoch is the input Git
commit timestamp. Two fresh complete builds with the same Stage, packaging
inputs, source identity and epoch produce byte-identical images and manifests.
A separate focused fixture also checks different build umasks. This is
packaging reproducibility, not proof that a full compiler/dependency rebuild
is bit-identical across arbitrary machines.

The machine manifest records source revision, Stage hash, every packaged file,
library boundary, excluded state, tool pins, notices, compression recipe and
final image hash. The builder extracts the actual output and verifies it, not
just the source AppDir. Build-only tooling is not staged. Compiler source-prefix
remapping and stripped frontend debug data prevent personal build paths in
shipped binaries. Full-file AppDir/extracted-image checks supplement the existing
credential/content audit. Operational build reports stay ignored in `.work`.
Local pip origin records/RECORD references are pruned only from the Stage copy;
package identity and notices stay intact. The full-file home-path check exempts
only two exact, generic upstream pip/aiohttp documentation comments, never their
whole files. The classic Stage cannot be a packaging destination or output target.

For independent verification:

```sh
/path/to/Embercade-1.0-x86_64.AppImage --appimage-extract
./scripts/appimage-build --audit-appdir /path/to/squashfs-root
/path/to/Embercade-1.0-x86_64.AppImage doctor
```

Runtime source/notices are indexed under `packaging/appimage/licenses` and copied
into the image. The upstream static-runtime recipe does not pin every Alpine
package revision; that provenance limit is explicit in its index. Preserving
these notices does not resolve the paused bezel audit, Carbon/shader attribution,
branding ownership or root-license strategy. ScreenScraper build authorization
is covered by the owner's explicit 2026-10-25 integration instruction.

## Steam and update

With Steam fully stopped, run the AppImage's existing integration command:

```sh
/path/to/Embercade-1.0-x86_64.AppImage steam --dry-run --replace-existing
/path/to/Embercade-1.0-x86_64.AppImage steam --yes --replace-existing
```

`--replace-existing` explicitly switches the one Embercade shortcut from classic
to AppImage (or back using the classic CLI). Its existing appid, launch options,
tags and artwork identity are preserved; foreign shortcuts/artwork are untouched.
It does not register a temporary mount or add a duplicate entry. Extracted
AppDirs cannot register transient paths. Start Steam yourself afterwards and
launch from the real interactive Gamescope session; SSH-triggered Steam starts
are not E2E evidence. Existing overlay-plane conflicts/limitations remain.

AppImage update means replacing the closed executable file at the same path.
External state remains untouched. There is no self-updater or automatic download.
Classic installation/update/uninstall still uses its normal verified installer,
never an AppImage purge or a new setup backend. The visible product label is
centrally `EMBERCADE 1.0`; Python/package identity stays `0.1.dev0` intentionally.
The owner-approved loading screen retains its existing Embercade logo, progress
and minimum duration without an additional version caption. Menu/About/window,
wizard and product metadata use the central 1.0 identity independently of themes.

## Acceptance

The Garuda blank-install fixes and their current acceptance limits are tracked
in [GARUDA_BLANK_INSTALL.md](GARUDA_BLANK_INSTALL.md). Host bootstrap now
supports Garuda through the same explicitly confirmed pacman infrastructure;
Xemu no longer needs a prepared EEPROM source. This does not broaden the
image's existing CPython/desktop-library contract or establish new gameplay E2E.

At the original packaging milestone, the complete source suite passed **578 tests**; runtime, frontend-library,
shader and Stage Doctor smokes pass. The verified Production Stage SHA-256 is
`a8612d6def70b249785964bb2e51be82965dc15bf7d856e4afa4b23494bce033`.

The owner completed the requested real AppImage E2E on Garuda/Hyprland and
CachyOS Handheld's interactive Steam/Gamescope session, including return to the
same frontend and normal Quit Embercade. The classic Garuda game/exit/quit
regression also passed. The caption-free splash was subsequently confirmed
visibly on Garuda. At the owner's request, CachyOS Handheld received the same
cosmetic update without another visible run; its Doctor returned status 0.
The final normal updates preserved 16,161 Garuda entries with no changes or
additions, and 198,109 CachyOS Handheld entries with no unexpected changes or
additions. Persistent-state inventories exclude only the owned install manifest.

These functional, update and diagnostic results are recorded in
[PROJECT_STATE.md](PROJECT_STATE.md). Packaging reproducibility passes through
two fresh full builds with identical inputs and byte-identical image/manifest
output. **Private functional GO** is established for the two tested
AMD/CachyOS reference hosts; general distribution portability is unvalidated.
Public release remains separately **BLOCKED** by the
existing licensing/provider-access gates.

## Local public preparation

`python -m embercade.appimage --public-candidate` prepares a separate public
distribution candidate from clean production inputs. Metadata is PUBLIC /
PREPARED_NOT_PUBLISHED; this option never uploads, tags or publishes. It rejects
dirty/development inputs and requires the per-user RetroAchievements frontend.
The default remains private for existing developer workflows. Use a fresh output
directory, retain earlier builds, and supply the exact clean public source
identity. The complete matching source kit and clean Git bundle must accompany
the reviewed release; see [release notes](PUBLIC_RELEASE_1_0.md).

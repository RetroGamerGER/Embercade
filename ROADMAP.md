# Embercade roadmap

This roadmap describes direction, not a promise or schedule. Priorities may
change as desktop compatibility, upstream projects and real-world testing
evolve.

System and provider expansion follows the [older-system product scope](README.md#a-simple-rule):
Embercade is not positioned as a replacement for consoles still sold as current
products. This is project philosophy, not a legal judgment. Existing systems
and compatibility evidence are retained.

## 0.1 — first public release

**Historical status:** implemented initial release-candidate scope under private
development; this section records that earlier baseline. The current visible
product label is `EMBERCADE 1.0`; the packaging identifier remains `0.1.dev0`.
Public release remains blocked by licensing review.

**Bezel licensing review: PAUSED / PUBLIC-RELEASE BLOCKER.** Further
bezel/decoration licensing investigation resumes only on explicit owner
instruction. Existing evidence and working assets are retained without
replacement or stripping. This pause does not resolve licensing or change
PRIVATE status; private development may continue, but public release stays
blocked. See [the release audit](docs/PUBLIC_RELEASE_AUDIT.md#console-decoration-redistribution-rights).

Planned scope:

- user-local installation on tested x86-64 CachyOS/Arch-family desktops;
- Batocera EmulationStation as a normal Wayland desktop application;
- pinned Batocera 44 launcher/configuration behavior;
- isolated Embercade XDG configuration, saves, states, caches and logs;
- existing user-supplied ROM and BIOS collection roots;
- separately installed host emulators and Libretro cores;
- tested RetroArch, Dolphin, PCSX2, RPCS3, Xemu and Xenia Edge routes;
- controller-first navigation and configurable emulator exit chord;
- RetroArch shaders and console bezels;
- standalone PCSX2/Xemu console bezels, with Gamescope production acceptance
  and Hyprland workspace/lifecycle prototype validation;
- setup, Doctor and optional confirmed Arch/CachyOS bootstrap;
- clean return to the same frontend session.

Explicitly outside 0.1:

- bundled or downloaded ROMs, BIOS, firmware, keys or game content;
- bundled emulator binaries, Libretro cores or Xenia Edge AppImage;
- system-wide installation or replacement of the host operating system;
- automatic repository enablement, system upgrades or unattended package work;
- broad distribution support claims;
- Wii special-controller acceptance, wheels, lightguns and other specialist
  hardware;
- automatic updates, cloud services or a public content store.

Before a public release, the scope of the owner-selected
PolyForm-Noncommercial-1.0.0 for independent own software and CC-BY-NC-SA-4.0
for own prose/cleared branding must be approved separately from GPL-bound
integration and original third-party terms. The earlier CC-software proposal
is superseded; final grants and resource-license questions remain unresolved.
The intended own-software model is non-commercial source-available, not OSI
open source. Working assets will not be stripped to force publication. See the
[license scope review](docs/LICENSE_SCOPE_REVIEW.md); no grant is introduced yet.

## 0.5 — comfort and polish

This is a historical completed private milestone. Its acceptance evidence is
retained below; the current product and image use `EMBERCADE 1.0`.

- Completed development milestone: CLI first-run selection of detected or
  manual Core/AppImage source folders, managed user-local import, concise
  Doctor output and isolated RPCS3 firmware-install handoff. This is not a
  public-release claim.
- Branding integration implemented: Embercade hicolor application icon, native
  4K startup splash and local Steam artwork. MainRig install checks and the
  WohnzimmerPC normal offline update pass. Optional native Steam shortcut/artwork
  registration is now integrated into interactive first run and the explicit
  `embercade steam` command, with account selection, backups and idempotent
  preservation of foreign entries. Flatpak Steam host-launcher integration
  remains deferred. Fresh automatic registration, byte-identical repeat runs
  and user-confirmed interactive Steam launches are accepted on both reference
  hosts, including the WohnzimmerPC's real Gamescope session. At that milestone,
  both installed runtimes matched the verified `9ebdca3` payload. User state was
  preserved by the normal update, and Xemu/bezel exit returned to the same
  frontend process without a remaining decoration helper. Normal frontend quit
  back to Steam is also accepted.
- Theme Library completed for both reference hosts: the pinned frontend owns
  catalogue/preview/download/install/activation, with persistent writable XDG
  themes and no separate downloader. AI-Hypertocera/Carbon switches, controller
  navigation, emulator return, full restart and normal reinstall are accepted
  on MainRig Hyprland and real WohnzimmerPC Steam/Gamescope. Downloaded themes
  and active selection survive reinstall. Product splash, icons and Steam
  artwork remain independent of the selected theme. Third-party theme license
  and compatibility guarantees are not implied; the project remains PRIVATE.
- Global frontend product text completed: `EMBERCADE 0.5` was centrally
  supplied at build time, not patched into themes. Carbon and AI-Hypertocera
  display the same text with their own styling on MainRig/Hyprland and real
  WohnzimmerPC Steam/Gamescope. This visible product version does not change
  the packaging identifier or constitute a public release.
- Provider-management polish implemented in the existing setup/import/resolver:
  embedded AppImage identity, content-based reuse, safe conflict/ambiguity
  handling and explicit Doctor diagnoses. No provider downloads, binaries or
  parallel selection framework. Normal committed-payload updates preserved the
  managed provider and user configuration on MainRig and WohnzimmerPC; Doctor,
  visible Xenia launch, Select+Start cleanup and return to the same frontend
  passed on both, including the real Steam/Gamescope session. This milestone is
  complete without changing compatibility/READY status.
- Update UX is complete on the existing verified Production Stage/offline
  installer: read-only preview, current/incoming payload identity, true no-op
  for an identical payload, post-activation verification and preserved-state
  guidance. The MainRig and WohnzimmerPC passed changed-update, repeat no-op,
  Doctor and visible emulator/frontend acceptance; both installed the same
  9,658-file Stage payload. Automatic internet updates and full
  rollback/migration remain later work.

**Historical 0.5 status: feature-complete / feature freeze (private).** Its
verified foundations carry into 1.0. The first 1.0 development feature was a
graphical first-run wizard that delegates to the existing setup and Doctor
backends. Its installed UI passed on MainRig/Hyprland and WohnzimmerPC/KDE;
the normal frontend path passed again from the latter's real Steam/Gamescope
session. HTPC / External Apps and the Batocera-ES GLES3 renderer optimization
are deferred. This is not permission to publish: unresolved asset licensing
and the unresolved project-license scope remain release blockers. Working assets
are not stripped to force a public build.

## 1.0 — complete desktop product

**Embercade 1.0 feature freeze reached.** Private AppImage packaging and central
`EMBERCADE 1.0` branding are implemented. Both reference hosts have confirmed
the requested real AppImage E2E. The caption-free splash is confirmed on MainRig
and its matching WohnzimmerPC update passes Doctor/preservation checks.
Two fresh full packaging builds with identical inputs produce byte-identical
images/manifests. Private functional GO applies to the two tested AMD/CachyOS
reference hosts; no additional features are accepted for 1.0.
The classic Production install is the golden reference. Public release stays
blocked independently by the unresolved licensing/attribution gates.

Current verification: 578 full-suite tests and runtime/frontend-library/shader/
Stage Doctor smokes pass. MainRig has confirmed image startup/menu branding,
the active external theme, ScreenScraper, Libretro and Xemu 4:3 bezel/exit.
The owner confirmed the complete requested image E2E in the WohnzimmerPC's
real interactive Steam/Gamescope session; the classic MainRig regression passes
as well. The final normal updates preserve the inventoried user state. The
WohnzimmerPC cosmetic update had no additional visible run at the owner's
request. See [APPIMAGE.md](docs/APPIMAGE.md) for the supported-host private GO,
packaging reproducibility and independent public-release blockers.

- private offline AppImage packaging of the unchanged verified Production
  Stage, with extraction/hash audit, host-runtime boundary and external XDG
  state; only default Carbon is bundled, while downloaded themes/selection
  remain user data. Public licensing/source-compliance gates stay BLOCKED;
- external-XDG/immutable-image state and separate owner-only ScreenScraper
  Developer/personal-account secret contract (implemented for the current
  Production and private AppImage paths; public provider-access gate remains
  open, see `docs/STATE_AND_SECRETS.md`);
- complete pinned Batocera system coverage, with generic classical Libretro
  route preparation and explicit READY/PREPARED/BLOCKED/UNSUPPORTED evidence;
  empty systems stay hidden until matching content appears. MAME/MESS appliance
  data/work paths and X68000 writable-BIOS isolation remain deferred ports,
  not silently enabled routes (see `docs/COMPATIBILITY_1_0.md`);
- existing theme-independent startup splash with a 2.75-second minimum from
  first presentation, including loading time rather than adding a fixed delay;
  its original embedded logo/native loading text remains without an extra
  generated version line;
- 3DO enabled through the existing generic Libretro/Opera route, with read-only
  BIOS diagnostics and CUE/BIN catalog semantics; two-game MainRig acceptance
  and real interactive Steam/Gamescope second-host acceptance pass
  (see `docs/COMPATIBILITY_1_0.md`);
- stable installer and upgrade contract;
- native Wii Remote/Nunchuk/IR support through existing Dolphin/Batocera
  settings (MainRig and interactive Steam/Gamescope DolphinBar-mode-4 gameplay,
  wireless reconnect and configured gamepad exit accepted;
  MotionPlus, direct Bluetooth/passthrough and multiplayer remain unvalidated;
  see `docs/WII_CONTROLLERS.md`);
- multi-controller foundation using existing EmulationStation player preferences
  and Batocera generators, with real two-player NES/RetroArch and
  GameCube/Dolphin acceptance on MainRig and in the second host's real
  Steam/Gamescope session. RetroArch's tested unique-device live reconnect
  restores both players; P3/P4 hardware, identical-model
  reconnect and standalone hotplug remain open (see `docs/MULTI_CONTROLLER.md`);
- lightgun, wheel and trackball input routes structurally prepared through the
  pinned Batocera/udev/Configgen stack. All three remain **UNVALIDATED** without
  physical hardware; wheel calibration/FFB, pointer focus and real hotplug
  need later device-specific acceptance (see `docs/SPECIAL_CONTROLLERS.md`);
- optional user-supplied shadPS4 AppImage import and pinned PS4 launch route
  (implemented; gameplay/input/audio/exit accepted on MainRig and the real
  second-host Steam/Gamescope session; no downloads or native PATH fallback);
- existing Batocera ES ScreenScraper integration with private runtime developer
  access and narrow gamelist/media writes (implemented; real two-host scrape,
  non-purge reinstall and no-op acceptance pass, see `docs/SCREENSCRAPER.md`);
- polished controller-first setup and settings experience;
- graphical first-run setup (implemented and accepted on both reference hosts),
  now including MainRig clean-install PSP/Xemu source selection and retained
  import status; clearer recovery and frontend emulator/core selection remain;
- clearer per-theme license/compatibility presentation;
- standalone Dolphin GameCube/Wii console bezels through the existing
  PCSX2/Xemu supervisor (implemented for Hyprland and Gamescope; see
  `docs/STANDALONE_DECORATIONS.md`); other emulator/compositor routes remain
  future work;
- emulated-Wiimote desktop gamepad Start/Back/Guide mapping, retaining the
  existing per-game Sideway mode and native Real-Wiimote path;
- deterministic shadPS4 Player-1 assignment with multiple pads remains
  upstream-limited in the tested v0.19.0 build; no global reorder workaround;
- broader controller presets, P3/P4 and identical-model multiplayer/hotplug
  validation, standalone-emulator reconnect and per-system diagnostics;
- broader desktop/session validation;
- optional HTPC / External Apps integration;
- reproducible release artifacts with complete license/source compliance;
- supported save/config migration and backup workflows;
- documented compatibility and regression test policy;
- dependable recovery when a provider or game exits unexpectedly;
- distribution packaging strategy based on validated target environments;
- release documentation suitable for ordinary desktop users.

## Later / 1.x

- additional Linux distributions and packaging formats;
- optional Flatpak-style provider integration where technically appropriate;
- broader Wii hardware/transport and multiplayer acceptance, and physical
  lightgun/wheel/trackball E2E;
- richer theme and decoration management;
- optional save backup/import workflows;
- additional emulator providers and systems after their desktop paths are
  proven;
- accessibility, localization and living-room usability improvements.

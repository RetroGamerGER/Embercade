# Linux graphics and shader compatibility

## Decision (25 October 2026)

Embercade prefers Vulkan for automatic desktop graphics selection when the
existing host probe finds it. Existing explicit system/game settings, raw
RetroArch video-driver overrides and the pinned core-specific OpenGL rules
remain authoritative. No global Vulkan flag is applied blindly across plugins.
Dolphin uses a Vulkan desktop default with its existing OpenGL fallback; PCSX2
uses its Vulkan renderer when detected, retaining explicit OpenGL/software/Auto
choices. RPCS3 already has an availability-aware Vulkan preference. Other
integrations retain their supported renderer paths.

**Shaders are optional and off by default.** The shipped first-run profile has
only `global.shaderset=none` and no system/game effect preset. Bundling the
complete catalogue does not select an effect. The owner clarified this after
the explicit-effect regression tests: prefer a compatible graphics backend,
but activate an effect only after the user's own choice. Preserve existing
explicit selections on update.

The fresh-default check found that the pinned writer left `video_shader_enable`
unset when its rendering map contained `shader: null`. Patch `0033` explicitly
disables it for that desktop None case, also clearing a previously enabled
effect. The real pinned dry run checks both a fresh config and stale enabled
state, with no shader argument and no change to the saved selection. Valid
explicit effects and non-desktop behavior retain their existing path.

Follow-up patch `0032` also gives standalone PPSSPP and Azahar desktop Vulkan
defaults through their existing native configuration writers and host probes.
PPSSPP retains its existing OpenGL fallback; Azahar falls back to OpenGL when
the host probe is unavailable. Explicit OpenGL/software and PPSSPP raw INI
overrides remain authoritative. Their non-desktop defaults are unchanged.
The real pinned writers pass 35 combinations of availability, desktop scope,
automatic values and manual/raw overrides; no native emulator is started with
synthetic content.

The owner rejected a technical Vulkan/OpenGL/shader explanation on the installer
completion page. No such text or new graphics setup step is added. Host software
assessment offers the optional `vulkan-tools` probe through the existing
confirmed package workflow; diagnosis does not install packages or drivers.

## 3DO failure

The laptop selected Newpixie while upstream automatic selection on Intel chose
legacy OpenGL. Configgen requested `embercade/newpixie.glslp`; the bundled
catalogue contains its Slang preset, `embercade/newpixie.slangp`. Launch aborted
before RetroArch. The managed Opera core and CUE/BIN references existed, and the
BIOS gate had passed. The owner confirmed that manually choosing Vulkan starts
the game. No source ROM/BIOS changes are needed.

The problem was renderer/format selection, not an absent Newpixie download.
All 14 curated effects are Slang presets, supported by Vulkan and OpenGL Core.
The full preset/include/texture graph is validated before staging. The catalogue
is now included in the packaged metadata so complete provision can also be
verified against the actual image in an empty user profile. No first-run shader
import or network download is required.

## Unsupported or unavailable effects

A retained manual legacy-OpenGL choice is not overwritten to satisfy a shader.
If the chosen format is unsupported or its preset is absent, the desktop
launcher starts the game without the effect. A final launch-local append config
disables stale shader state, including conflicting per-game append files; the
persistent choice and backend are not rewritten. Non-desktop upstream behavior
is unchanged.

A bounded, fixed-code notice is consumed by the same frontend when the game
returns. It distinguishes incompatible graphics settings from an unavailable
effect and offers a relevant action. English and German native translations
are included. No raw exception, filesystem path or credential is displayed,
and a notice cannot be replayed for a subsequent game. The existing in-game
menu, dynamic controller mapping and exit route are retained.

## Validation

The focused suite passes 84 tests. Coverage includes all 14 curated effects
through actual pinned Opera configgen, automatic Vulkan and OpenGL fallback,
manual choices and raw overrides, existing core exceptions, missing presets,
launch-local shader disabling, bounded native notice consumption, Dolphin/PCSX2
fallbacks and the optional host package plan. Synthetic content is used only
for dry runs and is never passed to a real emulator.

The complete isolated suite passes 776 of 781 tests (five intended native
opt-in skips), including 25 GTK checks and all 52 structural routes. Runtime
and shader smoke pass, validating 14 curated presets and 142 dependencies.
Actual-image, first-run provision and laptop rendering results follow below. Tests use separate profiles; MainRig, the laptop's
normal profiles, original collections and Wohnzimmer-PC are not reset. The
parallel README/getting-started work is preserved through an isolated worktree.
No push, public release or asset-licensing investigation is authorized.

The first private candidate passed 21 distinct packaged laptop render/start
cases: 3DO automatic Vulkan, retained manual OpenGL Core, manual legacy OpenGL
with the incompatible effect disabled, Game Boy/SNES automatic Vulkan, N64
automatic OpenGL Core exception and retained manual OpenGL Core, plus all 14
curated effects on Game Boy/Vulkan. Every effect compiled its actual Slang
passes on the laptop's Intel GPU without a shader error. Empty-profile
validation inside the real AppImage namespace reports all 14 presets and 142
dependencies without external development resources. The 3DO automatic case
retains the full 920 read-only scraper-media binds; no shared media is written.

The short 180-frame 3DO probe captures the early black console boot frame
(with Newpixie's expected texture). The manual-GL fallback was therefore
rechecked for 600 frames and captured the 3DO boot logo, with successful native
exit and `shader-incompatible` notice. Short captures establish rendering and
launch, not full gameplay or a controller-exit acceptance. The native localized
notice is compiled and its bounded consumer tested, but visible popup acceptance
after an interactive game return remains manual. Standalone emulator renderer
writers are automated configuration evidence, not new gameplay acceptance.

## Compatibility candidate validation before the explicit-None guard

The compatibility regression discovers **780 tests: 775 pass, five intended
native opt-in skips**, including all 25 GTK checks and 52 structural routes.
Runtime smoke, shader smoke and `git diff --check` pass. The production stage
and the extracted AppImage payload pass their manifest/runtime-closure checks.

- Source: `333b43bc256463100b4bbbf464e879e66e5a8539` (clean tree).
- Image: `Embercade-1.0-AutoGraphics-x86_64.AppImage` (279,116,280 bytes).
- SHA-256: `d1d478bfd8cb687fcf3349295453050a6012d0858712ff9ff8343073b6e7dfe8`.
- Native frontend SHA-256:
  `3be193f8613345d0c960b2baa34b9cc4e83c52d50aee22a8c9834519337192d0`.
- Image, adjacent checksum and manifest are verified in the private development
  `dist/private-autographics-2026-10-25/` folder and the owner's requested laptop
  `~/AppImages/` folder. Older images and menu/Steam targets are preserved.

All shader files, the native frontend and Libretro generator/config bytes
match the first GPU-tested candidate. The final payload changes only the
PPSSPP/Azahar modules, their package record and the stage manifest. The complete
14-effect compilation evidence therefore applies to the same actual files.
That image independently passes empty-profile 14/142 provision again.
Its four longer, 600-frame starts pass with captured, inspected images:

| System/core | Automatic selection | Captured output | Exit |
| --- | --- | --- | --- |
| 3DO / Opera | Vulkan | 3DO boot logo with Newpixie | 0 |
| Game Boy / Gambatte | Vulkan | Game image with Newpixie | 0 |
| SNES / Snes9x | Vulkan | Game intro with Newpixie | 0 |
| N64 / Mupen64Plus-Next | OpenGL Core exception | Game intro with Newpixie | 0 |

The normal laptop Embercade/RetroArch configurations retain their pre-test
hashes. The four explicitly owned remote temporary probe roots were removed
after bounded evidence was copied into the private development audit. Native
processes exited naturally after the requested frame count; no controller,
driver, package, normal profile, original ROM/BIOS or shared media change was
required. MainRig receives source/build artifacts only, with no setup run or
menu-owned image replacement. Wohnzimmer-PC is untouched. Parallel README and
getting-started commits are retained in the integrated source history. No push
or publication occurred.

Remaining manual acceptance: the localized frontend popup after returning from
a deliberately incompatible/missing-effect game, full interactive gameplay and
controller exit, standalone emulator gameplay with the new defaults, and other
GPU/Hyprland/Gamescope sessions. SSH-rendered startup captures do not establish
those results. The installer has no new technical graphics completion notice.

## Current handoff: automatic compatible graphics, optional effects

The owner reaffirmed that **only graphics selection is automatic; no shader is
preselected**. The latest private image includes the explicit-None guard:

- Source: `3430484d564d7ff58fa278c7e9de25391f5de754`, clean tree.
- Image: `Embercade-1.0-AutoGraphics-x86_64.AppImage` (279,116,280 bytes).
- SHA-256: `233f17457379dd679eb8a4ef595999e273dd035d52fc88ce49a83c3b0a623efd`.
- Stage manifest SHA-256:
  `9c16a03aeb008c4e4b5e0e087de2c0943a8f5e5cd65bc81e1115dbbefa6b68a2`.
- Native frontend identity is unchanged from the preceding candidate.

Full regression: **781 discovered, 776 pass, five intended skips**; all 25 GTK
checks and 52 structural routes pass. Runtime/shader smoke and diff whitespace
checks pass. Shader/frontend/Libretro-generator/default-profile files match the
preceding tested candidate; only Libretro's None-enable handling, its package
record and the stage manifest change. All 14 selected-effect pinned dry runs
remain green, and the actual image again validates the complete 14/142 graph.

The latest actual-image laptop tests use the **shipped profile defaults**,
adding only isolated window/saving/input test controls. They find exactly
`global.shaderset=none`, no per-system/game shader preset, no shader command-line
argument, no effect compilation and generated `video_shader_enable=false`.
3DO, Game Boy, SNES and N64 each run for 600 frames and exit zero, with captured
nonempty images. 3DO/GB/SNES use Vulkan; N64 keeps its shipped OpenGL Core
exception. A separate explicit Newpixie selection on GB enables shaders,
compiles all four passes and exits zero. Thus provision and optional activation
are verified independently of the off-by-default flow.

The three additional owned remote probe roots, including the pre-fix diagnostic
case, are removed after bounded evidence capture. Normal laptop configuration
hashes remain unchanged. The verified current image, checksum and manifest
replace only this task's earlier candidate in the private development `dist`
folder and requested laptop `~/AppImages/` folder. All other images, menu/Steam
targets, original collections, normal profiles, MainRig preparation and
Wohnzimmer-PC remain intact. The existing manual acceptance limits above still
apply. Changes are committed locally; no push or publication is authorized.

## Owner confirmation (25 October 2026)

After receiving the current candidate, the owner reported: “getestet und
funktioniert perfekt”. Record the delivered AutoGraphics image as working in
the owner's personal test, in addition to the automated evidence above. The
response does not enumerate individual games, hosts or every exceptional
scenario, so it does not close the entire outstanding manual acceptance list.

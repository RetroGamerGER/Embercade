# Laptop standalone decorations — 26 October 2026

The owner reported missing Xbox/Xemu and PS2/PCSX2 decorations on Garuda laptop
after successful tests on the other PCs. This investigation changes no graphics
driver, desktop configuration, emulator aspect setting or original media.

## Observed cause

Both laptop AppImage copies match the accepted private candidate:
SHA-256 `b77666fcb7a3acc1f1e495633301430386df89f646177082d20d86065a82eca8`,
source `935eacf508ab18c369091d8bfbd9023b0d9ed7fd`. Garuda's active managed copy
has the same hash. An outdated laptop image does not explain this failure.

During the owner's real fullscreen PS2 launch the shared renderer printed:

```text
Standalone decoration unavailable; game unchanged: No module named 'cairo'
```

The laptop already had `gtk-layer-shell` 0.10.1-1, `python-gobject` 3.58.1-1,
GTK3 and the native Cairo library. `python-cairo` was absent. Garuda had
`python-cairo` 1.29.2-1. The shared helper imports `cairo` before creating its
KWin observer or drawing either system's artwork, explaining the common failure.
The configured package metadata lists `cairo` and `python` as Pycairo's
dependencies; Mesa does not install this Python binding.

Read-only session probes confirmed layer-shell support and working KWin window
observation. On the laptop's 2560×1600 output at 150% scaling, both GDK's logical
monitor and the actual fullscreen PCSX2 window were 1707×1067 at (0, 0).
Existing PS2 4:3 and Xbox 4x3 selections were retained. These observations do
not establish general NVIDIA compatibility or replace visible game acceptance.

## Repair and prevention

With separate owner approval, installed only `python-cairo` 1.29.2-1 on the
laptop through a local authentication terminal. Its repository download was
101,910 bytes. The package query and actual host interpreter now pass:
Pycairo import, an image-surface drawing context, an empty input region, and
`gi.require_foreign('cairo')`. No driver package or emulator was installed.

The existing accepted image remains unchanged and uses the newly available
host module on the next game launch. A helper that already exited cannot recover
inside an earlier running game; relaunch through Embercade is necessary.

The source host assessment now independently checks this drawing support for
KDE/Hyprland Wayland and Gamescope. It offers `python-cairo` through the existing
confirmed optional host-software installation, with central German/English
labels. Missing artwork support remains optional and cannot block game launch.
The AppImage host-dependency description also records Pycairo. This installer
prevention is a source change for a future build, not a change to the already
deployed image. No new image, release, tag or upload was made for this repair.

## Validation

The 51 focused host-requirement tests pass, including missing Cairo while
layer-shell is available, KDE/Hyprland/Gamescope inclusion, unsupported-session
exclusion, localized labels, host-interpreter selection and bounded failures.
Full isolated regression passes: 792 tests, 787 successful and five expected
native opt-in skips, including the 25 GTK checks and all 52 structural routes.
Runtime smoke and `git diff --check` pass. Local diagnostic evidence is ignored under
`.work/bezel-laptop-2026-10-26/`; no credential values are recorded.

## Visible retest and remaining 16:10 limitation

The owner confirmed that artwork is visible after installation but reported
incorrect proportions, then extended that report to RetroArch. Captures of the
real PS2, Xbox and SNES launches confirm cropped side artwork on the 2560×1600
output. The later captures used 100% desktop scaling (the initial read-only
probe observed 150%); no desktop setting was changed by this investigation.
The SNES test retained the owner's selected NewPixie effect. No shader setting
was changed, and this investigation does not establish a shader fault.

Two geometry paths must be distinguished:

- The standalone renderer preserves the entire 16:9 image's aspect ratio,
  centers it inside the output, then clips outside the protected game area.
  On 16:10 the side strips are narrower than the artwork expects, cropping
  hardware graphics. PS2's preserved FMV Auto setting additionally reserves
  a possible 3:2 frame, even while the current game image is 4:3.
- The pinned RetroArch palette-image adapter explicitly crops 16:9 images to
  16:10 even when stretch is off. The non-stretch viewport calculation instead
  follows a centered, uncropped image. An isolated render of the same stock
  SNES palette artwork at 2560×1600 produced a transparent aperture of
  (264,39)–(2295,1561), whereas the equivalent RGBA non-stretch path produced
  (366,115)–(2193,1485). At 1920×1080, 2560×1440 and 3840×2160 the palette and
  RGBA outputs were pixel-identical. Cached adapted artwork can also retain
  an earlier transformation. These are offscreen geometry diagnostics, not
  an implemented or accepted rendering repair.

The owner explicitly permits documenting a 16:10 limitation if a safe common
repair is not straightforward, and requires preserving the working Garuda
and CachyOS Handheld presentation. A complete repair must address image transforms,
cache validity, viewport overrides and standalone game protection together;
simply stretching artwork or removing the clipping guard is not acceptable.
No renderer, native viewport, aspect/FMV option, shader or existing derived
artwork cache was changed. The README now records the known 16:10 limitation
and the existing Decoration=None opt-out. Correct proportions remain OPEN;
restored visibility is not full bezel acceptance. The Cairo dependency repair
does not depend on changing this geometry.

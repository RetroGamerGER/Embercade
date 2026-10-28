# Installer desktop file and folder selection

## Cause and scope

The old picker was a custom `Gtk.Dialog` and `Gtk.ListBox`, not a GTK file
chooser. `Path(entry.get_text())` turned an empty field into `Path(".")`; that
valid directory bypassed the Home fallback. Launching an AppImage from its
containing folder therefore started browsing there. The owner's `/run` screenshot
showed a subsequently visited location, not the initial default.

The custom list lacked desktop places and drive names, skipped symlinks and
limited each directory to 500 entries. It is replaced centrally for ROMs, BIOS,
core sources, provider sources, PPSSPP assets and Xemu sources. The same route
preserves the separate file actions for shadPS4 AppImage, EEPROM and PS3 PUP.
No setup, import, emulator or host-installation backend changes.

## Selection contract

- `Gtk.FileChooserNative` uses the session FileChooser portal. The wizard sets
  `GTK_USE_PORTAL=1` only when absent, before GTK initializes, without changing
  global session settings. An explicit override remains respected.
- Check the portal version with a bounded D-Bus call; folder mode needs version
  3 or newer. If missing, disabled, old or running under Gamescope, use the normal
  `Gtk.FileChooserDialog`. Construction/run exceptions can retry that fallback;
  a normal cancellation never opens a second picker.
- Existing readable directories retain their location, and existing files retain
  their parent plus preselection. Empty/unavailable paths start at Home. Never
  search upwards through a missing mount into technical system directories.
  No username, volume name or mountpoint is hardcoded.
- Standard desktop places and navigation expose home, volumes, bookmarks,
  recent places and filesystem access as supported by the desktop backend.
  The installer does not enumerate source contents, cap listings, hide symlinks,
  mount shares, create source directories or change desktop favorites.
- Selection is single, local and type-checked before changing the field. Mounted
  network shares, external drives, spaces and symlink paths remain valid. A
  remote URI without a local filesystem path cannot be handed to the existing
  emulator/import backends; the localized message asks for a mounted share.
- ACCEPT with a valid result changes the complete path. Cancel, window close,
  invalid selection and errors preserve the previous field. The chooser owns
  its lifetime; closing the parent hides it, and cleanup always releases it.
  Controller events cannot advance the wizard under a modal chooser. B cancels;
  the in-process fallback also supports focus/activation. Native navigation is
  owned by the desktop and its keyboard/mouse/Steam Input integration.
- Embercade titles and supplied action labels use the central German/English
  catalog. The portal accepts the title and accept label; KDE's navigation
  chrome and its own Cancel button follow the desktop service's language.
  The portal has no per-request language option. Changing the user's desktop
  language or restarting its portal is not part of installer localization.

## Validation and remaining acceptance

Automated checks, the actual packaged portal route and visual KDE inspection
are distinct evidence. The test profiles live in ignored development state;
no normal Embercade/emulator profile, ROM/BIOS source or host package is changed.
The complete personal clean-install, game launch and controller-exit acceptance
remains with the owner. Hyprland/Gamescope behavior must not be described as
visually proven from a KDE or synthetic environment test.

### Automated evidence — 2026-10-10

- Full suite: 682 discovered, 664 passed and 18 opt-in tests skipped. All 52
  structural routes passed with the existing backup cores used read-only.
- Separately enabled GTK suite: 13 passed (six existing wizard checks, complete
  German/English flows with simulated host installation, and five new chooser
  lifecycle checks). Therefore 677 tests executed successfully; the five
  unrelated native Xemu/layer-shell opt-ins remain unrun on the cleaned host.
- The 31 new unit tests cover initial locations, spaces, symlinks, missing
  mounts, unreadable/wrong-type paths, file selection, portal versions,
  Gamescope routing, fallback, cancellation and modal cleanup. Real GTK tests
  additionally cover directory accept/cancel/reopen in both languages, file
  preselection, controller cancellation and closing the parent window.
- GTK tests use an isolated Broadway display with the portal disabled; these
  prove GTK behavior, not a Hyprland/Gamescope or KDE visual acceptance.
- Runtime, frontend-library and shader smoke checks passed. Production staging,
  extracted package verification and AppImage creation passed. The packaged
  CLI starts successfully; Doctor correctly reports an incomplete empty profile
  with absent ROM/BIOS configuration and removed host emulators.
- An initial test-harness run placed temporary Unix sockets below an excessively
  long development path. The final full run uses the normal short `/tmp` root;
  the final counts above refer to that successful rerun.

Local automation/build evidence is under
`.work/chooser-audit-20261010-am3suj5h/reports/`; the 52-route result is
`.work/reports/system-structure.json`.

### Actual AppImage and visual KDE evidence — 2026-10-10

The built AppImage was launched on Garuda's Garuda KDE Plasma Wayland session
with disposable HOME/XDG profiles, separately for English and German. Only the
isolated installer language was seeded. No installation action was performed.
The wizard was advanced from Welcome to the paths page through its actual UI.

The actual wizard's own D-Bus sender issued `FileChooser.OpenFile` with
`directory=true`, `modal=true`, its isolated Home as `current_folder` and an
exported Wayland parent. The session portal forwarded the call to the KDE
backend. This proves the packaged portal route, not merely the source launch.

**Visual KDE test passed for opening and displaying the native folder browser.**
Screenshots were restricted to the newly opened, identified KDE portal window
and checked before and after capture. Both show the breadcrumb hierarchy and
the desktop Places sidebar, including Home, Network, recent places, `Roms`,
`Backup`, `root`, `Spiele` and the removable `Embercade` drive. English shows
“Choose folder” / “Use this folder”; German shows “Ordner auswählen” /
“Diesen Ordner wählen”. KDE navigation and Cancel remain German on this German
desktop. The starting directory is the isolated Home, not the AppImage folder.

Each exact test dialog was closed; the wizard recovered and exited normally.
Both isolated configuration files stayed byte-identical. Screenshots, guarded
window identities and the scoped D-Bus traces are retained locally under:

- `.work/appimage-chooser-kde-4msetc17/` (English)
- `.work/appimage-chooser-kde-de-tof7c0nt/` (German)

An additional German AppImage run seeded only the isolated ROM setting with
the existing CIFS-mounted ROM directory. Open, cancel, reopen and cancel all
passed: both portal requests retained that exact location, both native windows
displayed `Roms > roms` with its system folders, and configuration stayed
byte-identical. The source share was only read. Evidence:
`.work/appimage-chooser-kde-mounted-loffs6xx/`.

Native KDE selected-path acceptance is still a manual check: the shared KDE
backend did not expose its widgets through AT-SPI in this session. No synthetic
portal response was substituted. Actual interactive selection of internal,
external ext4 and mounted network paths, keyboard/controller navigation and
the complete personal clean-install remain with the owner. Hyprland and
Gamescope are not running here; their live desktop acceptance remains open.

### Delivered build

`Embercade-1.0-FileChooser-x86_64.AppImage` was built from clean source commit
`c638d2e55287f8033b1eb3b6207527c540ac8533` (279,095,800 bytes).
SHA-256:
`8fc4ce9a51fa409b38c564d16f6f630f11c99f844bffd3a73e5fe0e4caf0f8f2`.
Later evidence-only documentation commits do not change this image's source
identity. At the owner's explicit request, the previous local Final-polish
AppImage and its two matching sidecars were replaced by this image and its
verified checksum/manifest under `~/AppImage/`. The new image was verified
before deleting the exact three old artifacts. Existing profile metadata
remained unchanged; no normal setup or emulator was started. The replacement
record is in the audit reports as `image-replacement.json`.

The separate ScreenScraper authorization and paused public-release
licensing gates are unchanged by this selection fix.

## Desktop API references

- [GTK3 FileChooserNative](https://docs.gtk.org/gtk3/class.FileChooserNative.html)
- [GTK3 NativeDialog lifecycle](https://docs.gtk.org/gtk3/class.NativeDialog.html)
- [XDG FileChooser portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.FileChooser.html)

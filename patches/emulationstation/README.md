# EmulationStation patches

`0001-embercade-desktop-policy.patch` is intentionally limited to four policy
boundaries that Batocera's resource/config model cannot express:

- hide the appliance-oriented System Settings tree in desktop mode;
- replace reboot, suspend and shutdown with a normal exit branded as
  `Quit Embercade`;
- keep the fullscreen startup/reload splash independent of theme XML in
  Embercade desktop-policy mode. The installed branding image is supplied by
  Production; neither theme `splash.xml` nor the builtin splash XML can override
  its image, layout, progress styling or extras. Normal game-art loading panels
  and system/gamelist/menu theme styling retain upstream behavior;
- use the centrally supplied Embercade product label for `GuiMenu`'s global
  version footer/subtitle, the information menu and the visible frontend
  window title. `scripts/ui-build` supplies the
  compile-time `EMBERCADE_FRONTEND_PRODUCT_LABEL` from `src/embercade/version.py`,
  currently `EMBERCADE 1.0`, to both the app and core targets. The existing splash
  preserves its embedded logo, native loading text and lifecycle without an
  additional generated version line. `SDL_SetWindowTitle` runs after creation, preserving the original
  window class/app-id. Without the build definition the upstream display branch
  remains intact. Upstream API and scraper versions are unchanged; packaging
  retains its separate `0.1.dev0` identifier.

The patch is applied only to a disposable source archive of the pinned
EmulationStation commit under `.work/ui`. The sibling reference clone remains
read-only. Feature menus, emulator/core selection and all game options continue
to use Batocera's upstream data model.

`0002-embercade-screenscraper.patch` enables the existing provider through a
secret-free build flag. The copied `EmbercadeScreenScraper.h` reads only the
private runtime credentials file. It preserves upstream requests, settings,
system mapping, media and quota behavior while securing credential-bearing
HTTPS requests, suppressing unsafe error/URL logging and process dumps, and
restricting personal-account settings-file permissions. Debug credentials are
separately parsed, never transmitted in the normal path. All three inputs are
part of the disposable source identity. See `docs/SCREENSCRAPER.md`; real
MainRig and interactive second-host Steam/Gamescope acceptance pass.

`0005-embercade-launch-notices.patch` consumes only whitelisted, bounded shader
notice codes from the external state path, clears stale notices before launch,
and shows a specific native dialog after return. Patched German catalogue
entries are compiled by `ui-build`; no generic installer warning is introduced.

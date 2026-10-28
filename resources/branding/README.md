# Embercade branding resources

## Rights status

On 27 October 2026 the owner confirmed creation with Canva AI and supplied an
editor screenshot. The previous missing-creator/origin entry is resolved by that
direct declaration. The existing masters and their derivatives are mapped in
[scope.json](../../LICENSES/scope.json) under CC BY-NC-SA 4.0 for rights actually
held. This creates no exclusive copyright in AI output or new rights in
unprotected material; foreign/trademark rights retain their terms. See the
[origin and scope record](../../docs/BRANDING_ORIGIN.md). No images were changed.

The repository retains the original user-supplied masters under `source/`.
Production copies only the selected runtime and Steam-ready derivatives, not
the large source masters. Derivatives preserve their source aspect ratio and
are only scaled down. The 8000×4500 landscape master is the highest-resolution 16:9 artwork;
the installed splash is a 3840×2160 derivative. EmulationStation fits it to the
display while preserving aspect ratio and closes its built-in startup splash
when the frontend finishes loading. If that file is missing, Embercade starts
EmulationStation with its splash disabled and continues normally.

These are product resources, not interchangeable EmulationStation theme assets.
Production supplies the installed splash independently of `ThemeSet`. The
frontend desktop policy ignores theme and builtin splash XML for fullscreen
startup/reload screens, so background paths, styling and extras cannot replace
Embercade branding. Normal menu/system/gamelist styling and game-art panels
remain themeable. Themes are never rewritten to enforce this boundary; their
user-data directory is separate from the read-only product resources.

The global frontend menu footer/subtitle is also product-owned: `GuiMenu`
displays `EMBERCADE 1.0`, supplied at build time from the central frontend
product constants in `src/embercade/version.py`. Themes may style the footer
but cannot replace its text. The same central label supplies the information
version and window title. Wizard and generated desktop metadata also use it.
The existing splash preserves the embedded Embercade logo and native loading
text without an additional generated version line.
No Carbon, downloaded theme or artwork file is changed for the 1.0 label.
The packaging identifier remains `0.1.dev0`; Batocera/ES versions used by
upstream APIs, scrapers and diagnostics are separate and unchanged.

Historical acceptance of the previous `EMBERCADE 0.5` footer text covers Carbon
and AI-Hypertocera on Garuda/Hyprland and in the CachyOS Handheld's real interactive
Steam/Gamescope session. Font and color followed the theme while product text
stayed fixed. Those runs also accepted the product splash, controller menu and
normal frontend quit back to the host session without a remaining process. Current
AppImage artifact acceptance is tracked separately in
[APPIMAGE.md](../../docs/APPIMAGE.md).

## Asset map

| Resource | Source | Intended use |
| --- | --- | --- |
| `source/embercade-icon-master.jpg` | supplied `4.jpg`, 4688×4688 | Application and Steam shortcut icon master |
| `icon/embercade-{128,256,512}.png` | Downscaled from the icon master | Hicolor desktop icon; the 512px version is installed at `$XDG_DATA_HOME/icons/hicolor/512x512/apps/embercade.png` |
| `source/embercade-portrait-master.jpg` | supplied `5.jpg`, 10800×21600 | Portrait / Steam library grid master |
| `steam/embercade-grid-900x1800.jpg` | Downscaled from the portrait master | Steam library grid / portrait artwork |
| `source/embercade-landscape-master.jpg` | supplied `7.jpg`, 8000×4500 | Highest-resolution landscape master, with embedded Embercade wordmark |
| `splash/embercade-splash-3840x2160.jpg` | Downscaled from the landscape master | 4K startup splash |
| `steam/embercade-hero.jpg` | Relative link to the splash image | Steam hero and horizontal capsule candidate; one image is shared to avoid duplication |

There is no separate transparent wordmark in the supplied artwork. The
Embercade lettering is part of the portrait and landscape artwork. Supplied
`1.jpg`, `2.jpg`, `3.jpg` and `6.jpg` were inventoried but are not staged:
they are square or 4:3 variants, and the square/4:3 loading images embed a
fixed progress bar and `Lädt ...` label. The landscape master fits the product's
16:9 splash requirement and uses EmulationStation's native progress display.

Interactive setup optionally registers the installed Embercade launcher in
native Steam. The explicit `embercade steam` command provides the same path.
It requires Steam to be stopped and installs the existing icon, portrait grid,
landscape cover, hero and logo-slot artwork under the selected Steam profile.
The logo slot uses the existing landscape image with its embedded wordmark;
it is not a new transparent logo. No source masters are installed there.
Registration preserves existing shortcut IDs and all foreign shortcut bytes,
backs up modified files and makes no changes when declined. See
`docs/STEAM_INTEGRATION.md` in the source checkout for the complete contract.

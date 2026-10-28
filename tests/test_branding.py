from pathlib import Path
import struct
import unittest

from embercade.version import FRONTEND_PRODUCT_LABEL, FRONTEND_PRODUCT_VERSION, __version__
from embercade.staging import StagingError, render_desktop_entry


PROJECT = Path(__file__).resolve().parents[1]
BRANDING = PROJECT / "resources/branding"


def _jpeg_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\xff\xd8"):
        raise AssertionError(f"not a JPEG file: {path}")
    position = 2
    start_of_frame = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while position < len(data):
        if data[position] != 0xFF:
            position += 1
            continue
        while position < len(data) and data[position] == 0xFF:
            position += 1
        marker = data[position]
        position += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        length = struct.unpack_from(">H", data, position)[0]
        if marker in start_of_frame:
            height, width = struct.unpack_from(">HH", data, position + 3)
            return width, height
        position += length
    raise AssertionError(f"JPEG has no start-of-frame marker: {path}")


class BrandingResourceTests(unittest.TestCase):
    def test_frontend_product_label_is_separate_from_package_version(self) -> None:
        self.assertEqual(FRONTEND_PRODUCT_VERSION, "1.0")
        self.assertEqual(FRONTEND_PRODUCT_LABEL, "EMBERCADE 1.0")
        self.assertNotEqual(FRONTEND_PRODUCT_VERSION, __version__)

    def test_global_footer_uses_product_label_instead_of_upstream_branding(self) -> None:
        patch = (PROJECT / "patches/emulationstation/0001-embercade-desktop-policy.patch").read_text()
        product_branch = patch.split("+#ifdef EMBERCADE_FRONTEND_PRODUCT_LABEL", 1)[1].split("+#else", 1)[0]
        self.assertIn("std::string label = EMBERCADE_FRONTEND_PRODUCT_LABEL;", product_branch)
        for upstream_value in ("BATOCERA", "getVersion", "buildDate", "ThemeSet"):
            self.assertNotIn(upstream_value, product_branch)
        self.assertIn("target_compile_definitions(emulationstation PRIVATE", patch)

    def test_frontend_build_consumes_central_label_and_tracks_version_changes(self) -> None:
        build = (PROJECT / "scripts/ui-build").read_text()
        stage = (PROJECT / "scripts/stage-build").read_text()
        self.assertIn("from embercade.version import FRONTEND_PRODUCT_LABEL", build)
        self.assertIn('-DEMBERCADE_FRONTEND_PRODUCT_LABEL="$frontend_product_label"', build)
        self.assertIn('"$project_root/scripts/ui-build" "$@"', stage)
        self.assertNotIn(FRONTEND_PRODUCT_LABEL, build)

    def test_desktop_name_and_wizard_title_use_central_product_identity(self) -> None:
        template = (PROJECT / "packaging/linux/embercade.desktop").read_text()
        desktop = render_desktop_entry(template)
        self.assertIn(f"Name={FRONTEND_PRODUCT_LABEL}\n", desktop)
        self.assertIn("Icon=embercade\n", desktop)
        self.assertIn("Exec=embercade\n", desktop)
        self.assertNotIn("@EMBERCADE_PRODUCT_LABEL@", desktop)
        for invalid in (template.replace("@EMBERCADE_PRODUCT_LABEL@", "Embercade"),
                        template + "Comment=@EMBERCADE_PRODUCT_LABEL@\n"):
            with self.assertRaises(StagingError):
                render_desktop_entry(invalid)
        wizard = (PROJECT / "src/embercade/first_run_ui.py").read_text()
        self.assertIn('Gtk.Window(title=f"{FRONTEND_PRODUCT_LABEL} – ', wizard)

    def test_frontend_policy_prevents_fullscreen_splash_theme_overrides(self) -> None:
        patch = (PROJECT / "patches/emulationstation/0001-embercade-desktop-policy.patch").read_text()
        splash_patch = patch.split("--- a/es-core/src/Splash.cpp", 1)[1]
        self.assertIn('std::getenv("EMBERCADE_DESKTOP_POLICY")', splash_patch)
        self.assertIn('fullScreenBackGround && desktopPolicy != nullptr', splash_patch)
        self.assertIn('std::string(desktopPolicy) == "1"', splash_patch)
        self.assertIn('productSplash ? false : OLD_SPLASH_LAYOUT', splash_patch)
        self.assertIn('? std::map<std::string, ThemeSet>() : ThemeData::getThemeSets()', splash_patch)
        self.assertIn('if (!productSplash && Utils::FileSystem::exists(themeFilePath))', splash_patch)

    def test_information_branding_preserves_native_splash_without_extra_version_text(self) -> None:
        patch = (PROJECT / "patches/emulationstation/0001-embercade-desktop-policy.patch").read_text()
        splash_patch = patch.split("--- a/es-core/src/Splash.cpp", 1)[1].split(
            "--- a/es-app/src/guis/GuiSystemInformation.cpp", 1
        )[0]
        self.assertNotIn('mProductLabel', patch)
        self.assertNotIn('--- a/es-core/src/Splash.h', patch)
        self.assertNotIn('EMBERCADE_FRONTEND_PRODUCT_LABEL', splash_patch)
        self.assertNotIn('mText.setText', splash_patch)  # Native loading text stays unchanged.
        self.assertIn('target_compile_definitions(es-core PRIVATE', patch)
        info_patch = patch.split("--- a/es-app/src/guis/GuiSystemInformation.cpp", 1)[1].split(
            "--- a/es-core/CMakeLists.txt", 1
        )[0]
        self.assertIn('window, EMBERCADE_FRONTEND_PRODUCT_LABEL, font, color', info_patch)
        self.assertIn('+#else', info_patch)
        self.assertIn('ApiSystem::getInstance()->getVersion()', info_patch)
        self.assertNotIn('--- a/es-app/src/ApiSystem.cpp', patch)

    def test_frontend_window_title_preserves_creation_time_window_identity(self) -> None:
        patch = (PROJECT / "patches/emulationstation/0001-embercade-desktop-policy.patch").read_text()
        renderer_patch = patch.split("--- a/es-core/src/renderers/Renderer.cpp", 1)[1].split(
            "--- a/es-app/CMakeLists.txt", 1
        )[0]
        self.assertIn('SDL_SetWindowTitle(sdlWindow, EMBERCADE_FRONTEND_PRODUCT_LABEL)', renderer_patch)
        self.assertNotIn('SDL_CreateWindow', renderer_patch)
        self.assertNotIn('SDL_SetHint', renderer_patch)

    def test_icon_derivatives_have_standard_hicolor_sizes(self) -> None:
        for size in (128, 256, 512):
            path = BRANDING / f"icon/embercade-{size}.png"
            header = path.read_bytes()[:24]
            self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", header[16:24]), (size, size))

    def test_splash_and_hero_preserve_the_original_16_by_9_ratio(self) -> None:
        master = _jpeg_dimensions(BRANDING / "source/embercade-landscape-master.jpg")
        splash = _jpeg_dimensions(BRANDING / "splash/embercade-splash-3840x2160.jpg")
        self.assertEqual(master, (8000, 4500))
        self.assertEqual(splash, (3840, 2160))
        self.assertEqual(master[0] * splash[1], master[1] * splash[0])
        self.assertLess(splash[0], master[0])
        hero = BRANDING / "steam/embercade-hero.jpg"
        self.assertTrue(hero.is_symlink())
        self.assertEqual(hero.resolve(), (BRANDING / "splash/embercade-splash-3840x2160.jpg").resolve())

    def test_portrait_derivative_preserves_master_ratio(self) -> None:
        master = _jpeg_dimensions(BRANDING / "source/embercade-portrait-master.jpg")
        grid = _jpeg_dimensions(BRANDING / "steam/embercade-grid-900x1800.jpg")
        self.assertEqual(master, (10800, 21600))
        self.assertEqual(grid, (900, 1800))
        self.assertEqual(master[0] * grid[1], master[1] * grid[0])


if __name__ == "__main__":
    unittest.main()

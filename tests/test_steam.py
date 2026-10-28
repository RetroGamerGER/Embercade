from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import json
import shutil
import unittest

from embercade import steam
from embercade.cli import main
from embercade.version import FRONTEND_PRODUCT_LABEL


class SteamIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name) / "User with spaces"
        self.env = {"HOME": str(self.home), "PATH": ""}
        self.paths = steam.UserInstallPaths.from_environment(self.env)
        binary = self.paths.prefix / "bin/embercade"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"#!/bin/sh\n")
        binary.chmod(0o755)
        self.paths.launcher.parent.mkdir(parents=True)
        self.paths.launcher.symlink_to(binary)
        self.branding = self.paths.prefix / "share/embercade/resources/branding"
        for relative, content in (
            ("icon/embercade-512.png", b"icon"),
            ("steam/embercade-grid-900x1800.jpg", b"portrait"),
            ("splash/embercade-splash-3840x2160.jpg", b"landscape"),
        ):
            path = self.branding / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (self.branding / "steam/embercade-hero.jpg").symlink_to("../splash/embercade-splash-3840x2160.jpg")
        self.profile = self.home / ".local/share/Steam/userdata/42/config"
        self.profile.mkdir(parents=True)
        self.file = self.profile / "shortcuts.vdf"

    def register(self, **kwargs):
        return steam.register(self.profile, environment=self.env, running=lambda: False, **kwargs)

    def entries(self):
        return steam.parse_vdf(self.file.read_bytes())[0].value

    def existing(self, *, appid=4059814080, exe=None, name="Embercade", key="0"):
        return steam._node(key, tuple(steam._node(k, v) for k, v in {
            "appid": appid, "AppName": name, "Exe": exe or f'"{self.paths.launcher}"',
            "StartDir": '"/old path"', "icon": "old-icon",
            "LaunchOptions": "start --windowed", "tags": (steam._node("0", "Favorite"),),
            "LastPlayTime": 100,
        }.items()))

    def write_entries(self, *entries):
        self.file.write_bytes(steam._node("shortcuts", tuple(entries)).raw + b"\x08")

    def tree(self):
        return {str(p.relative_to(self.home)): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}

    def test_no_steam_profile_is_optional_and_makes_no_changes(self):
        self.profile.rmdir()
        before = self.tree()
        output = StringIO()
        result = steam.offer_integration(environment=self.env, output=output, input_function=lambda _: self.fail("unexpected prompt"))
        self.assertIsNone(result)
        self.assertIn("no initialized Steam profile", output.getvalue())
        self.assertEqual(before, self.tree())

    def test_declining_makes_no_changes(self):
        before = self.tree()
        result = steam.offer_integration(environment=self.env, output=StringIO(), input_function=lambda _: "n")
        self.assertIsNone(result)
        self.assertEqual(before, self.tree())

    def test_first_shortcut_uses_installed_launcher_and_expected_artwork(self):
        result = self.register()
        fields = steam._fields(self.entries()[0].value)
        self.assertTrue(result.created)
        self.assertEqual(steam._text(fields, "exe"), f'"{self.paths.launcher}"')
        self.assertEqual(steam._text(fields, "launchoptions"), "")
        self.assertEqual(result.appid, steam.shortcut_id(f'"{self.paths.launcher}"'))
        grid = self.profile / "grid"
        self.assertEqual((grid / f"{result.appid}p.jpg").read_bytes(), b"portrait")
        for suffix in ("", "_hero", "_logo"):
            self.assertEqual((grid / f"{result.appid}{suffix}.jpg").read_bytes(), b"landscape")
        self.assertEqual((grid / f"{result.appid}_icon.png").read_bytes(), b"icon")
        self.assertEqual(steam._text(fields, "icon"), str(grid / f"{result.appid}_icon.png"))
        self.assertTrue((result.backup / "restore.json").is_file())

    def test_repeat_is_byte_identical_no_duplicate_or_new_backup(self):
        first = self.register()
        before = self.tree()
        second = self.register()
        self.assertFalse(second.created)
        self.assertFalse(second.changed)
        self.assertIsNone(second.backup)
        self.assertEqual(first.appid, second.appid)
        self.assertEqual(len(self.entries()), 1)
        self.assertEqual(self.tree(), before)

    def appimage_environment(self):
        image = self.home / "Applications/Embercade.AppImage"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"\x7fELF\x02\x01\x01\x00AI\x02" + b"\x00" * 5)
        image.chmod(0o755)
        appdir = self.home / "mount"
        prefix = appdir / "usr"
        shutil.copytree(self.paths.prefix, prefix)
        return {**self.env, "EMBERCADE_APPIMAGE": "1", "APPIMAGE": str(image),
                "APPDIR": str(appdir), "EMBERCADE_PREFIX": str(prefix)}

    def test_appimage_retargets_existing_identity_only_when_explicit(self):
        self.write_entries(self.existing())
        env = self.appimage_environment()
        with self.assertRaisesRegex(steam.SteamError, "another executable"):
            steam.register(self.profile, environment=env, running=lambda: False)
        result = steam.register(self.profile, environment=env, running=lambda: False, replace_existing=True)
        fields = steam._fields(self.entries()[0].value)
        self.assertEqual(result.appid, 4059814080)
        self.assertEqual(len(self.entries()), 1)
        self.assertEqual(steam._text(fields, "exe"), f'"{env["APPIMAGE"]}"')
        self.assertEqual(steam._text(fields, "appname"), FRONTEND_PRODUCT_LABEL)
        self.assertEqual(steam._text(fields, "launchoptions"), "start --windowed")
        self.assertFalse(steam.register(self.profile, environment=env, running=lambda: False).changed)
        restored = self.register(replace_existing=True)
        self.assertEqual(restored.appid, result.appid)
        self.assertEqual(steam._text(steam._fields(self.entries()[0].value), "exe"), f'"{self.paths.launcher}"')

    def test_extracted_appdir_cannot_register_transient_mount(self):
        env = self.appimage_environment()
        del env["APPIMAGE"]
        before = self.tree()
        with self.assertRaisesRegex(steam.SteamError, "mounted"):
            steam.register(self.profile, environment=env, running=lambda: False)
        self.assertEqual(self.tree(), before)

    def test_appimage_wrong_root_fails_without_writes(self):
        env = self.appimage_environment()
        env["EMBERCADE_PREFIX"] = str(self.paths.prefix)
        before = self.tree()
        with self.assertRaisesRegex(steam.SteamError, "root"):
            steam.register(self.profile, environment=env, running=lambda: False)
        self.assertEqual(self.tree(), before)

    def test_appimage_symlink_is_not_registered(self):
        env = self.appimage_environment()
        alias = self.home / "alias.AppImage"
        alias.symlink_to(env["APPIMAGE"])
        env["APPIMAGE"] = str(alias)
        with self.assertRaisesRegex(steam.SteamError, "user-owned"):
            steam.register(self.profile, environment=env, running=lambda: False)

    def test_legacy_product_name_upgrade_preserves_appid_and_is_idempotent(self):
        self.write_entries(self.existing(name="Embercade 0.5"))
        result = self.register()
        self.assertEqual(result.appid, 4059814080)
        self.assertEqual(steam._text(steam._fields(self.entries()[0].value), "appname"), FRONTEND_PRODUCT_LABEL)
        self.assertFalse(self.register().changed)

    def test_existing_steam_identity_options_tags_and_permissions_survive(self):
        self.write_entries(self.existing())
        self.file.chmod(0o640)
        result = self.register()
        fields = steam._fields(self.entries()[0].value)
        self.assertFalse(result.created)
        self.assertEqual(result.appid, 4059814080)
        self.assertEqual(steam._text(fields, "LaunchOptions"), "start --windowed")
        self.assertEqual(fields["tags"].raw, steam._fields(self.existing().value)["tags"].raw)
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o640)
        self.assertEqual((result.backup / "0.original").read_bytes(), steam._node("shortcuts", (self.existing(),)).raw + b"\x08")

    def test_foreign_shortcuts_unknown_fields_and_artwork_are_byte_preserved(self):
        foreign = self.existing(appid=1234, exe='"/other/🎮"', name="Other", key="7")
        foreign = steam._node("7", (*foreign.value, steam.Node(3, "float", b"\x00\x00\x80\x3f", b"\x03float\0\x00\x00\x80\x3f")))
        self.write_entries(foreign)
        grid = self.profile / "grid"
        grid.mkdir()
        unrelated = grid / "1234_hero.png"
        unrelated.write_bytes(b"untouched")
        self.register()
        self.assertEqual(self.entries()[0].raw, foreign.raw)
        self.assertEqual(unrelated.read_bytes(), b"untouched")
        self.assertEqual(self.entries()[1].key, "8")

    def test_case_variant_keys_preserved_without_duplicate_fields(self):
        existing = self.existing()
        lower = steam._node("0", tuple(steam.Node(n.kind, n.key.lower(), n.value, bytes((n.kind,)) + steam._cstring(n.key.lower()) + n.raw[len(steam._cstring(n.key)) + 1:]) for n in existing.value))
        self.write_entries(lower)
        self.register()
        self.assertEqual(len(steam._fields(self.entries()[0].value)), len(existing.value))

    def test_multiple_accounts_require_selection_and_only_selected_account_changes(self):
        second = self.home / ".local/share/Steam/userdata/99/config"
        second.mkdir(parents=True)
        answers = iter(("y", "2"))
        with patch("embercade.steam.steam_running", return_value=False):
            result = steam.offer_integration(environment=self.env, output=StringIO(), input_function=lambda _: next(answers))
        self.assertEqual(result.profile, second)
        self.assertFalse(self.file.exists())
        self.assertTrue((second / "shortcuts.vdf").is_file())

    def test_noninteractive_multiple_accounts_do_not_guess(self):
        (self.home / ".local/share/Steam/userdata/99/config").mkdir(parents=True)
        before = self.tree()
        output = StringIO()
        result = steam.offer_integration(environment=self.env, output=output, accepted=True, interactive=False)
        self.assertIsNone(result)
        self.assertIn("--profile", output.getvalue())
        self.assertEqual(before, self.tree())

    def test_native_aliases_deduplicated_and_xdg_path_discovered(self):
        aliases = self.home / ".steam"
        aliases.mkdir()
        (aliases / "steam").symlink_to(self.home / ".local/share/Steam")
        (aliases / "root").symlink_to(self.home / ".local/share/Steam")
        self.assertEqual(steam.discover_profiles(self.env), (self.profile,))
        data = self.home / "custom-data"
        custom = data / "Steam/userdata/100/config"
        custom.mkdir(parents=True)
        self.assertEqual(set(steam.discover_profiles({**self.env, "XDG_DATA_HOME": str(data)})), {custom, self.profile})

    def test_flatpak_profile_detected_but_unvalidated_host_bridge_is_not_guessed(self):
        self.profile.rmdir()
        flatpak = self.home / ".var/app/com.valvesoftware.Steam/data/Steam/userdata/42/config"
        flatpak.mkdir(parents=True)
        self.assertEqual(steam.discover_profiles(self.env), (flatpak,))
        with self.assertRaisesRegex(steam.SteamError, "Flatpak"):
            steam.register(flatpak, environment=self.env, running=lambda: False)
        self.assertFalse((flatpak / "shortcuts.vdf").exists())

    def test_running_steam_defers_without_writes(self):
        before = self.tree()
        with self.assertRaisesRegex(steam.SteamError, "Close Steam"):
            steam.register(self.profile, environment=self.env, running=lambda: True)
        self.assertEqual(before, self.tree())

    def test_process_probe_recognizes_steam_and_webhelper(self):
        proc = self.home / "fake-proc"
        for comm in ("steam", "steamwebhelper", "other"):
            path = proc / "100"
            path.mkdir(parents=True, exist_ok=True)
            (path / "comm").write_text(comm + "\n")
            self.assertEqual(steam.steam_running(proc), comm != "other")

    def test_dry_run_has_no_side_effects(self):
        before = self.tree()
        result = self.register(dry_run=True)
        self.assertTrue(result.changed)
        self.assertEqual(before, self.tree())

    def test_missing_branding_is_optional_and_does_not_mutate_steam(self):
        (self.branding / "steam/embercade-grid-900x1800.jpg").unlink()
        before = self.tree()
        with self.assertRaisesRegex(steam.SteamError, "branding resource"):
            self.register()
        self.assertEqual(before, self.tree())

    def test_malformed_vdf_is_never_overwritten(self):
        for data in (b"", b"\x00shortcuts\0", b"\x00shortcuts\0\x08\x08trailing", b"\x00shortcuts\0\x09unknown\0\x08\x08"):
            self.file.write_bytes(data)
            before = self.tree()
            with self.assertRaises(steam.SteamError):
                self.register()
            self.assertEqual(before, self.tree())

    def test_duplicate_matching_shortcuts_fail_closed(self):
        self.write_entries(self.existing(), self.existing(appid=3000000000, key="1"))
        before = self.tree()
        with self.assertRaisesRegex(steam.SteamError, "Multiple Embercade"):
            self.register()
        self.assertEqual(before, self.tree())

    def test_duplicate_appids_are_rejected_before_artwork_changes(self):
        self.write_entries(self.existing(), self.existing(exe="elsewhere", name="Other", key="1"))
        with self.assertRaisesRegex(steam.SteamError, "Duplicate Steam appid"):
            self.register()

    def test_same_name_different_executable_is_not_duplicated(self):
        self.write_entries(self.existing(exe='"/some/development-launcher"'))
        before = self.tree()
        with self.assertRaisesRegex(steam.SteamError, "another executable"):
            self.register()
        self.assertEqual(before, self.tree())

    def test_new_id_collision_with_foreign_shortcut_is_rejected(self):
        appid = steam.shortcut_id(f'"{self.paths.launcher}"')
        self.write_entries(self.existing(appid=appid, exe="another", name="Other"))
        with self.assertRaisesRegex(steam.SteamError, "collides"):
            self.register()

    def test_new_id_collision_with_orphan_artwork_is_rejected(self):
        appid = steam.shortcut_id(f'"{self.paths.launcher}"')
        (self.profile / "grid").mkdir()
        (self.profile / "grid" / f"{appid}_hero.png").write_bytes(b"not owned")
        with self.assertRaisesRegex(steam.SteamError, "collides"):
            self.register()
        self.assertFalse(self.file.exists())

    def test_only_matching_app_stale_format_is_backed_up_and_removed(self):
        self.write_entries(self.existing())
        grid = self.profile / "grid"
        grid.mkdir()
        old = grid / "4059814080_hero.png"
        old.write_bytes(b"old hero")
        old.chmod(0o640)
        result = self.register()
        self.assertFalse(old.exists())
        records = json.loads((result.backup / "restore.json").read_text())
        record = next(r for r in records if r["path"] == str(old))
        self.assertEqual((result.backup / record["original"]).read_bytes(), b"old hero")

    def test_symlinked_grid_cannot_redirect_writes(self):
        external = self.home / "foreign"
        external.mkdir()
        (self.profile / "grid").symlink_to(external)
        with self.assertRaisesRegex(steam.SteamError, "symlinked"):
            self.register()
        self.assertEqual(list(external.iterdir()), [])

    def test_symlinked_shortcuts_cannot_redirect_writes(self):
        external = self.home / "foreign.vdf"
        external.write_bytes(b"foreign")
        self.file.symlink_to(external)
        with self.assertRaisesRegex(steam.SteamError, "symlinked"):
            self.register()
        self.assertEqual(external.read_bytes(), b"foreign")

    def test_missing_installed_launcher_is_rejected(self):
        self.paths.launcher.unlink()
        with self.assertRaisesRegex(steam.SteamError, "Install Embercade first"):
            self.register()
        self.assertFalse(self.file.exists())

    def test_failure_mid_activation_rolls_back_original_bytes_and_modes(self):
        self.write_entries(self.existing())
        before = self.file.read_bytes()
        self.file.chmod(0o640)
        actual_write = steam._atomic_write
        def fail_once(path, data, mode):
            if path.name == "4059814080p.jpg":
                raise OSError("injected disk failure")
            return actual_write(path, data, mode)
        with patch("embercade.steam._atomic_write", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected"):
                self.register()
        self.assertEqual(self.file.read_bytes(), before)
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o640)
        self.assertFalse((self.profile / "grid").exists())
        self.assertTrue(list((self.paths.state_root / "steam-backups").glob("*/restore.json")))

    def test_steam_starting_before_activation_leaves_original_intact(self):
        self.write_entries(self.existing())
        before = self.file.read_bytes()
        calls = iter((False, True))
        with self.assertRaisesRegex(steam.SteamError, "started"):
            steam.register(self.profile, environment=self.env, running=lambda: next(calls))
        self.assertEqual(before, self.file.read_bytes())

    def test_explicit_cli_dry_run_does_not_need_collection_config(self):
        before = self.tree()
        with patch.dict(os.environ, self.env, clear=True), patch("embercade.steam.steam_running", return_value=False), redirect_stdout(StringIO()):
            self.assertEqual(main(["steam", "--dry-run"]), 0)
        self.assertEqual(before, self.tree())

    def test_optional_failure_does_not_fail_setup(self):
        output = StringIO()
        with patch("embercade.steam.steam_running", return_value=True):
            result = steam.offer_integration(environment=self.env, output=output, input_function=lambda _: "y")
        self.assertIsNone(result)
        self.assertIn("Close Steam", output.getvalue())
        self.assertFalse(self.file.exists())

    def test_resource_update_reuses_identity_and_preserves_artwork_mode(self):
        first = self.register()
        icon = self.profile / "grid" / f"{first.appid}_icon.png"
        icon.chmod(0o644)
        (self.branding / "icon/embercade-512.png").write_bytes(b"updated icon")
        second = self.register()
        self.assertTrue(second.changed)
        self.assertEqual(first.appid, second.appid)
        self.assertEqual(len(self.entries()), 1)
        self.assertEqual(icon.read_bytes(), b"updated icon")
        self.assertEqual(icon.stat().st_mode & 0o777, 0o644)

    def test_cli_noninteractive_write_requires_explicit_opt_in(self):
        before = self.tree()
        with patch.dict(os.environ, self.env, clear=True), patch("embercade.cli.sys.stdin", type("Input", (), {"isatty": lambda _: False})()), redirect_stdout(StringIO()):
            self.assertEqual(main(["steam"]), 2)
        self.assertEqual(before, self.tree())

    def test_explicit_cli_reports_failure_but_optional_setup_can_continue(self):
        output = StringIO()
        with patch.dict(os.environ, self.env, clear=True), patch("embercade.steam.steam_running", return_value=True), redirect_stdout(output):
            self.assertEqual(main(["steam", "--yes"]), 2)
        self.assertIn("Close Steam", output.getvalue())
        self.assertFalse(self.file.exists())


if __name__ == "__main__":
    unittest.main()

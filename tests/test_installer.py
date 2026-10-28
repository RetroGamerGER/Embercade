from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os
import tomllib
import unittest

from embercade.installer import (
    InstallationError,
    STAGE_MANIFEST_RELATIVE,
    UserInstallPaths,
    install_user,
    launcher_path_guidance,
    running_installation_pids,
    uninstall_user,
    verify_payload,
)
from embercade.imports import import_providers
from embercade.setup_flow import configure, detect_xenia_edge
from tests.test_imports import elf


def _write_payload(root: Path, marker: str = "one") -> Path:
    payload = root / "Payload with spaces"
    files = {
        "bin/embercade": f"#!/bin/sh\n# {marker}\n",
        "bin/embercade-provider-runner": "#!/bin/sh\n",
        "share/embercade/frontend/emulationstation": "frontend\n",
        "share/embercade/runtime/venv/bin/python": "python\n",
        "share/embercade/resources/branding/icon/embercade-512.png": f"icon-{marker}\n",
        "share/embercade/runtime/venv/lib/python3.14/site-packages/example/"
        "__pycache__/module.cpython-314.pyc": f"bytecode {marker}\n",
        "share/applications/embercade.desktop": (
            "[Desktop Entry]\nName=EMBERCADE 1.0\nExec=embercade\nType=Application\nIcon=embercade\n"
        ),
    }
    entries = []
    for relative, content in files.items():
        path = payload / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if relative.startswith("bin/") or relative.endswith("emulationstation") or relative.endswith("/python"):
            path.chmod(0o755)
        data = path.read_bytes()
        entries.append(
            {"path": relative, "type": "file", "size": len(data), "sha256": sha256(data).hexdigest()}
        )
    manifest = payload / STAGE_MANIFEST_RELATIVE
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps({
            "format": 1, "embercade_version": "0.1.dev0",
            "product_label": "EMBERCADE 1.0", "pins": {"test": marker}, "entries": entries,
        }),
        encoding="utf-8",
    )
    return payload


def _environment(root: Path) -> dict[str, str]:
    return {
        "HOME": str(root / "Fake Home"),
        "XDG_CONFIG_HOME": str(root / "XDG Config"),
        "XDG_DATA_HOME": str(root / "XDG Data"),
        "XDG_CACHE_HOME": str(root / "XDG Cache"),
        "XDG_STATE_HOME": str(root / "XDG State"),
        "PATH": "",
    }


class InstallerTests(unittest.TestCase):
    def test_fresh_install_manifest_launcher_and_desktop(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _write_payload(root)
            environment = _environment(root)
            result = install_user(payload, environment=environment)
            paths = result.paths
            self.assertEqual(result.mode, "NEW INSTALL")
            self.assertTrue(paths.launcher.is_symlink())
            self.assertEqual(Path(os.readlink(paths.launcher)), paths.prefix / "bin/embercade")
            desktop = paths.desktop_entry.read_text(encoding="utf-8")
            self.assertIn(f'Exec="{paths.launcher}"', desktop)
            self.assertIn("Name=EMBERCADE 1.0\n", desktop)
            self.assertIn("Icon=embercade", desktop)
            self.assertEqual(paths.icon.read_bytes(), b"icon-one\n")
            manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
            self.assertNotIn("rom", json.dumps(manifest).casefold())
            self.assertEqual(manifest["product_label"], "EMBERCADE 1.0")
            self.assertTrue((paths.prefix / "bin/embercade").is_file())

    def test_dry_run_changes_nothing(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result = install_user(_write_payload(root), environment=_environment(root), dry_run=True)
            self.assertEqual(result.mode, "NEW INSTALL")
            self.assertFalse(result.paths.home.exists())

    def test_identical_payload_is_a_strict_noop(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            payload = _write_payload(root)
            first = install_user(payload, environment=environment)
            user_files = (
                first.paths.config_root / "embercade.toml",
                first.paths.data_root / "saves/save.bin",
                first.paths.data_root / "saves/xbox/xemu_eeprom.bin",
                first.paths.data_root / "states/slot.state",
                first.paths.data_root / "themes/custom/theme.xml",
                first.paths.data_root / "cores/test_libretro.so",
                first.paths.data_root / "providers/xenia/Xenia.AppImage",
                first.paths.data_root / "system/PPSSPP/font.dat",
                first.paths.data_root / "steam/shortcut.vdf",
                first.paths.config_root / "secrets/screenscraper.conf",
                first.paths.config_root / "secrets/screenscraper-user.conf",
            )
            for path in user_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(path.name.encode())
                if path.parent.name == "secrets":
                    path.parent.chmod(0o700)
                    path.chmod(0o600)
            watched = (*user_files, first.paths.manifest, first.paths.desktop_entry,
                       first.paths.icon, first.paths.prefix / "bin/embercade")
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in watched}
            dry = install_user(payload, environment=environment, dry_run=True)
            self.assertEqual(dry.mode, "ALREADY UP TO DATE")
            self.assertEqual(dry.current_manifest_sha256, dry.payload_manifest_sha256)
            with patch("embercade.installer._replace", side_effect=AssertionError("no replacement")):
                second = install_user(payload, environment=environment)
            self.assertEqual(second.mode, "ALREADY UP TO DATE")
            self.assertEqual({path: (path.read_bytes(), path.stat().st_mtime_ns) for path in watched}, before)
            self.assertFalse(tuple(first.paths.prefix.parent.glob(".*embercade-backup-*")))

    def test_update_dry_run_reports_two_revisions_without_writing(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            payload = _write_payload(root, "one")
            first = install_user(payload, environment=environment)
            before = (first.paths.prefix / "bin/embercade").read_bytes()
            manifest_before = first.paths.manifest.read_bytes()
            _write_payload(root, "two")
            result = install_user(payload, environment=environment, dry_run=True)
            self.assertEqual(result.mode, "UPDATE/REINSTALL")
            self.assertNotEqual(result.current_manifest_sha256, result.payload_manifest_sha256)
            self.assertEqual(result.incoming_product_label, "EMBERCADE 1.0")
            self.assertEqual((first.paths.prefix / "bin/embercade").read_bytes(), before)
            self.assertEqual(first.paths.manifest.read_bytes(), manifest_before)

    def test_reinstall_replaces_payload_and_keeps_user_data(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            first = install_user(_write_payload(root, "one"), environment=environment)
            user_data = first.paths.data_root / "saves" / "save.bin"
            user_data.parent.mkdir(parents=True)
            user_data.write_text("save", encoding="utf-8")
            eeprom = first.paths.data_root / "saves/xbox/xemu_eeprom.bin"
            eeprom.parent.mkdir()
            eeprom.write_bytes(b"existing EEPROM with HDD key")
            eeprom_before = (eeprom.read_bytes(), eeprom.stat().st_mtime_ns)
            installed_bytecode = (
                first.paths.prefix
                / "share/embercade/runtime/venv/lib/python3.14/site-packages/example/"
                "__pycache__/module.cpython-314.pyc"
            )
            installed_bytecode.write_text("regenerated after relocation", encoding="utf-8")
            payload = root / "Payload with spaces"
            for path in sorted(payload.rglob("*"), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            payload.rmdir()
            second = install_user(_write_payload(root, "two"), environment=environment)
            self.assertEqual(second.mode, "UPDATE/REINSTALL")
            self.assertIn("two", (second.paths.prefix / "bin/embercade").read_text())
            self.assertEqual(user_data.read_text(), "save")
            self.assertEqual((eeprom.read_bytes(), eeprom.stat().st_mtime_ns), eeprom_before)
            install_user(payload, environment=environment)
            self.assertEqual((eeprom.read_bytes(), eeprom.stat().st_mtime_ns), eeprom_before)
            self.assertEqual(second.paths.icon.read_bytes(), b"icon-two\n")

    def test_reinstall_preserves_downloaded_themes_and_active_selection(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            first = install_user(_write_payload(root), environment=environment)
            theme = first.paths.data_root / "themes/downloaded"
            theme.mkdir(parents=True)
            files = {
                theme / "theme.xml": b"downloaded theme",
                theme / "splash.xml": b"theme-owned splash",
                theme / "icon.png": b"theme-owned icon",
                first.paths.data_root / "themes/.tmp/partial.zip.tmp": b"partial",
                first.paths.config_root / "emulators/emulationstation/es_settings.cfg":
                    b'<string name="ThemeSet" value="downloaded" />',
                first.paths.config_root / "secrets/screenscraper.conf":
                    b'SCREENSCRAPER_DEV_ID=example\nSCREENSCRAPER_DEV_PASSWORD=example\n',
                first.paths.config_root / "secrets/screenscraper-user.conf":
                    b'SCREENSCRAPER_USER=example\nSCREENSCRAPER_PASSWORD=example\n',
            }
            for path, data in files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                if path.parent.name == "secrets":
                    path.parent.chmod(0o700)
                    path.chmod(0o600)
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in files}

            updated = install_user(_write_payload(root, "two"), environment=environment)

            self.assertEqual(updated.mode, "UPDATE/REINSTALL")
            self.assertEqual(
                {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in files}, before
            )
            self.assertEqual(updated.paths.icon.read_bytes(), b"icon-two\n")
            self.assertNotEqual(updated.paths.icon.read_bytes(), files[theme / "icon.png"])
            self.assertEqual((first.paths.config_root / "secrets/screenscraper.conf").stat().st_mode & 0o777, 0o600)
            self.assertEqual((first.paths.config_root / "secrets/screenscraper-user.conf").stat().st_mode & 0o777, 0o600)

    def test_reinstall_tolerates_only_existing_application_bytecode(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            first = install_user(_write_payload(root), environment=environment)
            settings = first.paths.config_root / "embercade.toml"
            settings.parent.mkdir(parents=True)
            settings.write_bytes(b"user settings remain untouched")
            before = (settings.read_bytes(), settings.stat().st_mtime_ns)
            relative = "share/embercade/app/embercade/__pycache__/installer.cpython-314.pyc"
            old_cache = first.paths.prefix / relative
            old_cache.parent.mkdir(parents=True)
            old_cache.write_bytes(b"generated by an older installation")
            with self.assertRaisesRegex(InstallationError, "file set"):
                verify_payload(first.paths.prefix)

            payload = _write_payload(root, "two")
            incoming_cache = payload / relative
            incoming_cache.parent.mkdir(parents=True)
            incoming_cache.write_bytes(b"unexpected incoming cache")
            with self.assertRaisesRegex(InstallationError, "file set"):
                install_user(payload, environment=environment)
            incoming_cache.unlink()
            for unexpected in (
                "share/embercade/app/embercade/__pycache__/changed.py",
                "share/embercade/resources/asset.pyc",
            ):
                with self.subTest(unexpected=unexpected):
                    file = first.paths.prefix / unexpected
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_bytes(b"not a disposable application cache")
                    with self.assertRaisesRegex(InstallationError, "file set"):
                        install_user(payload, environment=environment)
                    file.unlink()
            second = install_user(payload, environment=environment)
            self.assertEqual(second.mode, "UPDATE/REINSTALL")
            self.assertFalse(old_cache.exists())
            self.assertEqual((settings.read_bytes(), settings.stat().st_mtime_ns), before)
            verify_payload(second.paths.prefix)

    def test_imported_provider_and_config_survive_install_update_and_uninstall(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            paths = UserInstallPaths.from_environment(environment)
            source_directory = root / "External Provider files"
            source_directory.mkdir()
            source = source_directory / "Xenia Edge Linux.AppImage"
            source.write_bytes(elf(appimage=True, symbols=False))
            source.chmod(0o600)
            roms = root / "External ROMs"
            bios = root / "External BIOS"
            roms.mkdir()
            bios.mkdir()

            def snapshot(path: Path) -> tuple[bytes, int, int]:
                metadata = path.stat()
                return path.read_bytes(), metadata.st_mode & 0o777, metadata.st_mtime_ns

            source_before = snapshot(source)
            identity = {
                "Name": "Xenia Edge",
                "Exec": "xenia_edge %f",
                "StartupWMClass": "xenia_edge",
            }
            with patch("embercade.imports._provider_metadata", return_value=identity):
                imported = import_providers(source_directory, paths.data_root)
                self.assertEqual(imported.imported, 1)
                self.assertEqual(len(imported.imported_paths), 1)
                managed = imported.imported_paths[0]
                self.assertTrue(managed.is_relative_to(paths.data_root / "providers"))
                self.assertEqual(managed.read_bytes(), source_before[0])
                self.assertTrue(os.access(managed, os.R_OK | os.X_OK))
                config = paths.config_root / "embercade.toml"
                configure(
                    config,
                    roms_value=str(roms),
                    bios_value=str(bios),
                    xenia_value=str(managed),
                    environment=environment,
                )
                provider_before = snapshot(managed)
                config_before = snapshot(config)
                managed_entries = tuple(sorted(managed.parent.iterdir()))

                def assert_preserved() -> None:
                    self.assertEqual(snapshot(source), source_before)
                    self.assertEqual(snapshot(managed), provider_before)
                    self.assertEqual(snapshot(config), config_before)
                    self.assertEqual(tuple(sorted(managed.parent.iterdir())), managed_entries)
                    configured = tomllib.loads(config.read_text(encoding="utf-8"))
                    self.assertEqual(detect_xenia_edge(configured, environment), managed)

                with patch(
                    "embercade.imports.import_providers",
                    side_effect=AssertionError("existing managed provider must not be reimported"),
                ):
                    first = install_user(_write_payload(root, "one"), environment=environment)
                    self.assertEqual(first.mode, "NEW INSTALL")
                    assert_preserved()
                    updated = install_user(_write_payload(root, "two"), environment=environment)
                    self.assertEqual(updated.mode, "UPDATE/REINSTALL")
                    assert_preserved()
                    removed = uninstall_user(environment=environment)
                    self.assertEqual(removed.mode, "UNINSTALL")
                    self.assertFalse(paths.prefix.exists())
                    assert_preserved()
                    restored = install_user(_write_payload(root, "two"), environment=environment)
                    self.assertEqual(restored.mode, "NEW INSTALL")
                    assert_preserved()

    def test_update_migrates_previous_manifest_without_a_managed_icon(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            first = install_user(_write_payload(root), environment=environment)
            first.paths.icon.unlink()
            manifest = json.loads(first.paths.manifest.read_text(encoding="utf-8"))
            manifest.pop("icon_path")
            manifest.pop("icon_sha256")
            first.paths.manifest.write_text(json.dumps(manifest), encoding="utf-8")

            updated = install_user(_write_payload(root, "two"), environment=environment)

            self.assertEqual(updated.mode, "UPDATE/REINSTALL")
            self.assertEqual(updated.paths.icon.read_bytes(), b"icon-two\n")

    def test_corrupt_payload_is_rejected_before_targets_are_created(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _write_payload(root)
            (payload / "bin/embercade").write_text("tampered", encoding="utf-8")
            paths = UserInstallPaths.from_environment(_environment(root))
            with self.assertRaises(InstallationError):
                install_user(payload, environment=_environment(root))
            self.assertFalse(paths.prefix.exists())

    def test_failed_activation_rolls_back_existing_install(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            first = install_user(_write_payload(root), environment=environment)
            original = (first.paths.prefix / "bin/embercade").read_text()
            real_replace = os.replace
            calls = 0

            def fail_during_activation(source: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if destination == first.paths.launcher and "backup" not in str(source):
                    raise OSError("activation failure")
                real_replace(source, destination)

            with patch("embercade.installer._replace", side_effect=fail_during_activation):
                with self.assertRaises(OSError):
                    install_user(_write_payload(root, "two"), environment=environment)
            self.assertEqual((first.paths.prefix / "bin/embercade").read_text(), original)
            self.assertTrue(first.paths.launcher.is_symlink())

    def test_uninstall_retains_data_and_is_idempotent(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            installed = install_user(_write_payload(root), environment=environment)
            save = installed.paths.data_root / "saves/save.bin"
            save.parent.mkdir(parents=True)
            save.write_text("save", encoding="utf-8")
            dry = uninstall_user(environment=environment, dry_run=True)
            self.assertEqual(dry.mode, "UNINSTALL")
            self.assertTrue(installed.paths.prefix.exists())
            uninstall_user(environment=environment)
            self.assertFalse(installed.paths.prefix.exists())
            self.assertFalse(installed.paths.icon.exists())
            self.assertEqual(save.read_text(), "save")
            repeated = uninstall_user(environment=environment)
            self.assertEqual(repeated.mode, "NOT INSTALLED")

    def test_purge_requires_confirmation_and_never_deletes_external_paths(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            installed = install_user(_write_payload(root), environment=environment)
            roms = root / "External ROMs"
            bios = root / "External BIOS"
            provider = root / "External Provider.AppImage"
            roms.mkdir()
            bios.mkdir()
            provider.write_text("provider", encoding="utf-8")
            installed.paths.config_root.mkdir(parents=True)
            secret = installed.paths.config_root / "secrets/screenscraper-user.conf"
            secret.parent.mkdir(mode=0o700)
            secret.write_text("SCREENSCRAPER_USER=dummy\nSCREENSCRAPER_PASSWORD=dummy\n", encoding="utf-8")
            secret.chmod(0o600)
            (installed.paths.config_root / "embercade.toml").write_text(
                f'[paths]\nroms = {json.dumps(str(roms))}\nbios = {json.dumps(str(bios))}\n'
                f'[emulators.xenia-edge]\nprovider = "appimage"\nexecutable = {json.dumps(str(provider))}\n',
                encoding="utf-8",
            )
            with self.assertRaises(InstallationError):
                uninstall_user(environment=environment, purge=True)
            uninstall_user(environment=environment, purge=True, purge_confirmed=True)
            self.assertTrue(roms.is_dir())
            self.assertTrue(bios.is_dir())
            self.assertTrue(provider.is_file())
            self.assertFalse(installed.paths.config_root.exists())
            self.assertFalse(secret.exists())

    def test_purge_accepts_managed_xenia_provider(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            installed = install_user(_write_payload(root), environment=environment)
            provider = installed.paths.data_root / "providers/xenia/Xenia.Edge.AppImage"
            provider.parent.mkdir(parents=True)
            provider.write_text("managed copy", encoding="utf-8")
            installed.paths.config_root.mkdir(parents=True)
            (installed.paths.config_root / "embercade.toml").write_text(
                f'[emulators.xenia-edge]\nprovider = "appimage"\n'
                f'executable = {json.dumps(str(provider))}\n',
                encoding="utf-8",
            )
            uninstall_user(environment=environment, purge=True, purge_confirmed=True)
            self.assertFalse(installed.paths.data_root.exists())

    def test_manifest_rejects_path_traversal(self) -> None:
        with TemporaryDirectory() as directory:
            payload = _write_payload(Path(directory))
            manifest = payload / STAGE_MANIFEST_RELATIVE
            data = json.loads(manifest.read_text())
            data["entries"].append({"path": "../escape", "type": "file", "size": 0, "sha256": ""})
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(InstallationError):
                verify_payload(payload)

    def test_missing_and_hash_mismatched_payload_do_not_touch_install(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            payload = _write_payload(root, "one")
            first = install_user(payload, environment=environment)
            old = first.paths.manifest.read_bytes()
            _write_payload(root, "two")
            binary = payload / "bin/embercade"
            for damage in ("missing", "hash"):
                with self.subTest(damage=damage):
                    original = binary.read_bytes()
                    if damage == "missing":
                        binary.unlink()
                    else:
                        binary.write_bytes(b"tampered")
                    with self.assertRaises(InstallationError):
                        install_user(payload, environment=environment)
                    self.assertEqual(first.paths.manifest.read_bytes(), old)
                    binary.write_bytes(original)

    def test_post_activation_verification_failure_restores_previous_install(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            payload = _write_payload(root, "one")
            first = install_user(payload, environment=environment)
            original = (first.paths.prefix / "bin/embercade").read_bytes()
            original_manifest = first.paths.manifest.read_bytes()
            _write_payload(root, "two")
            real_replace = os.replace

            def corrupt_after_activation(source: Path, destination: Path) -> None:
                real_replace(source, destination)
                if destination == first.paths.prefix and source.name == "payload":
                    (destination / "bin/embercade").write_bytes(b"corrupt after activation")

            with patch("embercade.installer._replace", side_effect=corrupt_after_activation):
                with self.assertRaises(InstallationError):
                    install_user(payload, environment=environment)
            self.assertEqual((first.paths.prefix / "bin/embercade").read_bytes(), original)
            self.assertEqual(first.paths.manifest.read_bytes(), original_manifest)

    def test_install_and_uninstall_never_invoke_sudo_or_pacman(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            calls: list[list[str]] = []

            def record(argv: list[str], **_kwargs: object) -> object:
                calls.append(argv)
                return type("Completed", (), {"returncode": 0})()

            with patch("embercade.installer.subprocess.run", side_effect=record):
                install_user(_write_payload(root), environment=environment)
                uninstall_user(environment=environment)
            flattened = [part for argv in calls for part in argv]
            self.assertNotIn("sudo", flattened)
            self.assertNotIn("pacman", flattened)

    def test_reinstall_is_blocked_while_installed_process_is_running(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = _environment(root)
            install_user(_write_payload(root), environment=environment)
            with patch("embercade.installer.running_installation_pids", return_value=(1234,)):
                with self.assertRaisesRegex(InstallationError, "currently running"):
                    install_user(_write_payload(root, "two"), environment=environment)

    def test_running_process_probe_matches_only_installed_prefix(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = UserInstallPaths.from_environment(_environment(root))
            proc = root / "proc"
            (proc / "101").mkdir(parents=True)
            (proc / "101/cmdline").write_bytes(
                str(paths.prefix / "bin/embercade").encode() + b"\0"
            )
            self.assertEqual(running_installation_pids(paths, proc_root=proc, current_pid=999), (101,))

    def test_fish_path_warning_is_shell_specific_and_non_mutating(self) -> None:
        with TemporaryDirectory() as directory:
            paths = UserInstallPaths.from_environment(_environment(Path(directory)))
            guidance = launcher_path_guidance(
                paths, {"PATH": "/usr/bin", "SHELL": "/usr/bin/fish"}
            )
            self.assertIn(f"fish_add_path {paths.launcher.parent}", guidance)


if __name__ == "__main__":
    unittest.main()

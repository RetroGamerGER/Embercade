from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import subprocess
import tarfile
import unittest

from embercade.installer import STAGE_MANIFEST_RELATIVE
from embercade.transfer_payload import (
    CHECKSUM_NAME,
    MANIFEST_NAME,
    README_NAME,
    TransferPayloadError,
    audit_stage_payload,
    build_transfer_payload,
    verify_transfer_bundle,
)


def _write_stage(root: Path, extra_files: dict[str, bytes] | None = None) -> Path:
    stage = root / "Production Stage with spaces"
    files: dict[str, bytes] = {
        "bin/embercade": (
            b"#!/bin/sh\n"
            b"printf '%s\\n' \"$@\" > \"$HOME/install-args\"\n"
        ),
        "bin/embercade-provider-runner": b"#!/bin/sh\nexit 0\n",
        "share/embercade/frontend/emulationstation": b"frontend\n",
        "share/embercade/runtime/venv/bin/python": b"python\n",
        "share/embercade/resources/defaults/batocera.conf": b"global.bezel=none\n",
        "share/applications/embercade.desktop": (
            b"[Desktop Entry]\nName=Embercade\nExec=embercade\nType=Application\n"
        ),
    }
    files.update(extra_files or {})
    entries: list[dict[str, object]] = []
    for relative, data in files.items():
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if (
            relative.startswith("bin/")
            or relative.endswith("emulationstation")
            or relative.endswith("/python")
        ):
            path.chmod(0o755)
        entries.append(
            {
                "path": relative,
                "type": "file",
                "size": len(data),
                "sha256": sha256(data).hexdigest(),
            }
        )
    manifest = stage / STAGE_MANIFEST_RELATIVE
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "format": 1,
                "embercade_version": "0.1.dev0",
                "pins": {"test": "pinned"},
                "entries": sorted(entries, key=lambda item: str(item["path"])),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return stage


class TransferPayloadTests(unittest.TestCase):

    def test_first_run_readme_places_setup_before_bootstrap(self) -> None:
        from embercade.transfer_payload import _first_test_readme

        text = _first_test_readme()
        self.assertLess(text.index("embercade wizard"), text.index("embercade bootstrap"))
        self.assertIn("embercade setup", text)

    def test_payload_creation_manifest_readme_and_archive(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            stage = _write_stage(root)
            result = build_transfer_payload(
                stage_root=stage,
                dist_root=root / "dist",
                source_commit="a" * 40,
                build_root=root / "source repository",
            )
            self.assertTrue((result.directory / "install").is_file())
            self.assertTrue((result.directory / README_NAME).is_file())
            self.assertTrue((result.directory / CHECKSUM_NAME).is_file())
            self.assertTrue(result.archive.is_file())
            manifest = verify_transfer_bundle(result.directory)
            self.assertEqual(manifest["embercade_version"], "0.1.dev0")
            self.assertEqual(manifest["source_commit"], "a" * 40)
            paths = {entry["path"] for entry in manifest["payload_files"]}
            self.assertIn("bin/embercade", paths)
            self.assertIn(STAGE_MANIFEST_RELATIVE.as_posix(), paths)
            self.assertNotIn("share/embercade/app/embercade/transfer_payload.py", paths)
            self.assertEqual(result.payload_tree_sha256, manifest["payload_tree_sha256"])
            with tarfile.open(result.archive, "r:gz") as archive:
                names = set(archive.getnames())
            self.assertIn(f"{result.directory.name}/install", names)
            self.assertIn(f"{result.directory.name}/{MANIFEST_NAME}", names)

    def test_bundle_has_no_source_repo_or_development_path_dependency(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Source Repo with spaces"
            stage = _write_stage(root)
            result = build_transfer_payload(
                stage_root=stage,
                dist_root=root / "dist",
                source_commit="b" * 40,
                build_root=source,
            )
            manifest_text = result.manifest.read_text(encoding="utf-8")
            install_text = (result.directory / "install").read_text(encoding="utf-8")
            self.assertNotIn(str(source), manifest_text)
            self.assertNotIn(str(stage), manifest_text)
            self.assertNotIn(".work/", install_text)
            self.assertNotIn("dev-run", install_text)
            self.assertFalse((result.directory / ".git").exists())
            self.assertFalse((result.directory / "tests").exists())

    def test_forbidden_rom_provider_and_runtime_marker_are_rejected(self) -> None:
        cases = (
            {"share/game.iso": b"rom"},
            {"share/Xenia.AppImage": b"\x7fELFprovider"},
            {"share/embercade/resources/runtime/config.txt": b"call dev-run"},
            {"share/embercade/secrets/screenscraper.conf": b"SCREENSCRAPER_DEV_PASSWORD=dummy"},
            {"share/embercade/screenscraper-user.conf": b"SCREENSCRAPER_PASSWORD=dummy"},
            {"share/embercade/resources/defaults/es_settings.cfg":
             b'<config><string name="ScreenScraperPass" value="dummy" /></config>'},
        )
        for extra in cases:
            with self.subTest(extra=tuple(extra)):
                with TemporaryDirectory() as directory:
                    root = Path(directory)
                    stage = _write_stage(root, extra)
                    with self.assertRaises(TransferPayloadError):
                        audit_stage_payload(stage, build_root=root / "source")

    def test_install_delegates_to_existing_payload_installer_with_temp_home(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            stage = _write_stage(root)
            result = build_transfer_payload(
                stage_root=stage,
                dist_root=root / "Distribution with spaces",
                source_commit="c" * 40,
            )
            home = root / "Temporary Home with spaces"
            home.mkdir()
            environment = {"HOME": str(home), "PATH": "/usr/bin:/bin"}
            completed = subprocess.run(
                [str(result.directory / "install"), "--dry-run"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            arguments = (home / "install-args").read_text(encoding="utf-8").splitlines()
            self.assertEqual(arguments[0], "install")
            self.assertEqual(arguments[1:3], ["--payload", str(result.directory / "payload")])
            self.assertEqual(arguments[3:], ["--no-setup", "--dry-run"])
            install_text = (result.directory / "install").read_text(encoding="utf-8")
            for network_tool in ("curl", "wget", "git clone", "pip install"):
                self.assertNotIn(network_tool, install_text)

    def test_corrupted_payload_is_rejected_before_installer_execution(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result = build_transfer_payload(
                stage_root=_write_stage(root),
                dist_root=root / "dist",
                source_commit="d" * 40,
            )
            (result.directory / "payload/share/applications/embercade.desktop").write_text(
                "tampered", encoding="utf-8"
            )
            home = root / "home"
            home.mkdir()
            completed = subprocess.run(
                [str(result.directory / "install")],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse((home / "install-args").exists())
            with self.assertRaises(TransferPayloadError):
                verify_transfer_bundle(result.directory)

    def test_corrupted_checksum_list_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result = build_transfer_payload(
                stage_root=_write_stage(root),
                dist_root=root / "dist",
                source_commit="f" * 40,
            )
            (result.directory / CHECKSUM_NAME).write_text(
                "0" * 64 + "  install\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(TransferPayloadError, "checksum"):
                verify_transfer_bundle(result.directory)

    def test_two_fresh_builds_are_byte_reproducible(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            stage = _write_stage(root)
            first = build_transfer_payload(
                stage_root=stage,
                dist_root=root / "dist",
                source_commit="e" * 40,
            )
            first_archive = first.archive.read_bytes()
            first_manifest = first.manifest.read_bytes()
            second = build_transfer_payload(
                stage_root=stage,
                dist_root=root / "dist",
                source_commit="e" * 40,
            )
            self.assertEqual(second.archive.read_bytes(), first_archive)
            self.assertEqual(second.manifest.read_bytes(), first_manifest)
            self.assertEqual(second.archive_sha256, first.archive_sha256)


if __name__ == "__main__":
    unittest.main()

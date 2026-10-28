# SPDX-License-Identifier: MIT
"""Verify source/notice delivery inputs and archive safety without a build."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import tomllib
import unittest


PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_sources", PROJECT / "compliance/prepare_sources.py")
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class SourceDeliveryTests(unittest.TestCase):
    def test_public_source_receipt_never_claims_publication_approval(self):
        for distribution,state,status in (('PRIVATE','BLOCKED','LOCAL_PREPARATION_NOT_PUBLISHED'),
            ('PUBLIC','PREPARED_NOT_PUBLISHED','PUBLIC_CANDIDATE_NOT_PUBLISHED')):
            result=delivery.preparation_metadata({'distribution':distribution,'public_release':state})
            self.assertEqual(result['status'],status)
            self.assertEqual(result['artifact_distribution'],distribution)
            self.assertFalse(result['public_release_approved'])
        with self.assertRaisesRegex(ValueError,'publication state'):
            delivery.preparation_metadata({'distribution':'PUBLIC','public_release':'PUBLISHED'})

    def test_original_notice_copies_match_their_index(self):
        index = json.loads((PROJECT / "compliance/notices.lock.json").read_text())
        for row in index["notices"]:
            self.assertTrue(row["file"].startswith("LICENSES/third-party/"))
            self.assertEqual(delivery.checked_file(PROJECT, row).stat().st_size, row["bytes"])
        names = {r["file"] for r in index["notices"]}
        for suffix in ("python-vendors/libuv-LICENSE-extra.txt", "python-vendors/libyaml-LICENSE.txt",
                       "python-vendors/Pillow-wheel-LICENSE.txt", "fonts/EMBEDDED-NOTICES.txt",
                       "fonts/OFL-1.1.txt", "frontend/libcheevos-embedded-NOTICES.txt"):
            self.assertIn("LICENSES/third-party/"+suffix, names)

    def test_source_set_covers_locked_python_and_explicit_vendor_packages(self):
        index = json.loads((PROJECT / "compliance/sources.lock.json").read_text())
        sources = {r["component"].lower().replace("_", "-"): r for r in index["sources"]}
        for line in (PROJECT / "runtime/requirements.lock").read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            name, version = line.split("==")
            self.assertEqual(sources[name.lower().replace("_", "-")]["version"], version)
        self.assertIn("pip", sources)
        self.assertIn("certifi", sources)
        self.assertEqual(set(index["required_components"]), {r["component"] for r in index["sources"]})

    def test_native_and_batocera_source_versions_match_existing_locks(self):
        sources = {r["component"]: r for r in json.loads((PROJECT / "compliance/sources.lock.json").read_text())["sources"]}
        pins = tomllib.loads((PROJECT / "upstream.lock").read_text())["upstream"]
        self.assertEqual(sources["batocera"]["version"], pins["batocera.linux"])
        self.assertEqual(sources["emulationstation"]["version"], pins["batocera-emulationstation"])
        for name, row in tomllib.loads((PROJECT / "runtime/frontend-libs.lock").read_text()).items():
            self.assertEqual(sources[name]["sha256"], row["source_sha256"])
        runtime = json.loads((PROJECT / "packaging/appimage/licenses/index.json").read_text())
        self.assertEqual(sources["type2-runtime"]["version"], runtime["runtime"]["commit"])
        for row in runtime["build_evidence"]["recipe_pinned_archives"]:
            self.assertEqual(sources[row["component"]]["sha256"], row["sha256"])

    def test_cache_rejects_changed_input_traversal_and_external_links(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            inside = root / "cache"
            inside.mkdir()
            (inside / "source.tar.gz").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                delivery.checked_file(inside, {"file": "source.tar.gz", "sha256": "0"*64})
            for name in ("../secret", "/tmp/secret"):
                with self.assertRaises(ValueError):
                    delivery.child(inside, name)
            (inside / "outside").symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                delivery.child(inside, "outside/secret")

    def test_extraction_rejects_traversal_and_escaping_symlink(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for number, (name, link) in enumerate((("../outside", None), ("source/link", "/etc/passwd"))):
                archive = root / f"bad-{number}.tar"
                with tarfile.open(archive, "w") as stream:
                    info = tarfile.TarInfo(name)
                    if link:
                        info.type = tarfile.SYMTYPE
                        info.linkname = link
                        stream.addfile(info)
                    else:
                        info.size = 3
                        stream.addfile(info, io.BytesIO(b"bad"))
                with self.assertRaises((tarfile.FilterError, ValueError)):
                    delivery.extract(archive, root / f"extract-{number}")
            self.assertFalse((root / "outside").exists())

    def test_source_archive_is_reproducible_and_retains_executable_mode(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            (source / "file").write_text("original source\n")
            (source / "file").chmod(0o755)
            for name in ("a.tar.gz", "b.tar.gz"):
                delivery.archive_tree(source, root / name)
            self.assertEqual(delivery.digest(root / "a.tar.gz"), delivery.digest(root / "b.tar.gz"))
            with tarfile.open(root / "a.tar.gz") as stream:
                self.assertEqual(stream.getmember("Embercade-sources/file").mode, 0o755)

    def test_rebuild_instructions_cover_static_and_dynamic_lgpl_without_nc_restriction(self):
        text = (PROJECT / "compliance/REBUILDING.md").read_text()
        for required in ("section 6(a)", "mount.c.diff", "--runtime-file", "LibRaw", "Pyudev", "reverse engineering"):
            self.assertIn(required, text)
        self.assertIn("adds no restriction", text)
        self.assertNotIn("guaranteed legal independence", text)


if __name__ == "__main__":
    unittest.main()

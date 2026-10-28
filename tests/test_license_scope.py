"""Guard scoped grants, original legal texts and complete first-party mapping."""

import csv
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class LicenseScopeTests(unittest.TestCase):
    def test_every_current_client_source_is_explicitly_mapped(self):
        scope = json.loads((PROJECT / "LICENSES/scope.json").read_text())
        expected = {p.relative_to(PROJECT).as_posix() for p in (PROJECT / "src/embercade").glob("*.py")}
        self.assertEqual(set(scope["client_software"]["paths"]), expected)
        self.assertEqual(scope["client_software"]["license"], "PolyForm-Noncommercial-1.0.0")
        self.assertTrue(all(p.startswith("src/embercade/") for p in expected))

    def test_own_code_grants_never_overlap_the_backend_or_foreign_payload(self):
        scope = json.loads((PROJECT / "LICENSES/scope.json").read_text())
        client = set(scope["client_software"]["paths"])
        integration = set(scope["integration_contributions"]["paths"])
        self.assertFalse(client & integration)
        self.assertIn("integration/batocera/adapter.py", integration)
        self.assertEqual(scope["integration_contributions"]["license"], "MIT")
        self.assertEqual(scope["branding"]["license"], "CC-BY-NC-SA-4.0")
        self.assertEqual(scope["branding"]["status"], "OWNER_CONFIRMED_CANVA_AI_ORIGIN")
        for path in scope["branding"]["paths"]:
            self.assertTrue(path.startswith("resources/branding/") or path == "docs/images/embercade-poster.jpg")
            self.assertNotIn("..", Path(path).parts)
            self.assertTrue((PROJECT / path).is_file(), path)
        self.assertFalse(scope["public_release_approved"])
        for path in client | integration:
            self.assertTrue((PROJECT / path).is_file(), path)
            self.assertFalse(Path(path).is_absolute(), path)
            self.assertNotIn("..", Path(path).parts)
        self.assertFalse(any(p.startswith((".work/", "dist/", "resources/branding/")) for p in client))

    def test_standard_text_hashes_and_retained_upstream_copies(self):
        for folder in ("LICENSES", "LICENSES/prepared"):
            index = json.loads((PROJECT / folder / "sources.json").read_text())
            for entry in index["sources"]:
                data = (PROJECT / folder / entry["file"]).read_bytes()
                self.assertEqual(len(data), entry["bytes"], entry["file"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"], entry["file"])
                if entry.get("source_copy", "").startswith("prepared/CC-") or entry.get("source_copy", "").startswith("prepared/PolyForm-"):
                    self.assertEqual(data, (PROJECT / "LICENSES" / entry["source_copy"]).read_bytes())

    def test_component_map_has_no_missing_sources_or_patch_additions(self):
        with (PROJECT / "docs/LICENSE_COMPONENT_MAP.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        mapped = {row["path_or_group"] for row in rows}
        expected = set()
        for folder, pattern in (("src/embercade", "*.py"), ("patches/batocera-launch", "*.patch"),
                                ("patches/emulationstation", "*.patch"), ("patches/emulationstation", "*.h")):
            expected.update(p.relative_to(PROJECT).as_posix() for p in (PROJECT / folder).glob(pattern))
        self.assertTrue(expected <= mapped, sorted(expected - mapped))
        self.assertIn("integration/batocera/adapter.py", mapped)
        self.assertTrue(all(row["review_status"] != "UPSTREAM_BOUND_INTEGRATION" for row in rows
                            if row["path_or_group"].startswith("src/embercade/")))

    def test_payload_map_matches_real_contents_without_weakening_privacy_guard(self):
        from embercade.appimage import _scan_private_paths
        from embercade.staging import _payload_license_scope
        original = (PROJECT / "LICENSES/scope.json").read_bytes()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            client = root / "app/embercade/paths.py"
            backend = root / "integration/batocera/adapter.py"
            client.parent.mkdir(parents=True)
            backend.parent.mkdir(parents=True)
            client.touch()
            backend.touch()
            scope, rows = _payload_license_scope(PROJECT, root)
            self.assertEqual(scope["client_software"]["paths"], ["src/embercade/paths.py"])
            self.assertEqual(scope["integration_contributions"]["paths"], ["integration/batocera/adapter.py"])
            self.assertEqual(scope["independent_tools_and_tests"]["paths"], [])
            self.assertEqual(scope["branding"]["paths"], [])
            self.assertEqual(scope["source_scope_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual({r["path_or_group"] for r in rows},
                             {"src/embercade/paths.py", "integration/batocera/adapter.py"})
            (root / "scope.json").write_text(json.dumps(scope))
            _scan_private_paths(root, build_root=PROJECT)
        self.assertEqual(original, (PROJECT / "LICENSES/scope.json").read_bytes())


if __name__ == "__main__":
    unittest.main()

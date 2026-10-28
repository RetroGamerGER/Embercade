"""User-facing update flow through the existing payload installer CLI."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import unittest

from embercade.cli import main
from embercade.installer import UserInstallPaths
from tests.test_installer import _environment, _write_payload


class UpdateUxTests(unittest.TestCase):
    def _run(
        self, payload: Path, environment: dict[str, str], *options: str,
        no_setup: bool = True,
    ) -> tuple[int, str]:
        output = StringIO()
        with (
            patch.dict(os.environ, environment, clear=True),
            redirect_stdout(output),
            patch("embercade.cli.sys.stdin") as stdin,
        ):
            stdin.isatty.return_value = True
            result = main([
                "install", "--payload", str(payload),
                *(["--no-setup"] if no_setup else []), *options,
            ])
        return result, output.getvalue()

    def test_dry_run_update_noop_and_preserved_state_messaging(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            env = _environment(root)
            payload = _write_payload(root, "one")
            self.assertEqual(self._run(payload, env)[0], 0)
            paths = UserInstallPaths.from_environment(env)
            user_config = paths.config_root / "embercade.toml"
            user_config.parent.mkdir(parents=True)
            user_config.write_text("[paths]\n", encoding="utf-8")
            before = (user_config.read_bytes(), user_config.stat().st_mtime_ns)

            _write_payload(root, "two")
            code, dry_output = self._run(payload, env, "--dry-run")
            self.assertEqual(code, 0)
            self.assertIn("Current: EMBERCADE 1.0 (package 0.1.dev0, payload ", dry_output)
            self.assertIn("Incoming: EMBERCADE 1.0 (package 0.1.dev0, payload ", dry_output)
            self.assertIn("UPDATE/REINSTALL", dry_output)
            self.assertIn("managed cores/providers", dry_output)
            self.assertIn("Steam shortcut/artwork", dry_output)
            self.assertIn("Dry run complete: no files changed.", dry_output)
            self.assertEqual((user_config.read_bytes(), user_config.stat().st_mtime_ns), before)

            with patch("embercade.cli.main", wraps=main) as wrapped:
                code, updated = self._run(payload, env, no_setup=False)
                self.assertEqual(wrapped.call_count, 0, "an update must not enter first-run setup")
            self.assertEqual(code, 0)
            self.assertIn("Application files installed and verified", updated)
            self.assertIn("Next: embercade doctor", updated)
            self.assertNotIn("Next: embercade setup", updated)
            self.assertEqual((user_config.read_bytes(), user_config.stat().st_mtime_ns), before)

            manifest_before = paths.manifest.stat().st_mtime_ns
            code, repeated = self._run(payload, env)
            self.assertEqual(code, 0)
            self.assertIn("ALREADY UP TO DATE", repeated)
            self.assertIn("No files changed", repeated)
            self.assertEqual(paths.manifest.stat().st_mtime_ns, manifest_before)

    def test_invalid_payload_is_human_readable_and_keeps_existing_install(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            env = _environment(root)
            payload = _write_payload(root)
            self._run(payload, env)
            paths = UserInstallPaths.from_environment(env)
            old_manifest = paths.manifest.read_bytes()
            (payload / "bin/embercade").write_text("damaged", encoding="utf-8")
            errors = StringIO()
            with (
                patch.dict(os.environ, env, clear=True),
                redirect_stderr(errors),
                self.assertRaises(SystemExit) as stopped,
            ):
                main(["install", "--payload", str(payload), "--dry-run"])
            self.assertEqual(stopped.exception.code, 2)
            self.assertIn("installation/update stopped", errors.getvalue())
            self.assertIn("No user data was purged", errors.getvalue())
            self.assertNotIn("Traceback", errors.getvalue())
            self.assertEqual(paths.manifest.read_bytes(), old_manifest)


if __name__ == "__main__":
    unittest.main()

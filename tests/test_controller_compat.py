from unittest.mock import Mock, patch
from pathlib import Path
import json
import os
import subprocess
import stat
import tempfile
import unittest

from embercade import controller_compat as compat


class ControllerCompatTests(unittest.TestCase):
    def status(self, managed=False, disabled=False):
        return dict(driver_present=True, shift_disabled=disabled, managed=managed,
                    can_enable=not disabled, can_undo=managed, devices=[], code="ready")

    def test_fixed_isolated_helper_command_and_sanitized_auth_environment(self):
        payload = dict(ok=True, code="enabled", changed=True, pending_reconnect=[])
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps(payload), ""))
        with patch.object(compat, "status", return_value=self.status()), patch.dict(os.environ,
                {"PYTHONPATH": "/hostile", "LD_PRELOAD": "/hostile.so", "DISPLAY": ":7"}):
            result = compat.apply("enable", runner=runner)
        self.assertTrue(result["ok"])
        command = runner.call_args.args[0]
        self.assertEqual(command[:4], ["/usr/bin/pkexec", "/usr/bin/python3", "-I", "-B"])
        helper = Path(command[4])
        self.assertEqual(helper.name, "xpadneo_helper.py")
        self.assertEqual(helper.parent.parent, Path("/tmp"))
        self.assertFalse(helper.parent.exists())
        self.assertEqual(command[5:], ["enable"])
        env = runner.call_args.kwargs["env"]
        self.assertNotIn("PYTHONPATH", env)
        self.assertNotIn("LD_PRELOAD", env)
        self.assertEqual(env["DISPLAY"], ":7")
        self.assertNotIn("shell", runner.call_args.kwargs)

    def test_authorization_cancel_and_denial_are_distinct(self):
        for code, expected in ((126, "authorization_cancelled"), (127, "authorization_failed")):
            with self.subTest(code=code), patch.object(compat, "status", return_value=self.status()):
                result = compat.apply("enable", runner=Mock(return_value=subprocess.CompletedProcess([], code, "", "")))
            self.assertEqual(result["code"], expected)
            self.assertFalse(result["changed"])

    def test_lost_response_refreshes_actual_persistence_and_does_not_claim_rollback(self):
        with patch.object(compat, "status", side_effect=[self.status(), self.status(True, True)]):
            result = compat.apply("enable", runner=Mock(return_value=subprocess.CompletedProcess([], 1, "not JSON", "")))
        self.assertEqual(result["code"], "outcome_unknown")
        self.assertTrue(result["changed"])
        self.assertTrue(result["status"]["managed"])

    def test_partial_result_is_preserved(self):
        payload = dict(ok=False, code="reconnect_pending", changed=True, pending_reconnect=["00:11:22:33:44:55"])
        with patch.object(compat, "status", return_value=self.status(True, True)):
            result = compat.apply("undo", runner=Mock(return_value=subprocess.CompletedProcess([], 1, json.dumps(payload), "")))
        self.assertEqual(result["pending_reconnect"], payload["pending_reconnect"])
        self.assertTrue(result["changed"])

    def test_invalid_action_does_not_authenticate_or_probe(self):
        runner = Mock()
        with patch.object(compat, "status") as status:
            self.assertEqual(compat.apply("enable /tmp/root", runner=runner)["code"], "invalid_request")
        runner.assert_not_called()
        status.assert_not_called()

    def test_missing_privilege_tool_disables_offer_without_prompt(self):
        with patch.object(compat.xpadneo_helper, "inspect", return_value=self.status()), patch.object(os, "access", return_value=False):
            result = compat.status()
        self.assertFalse(result["can_enable"])
        self.assertEqual(result["code"], "unavailable")

    def test_appimage_helper_copy_has_exact_bytes_private_modes_and_ignores_tmpdir(self):
        source = Path(compat.__file__).resolve().with_name("xpadneo_helper.py")
        contents = source.read_bytes()
        copied = []
        def run(command, **_kwargs):
            path = Path(command[4])
            copied.append(path)
            self.assertEqual(path.parent.parent, Path("/tmp"))
            self.assertFalse(path.is_relative_to(source.parent))
            self.assertEqual(path.read_bytes(), contents)
            self.assertEqual(list(path.parent.iterdir()), [path])
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(path.stat().st_uid, os.getuid())
            return subprocess.CompletedProcess(command, 0, json.dumps(dict(
                ok=True, changed=True, code="enabled", pending_reconnect=[])), "")
        with patch.object(compat, "status", return_value=self.status()), \
                patch.dict(os.environ, {"TMPDIR": "/nonexistent-fuse-mount"}):
            self.assertTrue(compat.apply("enable", runner=run)["ok"])
        self.assertEqual(source.read_bytes(), contents)
        self.assertFalse(copied[0].parent.exists())

    def test_staged_copy_removed_on_auth_cancel_rejection_invalid_reply_and_runner_failure(self):
        for outcome in (126, 127, 1, OSError("fixture spawn failure"),
                        subprocess.TimeoutExpired("fixture", 1), KeyboardInterrupt()):
            paths = []
            def run(command, **_kwargs):
                path = Path(command[4])
                paths.append(path)
                self.assertTrue(path.exists())
                if isinstance(outcome, BaseException):
                    raise outcome
                return subprocess.CompletedProcess(command, outcome, "invalid reply", "")
            with self.subTest(outcome=outcome), patch.object(compat, "status", return_value=self.status()):
                if isinstance(outcome, KeyboardInterrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        compat.apply("enable", runner=run)
                else:
                    self.assertFalse(compat.apply("enable", runner=run)["ok"])
            self.assertEqual(len(paths), 1)
            self.assertFalse(paths[0].parent.exists())

    def test_staging_failure_cleans_private_directory_without_authentication(self):
        actual_temporary = tempfile.TemporaryDirectory
        directories = []
        def temporary(**kwargs):
            result = actual_temporary(**kwargs)
            directories.append(Path(result.name))
            return result
        runner = Mock()
        with patch.object(compat, "status", return_value=self.status()), \
                patch.object(compat.tempfile, "TemporaryDirectory", side_effect=temporary), \
                patch.object(compat.os, "fchmod", side_effect=OSError("fixture private-file failure")):
            result = compat.apply("enable", runner=runner)
        self.assertEqual(result["code"], "unavailable")
        self.assertFalse(result["changed"])
        runner.assert_not_called()
        self.assertEqual(len(directories), 1)
        self.assertFalse(directories[0].exists())

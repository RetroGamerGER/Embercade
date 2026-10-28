from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import json
import os
import subprocess
import sys
import threading
import pty
import select
import time
import unittest

from embercade.host_install import read_result, run_installation, terminal_command


class HostInstallTests(unittest.TestCase):
    def test_konsole_has_own_lifecycle_and_no_unconditional_hold_or_shell(self):
        with patch("embercade.host_install.shutil.which", side_effect=lambda name, **_: "/usr/bin/konsole" if name == "konsole" else None):
            argv = terminal_command(["/App Image/embercade", "host-install", "/state with spaces/result.json"])
        self.assertEqual(argv, ["/usr/bin/konsole", "--separate", "--nofork", "-e", "/App Image/embercade", "host-install", "/state with spaces/result.json"])
        self.assertNotIn("--hold", argv)

    def test_result_is_not_published_until_child_and_transaction_hooks_finish(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            installed, hooks, release = threading.Event(), threading.Event(), threading.Event()
            def runner(argv, *, check):
                installed.set()
                release.wait(3)
                hooks.set()
                return subprocess.CompletedProcess(argv, 0)
            hold = Mock()
            worker = threading.Thread(target=run_installation, args=(path, ["fake pacman"], "en"),
                                      kwargs=dict(runner=runner, input_function=hold, output=lambda _: None))
            worker.start()
            self.assertTrue(installed.wait(1))
            self.assertIsNone(read_result(path))
            release.set(); worker.join(3)
            self.assertFalse(worker.is_alive())
            self.assertTrue(hooks.is_set())
            self.assertEqual(read_result(path), dict(outcome="success", code=0))
            hold.assert_not_called()

    def test_failure_preserves_terminal_until_acknowledged_and_publishes_for_retry(self):
        for language in ("de", "en"):
            with self.subTest(language=language), TemporaryDirectory() as directory:
                path = Path(directory) / "result.json"
                messages = []
                def acknowledge(prompt):
                    self.assertEqual(read_result(path), dict(outcome="failed", code=7))
                    messages.append(prompt)
                code = run_installation(path, [sys.executable, "-c", "raise SystemExit(7)"], language,
                                        input_function=acknowledge, output=messages.append)
                self.assertEqual(code, 7)
                self.assertIn("Enter", messages[-1])
                self.assertEqual(len(messages), 2)

    def test_real_failed_child_keeps_diagnostics_in_owned_terminal_until_enter(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            master, slave = pty.openpty()
            script = "from pathlib import Path; import sys; from embercade.host_install import run_installation; raise SystemExit(run_installation(Path(sys.argv[1]), [sys.executable, '-c', \"print(\\'diagnostic fixture\\');raise SystemExit(9)\"], 'en'))"
            process = subprocess.Popen([sys.executable, "-c", script, str(path)], stdin=slave, stdout=slave, stderr=slave)
            os.close(slave)
            try:
                deadline = time.monotonic() + 3
                while read_result(path) is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertEqual(read_result(path), dict(outcome="failed", code=9))
                self.assertIsNone(process.poll())
                os.write(master, b"\n")
                self.assertEqual(process.wait(timeout=3), 9)
                self.assertIn(b"diagnostic fixture", os.read(master, 8192))
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)
                os.close(master)

    def test_cancel_and_spawn_failure_cannot_report_success(self):
        for error, expected in ((KeyboardInterrupt(), 130), (OSError(), 127)):
            with self.subTest(error=type(error)), TemporaryDirectory() as directory:
                path = Path(directory) / "result.json"
                with patch("builtins.print"):
                    run_installation(path, ["fake"], "de", runner=Mock(side_effect=error),
                                     input_function=lambda _: "", output=lambda _: None)
                self.assertEqual(read_result(path)["code"], expected)
                self.assertNotEqual(read_result(path)["outcome"], "success")

    def test_crashed_child_is_failure_and_keeps_output_instead_of_claiming_cancel(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            hold = Mock()
            code = run_installation(path, ["fake"], "en", runner=Mock(return_value=Mock(returncode=-11)),
                                    input_function=hold, output=lambda _: None)
            self.assertEqual(code, 139)
            self.assertEqual(read_result(path), dict(outcome="failed", code=-11))
            hold.assert_called_once()

    def test_result_rejects_symlinks_and_nonprivate_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "result.json"
            victim = root / "victim"
            victim.write_text("original")
            path.symlink_to(victim)
            with self.assertRaises(OSError):
                run_installation(path, ["fake"], "en", runner=Mock(return_value=Mock(returncode=0)))
            self.assertEqual(victim.read_text(), "original")
            path.unlink()
            root.chmod(0o755)
            with self.assertRaises(ValueError): read_result(path)

class HostProgressTests(unittest.TestCase):
    def test_progress_records_phases_and_duration_without_faking_result(self):
        from embercade.host_install import publish_progress,read_progress
        with TemporaryDirectory() as directory:
            path=Path(directory)/'progress.json'
            with patch('embercade.host_install.time.monotonic',side_effect=[10.0,25.0]):
                publish_progress(path,'checking');publish_progress(path,'repository')
            self.assertEqual(read_progress(path),dict(phase='repository',started=10.0,updated=25.0))
            self.assertIsNone(read_result(path.with_name('result.json')))
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            entries=[json.loads(line) for line in path.with_name('timings.jsonl').read_text().splitlines()]
            self.assertEqual(entries[-1],dict(phase='repository',elapsed_seconds=15.0))
            self.assertEqual(set(entries[-1]),{'phase','elapsed_seconds'})

    def test_progress_refuses_symlinks_and_malformed_phase_or_clocks(self):
        from embercade.host_install import publish_progress,read_progress
        with TemporaryDirectory() as directory:
            root=Path(directory);path=root/'progress.json';victim=root/'victim';victim.write_text('preserved')
            path.symlink_to(victim)
            with self.assertRaises(OSError):publish_progress(path,'checking')
            self.assertEqual(victim.read_text(),'preserved');path.unlink()
            for item in (dict(phase=[],started=1,updated=2),dict(phase='checking',started=True,updated=2),dict(phase='checking',started=3,updated=2)):
                path.write_text(json.dumps(item));path.chmod(0o600)
                with self.assertRaises(ValueError):read_progress(path)

    def test_real_result_and_timing_archive_survive_terminal_cleanup(self):
        from embercade.host_install import TerminalInstallation
        with TemporaryDirectory() as root:
            directory=TemporaryDirectory(prefix='host-install-',dir=root);path=Path(directory.name)/'result.json'
            run_installation(path,[sys.executable,'-c','pass'],'en',output=lambda _:None)
            transaction=TerminalInstallation(Mock(),path,directory);transaction.process.poll.return_value=0
            transaction.reap()
            self.assertFalse(path.parent.exists())
            archive=list(Path(root).glob('*-timings.json'));self.assertEqual(len(archive),1)
            proof=json.loads(archive[0].read_text());self.assertEqual(proof['result']['code'],0)
            self.assertEqual([e['phase'] for e in proof['events']],['starting','completed'])

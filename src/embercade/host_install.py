"""Own one terminal transaction and publish its real child result before exit/hold.

The terminal launcher can fork/reuse a server. Its exit status is never used as
package success. The child CLI waits for pacman/AUR including transaction hooks.
Only that child completing with zero permits the extra terminal to close.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import json
import math
import time
import os
import shutil
import stat
import subprocess
import tempfile

from embercade.i18n import Translator


def terminal_command(command: Sequence[str], *, path: str | None = None) -> list[str] | None:
    for name, flags in (("konsole", ("--separate", "--nofork", "-e")),
                        ("kitty", ("-e",)), ("foot", ("-e",)), ("xterm", ("-e",))):
        if executable := shutil.which(name, path=path):
            return [executable, *flags, *command]
    return None


def _private_parent(path: Path) -> None:
    info = path.parent.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("Installation result requires an owner-only directory")


PROGRESS_PHASES = frozenset(('starting', 'checking', 'confirmation', 'repository', 'community', 'completed', 'failed', 'cancelled'))


def publish_progress(path: Path, phase: str) -> None:
    """Value-free private progress, independent of the child's actual result."""
    _private_parent(path)
    if phase not in PROGRESS_PHASES:
        raise ValueError('Invalid installation phase')
    previous = read_progress(path)
    now = time.monotonic()
    started = previous['started'] if previous else now
    payload = dict(phase=phase, started=started, updated=now)
    fd, temporary = tempfile.mkstemp(prefix='.progress-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(payload, stream)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        # Timings contain only fixed phase identifiers and elapsed seconds.
        journal = path.with_name('timings.jsonl')
        descriptor = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1:
                raise ValueError('Unsafe timing journal')
            stream.write(json.dumps(dict(phase=phase, elapsed_seconds=round(now-started, 3)))+'\n')
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def read_progress(path: Path) -> dict | None:
    _private_parent(path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, 'r') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 1024 or info.st_nlink != 1:
            raise ValueError('Unsafe installation progress')
        item = json.load(stream)
    if (not isinstance(item, dict) or set(item) != {'phase','started','updated'}
            or not isinstance(item['phase'], str) or item['phase'] not in PROGRESS_PHASES
            or any(type(item[k]) not in (int,float) or not math.isfinite(item[k]) or item[k] < 0 for k in ('started','updated'))
            or item['updated'] < item['started']):
        raise ValueError('Invalid installation progress')
    return item


def installation_outcome(code: int) -> str:
    if code == 0:
        return "success"
    if code in (129, 130, 143, -1, -2, -15):
        return "cancelled"
    return "failed"


def publish_result(path: Path, code: int) -> dict:
    _private_parent(path)
    outcome = installation_outcome(code)
    result = {"outcome": outcome, "code": code}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(result, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return result


def read_result(path: Path) -> dict | None:
    _private_parent(path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "r", encoding="utf-8") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > 1024:
            raise ValueError("Unsafe installation result")
        try:
            result = json.load(stream)
        except json.JSONDecodeError:
            return None  # Writer has not completed the tiny result yet.
    code = result.get("code")
    expected = installation_outcome(code) if type(code) is int else None
    if type(code) is not int or result.get("outcome") != expected:
        raise ValueError("Invalid installation result")
    return result


def run_installation(path: Path, command: Sequence[str], language: str, *,
                     runner=subprocess.run, input_function=input, output=print) -> int:
    _private_parent(path)
    t = Translator(language)
    progress_path = path.with_name("progress.json")
    publish_progress(progress_path, "starting")
    try:
        completed = runner(list(command), check=False)
        code = completed.returncode
    except (EOFError, KeyboardInterrupt):
        code = 130
    except OSError:
        code = 127
    result = publish_result(path, code)
    publish_progress(progress_path, "completed" if result["outcome"] == "success" else result["outcome"])
    if result["outcome"] == "success":
        output(t("Host installation completed."))
    elif result["outcome"] == "cancelled":
        output(t("Host installation was cancelled."))
    else:
        output(t("Host package installation failed or was cancelled (exit {code}). Review the package-manager output above before retrying.", code=code))
        try:
            input_function(t("Press Enter to close this terminal."))
        except (EOFError, KeyboardInterrupt):
            pass
    return code if code >= 0 else 128 - code


@dataclass
class TerminalInstallation:
    process: subprocess.Popen
    result_path: Path
    directory: tempfile.TemporaryDirectory

    @classmethod
    def start(cls, command: Sequence[str], config: Path, state_root: Path, language: str):
        state_root.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix="host-install-", dir=state_root)
        result_path = Path(directory.name) / "result.json"
        argv = terminal_command([*command, "--config", str(config), "host-install",
                                 "--result", str(result_path), "--language", language])
        if argv is None:
            directory.cleanup()
            raise FileNotFoundError("No supported terminal")
        try:
            process = subprocess.Popen(argv, start_new_session=True)
        except OSError:
            directory.cleanup()
            raise
        return cls(process, result_path, directory)

    def progress(self) -> dict | None:
        return read_progress(self.result_path.with_name("progress.json"))

    def result(self) -> dict | None:
        result = read_result(self.result_path)
        if result is not None:
            return result
        if self.process.poll() is not None:
            return {"outcome": "unknown", "code": self.process.returncode}
        return None

    def reap(self) -> None:
        self.process.wait()
        try:
            events = []
            journal = self.result_path.with_name("timings.jsonl")
            if journal.is_file() and not journal.is_symlink() and journal.stat().st_size < 16384:
                for line in journal.read_text().splitlines():
                    event = json.loads(line)
                    if (set(event) != {"phase", "elapsed_seconds"} or not isinstance(event["phase"], str)
                            or event["phase"] not in PROGRESS_PHASES
                            or type(event["elapsed_seconds"]) not in (int, float)
                            or not math.isfinite(event["elapsed_seconds"]) or event["elapsed_seconds"] < 0):
                        raise ValueError("Invalid timing event")
                    events.append(event)
            result = self.result()
            if events:
                target = self.result_path.parent.parent / (self.result_path.parent.name + "-timings.json")
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "w") as stream:
                    json.dump(dict(format=1, events=events, result=result), stream)
        except (OSError, ValueError):
            pass  # Timing archival cannot change the child's actual outcome.
        finally:
            self.directory.cleanup()

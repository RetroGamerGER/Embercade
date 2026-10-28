"""Read-only driver detection and explicit Polkit-mediated compatibility changes."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
import os
import subprocess
import tempfile

from . import xpadneo_helper


def status() -> dict:
    result = xpadneo_helper.inspect()
    if result["can_enable"] and not all(os.access(path, os.X_OK) for path in
            ("/usr/bin/pkexec", "/usr/bin/python3", "/usr/bin/bluetoothctl")):
        result.update(can_enable=False, code="unavailable")
    return result


@contextmanager
def _staged_helper():
    # Root cannot normally read an AppImage's user FUSE mount. Copy only this
    # standalone stdlib helper, never the application or user configuration.
    # A fixed local parent also prevents TMPDIR from selecting another FUSE
    # mount. The private directory survives for the whole authorized call.
    source = Path(__file__).resolve().with_name("xpadneo_helper.py")
    contents = source.read_bytes()
    with tempfile.TemporaryDirectory(prefix="embercade-xpadneo-", dir="/tmp") as directory:
        os.chmod(directory, 0o700)
        path = Path(directory) / "xpadneo_helper.py"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(contents)
        yield path


def apply(operation: str, *, runner=subprocess.run) -> dict:
    """Caller must obtain the user's explicit confirmation before calling."""
    result = dict(ok=False, code="invalid_request", changed=False, pending_reconnect=[])
    if operation not in ("enable", "undo"):
        return result
    before = status()
    # Keep only session values needed by the existing authentication agent;
    # never inherit loader/Python overrides into the privileged command.
    env = dict(xpadneo_helper.CLEAN_ENV)
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "XAUTHORITY"):
        if key in os.environ:
            env[key] = os.environ[key]
    started = False
    try:
        with _staged_helper() as helper:
            command = ["/usr/bin/pkexec", "/usr/bin/python3", "-I", "-B", str(helper), operation]
            started = True
            completed = runner(command, env=env, cwd="/", stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, check=False)
        if completed.returncode == 126:
            result["code"] = "authorization_cancelled"
        elif completed.returncode == 127:
            result["code"] = "authorization_failed"
        else:
            parsed = json.loads(completed.stdout)
            if (not isinstance(parsed, dict) or type(parsed.get("ok")) is not bool
                    or type(parsed.get("changed")) is not bool or not isinstance(parsed.get("code"), str)
                    or not isinstance(parsed.get("pending_reconnect"), list)
                    or (parsed["ok"] and completed.returncode != 0)):
                raise ValueError("Invalid helper result")
            result = parsed
    except FileNotFoundError:
        result["code"] = "unavailable"
    except (OSError, ValueError, subprocess.TimeoutExpired):
        result["code"] = "outcome_unknown" if started else "unavailable"
    after = status()
    result["status"] = after
    # Authentication errors do not imply rollback; refresh actual ownership
    # after a lost process/result rather than falsely reporting no change.
    if before.get("managed") != after.get("managed") or before.get("shift_disabled") != after.get("shift_disabled"):
        result["changed"] = True
    return result

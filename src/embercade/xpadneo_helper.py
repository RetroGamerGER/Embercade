"""Narrow, standalone privileged xpadneo transaction; no application imports.

CLI accepts only enable/undo. Paths/UID/transport injection are Python-only test
seams. Never change the global parameter while a controller remains bound:
xpadneo can otherwise strand its synthetic mouse's pressed buttons.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import fcntl
import hashlib
import json
import os
import re
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time


CONFIG = b"# Managed by Embercade controller compatibility.\noptions hid_xpadneo disable_shift_mode=1\n"
CONFIG_HASH = hashlib.sha256(CONFIG).hexdigest()
CLEAN_ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"}
MAC = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\Z")
HID = re.compile(r"[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}\.[0-9A-Fa-f]+\Z")
MAX_CONTROLLERS = 8


class Refused(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Device:
    name: str
    address: str
    node: Path


class Host:
    """Fixed production targets, with an explicit synthetic filesystem test seam."""

    def __init__(self, root: Path = Path("/"), *, owner_uid: int = 0,
                 runner=subprocess.run, sleep=time.sleep, clock=time.monotonic):
        self.root = root
        self.owner_uid = owner_uid
        self.runner, self.sleep, self.clock = runner, sleep, clock
        self.parameter = root / "sys/module/hid_xpadneo/parameters/disable_shift_mode"
        self.driver = root / "sys/bus/hid/drivers/xpadneo"
        self.config = root / "etc/modprobe.d/90-embercade-controller-compat.conf"
        self.receipt = root / "var/lib/embercade/controller-compat/xpadneo.json"
        self.lock = root / "run/embercade-xpadneo.lock"

    def _parents(self, path: Path, *, create=False):
        # A privileged write must never traverse a user-controlled parent.
        relative = path.parent.relative_to(self.root)
        current = self.root
        for part in ("", *relative.parts):
            current /= part
            try:
                info = current.lstat()
            except FileNotFoundError:
                if not create:
                    raise
                current.mkdir(mode=0o755)
                info = current.lstat()
            if (not stat.S_ISDIR(info.st_mode) or info.st_uid != self.owner_uid
                    or info.st_mode & 0o022):
                raise Refused("ownership_conflict")

    def secure_read(self, path: Path) -> bytes | None:
        try:
            self._parents(path)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        except OSError as error:
            raise Refused("ownership_conflict") from error
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner_uid
                    or info.st_mode & 0o022 or info.st_size > 16384 or info.st_nlink != 1):
                raise Refused("ownership_conflict")
            return stream.read(16385)

    def atomic_write(self, path: Path, data: bytes):
        self._parents(path, create=True)
        self.secure_read(path)  # Existing foreign/symlink files are never replaced.
        fd, temporary = tempfile.mkstemp(prefix=".embercade-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o644)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            self.sync_parent(path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def sync_parent(path):
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def ownership(self):
        config = self.secure_read(self.config)
        raw = self.secure_read(self.receipt)
        if raw is None:
            if config is not None:
                raise Refused("ownership_conflict")
            return None
        try:
            receipt = json.loads(raw)
            valid = (set(receipt) == {"version", "previous_shift_disabled", "config_sha256", "state"}
                     and receipt["version"] == 1
                     and type(receipt["previous_shift_disabled"]) is bool
                     and receipt["config_sha256"] == CONFIG_HASH
                     and receipt["state"] in ("pending", "enabled"))
        except (ValueError, TypeError):
            valid = False
        if not valid or config not in (None, CONFIG):
            raise Refused("ownership_conflict")
        return receipt

    def external_options(self):
        # Conservatively include shadowed declarations: foreign policy must not
        # be adopted or edited. The module name's '-' and '_' are equivalent.
        seen = set()
        for directory in ("etc/modprobe.d", "run/modprobe.d", "usr/local/lib/modprobe.d",
                          "usr/lib/modprobe.d", "lib/modprobe.d"):
            for path in (self.root / directory).glob("*.conf"):
                real = path.resolve()
                if real in seen or path == self.config:
                    continue
                seen.add(real)
                content = path.read_text().replace("\\\n", " ")
                for line in content.splitlines():
                    words = shlex.split(line, comments=True)
                    if (len(words) >= 3 and words[0] == "options"
                            and words[1].replace("-", "_") == "hid_xpadneo"
                            and any(word.split("=", 1)[0] == "disable_shift_mode" for word in words[2:])):
                        return True
        return False

    def parameter_value(self):
        try:
            fd = os.open(self.parameter, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError as error:
            code = "unsupported_parameter" if self.parameter.parent.parent.exists() else "driver_not_loaded"
            raise Refused(code) from error
        with os.fdopen(fd, "r") as stream:
            info = os.fstat(stream.fileno())
            value = stream.read(16).strip().lower()
        if value not in ("y", "n", "1", "0"):
            raise Refused("unsupported_parameter")
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner_uid
                or not info.st_mode & stat.S_IWUSR):
            raise Refused("permission_unavailable")
        if os.statvfs(self.parameter).f_flag & os.ST_RDONLY:
            raise Refused("permission_unavailable")
        return value in ("y", "1")

    def set_parameter(self, disabled):
        self.parameter_value()
        # Both enable and undo can spend time persisting their recovery
        # receipt. Recheck immediately before touching the module-global flag.
        if self.devices():
            raise Refused("devices_still_connected")
        fd = os.open(self.parameter, os.O_WRONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "w") as stream:
            stream.write("Y" if disabled else "N")
        if self.parameter_value() is not disabled:
            raise Refused("operation_failed")

    def devices(self):
        result = []
        if not self.driver.exists():
            return result
        for link in sorted(self.driver.iterdir()):
            if not HID.fullmatch(link.name):
                continue
            node = link.resolve(strict=True)
            if not node.is_relative_to(self.root / "sys/devices"):
                raise Refused("unsupported_device")
            values = dict(line.split("=", 1) for line in (node / "uevent").read_text().splitlines() if "=" in line)
            if values.get("HID_ID", "").split(":")[0] != "0005":
                raise Refused("unsupported_device")
            address = values.get("HID_UNIQ", "")
            if not MAC.fullmatch(address):
                raise Refused("controller_unidentified")
            result.append(Device(values.get("HID_NAME", "xpadneo")[:200], address.upper(), node))
        if len(result) > MAX_CONTROLLERS or len({d.address for d in result}) != len(result):
            raise Refused("too_many_controllers")
        return result

    def bluetooth(self, action, address):
        if action not in ("info", "connect", "disconnect") or not MAC.fullmatch(address):
            raise Refused("invalid_request")
        try:
            return self.runner(["/usr/bin/bluetoothctl", "--timeout", "8", action, address],
                               env=dict(CLEAN_ENV), cwd="/", stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Refused("bluetooth_unavailable") from error

    def wait_absent(self, device):
        deadline = self.clock() + 4
        while True:
            # Do not trust bluetoothctl's process status: wait for removal of
            # both its binding and old input-device tree (held keys live there).
            present = any(d.address == device.address for d in self.devices())
            if not present and not device.node.exists():
                return True
            if self.clock() >= deadline:
                return False
            self.sleep(0.05)

    def mouse_released(self, device):
        inputs = list(device.node.glob("input/input*"))
        if not inputs:
            return None  # The new probe has not registered its input tree yet.
        mice = 0
        for input_dir in inputs:
            rel = input_dir / "capabilities/rel"
            if not rel.exists() or not any(int(word, 16) for word in rel.read_text().split()):
                continue
            mice += 1
            events = list(input_dir.glob("event*"))
            if not events:
                return None
            for event in events:
                if not re.fullmatch(r"event[0-9]+", event.name):
                    return None
                expected = tuple(map(int, (event / "dev").read_text().strip().split(":")))
                fd = os.open(self.root / "dev/input" / event.name,
                             os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
                try:
                    info = os.fstat(fd)
                    if (not stat.S_ISCHR(info.st_mode)
                            or (os.major(info.st_rdev), os.minor(info.st_rdev)) != expected):
                        return False
                    keys = bytearray(96)  # EVIOCGKEY: current state, never a key log.
                    fcntl.ioctl(fd, 0x80604518, keys, True)
                    if any(keys):
                        return False
                finally:
                    os.close(fd)
        if mice:
            return True
        # xpadneo registers the mouse separately after the gamepad. Its
        # absence is proof only when that separate device was disabled.
        disable_mouse = self.parameter.with_name("disable_mouse")
        return True if disable_mouse.exists() and disable_mouse.read_text().strip().lower() in ("y", "1") else None

    def reconnect(self, disconnected):
        pending = []
        for device in disconnected:
            fresh = None
            verified = False
            try:
                try:
                    self.bluetooth("connect", device.address)
                except Refused:
                    pass  # Timed-out transport may still have connected it.
                deadline = self.clock() + 4
                while True:
                    fresh = next((d for d in self.devices() if d.address == device.address), None)
                    released = self.mouse_released(fresh) if fresh else None
                    if released is not None or self.clock() >= deadline:
                        break
                    self.sleep(0.05)
                verified = released is True
            except (Refused, OSError, ValueError):
                verified = False
            if not verified:
                # Failed/unknown key-state reads are as unsafe as pressed
                # buttons. Remove this exact device, even when connect timed
                # out after recreating it. Never leave an unchecked mouse.
                try:
                    self.bluetooth("disconnect", device.address)
                    if fresh is not None:
                        self.wait_absent(fresh)
                except (Refused, OSError, ValueError):
                    pass
                pending.append(device.address)
        return pending

    @contextmanager
    def transaction_lock(self):
        self._parents(self.lock)
        try:
            fd = os.open(self.lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o644)
        except OSError as error:
            raise Refused("ownership_conflict") from error
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner_uid
                    or info.st_mode & 0o022 or info.st_nlink != 1):
                raise Refused("ownership_conflict")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise Refused("busy") from error
            os.fchmod(fd, 0o644)  # Read-only status can inspect the lock, even with umask 077.
            yield
        finally:
            os.close(fd)

    def write_receipt(self, previous, state):
        receipt = dict(version=1, previous_shift_disabled=previous,
                       config_sha256=CONFIG_HASH, state=state)
        self.atomic_write(self.receipt, (json.dumps(receipt, sort_keys=True) + "\n").encode())

    def busy(self):
        try:
            self._parents(self.lock)
            fd = os.open(self.lock, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return False
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner_uid
                    or info.st_mode & 0o022 or info.st_nlink != 1):
                raise Refused("ownership_conflict")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return False
            except BlockingIOError:
                return True
        finally:
            os.close(fd)


def inspect(host=None):
    host = host or Host()
    result = dict(driver_present=host.parameter.parent.parent.exists(), shift_disabled=None,
                  managed=False, can_enable=False, can_undo=False, devices=[], code="unavailable")
    try:
        result["shift_disabled"] = host.parameter_value()
        result["devices"] = [dict(name=d.name, address=d.address) for d in host.devices()]
        receipt = host.ownership()
        if host.busy():
            raise Refused("busy")
        if host.external_options():
            raise Refused("ownership_conflict" if receipt else "external_configuration")
        if receipt:
            if receipt["state"] == "enabled" and (not result["shift_disabled"] or not host.config.exists()):
                raise Refused("ownership_conflict")
            result.update(managed=True, can_undo=True,
                          code="managed_enabled" if receipt["state"] == "enabled" and result["shift_disabled"]
                          and host.config.exists() else "managed_pending")
        elif result["shift_disabled"]:
            result["code"] = "already_enabled"
        else:
            result.update(can_enable=True, code="ready")
    except Refused as error:
        result["code"] = error.code
    except (OSError, ValueError):
        result["code"] = "unavailable"
    return result


def execute(operation, host=None):
    """Run one authorized transaction; every failure reports any durable change."""
    host = host or Host()
    result = dict(ok=False, code="invalid_request", changed=False, pending_reconnect=[])
    if operation not in ("enable", "undo"):
        return result
    disconnected = []
    changed = False
    try:
        with host.transaction_lock():
            try:
                before = host.parameter_value()
                receipt = host.ownership()
                if host.external_options():
                    raise Refused("ownership_conflict" if receipt else "external_configuration")
                if operation == "enable" and (receipt or before):
                    raise Refused("already_enabled" if before else "managed_pending")
                if operation == "undo" and receipt is None:
                    raise Refused("ownership_conflict")
                if (receipt and receipt["state"] == "enabled"
                        and (not before or not host.config.exists())):
                    raise Refused("ownership_conflict")
                devices = host.devices()
                # All pairing checks complete before the first disconnect.
                for device in devices:
                    response = host.bluetooth("info", device.address)
                    if response.returncode or not re.search(r"^\s*Paired: yes\s*$", response.stdout, re.M):
                        raise Refused("controller_not_paired")
                for device in devices:
                    try:
                        host.bluetooth("disconnect", device.address)
                    finally:
                        if host.wait_absent(device):
                            disconnected.append(device)
                    if device not in disconnected:
                        raise Refused("disconnect_failed")
                if host.devices():
                    raise Refused("devices_still_connected")
                if operation == "enable":
                    # Receipt first leaves a recoverable ownership record even
                    # if power/authentication session ends during persistence.
                    # Once a write starts a late fsync/I/O error may mean a
                    # durable change: conservatively report partial progress.
                    changed = True
                    host.write_receipt(before, "pending")
                    host.atomic_write(host.config, CONFIG)
                    if host.devices():
                        raise Refused("devices_still_connected")
                    host.set_parameter(True)
                    host.write_receipt(before, "enabled")
                else:
                    changed = True
                    host.write_receipt(receipt["previous_shift_disabled"], "pending")
                    host.set_parameter(receipt["previous_shift_disabled"])
                    # Revalidate exact ownership before deleting only our files.
                    host.ownership()
                    if host.config.exists():
                        host.config.unlink()
                        host.sync_parent(host.config)
                    host.receipt.unlink()
                    host.sync_parent(host.receipt)
                result.update(ok=True, code="enabled" if operation == "enable" else "undone")
            except Refused as error:
                result["code"] = "partial_failure" if changed else error.code
            except (OSError, ValueError, KeyboardInterrupt):
                result["code"] = "partial_failure" if changed else "operation_failed"
            finally:
                result["changed"] = changed
                result["pending_reconnect"] = host.reconnect(disconnected)
                if result["pending_reconnect"] and result["ok"]:
                    result.update(ok=False, code="reconnect_pending")
    except Refused as error:
        result["code"] = error.code
    except OSError:
        result["code"] = "operation_failed"
    result["status"] = inspect(host)
    return result


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in ("enable", "undo"):
        result = dict(ok=False, code="invalid_request", changed=False, pending_reconnect=[])
    elif os.geteuid() != 0:
        result = dict(ok=False, code="authorization_failed", changed=False, pending_reconnect=[])
    else:
        # A normal termination request still runs the bounded reconnect
        # cleanup. SIGKILL/power loss leave the root-owned pending receipt.
        def interrupted(_signum, _frame):
            raise KeyboardInterrupt
        previous = signal.signal(signal.SIGTERM, interrupted)
        try:
            result = execute(argv[0])
        finally:
            signal.signal(signal.SIGTERM, previous)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

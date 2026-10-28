"""Narrow Linux Wii HID discovery, not a Wiimote input/mapping backend.

Dolphin owns buttons, extensions, IR, motion and reconnect. Inventory/Doctor
never open hardware. Only a Wii launch probes the native status-request report
to distinguish an attached DolphinBar from a connected remote (unused slots
return EPIPE). No Bluetooth pairing, driver rebinding or permission changes.
"""

from dataclasses import dataclass
from pathlib import Path
import os
import re
import stat


@dataclass(frozen=True, slots=True)
class WiiHidDevice:
    path: Path
    transport: str
    name: str
    driver: str
    accessible: bool
    device_number: int

    @property
    def usable(self) -> bool:
        return self.accessible and self.driver == "hid-generic"


def discover_wii_hid(
    sysfs: Path = Path("/sys/class/hidraw"), dev: Path = Path("/dev"),
) -> tuple[WiiHidDevice, ...]:
    """Identify current nodes by kernel HID identity, never a cached node index."""
    devices = []
    for entry in sorted(sysfs.glob("hidraw*")):
        if not re.fullmatch(r"hidraw\d+", entry.name):
            continue
        try:
            metadata = dict(line.split("=", 1) for line in
                            (entry / "device/uevent").read_text().splitlines() if "=" in line)
            bus, vendor, product = (int(value, 16) for value in metadata["HID_ID"].split(":"))
            # Nintendo RVL-CNT-01 / -TR. A mode-4 DolphinBar presents 0306.
            if bus not in {3, 5} or vendor != 0x057E or product not in {0x0306, 0x0330}:
                continue
            path = dev / entry.name
            major, minor = (int(value) for value in (entry / "dev").read_text().split(":"))
            expected = os.makedev(major, minor)
            info = path.lstat()
            if not stat.S_ISCHR(info.st_mode) or info.st_rdev != expected:
                continue
            driver = (entry / "device/driver").resolve(strict=True).name
            devices.append(WiiHidDevice(
                path, "USB" if bus == 3 else "Bluetooth",
                metadata.get("HID_NAME", "Wii Remote"), driver,
                os.access(path, os.R_OK | os.W_OK), expected,
            ))
        except (OSError, KeyError, ValueError):
            # A device can disappear between enumeration and its metadata read.
            continue
    return tuple(devices)


def wii_device_mounts() -> tuple[str, ...]:
    """Expose only recognized, permitted Wii HID nodes, never the whole /dev."""
    return tuple(argument for device in discover_wii_hid() if device.usable
                 for argument in ("--dev-bind", str(device.path), str(device.path)))


def _remote_responds(device: WiiHidDevice) -> bool:
    """Short launch-only liveness probe; leave input interpretation to Dolphin."""
    handle = None
    try:
        handle = os.open(device.path, os.O_RDWR | os.O_NONBLOCK | os.O_NOFOLLOW)
        info = os.fstat(handle)
        if not stat.S_ISCHR(info.st_mode) or info.st_rdev != device.device_number:
            return False
        # Native output report 0x15, rumble off. No configuration/extension write.
        return os.write(handle, bytes((0x15, 0))) == 2
    except OSError:
        return False
    finally:
        if handle is not None:
            os.close(handle)


def real_wiimote_connected() -> bool:
    """Re-enumerate at each launch, including Wiimote reconnect after ES start."""
    return any(_remote_responds(device) for device in discover_wii_hid() if device.usable)


def wii_hardware_summary() -> str:
    """Informational, read-only; receiver presence cannot prove an extension."""
    devices = discover_wii_hid()
    if any(device.usable for device in devices):
        return "Wii receiver/HID available; remote, Nunchuk and IR require a game test"
    if devices:
        return "Wii HID detected; access/driver needs attention (gamepad remains available)"
    return "No Wii Remote HID detected; emulated gamepad remains available"


if __name__ == "__main__":
    # Internal development namespace builder; no user setup/configuration path.
    for argument in wii_device_mounts():
        print(argument)

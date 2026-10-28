"""SDL2 discovery and Batocera-compatible player assignment."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
import ctypes
import ctypes.util
import json
import os
import re
import stat
import xml.etree.ElementTree as ET


SDL_INIT_JOYSTICK = 0x00000200
SDL_INIT_GAMECONTROLLER = 0x00002000
SDL_ALLOW_STEAM_VIRTUAL_GAMEPAD = "SDL_GAMECONTROLLER_ALLOW_STEAM_VIRTUAL_GAMEPAD"
SDL_IGNORE_GAMECONTROLLERS = "SDL_GAMECONTROLLER_IGNORE_DEVICES"
SDL_IGNORE_GAMECONTROLLERS_EXCEPT = "SDL_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT"
SDL_WII_HIDAPI = "SDL_JOYSTICK_HIDAPI_WII"


class ControllerUnavailable(RuntimeError):
    """A connected controller cannot be mapped safely."""


class _SDLJoystickGUID(ctypes.Structure):
    _fields_ = (("data", ctypes.c_uint8 * 16),)


@dataclass(frozen=True, slots=True)
class ControllerDevice:
    index: int
    guid: str
    name: str
    device_path: Path
    buttons: int
    hats: int
    axes: int
    mapping: str
    real_name: str | None = None
    usb_vendor: str | None = None
    usb_product: str | None = None
    kernel_driver: str | None = None

    def player_arguments(self, player: int, *, device_name: str | None = None) -> tuple[str, ...]:
        if not 1 <= player <= 8:
            raise ValueError("Batocera supports player slots 1 through 8")
        prefix = f"-p{player}"
        return (
            f"{prefix}index",
            str(self.index),
            f"{prefix}guid",
            self.guid,
            f"{prefix}name",
            device_name or self.real_name or self.name,
            f"{prefix}devicepath",
            str(self.device_path),
            f"{prefix}nbbuttons",
            str(self.buttons),
            f"{prefix}nbhats",
            str(self.hats),
            f"{prefix}nbaxes",
            str(self.axes),
        )

    def player_one_arguments(self, *, device_name: str | None = None) -> tuple[str, ...]:
        return self.player_arguments(1, device_name=device_name)

    def as_json(self) -> str:
        payload = asdict(self)
        payload["device_path"] = str(self.device_path)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True, slots=True)
class ControllerMappingSource:
    guid: str
    name: str


def _decode(value: bytes | None) -> str | None:
    return value.decode(errors="replace") if value else None


def _load_sdl2() -> ctypes.CDLL:
    library = ctypes.util.find_library("SDL2-2.0") or "libSDL2-2.0.so.0"
    return ctypes.CDLL(library)


def _configure_sdl2(sdl: ctypes.CDLL) -> None:
    sdl.SDL_Init.argtypes = [ctypes.c_uint32]
    sdl.SDL_Init.restype = ctypes.c_int
    sdl.SDL_GetError.restype = ctypes.c_char_p
    sdl.SDL_NumJoysticks.restype = ctypes.c_int
    sdl.SDL_IsGameController.argtypes = [ctypes.c_int]
    sdl.SDL_IsGameController.restype = ctypes.c_int
    sdl.SDL_GameControllerNameForIndex.argtypes = [ctypes.c_int]
    sdl.SDL_GameControllerNameForIndex.restype = ctypes.c_char_p
    sdl.SDL_JoystickPathForIndex.argtypes = [ctypes.c_int]
    sdl.SDL_JoystickPathForIndex.restype = ctypes.c_char_p
    sdl.SDL_JoystickGetDeviceGUID.argtypes = [ctypes.c_int]
    sdl.SDL_JoystickGetDeviceGUID.restype = _SDLJoystickGUID
    sdl.SDL_JoystickGetGUIDString.argtypes = [_SDLJoystickGUID, ctypes.c_char_p, ctypes.c_int]
    sdl.SDL_GameControllerOpen.argtypes = [ctypes.c_int]
    sdl.SDL_GameControllerOpen.restype = ctypes.c_void_p
    sdl.SDL_GameControllerGetJoystick.argtypes = [ctypes.c_void_p]
    sdl.SDL_GameControllerGetJoystick.restype = ctypes.c_void_p
    sdl.SDL_JoystickNumButtons.argtypes = [ctypes.c_void_p]
    sdl.SDL_JoystickNumButtons.restype = ctypes.c_int
    sdl.SDL_JoystickNumHats.argtypes = [ctypes.c_void_p]
    sdl.SDL_JoystickNumHats.restype = ctypes.c_int
    sdl.SDL_JoystickNumAxes.argtypes = [ctypes.c_void_p]
    sdl.SDL_JoystickNumAxes.restype = ctypes.c_int
    sdl.SDL_GameControllerMapping.argtypes = [ctypes.c_void_p]
    sdl.SDL_GameControllerMapping.restype = ctypes.c_void_p
    sdl.SDL_GameControllerClose.argtypes = [ctypes.c_void_p]
    sdl.SDL_free.argtypes = [ctypes.c_void_p]
    sdl.SDL_Quit.argtypes = []


def _usb_identity(device_path: Path) -> tuple[str | None, str | None, str | None]:
    sysfs = Path("/sys/class/input") / device_path.name / "device"
    try:
        current = sysfs.resolve(strict=True)
    except OSError:
        return None, None, None

    vendor: str | None = None
    product: str | None = None
    driver: str | None = None
    for candidate in (current, *current.parents):
        if driver is None:
            driver_link = candidate / "driver"
            if driver_link.is_symlink():
                driver = driver_link.resolve().name
        if vendor is None and (candidate / "idVendor").is_file():
            vendor = (candidate / "idVendor").read_text(encoding="ascii").strip().lower()
        if product is None and (candidate / "idProduct").is_file():
            product = (candidate / "idProduct").read_text(encoding="ascii").strip().lower()
        if vendor is not None and product is not None and driver is not None:
            break
    return vendor, product, driver


def _kernel_input_name(device_path: Path) -> str | None:
    try:
        name = (Path("/sys/class/input") / device_path.name / "device/name").read_text(
            encoding="utf-8"
        ).strip()
    except OSError:
        return None
    return name or None


def _enumerate_sdl_game_controllers() -> tuple[ControllerDevice, ...]:
    sdl = _load_sdl2()
    _configure_sdl2(sdl)
    if sdl.SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER) != 0:
        error = _decode(sdl.SDL_GetError()) or "unknown SDL error"
        raise ControllerUnavailable(f"SDL2 controller initialization failed: {error}")

    controllers: list[ControllerDevice] = []
    try:
        for index in range(sdl.SDL_NumJoysticks()):
            if not sdl.SDL_IsGameController(index):
                continue

            name = _decode(sdl.SDL_GameControllerNameForIndex(index))
            raw_path = _decode(sdl.SDL_JoystickPathForIndex(index))
            if not name or not raw_path:
                continue

            device_path = Path(raw_path)
            try:
                device_mode = device_path.stat().st_mode
            except OSError:
                continue
            if not stat.S_ISCHR(device_mode) or not os.access(device_path, os.R_OK | os.W_OK):
                continue

            guid = sdl.SDL_JoystickGetDeviceGUID(index)
            guid_buffer = ctypes.create_string_buffer(33)
            sdl.SDL_JoystickGetGUIDString(guid, guid_buffer, len(guid_buffer))

            handle = sdl.SDL_GameControllerOpen(index)
            if not handle:
                continue
            try:
                joystick = sdl.SDL_GameControllerGetJoystick(handle)
                mapping_pointer = sdl.SDL_GameControllerMapping(handle)
                mapping = ""
                if mapping_pointer:
                    try:
                        mapping = ctypes.string_at(mapping_pointer).decode(errors="replace")
                    finally:
                        sdl.SDL_free(mapping_pointer)
                vendor, product, driver = _usb_identity(device_path)
                controllers.append(
                    ControllerDevice(
                        index=index,
                        guid=guid_buffer.value.decode("ascii"),
                        name=name,
                        device_path=device_path,
                        buttons=sdl.SDL_JoystickNumButtons(joystick),
                        hats=sdl.SDL_JoystickNumHats(joystick),
                        axes=sdl.SDL_JoystickNumAxes(joystick),
                        mapping=mapping,
                        real_name=_kernel_input_name(device_path),
                        usb_vendor=vendor,
                        usb_product=product,
                        kernel_driver=driver,
                    )
                )
            finally:
                sdl.SDL_GameControllerClose(handle)
    finally:
        sdl.SDL_Quit()
    return tuple(controllers)


def enumerate_sdl_game_controllers() -> tuple[ControllerDevice, ...]:
    """Enumerate physical SDL2 GameController devices without initializing video.

    Steam may opt applications into its virtual gamepad through the inherited
    process environment.  That device has no stable USB/sysfs identity, while
    Embercade's controller handoff and exit bridge deliberately require one.
    Keep the opt-in disabled only for discovery and restore the caller's
    environment immediately afterwards.
    """
    managed_environment = (
        SDL_ALLOW_STEAM_VIRTUAL_GAMEPAD,
        SDL_IGNORE_GAMECONTROLLERS,
        SDL_IGNORE_GAMECONTROLLERS_EXCEPT,
        SDL_WII_HIDAPI,
    )
    previous = {name: os.environ.get(name) for name in managed_environment}
    os.environ[SDL_ALLOW_STEAM_VIRTUAL_GAMEPAD] = "0"
    # Real Wii HID belongs to Dolphin, not SDL's incompatible DolphinBar driver.
    os.environ[SDL_WII_HIDAPI] = "0"
    os.environ.pop(SDL_IGNORE_GAMECONTROLLERS, None)
    os.environ.pop(SDL_IGNORE_GAMECONTROLLERS_EXCEPT, None)
    try:
        return _enumerate_sdl_game_controllers()
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def require_player_one_controller(
    controllers: Iterable[ControllerDevice] | None = None,
) -> ControllerDevice:
    detected = resolve_player_controllers(controllers)
    if not detected:
        raise ControllerUnavailable("No connected SDL2 GameController")
    return detected[0]


def _es_sort_device_path(controller: ControllerDevice) -> str:
    """Match ES InputConfig::getSortDevicePath on Linux, including udev parents."""
    try:
        current = (Path("/sys/class/input") / controller.device_path.name).resolve(strict=True)
    except OSError:
        return str(controller.device_path)
    event_path = str(current)
    for subsystem in ("bluetooth", "usb"):
        for candidate in current.parents:
            link = candidate / "subsystem"
            if link.is_symlink() and link.resolve().name == subsystem:
                return str(candidate)
    return event_path


def _es_player_preferences(settings: Path | None) -> tuple[dict[str, str], ...]:
    if settings is None or not settings.is_file():
        return tuple({field: "" for field in ("PATH", "NAME", "GUID")} for _ in range(8))
    try:
        root = ET.parse(settings).getroot()
    except (OSError, ET.ParseError) as error:
        raise ControllerUnavailable(f"Cannot read ES controller settings: {settings}") from error
    values = {
        item.get("name", ""): item.get("value", "")
        for item in root.findall("./string")
    }
    return tuple({
        field: values.get(f"INPUT P{player}{field}", "")
        for field in ("PATH", "NAME", "GUID")
    } for player in range(1, 9))


def resolve_player_controllers(
    controllers: Iterable[ControllerDevice] | None = None,
    *,
    es_settings: Path | None = None,
) -> tuple[ControllerDevice, ...]:
    """Mirror ES computePlayersConfigs: path, GUID/name, name, then physical path.

    There is no persistent Embercade input database. Slots are resolved anew at
    every launch from the live devices and ES's existing player preferences.
    """
    detected = tuple(enumerate_sdl_game_controllers() if controllers is None else controllers)
    if len(detected) > 8:
        detected = detected[:8]
    if len({device.device_path for device in detected}) != len(detected):
        raise ControllerUnavailable("Duplicate SDL controller device path")
    available = sorted(detected, key=lambda item: (_es_sort_device_path(item), item.index))
    preferences = _es_player_preferences(es_settings)
    assigned: list[ControllerDevice | None] = [None] * 8
    for field in ("PATH", "GUID", "NAME"):
        for slot, preferred in enumerate(preferences):
            if assigned[slot] is not None:
                continue
            value = preferred[field]
            if not value or value == "DEFAULT":
                continue
            for device in available:
                match = (
                    _es_sort_device_path(device) == value if field == "PATH" else
                    device.name == preferred["NAME"] and device.guid == preferred["GUID"]
                    if field == "GUID" else device.name == value
                )
                if match:
                    assigned[slot] = device
                    available.remove(device)
                    break
    for slot in range(8):
        if assigned[slot] is None and available:
            assigned[slot] = available.pop(0)
    return tuple(device for device in assigned if device is not None)


def guid_without_crc(guid: str) -> str:
    if len(guid) != 32:
        raise ControllerUnavailable(f"Invalid SDL2 controller GUID: {guid!r}")
    return f"{guid[:4]}0000{guid[8:]}"


_SDL_TO_ES = {
    "a": "b", "b": "a", "x": "y", "y": "x", "back": "select",
    "guide": "hotkey", "start": "start", "leftshoulder": "pageup",
    "rightshoulder": "pagedown", "lefttrigger": "l2", "righttrigger": "r2",
    "leftstick": "l3", "rightstick": "r3", "dpup": "up", "dpdown": "down",
    "dpleft": "left", "dpright": "right", "leftx": "joystick1left",
    "lefty": "joystick1up", "rightx": "joystick2left", "righty": "joystick2up",
}
_SDL_TO_ES_LEGACY = _SDL_TO_ES | {"a": "a", "b": "b", "x": "x", "y": "y"}


def _mapping_from_sdl(controller: ControllerDevice, *, legacy_faces: bool = False) -> ET.Element:
    """Use SDL's live mapping only when the pinned Batocera DB lacks this GUID.

    This is a device-local translation, not a second collection of controller
    profiles. Unknown SDL binding formats are rejected rather than guessed.
    """
    element = ET.Element("inputConfig", {
        "type": "joystick", "deviceName": controller.name, "deviceGUID": controller.guid,
    })
    bindings: dict[str, str] = {}
    names = _SDL_TO_ES_LEGACY if legacy_faces else _SDL_TO_ES
    for part in controller.mapping.split(",")[2:]:
        key, separator, value = part.partition(":")
        if separator and key in names:
            bindings[key] = value
    if "guide" not in bindings and "back" in bindings:
        bindings["guide"] = bindings["back"]
    for key, name in names.items():
        value = bindings.get(key)
        if value is None:
            continue
        button = re.fullmatch(r"b(\d+)", value)
        hat = re.fullmatch(r"h(\d+)\.(\d+)", value)
        axis = re.fullmatch(r"([+-]?)a(\d+)(~?)", value)
        if button:
            input_type, identifier, direction = "button", button.group(1), "1"
        elif hat:
            input_type, identifier, direction = "hat", hat.group(1), hat.group(2)
        elif axis:
            input_type, identifier = "axis", axis.group(2)
            direction = "-1" if name in {
                "joystick1left", "joystick1up", "joystick2left", "joystick2up"
            } else "1"
            if axis.group(3):
                direction = str(-int(direction))
        else:
            raise ControllerUnavailable(f"Unsupported SDL binding {key}={value!r} for {controller.name}")
        ET.SubElement(element, "input", {
            "name": name, "type": input_type, "id": identifier, "value": direction,
        })
    return element


def _input_signature(mapping: ET.Element) -> tuple[tuple[str, str, str, str], ...]:
    return tuple(sorted((item.get("name", ""), item.get("type", ""),
                         item.get("id", ""), item.get("value", ""))
                        for item in mapping.findall("./input")))


def write_es_input_override(
    controller: ControllerDevice,
    database: Path,
    destination: Path,
) -> ControllerMappingSource:
    """Compatibility wrapper for the original single-controller callers."""
    return write_es_input_overrides((controller,), database, destination)[0]


def write_es_input_overrides(
    controllers: Iterable[ControllerDevice],
    database: Path,
    destination: Path,
) -> tuple[ControllerMappingSource, ...]:
    """Add missing live devices without replacing mappings configured in ES."""
    try:
        source_root = ET.parse(database).getroot()
    except (OSError, ET.ParseError) as error:
        raise ControllerUnavailable(f"Cannot read Batocera controller database: {database}") from error

    candidates = list(source_root.findall("./inputConfig"))
    if destination.is_file():
        try:
            output_root = ET.parse(destination).getroot()
        except (OSError, ET.ParseError) as error:
            raise ControllerUnavailable(f"Cannot read ES controller mapping: {destination}") from error
        if output_root.tag != "inputList":
            raise ControllerUnavailable(f"Invalid ES controller mapping: {destination}")
    else:
        output_root = ET.Element("inputList")
    sources: list[ControllerMappingSource] = []
    seen: set[tuple[str, str]] = set()
    changed = False
    for controller in controllers:
        identity = (controller.guid, controller.name)
        if identity in seen:
            continue  # Identical pads share one ES mapping, but retain distinct player slots.
        seen.add(identity)
        existing = next((item for item in output_root.findall("./inputConfig")
                         if item.get("deviceGUID") == controller.guid
                         and item.get("deviceName") == controller.name), None)
        if existing is not None:
            # An early Embercade fallback translated SDL face names literally.
            # Upgrade only an exact generated signature; any user-edited mapping
            # is left untouched, even if it uses the old face-button layout.
            try:
                legacy = _mapping_from_sdl(controller, legacy_faces=True)
            except ControllerUnavailable:
                legacy = None
            if legacy is not None and _input_signature(existing) == _input_signature(legacy):
                replacement = _mapping_from_sdl(controller)
                position = list(output_root).index(existing)
                output_root.remove(existing)
                output_root.insert(position, replacement)
                changed = True
                sources.append(ControllerMappingSource(controller.guid, "corrected SDL mapping"))
                continue
            sources.append(ControllerMappingSource(controller.guid, "EmulationStation user mapping"))
            continue
        normalized_guid = guid_without_crc(controller.guid)

        def score(element: ET.Element) -> int:
            candidate_guid = element.get("deviceGUID", "")
            candidate_name = element.get("deviceName", "")
            exact_name = candidate_name.casefold() == controller.name.casefold()
            if candidate_guid == controller.guid and exact_name:
                return 0
            if candidate_guid == controller.guid:
                return 1
            if candidate_guid == normalized_guid and exact_name:
                return 2
            if candidate_guid == normalized_guid:
                return 3
            if exact_name:
                return 4
            return 99

        source = min(candidates, key=score, default=None)
        if source is None or score(source) == 99:
            mapping = _mapping_from_sdl(controller)
            mapping_source = ControllerMappingSource(controller.guid, "live SDL mapping")
        else:
            mapping = deepcopy(source)
            mapping_source = ControllerMappingSource(
                guid=source.get("deviceGUID", ""), name=source.get("deviceName", ""),
            )
        mapping.set("deviceGUID", controller.guid)
        mapping.set("deviceName", controller.name)
        required_inputs = {"a", "b", "up", "down", "left", "right", "start", "hotkey"}
        available_inputs = {item.get("name", "") for item in mapping.findall("./input")}
        missing = sorted(required_inputs - available_inputs)
        if missing:
            raise ControllerUnavailable(f"Batocera controller mapping lacks inputs: {', '.join(missing)}")
        output_root.append(mapping)
        changed = True
        sources.append(mapping_source)
    if changed or not destination.is_file():
        tree = ET.ElementTree(output_root)
        ET.indent(tree, space="\t")
        destination.parent.mkdir(parents=True, exist_ok=True)
        tree.write(destination, encoding="utf-8", xml_declaration=True)
    return tuple(sources)

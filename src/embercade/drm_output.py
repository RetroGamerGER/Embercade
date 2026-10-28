"""Read the active scanout size for Gamescope's unscaled external-overlay plane.

Xwayland and wl_output advertise the *game* resolution, not necessarily the TV
resolution. Only GET resources/CRTC calls are used; never DRM master or modesets.
"""

from __future__ import annotations

import ctypes as C
import json
import os
import subprocess
from pathlib import Path
from typing import Mapping


U32 = C.c_uint32
U32P = C.POINTER(U32)


class Resources(C.Structure):
    _fields_ = [
        ('count_fbs', C.c_int), ('fbs', U32P),
        ('count_crtcs', C.c_int), ('crtcs', U32P),
        ('count_connectors', C.c_int), ('connectors', U32P),
        ('count_encoders', C.c_int), ('encoders', U32P),
        ('min_width', U32), ('max_width', U32), ('min_height', U32), ('max_height', U32),
    ]


class Mode(C.Structure):
    _fields_ = [('clock', U32)] + [
        (name, C.c_uint16) for name in (
            'hdisplay', 'hsync_start', 'hsync_end', 'htotal', 'hskew',
            'vdisplay', 'vsync_start', 'vsync_end', 'vtotal', 'vscan',
        )
    ] + [('vrefresh', U32), ('flags', U32), ('type', U32), ('name', C.c_char * 32)]


class Crtc(C.Structure):
    _fields_ = [(name, U32) for name in ('crtc_id', 'buffer_id', 'x', 'y', 'width', 'height')] + [
        ('mode_valid', C.c_int), ('mode', Mode), ('gamma_size', C.c_int),
    ]


def single_output(modes: list[tuple[int, int]]) -> tuple[int, int]:
    if len(modes) != 1 or not all(0 < value <= 16384 for value in modes[0]):
        raise ValueError('Gamescope decoration requires one unambiguous active DRM output')
    return modes[0]


def gamescope_drm_nodes(pid: int, proc: Path = Path('/proc')) -> tuple[Path, ...]:
    process = proc / str(pid)
    # Gamescope renames its main thread to gamescope-wl; comm is not its binary.
    if (process / 'exe').resolve(strict=True).name != 'gamescope':
        raise ValueError('Invalid Gamescope compositor PID')
    environment = dict(part.split('=', 1) for part in (process / 'environ').read_text().split('\0') if '=' in part)
    command = (process / 'cmdline').read_bytes().split(b'\0')
    if environment.get('DISPLAY') or environment.get('WAYLAND_DISPLAY') or b'--force-orientation' in command:
        raise ValueError('Nested/rotated Gamescope output needs a separate verified sizing adapter')
    nodes = set()
    for descriptor in (process / 'fd').iterdir():
        try:
            target = descriptor.resolve(strict=True)
        except OSError:
            continue
        if target.parent == Path('/dev/dri') and target.name.startswith('card') and target.name[4:].isdigit():
            nodes.add(target)
    if not nodes:
        raise ValueError('Gamescope DRM output device is not readable')
    return tuple(sorted(nodes))


def gamescope_device_hint(environment: Mapping[str, str]) -> str:
    # The pinned launcher venv deliberately does not contain desktop Xlib.
    # Use the same host Python as the optional GTK decoration renderer.
    result = subprocess.run(
        ['/usr/bin/python', '-I', '-B', str(Path(__file__).resolve())],
        env=dict(environment), capture_output=True, text=True, timeout=3,
        check=True,
    )
    payload = json.loads(result.stdout)
    return json.dumps(payload)


def _host_device_hint(environment: Mapping[str, str]) -> str:
    """Host-side discovery before Bubblewrap's /proc permission boundary."""
    from Xlib import X, display
    connection = display.Display(environment['DISPLAY'])
    try:
        prop = connection.screen().root.get_full_property(
            connection.intern_atom('GAMESCOPE_PID'), X.AnyPropertyType)
        if prop is None or len(prop.value) != 1:
            raise ValueError('Gamescope compositor identity unavailable')
        pid = int(prop.value[0])
        return json.dumps({'pid': pid, 'nodes': list(map(str, gamescope_drm_nodes(pid)))})
    finally:
        connection.close()


def decoration_drm_nodes(pid: int, environment: Mapping[str, str]) -> tuple[Path, ...]:
    hint = environment.get('EMBERCADE_DECORATION_DRM_DEVICES')
    if hint is None:
        return gamescope_drm_nodes(pid)
    payload = json.loads(hint)
    if payload['pid'] != pid:
        raise ValueError('Gamescope compositor changed since frontend start')
    nodes = tuple(Path(value) for value in payload['nodes'])
    if not nodes or len(nodes) > 8 or any(
        node.parent != Path('/dev/dri') or not node.name.startswith('card')
        or not node.name[4:].isdigit() or not node.is_char_device() for node in nodes
    ):
        raise ValueError('Invalid Gamescope DRM device hint')
    return nodes


def active_output_size(nodes: tuple[Path, ...]) -> tuple[int, int]:
    library = C.CDLL('libdrm.so.2')
    library.drmModeGetResources.argtypes = [C.c_int]
    library.drmModeGetResources.restype = C.POINTER(Resources)
    library.drmModeFreeResources.argtypes = [C.POINTER(Resources)]
    library.drmModeFreeResources.restype = None
    library.drmModeGetCrtc.argtypes = [C.c_int, U32]
    library.drmModeGetCrtc.restype = C.POINTER(Crtc)
    library.drmModeFreeCrtc.argtypes = [C.POINTER(Crtc)]
    library.drmModeFreeCrtc.restype = None
    modes = []
    for node in nodes:
        descriptor = os.open(node, os.O_RDONLY | os.O_CLOEXEC)
        try:
            resources = library.drmModeGetResources(descriptor)
            if not resources:
                raise OSError('DRM GET resources failed')
            try:
                count = resources.contents.count_crtcs
                if not 0 <= count <= 64:
                    raise ValueError('Invalid DRM CRTC count')
                for index in range(count):
                    crtc = library.drmModeGetCrtc(descriptor, resources.contents.crtcs[index])
                    if not crtc:
                        raise OSError('DRM GET CRTC failed')
                    try:
                        if crtc.contents.mode_valid:
                            modes.append((crtc.contents.mode.hdisplay, crtc.contents.mode.vdisplay))
                    finally:
                        library.drmModeFreeCrtc(crtc)
            finally:
                library.drmModeFreeResources(resources)
        finally:
            os.close(descriptor)
    return single_output(modes)


if __name__ == '__main__':
    print(_host_device_hint(os.environ))

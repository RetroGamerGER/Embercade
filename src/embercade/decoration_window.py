"""Disposable GTK renderer. No window is mapped until its emulator owns focus.

KWin and Hyprland use a native, input-transparent layer with compositor focus events.
Gamescope uses its external-overlay plane on the root Xwayland server. It is
not an ordinary application window and never sets STEAM_GAME or input focus.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import socket
import sys
import time

# Only the sibling application package; no dependency on the caller's PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from embercade.standalone_decoration import (
    Decoration, belongs_to_launch, hyprland_request, hyprland_socket_dir,
    safe_margins, visible_on_monitor,
)
from embercade.drm_output import active_output_size, decoration_drm_nodes


class GamescopeWindows:
    """Gamescope 3.16 external-overlay and focus properties (read-only root)."""

    def __init__(self):
        from Xlib import X, display
        self.X = X
        self.connections = {}
        self.root_display = None
        # Discover the root server by its properties, never assume :0/:1.
        for path in sorted(Path('/tmp/.X11-unix').glob('X*')):
            if not path.name[1:].isdigit():
                continue
            name = ':' + path.name[1:]
            try:
                connection = display.Display(name)
                root = connection.screen().root
                if not self.property(connection, root, 'GAMESCOPE_PID'):
                    connection.close()
                    continue
                self.connections[name] = connection
                if self.property(connection, root, 'GAMESCOPE_FOCUSED_WINDOW'):
                    self.root_display = connection
            except Exception:
                continue
        if self.root_display is None:
            raise RuntimeError('Gamescope root focus properties unavailable')
        self.root = self.root_display.screen().root
        compositor = self.property(self.root_display, self.root, 'GAMESCOPE_PID')
        self.drm_nodes = decoration_drm_nodes(int(compositor[0]), os.environ)
        self.output_dimensions = active_output_size(self.drm_nodes)
        self.output_checked_at = time.monotonic()
        # Gamescope has one external-overlay slot. Do not displace MangoApp or
        # any other active external overlay.
        for child in self.root.query_tree().children:
            if (child.get_attributes().map_state == X.IsViewable
                    and self.property(self.root_display, child, 'GAMESCOPE_EXTERNAL_OVERLAY')):
                raise RuntimeError('Gamescope external-overlay plane already occupied')

    def output_size(self):
        if time.monotonic() - self.output_checked_at >= 1:
            self.output_dimensions = active_output_size(self.drm_nodes)
            self.output_checked_at = time.monotonic()
        return self.output_dimensions

    def property(self, connection, window, name):
        prop = window.get_full_property(connection.intern_atom(name), self.X.AnyPropertyType)
        return prop.value if prop is not None else None

    def active(self):
        focus = self.property(self.root_display, self.root, 'GAMESCOPE_FOCUSED_WINDOW')
        server = self.property(self.root_display, self.root, 'GAMESCOPE_FOCUS_DISPLAY')
        if focus is None or server is None:
            return {}
        # Upstream publishes the display string in a 32-bit CARDINAL property.
        name = server.tobytes().split(b'\0', 1)[0].decode('ascii')
        connection = self.connections.get(name)
        if connection is None:
            return {}
        window = connection.create_resource_object('window', int(focus[0]))
        pid = self.property(connection, window, '_NET_WM_PID')
        geometry = window.get_geometry()
        root_geometry = self.root.get_geometry()
        states = self.property(connection, window, '_NET_WM_STATE')
        fullscreen = connection.intern_atom('_NET_WM_STATE_FULLSCREEN')
        # Gamescope places Xwayland clients at (1,1), but composites their
        # fullscreen surface at the output origin. This is not desktop window
        # geometry: normalize only a fullscreen, exact output-sized surface.
        output_sized = (geometry.width, geometry.height) == (root_geometry.width, root_geometry.height)
        # SDL/Xemu can omit EWMH fullscreen in Gamescope. The compositor's
        # focused surface at its origin covering the entire logical output
        # is sufficient here, unlike on a normal desktop compositor.
        output_surface = output_sized and (geometry.x, geometry.y) in ((0, 0), (1, 1))
        is_fullscreen = (states is not None and fullscreen in states) or output_surface
        return {
            'pid': int(pid[0]) if pid is not None else 0,
            'mapped': window.get_attributes().map_state == self.X.IsViewable,
            'hidden': False,
            'fullscreen': 2 if is_fullscreen else 0,
            'at': [0, 0] if is_fullscreen and output_sized else [geometry.x, geometry.y],
            'size': [geometry.width, geometry.height],
            'monitor': (0, 0, root_geometry.width, root_geometry.height),
        }

    def register(self, xid):
        from Xlib import Xatom
        window = self.root_display.create_resource_object('window', xid)
        window.change_property(self.root_display.intern_atom('GAMESCOPE_EXTERNAL_OVERLAY'),
                               Xatom.CARDINAL, 32, [1])
        # Do not request STEAM_INPUT_FOCUS. GTK's input=False and empty shape
        # provide the second independent input-transparency safeguard.
        self.root_display.sync()

    def size_overlay(self, xid, dimensions):
        # Gtk.Window.resize() constrains a toplevel to the logical Xwayland
        # monitor (1080p even on a 4K scanout). External overlays are unscaled:
        # configure their own X surface in physical pixels, like MangoApp.
        window = self.root_display.create_resource_object('window', xid)
        geometry = window.get_geometry()
        width, height = dimensions
        if (geometry.x, geometry.y, geometry.width, geometry.height) != (0, 0, width, height):
            window.configure(x=0, y=0, width=width, height=height)
            self.root_display.sync()


def configure_layer(window, layer):
    """Full output in logical coordinates, including areas reserved by panels."""
    layer.init_for_window(window)
    layer.set_namespace(window, 'embercade-decoration')
    layer.set_layer(window, layer.Layer.OVERLAY)
    layer.set_keyboard_mode(window, layer.KeyboardMode.NONE)
    # Zero respects other surfaces' exclusive zones: on Plasma a top panel
    # otherwise shrinks/offsets the surface even while the game is fullscreen.
    # -1 uses the full output without reserving space or changing the panel.
    layer.set_exclusive_zone(window, -1)
    for edge in (layer.Edge.TOP, layer.Edge.BOTTOM, layer.Edge.LEFT, layer.Edge.RIGHT):
        layer.set_anchor(window, edge, True)
        layer.set_margin(window, edge, 0)


def main() -> int:
    backend, owner_text, executable_text, descriptor = sys.argv[1:]
    owner, executable = int(owner_text), Path(executable_text)
    decoration = Decoration(**{**json.loads(descriptor), 'png': Path(json.loads(descriptor)['png'])})
    gamescope = GamescopeWindows() if backend == 'gamescope' else None
    os.environ['GDK_BACKEND'] = 'x11' if gamescope else 'wayland'
    if gamescope:
        os.environ['DISPLAY'] = gamescope.root_display.get_display_name()
        os.environ['GDK_SCALE'] = '1'  # external overlays are physical output pixels
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
    import cairo

    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    if not gamescope:
        gi.require_version('GtkLayerShell', '0.1')
        from gi.repository import GtkLayerShell
        configure_layer(window, GtkLayerShell)
    window.set_title('Embercade decoration')
    window.set_decorated(False)
    window.set_accept_focus(False)
    window.set_focus_on_map(False)
    window.set_skip_taskbar_hint(True)
    window.set_skip_pager_hint(True)
    window.set_app_paintable(True)
    visual = window.get_screen().get_rgba_visual()
    if visual is None:
        raise RuntimeError('Transparent visual unavailable')
    window.set_visual(visual)
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(decoration.png))
    visible = False
    monitor_key = None

    def passthrough(*_args):
        native = window.get_window()
        if native:
            native.set_accept_focus(False)
            native.set_pass_through(True)
            native.input_shape_combine_region(cairo.Region(), 0, 0)
        return False

    def draw(widget, context):
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.set_source_rgba(0, 0, 0, 0)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        # GDK and KWin report logical Wayland geometry. Cairo/GDK apply the
        # buffer scale; multiplying by physical mode pixels would scale twice.
        # Do not paint a cropped frame during a monitor/scale configure event.
        if not gamescope and (monitor_key is None or (width, height) != monitor_key[2:]):
            return True
        left, right = safe_margins(decoration, width, height)
        context.rectangle(0, 0, left, height)
        context.rectangle(width - right, 0, right, height)
        context.clip()
        scale = min(width / decoration.width, height / decoration.height)
        context.translate((width - decoration.width * scale) / 2,
                          (height - decoration.height * scale) / 2)
        context.scale(scale, scale)
        Gdk.cairo_set_source_pixbuf(context, pixbuf, 0, 0)
        context.paint_with_alpha(decoration.opacity)
        return True

    ipc = hyprland_socket_dir(os.environ) if backend == 'hyprland' else None
    from embercade.kwin_decoration import KWinWindows
    kwin = KWinWindows() if backend == 'kwin' else None

    def tick():
        nonlocal visible, monitor_key
        if os.getppid() != owner:
            window.hide()
            Gtk.main_quit()
            return False
        try:
            active = gamescope.active() if gamescope else kwin.active() if kwin else hyprland_request(ipc, 'j/activewindow')
            owned = belongs_to_launch(int(active.get('pid', 0)), owner, executable)
            matched = None
            if gamescope:
                geometry = active.get('monitor', (0, 0, 0, 0))
                if visible_on_monitor(active, geometry, owned):
                    matched = (0, 0, *gamescope.output_size())
            else:
                display = Gdk.Display.get_default()
                for i in range(display.get_n_monitors()):
                    monitor = display.get_monitor(i)
                    rect = monitor.get_geometry()
                    geometry = (rect.x, rect.y, rect.width, rect.height)
                    if visible_on_monitor(active, geometry, owned):
                        matched = geometry
                        if monitor_key != geometry:
                            window.hide()
                            visible = False
                            GtkLayerShell.set_monitor(window, monitor)
                            window.resize(1, 1)  # discard any old monitor's size request
                        break
            if matched is not None and max(safe_margins(decoration, *matched[2:])) > 0:
                if not visible or monitor_key != matched:
                    monitor_key = matched
                    window.show_all()
                    GLib.idle_add(passthrough)
                    print(f'Standalone decoration visible: {backend}, emulator PID {active["pid"]}', flush=True)
                if gamescope:
                    gamescope.size_overlay(GdkX11.X11Window.get_xid(window.get_window()), matched[2:])
                visible, monitor_key = True, matched
            else:
                if visible:
                    window.hide()
                    print('Standalone decoration hidden: emulator not focused/fullscreen', flush=True)
                visible = False
        except Exception as error:
            window.hide()
            visible = False
            # Lost compositor connection must not leave a display-global layer.
            print(f'Standalone decoration stopped: {error}', file=sys.stderr, flush=True)
            Gtk.main_quit()
            return False
        return True

    def stop(*_args):
        window.hide()
        Gtk.main_quit()
        return False

    window.connect('draw', draw)
    window.connect('map-event', passthrough)
    window.realize()
    passthrough()
    if gamescope:
        gi.require_version('GdkX11', '3.0')
        from gi.repository import GdkX11
        gamescope.register(GdkX11.X11Window.get_xid(window.get_window()))
    elif ipc is not None:
        events = socket.socket(socket.AF_UNIX)
        events.connect(str(ipc / '.socket2.sock'))

        def event_ready(source, condition):
            if condition & (GLib.IO_HUP | GLib.IO_ERR):
                return stop()
            if not source.recv(65536):
                return stop()
            return tick()

        GLib.io_add_watch(events, GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR, event_ready)
    GLib.io_add_watch(sys.stdin.fileno(), GLib.IO_HUP | GLib.IO_ERR, stop)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, stop)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, stop)
    GLib.timeout_add(250, tick)
    try:
        if tick():
            Gtk.main()
    finally:
        window.destroy()
        if kwin:
            kwin.close()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'Standalone decoration unavailable; game unchanged: {error}', file=sys.stderr)
        raise SystemExit(1)

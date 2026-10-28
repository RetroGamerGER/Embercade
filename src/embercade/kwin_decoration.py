"""Disposable KWin 6 observer for the existing input-transparent bezel renderer.

No window rules, geometry changes or persistent KWin settings. The script only
reports the active window's PID/fullscreen/geometry to this helper's unique bus
connection. KWin unloads this uniquely named observer when the helper disappears.
"""
from __future__ import annotations

import json
import os
import time
import uuid


INTERFACE = "org.embercade.Decoration"
OBJECT = "/org/embercade/Decoration"


def observer_script(bus_name: str, plugin: str) -> bytes:
    return ("const target = " + json.dumps(bus_name) + ";\nconst plugin = " + json.dumps(plugin) + ";\n" + r'''
const timer = new QTimer();
timer.interval = 150;
function update() {
    callDBus("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
             "NameHasOwner", target, function(alive) {
        if (!alive) {
            timer.stop();
            callDBus("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "unloadScript", plugin);
            return;
        }
        const w = workspace.activeWindow;
        let data = {};
        if (w) {
            const g = w.frameGeometry;
            data = {pid: w.pid, mapped: true, hidden: w.minimized,
                    fullscreen: w.fullScreen ? 2 : 0,
                    at: [Math.round(g.x), Math.round(g.y)],
                    size: [Math.round(g.width), Math.round(g.height)]};
        }
        callDBus(target, "/org/embercade/Decoration", "org.embercade.Decoration",
                 "Update", JSON.stringify(data));
    });
}
timer.timeout.connect(update);
timer.start();
update();
''').encode()


class KWinWindows:
    def __init__(self):
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.connection = Gio.DBusConnection.new_for_address_sync(
            Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None),
            Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
            None, None)
        self.proxy = Gio.DBusProxy.new_sync(self.connection, Gio.DBusProxyFlags.NONE, None,
            "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", None)
        self.sender = self.proxy.get_name_owner()
        if not self.sender:
            raise RuntimeError("KWin scripting service unavailable")
        self.plugin = "embercade-decoration-" + uuid.uuid4().hex
        self.snapshot, self.received = {}, time.monotonic()
        self.fd = os.memfd_create("embercade-kwin-observer", os.MFD_CLOEXEC)
        self.registration = None
        self.loaded = False
        try:
            info = Gio.DBusNodeInfo.new_for_xml(
                '<node><interface name="org.embercade.Decoration"><method name="Update">'
                '<arg type="s" direction="in" name="snapshot"/></method></interface></node>')
            self.registration = self.connection.register_object(OBJECT, info.interfaces[0], self._update, None, None)
            os.write(self.fd, observer_script(self.connection.get_unique_name(), self.plugin))
            path = f"/proc/{os.getpid()}/fd/{self.fd}"
            reply = self.proxy.call_sync("loadScript", GLib.Variant("(ss)", (path, self.plugin)),
                                         Gio.DBusCallFlags.NONE, 5000, None)
            identifier = reply.unpack()[0]
            if identifier < 0:
                raise RuntimeError("KWin could not load decoration observer")
            self.loaded = True
            self.connection.call_sync("org.kde.KWin", f"/Scripting/Script{identifier}",
                "org.kde.kwin.Script", "run", None, None, Gio.DBusCallFlags.NONE, 5000, None)
        except Exception:
            self.close()
            raise

    def _update(self, connection, sender, path, interface, method, parameters, invocation):
        if sender != self.sender:
            invocation.return_dbus_error("org.embercade.Decoration.UntrustedSender", "KWin required")
            return
        text = parameters.unpack()[0]
        try:
            if len(text) > 4096:
                raise ValueError("oversized KWin snapshot")
            snapshot = json.loads(text)
            if not isinstance(snapshot, dict):
                raise ValueError("invalid KWin snapshot")
            self.snapshot, self.received = snapshot, time.monotonic()
            invocation.return_value(None)
        except ValueError:
            invocation.return_dbus_error("org.embercade.Decoration.InvalidSnapshot", "Invalid snapshot")

    def active(self):
        if time.monotonic() - self.received > 2:
            raise RuntimeError("KWin observer disconnected")
        return self.snapshot

    def close(self):
        if self.loaded:
            try:
                self.proxy.call_sync("unloadScript", self.GLib.Variant("(s)", (self.plugin,)),
                                     self.Gio.DBusCallFlags.NONE, 1000, None)
            except Exception:
                pass  # Closing the private connection triggers the script's watchdog.
            self.loaded = False
        if self.registration:
            self.connection.unregister_object(self.registration)
            self.registration = None
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        if not self.connection.is_closed():
            self.connection.close_sync(None)

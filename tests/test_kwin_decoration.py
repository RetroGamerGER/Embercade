"""Opt-in KWin service/renderer checks using an owned GTK fixture, no emulator/ROM."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import subprocess
import sys
import time
import unittest

from embercade.kwin_decoration import KWinWindows
from embercade.standalone_decoration import Decoration


@unittest.skipUnless(os.environ.get("EMBERCADE_TEST_KWIN") == "1", "opt-in actual KWin session required")
class KWinDecorationTests(unittest.TestCase):
    def test_native_layer_allocation_matches_full_logical_monitor(self):
        script = '''import gi
gi.require_version("Gtk", "3.0"); gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib
from embercade.decoration_window import configure_layer
import cairo, json
w=Gtk.Window(); configure_layer(w, GtkLayerShell)
w.set_decorated(False); w.set_accept_focus(False)
monitor=Gdk.Display.get_default().get_monitor(0)
GtkLayerShell.set_monitor(w, monitor)
def check():
    r=monitor.get_geometry()
    print(json.dumps(dict(expected=[r.width,r.height], actual=[w.get_allocated_width(),w.get_allocated_height()], scale=w.get_scale_factor(), zone=GtkLayerShell.get_exclusive_zone(w))),flush=True)
    w.destroy(); Gtk.main_quit(); return False
w.show_all(); w.get_window().input_shape_combine_region(cairo.Region(),0,0)
GLib.timeout_add(300,check); Gtk.main()
'''
        result = subprocess.run([sys.executable, '-c', script],
            env=dict(os.environ, GDK_BACKEND='wayland'), text=True, capture_output=True, timeout=5, check=True)
        result = json.loads(result.stdout)
        self.assertEqual(result['actual'], result['expected'])
        self.assertEqual(result['zone'], -1)

    def test_observer_unloads_after_normal_close_and_helper_crash(self):
        observer = KWinWindows()
        plugin = observer.plugin
        observer.close()
        def loaded(name):
            result = subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.isScriptLoaded", name], text=True, capture_output=True, check=True)
            return result.stdout.strip() == "true"
        self.assertFalse(loaded(plugin))
        # Abrupt exit deliberately bypasses close: the unique-connection watchdog cleans up.
        script = "from embercade.kwin_decoration import KWinWindows; import os; o=KWinWindows(); print(o.plugin,flush=True); os._exit(0)"
        child = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True, check=True)
        time.sleep(0.4)
        self.assertFalse(loaded(child.stdout.strip()))

    def test_owned_fullscreen_fixture_shows_hides_and_reaps_same_renderer(self):
        project = Path(__file__).resolve().parents[1]
        image = project / ".work/ui/share/batocera/datainit/decorations/consoles/systems/xbox.png"
        if not image.is_file(): self.skipTest("prepared existing bezel resource required")
        fixture = '''import gi
from gi.repository import GLib
import sys
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
window=Gtk.Window(title="Embercade automated bezel check")
window.fullscreen(); window.show_all(); window.present()
GLib.timeout_add(1100, lambda: (window.unfullscreen(), False)[1])
GLib.timeout_add(1800, lambda: (Gtk.main_quit(), False)[1])
Gtk.main(); window.destroy()
'''
        child = subprocess.Popen([sys.executable, "-c", fixture], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        descriptor = Decoration(image, 1920, 1080, 250, 14, 265, 16, 1, 4/3).to_json()
        renderer = subprocess.Popen([sys.executable, "-B", str(project / "src/embercade/decoration_window.py"),
            "kwin", str(os.getpid()), str(Path(sys.executable).resolve()), descriptor],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            child.communicate(timeout=6)
            time.sleep(0.3)
            renderer.stdin.close(); renderer.stdin = None
            output, errors = renderer.communicate(timeout=4)
            self.assertEqual(renderer.returncode, 0, errors)
            self.assertIn("Standalone decoration visible: kwin", output, errors)
            self.assertIn("Standalone decoration hidden", output, errors)
        finally:
            for process in (child, renderer):
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)

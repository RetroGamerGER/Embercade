"""Controller-friendly GTK first-run window; no setup rules live in this UI.

GTK is loaded only in this system-Python process.  The pinned launcher runtime
remains independent of host Python packages and all writes go through its CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import argparse
import json
import ctypes
import ctypes.util
import os
import subprocess
import sys
import threading
import time

from embercade.first_run import (
    FirstRunError, action_arguments, branding_icon, launcher_command,
    read_state, run_action, setup_arguments, validate_asset_sources,
)
from embercade.version import FRONTEND_PRODUCT_LABEL
from embercade.i18n import Translator, system_language
from embercade.paths import EmbercadePaths
from embercade.host_install import TerminalInstallation
from embercade.host_requirements import PACMAN_UNAVAILABLE, Pacman, read_os_release
from embercade.file_chooser import create_chooser, native_portal_available, validate_selection
from embercade import controller_compat
from embercade.controller_test import ChordTest


STEPS = (("Language", {"language"}), ("Welcome", {"welcome"}),
         ("Games and BIOS", {"paths", "sources", "shadps4", "assets"}),
         ("Host software", {"host"}), ("Controller & Hotkeys", {"controller"}),
         ("Xbox", {"xbox"}), ("PlayStation 3", {"ps3"}),
         ("Desktop integration", {"desktop"}), ("System checks", {"checks"}),
         ("Complete", {"finish"}))


class Gamepad:
    """Poll the first SDL game controller, including Steam's virtual gamepad."""

    BUTTONS = {"a": 0, "b": 1, "x": 2, "y": 3, "back": 4, "guide": 5, "start": 6,
               "leftstick": 7, "rightstick": 8, "leftshoulder": 9, "rightshoulder": 10,
               "up": 11, "down": 12, "left": 13, "right": 14, "misc": 15,
               "paddle1": 16, "paddle2": 17, "paddle3": 18, "paddle4": 19, "touchpad": 20}

    def __init__(self) -> None:
        self.lib = None
        self.controller = None
        self.previous: set[str] = set()
        self.name = ""
        self.generation = 0
        name = ctypes.util.find_library("SDL2")
        if not name:
            return
        try:
            lib = ctypes.CDLL(name)
            lib.SDL_InitSubSystem.argtypes = [ctypes.c_uint32]
            lib.SDL_InitSubSystem.restype = ctypes.c_int
            lib.SDL_NumJoysticks.restype = ctypes.c_int
            lib.SDL_IsGameController.argtypes = [ctypes.c_int]
            lib.SDL_IsGameController.restype = ctypes.c_int
            lib.SDL_GameControllerOpen.argtypes = [ctypes.c_int]
            lib.SDL_GameControllerOpen.restype = ctypes.c_void_p
            lib.SDL_GameControllerGetAttached.argtypes = [ctypes.c_void_p]
            lib.SDL_GameControllerGetAttached.restype = ctypes.c_int
            lib.SDL_GameControllerGetButton.argtypes = [ctypes.c_void_p, ctypes.c_int]
            lib.SDL_GameControllerGetButton.restype = ctypes.c_uint8
            lib.SDL_GameControllerClose.argtypes = [ctypes.c_void_p]
            lib.SDL_GameControllerName.argtypes = [ctypes.c_void_p]
            lib.SDL_GameControllerName.restype = ctypes.c_char_p
            lib.SDL_GameControllerUpdate.restype = None
            lib.SDL_PumpEvents.restype = None
            if lib.SDL_InitSubSystem(0x2000) == 0:
                self.lib = lib
        except (AttributeError, OSError):
            self.lib = None

    def poll(self) -> set[str]:
        if self.lib is None:
            return set()
        self.lib.SDL_PumpEvents()
        if self.controller and not self.lib.SDL_GameControllerGetAttached(self.controller):
            self.lib.SDL_GameControllerClose(self.controller)
            self.controller = None
            self.previous.clear()
            self.name = ""
        if not self.controller:
            for index in range(self.lib.SDL_NumJoysticks()):
                if self.lib.SDL_IsGameController(index):
                    self.controller = self.lib.SDL_GameControllerOpen(index)
                    if self.controller:
                        self.generation = getattr(self, "generation", 0) + 1
                        if hasattr(self.lib, "SDL_GameControllerName"):
                            self.name = (self.lib.SDL_GameControllerName(self.controller) or b"").decode(errors="replace")
                        break
        if hasattr(self.lib, "SDL_GameControllerUpdate"):
            self.lib.SDL_GameControllerUpdate()
        pressed = {
            label for label, code in self.BUTTONS.items()
            if self.controller and self.lib.SDL_GameControllerGetButton(self.controller, code)
        }
        new = pressed - self.previous
        self.previous = pressed
        return new

    def close(self) -> None:
        if self.controller and self.lib:
            self.lib.SDL_GameControllerClose(self.controller)
            self.controller = None


def _gtk():
    # GTK caches its portal preference on first use; scope it to this wizard.
    os.environ.setdefault("GTK_USE_PORTAL", "1")
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gtk
    if not Gtk.init_check()[0]:
        raise FirstRunError("No usable graphical session was found")
    Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
    return GLib, Gtk


class Wizard:
    def __init__(self, config_path: Path, GLib, Gtk) -> None:
        self.GLib, self.Gtk = GLib, Gtk
        self.state = read_state(config_path)
        self.command = launcher_command()
        self.roms, self.bios = self.state.roms, self.state.bios
        self.hotkey = self.state.exit_hotkey
        self.cores, self.providers = "", ""
        self.shadps4 = ""
        self.ppsspp, self.xemu = self.state.ppsspp_assets, ""
        self.language = self.state.language or system_language()
        self._language_return: str | None = None
        self.page = "language"
        self.busy = False
        self.folder_dialog = None
        self.message_dialog = None
        self.launch_after_close = False
        self.closed = False
        self.menu_enabled, self.shortcut_enabled = True, False
        self.local_image_enabled, self.steam_enabled = True, False
        self.eeprom_source = self.pup_source = ""
        self.xbox_choices = {"language": "keep", "region": "keep", "video": "keep"}
        self.last_report = None
        self.controller_report = None
        self.controller_test_result = None
        self.controller_test = None
        self.controller_test_dialog = None
        self._controller_release_pending = False
        self.pad = Gamepad()
        self.icon = branding_icon()
        self.window = Gtk.Window(title=f"{FRONTEND_PRODUCT_LABEL} – {self._t('Setup')}")
        self.window.set_default_size(1120, 660)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        if self.icon:
            self.window.set_icon_from_file(str(self.icon))
        if os.environ.get("GAMESCOPE_WAYLAND_DISPLAY"):
            self.window.fullscreen()
        self.window.connect("delete-event", lambda *_: self.busy)
        self.window.connect("destroy", self._quit)
        self.window.connect("key-press-event", self._key)
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            window { background: #121013; color: #f6efe8; }
            label { color: #f6efe8; font-size: 16px; }
            label.title { font-size: 29px; font-weight: bold; }
            label.muted { color: #b7a9a6; font-size: 14px; }
            .brand-header { background: #1f181b; border-bottom: 2px solid #ed6237; padding: 16px 24px; }
            .steps { background: #191519; padding: 22px 14px; border-right: 1px solid #38272b; }
            .step { padding: 10px 8px; color: #a89b9a; }
            .step.active { background: #49241f; border-radius: 8px; color: #ffab66; font-weight: bold; }
            .footer { padding: 12px 24px; background: #1f181b; border-top: 1px solid #38272b; }
            button { min-height: 34px; padding: 6px 16px; font-size: 16px; border-radius: 8px;
                     background-image: none; background-color: #302329; color: #f6efe8; border: 1px solid #57382f; }
            button:hover { background-color: #513026; }
            button.primary { background-color: #b84324; border-color: #ef7c43; font-weight: bold; }
            entry, combobox { min-height: 36px; font-size: 16px; border-radius: 6px; }
            entry { background: #211b20; color: #f6efe8; border: 1px solid #624135; }
            button:focus, entry:focus, combobox:focus { outline: 3px solid #ffa259; outline-offset: 1px; }
            progressbar trough { min-height: 5px; background: #38272b; }
            progressbar progress { background: #f2713c; }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            self.window.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.header_box.get_style_context().add_class("brand-header")
        shell.pack_start(self.header_box, False, False, 0)
        self.step_progress = Gtk.ProgressBar()
        shell.pack_start(self.step_progress, False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.steps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.steps_box.set_size_request(190, -1)
        self.steps_box.get_style_context().add_class("steps")
        body.pack_start(self.steps_box, False, False, 0)
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.root.set_border_width(24)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.root)
        body.pack_start(scroll, True, True, 0)
        shell.pack_start(body, True, True, 0)
        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        footer.get_style_context().add_class("footer")
        self.navigation = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        footer.pack_start(self.navigation, False, False, 0)
        self.controls_hint = Gtk.Label()
        self.controls_hint.set_xalign(0)
        self.controls_hint.get_style_context().add_class("muted")
        footer.pack_start(self.controls_hint, False, False, 0)
        shell.pack_start(footer, False, False, 0)
        self.window.add(shell)
        self.focusables = []
        self._render()
        self.pad_source = GLib.timeout_add(70, self._poll_gamepad)

    def _t(self, message: str, **fields) -> str:
        return Translator(getattr(self, "language", "en"))(message, **fields)

    def _badge(self, category):
        symbol = {"Ready": "●", "Optional": "○", "Setup required": "!", "Error": "×"}[category]
        return symbol + " " + self._t(category)

    def _quit(self, *_args) -> None:
        self.closed = True
        self.GLib.source_remove(self.pad_source)
        self.pad.close()
        self.Gtk.main_quit()

    def _key(self, _widget, event) -> bool:
        from gi.repository import Gdk
        if self.message_dialog is not None or self.folder_dialog is not None:
            return False
        if event.keyval == Gdk.KEY_Escape and not self.busy:
            self._back()
            return True
        if event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down) and not self.busy:
            self._focus_step(-1 if event.keyval == Gdk.KEY_Up else 1)
            return True
        return False

    def _poll_gamepad(self) -> bool:
        buttons = self.pad.poll()
        tested = getattr(self, "controller_test_result", None)
        if tested is not None and (not self.pad.controller or tested != (self.hotkey, self.pad.generation)):
            self.controller_test_result = None
            summary = getattr(self, "controller_test_summary", None)
            if self.page == "controller" and summary is not None:
                summary.set_text(self._t("The exit combination has not been tested in this session."))
        if getattr(self, "controller_test", None) is not None:
            self._poll_controller_test(buttons)
            return True
        if getattr(self, "_controller_release_pending", False):
            if not self.pad.previous:
                self._controller_release_pending = False
            return True
        for button in buttons:
            # A nested modal loop may consume a whole new sequence of input.
            # Never replay the remaining edges from the tick that opened it.
            if getattr(self, "_controller_release_pending", False):
                break
            if self.message_dialog is not None:
                self._dialog_input(button)
            elif self.folder_dialog is not None:
                self._folder_input(button)
            elif not self.busy:
                if button in {"up", "down"}:
                    self._focus_step(-1 if button == "up" else 1)
                elif button in {"left", "b"}:
                    self._back()
                elif button in {"a", "start", "right"}:
                    focused = self.window.get_focus()
                    if isinstance(focused, self.Gtk.CheckButton):
                        focused.set_active(not focused.get_active())
                    elif isinstance(focused, self.Gtk.Button):
                        # A modal opened inside this timeout would suspend
                        # its own non-recursive GLib input source. Activate
                        # on the next idle turn so polling continues inside
                        # Gtk.Dialog.run, and discard the rest of this batch.
                        if not getattr(self, "_gamepad_activation_pending", False):
                            self._gamepad_activation_pending = True
                            self.GLib.idle_add(self._activate_gamepad_button, focused)
                        return True
                    elif isinstance(focused, self.Gtk.ComboBox):
                        focused.popup()
                    elif self.focusables:
                        self.focusables[0].grab_focus()
        return True

    def _activate_gamepad_button(self, button) -> bool:
        self._gamepad_activation_pending = False
        if (not getattr(self, "closed", False) and not self.busy
                and self.message_dialog is None and self.folder_dialog is None
                and button.get_toplevel() == self.window):
            button.clicked()
        return False

    def _focus_step(self, direction: int) -> None:
        if not self.focusables:
            return
        focused = self.window.get_focus()
        try:
            index = self.focusables.index(focused)
        except ValueError:
            index = -1 if direction > 0 else 0
        self.focusables[(index + direction) % len(self.focusables)].grab_focus()

    def _clear(self) -> None:
        for child in self.root.get_children():
            self.root.remove(child)
        for container in (self.header_box, self.steps_box, self.navigation):
            for child in container.get_children(): container.remove(child)
        self.focusables = []

    def _label(self, text: str, *, title: bool = False, muted: bool = False):
        label = self.Gtk.Label(label=self._t(text))
        label.set_xalign(0)
        label.set_line_wrap(True)
        label.set_max_width_chars(85)
        label.set_selectable(False)
        if title:
            label.get_style_context().add_class("title")
        if muted:
            label.get_style_context().add_class("muted")
        self.root.pack_start(label, False, False, 0)
        return label

    def _header(self, page_title: str) -> None:
        header = self.Gtk.Box(orientation=self.Gtk.Orientation.HORIZONTAL, spacing=18)
        if self.icon:
            from gi.repository import GdkPixbuf
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(self.icon), 78, 78, True)
            header.pack_start(self.Gtk.Image.new_from_pixbuf(pixbuf), False, False, 0)
        heading = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=3)
        name = self.Gtk.Label(label=FRONTEND_PRODUCT_LABEL)
        name.set_xalign(0)
        name.get_style_context().add_class("title")
        heading.pack_start(name, False, False, 0)
        subtitle = self.Gtk.Label(label=self._t("Setup  ·  {page}", page=self._t(page_title)))
        subtitle.set_xalign(0)
        subtitle.get_style_context().add_class("muted")
        heading.pack_start(subtitle, False, False, 0)
        header.pack_start(heading, True, True, 0)
        self.header_box.pack_start(header, False, False, 0)

    def _button(self, text: str, action: Callable, *, focus: bool = True):
        button = self.Gtk.Button(label=self._t(text))
        button.connect("clicked", lambda _button: action())
        navigation = text in {"Continue", "Back", "Language", "Finish", "Save language and continue", "Start Embercade"}
        (self.navigation if navigation else self.root).pack_start(button, False, False, 0)
        if text in {"Continue", "Save language and continue", "Start Embercade", "Begin setup", "Save and check setup"}:
            button.get_style_context().add_class("primary")
        if focus:
            self.focusables.append(button)
        return button

    def _field(self, title: str, value: str, *, directory: bool = False, file: bool = False):
        self._label(title)
        row = self.Gtk.Box(orientation=self.Gtk.Orientation.HORIZONTAL, spacing=12)
        entry = self.Gtk.Entry()
        entry.set_text(value)
        entry.set_hexpand(True)
        row.pack_start(entry, True, True, 0)
        self.focusables.append(entry)
        if directory or file:
            browse = self.Gtk.Button(label=self._t("Choose file" if file else "Choose folder"))
            browse.connect("clicked", lambda _button: self._choose_directory(entry, file=file))
            row.pack_start(browse, False, False, 0)
            self.focusables.append(browse)
        self.root.pack_start(row, False, False, 0)
        return entry

    def _go(self, page: str) -> None:
        self.page = page
        if page == "controller":
            self.controller_report = controller_compat.status()
        self._render()

    def _back(self) -> None:
        self._remember_visible_fields()
        pages = {"paths": "welcome", "controller": "host", "sources": "paths",
                 "shadps4": "sources", "assets": "shadps4", "host": "assets", "xbox": "controller", "ps3": "xbox", "desktop": "ps3", "checks": "desktop", "finish": "checks"}
        if self.page == "language":
            if self._language_return is not None:
                self._go(self._language_return)
            else:
                self.window.destroy()
        elif self.page in pages:
            self._go(pages[self.page])
        elif self.page == "welcome":
            self.window.destroy()

    def _remember_visible_fields(self) -> None:
        """Going back must not discard unsubmitted text on the current page."""
        if self.page == "paths":
            self.roms, self.bios = self.rom_entry.get_text().strip(), self.bios_entry.get_text().strip()
        elif self.page == "sources":
            self.cores, self.providers = self.core_entry.get_text().strip(), self.provider_entry.get_text().strip()
        elif self.page == "assets":
            self.ppsspp, self.xemu = self.ppsspp_entry.get_text().strip(), self.xemu_entry.get_text().strip()
        elif self.page == "shadps4":
            self.shadps4 = self.shadps4_entry.get_text().strip()
        elif self.page == "xbox":
            self.eeprom_source = self.eeprom_entry.get_text().strip()
            self.xbox_choices = {key: combo.get_active_id() for key, combo in self.xbox_combos.items()}
        elif self.page == "ps3":
            self.pup_source = self.pup_entry.get_text().strip()
        elif self.page == "desktop":
            for key, toggle in self.desktop_toggles.items(): setattr(self, key, toggle.get_active())

    def _render(self) -> None:
        self._clear()
        pages = {"welcome": 'Welcome', "paths": 'Your games and system files',
                 "controller": 'Controller & Hotkeys', "sources": 'More emulator files',
                 "assets": 'Additional system files',
                 "shadps4": 'PlayStation 4 (optional)',
                 "checks": 'Check and set up', "finish": 'Complete'}
        pages.update(language="Language", host="Host software", xbox="Xbox console settings",
                     ps3="PlayStation 3 firmware", desktop="Desktop integration")
        groups = STEPS
        current = next(index for index, (_, group) in enumerate(groups) if self.page in group)
        self.step_progress.set_fraction(current / (len(groups)-1))
        for index, (title, _) in enumerate(groups):
            label = self.Gtk.Label(label=f"{index+1:02d}  {self._t(title)}")
            label.set_xalign(0)
            label.set_line_wrap(True)
            label.get_style_context().add_class("step")
            if index == current: label.get_style_context().add_class("active")
            self.steps_box.pack_start(label, False, False, 0)
        self.window.set_title(f"{FRONTEND_PRODUCT_LABEL} – {self._t('Setup')}")
        self._header(pages[self.page])
        if self.page == "language":
            self._label("Choose your language before setup. You can change it at any time.")
            self.language_choice = self.Gtk.ComboBoxText()
            for code, name in (("de", "Deutsch"), ("en", "English")):
                self.language_choice.append(code, name)
            self.language_choice.set_active_id(self.language)
            self.language_choice.connect("changed", self._preview_language)
            self.root.pack_start(self.language_choice, False, False, 0)
            self.focusables.append(self.language_choice)
            self._button("Save language and continue", self._save_language)
            self._button("Back", self._back)
        elif self.page == "welcome":
            self._label('Automatic host-software installation supports Arch-based distributions with pacman, including Arch Linux, CachyOS, Garuda and EndeavourOS.')
            self._label('Show Embercade where your files are. Embercade will take care of the rest.')
            self._label('Your games, BIOS files and source files will be preserved.', muted=True)
            if self.state.configured:
                self._label('Your existing setup was found. You can check it now or change its settings.')
                self._button('Check existing setup', lambda: self._go("checks"))
                self._button('Change settings', lambda: self._go("paths"))
                self._button('Controller & Hotkeys', lambda: self._go("controller"))
            else:
                self._button('Begin setup', lambda: self._go("paths"))
            self._button('Later', self.window.destroy)
        elif self.page == "paths":
            self._label('Choose your existing folders. Embercade only reads them; nothing is copied.', muted=True)
            self.rom_entry = self._field('Games folder', self.roms, directory=True)
            self.bios_entry = self._field('BIOS folder', self.bios, directory=True)
            self._button('Continue', self._save_paths)
            self._button('Back', self._back)
        elif self.page == "controller":
            self._render_controller()
        elif self.page == "sources":
            self._label('Previously imported files stay in Embercade. You do not need to select their original folders again.', muted=True)
            if self.state.managed_cores:
                self._label(self._t("RetroArch cores already imported: {count}", count=self.state.managed_cores), muted=True)
            if self.state.managed_xenia:
                self._label('The Xenia AppImage has already been imported and configured.', muted=True)
            self.core_entry = self._field('Import another folder of RetroArch cores (optional)', self.cores, directory=True)
            self.provider_entry = self._field('Import another folder of emulator AppImages (optional)', self.providers, directory=True)
            self._button('Continue', self._save_sources)
            self._button('Back', self._back)
        elif self.page == "shadps4":
            self._label('If you already have shadPS4, select your AppImage. Embercade imports its own copy and preserves your source.')
            self._label('Nothing is downloaded. You can skip this and use the rest of Embercade.', muted=True)
            if self.state.shadps4:
                self._label(self._t("Already configured: {path}", path=self.state.shadps4), muted=True)
            self.shadps4_entry = self._field('shadPS4 AppImage (optional)', self.shadps4, file=True)
            self._button('Continue', self._save_shadps4)
            self._button('Back', self._back)
        elif self.page == "assets":
            self._label('PSP and Xbox system files are optional for Embercade setup. Leave these fields empty or skip this step if you do not need these systems yet.')
            self._label('Choose a complete system-specific folder. The general BIOS folder is not used automatically.', muted=True)
            self._label('PSP games require the complete official PPSSPP assets folder with ppge_atlas.zim, lang/ and flash0/. PSP games cannot start reliably without it.', muted=True)
            self.ppsspp_entry = self._field('PSP assets (optional for setup; required for PSP games)', self.ppsspp, directory=True)
            self._label('Xemu requires Complex_4627.bin, mcpx_1.0.bin and xbox_hdd.qcow2. Embercade creates working copies. Xemu generates its EEPROM on first start; an existing Embercade EEPROM is preserved.', muted=True)
            if self.state.xemu_prepared:
                self._label('Xemu system files are already prepared. You do not need to select their source folder again.', muted=True)
            self.xemu_entry = self._field('Xbox system files (if not set up yet)', self.xemu, directory=True)
            self._label("Xbox language and region are stored in Embercade's own EEPROM. You can import or edit it on the Xbox page.", muted=True)
            self._button('Continue', self._save_assets)
            self._button('Skip for now', self._skip_assets)
            self._button('Back', self._back)
        elif self.page == "host":
            self._label('Automatic host-software installation supports Arch-based distributions with pacman, including Arch Linux, CachyOS, Garuda and EndeavourOS.')
            self._label("Components for your current collection appear first. Other emulators are optional.", muted=True)
            if self.last_report:
                for item in self.last_report["requirements"]:
                    category = "Ready" if item["available"] else "Setup required" if item.get("required", True) else "Optional"
                    self._label(self._t("{component}: {status}", component=self._t(item["label"]), status=self._badge(category)))
            self._button("Refresh checks", lambda: self._run("host-status", self._refresh_page))
            self._button("Install optional host software", self._bootstrap)
            self._button("Show details", lambda: self._run("host-status", self._host_status))
            self._button("Continue", lambda: self._go("controller"))
            self._button("Back", self._back)
        elif self.page == "xbox":
            self._label("Choose a default EEPROM, import your own, or edit console settings. Settings edits preserve console identity and HDD keys.")
            self._label("Embercade uses its own Xbox EEPROM. Your normal Xemu profile stays separate. Close Xemu before changing these settings.", muted=True)
            info = (self.last_report or {}).get("eeprom", {"missing": True})
            self._label(self._t("Xbox EEPROM: {status}", status=self._badge("Error" if info.get("invalid") else "Setup required" if info.get("missing") else "Ready")))
            if "language" in info:
                self._label(self._t("Console settings: language {language}, region {region}, video {video}",
                    language=self._t({1:"English",3:"German"}.get(info["language"], "Other")),
                    region=self._t({1:"North America",2:"Japan",4:"Europe"}.get(info["region"], "Other")),
                    video={0x00800300:"PAL",0x00400100:"NTSC-M",0x00400200:"NTSC-J"}.get(info["video"], self._t("Other"))), muted=True)
            self._button("Create default EEPROM with Xemu", lambda: self._xbox_action("xbox-init"))
            self.eeprom_entry = self._field("Your EEPROM file (optional)", self.eeprom_source, file=True)
            self._button("Import EEPROM", lambda: self._xbox_action("xbox-import"))
            self.xbox_combos = {}
            for key, label, choices in (
                ("language", "Console language", (("keep","Keep current"),("en","English"),("de","German"))),
                ("region", "Game region", (("keep","Keep current"),("north-america","North America"),("japan","Japan"),("europe","Europe"))),
                ("video", "Video standard", (("keep","Keep current"),("pal","PAL"),("ntsc-m","NTSC-M"),("ntsc-j","NTSC-J")))):
                self._label(label)
                combo = self.Gtk.ComboBoxText()
                for code, title in choices: combo.append(code, self._t(title))
                combo.set_active_id(self.xbox_choices[key])
                self.root.pack_start(combo, False, False, 0)
                self.focusables.append(combo)
                self.xbox_combos[key] = combo
            self._button("Save console settings", lambda: self._xbox_action("xbox-edit"))
            self._button("Continue", self._continue_xbox)
            self._button("Back", self._back)
        elif self.page == "ps3":
            self._label("Install official PS3 firmware in Embercade's isolated RPCS3 profile. You can also select your own PUP or skip this step.")
            ready = (self.last_report or {}).get("rpcs3", False)
            self._label(self._t("PS3 firmware: {status}", status=self._badge("Ready" if ready else "Setup required")))
            self._label("Existing firmware is preserved. Close RPCS3 when its installation has finished to return here.", muted=True)
            self._button("Download and install official firmware", lambda: self._ps3_action(download=True))
            self.pup_entry = self._field("PS3UPDAT.PUP file", self.pup_source, file=True)
            self._button("Install selected firmware", self._ps3_action)
            if (self.last_report or {}).get("rpcs3_source") and not ready:
                self._button("Import existing installed firmware", self._firmware)
            self._button("Continue", self._continue_ps3)
            self._button("Back", self._back)
        elif self.page == "desktop":
            self._label("Keep Embercade easy to find in Games, on your desktop or in Steam.")
            self._label("A local AppImage copy keeps your launcher working when the original drive is disconnected. Existing classic installations keep their verified launcher.", muted=True)
            self.desktop_toggles = {}
            for key, label in (("menu_enabled", "Application menu · Games (recommended)"),
                               ("local_image_enabled", "Keep a stable local AppImage copy"),
                               ("shortcut_enabled", "Desktop shortcut"), ("steam_enabled", "Add to Steam with Embercade artwork")):
                toggle = self.Gtk.CheckButton(label=self._t(label))
                toggle.set_active(getattr(self, key))
                self.root.pack_start(toggle, False, False, 0)
                self.focusables.append(toggle)
                self.desktop_toggles[key] = toggle
            self._button("Continue", self._save_desktop)
            self._button("Back", self._back)
        elif self.page == "checks":
            self._label(self._t("Games: {path}", path=self.roms or self._t("not selected")))
            self._label(self._t("BIOS: {path}", path=self.bios or self._t("not selected")))
            self._label(self._t("PSP assets: {path}", path=self.ppsspp or self._t("not selected")), muted=True)
            self._label(self._t("Xemu system files: {path}", path=self.xemu or self._t("not selected")), muted=True)
            self._label(self._t("shadPS4: {path}", path=self.shadps4 or self.state.shadps4 or self._t("not selected")), muted=True)
            self._label('The check also examines firmware, emulators, controllers and additional system files.', muted=True)
            if self.last_report:
                self._label(self._status_text(self.last_report), muted=True)
            self._button('Save and check setup', self._apply)
            self._button('Show missing host software', lambda: self._run("host-status", self._host_status))
            self._button('Install optional host software', self._bootstrap)
            self._button('Back', self._back)
        elif self.page == "finish":
            self._label(self.finish_text)
            self._label('PS3, Xbox and PSP firmware and additional files were included in the check.', muted=True)
            self._label(self.doctor_output, muted=True)
            self._button('Check again', lambda: self._run("doctor", self._doctor_done))
            self._button("Controller & Hotkeys", lambda: self._go("controller"))
            self._button("Xbox console settings", lambda: self._go("xbox"))
            self._button("PlayStation 3 firmware", lambda: self._go("ps3"))
            self._button("Desktop integration", lambda: self._go("desktop"))
            self._button('Install optional host software', self._bootstrap)
            self._button('Add to Steam (optional)', self._steam)
            if self.state.configured:
                self._button('Start Embercade', self._launch)
            self._button('Finish', self.window.destroy)
            self._button('Change settings', lambda: self._go("paths"))
        if self.page != "language":
            self._button("Language", self._language_settings)
        self.controls_hint.set_text(self._t('Controller: ↑/↓ select  ·  A confirm  ·  B back  ·  X use folder'))
        self.window.show_all()
        if self.focusables:
            self.focusables[0].grab_focus()

    def _save_paths(self) -> None:
        self.roms, self.bios = self.rom_entry.get_text().strip(), self.bios_entry.get_text().strip()
        self._go("sources")

    def _choose_hotkey(self, value: str) -> None:
        if value not in {"back-start", "guide-start"}:
            return
        self.hotkey = value
        self.controller_test_result = None
        self._render()

    def _render_controller(self) -> None:
        report = self.controller_report or controller_compat.status()
        self.controller_report = report
        self._label("Choose your exit combination, check compatibility and try it here.")
        self.hotkey_choice = self.Gtk.ComboBoxText()
        self.hotkey_choice.append("back-start", self._t("Back/Select + Start"))
        self.hotkey_choice.append("guide-start", self._t("Guide + Start"))
        self.hotkey_choice.set_active_id(self.hotkey)
        self.hotkey_choice.connect("changed", lambda choice: self._choose_hotkey(choice.get_active_id()))
        self.root.pack_start(self.hotkey_choice, False, False, 0)
        self.focusables.append(self.hotkey_choice)
        devices = report.get("devices", [])
        for device in devices:
            self._label(self._t("{name} · Bluetooth · xpadneo", name=device["name"]), muted=True)
        if report.get("driver_present"):
            if report.get("shift_disabled"):
                self._label("The xpadneo Guide special mode is disabled.")
            elif self.hotkey == "guide-start":
                self._label("Possible hotkey conflict: xpadneo can intercept the Guide button.")
                self._label("Use Back/Select + Start, or approve the driver adjustment below.", muted=True)
            else:
                self._label("Back/Select + Start does not require changing xpadneo.", muted=True)
        else:
            self._label("No active xpadneo driver was found. Other controllers keep their existing setup.", muted=True)
        if report.get("code") in {"ownership_conflict", "external_configuration"}:
            self._label("Existing system settings are preserved. Only changes recorded by this installer can be undone here.", muted=True)
        elif report.get("code") in {"unsupported_parameter", "permission_unavailable", "unavailable"}:
            self._label("Automatic driver adjustment is unavailable. You can use Back/Select + Start.", muted=True)
        elif report.get("code") == "managed_pending":
            self._label("A previous driver adjustment is incomplete. Undo it before trying again.", muted=True)
        if report.get("can_enable") and self.hotkey == "guide-start":
            self._button("Enable Guide + Start compatibility…", lambda: self._adjust_controller("enable"))
        if report.get("can_undo"):
            self._button("Undo Embercade's driver adjustment…", lambda: self._adjust_controller("undo"))
        self._button("Refresh controller check", lambda: self._go("controller"))
        tested = self.controller_test_result == (self.hotkey, self.pad.generation)
        self.controller_test_summary = self._label("Exit combination detected and released." if tested else "The exit combination has not been tested in this session.", muted=True)
        self._button("Test exit combination", self._start_controller_test)
        self._label("The test checks the controller shown in the dialog. Then test exiting a real game from Player 1.", muted=True)
        self._button("Continue", self._save_controller)
        self._button("Back", self._back)

    def _save_controller(self) -> None:
        if self.controller_test_result != (self.hotkey, self.pad.generation):
            if not self._question("Continue without a live test?", "The selected exit combination has not been verified. You can test it now or return to Controller & Hotkeys later. Continue anyway?"):
                return
        self._run_arguments(("--config", str(self.state.config_path), "installer", "controller",
                             "--exit-hotkey", self.hotkey), self._controller_saved)

    def _controller_saved(self, result) -> None:
        if result.returncode:
            self._message("Controller settings need attention", "The exit combination could not be saved. Your existing setup is preserved. Check file permissions and try again.", error=True)
            return
        self.state = read_state(self.state.config_path)
        self._go("xbox")

    def _adjust_controller(self, operation: str) -> None:
        if self.busy or self.message_dialog is not None:
            return
        body = ("This changes a system-wide xpadneo setting for all controllers using that driver. Guide-based mouse and profile switching will be disabled. All affected connected controllers will briefly disconnect before the change, clearing virtual mouse buttons, and then reconnect. Close running games first. Administrator authentication is required. You can undo Embercade's change here. Continue?"
                if operation == "enable" else
                "Restore the xpadneo setting saved before Embercade's adjustment? All affected connected controllers will briefly disconnect first, then reconnect. Guide-based special functions may return and Guide + Start may stop working. Administrator authentication is required. Close running games first.")
        if not self._question("Adjust the controller driver?", self._t(body)):
            return
        self.controller_test_result = None
        self.busy = True
        self.window.set_sensitive(False)
        self.progress = self._label("Adjusting the driver and reconnecting controllers…")
        self.progress.show()
        self.GLib.timeout_add(120, self._pulse)
        def worker():
            try:
                result = controller_compat.apply(operation)
            except Exception:
                result = {"ok": False, "code": "outcome_unknown"}
            self.GLib.idle_add(self._controller_adjusted, result)
        threading.Thread(target=worker, daemon=True).start()

    def _controller_adjusted(self, result) -> bool:
        self.busy = False
        self.window.set_sensitive(True)
        self._controller_release_pending = True
        self._go("controller")
        code = result.get("code")
        if result.get("ok"):
            body = ("The previous driver setting was restored. Test your selected exit combination again."
                    if code == "undone" else
                    "The driver adjustment is active. Controllers were safely reconnected. Test the exit combination now.")
        elif code == "authorization_cancelled":
            body = "Administrator authentication was cancelled. No driver change was requested."
        elif code in {"authorization_failed", "permission_unavailable"}:
            body = "Administrator authentication is unavailable or failed. Use Back/Select + Start or retry in your desktop session."
        elif code == "reconnect_pending" or result.get("pending_reconnect"):
            body = "A controller has not reconnected. Switch affected controllers off and on, refresh the driver check and run the live test. Do not assume the driver adjustment or exit shortcut is ready yet."
        elif code in {"ownership_conflict", "external_configuration"}:
            body = "An existing or modified system setting cannot be safely replaced or undone by Embercade. It has been preserved. Use Back/Select + Start or review the driver configuration."
        elif code in {"disconnect_failed", "devices_still_connected", "controller_unidentified", "unsupported_device", "controller_not_paired", "too_many_controllers"}:
            body = "The affected controllers could not all be safely identified or disconnected. The driver was not changed. Reconnect them and retry, or use Back/Select + Start."
        elif code in {"driver_not_loaded", "unsupported_parameter", "bluetooth_unavailable", "unavailable"}:
            body = "The required driver or Bluetooth service is unavailable. Refresh the check after connecting your controller, or use Back/Select + Start."
        elif code == "busy":
            body = "Another driver adjustment is running. Wait for it to finish, then refresh the check."
        else:
            body = "The driver adjustment did not finish reliably. Refresh the check, switch affected controllers off and on, and retry. Back/Select + Start remains available."
        self._message("Controller & Hotkeys", self._t(body), error=not result.get("ok") and code != "authorization_cancelled")
        return False

    def _start_controller_test(self) -> None:
        if self.busy or self.message_dialog is not None:
            return
        self.controller_test_result = None
        self.controller_test = ChordTest(self.hotkey)
        self.controller_test_started = time.monotonic()
        dialog = self.Gtk.MessageDialog(transient_for=self.window, modal=True,
            destroy_with_parent=True, message_type=self.Gtk.MessageType.INFO,
            buttons=self.Gtk.ButtonsType.NONE, text=self._t("Test exit combination"))
        dialog.add_button(self._t("Cancel"), self.Gtk.ResponseType.CANCEL)
        dialog.format_secondary_text(self._t("Release all controller buttons to begin."))
        self._size_message(dialog)
        self.controller_test_dialog = dialog
        try:
            result = self._run_dialog(dialog, self.Gtk.ResponseType.CANCEL)
            if result == self.Gtk.ResponseType.OK:
                self.controller_test_result = (self.hotkey, self.pad.generation)
        finally:
            self.controller_test = None
            self.controller_test_dialog = None
            self._controller_release_pending = True
        if getattr(self, "closed", False):
            return
        self._render()
        if result == self.Gtk.ResponseType.REJECT:
            self._message("Exit combination not detected", "No sustained combination was detected within 30 seconds. Check the driver status, reconnect the controller and retry, or choose Back/Select + Start.")

    def _poll_controller_test(self, buttons) -> None:
        dialog = self.controller_test_dialog
        if "b" in buttons:
            dialog.response(self.Gtk.ResponseType.CANCEL)
            return
        now = time.monotonic()
        phase = self.controller_test.update(self.pad.previous, bool(self.pad.controller), now,
                                            self.pad.generation)
        if phase == "passed":
            dialog.response(self.Gtk.ResponseType.OK)
            return
        if now - self.controller_test_started >= 30:
            dialog.response(self.Gtk.ResponseType.REJECT)
            return
        shortcut = "Guide + Start" if self.hotkey == "guide-start" else "Back/Select + Start"
        text = {"release": "Release all controller buttons to begin.",
                "press": "Hold {shortcut} together for a moment.",
                "hold": "Keep holding both buttons…",
                "release_after": "Combination detected. Release all buttons to finish."}[phase]
        body = (self._t("Controller: {name}", name=self.pad.name) if self.pad.controller
                else self._t("No controller connected. Switch it on to continue."))
        body += "\n\n" + self._t(text, shortcut=shortcut)
        dialog.format_secondary_text(body)

    def _save_sources(self) -> None:
        self.cores = self.core_entry.get_text().strip()
        self.providers = self.provider_entry.get_text().strip()
        self._go("shadps4")

    def _save_shadps4(self) -> None:
        self.shadps4 = self.shadps4_entry.get_text().strip()
        if self.shadps4:
            from embercade.imports import ImportError as ManagedImportError, inspect_provider
            try:
                inspect_provider(Path(self.shadps4), provider="shadps4")
            except ManagedImportError as error:
                self._message("Check shadPS4 file", self._t("The selected AppImage could not be verified as shadPS4. Choose a readable, supported shadPS4 AppImage."), error=True)
                return
        self._go("assets")

    def _save_assets(self) -> None:
        ppsspp = self.ppsspp_entry.get_text().strip()
        xemu = self.xemu_entry.get_text().strip()
        try:
            validate_asset_sources(Path(ppsspp) if ppsspp else None,
                                   Path(xemu) if xemu else None)
        except FirstRunError as error:
            self._message("System files missing", self._t("The selected PSP or Xbox folder is incomplete. Choose the matching system files, clear the field, or select Skip for now. Your existing configuration and files are preserved."), error=True)
            return
        self.ppsspp, self.xemu = ppsspp, xemu
        self._apply(next_page="host")

    def _skip_assets(self) -> None:
        # Discard only unsubmitted source choices, never a saved configuration
        # or Xemu's existing isolated working files.
        self.ppsspp, self.xemu = self.state.ppsspp_assets, ""
        self._apply(next_page="host")

    def _message(self, title: str, body: str, *, error: bool = False) -> None:
        kind = self.Gtk.MessageType.ERROR if error else self.Gtk.MessageType.INFO
        dialog = self.Gtk.MessageDialog(
            transient_for=self.window, modal=True, destroy_with_parent=True,
            message_type=kind, buttons=self.Gtk.ButtonsType.NONE, text=self._t(title),
        )
        dialog.add_button(self._t("OK"), self.Gtk.ResponseType.OK)
        dialog.format_secondary_text(self._t(body))
        self._size_message(dialog)
        self._run_dialog(dialog, self.Gtk.ResponseType.OK)

    def _size_message(self, dialog) -> None:
        from gi.repository import Pango

        width, height_limit = 640, 340
        parent_window = self.window.get_window()
        if parent_window is not None:
            monitor = self.window.get_display().get_monitor_at_window(parent_window)
            if monitor is not None:
                workarea = monitor.get_workarea()
                # Some backends expose an unknown (zero-sized) work area.
                if workarea.width > 48:
                    width = min(width, workarea.width - 48)
                if workarea.height > 0:
                    height_limit = min(height_limit, max(1, workarea.height // 2))
        dialog.set_default_size(width, -1)
        dialog.set_resizable(True)
        area = dialog.get_message_area()
        labels = [child for child in area.get_children() if isinstance(child, self.Gtk.Label)]
        for label in labels:
            label.set_line_wrap(True)
            label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            label.set_ellipsize(Pango.EllipsizeMode.NONE)
            label.set_lines(-1)
            label.set_max_width_chars(65)
            # WORD_CHAR otherwise has a one-character minimum width, which
            # can inflate the initial Wayland window height before mapping.
            label.set_size_request(max(1, width - 80), -1)
        if len(labels) > 1:
            details = labels[-1]
            # Keep GTK's height-for-width layout intact for normal messages;
            # only reports taller than the readable area need a viewport.
            _minimum, natural = details.get_preferred_height_for_width(max(1, width - 80))
            if natural <= height_limit:
                return
            area.remove(details)
            details.set_yalign(0)
            scroll = self.Gtk.ScrolledWindow()
            scroll.set_policy(self.Gtk.PolicyType.NEVER, self.Gtk.PolicyType.AUTOMATIC)
            scroll.set_overlay_scrolling(False)
            scroll.set_min_content_width(max(1, width - 80))
            scroll.add(details)
            area.pack_start(scroll, True, True, 0)
            scroll.show_all()

            # ScrolledWindow's natural-height propagation does not reliably
            # account for the label wrapping at the viewport's actual width.
            # Measure that width explicitly, including after a user resize.
            def fit_text(_widget=None, allocation=None):
                available = allocation.width if allocation is not None else max(1, width - 80)
                _minimum, natural = details.get_preferred_height_for_width(available)
                requested = min(height_limit, natural)
                if scroll.get_min_content_height() != requested:
                    scroll.set_min_content_height(requested)

            scroll.get_child().connect("size-allocate", fit_text)
            fit_text()

    def _question(self, title: str, body: str) -> bool:
        dialog = self.Gtk.MessageDialog(
            transient_for=self.window, modal=True, destroy_with_parent=True,
            message_type=self.Gtk.MessageType.QUESTION,
            buttons=self.Gtk.ButtonsType.NONE, text=self._t(title),
        )
        dialog.add_button(self._t("No"), self.Gtk.ResponseType.NO)
        dialog.add_button(self._t("Yes"), self.Gtk.ResponseType.YES)
        dialog.format_secondary_text(self._t(body))
        self._size_message(dialog)
        return self._run_dialog(dialog, self.Gtk.ResponseType.NO) == self.Gtk.ResponseType.YES

    def _run_dialog(self, dialog, default_response):
        # SDL polling continues inside Gtk.Dialog.run's nested loop. Own the
        # dialog explicitly so those inputs cannot activate the parent wizard.
        self.message_dialog = dialog
        dialog.set_default_response(default_response)
        dialog.get_widget_for_response(default_response).grab_focus()
        try:
            return dialog.run()
        finally:
            self.message_dialog = None
            dialog.destroy()

    def _dialog_input(self, button: str) -> None:
        dialog = self.message_dialog
        if button in {"b"}:
            dialog.response(self.Gtk.ResponseType.CANCEL)
        elif button in {"a", "start"}:
            focused = dialog.get_focus()
            if isinstance(focused, self.Gtk.Button):
                focused.clicked()
        elif button in {"up", "down", "left", "right"}:
            direction = (self.Gtk.DirectionType.TAB_BACKWARD if button in {"up", "left"}
                         else self.Gtk.DirectionType.TAB_FORWARD)
            dialog.child_focus(direction)

    def _run(self, action: str, callback: Callable) -> None:
        if action in {"doctor", "host-status"}:
            arguments = ("--config", str(self.state.config_path), "installer", "status")
        else:
            arguments = action_arguments(self.state.config_path, action)
        if action.startswith("steam") and getattr(self, "integration_launcher", None):
            arguments += ("--replace-existing",)
            self._run_arguments(arguments, callback, command=(self.integration_launcher,))
        else:
            self._run_arguments(arguments, callback)

    def _run_arguments(self, arguments: tuple[str, ...], callback: Callable, *, command=None) -> None:
        if self.busy:
            return
        self.busy = True
        self.window.set_sensitive(False)
        self.progress = self._label("Working… Please wait.")
        self.GLib.timeout_add(120, self._pulse)
        self.root.reorder_child(self.progress, 1)
        self.progress.show()

        def worker():
            try:
                result = run_action(command or self.command, arguments)
            except OSError as error:
                result = error
            self.GLib.idle_add(self._done, result, callback)

        threading.Thread(target=worker, daemon=True).start()

    def _pulse(self):
        if not self.busy: return False
        if getattr(self, "step_progress", None) is not None: self.step_progress.pulse()
        return True

    def _done(self, result, callback: Callable) -> bool:
        self.busy = False
        self.window.set_sensitive(True)
        if getattr(self, "progress", None) is not None and self.progress.get_parent() == self.root:
            self.root.remove(self.progress)
        if getattr(self, "step_progress", None) is not None: self.step_progress.set_fraction(self._step_fraction())
        if isinstance(result, OSError):
            self._message("Action unavailable", self._t("This step could not be completed (exit {code}). Check your folders, file permissions and available disk space, then try again. Your existing setup is preserved.", code=127), error=True)
        else:
            callback(result)
        return False

    def _apply(self, next_page=None) -> None:
        self.next_page = next_page
        unchanged = (self.state.configured and self.roms == self.state.roms
                     and self.bios == self.state.bios and self.hotkey == self.state.exit_hotkey
                     and self.ppsspp == self.state.ppsspp_assets
                     and not self.cores and not self.providers and not self.xemu and not self.shadps4)
        if unchanged:
            self._after_setup()
            return
        try:
            arguments = setup_arguments(
                self.state.config_path, roms=self.roms, bios=self.bios,
                exit_hotkey=self.hotkey, cores_from=self.cores,
                providers_from=self.providers,
                ppsspp_assets_from=(self.ppsspp if self.ppsspp != self.state.ppsspp_assets else ""),
                xemu_files_from=self.xemu,
                shadps4_from=self.shadps4,
            )
        except FirstRunError as error:
            self._message("Please check your folders", "Choose readable games and BIOS folders. Optional source folders must exist and contain the required files listed on the previous pages.", error=True)
            return
        self._run_arguments(arguments, self._setup_done)

    def _setup_done(self, result) -> None:
        if result.returncode:
            self._message("Setup needs attention", self._failure(result), error=True)
            return
        try:
            self.state = read_state(self.state.config_path)
        except FirstRunError as error:
            self._message("Setup needs attention", "Your settings file could not be read. It has not been changed. Please check it or use terminal setup.", error=True)
            return
        self.cores = self.providers = self.xemu = self.shadps4 = ""
        self._after_setup()

    def _after_setup(self):
        if getattr(self, "next_page", None):
            page = self.next_page
            self._run("host-status", lambda result: self._refresh_page(result, page))
        else:
            self._run("doctor", self._doctor_done)

    def _failure(self, result) -> str:
        return self._t("This step could not be completed (exit {code}). Check your folders, file permissions and available disk space, then try again. Your existing setup is preserved.", code=result.returncode)

    def _status(self, result) -> dict | None:
        try:
            report = json.loads(result.stdout) if result.returncode == 0 else None
            if not isinstance(report, dict) or "requirements" not in report:
                raise ValueError("invalid report")
            return report
        except (ValueError, TypeError):
            self._message("Check complete", "Host status could not be checked. Please try again.", error=True)
            return None

    def _status_text(self, report: dict) -> str:
        t = self._t
        lines = []
        active = set(report.get("active_systems", ()))
        for entry in report["requirements"] + report["cores"] + report.get("checks", []):
            category = ("Error" if entry.get("invalid") else "Ready" if entry["available"] else
                        "Setup required" if entry.get("required", True) else "Optional")
            lines.append(t("{component}: {status}", component=t(entry["label"]), status=self._badge(category)))
        for key, message, system in (("rpcs3", "PS3 firmware: {status}", "ps3"),
                             ("xemu_firmware", "Xbox firmware: {status}", "xbox"),
                             ("xemu_hdd", "Xbox HDD: {status}", "xbox")):
            category = "Ready" if report[key] else "Setup required" if system in active else "Optional"
            lines.append(t(message, status=self._badge(category)))
        eeprom = report.get("eeprom", {"missing": not report["xemu_eeprom"]})
        category = "Error" if eeprom.get("invalid") else "Setup required" if eeprom.get("missing") and "xbox" in active else "Optional" if eeprom.get("missing") else "Ready"
        lines.append(t("Xbox EEPROM: {status}", status=self._badge(category)))
        for key, label, system in (("xenia", "Xenia", "xbox360"), ("shadps4", "shadPS4", "ps4")):
            status = report[key]
            category = ("Ready" if status in {"MANAGED", "OVERRIDE", "FOUND"} else
                        "Error" if status in {"INVALID", "AMBIGUOUS", "RUNTIME_DEPENDENCY_MISSING"} else
                        "Setup required" if system in active else "Optional")
            lines.append(f"{label}: " + self._badge(category))
        return "\n".join(lines)

    def _doctor_done(self, result) -> None:
        report = self._status(result)
        if report is None:
            return
        self.last_report = report
        self.doctor_output = self._status_text(report)
        healthy = report["configured"] and all(s["available"] for s in report["requirements"] + report["cores"] + report.get("checks", []) if s.get("required", True))
        active = set(report.get("active_systems", ()))
        healthy = healthy and ("ps3" not in active or report["rpcs3"])
        healthy = healthy and ("xbox" not in active or (report["xemu_firmware"] and report["xemu_hdd"] and not report.get("eeprom", {}).get("invalid")))
        healthy = healthy and ("3do" not in active or report.get("opera_bios") == "OK")
        for system, provider in (("ps4", "shadps4"), ("xbox360", "xenia")):
            healthy = healthy and (system not in active or report[provider] in {"MANAGED", "OVERRIDE", "FOUND"})
        self.finish_text = ("Your setup checks passed. Start Embercade to check each game and its BIOS requirements." if healthy else
                            "Your basic configuration is saved. Some components still need attention.")
        self._go("finish")

    def _host_status(self, result) -> None:
        report = self._status(result)
        if report is None:
            return
        self.last_report = report
        lines = [self._status_text(report)]
        for key, message in (("packages", "Installable repository packages: {packages}"),
                             ("unavailable", "Unavailable packages: {packages}"),
                             ("community", "Optional community packages: {packages}")):
            if report[key]:
                lines.append(self._t(message, packages=", ".join(report[key])))
        self._message("Host software", "\n".join(lines))

    def _show_result(self, result) -> None:
        self._message("Action unavailable" if result.returncode else "Check complete",
                      self._failure(result) if result.returncode else self._t("Steam shortcut saved."), error=bool(result.returncode))

    def _language_settings(self) -> None:
        self._remember_visible_fields()
        self._language_return = self.page
        self._go("language")

    def _preview_language(self, choice) -> None:
        self.language = choice.get_active_id()
        self._render()

    def _save_language(self) -> None:
        self.language = self.language_choice.get_active_id()
        arguments = ("--config", str(self.state.config_path), "installer", "language", "--language", self.language)
        self._run_arguments(arguments, self._language_saved)

    def _language_saved(self, result) -> None:
        if result.returncode:
            self._message("Setup needs attention", "Language could not be saved. Check that your settings file is writable. Your existing setup is preserved.", error=True)
            return
        self.state = read_state(self.state.config_path)
        if getattr(self, "last_report", None) is not None:
            self.doctor_output = self._status_text(self.last_report)
        self._go(self._language_return or "welcome")

    def _bootstrap(self) -> None:
        if self.busy or self.message_dialog is not None:
            return
        distro = read_os_release()
        if not distro.supports_automatic_install:
            self._message("Unsupported distribution", self._t('Detected system: {distribution}. Automatic host-software installation requires an Arch-based distribution and pacman. No packages have been installed.', distribution=distro.name), error=True)
            return
        if not Pacman.is_available():
            self._message("Pacman unavailable", PACMAN_UNAVAILABLE, error=True)
            return
        if not self._question("Install missing host software?",
                              "Embercade opens a terminal so you can review and confirm the packages. It closes after success. On failure, the output stays visible until you press Enter."):
            return
        try:
            transaction = TerminalInstallation.start(self.command, self.state.config_path,
                EmbercadePaths.from_environment().state / "installer", self.language)
        except OSError:
            self._message("Terminal required", "Open a desktop terminal and run: embercade bootstrap", error=True)
            return
        self.busy = True
        self.window.set_sensitive(False)
        self.progress = self._label("Working… Please wait.")
        self.GLib.timeout_add(120, self._pulse)
        self.root.reorder_child(self.progress, 1)
        self.progress.show()
        self.GLib.timeout_add(150, self._host_poll, transaction)

    def _host_poll(self, transaction) -> bool:
        try:
            progress = transaction.progress()
            if isinstance(progress, dict):
                messages = {
                    "starting": "Opening the host installation…",
                    "checking": "Checking installed software and available packages…",
                    "confirmation": "Please review and confirm the installation in the terminal.",
                    "repository": "Installing host software: downloads, package checks and completion hooks…",
                    "community": "Building additional host software. This can take several minutes; follow the terminal output.",
                }
                if progress.get("phase") in messages:
                    seconds = max(0, int(time.monotonic() - progress["started"]))
                    self.progress.set_text(self._t(messages[progress["phase"]]) + "\n" +
                        self._t("Elapsed: {minutes}:{seconds}", minutes=seconds // 60, seconds=f"{seconds % 60:02d}"))
        except (OSError, ValueError, AttributeError):
            pass  # Progress is informational; only the actual result ends the transaction.
        try:
            result = transaction.result()
        except (OSError, ValueError):
            result = {"outcome": "unknown", "code": 127}
        if result is None:
            return True
        threading.Thread(target=transaction.reap, daemon=True).start()
        self.busy = False
        self.window.set_sensitive(True)
        if self.progress.get_parent() == self.root:
            self.root.remove(self.progress)
        self.host_result = result
        self._run("host-status", self._host_finished)
        return False

    def _host_finished(self, result) -> None:
        report = self._status(result)
        if report is not None:
            self.last_report = report
            if self.page == "finish":
                self.doctor_output = self._status_text(report)
            self._render()
        outcome = self.host_result["outcome"]
        message = {"success": "Host installation completed.",
                   "failed": "Host installation failed (exit {code}). The terminal keeps the diagnostic output. You can retry the installation.",
                   "cancelled": "Host installation was cancelled.",
                   "unknown": "Host installation ended without a result. The terminal may have been closed. Dependencies will be checked again."}[outcome]
        body = self._t(message, code=self.host_result["code"])
        if report is not None:
            body += "\n\n" + self._status_text(report)
        self._message("Host software", body, error=outcome in {"failed", "unknown"})

    def _step_fraction(self):
        return next(index / (len(STEPS) - 1) for index, (_, group) in enumerate(STEPS) if self.page in group)

    def _refresh_page(self, result, page=None):
        report = self._status(result)
        if report is not None:
            self.last_report = report
            self.doctor_output = self._status_text(report)
            self._go(page or self.page)

    def _continue_xbox(self):
        self._remember_visible_fields()
        self._go("ps3")

    def _continue_ps3(self):
        self._remember_visible_fields()
        self._go("desktop")

    def _xbox_action(self, action):
        self._remember_visible_fields()
        extra = []
        if action == "xbox-import":
            if not self.eeprom_source:
                self._message("Choose file", "Select a valid 256-byte EEPROM file first.", error=True)
                return
            if not self._question("Import EEPROM?", "Import replaces the whole EEPROM, including its console identity and HDD key. Your existing EEPROM is backed up; the HDD image and selected source file stay unchanged."): return
            extra = ["--eeprom", self.eeprom_source, "--replace-eeprom"]
        elif action == "xbox-edit":
            if not self._question("Save console settings?", "A valid EEPROM is required. Embercade saves a backup and preserves the HDD key and console identity."): return
            for key, option in (("language", "--xbox-language"), ("region", "--region"), ("video", "--video")):
                extra += [option, self.xbox_choices[key]]
        self._run_arguments(("--config", str(self.state.config_path), "installer", action, *extra), self._xbox_done)

    def _xbox_done(self, result):
        if result.returncode:
            self._message("Xbox setup needs attention", "Close Xemu and check the selected file. Editing requires an authenticated 256-byte EEPROM with valid checksums. Create a default EEPROM or import a valid file, then retry. Existing data is preserved.", error=True)
            return
        self._message("Check complete", "Xbox EEPROM validated and saved. Any replaced EEPROM has a backup beside it.")
        self._run("host-status", self._refresh_page)

    def _ps3_action(self, download=False):
        self._remember_visible_fields()
        if download:
            if not self._question("Download official PS3 firmware?", "Download PS3UPDAT.PUP from the official PlayStation support page and install it with RPCS3? Firmware is subject to Sony's terms. Embercade does not distribute it. Existing firmware is preserved."): return
            extra = ("--download", "--yes")
        else:
            if not self.pup_source:
                self._message("Choose file", "Select your PS3UPDAT.PUP file first.", error=True)
                return
            if not self._question("Install selected firmware?", "RPCS3 will validate and install this PUP in a temporary Embercade profile. Only a successful installation is copied to your isolated profile. Existing firmware is preserved."): return
            extra = ("--pup", self.pup_source)
        self._run_arguments(("--config", str(self.state.config_path), "installer", "firmware", *extra), self._ps3_done)

    def _ps3_done(self, result):
        if result.returncode:
            self._message("PS3 setup needs attention", "Check your connection and PUP file, close RPCS3 and try again. Existing firmware is never replaced. If automatic download fails, select the official PUP downloaded in your browser.", error=True)
        else:
            self._message("Check complete", "PS3 firmware is installed in Embercade's isolated profile.")
        self._run("host-status", self._refresh_page)

    def _save_desktop(self):
        self._remember_visible_fields()
        if not os.environ.get("EMBERCADE_PREFIX"):
            self._message("Desktop integration", "Desktop integration is available from the installed application or AppImage. You can continue setup here.")
            self._go("checks")
            return
        if not self.menu_enabled and not self.shortcut_enabled and not self.local_image_enabled:
            if self.steam_enabled: self._steam()
            self._go("checks")
            return
        extra = []
        if not self.menu_enabled: extra.append("--no-menu")
        if self.shortcut_enabled: extra.append("--shortcut")
        if not self.local_image_enabled: extra.append("--original-image")
        self._run_arguments(("--config", str(self.state.config_path), "installer", "desktop", *extra), self._desktop_done)

    def _desktop_done(self, result):
        if result.returncode:
            self._message("Desktop integration needs attention", "Check the Desktop folder and free space. Existing files changed outside Embercade are preserved. Adjust your choices and retry, or turn off menu and desktop integration to continue.", error=True)
            return
        try: self.integration_launcher = json.loads(result.stdout)["launcher"]
        except (ValueError, KeyError):
            self._message("Desktop integration needs attention", "Host status could not be checked. Please try again.", error=True)
            return
        self._go("checks")
        if self.steam_enabled: self._steam()

    def _firmware(self) -> None:
        if self._question("Open the isolated RPCS3 firmware installer?",
                          "In RPCS3, choose File → Install Firmware and select your own PS3UPDAT.PUP. Close RPCS3 when finished. Existing firmware and saves are preserved."):
            self._run_arguments(("--config", str(self.state.config_path), "installer", "firmware"), self._firmware_done)

    def _firmware_done(self, result) -> None:
        if result.returncode:
            self._message("Setup needs attention", "Firmware is still missing. Install it in RPCS3 and try the check again.", error=True)
        self._run("host-status", self._refresh_page)

    def _steam(self) -> None:
        self._run("steam-plan", self._steam_plan)

    def _steam_plan(self, result) -> None:
        if result.returncode:
            self._message("Add Steam later", "Close Steam completely and try again. Your other entries are preserved.")
            return
        approved = self._question(
            'Add Embercade to Steam?',
            'Steam must be fully closed. Your other games and entries will be preserved.',
        )
        if approved:
            self._run("steam", self._show_result)

    def _launch(self) -> None:
        self.launch_after_close = True
        self.window.destroy()

    def _choose_directory(self, entry, *, file: bool = False) -> None:
        if self.folder_dialog is not None:
            return
        Gtk = self.Gtk
        accepted, selected, failed = False, None, False
        parent_closed = False
        use_native = native_portal_available(file=file)
        for native in ((True, False) if use_native else (False,)):
            dialog, parent_close = None, None
            try:
                dialog = create_chooser(
                    Gtk, self.window, title=self._t("Choose file" if file else "Choose folder"),
                    accept_label=self._t("Use this file" if file else "Use this folder"),
                    cancel_label=self._t("Cancel"), initial=entry.get_text(), file=file,
                    use_native=native,
                )
                self.folder_dialog = dialog
                # A portal is not a Gtk.Window and has no destroy-with-parent.
                def close_with_parent(*_):
                    nonlocal parent_closed
                    parent_closed = True
                    dialog.hide()
                parent_close = self.window.connect("destroy", close_with_parent)
                accepted = dialog.run() == Gtk.ResponseType.ACCEPT
                selected = validate_selection(dialog.get_filename(), file=file) if accepted else None
                break  # Cancellation/close must never reopen a fallback dialog.
            except (OSError, RuntimeError, ValueError):
                accepted, selected = False, None
                failed = not native
            finally:
                self.folder_dialog = None
                if parent_close is not None and self.window.handler_is_connected(parent_close):
                    self.window.disconnect(parent_close)
                if dialog is not None:
                    dialog.destroy()
        if accepted and selected is not None:
            entry.set_text(selected)
        elif failed or accepted:
            self._message("Location unavailable", "Choose an available local folder or file. Mount network shares before selecting them. Your previous selection is unchanged.", error=True)
        if not parent_closed:
            entry.grab_focus()

    def _folder_input(self, button: str) -> None:
        dialog = self.folder_dialog
        if button == "b":
            # hide() ends NativeDialog.run without accepting, including portals.
            dialog.hide()
        elif isinstance(dialog, self.Gtk.FileChooserDialog):
            # The in-process fallback is also usable in a Gamescope session.
            if button in {"up", "down", "left", "right"}:
                direction = (self.Gtk.DirectionType.TAB_BACKWARD if button in {"up", "left"}
                             else self.Gtk.DirectionType.TAB_FORWARD)
                dialog.child_focus(direction)
            elif button == "a":
                focused = dialog.get_focus()
                if focused is not None:
                    focused.activate()
            elif button in {"x", "start"}:
                dialog.response(self.Gtk.ResponseType.ACCEPT)
        # Native desktop dialogs own their keyboard/mouse/Steam Input navigation;
        # never forward their controller events to the wizard underneath them.


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="embercade wizard")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        GLib, Gtk = _gtk()
    except (ImportError, OSError, FirstRunError) as error:
        print(Translator(system_language())("Graphical setup is unavailable. Check GTK3/PyGObject and your desktop session."), file=sys.stderr)
        return 2
    try:
        wizard = Wizard(args.config, GLib, Gtk)
    except (OSError, FirstRunError) as error:
        dialog = Gtk.MessageDialog(
            modal=True, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.NONE,
            text=Translator(system_language())("Existing Embercade settings need attention"),
        )
        dialog.add_button(Translator(system_language())("OK"), Gtk.ResponseType.OK)
        dialog.format_secondary_text(
            Translator(system_language())("Your settings file could not be read. It has not been changed. Please check it or use terminal setup.")
        )
        dialog.run()
        dialog.destroy()
        return 2
    wizard.window.show_all()
    Gtk.main()
    if wizard.launch_after_close:
        return subprocess.call([*wizard.command, *action_arguments(args.config, "start")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

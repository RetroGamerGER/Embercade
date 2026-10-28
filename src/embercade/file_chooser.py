"""Desktop file selection shared by every installer source field.

Use the desktop's places/navigation rather than enumerating source directories.
Only mounted paths can be handed to the existing setup/import backends.
"""
from __future__ import annotations

from pathlib import Path
import os


def validate_selection(filename: str | None, *, file: bool = False) -> str | None:
    if not filename or not filename.strip() or "://" in filename:
        return None
    try:
        path = Path(filename).expanduser().absolute()
        valid = path.is_file() if file else path.is_dir()
        if valid and os.access(path, os.R_OK | (0 if file else os.X_OK)):
            return str(path)
    except (OSError, ValueError, RuntimeError):
        pass
    return None


def initial_location(value: str, *, file: bool = False,
                     home: Path | None = None) -> tuple[Path, Path | None]:
    # Path("") is "."; never let an empty field select the launch directory.
    home = (home or Path.home()).absolute()
    if value.strip():
        selected = validate_selection(value, file=file)
        if selected:
            path = Path(selected)
            return (path.parent, path) if file else (path, None)
        if file and (directory := validate_selection(value)):
            return Path(directory), None
    # Do not climb a disconnected mount's ancestors into /run or /media.
    return home, None


def native_portal_available(*, file: bool = False) -> bool:
    """Bound the missing-service check; keep Gamescope's fallback in-process."""
    if os.environ.get("GTK_USE_PORTAL") == "0" or os.environ.get("GAMESCOPE_WAYLAND_DISPLAY"):
        return False
    from gi.repository import Gio, GLib
    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        result = connection.call_sync(
            "org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop",
            "org.freedesktop.DBus.Properties", "Get",
            GLib.Variant("(ss)", ("org.freedesktop.portal.FileChooser", "version")),
            GLib.VariantType.new("(v)"), Gio.DBusCallFlags.NONE, 1000, None,
        )
        return result.unpack()[0] >= (1 if file else 3)
    except GLib.Error:
        return False


def create_chooser(Gtk, parent, *, title: str, accept_label: str,
                   cancel_label: str, initial: str, file: bool = False,
                   use_native: bool = True):
    action = Gtk.FileChooserAction.OPEN if file else Gtk.FileChooserAction.SELECT_FOLDER
    dialog = None
    if use_native:
        try:
            dialog = Gtk.FileChooserNative.new(title, parent, action, accept_label, cancel_label)
        except (AttributeError, TypeError, RuntimeError):
            # Older/unavailable native integration still has GTK's places browser.
            pass
    if dialog is None:
        dialog = Gtk.FileChooserDialog(title=title, transient_for=parent, action=action)
        dialog.add_buttons(cancel_label, Gtk.ResponseType.CANCEL,
                           accept_label, Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        dialog.set_default_size(960, 640)
    try:
        dialog.set_modal(True)
        dialog.set_local_only(True)
        dialog.set_select_multiple(False)
        dialog.set_create_folders(False)
        directory, selected = initial_location(initial, file=file)
        if dialog.set_current_folder(str(directory)) is False:
            dialog.set_current_folder(str(Path.home()))
        if selected is not None:
            dialog.set_filename(str(selected))
    except Exception:
        dialog.destroy()
        raise
    return dialog

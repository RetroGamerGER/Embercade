from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
import json
import os
import shutil
import stat
import subprocess
import unittest

from embercade import xpadneo_helper as helper


class SyntheticHost(helper.Host):
    """All writes and device lifetime simulation are confined to a temp root."""

    def __init__(self, root):
        super().__init__(root, owner_uid=os.getuid(), runner=self.run,
                         sleep=self.advance, clock=lambda: self.now)
        self.now = 0
        self.actions = []
        self.sequence = 0
        self.not_paired = set()
        self.fail_disconnect = set()
        self.fail_reconnect = set()
        self.held_mouse = set()
        self.parameter.parent.mkdir(parents=True)
        self.parameter.write_text("N")
        self.driver.mkdir(parents=True)
        self.config.parent.mkdir(parents=True)
        self.lock.parent.mkdir(parents=True)

    def advance(self, seconds):
        self.now += seconds

    def attach(self, address="00:11:22:33:44:55", *, bus="0005", name="Fixture gamepad"):
        self.sequence += 1
        identity = f"{bus}:045E:028E.{self.sequence:04X}"
        node = self.root / "sys/devices/virtual/misc/uhid" / identity
        node.mkdir(parents=True)
        (node / "uevent").write_text(f"HID_ID={bus}:0000045E:0000028E\nHID_UNIQ={address}\nHID_NAME={name}\n")
        (self.driver / identity).symlink_to(node)
        return node

    def run(self, command, **kwargs):
        self.actions.append(tuple(command[-2:]))
        self.assert_transport(kwargs)
        action, address = command[-2:]
        if action == "info":
            value = "no" if address in self.not_paired else "yes"
            return subprocess.CompletedProcess(command, 0, f"Paired: {value}\nConnected: yes\n", "")
        if action == "disconnect" and address not in self.fail_disconnect:
            for device in self.devices():
                if device.address == address:
                    (self.driver / device.node.name).unlink()
                    shutil.rmtree(device.node)
        if action == "connect" and address not in self.fail_reconnect:
            self.attach(address)
        return subprocess.CompletedProcess(command, 0, "", "")

    @staticmethod
    def assert_transport(kwargs):
        assert kwargs["env"] == helper.CLEAN_ENV
        assert kwargs["cwd"] == "/"
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["timeout"] == 10

    def atomic_write(self, path, data):
        assert not self.devices(), "Persistence started before every controller was removed"
        self.actions.append(("write", path.name))
        super().atomic_write(path, data)

    def set_parameter(self, disabled):
        assert not self.devices(), "Live flag changed with a bound controller"
        self.actions.append(("parameter", disabled))
        super().set_parameter(disabled)

    def mouse_released(self, device):
        self.actions.append(("mouse_check", device.address))
        return device.address not in self.held_mouse


class XpadneoHelperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.host = SyntheticHost(Path(self.temporary.name))

    def test_status_is_read_only_and_driver_based(self):
        self.host.attach(name="Unlisted Bluetooth Controller")
        result = helper.inspect(self.host)
        self.assertTrue(result["can_enable"])
        self.assertEqual(result["devices"][0]["name"], "Unlisted Bluetooth Controller")
        self.assertEqual(self.host.actions, [])
        self.assertFalse(self.host.lock.exists())
        self.assertFalse(self.host.receipt.exists())

    def test_disconnect_all_then_persist_then_flag_then_fresh_reconnect(self):
        first, second = "00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"
        old = [self.host.attach(first), self.host.attach(second)]
        unrelated = self.host.config.parent / "other-controller.conf"
        unrelated.write_text("options hid_xpadneo rumble_attenuation=20\n")
        result = helper.execute("enable", self.host)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["changed"])
        self.assertEqual(result["code"], "enabled")
        self.assertEqual(self.host.actions[:4], [("info", first), ("info", second), ("disconnect", first), ("disconnect", second)])
        self.assertTrue(all(not path.exists() for path in old))
        parameter = self.host.actions.index(("parameter", True))
        self.assertGreater(self.host.actions.index(("connect", first)), parameter)
        self.assertEqual(self.host.config.read_bytes(), helper.CONFIG)
        self.assertFalse(json.loads(self.host.receipt.read_text())["previous_shift_disabled"])
        self.assertEqual(unrelated.read_text(), "options hid_xpadneo rumble_attenuation=20\n")
        self.assertTrue(result["status"]["can_undo"])

    def test_undo_restores_saved_state_and_only_owned_files(self):
        self.host.attach()
        self.assertTrue(helper.execute("enable", self.host)["ok"])
        result = helper.execute("undo", self.host)
        self.assertTrue(result["ok"], result)
        self.assertEqual(self.host.parameter.read_text(), "N")
        self.assertFalse(self.host.receipt.exists())
        self.assertFalse(self.host.config.exists())
        self.assertEqual(len(self.host.devices()), 1)

    def test_legacy_manual_option_is_never_adopted_or_undone(self):
        path = self.host.config.parent / "90-embercade-xpadneo.conf"
        text = "options hid-xpadneo disable_shift_mode=1\n"
        path.write_text(text)
        self.host.parameter.write_text("Y")
        self.assertEqual(helper.inspect(self.host)["code"], "external_configuration")
        for operation in ("enable", "undo"):
            result = helper.execute(operation, self.host)
            self.assertFalse(result["changed"])
        self.assertFalse(self.host.receipt.exists())
        self.assertEqual(path.read_text(), text)

    def test_already_disabled_without_receipt_has_no_enable_or_undo(self):
        self.host.parameter.write_text("Y")
        result = helper.inspect(self.host)
        self.assertFalse(result["can_enable"])
        self.assertFalse(result["can_undo"])
        self.assertEqual(result["code"], "already_enabled")

    def test_unowned_or_changed_config_refuses_without_disconnect(self):
        self.host.attach()
        self.host.config.write_bytes(helper.CONFIG)
        self.assertEqual(helper.execute("enable", self.host)["code"], "ownership_conflict")
        # Seed only synthetic state directly: simulate foreign edits after an
        # earlier successful installation without calling live transport.
        self.host.receipt.parent.mkdir(parents=True)
        self.host.receipt.write_text(json.dumps(dict(version=1, previous_shift_disabled=False,
                                                   config_sha256=helper.CONFIG_HASH, state="enabled")))
        self.host.config.write_text("# changed by its owner\n")
        self.assertEqual(helper.execute("undo", self.host)["code"], "ownership_conflict")
        self.assertEqual(self.host.actions, [])

    def test_symlink_and_writable_parent_refused(self):
        target = self.host.root / "protected.txt"
        target.write_text("preserve")
        self.host.config.symlink_to(target)
        self.assertEqual(helper.execute("enable", self.host)["code"], "ownership_conflict")
        self.assertEqual(target.read_text(), "preserve")
        self.host.config.unlink()
        self.host.config.parent.chmod(0o777)
        self.assertEqual(helper.execute("enable", self.host)["code"], "ownership_conflict")

    def test_busy_lock_and_status_do_not_begin_transaction(self):
        with self.host.transaction_lock():
            self.assertEqual(helper.inspect(self.host)["code"], "busy")
            self.assertEqual(helper.execute("enable", self.host)["code"], "busy")
        self.assertEqual(self.host.actions, [])

    def test_unknown_readonly_and_absent_parameter(self):
        self.host.parameter.write_text("unknown")
        self.assertEqual(helper.inspect(self.host)["code"], "unsupported_parameter")
        self.host.parameter.write_text("N")
        self.host.parameter.chmod(0o444)
        self.assertEqual(helper.inspect(self.host)["code"], "permission_unavailable")
        self.host.parameter.unlink()
        self.assertEqual(helper.inspect(self.host)["code"], "unsupported_parameter")
        shutil.rmtree(self.host.parameter.parent.parent)
        self.assertEqual(helper.inspect(self.host)["code"], "driver_not_loaded")

    def test_usb_unknown_identity_and_unpaired_fail_before_disconnect(self):
        node = self.host.attach(bus="0003")
        self.assertEqual(helper.execute("enable", self.host)["code"], "unsupported_device")
        (node / "uevent").write_text("HID_ID=0005:0000045E:0000028E\nHID_UNIQ=not-a-mac\n")
        self.assertEqual(helper.execute("enable", self.host)["code"], "controller_unidentified")
        (self.host.driver / node.name).unlink()
        shutil.rmtree(node)
        self.host.attach()
        self.host.not_paired.add("00:11:22:33:44:55")
        self.assertEqual(helper.execute("enable", self.host)["code"], "controller_not_paired")
        self.assertFalse(any(action[0] == "disconnect" for action in self.host.actions))

    def test_partial_disconnect_failure_reconnects_only_removed_controller(self):
        first, second = "00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"
        self.host.attach(first)
        self.host.attach(second)
        self.host.fail_disconnect.add(second)
        result = helper.execute("enable", self.host)
        self.assertEqual(result["code"], "disconnect_failed")
        self.assertFalse(result["changed"])
        self.assertIn(("connect", first), self.host.actions)
        self.assertNotIn(("connect", second), self.host.actions)
        self.assertFalse(self.host.config.exists())

    def test_new_controller_before_live_write_leaves_recoverable_pending_receipt(self):
        original = self.host.atomic_write
        def write(path, data):
            original(path, data)
            if path == self.host.config:
                self.host.attach()
        self.host.atomic_write = write
        result = helper.execute("enable", self.host)
        self.assertEqual(result["code"], "partial_failure")
        self.assertTrue(result["changed"])
        self.assertEqual(self.host.parameter.read_text(), "N")
        self.assertEqual(result["status"]["code"], "managed_pending")
        self.assertTrue(helper.execute("undo", self.host)["ok"])

    def test_pending_receipt_without_config_can_be_safely_undone(self):
        self.host.write_receipt(False, "pending")
        self.assertTrue(helper.inspect(self.host)["can_undo"])
        self.assertTrue(helper.execute("undo", self.host)["ok"])
        self.assertFalse(self.host.receipt.exists())

    def test_undo_refuses_changed_live_state_before_disconnect(self):
        self.host.attach()
        self.assertTrue(helper.execute("enable", self.host)["ok"])
        self.host.parameter.write_text("N")
        self.host.actions.clear()
        result = helper.execute("undo", self.host)
        self.assertEqual(result["code"], "ownership_conflict")
        self.assertFalse(result["changed"])
        self.assertEqual(self.host.actions, [])

    def test_new_controller_during_undo_receipt_prevents_live_flag_change(self):
        self.assertTrue(helper.execute("enable", self.host)["ok"])
        original = self.host.atomic_write
        def write(path, data):
            original(path, data)
            if path == self.host.receipt:
                self.host.attach()
        self.host.atomic_write = write
        # Exercise the production write guard, independently of the fixture's
        # additional assertion that all earlier writes happened disconnected.
        self.host.set_parameter = lambda value: helper.Host.set_parameter(self.host, value)
        result = helper.execute("undo", self.host)
        self.assertEqual(result["code"], "partial_failure")
        self.assertTrue(result["changed"])
        self.assertEqual(self.host.parameter.read_text(), "Y")
        self.assertEqual(result["status"]["code"], "managed_pending")

    def test_persistence_error_reports_possible_change_and_reconnects(self):
        self.host.attach()
        original = self.host.atomic_write
        def write(path, data):
            original(path, data)
            if path == self.host.config:
                raise OSError("synthetic late fsync failure")
        self.host.atomic_write = write
        result = helper.execute("enable", self.host)
        self.assertEqual(result["code"], "partial_failure")
        self.assertTrue(result["changed"])
        self.assertEqual(len(self.host.devices()), 1)

    def test_reconnect_failure_never_reports_no_change(self):
        address = "00:11:22:33:44:55"
        self.host.attach(address)
        self.host.fail_reconnect.add(address)
        result = helper.execute("enable", self.host)
        self.assertEqual(result["code"], "reconnect_pending")
        self.assertTrue(result["changed"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["pending_reconnect"], [address])
        self.assertTrue(result["status"]["managed"])

    def test_reconnected_mouse_with_held_keys_is_removed_and_reported_pending(self):
        address = "00:11:22:33:44:55"
        self.host.attach(address)
        self.host.held_mouse.add(address)
        result = helper.execute("enable", self.host)
        self.assertEqual(result["code"], "reconnect_pending")
        self.assertEqual(self.host.devices(), [])
        self.assertEqual(self.host.actions.count(("disconnect", address)), 2)

    def test_reconnected_mouse_with_unreadable_keys_is_also_removed(self):
        self.host.attach()
        with patch.object(self.host, "mouse_released", side_effect=OSError("synthetic read failure")):
            result = helper.execute("enable", self.host)
        self.assertEqual(result["code"], "reconnect_pending")
        self.assertTrue(result["changed"])
        self.assertEqual(self.host.devices(), [])

    def test_old_input_tree_must_disappear_even_if_driver_binding_is_gone(self):
        node = self.host.attach()
        original = self.host.run
        def transport(command, **kwargs):
            if command[-2] == "disconnect":
                (self.host.driver / node.name).unlink()
                return subprocess.CompletedProcess(command, 0, "", "")
            return original(command, **kwargs)
        self.host.runner = transport
        result = helper.execute("enable", self.host)
        self.assertEqual(result["code"], "disconnect_failed")
        self.assertFalse(result["changed"])
        self.assertTrue(node.exists())
        self.assertFalse(self.host.config.exists())

    def test_real_mouse_probe_waits_for_tree_and_event_and_checks_current_keys(self):
        node = self.host.attach()
        device = self.host.devices()[0]
        probe = lambda: helper.Host.mouse_released(self.host, device)
        self.assertIsNone(probe())
        mouse = node / "input/input90"
        (mouse / "capabilities").mkdir(parents=True)
        (mouse / "capabilities/rel").write_text("3\n")
        self.assertIsNone(probe())
        event = mouse / "event90"
        event.mkdir()
        (event / "dev").write_text("13:90\n")
        info = SimpleNamespace(st_mode=stat.S_IFCHR | 0o600, st_rdev=os.makedev(13, 90))
        with patch.object(os, "open", return_value=45) as opened, patch.object(os, "close") as closed, \
                patch.object(os, "fstat", return_value=info), patch.object(helper.fcntl, "ioctl") as ioctl:
            self.assertTrue(probe())
            self.assertEqual(opened.call_args.args[0], self.host.root / "dev/input/event90")
            self.assertEqual(ioctl.call_args.args[1], 0x80604518)
            def held(_fd, _request, keys, _mutate):
                keys[276 // 8] |= 1 << (276 % 8)
            ioctl.side_effect = held
            self.assertFalse(probe())
            ioctl.side_effect = OSError("fixture cannot inspect keys")
            with self.assertRaises(OSError):
                probe()
            self.assertEqual(closed.call_count, 3)

    def test_real_probe_missing_mouse_requires_explicit_disable_mouse(self):
        node = self.host.attach()
        (node / "input/input1/capabilities").mkdir(parents=True)
        (node / "input/input1/capabilities/rel").write_text("0\n")
        device = self.host.devices()[0]
        self.assertIsNone(helper.Host.mouse_released(self.host, device))
        self.host.parameter.with_name("disable_mouse").write_text("Y\n")
        self.assertTrue(helper.Host.mouse_released(self.host, device))

    def test_reconnect_waits_for_mouse_registration_before_accepting(self):
        self.host.attach()
        with patch.object(self.host, "mouse_released", side_effect=[None, None, True]) as probe:
            result = helper.execute("enable", self.host)
        self.assertTrue(result["ok"], result)
        self.assertEqual(probe.call_count, 3)

    def test_cli_rejects_extra_paths_and_nonroot_without_execution(self):
        with patch.object(helper, "execute") as execute, patch("builtins.print"):
            self.assertEqual(helper.main(["enable", "/tmp/arbitrary"]), 1)
            with patch.object(os, "geteuid", return_value=1000):
                self.assertEqual(helper.main(["enable"]), 1)
        execute.assert_not_called()

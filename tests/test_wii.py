from io import StringIO
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import os
import stat
import subprocess
import unittest

from embercade.wii import (WiiHidDevice, discover_wii_hid, _remote_responds,
                          real_wiimote_connected, wii_device_mounts, wii_hardware_summary)


class WiiHardwareTests(unittest.TestCase):
    def device(self, **values):
        fields = dict(path=Path('/dev/hidraw42'), transport='USB', name='receiver',
                      driver='hid-generic', accessible=True, device_number=os.makedev(243, 42))
        return WiiHidDevice(**(fields | values))

    def test_identity_and_node_are_checked_without_opening_hardware(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            entry = root / 'sys/hidraw42'
            (entry / 'device').mkdir(parents=True)
            (entry / 'device/uevent').write_text('HID_ID=0003:0000057E:00000306\nHID_NAME=Mayflash\n')
            (entry / 'device/driver').symlink_to(root / 'hid-generic')
            (root / 'hid-generic').mkdir()
            (entry / 'dev').write_text('243:42\n')
            native_lstat = Path.lstat

            def node_stat(path):
                if path == root / 'dev/hidraw42':
                    return SimpleNamespace(st_mode=stat.S_IFCHR, st_rdev=os.makedev(243, 42))
                return native_lstat(path)

            with patch.object(Path, 'lstat', node_stat), patch('embercade.wii.os.access', return_value=True), \
                    patch('embercade.wii.os.open') as opened:
                devices = discover_wii_hid(root / 'sys', root / 'dev')
                self.assertEqual(len(devices), 1)
                self.assertTrue(devices[0].usable)
                self.assertEqual(devices[0].transport, 'USB')
                opened.assert_not_called()
                (entry / 'device/uevent').write_text('HID_ID=0003:00001234:00000306\n')
                self.assertEqual(discover_wii_hid(root / 'sys', root / 'dev'), ())
                (entry / 'device/uevent').write_text('HID_ID=invalid\n')
                self.assertEqual(discover_wii_hid(root / 'sys', root / 'dev'), ())

    def test_namespace_mounts_only_known_permitted_generic_hid_devices(self):
        devices = (self.device(), self.device(accessible=False), self.device(driver='wiimote'))
        with patch('embercade.wii.discover_wii_hid', return_value=devices):
            self.assertEqual(wii_device_mounts(), ('--dev-bind', '/dev/hidraw42', '/dev/hidraw42'))
        with patch('embercade.wii.discover_wii_hid', return_value=()):
            self.assertEqual(wii_device_mounts(), ())

    def test_unconnected_dolphinbar_slot_falls_back_and_closes(self):
        with patch('embercade.wii.os.open', return_value=7), \
                patch('embercade.wii.os.fstat', return_value=SimpleNamespace(
                    st_mode=stat.S_IFCHR, st_rdev=self.device().device_number)), \
                patch('embercade.wii.os.write', side_effect=BrokenPipeError), \
                patch('embercade.wii.os.close') as close:
            self.assertFalse(_remote_responds(self.device()))
            close.assert_called_once_with(7)

    def test_connected_probe_is_only_status_request_and_closes(self):
        with patch('embercade.wii.os.open', return_value=7) as opened, \
                patch('embercade.wii.os.fstat', return_value=SimpleNamespace(
                    st_mode=stat.S_IFCHR, st_rdev=self.device().device_number)), \
                patch('embercade.wii.os.write', return_value=2) as write, \
                patch('embercade.wii.os.close') as close:
            self.assertTrue(_remote_responds(self.device()))
            self.assertTrue(opened.call_args.args[1] & os.O_NOFOLLOW)
            write.assert_called_once_with(7, b'\x15\x00')
            close.assert_called_once_with(7)

    def test_node_reuse_cannot_probe_a_foreign_device(self):
        with patch('embercade.wii.os.open', return_value=7), \
                patch('embercade.wii.os.fstat', return_value=SimpleNamespace(st_mode=stat.S_IFREG, st_rdev=0)), \
                patch('embercade.wii.os.write') as write, patch('embercade.wii.os.close') as close:
            self.assertFalse(_remote_responds(self.device()))
            write.assert_not_called()
            close.assert_called_once_with(7)

    def test_launch_reenumerates_after_disconnect_and_reconnect(self):
        with patch('embercade.wii.discover_wii_hid', side_effect=[(), (self.device(),), ()]), \
                patch('embercade.wii._remote_responds', return_value=True) as probe:
            self.assertFalse(real_wiimote_connected())
            self.assertTrue(real_wiimote_connected())
            self.assertFalse(real_wiimote_connected())
            probe.assert_called_once()

    def test_permissions_and_conflicting_driver_do_not_force_real_mode(self):
        with patch('embercade.wii.discover_wii_hid', return_value=(
                self.device(accessible=False), self.device(driver='wiimote'))), \
                patch('embercade.wii._remote_responds') as probe:
            self.assertFalse(real_wiimote_connected())
            probe.assert_not_called()

    def test_doctor_inventory_never_probes_or_claims_extension(self):
        with patch('embercade.wii.discover_wii_hid', return_value=(self.device(),)), \
                patch('embercade.wii.os.open') as opened:
            self.assertIn('require a game test', wii_hardware_summary())
            opened.assert_not_called()

    def test_absent_hardware_is_information_not_a_doctor_failure(self):
        from embercade.doctor import report
        from embercade.paths import EmbercadePaths
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'roms').mkdir()
            (root / 'bios').mkdir()
            paths = EmbercadePaths.from_environment({'HOME': directory}, config={
                'paths': {'roms': str(root / 'roms'), 'bios': str(root / 'bios')}})
            runtime = SimpleNamespace(installed_root=True)
            status = SimpleNamespace(available=True, python_version='test', imports={}, cli_error=None)
            stream = StringIO()
            with patch('embercade.wii.discover_wii_hid', return_value=()), \
                    patch('embercade.doctor.probe_runtime', return_value=status):
                result = report(paths, SimpleNamespace(probe_all=lambda: {}),
                                environment={}, runtime=runtime, stream=stream)
            self.assertEqual(result, 0)
            self.assertIn('No Wii Remote HID detected', stream.getvalue())


class WiiGeneratorTests(unittest.TestCase):
    def test_existing_ui_option_explains_auto_without_a_parallel_setting(self):
        from embercade.ui_data import _filter_desktop_features
        from xml.etree import ElementTree as ET
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'features.xml'
            file.write_text('<features><feature value="emulatedwiimotes" /></features>')
            _filter_desktop_features(file)
            feature = ET.parse(file).getroot()[0]
            self.assertEqual(feature.get('value'), 'emulatedwiimotes')
            self.assertIn('Auto uses a connected real Wii Remote', feature.get('description'))

    def test_pinned_generation_real_fallback_overrides_nunchuk_gamecube_and_isolation(self):
        from configparser import ConfigParser
        from embercade.controller import ControllerDevice
        from embercade.dolphin_dry_run import execute_dry_run
        from embercade.launcher import create_launch_plan, prepare_launch_layout
        from embercade.paths import EmbercadePaths
        from embercade.runtime import ProjectRuntime
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        self.assertTrue(runtime.launcher.is_file(), 'prepare the pinned runtime before testing')
        cases = [('wii', 'auto', True, 'real'), ('wii', 'auto', False, 'emulated'),
                 ('wii', 'true', True, 'emulated'), ('wii', 'false', False, 'real'),
                 ('wii', None, True, 'real'), ('gamecube', 'false', True, 'gamecube')]
        for system, selection, connected, expected in cases:
            with self.subTest(system=system, selection=selection, connected=connected), TemporaryDirectory() as directory:
                root = Path(directory)
                rom = root / 'RO ROMs' / system / 'Fixture.rvz'
                rom.parent.mkdir(parents=True)
                rom.write_bytes(b'Never execute synthetic content')
                fake = root / 'bin/dolphin-emu'
                fake.parent.mkdir()
                fake.write_text('#!/bin/sh\nexit 99\n')
                fake.chmod(0o755)
                environment = dict(os.environ) | {'HOME': str(root / 'host'),
                    'PATH': f'{fake.parent}:{os.environ.get("PATH", "")}',
                    'EMBERCADE_CONFIG_HOME': str(root / 'isolated/config'),
                    'EMBERCADE_DATA_HOME': str(root / 'isolated/data'),
                    'EMBERCADE_CACHE_HOME': str(root / 'isolated/cache'),
                    'EMBERCADE_STATE_HOME': str(root / 'isolated/state'),
                    'EMBERCADE_RUNTIME_HOME': str(root / 'isolated/runtime'),
                    'EMBERCADE_DISPLAY_WIDTH': '1920', 'EMBERCADE_DISPLAY_HEIGHT': '1080'}
                paths = EmbercadePaths.from_environment(environment, config={'paths': {'roms': str(rom.parent.parent)}})
                prepare_launch_layout(paths, project)
                # This is the existing Batocera setting, not a new selection file.
                paths.batocera_conf.write_text('wii.controller_mode=in\n' + (
                    f'wii.emulatedwiimotes={selection}\n' if selection else ''))
                before = paths.batocera_conf.read_bytes()
                host = root / 'host/.config/dolphin-emu/WiimoteNew.ini'
                host.parent.mkdir(parents=True)
                host.write_bytes(b'foreign host profile')
                controller = ControllerDevice(0, '030081b85e0400008e02000010010000',
                    'Xbox 360 Controller', Path('/dev/input/event42'), 11, 1, 6, 'mapping',
                    real_name='Microsoft X-Box 360 pad')
                with patch('embercade.wii.real_wiimote_connected', return_value=connected) as probe:
                    plan = create_launch_plan(system=system, rom=rom, paths=paths, runtime=runtime,
                        config={'input': {'exit_hotkey': 'guide-start'}}, environment=environment,
                        dry_run=True, controller=controller)
                    probe.assert_not_called()
                    if system == 'wii':
                        # Inject transport state into the structural generator;
                        # never probe a real remote or execute fixture content.
                        plan = replace(plan, environment=dict(plan.environment) | {
                            'EMBERCADE_WII_REAL_CONNECTED': '1' if connected else '0'})
                        row = execute_dry_run(plan, paths)
                        self.assertEqual(row['wiimote_mode'], expected)
                        self.assertEqual(row['special_controller_validation'], 'PENDING')
                    else:
                        result = subprocess.run(plan.command, env=dict(plan.environment), capture_output=True, text=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        probe.assert_not_called()
                        self.assertNotIn('EMBERCADE_WII_REAL_CONNECTED', plan.environment)
                config = paths.emulator_configs / 'dolphin-emu'
                parser = ConfigParser(interpolation=None, strict=False)
                parser.optionxform = str
                parser.read(config / ('GCPadNew.ini' if system == 'gamecube' else 'WiimoteNew.ini'), encoding='utf-8-sig')
                if expected == 'real':
                    self.assertEqual([parser.get(f'Wiimote{i}', 'Source') for i in range(1, 5)], ['2'] * 4)
                    self.assertFalse(parser.has_option('Wiimote1', 'Extension'))
                    self.assertTrue((config / 'GCPadNew.ini').exists())
                elif expected == 'emulated':
                    self.assertEqual(parser.get('Wiimote1', 'Source'), '1')
                    self.assertEqual(parser.get('Wiimote1', 'Extension'), 'Nunchuk')
                    self.assertTrue(parser.has_option('Wiimote1', 'Nunchuk/Buttons/C'))
                    self.assertTrue(parser.has_option('Wiimote1', 'Nunchuk/Buttons/Z'))
                    # Desktop gamepad fallback uses the physical Start/Back/
                    # Guide controls for Wii +, - and Home. RB is no longer +.
                    self.assertTrue(parser.has_option('Wiimote1', 'Buttons/+'))
                    self.assertTrue(parser.has_option('Wiimote1', 'Buttons/-'))
                    self.assertTrue(parser.has_option('Wiimote1', 'Buttons/Home'))
                    self.assertTrue(parser.has_option('Wiimote1', 'Shake/Z'))
                    self.assertNotEqual(parser.get('Wiimote1', 'Buttons/+'),
                                        parser.get('Wiimote1', 'Buttons/-'))
                    self.assertFalse(parser.has_option('Wiimote1', 'Buttons/Hotkey'))
                    self.assertFalse((config / 'GCPadNew.ini').exists())
                else:
                    self.assertTrue(parser.has_option('GCPad1', 'Buttons/A'))
                    self.assertFalse((config / 'WiimoteNew.ini').exists())
                self.assertEqual(host.read_bytes(), b'foreign host profile')
                self.assertEqual(paths.batocera_conf.read_bytes(), before)
                self.assertEqual(rom.read_bytes(), b'Never execute synthetic content')


if __name__ == '__main__':
    unittest.main()

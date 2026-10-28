"""Offline format vectors and transactional preservation; no synthetic image boots."""
import hashlib
import os
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from embercade import xbox_eeprom as e
from embercade.paths import EmbercadePaths


def fixture(version='1.0', identity=bytes(range(24))):
    # Deterministic synthetic codec data, never supplied to an emulator.
    data = bytearray(range(256))
    plain = identity + struct.pack('<I', 1)
    digest = e._digest(plain, version)
    data[:48] = digest + e._rc4(plain, e._digest(digest, version))
    struct.pack_into('<I', data, 0x90, 1)
    struct.pack_into('<I', data, 0x58, e.VIDEO['ntsc-m'])
    data[0x30:0x34] = e.checksum(data[0x34:0x60])
    data[0x60:0x64] = e.checksum(data[0x64:0xc0])
    return bytes(data)


class EepromTests(unittest.TestCase):
    def test_standard_sha1_and_rc4_independent_vectors(self):
        iv=(0x67452301,0xefcdab89,0x98badcfe,0x10325476,0xc3d2e1f0)
        for data in (b'', b'abc', bytes(range(256))):
            self.assertEqual(e._sha1_continue(data,iv,previous=0),hashlib.sha1(data).digest())
        self.assertEqual(e._rc4(b'Plaintext',b'Key').hex(),'bbf316e8d940af0ad3')

    def test_hardware_formats_authentication_and_settings_preserve_identity(self):
        for version in e._STATES:
            with self.subTest(version=version):
                original=fixture(version)
                self.assertEqual(e.inspect(original)['version'],version)
                changed=e.edit(original,language='de',region='europe',video='pal')
                self.assertEqual(e.inspect(changed),dict(version=version,language=3,region=4,video=e.VIDEO['pal']))
                self.assertEqual(e._validated(original)[1][:24],e._validated(changed)[1][:24])
                # Factory identity and serial/MAC, unused/user fields stay exact.
                self.assertEqual(original[0x34:0x58],changed[0x34:0x58])
                self.assertEqual(original[0x64:0x90],changed[0x64:0x90])
                self.assertEqual(original[0x94:],changed[0x94:])
                self.assertEqual(e.edit(changed,language='de',region='europe',video='pal'),changed)

    def test_language_change_leaves_encrypted_security_and_factory_exact(self):
        before=fixture();after=e.edit(before,language='de')
        self.assertEqual(before[:0x60],after[:0x60])
        self.assertEqual(e.edit(before),before)
        for offset in (0,20,0x30,0x60,0x90):
            broken=bytearray(before);broken[offset]^=1
            with self.assertRaises(e.EepromError): e.edit(bytes(broken),language='de')
        with self.assertRaises(e.EepromError): e.edit(before,language='fr')
        with self.assertRaises(e.EepromError): e.inspect(before+b'x')

    def test_import_requires_consent_backup_and_refuses_symlink(self):
        with TemporaryDirectory() as directory:
            target=Path(directory)/'eeprom.bin'
            original=fixture();changed=e.edit(fixture(identity=b'X'*24),language='de')
            self.assertNotEqual(e._validated(original)[1][:24],e._validated(changed)[1][:24])
            e.save(target,original)
            with self.assertRaises(e.EepromError):e.save(target,changed)
            backup=e.save(target,changed,replace=True)
            self.assertEqual(Path(backup).read_bytes(),original)
            self.assertEqual(Path(backup).stat().st_mode&0o777,0o600)
            self.assertEqual(e.read(target),changed)
            self.assertIsNone(e.save(target,changed,replace=True))
            target.unlink();target.symlink_to(backup)
            with self.assertRaises(e.EepromError): e.save(target,original,replace=True)
            with self.assertRaises(OSError): e.read(target)
            self.assertEqual(Path(backup).read_bytes(),original)

    def test_failed_atomic_write_keeps_original_and_backup(self):
        with TemporaryDirectory() as directory:
            target=Path(directory)/'eeprom.bin';target.write_bytes(fixture())
            with patch('embercade.xbox_eeprom.os.replace',side_effect=OSError('disk full')):
                with self.assertRaises(OSError):e.save(target,e.edit(fixture(),language='de'),replace=True)
            self.assertEqual(target.read_bytes(),fixture())
            self.assertEqual(len(list(target.parent.glob('*.backup-*'))),1)
            self.assertFalse(list(target.parent.glob('.eeprom-*')))

    def test_active_xemu_and_symlinked_state_refuse_mutation(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ,{'HOME':directory},clear=True):
            paths=EmbercadePaths.from_environment()
            with patch('embercade.xbox_eeprom._running',return_value=True):
                with self.assertRaises(e.EepromError):
                    with e.transaction(paths,Path('/usr/bin/xemu')):self.fail('must refuse')
            self.assertFalse(paths.saves.exists())
            paths.state.mkdir(parents=True,exist_ok=True)
            (paths.state/'installer/xemu.lock').unlink()
            (paths.state/'installer').rmdir()
            (paths.state/'installer').symlink_to(Path(directory))
            with self.assertRaises(e.EepromError):
                with e.transaction(paths,Path('/usr/bin/xemu')):self.fail('must refuse')

import hashlib
import io
import os
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from embercade.paths import EmbercadePaths
from embercade import ps3_firmware as p
from embercade.rpcs3 import Rpcs3RuntimeError, firmware_version


def pup_bytes():
    # Structure-only fixture; a mocked native boundary handles it, never RPCS3.
    return b'SCEUF\0\0\0'+struct.pack('>5Q',1,1,1,112,16)+b'\0'*80


class Response(io.BytesIO):
    def __init__(self,data,url):super().__init__(data);self.url=url
    def geturl(self):return self.url


class FirmwareTests(unittest.TestCase):
    def test_official_source_and_reject_credentials_query_other_host(self):
        self.assertEqual(p.official_url(p.OFFICIAL_PAGE,page=True),p.OFFICIAL_PAGE)
        for url in ('https://evil.example/PS3UPDAT.PUP','http://www.playstation.com/a',
                    'https://user@dus01.ps3.update.playstation.net/a',
                    'https://dus01.ps3.update.playstation.net/a?q=1'):
            with self.assertRaises(p.FirmwareError):p.official_url(url)

    def test_pup_structure_size_magic_and_symlink(self):
        with TemporaryDirectory() as directory:
            file=Path(directory)/'PUP';file.write_bytes(pup_bytes())
            self.assertEqual(p.verify_pup(file),hashlib.sha256(pup_bytes()).hexdigest())
            for broken in (b'bad',pup_bytes()[:-1],b'x'+pup_bytes()[1:]):
                file.write_bytes(broken)
                with self.assertRaises(p.FirmwareError):p.verify_pup(file)
            link=file.with_name('link');link.symlink_to(file)
            with self.assertRaises(OSError):p.verify_pup(link)

    def test_download_requires_page_digest_reuses_cache_and_cleans_failure(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ,{'HOME':directory},clear=True):
            paths=EmbercadePaths.from_environment();data=pup_bytes();digest=hashlib.md5(data).hexdigest()
            url=f'http://dus01.ps3.update.playstation.net/update/ps3/image/us/2026_0101_{digest}/PS3UPDAT.PUP'
            class Opener:
                requests=[];broken=False
                def open(self,request,**kw):
                    self.requests.append(request.full_url)
                    return Response(f'<a href="{url}">Download</a>'.encode() if request.full_url==p.OFFICIAL_PAGE else b'broken' if self.broken else data, request.full_url)
            opener=Opener();file=p.download(paths,opener=opener)
            self.assertEqual(file.read_bytes(),data)
            before=file.stat().st_mtime_ns
            self.assertEqual(p.download(paths,opener=opener),file)
            self.assertEqual(file.stat().st_mtime_ns,before)
            self.assertEqual(opener.requests.count(url),1)
            file.unlink();opener.broken=True
            with self.assertRaises(p.FirmwareError):p.download(paths,opener=opener)
            self.assertFalse(list(file.parent.iterdir()))

    def test_native_failure_and_retry_never_touch_existing_profile(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ,{'HOME':directory},clear=True), patch('embercade.xbox_eeprom._running',return_value=False):
            paths=EmbercadePaths.from_environment();file=Path(directory)/'PUP';file.write_bytes(pup_bytes())
            target=paths.emulator_configs/'rpcs3';target.mkdir(parents=True)
            (target/'config.yml').write_text('keep user settings')
            def failed(executable,private,*args,**kwargs):
                partial=private.emulator_configs/'rpcs3/dev_flash';partial.mkdir(parents=True)
                raise Rpcs3RuntimeError('cancelled')
            with patch('embercade.ps3_firmware.open_firmware_installer',side_effect=failed):
                with self.assertRaises(Rpcs3RuntimeError):p.install(Path('/rpcs3'),paths,{},os.environ,file)
            self.assertFalse((target/'dev_flash').exists())
            def success(executable,private,*args,**kwargs):
                self.assertNotEqual(private.emulator_configs,paths.emulator_configs)
                for name in ('dev_flash','dev_flash2','dev_flash3'):(private.emulator_configs/'rpcs3'/name).mkdir(parents=True)
                version=private.emulator_configs/'rpcs3/dev_flash/vsh/etc/version.txt'
                version.parent.mkdir(parents=True);version.write_text('release:04.9300:synthetic\n')
            with patch('embercade.ps3_firmware.open_firmware_installer',side_effect=success) as native:
                self.assertEqual(p.install(Path('/rpcs3'),paths,{},os.environ,file),'04.9300')
                with self.assertRaises(p.FirmwareError):p.install(Path('/rpcs3'),paths,{},os.environ,file)
                self.assertEqual(native.call_count,1)
            self.assertEqual((target/'config.yml').read_text(),'keep user settings')
            self.assertEqual(firmware_version(target),'04.9300')
            self.assertFalse(list((paths.cache/'installer').glob('ps3-install-*')))

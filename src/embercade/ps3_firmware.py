"""Consent-driven official PUP retrieval and the existing isolated RPCS3 installer.

Firmware is external user data, never part of Stage or the AppImage. The trusted
HTTPS page's content digest and PUP structure are checked; RPCS3 validates content.
"""
from __future__ import annotations

import hashlib
from dataclasses import replace
from html.parser import HTMLParser
import fcntl
import shutil
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from embercade.rpcs3 import firmware_version, open_firmware_installer, Rpcs3RuntimeError

OFFICIAL_PAGE = 'https://www.playstation.com/en-us/support/hardware/ps3/system-software/'
MAX_PUP = 512 * 1024 * 1024


class FirmwareError(ValueError):
    pass


def official_url(url: str, *, page=False) -> str:
    parsed = urlsplit(url)
    host = parsed.hostname or ''
    allowed = host == 'www.playstation.com' if page else bool(re.fullmatch(r'd[a-z0-9]+\.ps3\.update\.playstation\.net', host))
    if (not allowed or parsed.scheme not in (('https',) if page else ('http','https'))
            or parsed.username or parsed.password
            or parsed.port not in (None,443 if parsed.scheme == 'https' else 80)
            or parsed.query or parsed.fragment):
        raise FirmwareError('Unexpected firmware source; use the official PlayStation page')
    return url


class _Redirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        official_url(newurl, page=urlsplit(newurl).hostname == 'www.playstation.com')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag != 'a': return
        link = dict(attrs).get('href', '')
        parsed = urlsplit(link)
        if parsed.path.endswith('/PS3UPDAT.PUP'):
            # Use the link from the authenticated official page. Sony's HTTP
            # download endpoint currently has no valid HTTPS certificate. No
            # TLS verification bypass; its page-published content digest is
            # mandatory before any downloaded bytes are installed.
            self.links.add(official_url(link))


def verify_pup(path: Path) -> str:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or not 48 <= info.st_size <= MAX_PUP:
            raise FirmwareError('PUP file is unreadable or has an invalid size')
        header = stream.read(48)
        if header[:8] != b'SCEUF\0\0\0': raise FirmwareError('File is not a PS3 update package')
        # Six big-endian 64-bit fields: magic, package/image versions, entry
        # count, header length and data length (RPCS3 Loader/PUP.h).
        _, _, _, entries, header_size, data_size = struct.unpack('>6Q', header)
        if not 0 < entries < 4096 or header_size < 48 + entries * 64 or header_size + data_size != info.st_size:
            raise FirmwareError('PS3 update package header is inconsistent')
        stream.seek(0)
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download(paths, *, opener=None) -> Path:
    paths.validate_application_boundary(os.environ)
    opener = opener or build_opener(_Redirect())
    request = lambda url: Request(url, headers={'User-Agent': 'Embercade/1.0'})
    with opener.open(request(OFFICIAL_PAGE), timeout=30) as response:
        official_url(response.geturl(), page=True)
        html = response.read(2*1024*1024+1)
    if len(html)>2*1024*1024: raise FirmwareError('Official firmware page is too large')
    parser = _Links(); parser.feed(html.decode('utf-8'))
    if len(parser.links) != 1: raise FirmwareError('Official firmware download link could not be verified')
    url = parser.links.pop()
    match = re.search(r'/\d{4}_\d{4}_([a-fA-F0-9]{32})/PS3UPDAT\.PUP$', urlsplit(url).path)
    if not match: raise FirmwareError('Official download link has no verifiable content digest')
    expected = match.group(1).lower()
    folder = paths.cache / 'firmware/ps3'
    if any(p.is_symlink() for p in (folder,*folder.parents)): raise FirmwareError('Unsafe firmware cache')
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = folder / (expected + '.PUP')
    if target.exists() or target.is_symlink():
        verify_pup(target)
        if hashlib.md5(target.read_bytes()).hexdigest() != expected:
            raise FirmwareError('Existing cached firmware failed integrity verification')
        return target
    fd, name = tempfile.mkstemp(prefix='.download-', dir=folder)
    temporary = Path(name)
    try:
        digest = hashlib.md5(); size = 0
        with os.fdopen(fd, 'wb') as stream, opener.open(request(url), timeout=45) as response:
            official_url(response.geturl())
            while block := response.read(1024*1024):
                size += len(block)
                if size > MAX_PUP: raise FirmwareError('Firmware download exceeds the size limit')
                digest.update(block); stream.write(block)
            stream.flush(); os.fsync(stream.fileno())
        if digest.hexdigest() != expected: raise FirmwareError('Official firmware download failed integrity verification')
        verify_pup(temporary)
        # Link is exclusive: a concurrent operation never overwrites user data.
        os.link(temporary, target)
        return target
    finally: temporary.unlink(missing_ok=True)


def install(executable, paths, config, environment, pup: Path):
    """Native validation in disposable state, then activate only firmware trees.

    Failed/cancelled native installs never leave a partial active profile and
    retry uses a fresh temporary directory. Existing profiles are not opened.
    """
    paths.validate_application_boundary(environment)
    isolated = paths.emulator_configs / 'rpcs3'
    for location in (isolated, paths.cache / 'installer', paths.state / 'installer'):
        if any(p.is_symlink() for p in (location, *location.parents)):
            raise FirmwareError('Unsafe isolated firmware directory')
        location.mkdir(parents=True, exist_ok=True, mode=0o700)
    from embercade.xbox_eeprom import _running
    if _running(executable): raise FirmwareError('Close RPCS3 before installing firmware')
    lock = os.open(paths.state / 'installer/ps3.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    activated = []
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if firmware_version(isolated):
            raise FirmwareError('Isolated PS3 firmware is already installed; no replacement performed')
        names = ('dev_flash', 'dev_flash2', 'dev_flash3')
        if any((isolated/name).exists() or (isolated/name).is_symlink() for name in names):
            raise FirmwareError('Existing isolated firmware files require inspection; nothing overwritten')
        verify_pup(pup)
        with tempfile.TemporaryDirectory(prefix='ps3-install-', dir=paths.cache/'installer') as directory:
            root = Path(directory)
            private = replace(paths, config=root/'config', data=root/'data',
                              cache=root/'cache', state=root/'state')
            open_firmware_installer(executable, private, {}, environment, pup=pup)
            source = private.emulator_configs/'rpcs3'
            version = firmware_version(source)
            if not version or not all((source/name).is_dir() for name in names):
                raise FirmwareError('Native RPCS3 firmware installation is incomplete or was cancelled')
            # Stage beside targets, so activation never depends on cross-device rename.
            with tempfile.TemporaryDirectory(prefix='.firmware-', dir=isolated) as staging:
                for name in names:
                    shutil.copytree(source/name, Path(staging)/name, symlinks=False)
                for name in names:
                    target = isolated/name
                    if target.exists() or target.is_symlink():
                        raise FirmwareError('Firmware target changed during installation')
                    (Path(staging)/name).rename(target)
                    activated.append(target)
            return version
    except BaseException:
        for target in reversed(activated): shutil.rmtree(target)
        raise
    finally: os.close(lock)

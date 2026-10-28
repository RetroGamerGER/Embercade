"""Offline EEPROM inspection/editing; no keys or identity fields leave this module.

Format references: Xemu eeprom_generation.{c,h} at 478b4f496102379c7eaa7f3ec10e714a703c4300.
The public SHA-1 continuation states identify the Xbox EEPROM hardware formats.
An edit starts from an authenticated image and preserves its identity/HDD key.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hmac
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import tempfile
import uuid

from embercade.xemu import isolated_xemu_files


class EepromError(ValueError):
    pass


_STATES = {
    '1.0': ((0x72127625,0x336472B9,0xBE609BEA,0xF55E226B,0x99958DAC),
            (0x76441D41,0x4DE82659,0x2E8EF85E,0xB256FACA,0xC4FE2DE8)),
    '1.1–1.4': ((0x39B06E79,0xC9BD25E8,0xDBC6B498,0x40B4389D,0x86BBD7ED),
                (0x9B49BED3,0x84B430FC,0x6B8749CD,0xEBFE5FE5,0xD96E7393)),
    '1.6': ((0x8058763A,0xF97D4E0E,0x865A9762,0x8A3D920D,0x08995B2C),
            (0x01075307,0xA2F1E037,0x1186EEEA,0x88DA9992,0x168A5609)),
    'debug': ((0x85F9E51A,0xE04613D2,0x6D86A50C,0x77C32E3C,0x4BD717A4),
              (0x5D7A9C6B,0xE1922BEB,0xB82CCDBC,0x3137AB34,0x486B52B3)),
}
LANGUAGES = {'en': 1, 'de': 3}
REGIONS = {'north-america': 1, 'japan': 2, 'europe': 4}
VIDEO = {'ntsc-m': 0x00400100, 'ntsc-j': 0x00400200, 'pal': 0x00800300}


def _sha1_continue(data: bytes, state: tuple[int, ...], previous=64) -> bytes:
    """Standard SHA-1 compression starting after an already hashed full block."""
    rotate = lambda n, bits: ((n << bits) | (n >> (32 - bits))) & 0xffffffff
    padded = data + b'\x80'
    padded += b'\0' * ((56 - len(padded) % 64) % 64)
    padded += struct.pack('>Q', (previous + len(data)) * 8)
    state = list(state)
    for offset in range(0, len(padded), 64):
        words = list(struct.unpack('>16I', padded[offset:offset+64]))
        for i in range(16, 80):
            words.append(rotate(words[i-3] ^ words[i-8] ^ words[i-14] ^ words[i-16], 1))
        a,b,c,d,e = state
        for i, word in enumerate(words):
            if i < 20: f, k = (b & c) | (~b & d), 0x5a827999
            elif i < 40: f, k = b ^ c ^ d, 0x6ed9eba1
            elif i < 60: f, k = (b & c) | (b & d) | (c & d), 0x8f1bbcdc
            else: f, k = b ^ c ^ d, 0xca62c1d6
            a,b,c,d,e = (rotate(a,5) + f + e + k + word) & 0xffffffff, a, rotate(b,30), c, d
        state = [(v + w) & 0xffffffff for v,w in zip(state, (a,b,c,d,e))]
    return struct.pack('>5I', *state)


def _digest(data: bytes, version: str) -> bytes:
    inner, outer = _STATES[version]
    return _sha1_continue(_sha1_continue(data, inner), outer)


def _rc4(data: bytes, key: bytes) -> bytes:
    table = list(range(256)); j = 0
    for i in range(256):
        j = (j + table[i] + key[i % len(key)]) % 256
        table[i], table[j] = table[j], table[i]
    result = bytearray(); i = j = 0
    for value in data:
        i = (i + 1) % 256; j = (j + table[i]) % 256
        table[i], table[j] = table[j], table[i]
        result.append(value ^ table[(table[i] + table[j]) % 256])
    return bytes(result)


def checksum(data: bytes) -> bytes:
    total = sum(struct.unpack('<' + 'I' * (len(data) // 4), data))
    return struct.pack('<I', ~((total & 0xffffffff) + (total >> 32)) & 0xffffffff)


def _validated(data: bytes) -> tuple[str, bytes]:
    if len(data) != 256:
        raise EepromError('EEPROM must contain exactly 256 bytes')
    if data[0x30:0x34] != checksum(data[0x34:0x60]) or data[0x60:0x64] != checksum(data[0x64:0xc0]):
        raise EepromError('EEPROM checksum validation failed')
    for version in _STATES:
        plain = _rc4(data[20:48], _digest(data[:20], version))
        if hmac.compare_digest(_digest(plain, version), data[:20]):
            return version, plain
    raise EepromError('EEPROM security authentication failed; no changes made')


def inspect(data: bytes) -> dict:
    version, plain = _validated(data)
    return dict(version=version, language=struct.unpack_from('<I', data, 0x90)[0],
                region=struct.unpack_from('<I', plain, 24)[0],
                video=struct.unpack_from('<I', data, 0x58)[0])


def edit(data: bytes, *, language='keep', region='keep', video='keep') -> bytes:
    version, plain = _validated(data)
    output = bytearray(data)
    for choice, allowed in ((language,LANGUAGES), (region,REGIONS), (video,VIDEO)):
        if choice != 'keep' and choice not in allowed:
            raise EepromError('Unsupported EEPROM setting')
    if language != 'keep': struct.pack_into('<I', output, 0x90, LANGUAGES[language])
    if video != 'keep': struct.pack_into('<I', output, 0x58, VIDEO[video])
    if region != 'keep' and struct.unpack_from('<I', plain, 24)[0] != REGIONS[region]:
        changed = plain[:24] + struct.pack('<I', REGIONS[region])
        digest = _digest(changed, version)
        output[:48] = digest + _rc4(changed, _digest(digest, version))
    output[0x30:0x34] = checksum(output[0x34:0x60])
    output[0x60:0x64] = checksum(output[0x64:0xc0])
    _, verified = _validated(bytes(output))
    if verified[:24] != plain[:24]:
        raise EepromError('Console identity preservation check failed')
    return bytes(output)


def read(path: Path) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise EepromError('EEPROM must be a regular file')
        data = stream.read(257)
    _validated(data)
    return data


def _directory(path: Path):
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise EepromError('Unsafe EEPROM state directory')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)


def _running(executable: Path) -> bool:
    for process in Path('/proc').iterdir():
        if not process.name.isdigit(): continue
        try:
            if process.stat().st_uid == os.getuid() and (process / 'exe').resolve(strict=True) == executable.resolve():
                return True
        except OSError: pass
    return False


@contextmanager
def transaction(paths, executable: Path):
    paths.validate_application_boundary(os.environ)
    _directory(paths.state / 'installer')
    fd = os.open(paths.state / 'installer/xemu.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise EepromError('Unsafe EEPROM lock')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if _running(executable): raise EepromError('Close Xemu before changing its EEPROM')
        target = isolated_xemu_files(paths).eeprom
        _directory(target.parent)
        yield target
    finally:
        os.close(fd)


def _atomic(target: Path, data: bytes):
    fd, name = tempfile.mkstemp(prefix='.eeprom-', dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally: temporary.unlink(missing_ok=True)


def save(target: Path, data: bytes, *, replace=False) -> str | None:
    """Called under transaction lock; backup old bytes before atomic replacement."""
    _validated(data)
    if target.is_symlink(): raise EepromError('Refusing symlinked EEPROM')
    backup = None
    if target.exists():
        if not replace: raise EepromError('Existing EEPROM requires explicit replacement confirmation')
        original = read(target)
        if original == data: return None
        backup = target.with_name(target.name + '.backup-' + uuid.uuid4().hex)
        fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(original); stream.flush(); os.fsync(stream.fileno())
    _atomic(target, data)
    return str(backup) if backup else None


def initialize(paths, executable: Path, environment: dict) -> dict:
    """Let native Xemu create its EEPROM without booting firmware or a game."""
    with transaction(paths, executable) as target:
        if target.exists(): return inspect(read(target))
        _directory(paths.cache / 'installer')
        with tempfile.TemporaryDirectory(prefix='xemu-init-', dir=paths.cache / 'installer') as directory:
            root = Path(directory)
            env = dict(environment)
            for key in ('HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME'):
                location = root / key; location.mkdir(); env[key] = str(location)
            config = root / 'xemu.toml'
            config.write_text('[sys.files]\neeprom_path = ' + json.dumps(str(target)) + '\n')
            result = subprocess.run([str(executable), '-config_path', str(config), '--version'],
                                    env=env, capture_output=True, timeout=30)
            if result.returncode: raise EepromError('Xemu could not initialize the isolated EEPROM')
        return inspect(read(target))

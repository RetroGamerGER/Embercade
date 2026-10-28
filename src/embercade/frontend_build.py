"""ScreenScraper build authorization; RetroAchievements uses runtime user keys.

Compiled application credentials are extractable. Private inputs/headers/objects
are build material, not source archives or diagnostics. Only the frontend and
value-free build identity enter the Stage.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from urllib.parse import quote

BUILD_SECRET_ENV = 'EMBERCADE_SCREENSCRAPER_BUILD_SECRET_FILE'
MARKER = b'EMBERCADE_SCREENSCRAPER_EMBEDDED_V1'
INFO_NAME = 'frontend-build.json'
KEYS = ('SCREENSCRAPER_DEV_ID', 'SCREENSCRAPER_DEV_PASSWORD')
RA_SECRET_ENV = 'EMBERCADE_RETROACHIEVEMENTS_BUILD_SECRET_FILE'
RA_MARKER = b'EMBERCADE_RETROACHIEVEMENTS_PRIVATE_WEB_API_V1'
RA_USER_MARKER = b'EMBERCADE_RETROACHIEVEMENTS_USER_WEB_API_V1'


class FrontendBuildError(ValueError):
    pass


def _secret(path: Path | None, *, keys=KEYS) -> dict[str, str]:
    if path is None:
        raise FrontendBuildError('Production frontend requires its private ScreenScraper build source. Set '+BUILD_SECRET_ENV+' to an owner-only file; no values belong in arguments.')
    try:
        parent = path.parent.lstat()
        if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o077:
            raise OSError('private parent required')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > 16384:
                raise OSError('private regular file required')
            raw = stream.read(16385)
        if len(raw) > 16384 or b'\0' in raw:
            raise ValueError()
        values = {}
        for line in raw.decode('utf-8').splitlines():
            if not line or line.startswith('#'):
                continue
            key, separator, value = line.partition('=')
            if not separator or key not in keys or key in values:
                raise ValueError()
            if not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise ValueError()
            values[key] = value
        if set(values) != set(keys):
            raise ValueError()
        return values
    except (OSError, UnicodeError, ValueError):
        raise FrontendBuildError('Private ScreenScraper build source is missing, unsafe or incomplete. Exactly the two developer fields are required; personal/debug fields are not build inputs.') from None


def developer_query(values: dict[str, str]) -> str:
    return 'devid='+quote(values[KEYS[0]], safe='')+'&devpassword='+quote(values[KEYS[1]], safe='')


def _runtime_ra_only(source: Path | None) -> None:
    if source is not None:
        raise FrontendBuildError('Build-time RetroAchievements keys are no longer supported. Configure a personal key in the frontend settings.')


def _write_private(path: Path, content: bytes) -> None:
    if path.is_symlink():
        raise FrontendBuildError('Refusing a symlinked build artifact')
    if path.exists():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise FrontendBuildError('Refusing an unsafe build artifact')
    if path.exists() and path.read_bytes() == content:
        path.chmod(0o600)
        return
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(content)


def prepare(project: Path, source: Path | None, *, development: bool = False, retroachievements_source: Path | None = None) -> Path:
    _runtime_ra_only(retroachievements_source)
    ui = project / '.work/ui'
    if (project / '.work').is_symlink() or ui.is_symlink():
        raise FrontendBuildError('Refusing a symlinked build workspace')
    ui.mkdir(parents=True, exist_ok=True)
    ui.chmod(0o700)
    private = ui / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    if private.is_symlink():
        raise FrontendBuildError('Refusing a symlinked private build directory')
    private.chmod(0o700)
    query = None if development else developer_query(_secret(source))
    lines = ['#pragma once', '// Generated private application authorization; do not redistribute this header.']
    if query:
        lines.append('#define SCREENSCRAPER_DEV_LOGIN '+json.dumps(query))
    else:
        lines.append('// Explicit development build without application authorization.')
    header = private / 'ScreenScraperAuthorization.h'
    _write_private(header, ('\n'.join(lines)+'\n').encode())
    return header


def file_digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def finalize(project: Path, source: Path | None, *, development: bool = False, retroachievements_source: Path | None = None) -> dict:
    _runtime_ra_only(retroachievements_source)
    frontend = project / '.work/ui/es-source/emulationstation'
    if frontend.is_symlink():
        raise FrontendBuildError('Refusing a symlinked frontend binary')
    data = frontend.read_bytes()
    if development:
        if MARKER in data:
            raise FrontendBuildError('Development frontend is stale: compiled authorization remains')
    elif MARKER not in data or developer_query(_secret(source)).encode() not in data:
        raise FrontendBuildError('New frontend does not contain the intended application authorization; rebuild required')
    frontend.chmod(0o755)  # Its containing build directory remains private.
    if RA_MARKER in data or RA_USER_MARKER not in data:
        raise FrontendBuildError('Frontend requires the per-user RetroAchievements implementation and must contain no compiled shared key')
    info = dict(format=1, software='Embercade', authorization='development-local' if development else 'embedded',
                frontend_sha256=file_digest(frontend), retroachievements_authorization='per-user-web-api')
    _write_private(project / '.work/ui' / INFO_NAME, (json.dumps(info, sort_keys=True)+'\n').encode())
    return info


def verify_frontend(frontend: Path, metadata: Path, *, development: bool = False) -> dict:
    try:
        if metadata.is_symlink() or frontend.is_symlink():
            raise ValueError()
        info = json.loads(metadata.read_text())
        base = {'format','software','authorization','frontend_sha256','retroachievements_authorization'}
        if (set(info) != base or info['format'] != 1
                or info['software'] != 'Embercade' or info['frontend_sha256'] != file_digest(frontend)):
            raise ValueError()
        embedded = info['authorization'] == 'embedded'
        if info['authorization'] not in ('embedded','development-local') or (not embedded and not development):
            raise ValueError()
        if (MARKER in frontend.read_bytes()) != embedded:
            raise ValueError()
        data = frontend.read_bytes()
        if (RA_MARKER in data or RA_USER_MARKER not in data
                or info['retroachievements_authorization'] != 'per-user-web-api'):
            raise ValueError()
        return info
    except (OSError, TypeError, ValueError):
        raise FrontendBuildError('Frontend authorization/build identity is missing or stale. Production packaging requires the newly built embedded-authorization frontend; credential-free development must be explicitly selected.') from None


def sanitized_run(command: list[str], source: Path | None, *, development=False, retroachievements_source: Path | None = None) -> int:
    _runtime_ra_only(retroachievements_source)
    values = {} if development else _secret(source)
    sensitive = sorted({value for v in values.values() for value in (v, quote(v, safe=''))}, key=len, reverse=True)
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace') as process:
        for line in process.stdout:
            for value in sensitive:
                line = line.replace(value, '[REDACTED]')
            print(line, end='', flush=True)
        return process.wait()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','finalize','run'))
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--development-without-screenscraper', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    source = Path(os.environ[BUILD_SECRET_ENV]) if os.environ.get(BUILD_SECRET_ENV) else None
    try:
        ra_source = Path(os.environ[RA_SECRET_ENV]) if os.environ.get(RA_SECRET_ENV) else None
        _runtime_ra_only(ra_source)
        if args.action == 'run':
            command = args.command[1:] if args.command[:1] == ['--'] else args.command
            if not command:
                raise FrontendBuildError('Build command required')
            return sanitized_run(command, source, development=args.development_without_screenscraper, retroachievements_source=ra_source)
        if args.action == 'prepare':
            print(prepare(args.project_root, source, development=args.development_without_screenscraper, retroachievements_source=ra_source))
        else:
            finalize(args.project_root, source, development=args.development_without_screenscraper, retroachievements_source=ra_source)
            print('Frontend build identity verified; no credential values in metadata.')
        return 0
    except (OSError, FrontendBuildError):
        # Never render OS/source contents or a secret-bearing compiler diagnostic here.
        print('Frontend build authorization is unavailable or invalid; check the private two-field build source and explicit build mode.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

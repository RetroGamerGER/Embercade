"""User-local AppImage/menu integration with explicit ownership and rollback.

Classic installations continue to use install_user and its existing manifest.
An AppImage can be retained at a stable local filename independent of its source.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import fcntl
import subprocess
import tempfile

from embercade.installer import UserInstallPaths, install_user, _desktop_exec_quote
from embercade.version import FRONTEND_PRODUCT_LABEL


class DesktopError(ValueError):
    pass


def _safe(path: Path):
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise DesktopError('Desktop integration target is symlinked')


def _hash(path: Path) -> str:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise DesktopError('Integration requires regular files')
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _desktop_folder(env):
    home = Path(env.get('HOME',str(Path.home()))).expanduser().absolute()
    executable = shutil.which('xdg-user-dir', path=env.get('PATH',''))
    if executable:
        result = subprocess.run([executable,'DESKTOP'], env=dict(env), capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            folder = Path(result.stdout.strip())
            if folder.is_absolute() and folder != home and folder.is_relative_to(home): return folder
    # No assumption about a translated Desktop directory when xdg-user-dir is
    # unavailable: its existing per-user configuration remains authoritative.
    config = Path(env.get('XDG_CONFIG_HOME',home/'.config'))/'user-dirs.dirs'
    if config.is_file():
        for line in config.read_text().splitlines():
            if line.startswith('XDG_DESKTOP_DIR="') and line.endswith('"'):
                text = line[len('XDG_DESKTOP_DIR="'):-1].replace('$HOME',str(home))
                folder = Path(text)
                if folder.is_absolute() and folder != home and folder.is_relative_to(home): return folder
    raise DesktopError('No Desktop folder is configured; use the application menu or configure it in your desktop settings')


def integrate(environment, *, menu=True, shortcut=False, local_image=True) -> dict:
    from embercade.paths import EmbercadePaths
    EmbercadePaths.from_environment(environment).validate_application_boundary(environment)
    paths = UserInstallPaths.from_environment(environment)
    EmbercadePaths.from_environment(environment).validate_application_boundary(environment,
        targets=(paths.state_root, paths.icon, paths.desktop_entry, paths.data_root))
    _safe(paths.state_root)
    paths.state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(paths.state_root/'desktop.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise DesktopError('Invalid desktop integration lock')
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _integrate(environment, menu=menu, shortcut=shortcut, local_image=local_image)
    finally: os.close(fd)


def _integrate(environment, *, menu=True, shortcut=False, local_image=True) -> dict:
    env = dict(environment)
    paths = UserInstallPaths.from_environment(env)
    prefix = Path(env.get('EMBERCADE_PREFIX',''))
    if not env.get('EMBERCADE_PREFIX'):
        raise DesktopError('Desktop integration requires an installed Embercade or its AppImage')
    if env.get('EMBERCADE_APPIMAGE') != '1':
        if prefix.resolve() != paths.prefix.resolve():
            raise DesktopError('Use the installed application for desktop integration')
        launcher = paths.launcher
    else:
        image = Path(env.get('APPIMAGE',''))
        appdir = Path(env.get('APPDIR',''))
        if not image.is_absolute() or prefix.resolve() != (appdir/'usr').resolve():
            raise DesktopError('Invalid mounted AppImage environment')
        _safe(image)
        with image.open('rb') as stream: header = stream.read(16)
        if (header[:4]!=b'\x7fELF' or header[8:11]!=b'AI\x02'
                or image.stat().st_uid!=os.getuid() or not os.access(image,os.X_OK)):
            raise DesktopError('Use the user-owned executable Embercade AppImage')
        launcher = paths.data_root/'application/Embercade.AppImage' if local_image else image

    state = paths.state_root/'desktop-integration.json'
    _safe(state)
    prior = json.loads(state.read_text()) if state.is_file() else {'files':{}}
    if prior.get('format',1)!=1 or not isinstance(prior.get('files'),dict):
        raise DesktopError('Invalid desktop integration manifest')
    icon_source = prefix/'share/embercade/resources/branding/icon/embercade-512.png'
    if not icon_source.is_file(): raise DesktopError('Original Embercade icon is unavailable')
    text = ('[Desktop Entry]\nType=Application\nName='+FRONTEND_PRODUCT_LABEL+'\n'
            'Exec='+_desktop_exec_quote(launcher)+'\nIcon=embercade\n'
            'Categories=Game;Emulator;\nTerminal=false\nStartupNotify=true\nStartupWMClass=embercade\n'
            'X-Embercade-Managed=appimage\n')
    targets = {paths.icon:icon_source}
    if menu: targets[paths.desktop_entry]=text.encode()
    if shortcut: targets[_desktop_folder(env)/'embercade.desktop']=text.encode()
    if env.get('EMBERCADE_APPIMAGE')=='1' and local_image: targets[launcher]=image

    # Preserve the classic installer's ownership and launcher. Verify it with
    # its existing installer; the wizard never upgrades a running installation.
    if paths.manifest.is_file():
        install_user(paths.prefix, environment=env, dry_run=True)
        launcher = paths.launcher
        local_image = False
        text = paths.desktop_entry.read_bytes()
        targets = {}
        if shortcut: targets[_desktop_folder(env)/'embercade.desktop'] = text
    elif env.get('EMBERCADE_APPIMAGE') != '1':
        raise DesktopError('No verified classic installation was found')

    for target, source in targets.items():
        _safe(target)
        if target.exists():
            digest = _hash(target)
            new_digest = hashlib.sha256(source).hexdigest() if isinstance(source,bytes) else _hash(source)
            if digest != new_digest and prior['files'].get(str(target)) != digest:
                raise DesktopError('An integration file already exists and is not managed or has changed; nothing overwritten')
    operations=[]
    pending=[]
    try:
        for target, source in targets.items():
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists() and _hash(target)==(hashlib.sha256(source).hexdigest() if isinstance(source,bytes) else _hash(source)):
                continue
            fd,name=tempfile.mkstemp(prefix='.embercade-integration-',dir=target.parent)
            temporary=Path(name)
            pending.append(temporary)
            with os.fdopen(fd,'wb') as stream:
                if isinstance(source,bytes): stream.write(source)
                else:
                    with source.open('rb') as original: shutil.copyfileobj(original,stream)
                stream.flush();os.fsync(stream.fileno())
            expected = hashlib.sha256(source).hexdigest() if isinstance(source,bytes) else _hash(source)
            if _hash(temporary) != expected: raise DesktopError('Source changed while copying; retry integration')
            temporary.chmod(0o755 if target==launcher or target.suffix=='.desktop' else 0o644)
            backup=None
            if target.exists():
                backup=temporary.with_suffix('.previous');os.replace(target,backup)
            operations.append((target,temporary,backup))
            os.replace(temporary,target)
        state.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        fd,name=tempfile.mkstemp(prefix='.desktop-manifest-',dir=state.parent)
        temporary=Path(name)
        pending.append(temporary)
        files=dict(prior['files']);files.update({str(p):_hash(p) for p in targets})
        with os.fdopen(fd,'w') as stream:
            json.dump(dict(format=1,files=files,launcher=str(launcher)),stream,indent=2)
            stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,state)
    except BaseException:
        for target,temporary,backup in reversed(operations):
            target.unlink(missing_ok=True)
            if backup:os.replace(backup,target)
            temporary.unlink(missing_ok=True)
        raise
    finally:
        for temporary in pending: temporary.unlink(missing_ok=True)
    for _,_,backup in operations:
        if backup:backup.unlink(missing_ok=True)
    updater=shutil.which('update-desktop-database',path=env.get('PATH',''))
    if updater and menu:subprocess.run([updater,str(paths.desktop_entry.parent)],env=env,capture_output=True,check=False)
    return dict(launcher=str(launcher),menu=menu,shortcut=shortcut,local_image=local_image)

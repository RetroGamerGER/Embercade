import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from embercade.desktop_integration import integrate, DesktopError
from embercade.installer import UserInstallPaths


class DesktopIntegrationTests(unittest.TestCase):
    def environment(self,root):
        image=root/'source drive/Embercade.AppImage';image.parent.mkdir();image.write_bytes(b'\x7fELF'+b'\0'*4+b'AI\x02'+b'\0'*32);image.chmod(0o755)
        appdir=root/'mount';prefix=appdir/'usr'
        icon=prefix/'share/embercade/resources/branding/icon/embercade-512.png';icon.parent.mkdir(parents=True);icon.write_bytes(b'original test icon')
        env=dict(HOME=str(root/'home'),XDG_DATA_HOME=str(root/'data'),XDG_STATE_HOME=str(root/'state'),XDG_CONFIG_HOME=str(root/'config'),PATH='',
                 EMBERCADE_APPIMAGE='1',APPIMAGE=str(image),APPDIR=str(appdir),EMBERCADE_PREFIX=str(prefix))
        config=root/'config';config.mkdir();(config/'user-dirs.dirs').write_text('XDG_DESKTOP_DIR="$HOME/Schreibtisch"\n')
        return env

    def test_local_copy_menu_shortcut_and_reinstall_are_idempotent(self):
        with TemporaryDirectory(prefix='desktop space ') as directory:
            root=Path(directory);env=self.environment(root);paths=UserInstallPaths.from_environment(env)
            result=integrate(env,shortcut=True)
            launcher=Path(result['launcher']);self.assertNotEqual(launcher,Path(env['APPIMAGE']))
            self.assertEqual(launcher.read_bytes(),Path(env['APPIMAGE']).read_bytes())
            self.assertIn('Categories=Game;Emulator;',paths.desktop_entry.read_text())
            self.assertIn('Exec="'+str(launcher)+'"', paths.desktop_entry.read_text())
            self.assertIn('Icon=embercade',paths.desktop_entry.read_text())
            desktop=root/'home/Schreibtisch/embercade.desktop'
            self.assertEqual(desktop.read_bytes(),paths.desktop_entry.read_bytes())
            files=(launcher,paths.desktop_entry,paths.icon,desktop)
            before=[(p.read_bytes(),p.stat().st_mtime_ns) for p in files]
            integrate(env,shortcut=True)
            self.assertEqual(before,[(p.read_bytes(),p.stat().st_mtime_ns) for p in files])
            self.assertEqual(launcher.stat().st_mode&0o777,0o755)
            self.assertFalse(list(root.rglob('*.previous')))

    def test_unmanaged_or_modified_files_are_preserved_before_any_copy(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);env=self.environment(root);paths=UserInstallPaths.from_environment(env)
            paths.desktop_entry.parent.mkdir(parents=True);paths.desktop_entry.write_text('user entry')
            with self.assertRaises(DesktopError):integrate(env)
            self.assertEqual(paths.desktop_entry.read_text(),'user entry')
            self.assertFalse(paths.icon.exists());self.assertFalse((paths.data_root/'application').exists())
            paths.desktop_entry.unlink();integrate(env)
            paths.desktop_entry.write_text('edited later')
            with self.assertRaises(DesktopError):integrate(env)
            self.assertEqual(paths.desktop_entry.read_text(),'edited later')

    def test_failure_rolls_back_new_files_and_existing_owned_update(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);env=self.environment(root);paths=UserInstallPaths.from_environment(env)
            integrate(env);before=paths.icon.read_bytes()
            source=Path(env['EMBERCADE_PREFIX'])/'share/embercade/resources/branding/icon/embercade-512.png';source.write_bytes(b'updated icon')
            original=os.replace
            def failure(source,target):
                if Path(target).name=='desktop-integration.json':raise OSError('disk full')
                return original(source,target)
            with patch('embercade.desktop_integration.os.replace',side_effect=failure):
                with self.assertRaises(OSError):integrate(env)
            self.assertEqual(paths.icon.read_bytes(),before)
            self.assertFalse(list(root.rglob('*.previous')))
            self.assertFalse(list(root.rglob('.embercade-integration-*')))

    def test_symlink_and_unconfigured_desktop_refuse_writes(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);env=self.environment(root);paths=UserInstallPaths.from_environment(env)
            (root/'config/user-dirs.dirs').unlink()
            with self.assertRaises(DesktopError):integrate(env,shortcut=True)
            self.assertFalse(paths.icon.exists())
            paths.icon.parent.mkdir(parents=True);paths.icon.symlink_to(root/'other')
            with self.assertRaises(DesktopError):integrate(env)
            self.assertFalse((root/'other').exists())

    def test_classic_owned_menu_is_not_replaced_by_appimage(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);env=self.environment(root);paths=UserInstallPaths.from_environment(env)
            paths.manifest.parent.mkdir(parents=True);paths.manifest.write_text('{}')
            paths.desktop_entry.parent.mkdir(parents=True);paths.desktop_entry.write_text('verified classic menu')
            with patch('embercade.desktop_integration.install_user') as verify:
                result=integrate(env,shortcut=True)
                verify.assert_called_once_with(paths.prefix,environment=env,dry_run=True)
            self.assertEqual(result['launcher'],str(paths.launcher))
            self.assertFalse(result['local_image'])
            self.assertEqual(paths.desktop_entry.read_text(),'verified classic menu')
            self.assertEqual((root/'home/Schreibtisch/embercade.desktop').read_text(),'verified classic menu')
            self.assertFalse((paths.data_root/'application').exists())

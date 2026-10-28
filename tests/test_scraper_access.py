from pathlib import Path
from tempfile import TemporaryDirectory
import os
import shutil
import subprocess
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from embercade.paths import EmbercadePaths
from embercade.scraper_access import metadata_mounts, secret_mounts, secret_status, user_secret_status
from embercade.staging import StagingError, _manifest

PROJECT = Path(__file__).resolve().parents[1]
EXAMPLE = ('SCREENSCRAPER_DEV_ID=example-id\n'
           'SCREENSCRAPER_DEV_PASSWORD=example-password\n'
           'SCREENSCRAPER_DEV_DEBUG_PASSWORD=example-debug\n')


class ScraperAccessTests(unittest.TestCase):
    def setUp(self):
        self.workspace = TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.base = Path(self.workspace.name)
        self.paths = EmbercadePaths.from_environment({'HOME': str(self.base)})
        self.secret = self.paths.config / 'secrets/screenscraper.conf'
        self.secret.parent.mkdir(parents=True, mode=0o700)
        self.secret.write_text(EXAMPLE)
        self.secret.chmod(0o600)
        self.paths.rom_root.mkdir(parents=True)
        self.system = self.paths.rom_root / 'nes'
        self.system.mkdir()
        self.rom = self.system / 'example.nes'
        self.rom.write_bytes(b'read only game')
        self.catalog = self.base / 'systems.xml'
        self.catalog.write_text('<systemList><system><path>/userdata/roms/nes</path>'
                                '</system></systemList>')

    def test_secret_status_never_returns_values(self):
        self.assertEqual(secret_status(self.paths), 'CONFIGURED (NOT AUTHENTICATED)')
        mounts, variables = secret_mounts(self.paths)
        self.assertEqual(mounts[0], '--ro-bind')
        self.assertEqual(mounts[1], str(self.secret))
        self.assertTrue(mounts[2].endswith('/secrets/screenscraper.conf'))
        for value in ('example-id', 'example-password', 'example-debug'):
            self.assertNotIn(value, repr(mounts + variables))
        self.assertNotIn('devdebugpassword=', repr(variables))

    def test_missing_access_is_optional_and_not_mounted(self):
        self.secret.unlink()
        self.assertEqual(secret_status(self.paths), 'NOT CONFIGURED')
        self.assertEqual(secret_mounts(self.paths), ([], []))

    @unittest.skipUnless(shutil.which('bwrap'), 'Bubblewrap required')
    def test_namespace_freezes_developer_file_but_allows_personal_account(self):
        mounts, variables = secret_mounts(self.paths)
        code = '''
from pathlib import Path
import os
developer = Path('/userdata/system/xdg/config/embercade/secrets/screenscraper.conf')
personal = developer.with_name('screenscraper-user.conf')
try: developer.write_text('bad')
except OSError: pass
else: raise AssertionError('developer credential write was allowed')
os.umask(0o077)
personal.write_text('SCREENSCRAPER_USER=dummy\\nSCREENSCRAPER_PASSWORD=dummy\\n')
assert personal.stat().st_mode & 0o077 == 0
'''
        completed = subprocess.run([
            'bwrap', '--ro-bind', '/usr', '/usr',
            '--ro-bind', '/lib', '/lib', '--ro-bind', '/lib64', '/lib64',
            '--dir', '/userdata', '--dir', '/userdata/system',
            '--dir', '/userdata/system/xdg', '--dir', '/userdata/system/xdg/config',
            '--bind', str(self.paths.config), '/userdata/system/xdg/config/embercade',
            *mounts, *variables, '--', shutil.which('python'), '-B', '-c', code,
        ], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.secret.read_text(), EXAMPLE)
        self.assertTrue((self.paths.secrets / 'screenscraper-user.conf').is_file())

    def test_personal_account_status_and_legacy_migration_signal_are_value_free(self):
        settings = self.paths.emulationstation_config / 'es_settings.cfg'
        settings.parent.mkdir(parents=True)
        settings.write_text('<config><string name="ScreenScraperUser" value="dummy-user" />'
                            '<string name="ScreenScraperPass" value="dummy-password" /></config>')
        settings.chmod(0o600)
        self.assertEqual(user_secret_status(self.paths), 'LEGACY PRIVATE SETTINGS (MIGRATION PENDING)')
        user = self.paths.secrets / 'screenscraper-user.conf'
        user.write_text('SCREENSCRAPER_USER=dummy-user\nSCREENSCRAPER_PASSWORD=dummy-password\n')
        user.chmod(0o600)
        status = user_secret_status(self.paths)
        self.assertIn('LEGACY COPY PENDING REMOVAL', status)
        self.assertNotIn('dummy-', status)
        settings.write_text('<config />')
        self.assertEqual(user_secret_status(self.paths), 'CONFIGURED (NOT AUTHENTICATED)')
        user.chmod(0o644)
        self.assertEqual(user_secret_status(self.paths), 'UNSAFE PERMISSIONS')
        user.unlink()
        self.assertEqual(user_secret_status(self.paths), 'NOT CONFIGURED')

    def test_permissions_and_symlinks_rejected(self):
        self.secret.chmod(0o644)
        self.assertEqual(secret_status(self.paths), 'UNSAFE PERMISSIONS')
        self.assertEqual(secret_mounts(self.paths), ([], []))
        self.secret.chmod(0o600)
        self.secret.parent.chmod(0o755)
        self.assertEqual(secret_status(self.paths), 'UNSAFE PERMISSIONS')
        self.secret.parent.chmod(0o700)
        self.secret.unlink()
        self.secret.symlink_to(self.rom)
        self.assertEqual(secret_mounts(self.paths), ([], []))

    def test_invalid_and_duplicate_fields_do_not_echo_input(self):
        for data in ('export example-private-data', EXAMPLE + 'SCREENSCRAPER_DEV_ID=other\n',
                     'SCREENSCRAPER_DEV_ID=\n', '\0private', 'X' * 16385):
            self.secret.write_text(data)
            result = secret_status(self.paths)
            self.assertNotEqual(result, 'CONFIGURED (NOT AUTHENTICATED)')
            self.assertNotIn('private', result)

    def test_only_metadata_and_media_are_writable_both_aliases(self):
        mounts, unavailable = metadata_mounts(self.paths, self.catalog)
        self.assertFalse(unavailable)
        sources = mounts[1::3]
        self.assertNotIn(str(self.paths.rom_root), sources)
        self.assertNotIn(str(self.system), sources)
        self.assertNotIn(str(self.rom), sources)
        self.assertEqual(set(Path(p).name for p in sources),
                         {'gamelist.xml', 'images', 'videos', 'manuals', 'magazines'})
        self.assertEqual(len(mounts), 30)
        self.assertEqual(self.rom.read_bytes(), b'read only game')

    def test_existing_gamelist_media_and_secrets_survive_repeated_preparation(self):
        metadata_mounts(self.paths, self.catalog)
        gamelist = self.system / 'gamelist.xml'
        xml = b'<gameList><game><path>./example.nes</path><image>./images/example.png</image></game></gameList>'
        gamelist.write_bytes(xml)
        image = self.system / 'images/example.png'
        image.write_bytes(b'image')
        before = [(p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode)
                  for p in (gamelist, image, self.secret, self.rom)]
        metadata_mounts(self.paths, self.catalog)
        after = [(p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode)
                 for p in (gamelist, image, self.secret, self.rom)]
        self.assertEqual(before, after)
        self.assertEqual(ET.parse(gamelist).findtext('game/image'), './images/example.png')

    def test_symlinked_media_and_system_escape_are_not_exposed(self):
        external = self.base / 'external'
        external.mkdir()
        (self.system / 'images').symlink_to(external)
        mounts, unavailable = metadata_mounts(self.paths, self.catalog)
        self.assertEqual(mounts, [])
        self.assertEqual(unavailable, ('nes',))
        self.assertFalse((self.system / 'gamelist.xml').exists())
        self.catalog.write_text('<systemList><system><path>/userdata/roms/../external</path></system></systemList>')
        self.assertEqual(metadata_mounts(self.paths, self.catalog), ([], ()))

    def test_unwritable_metadata_falls_back_without_exposing_roms(self):
        with patch('embercade.scraper_access.os.access', return_value=False):
            mounts, unavailable = metadata_mounts(self.paths, self.catalog)
        self.assertEqual(mounts, [])
        self.assertEqual(unavailable, ('nes',))
        self.assertEqual(self.rom.read_bytes(), b'read only game')
        self.assertEqual(secret_status(self.paths), 'CONFIGURED (NOT AUTHENTICATED)')

    def test_existing_upstream_fallback_gamelist_is_retained_in_original_system_directory(self):
        self.catalog.write_text('<systemList><system><name>nes</name>'
                                '<path>/userdata/roms/nes</path></system></systemList>')
        legacy = self.paths.emulationstation_config / 'gamelists/nes/gamelist.xml'
        legacy.parent.mkdir(parents=True)
        data = b'<gameList><game><path>./example.nes</path><name>Existing name</name></game></gameList>'
        legacy.write_bytes(data)
        metadata_mounts(self.paths, self.catalog)
        self.assertEqual((self.system / 'gamelist.xml').read_bytes(), data)
        self.assertEqual(legacy.read_bytes(), data)

    @unittest.skipUnless(shutil.which('bwrap'), 'Bubblewrap required')
    def test_real_namespace_roms_bios_protected_metadata_writable(self):
        mounts, _ = metadata_mounts(self.paths, self.catalog)
        self.paths.bios_root.mkdir(parents=True)
        bios = self.paths.bios_root / 'firmware.bin'
        bios.write_bytes(b'firmware')
        code = '''
from pathlib import Path
for alias in (Path('/userdata/roms/nes'), Path(__import__('sys').argv[1])):
    for target in (alias / 'example.nes', alias / 'extra.nes'):
        try: target.write_bytes(b'bad')
        except OSError: pass
        else: raise AssertionError('ROM write was allowed')
    (alias / 'gamelist.xml').write_text('<gameList />')
    tmp = alias / 'images/test.tmp'
    tmp.write_bytes(b'image')
    tmp.rename(alias / 'images/test.png')
try: Path('/userdata/bios/firmware.bin').write_bytes(b'bad')
except OSError: pass
else: raise AssertionError('BIOS write was allowed')
'''
        completed = subprocess.run(['bwrap', '--ro-bind', '/usr', '/usr',
            '--ro-bind', '/lib', '/lib', '--ro-bind', '/lib64', '/lib64',
            '--ro-bind', str(self.paths.rom_root), str(self.paths.rom_root),
            '--ro-bind', str(self.paths.rom_root), '/userdata/roms',
            '--ro-bind', str(self.paths.bios_root), '/userdata/bios',
            *mounts, '--', shutil.which('python'), '-B', '-c', code, str(self.system)],
            capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.rom.read_bytes(), b'read only game')
        self.assertEqual(bios.read_bytes(), b'firmware')

    def test_build_contains_no_credentials_and_enables_existing_provider(self):
        build = (PROJECT / 'scripts/ui-build').read_text()
        patch = (PROJECT / 'patches/emulationstation/0002-embercade-screenscraper.patch').read_text()
        self.assertIn('-DEMBERCADE_SCREENSCRAPER_RUNTIME=ON', build)
        self.assertNotIn('-DSCREENSCRAPER_DEV_LOGIN=', build)
        self.assertIn('developerQuery()', patch)
        self.assertIn('PR_SET_DUMPABLE', patch)
        self.assertIn('safeError(mStatus)', patch)
        self.assertIn('isSensitive(url) ? 0L : 1L', patch)
        self.assertNotIn('<< url <<', patch.split('+\tLOG(LogDebug)')[-1])
        staging = (PROJECT / 'src/embercade/staging.py').read_text()
        self.assertNotIn('paths.config', staging)

    def test_stage_rejects_credentials_file_before_manifesting_it(self):
        stage = self.base / 'stage'
        stage.mkdir()
        (stage / 'screenscraper.conf').write_text(EXAMPLE)
        with self.assertRaisesRegex(StagingError, 'must never enter a payload'):
            _manifest(stage, {})
        (stage / 'screenscraper.conf').unlink()
        (stage / 'screenscraper-user.conf').write_text('SCREENSCRAPER_PASSWORD=dummy')
        with self.assertRaisesRegex(StagingError, 'must never enter a payload'):
            _manifest(stage, {})
        (stage / 'screenscraper-user.conf').unlink()
        for name in ('screenscraper-build.conf', 'ScreenScraperAuthorization.h',
                     'retroachievements-user.conf', 'retroachievements-build.conf'):
            target=stage/name;target.write_text('synthetic-only authorization fixture')
            with self.assertRaisesRegex(StagingError, 'must never enter a payload'):
                _manifest(stage,{})
            target.unlink()


@unittest.skipUnless(shutil.which('c++'), 'C++ compiler needed for native integration tests')
class NativeCredentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = TemporaryDirectory()
        cls.base = Path(cls.workspace.name)
        cls.binary = cls.base / 'probe'
        source = '''
#include "EmbercadeScreenScraper.h"
#include <cassert>
int main(int argc, char** argv) {
    if (argc == 2) {
        setenv("EMBERCADE_SCREENSCRAPER_SECRET_FILE", argv[1], 1);
        return EmbercadeScreenScraper::load().valid() ? 0 : 2;
    }
    if (argc == 3) {
        setenv("XDG_CONFIG_HOME", argv[1], 1);
        EmbercadeScreenScraper::UserCredentials account;
        std::string action(argv[2]);
        if (action == "write") {
            account.name = "dummy-user";
            account.password = "dummy-password";
            return EmbercadeScreenScraper::saveUser(account) ? 0 : 3;
        }
        if (action == "read")
            return EmbercadeScreenScraper::loadUser(account)
                && account.name == "dummy-user" && account.password == "dummy-password" ? 0 : 4;
        if (action == "clear")
            return EmbercadeScreenScraper::saveUser(account) ? 0 : 5;
        return 6;
    }
    using namespace EmbercadeScreenScraper;
    assert(isService("https://api.screenscraper.fr/api2/jeuInfos.php"));
    assert(isService("https://neoclone.screenscraper.fr/api2/mediaJeu.php?devid=example&devpassword=example"));
    assert(isService("https://OTHER.screenscraper.fr/api2/mediaJeu.php"));
    assert(isService("https://screenscraper.fr/"));
    assert(!isService("https://api.screenscraper.fr.evil/test"));
    assert(!isService("https://screenscraper.fr@evil.test/test"));
    assert(!isService("https://evil.test/path/screenscraper.fr"));
    assert(!isService("https://evilscreenscraper.fr/test"));
    assert(!isService("https://.screenscraper.fr/test"));
    assert(!isService("https://api..screenscraper.fr/test"));
    assert(!isService("https://api.screenscraper.fr:8443/test"));
    assert(!isService("https://api.screenscraper.fr%00.evil/test"));
    assert(!isService("http://api.screenscraper.fr/test"));
    assert(!isService("http://neoclone.screenscraper.fr/test"));
    assert(isSensitive("https://other/thing?sspassword=example"));
    assert(isSensitive("https://other/?devdebugpassword=example"));
    assert(safeError(401).find("active members") != std::string::npos);
    assert(safeError(403).find("access was refused") != std::string::npos);
    assert(safeError(423).find("temporarily closed") != std::string::npos);
    assert(safeError(426).find("cannot access the service") != std::string::npos);
    assert(safeError(429).find("limit") != std::string::npos);
    return 0;
}
'''
        result = subprocess.run(['c++', '-std=c++11', '-I', str(PROJECT / 'patches/emulationstation'),
                                 '-x', 'c++', '-', '-o', str(cls.binary)], input=source,
                                text=True, capture_output=True)
        if result.returncode:
            cls.workspace.cleanup()
            raise RuntimeError('Native test helper failed to compile: ' + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def test_native_load_valid_missing_permissions_duplicate_nul_and_symlink(self):
        source = self.base / 'credentials.conf'
        for data, mode, expected in ((EXAMPLE, 0o600, 0), (EXAMPLE, 0o644, 2),
                (EXAMPLE + 'SCREENSCRAPER_DEV_ID=other\n', 0o600, 2),
                ('SCREENSCRAPER_DEV_ID=\0bad', 0o600, 2), ('X'*16385, 0o600, 2)):
            source.write_text(data)
            source.chmod(mode)
            result = subprocess.run([str(self.binary), str(source)], capture_output=True)
            self.assertEqual(result.returncode, expected)
            self.assertEqual(result.stdout + result.stderr, b'')
        source.unlink()
        self.assertEqual(subprocess.run([str(self.binary), str(source)]).returncode, 2)
        real = self.base / 'real'
        real.write_text(EXAMPLE)
        real.chmod(0o600)
        source.symlink_to(real)
        self.assertEqual(subprocess.run([str(self.binary), str(source)]).returncode, 2)

    def test_personal_account_file_is_atomic_private_and_never_echoes_values(self):
        root = self.base / 'user-config'
        (root / 'embercade').mkdir(parents=True)
        target = root / 'embercade/secrets/screenscraper-user.conf'
        for action in ('write', 'read', 'write', 'clear'):
            result = subprocess.run([str(self.binary), str(root), action], capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout + result.stderr, b'')
            self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(target.parent.glob('.screenscraper-user.conf.*')), [])
        target.chmod(0o644)
        self.assertNotEqual(subprocess.run([str(self.binary), str(root), 'write']).returncode, 0)
        self.assertEqual(list(target.parent.glob('.screenscraper-user.conf.*')), [])

    def test_native_transport_security_and_safe_errors(self):
        self.assertEqual(subprocess.run([str(self.binary)]).returncode, 0)

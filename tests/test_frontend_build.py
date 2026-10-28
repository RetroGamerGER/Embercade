from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import quote
import io,json,os,shutil,stat,subprocess,sys,time,unittest
from embercade.frontend_build import (FrontendBuildError, MARKER, INFO_NAME, _secret,
                                     developer_query, prepare, finalize, verify_frontend, sanitized_run, RA_USER_MARKER, RA_MARKER)


class FrontendBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.private=self.root/'protected';self.private.mkdir(mode=0o700)
        self.secret=self.private/'input.conf'
        self.values={'SCREENSCRAPER_DEV_ID':'test app+Ä&=?', 'SCREENSCRAPER_DEV_PASSWORD':'test p@ss/é&"?+#'}
        self.write(self.values)
        self.frontend=self.root/'.work/ui/es-source/emulationstation'

    def write(self, fields):
        self.secret.write_text(''.join(k+'='+v+'\n' for k,v in fields.items()));self.secret.chmod(0o600)

    def binary(self, embedded=True):
        self.frontend.parent.mkdir(parents=True,exist_ok=True)
        self.frontend.write_bytes(b'fixture\0'+RA_USER_MARKER+b'\0'+(MARKER+b'\0'+developer_query(self.values).encode() if embedded else b'development fixture'))

    def test_production_requires_complete_private_input_and_never_uses_home_fallback(self):
        with self.assertRaises(FrontendBuildError):prepare(self.root,None)
        for fields in ({}, {'SCREENSCRAPER_DEV_ID':'synthetic'}, {**self.values,'SCREENSCRAPER_USER':'personal'},
                       {**self.values,'SCREENSCRAPER_DEV_DEBUG_PASSWORD':'debug'}):
            self.write(fields)
            with self.subTest(fields=list(fields)),self.assertRaises(FrontendBuildError) as caught:prepare(self.root,self.secret)
            self.assertNotIn('personal', str(caught.exception).replace('personal/debug fields',''))

    def test_permissions_symlink_duplicate_control_and_nonregular_sources_are_refused(self):
        self.secret.chmod(0o644)
        with self.assertRaises(FrontendBuildError):_secret(self.secret)
        self.secret.chmod(0o600);self.private.chmod(0o755)
        with self.assertRaises(FrontendBuildError):_secret(self.secret)
        self.private.chmod(0o700);original=self.private/'actual';self.secret.rename(original);self.secret.symlink_to(original)
        with self.assertRaises(FrontendBuildError):_secret(self.secret)
        self.secret.unlink()
        for content in ('SCREENSCRAPER_DEV_ID=x\nSCREENSCRAPER_DEV_ID=y\n', 'SCREENSCRAPER_DEV_ID=bad\0value\n','X'*16385):
            self.secret.write_text(content);self.secret.chmod(0o600)
            with self.assertRaises(FrontendBuildError):_secret(self.secret)

    def test_url_encoding_and_generated_header_do_not_mix_user_or_debug_fields(self):
        header=prepare(self.root,self.secret)
        self.assertEqual(stat.S_IMODE(header.stat().st_mode),0o600)
        self.assertEqual(stat.S_IMODE(header.parent.stat().st_mode),0o700)
        text=header.read_text()
        self.assertIn('devid='+quote(self.values['SCREENSCRAPER_DEV_ID'],safe=''),text)
        self.assertIn('devpassword='+quote(self.values['SCREENSCRAPER_DEV_PASSWORD'],safe=''),text)
        self.assertNotIn('ssid=',text);self.assertNotIn('devdebugpassword=',text)
        timestamp=header.stat().st_mtime_ns;prepare(self.root,self.secret)
        self.assertEqual(header.stat().st_mtime_ns,timestamp)

    def test_compiled_header_works_without_any_runtime_developer_file(self):
        if not shutil.which('c++'):self.skipTest('C++ compiler unavailable')
        header=prepare(self.root,self.secret);source=self.root/'probe.cpp';binary=self.root/'probe'
        expected=developer_query(self.values)
        source.write_text('#include <string>\nint main(){return std::string(SCREENSCRAPER_DEV_LOGIN)=='+json.dumps(expected)+' ? 0:1;}\n')
        compiled=subprocess.run(['c++','-include',str(header),str(source),'-o',str(binary)],capture_output=True)
        self.assertEqual(compiled.returncode,0)
        self.secret.unlink();header.unlink()
        env={k:v for k,v in os.environ.items() if not k.startswith('EMBERCADE_')}
        self.assertEqual(subprocess.run([str(binary)],env=env).returncode,0)

    def test_finalize_detects_stale_binary_after_authorization_rotation(self):
        prepare(self.root,self.secret);self.binary();info=finalize(self.root,self.secret)
        self.assertEqual(set(info),{'format','software','authorization','frontend_sha256','retroachievements_authorization'})
        self.assertNotIn('test p@ss',json.dumps(info))
        self.write({**self.values,'SCREENSCRAPER_DEV_PASSWORD':'rotated dummy password'})
        with self.assertRaises(FrontendBuildError):finalize(self.root,self.secret)

    def test_packaging_checks_matching_binary_metadata_and_explicit_development_mode(self):
        prepare(self.root,self.secret);self.binary();finalize(self.root,self.secret)
        metadata=self.root/'.work/ui'/INFO_NAME
        self.assertEqual(verify_frontend(self.frontend,metadata)['authorization'],'embedded')
        self.frontend.write_bytes(b'stale frontend')
        with self.assertRaises(FrontendBuildError):verify_frontend(self.frontend,metadata)
        self.binary(False);prepare(self.root,None,development=True);finalize(self.root,None,development=True)
        with self.assertRaises(FrontendBuildError):verify_frontend(self.frontend,metadata)
        self.assertEqual(verify_frontend(self.frontend,metadata,development=True)['authorization'],'development-local')

    def test_builder_output_redacts_raw_and_encoded_values(self):
        expected=developer_query(self.values)
        script='print('+repr(self.values['SCREENSCRAPER_DEV_ID']+' '+self.values['SCREENSCRAPER_DEV_PASSWORD']+' '+expected)+')'
        output=io.StringIO()
        with redirect_stdout(output):code=sanitized_run([sys.executable,'-c',script],self.secret)
        self.assertEqual(code,0)
        for v in self.values.values():
            self.assertNotIn(v,output.getvalue());self.assertNotIn(quote(v,safe=''),output.getvalue())
        self.assertIn('[REDACTED]',output.getvalue())

    def test_build_time_personal_keys_are_rejected_before_reading_or_spawning(self):
        for function in (prepare, finalize):
            with self.subTest(function=function.__name__),patch('embercade.frontend_build._secret') as reader:
                with self.assertRaises(FrontendBuildError):
                    function(self.root,self.secret,retroachievements_source=self.private/'legacy-ra.conf')
                reader.assert_not_called()
        with patch('embercade.frontend_build.subprocess.Popen') as process:
            with self.assertRaises(FrontendBuildError):
                sanitized_run([sys.executable,'-c','print("not run")'],self.secret,
                              retroachievements_source=self.private/'legacy-ra.conf')
            process.assert_not_called()

    def test_new_headers_cannot_retain_previous_shared_authorization(self):
        header=prepare(self.root,self.secret)
        header.write_text(header.read_text()+'#define CHEEVOS_DEV_LOGIN "dummy-shared-key"\n')
        prepare(self.root,self.secret)
        self.assertNotIn('CHEEVOS_DEV_LOGIN',header.read_text())
        self.assertNotIn('dummy-shared-key',header.read_text())
        self.assertIn('SCREENSCRAPER_DEV_LOGIN',header.read_text())

    def test_packaging_requires_runtime_user_mode_and_rejects_legacy_marker(self):
        self.binary();info=finalize(self.root,self.secret)
        self.assertEqual(info['retroachievements_authorization'],'per-user-web-api')
        metadata=self.root/'.work/ui'/INFO_NAME
        self.assertEqual(verify_frontend(self.frontend,metadata),info)
        for data in [self.frontend.read_bytes().replace(RA_USER_MARKER,b'old-build'),
                     self.frontend.read_bytes()+b'\0'+RA_MARKER+b'\0z=synthetic&y=synthetic-key']:
            self.frontend.write_bytes(data)
            with self.assertRaises(FrontendBuildError):finalize(self.root,self.secret)
            info['frontend_sha256']=__import__('hashlib').sha256(data).hexdigest()
            metadata.write_text(json.dumps(info))
            with self.assertRaises(FrontendBuildError):verify_frontend(self.frontend,metadata)

    def test_cli_rejects_inherited_legacy_build_environment_without_echoing_values(self):
        from embercade.frontend_build import main,RA_SECRET_ENV
        with patch.dict(os.environ,{RA_SECRET_ENV:'synthetic-sensitive-path','EMBERCADE_PRIVATE_RETROACHIEVEMENTS_BUILD':'1'}):
            output=io.StringIO()
            from contextlib import redirect_stderr
            with redirect_stderr(output):
                self.assertEqual(main(['--project-root',str(self.root),'prepare']),2)
            self.assertNotIn('synthetic-sensitive-path',output.getvalue())

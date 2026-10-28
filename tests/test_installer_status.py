import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from embercade.host_requirements import HostAssessment, HostRequirement, RequirementStatus, DistroInfo, BootstrapPlan
from embercade.installer_preferences import status_report
from embercade.paths import EmbercadePaths
from embercade.first_run_ui import Wizard


class InstallerStatusTests(unittest.TestCase):
    def assessment(self):
        return HostAssessment(DistroInfo('garuda','Garuda',()),
            (RequirementStatus(HostRequirement('dolphin','Dolphin','dolphin-emu',emulator='dolphin'),False,''),
             RequirementStatus(HostRequirement('python','Python runtime','python'),True,''),
             RequirementStatus(HostRequirement('rpcs3','RPCS3','rpcs3',emulator='rpcs3'),False,'')),
            (),('ps3',),rpcs3_firmware='OK',active_emulators=('rpcs3',))

    def test_effective_collection_route_prioritizes_required_components(self):
        with TemporaryDirectory() as directory:
            paths=EmbercadePaths.from_environment({'HOME':directory})
            report=status_report(paths,{},self.assessment(),BootstrapPlan(self.assessment(),()))
            self.assertEqual([r['label'] for r in report['requirements']],['Python runtime','RPCS3','Dolphin'])
            self.assertEqual([r['required'] for r in report['requirements']],[True,True,False])
            self.assertTrue(report['rpcs3_source'])
            self.assertFalse(report['rpcs3'])
            self.assertTrue(report['eeprom']['missing'])

    def test_host_firmware_is_not_reported_as_isolated_and_invalid_eeprom_is_error(self):
        with TemporaryDirectory() as directory:
            paths=EmbercadePaths.from_environment({'HOME':directory})
            version=paths.emulator_configs/'rpcs3/dev_flash/vsh/etc/version.txt'
            version.parent.mkdir(parents=True);version.write_text('release:04.9300:fixture\n')
            from embercade.xemu import isolated_xemu_files
            file=isolated_xemu_files(paths).eeprom;file.parent.mkdir(parents=True);file.write_bytes(b'invalid')
            report=status_report(paths,{},self.assessment(),BootstrapPlan(self.assessment(),()))
            self.assertTrue(report['rpcs3'])
            self.assertEqual(report['eeprom'],{'invalid':True})
            self.assertNotIn('key',str(report).lower())

    def test_failed_required_runtime_prevents_success_even_if_optional_hosts_missing(self):
        for available, expected in ((False,'Some components'),(True,'checks passed')):
            wizard=Wizard.__new__(Wizard);wizard.language='en';wizard._go=Mock()
            report=dict(configured=True,requirements=[dict(label='Dolphin',available=False,required=False)],cores=[],
                        checks=[dict(label='Application runtime',available=available,required=True)],active_systems=[],
                        rpcs3=False,xemu_firmware=False,xemu_hdd=False,xemu_eeprom=False,eeprom={'missing':True},
                        xenia='OPTIONAL',shadps4='OPTIONAL',scraper_developer='MISSING',scraper_user='MISSING')
            wizard._status=Mock(return_value=report)
            wizard._doctor_done(Mock())
            self.assertIn(expected,wizard.finish_text)
            self.assertIn('Optional',wizard.doctor_output)
            wizard._go.assert_called_once_with('finish')

    def test_bilingual_installer_details_and_summary_have_no_scraper_account_status(self):
        with TemporaryDirectory() as directory:
            paths=EmbercadePaths.from_environment({'HOME':directory})
            report=status_report(paths,{},self.assessment(),BootstrapPlan(self.assessment(),()))
            self.assertNotIn('scraper_developer',report)
            self.assertNotIn('scraper_user',report)
        report.update(configured=True,requirements=[],cores=[],checks=[],active_systems=[],
                      scraper_developer='synthetic-private-marker',scraper_user='synthetic-user-marker')
        for language in ('de','en'):
            wizard=Wizard.__new__(Wizard);wizard.language=language
            text=wizard._status_text(report)
            self.assertNotIn('ScreenScraper',text)
            self.assertNotIn('synthetic-',text)
            self.assertNotIn('developer',text.casefold())
            self.assertNotIn('Entwickler',text)

    def test_missing_personal_account_cannot_prevent_installation_success(self):
        with TemporaryDirectory() as directory:
            paths=EmbercadePaths.from_environment({'HOME':directory})
            report=status_report(paths,{},self.assessment(),BootstrapPlan(self.assessment(),()))
            report.update(configured=True,requirements=[],cores=[],checks=[],active_systems=[])
            wizard=Wizard.__new__(Wizard);wizard.language='en';wizard._go=Mock()
            wizard._status=Mock(return_value=report);wizard._doctor_done(Mock())
            self.assertIn('checks passed',wizard.finish_text)
            self.assertFalse(paths.secrets.exists())

    def test_cli_download_without_consent_and_invalid_eeprom_fail_without_traceback(self):
        from embercade.cli import main
        from io import StringIO
        with TemporaryDirectory() as directory, patch.dict(os.environ,{"HOME":directory,"PATH":"/usr/bin"},clear=True):
            paths=EmbercadePaths.from_environment()
            from embercade.xemu import isolated_xemu_files
            file=isolated_xemu_files(paths).eeprom;file.parent.mkdir(parents=True);file.write_bytes(b'invalid')
            for action in (("firmware","--download"),("xbox-status",)):
                with patch("sys.stderr",new_callable=StringIO) as output:
                    with self.assertRaises(SystemExit) as error:main(["installer",*action])
                self.assertEqual(error.exception.code,2)
                self.assertNotIn("Traceback",output.getvalue())
                self.assertIn("error:",output.getvalue())
            self.assertFalse((paths.cache/"firmware").exists())
            self.assertEqual(file.read_bytes(),b'invalid')

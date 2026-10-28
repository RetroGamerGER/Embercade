from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from embercade.doctor import report
from embercade.elf_runtime import ElfRuntimeClosure, FrontendRuntimeReport
from embercade.paths import EmbercadePaths
from embercade.host_requirements import (
    DistroInfo,
    HostAssessment,
    HostRequirement,
    RequirementStatus,
    XeniaProviderStatus,
)
from embercade.production import ProductionLayout


class _NoEmulators:
    @staticmethod
    def probe_all() -> dict[str, object]:
        return {}


class DoctorPathTests(unittest.TestCase):
    def test_secret_status_is_value_free_and_appdir_misplacement_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            appdir = root / 'AppDir'
            paths = EmbercadePaths.from_environment({
                'HOME': str(root / 'home'), 'XDG_CONFIG_HOME': str(appdir / 'config'),
            })
            secret = paths.secrets / 'screenscraper.conf'
            secret.parent.mkdir(parents=True, mode=0o700)
            secret.write_text('SCREENSCRAPER_DEV_ID=dummy-private-id\n'
                              'SCREENSCRAPER_DEV_PASSWORD=dummy-private-password\n')
            secret.chmod(0o600)
            output = StringIO()
            result = report(paths, _NoEmulators(), environment={'APPDIR': str(appdir)}, stream=output)
            text = output.getvalue()
            self.assertNotEqual(result, 0)
            self.assertNotIn('ScreenScraper', text)
            self.assertNotIn('Secret backend', text)
            self.assertIn('AppImage state separation: UNSAFE', text)
            self.assertNotIn('dummy-private-id', text)
            self.assertNotIn('dummy-private-password', text)

    def test_frontend_binary_and_shared_library_status_are_separate(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            layout = ProductionLayout(root / "prefix")
            layout.frontend.parent.mkdir(parents=True)
            layout.frontend.write_bytes(b"ELF")
            runtime_report = FrontendRuntimeReport(
                ElfRuntimeClosure((), ("libfreeimage.so.3",)),
                ("libfreeimage.so.3",),
                ("frontend shared libraries missing: libfreeimage.so.3",),
            )
            paths = EmbercadePaths.from_environment({"HOME": str(root / "home")})
            output = StringIO()

            with (
                patch.object(ProductionLayout, "validate", return_value=()),
                patch.object(ProductionLayout, "frontend_runtime", return_value=runtime_report),
            ):
                result = report(
                    paths,
                    _NoEmulators(),
                    environment={},
                    production_layout=layout,
                    stream=output,
                )

            text = output.getvalue()
            self.assertNotEqual(result, 0)
            self.assertIn("binary present        OK", text)
            self.assertIn("shared libraries      MISSING", text)
            self.assertIn("libfreeimage.so.3", text)

    def test_collection_root_status_is_printed_without_enumeration(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "ROM root"
            bios = root / "BIOS root"
            roms.mkdir()
            bios.mkdir()
            paths = EmbercadePaths.from_environment(
                {"HOME": str(root)},
                config={"paths": {"roms": str(roms), "bios": str(bios)}},
            )
            output = StringIO()

            report(paths, _NoEmulators(), environment={}, stream=output)

            text = output.getvalue()
            self.assertIn(f"ROM root   OK              {roms}", text)
            self.assertIn(f"BIOS root  OK              {bios}", text)

    def test_unconfigured_roots_are_reported(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            output = StringIO()

            report(paths, _NoEmulators(), environment={}, stream=output)

            self.assertEqual(output.getvalue().count("CONFIGURATION REQUIRED"), 2)
            self.assertIn("PPSSPP assets: PSP GAMES UNAVAILABLE", output.getvalue())

    def test_ppsspp_default_assets_are_reported_without_modification(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            source = paths.data / "resources/PPSSPP"
            (source / "lang").mkdir(parents=True)
            (source / "flash0").mkdir()
            (source / "ppge_atlas.zim").write_bytes(b"atlas")
            output = StringIO()
            report(paths, _NoEmulators(), environment={}, stream=output)
            self.assertIn(f"PPSSPP assets: OK  {source}", output.getvalue())
            self.assertFalse(paths.isolated_bios.exists())

    def test_doctor_uses_shared_host_assessment(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": directory})
            requirement = HostRequirement(
                "dolphin", "Dolphin", "dolphin-emu", emulator="dolphin"
            )
            assessment = HostAssessment(
                DistroInfo("arch", "Arch Linux", ()),
                (RequirementStatus(requirement, False, "shared missing result"),),
                (),
                (),
            )
            output = StringIO()
            report(
                paths,
                _NoEmulators(),
                environment={},
                host_assessment=assessment,
                stream=output,
            )
            self.assertIn("dolphin", output.getvalue())
            self.assertIn("shared missing result", output.getvalue())

    def test_doctor_reports_provider_diagnoses_without_fatal_installation_damage(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            for status in ("MANAGED", "OVERRIDE", "FOUND", "MISSING", "INVALID", "UNVERIFIED", "AMBIGUOUS", "OPTIONAL", "UNSELECTED"):
                with self.subTest(status=status):
                    diagnosis = XeniaProviderStatus(
                        status, "provider-specific detail", "/example/Provider.AppImage",
                        "configured provider", status != "OPTIONAL",
                    )
                    assessment = HostAssessment(
                        DistroInfo("arch", "Arch", ()), (), (), (), xenia_provider=diagnosis,
                    )
                    output = StringIO()
                    report(paths, _NoEmulators(), environment={}, host_assessment=assessment, stream=output)
                    text = output.getvalue()
                    self.assertIn(f"xenia-edge   {status}", text)
                    self.assertIn("provider-specific detail", text)
                    self.assertIn("/example/Provider.AppImage (configured provider)", text)
                    self.assertNotIn("FATAL", text)

    def test_optional_provider_absence_does_not_fail_an_otherwise_healthy_installation(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            bios = root / "bios"
            roms.mkdir()
            bios.mkdir()
            paths = EmbercadePaths.from_environment(
                {"HOME": directory}, config={"paths": {"roms": str(roms), "bios": str(bios)}},
            )
            assessment = HostAssessment(
                DistroInfo("arch", "Arch", ()), (), (), (),
                xenia_provider=XeniaProviderStatus("OPTIONAL", "not needed", needed=False),
            )
            runtime = SimpleNamespace(installed_root=True)
            runtime_status = SimpleNamespace(
                available=True, python_version="test", imports={}, cli_error=None,
            )
            with patch("embercade.doctor.probe_runtime", return_value=runtime_status):
                result = report(
                    paths, _NoEmulators(), environment={}, runtime=runtime,
                    host_assessment=assessment, stream=StringIO(),
                )
            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()

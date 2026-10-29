from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import subprocess
import unittest

from embercade.host_requirements import (
    CORE_ARCH_PACKAGES,
    appimage_host_dependencies,
    BootstrapPlan,
    CoreRequirementStatus,
    DistroInfo,
    HostAssessment,
    HostRequirement,
    HOST_REQUIREMENTS,
    AurHelper,
    Pacman,
    RequirementStatus,
    active_libretro_cores,
    create_bootstrap_plan,
    read_os_release,
    render_bootstrap_plan,
    run_bootstrap,
    assess_host,
    inspect_xenia_provider,
    render_host_summary,
)
from embercade.executables import (
    EmulatorProvider, ExecutableResolutionError, ExecutableResolver,
    ProviderType, ResolvedExecutable,
)
from embercade.imports import ImportError as ManagedImportError
from embercade.setup_flow import SetupError, recommended_xenia_directory
from test_imports import elf


PROVIDER_METADATA = {
    "Name": "Xenia Edge", "Exec": "xenia_edge", "StartupWMClass": "xenia_edge",
}


def _assessment(*, distro: str = "cachyos", installed: bool = False) -> HostAssessment:
    requirement = HostRequirement("retroarch", "RetroArch", "retroarch", emulator="retroarch")
    return HostAssessment(
        DistroInfo(distro, distro, ("arch",) if distro in {"cachyos", "garuda", "endeavouros"} else ()),
        (RequirementStatus(requirement, installed, "test"),),
        (),
        (),
    )


class HostRequirementTests(unittest.TestCase):
    def test_optional_vulkan_probe_tool_is_in_existing_confirmed_install_plan(self):
        from embercade.host_requirements import _probe_requirement
        requirement = next(r for r in HOST_REQUIREMENTS if r.key == "vulkan-tools")
        with patch("embercade.host_requirements.shutil.which", return_value=None):
            status = _probe_requirement(requirement, Mock(), {"PATH": ""})
        self.assertFalse(status.installed)
        self.assertFalse(requirement.required)
        assessment = HostAssessment(DistroInfo("garuda", "Garuda", ("arch",)), (status,), (), ())
        plan = create_bootstrap_plan(assessment, Mock(available=lambda _: True))
        self.assertEqual(plan.packages, ("vulkan-tools",))

    def test_missing_elf_inspector_is_offered_for_real_core_runtime_checks(self):
        from embercade.host_requirements import _probe_requirement
        requirement = next(r for r in HOST_REQUIREMENTS if r.key == "binutils")
        with patch("embercade.host_requirements.shutil.which", return_value=None):
            status = _probe_requirement(requirement, Mock(), {"PATH":""})
        self.assertFalse(status.installed)
        assessment = HostAssessment(DistroInfo("garuda","Garuda",("arch",)),(status,),(),())
        plan = create_bootstrap_plan(assessment, Mock(available=lambda _: True))
        self.assertEqual(plan.packages,("binutils",))
        self.assertTrue(requirement.required)

    def test_static_appimage_runtime_does_not_require_libfuse2(self):
        with patch("embercade.host_requirements.shutil.which", side_effect=lambda name, **_: name), \
             patch("embercade.host_requirements.direct_elf_sonames", return_value=((), None)), \
             patch("embercade.host_requirements.inspect_elf_runtime") as closure:
            self.assertEqual(appimage_host_dependencies(Path("/provider"), {}), ())
            closure.assert_not_called()

    def test_dynamic_appimage_reports_actual_missing_dependencies_and_cleanup_fallback(self):
        from embercade.elf_runtime import ElfRuntimeClosure
        with patch("embercade.host_requirements.shutil.which", side_effect=lambda name, **_: None if name == "fusermount3" else name), \
             patch("embercade.host_requirements.direct_elf_sonames", return_value=(("libfuse.so.2",), None)), \
             patch("embercade.host_requirements.inspect_elf_runtime", return_value=ElfRuntimeClosure((), ("libfuse.so.2",))):
            self.assertEqual(appimage_host_dependencies(Path("/provider"), {}), ("libfuse.so.2",))

    def test_kde_wayland_layer_shell_is_offered_by_existing_bootstrap_only_where_needed(self):
        for gamescope in (False, True):
            env = dict(WAYLAND_DISPLAY="w", XDG_CURRENT_DESKTOP="KDE", DISPLAY=":1")
            if gamescope: env["GAMESCOPE_WAYLAND_DISPLAY"] = "gamescope"
            optional = __import__("embercade.host_requirements", fromlist=["XeniaProviderStatus"]).XeniaProviderStatus("OPTIONAL", "optional")
            with patch("embercade.host_requirements._active_routes", return_value=((), (), ())), \
                 patch("embercade.host_requirements.inspect_xenia_provider", return_value=optional), \
                 patch("embercade.host_requirements.inspect_appimage_provider", return_value=optional), \
                 patch("embercade.host_requirements._probe_requirement", side_effect=lambda r, *_: RequirementStatus(r, r.key != "gtk-layer-shell", "fixture")):
                assessment = assess_host(resolver=Mock(), core_resolver=Mock(), environment=env, rom_root=Path("/roms"),
                    systems_config=Path("/systems"), default_config=Path("/defaults"), user_config=Path("/user"), distro=DistroInfo("garuda", "Garuda", ("arch",)))
            plan = create_bootstrap_plan(assessment, Mock(available=lambda _: True))
            self.assertEqual("gtk-layer-shell" in plan.packages, not gamescope)

    def test_missing_cairo_is_offered_even_when_layer_shell_is_available(self):
        from embercade.host_requirements import XeniaProviderStatus
        environments = (
            ({"WAYLAND_DISPLAY": "w", "XDG_CURRENT_DESKTOP": "KDE"}, True),
            ({"WAYLAND_DISPLAY": "w", "HYPRLAND_INSTANCE_SIGNATURE": "test"}, True),
            ({"WAYLAND_DISPLAY": "w", "GAMESCOPE_WAYLAND_DISPLAY": "g", "DISPLAY": ":1"}, True),
            ({"WAYLAND_DISPLAY": "w", "XDG_CURRENT_DESKTOP": "GNOME"}, False),
            ({}, False),
        )
        optional = XeniaProviderStatus("OPTIONAL", "optional")
        for environment, supported in environments:
            with self.subTest(environment=environment), \
                 patch("embercade.host_requirements._active_routes", return_value=((), (), ())), \
                 patch("embercade.host_requirements.inspect_xenia_provider", return_value=optional), \
                 patch("embercade.host_requirements.inspect_appimage_provider", return_value=optional), \
                 patch("embercade.host_requirements._probe_requirement", side_effect=lambda r, *_: RequirementStatus(r, r.key != "python-cairo", "fixture")):
                assessment = assess_host(resolver=Mock(), core_resolver=Mock(), environment=environment,
                    rom_root=Path("/roms"), systems_config=Path("/systems"), default_config=Path("/defaults"),
                    user_config=Path("/user"), distro=DistroInfo("garuda", "Garuda", ("arch",)))
                plan = create_bootstrap_plan(assessment, Mock(available=lambda _: True))
                self.assertEqual(plan.packages, ("python-cairo",) if supported else ())
                if supported:
                    requirement = next(s.requirement for s in assessment.requirements if s.requirement.key == "python-cairo")
                    self.assertFalse(requirement.required)  # A missing bezel must not block game launch.
                    from embercade.i18n import Translator
                    self.assertEqual(Translator("de")(requirement.label), "Darstellung der Standalone-Bezels")
                    self.assertEqual(Translator("en")(requirement.label), requirement.label)

    def test_cairo_probe_checks_host_interpreter_and_drawing_bridge_without_opening_window(self):
        from embercade.host_requirements import _probe_requirement
        requirement = HostRequirement("python-cairo", "Standalone decoration drawing", "python-cairo", probe="python-cairo", required=False)
        for result in (subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1),
                       OSError("unavailable"), subprocess.TimeoutExpired([], 5)):
            with self.subTest(result=result), patch("embercade.host_requirements.subprocess.run") as run:
                if isinstance(result, Exception):
                    run.side_effect = result
                else:
                    run.return_value = result
                status = _probe_requirement(requirement, Mock(), {})
                self.assertEqual(status.installed, not isinstance(result, Exception) and result.returncode == 0)
                args = run.call_args.args[0]
                self.assertEqual(args[:4], ["/usr/bin/python", "-I", "-B", "-c"])
                self.assertIn("gi.require_foreign('cairo')", args[4])
                self.assertIn("cairo.ImageSurface", args[4])
                self.assertNotIn("Gtk.Window", args[4])
                self.assertEqual(run.call_args.kwargs["timeout"], 5)

    def test_german_bootstrap_uses_localized_confirmation_and_recognizes_decline(self):
        prompts, output = [], StringIO()
        pacman = Mock(install=lambda _: 0)
        plan = BootstrapPlan(_assessment(), ("retroarch",))
        def answer(prompt):
            prompts.append(prompt); return "ja"
        self.assertEqual(run_bootstrap(plan, dry_run=False, input_function=answer, stream=output, pacman=pacman, language="de"), 0)
        self.assertIn("installieren? [j/N]", prompts[0])
        self.assertIn("Host-Paketinstallation", output.getvalue())
        self.assertEqual(run_bootstrap(plan, dry_run=False, input_function=lambda _: "", stream=output, pacman=pacman, language="de"), 130)

    def test_progress_matches_real_install_phases_and_stops_after_failure(self):
        for result in (0,7):
            events=[];pacman=Mock();pacman.install.side_effect=lambda _packages:(events.append('install-returning'),result)[1]
            plan=BootstrapPlan(_assessment(),('retroarch',))
            code=run_bootstrap(plan,dry_run=False,input_function=lambda _:'yes',stream=StringIO(),
                               pacman=pacman,progress=events.append)
            self.assertEqual(code,result)
            self.assertEqual(events,['confirmation','repository','install-returning'])

    def test_os_release_recognizes_arch_ancestry_without_a_name_allowlist(self) -> None:
        with TemporaryDirectory() as directory:
            release = Path(directory) / "os-release"
            release.write_text('ID=cachyos\nNAME="CachyOS Linux"\nID_LIKE=arch\n')
            distro = read_os_release(release)
            self.assertTrue(distro.supports_automatic_install)
            self.assertEqual(distro.distro_id, "cachyos")
            release.write_text("ID=arch\nNAME=Arch\n")
            self.assertTrue(read_os_release(release).supports_automatic_install)
            release.write_text('ID=garuda\nPRETTY_NAME="Garuda Linux"\nID_LIKE="arch"\n')
            garuda = read_os_release(release)
            self.assertEqual((garuda.distro_id, garuda.name, garuda.id_like),
                             ("garuda", "Garuda Linux", ("arch",)))
            self.assertTrue(garuda.supports_automatic_install)
            release.write_text("ID=unvalidated-derivative\nID_LIKE=arch\n")
            self.assertTrue(read_os_release(release).supports_automatic_install)
            release.write_text("ID=endeavouros\nID_LIKE=arch\n")
            self.assertTrue(read_os_release(release).supports_automatic_install)
            release.write_text("ID=custom\nID_LIKE=\"arch other\"\n")
            self.assertTrue(read_os_release(release).supports_automatic_install)
            release.write_text("ID=ubuntu\nID_LIKE=debian\n")
            self.assertFalse(read_os_release(release).supports_automatic_install)

    def test_unsupported_distro_never_builds_install_plan(self) -> None:
        pacman = Mock()
        plan = create_bootstrap_plan(_assessment(distro="ubuntu"), pacman)
        self.assertEqual(plan.packages, ())
        pacman.available.assert_not_called()

    def test_ancestry_uses_exact_tokens_and_never_pacman_presence_alone(self):
        for distro in (DistroInfo("ubuntu", "Ubuntu", ("debian",)),
                       DistroInfo("fedora", "Fedora", ()),
                       DistroInfo("custom", "Custom", ("archlinux",)),
                       DistroInfo("unknown", "Unknown", ())):
            with self.subTest(distro=distro):
                self.assertFalse(distro.supports_automatic_install)
                pacman = Mock(is_available=Mock(return_value=True))
                plan = create_bootstrap_plan(HostAssessment(distro, (), (), ()), pacman)
                self.assertEqual(plan.packages, ())
                self.assertFalse(pacman.mock_calls)

    def test_endeavouros_keeps_repository_and_explicit_confirmation_contract(self):
        assessment = _assessment(distro="endeavouros")
        pacman, helper = Mock(), Mock()
        pacman.available.return_value = True
        pacman.install.return_value = 0
        plan = create_bootstrap_plan(assessment, pacman, helper)
        self.assertEqual(plan.packages, ("retroarch",))
        output = StringIO()
        self.assertEqual(run_bootstrap(plan, dry_run=False, input_function=lambda _: "",
                                      stream=output, pacman=pacman), 130)
        pacman.install.assert_not_called()
        self.assertEqual(run_bootstrap(plan, dry_run=False, input_function=lambda _: "yes",
                                      stream=output, pacman=pacman), 0)
        pacman.install.assert_called_once_with(("retroarch",))
        helper.install.assert_not_called()

    def test_missing_pacman_blocks_planning_before_repository_or_aur_queries(self):
        pacman, helper = Mock(), Mock()
        pacman.is_available.return_value = False
        plan = create_bootstrap_plan(_assessment(distro="endeavouros"), pacman, helper)
        self.assertEqual(plan.packages, ())
        self.assertEqual(plan.unavailable_packages, ("retroarch",))
        self.assertIn("Pacman is not available", plan.blocked_reason)
        pacman.available.assert_not_called()
        self.assertFalse(helper.mock_calls)

    def test_missing_pacman_blocks_precomputed_repository_and_aur_plans(self):
        for packages, community in ((("retroarch",), ()), ((), ("pcsx2-git",))):
            for language in ("de", "en"):
                with self.subTest(packages=packages, language=language):
                    pacman, helper, prompt = Mock(), Mock(), Mock()
                    pacman.is_available.return_value = False
                    plan = BootstrapPlan(_assessment(distro="endeavouros"), packages,
                                         aur_packages=community, aur_helper="paru")
                    output = StringIO()
                    self.assertEqual(run_bootstrap(plan, dry_run=False, input_function=prompt,
                        stream=output, pacman=pacman, aur_helper=helper, language=language), 2)
                    self.assertIn("Pacman", output.getvalue())
                    prompt.assert_not_called()
                    pacman.install.assert_not_called()
                    helper.install.assert_not_called()

    def test_pacman_adapter_never_invokes_a_missing_executable(self):
        runner = Mock()
        with patch("embercade.host_requirements.shutil.which", return_value=None):
            adapter = Pacman(runner)
            self.assertFalse(adapter.available("retroarch"))
            self.assertEqual(adapter.install(("retroarch",)), 127)
        runner.assert_not_called()

    def test_unsupported_distro_cannot_execute_even_a_prepopulated_install_plan(self):
        for distro in ('ubuntu','fedora','unvalidated-derivative'):
            for language in ('de','en'):
                with self.subTest(distro=distro,language=language):
                    pacman,aur=Mock(),Mock()
                    plan=BootstrapPlan(_assessment(distro=distro),('retroarch',),(),('pcsx2-git',),'paru')
                    prompt=Mock(side_effect=AssertionError('Unsupported host must not prompt to install'))
                    code=run_bootstrap(plan,dry_run=False,input_function=prompt,
                        stream=StringIO(),pacman=pacman,aur_helper=aur,language=language)
                    self.assertEqual(code,2)
                    self.assertFalse(pacman.mock_calls)
                    self.assertFalse(aur.mock_calls)
                    prompt.assert_not_called()

    def test_package_plan_only_contains_available_missing_packages(self) -> None:
        pacman = Mock()
        pacman.available.return_value = True
        plan = create_bootstrap_plan(_assessment(), pacman)
        self.assertEqual(plan.packages, ("retroarch",))
        self.assertEqual(
            plan.command, ("sudo", "pacman", "-S", "--needed", "retroarch")
        )

    def test_garuda_probes_configured_repository_git_variants_before_aur(self) -> None:
        requirements = tuple(RequirementStatus(r, False, "missing") for r in HOST_REQUIREMENTS
                             if r.key in {"retroarch", "dolphin", "pcsx2", "rpcs3", "xemu"})
        assessment = HostAssessment(DistroInfo("garuda", "Garuda Linux", ("arch",)), requirements, (), ())
        available = {"retroarch", "dolphin-emu", "pcsx2-git", "rpcs3-git", "xemu-git"}
        pacman = Mock()
        pacman.available.side_effect = lambda package: package in available
        helper = Mock(executable="/usr/bin/paru")
        plan = create_bootstrap_plan(assessment, pacman, helper)
        self.assertEqual(set(plan.packages), available)
        self.assertEqual(plan.unavailable_packages, ())
        self.assertEqual(plan.aur_packages, ())
        helper.available.assert_not_called()
        for package in ("pcsx2", "rpcs3", "xemu"):
            calls = [c.args[0] for c in pacman.available.call_args_list]
            self.assertLess(calls.index(package), calls.index(package+"-git"))
        output = StringIO()
        render_bootstrap_plan(plan, output)
        self.assertIn("PCSX2 (repository development package)", output.getvalue())
        self.assertNotIn("not supported", output.getvalue())
        pacman.install.return_value = 0
        run_bootstrap(plan, dry_run=False, input_function=lambda _: "", stream=output, pacman=pacman)
        pacman.install.assert_not_called()
        run_bootstrap(plan, dry_run=False, input_function=lambda _: "yes", stream=output, pacman=pacman)
        pacman.install.assert_called_once_with(plan.packages)

    def test_failed_repository_install_stops_before_community_install(self) -> None:
        pacman, helper = Mock(), Mock()
        pacman.install.return_value = 1
        plan = BootstrapPlan(_assessment(distro="garuda"), ("retroarch",), (), ("pcsx2-git",), "paru")
        output = StringIO()
        result = run_bootstrap(plan, dry_run=False, input_function=lambda _: "yes", stream=output,
                               pacman=pacman, aur_helper=helper)
        self.assertEqual(result, 1)
        helper.install.assert_not_called()
        self.assertIn("failed or was cancelled (exit 1)", output.getvalue())

    def test_cli_bootstrap_reports_input_cancellation_without_traceback(self) -> None:
        from embercade.cli import main
        with TemporaryDirectory() as directory:
            for error in (EOFError(), KeyboardInterrupt()):
                with self.subTest(error=type(error).__name__), \
                     patch("embercade.cli._assess_host", return_value=_assessment(distro="garuda")), \
                     patch("embercade.cli.AurHelper.detect", return_value=None), \
                     patch("embercade.cli.create_bootstrap_plan"), \
                     patch("embercade.cli.run_bootstrap", side_effect=error), \
                     patch("sys.stdout", new_callable=StringIO) as output:
                    self.assertEqual(main(["--config", str(Path(directory)/"absent.toml"), "bootstrap"]), 130)
                    self.assertIn("cancelled", output.getvalue())

    def test_stable_standalone_packages_precede_optional_git_candidates(self) -> None:
        requirements = {requirement.key: requirement for requirement in HOST_REQUIREMENTS}
        for emulator in ("pcsx2", "rpcs3", "xemu"):
            self.assertEqual(requirements[emulator].package, emulator)
            self.assertEqual(requirements[emulator].aur_package, f"{emulator}-git")

    def test_unavailable_repo_package_is_not_claimed_as_an_aur_result(self) -> None:
        pacman = Mock()
        pacman.available.return_value = False
        plan = create_bootstrap_plan(_assessment(), pacman)
        output = StringIO()

        render_bootstrap_plan(plan, output)

        rendered = output.getvalue()
        self.assertIn("Unavailable in configured pacman repositories", rendered)
        self.assertNotIn("Manual/AUR dependencies", rendered)

    def test_installed_requirement_is_not_planned(self) -> None:
        pacman = Mock()
        plan = create_bootstrap_plan(_assessment(installed=True), pacman)
        self.assertEqual(plan.packages, ())
        pacman.available.assert_not_called()

    def test_dry_run_and_default_no_never_call_sudo(self) -> None:
        assessment = _assessment()
        plan = BootstrapPlan(assessment, ("retroarch",))
        pacman = Mock()
        output = StringIO()
        self.assertEqual(
            run_bootstrap(plan, dry_run=True, stream=output, pacman=pacman), 0
        )
        pacman.install.assert_not_called()
        self.assertEqual(
            run_bootstrap(
                plan,
                dry_run=False,
                input_function=lambda _: "",
                stream=output,
                pacman=pacman,
            ),
            130,
        )
        pacman.install.assert_not_called()

    def test_confirmed_install_uses_argv_without_shell_or_syu(self) -> None:
        runner = Mock(
            return_value=subprocess.CompletedProcess([], returncode=0)
        )
        adapter = Pacman(runner)
        result = adapter.install(("retroarch", "bubblewrap"))
        self.assertEqual(result, 0)
        argv = runner.call_args.args[0]
        self.assertEqual(
            argv,
            ["sudo", "pacman", "-S", "--needed", "retroarch", "bubblewrap"],
        )
        self.assertNotIn("-Syu", argv)
        self.assertNotIn("shell", runner.call_args.kwargs)

    def test_package_availability_probe_is_read_only_argv(self) -> None:
        runner = Mock(return_value=subprocess.CompletedProcess([], returncode=0))
        self.assertTrue(Pacman(runner).available("retroarch"))
        self.assertEqual(runner.call_args.args[0], ["pacman", "-Si", "--", "retroarch"])
        self.assertNotIn("shell", runner.call_args.kwargs)

    def test_confirmed_bootstrap_delegates_exact_package_tuple(self) -> None:
        plan = BootstrapPlan(_assessment(), ("retroarch",))
        pacman = Mock()
        pacman.install.return_value = 0
        result = run_bootstrap(
            plan,
            dry_run=False,
            input_function=lambda _: "y",
            stream=StringIO(),
            pacman=pacman,
        )
        self.assertEqual(result, 0)
        pacman.install.assert_called_once_with(("retroarch",))

    def test_only_verified_core_package_mappings_are_present(self) -> None:
        self.assertEqual(CORE_ARCH_PACKAGES["mednafen_psx"], "libretro-beetle-psx-hw")
        self.assertEqual(CORE_ARCH_PACKAGES["mupen64plus-next"], "libretro-mupen64plus-next")
        self.assertNotIn("fbneo", CORE_ARCH_PACKAGES)
        self.assertNotIn("melondsds", CORE_ARCH_PACKAGES)
        self.assertNotIn("cemu", CORE_ARCH_PACKAGES)

    def test_active_collection_uses_system_definition_and_config_override(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms = root / "roms"
            (roms / "nes").mkdir(parents=True)
            (roms / "nes" / "Game.nes").write_bytes(b"rom")
            systems = root / "es_systems.cfg"
            systems.write_text(
                """<systemList><system><name>nes</name><path>/userdata/roms/nes</path>
                <extension>.nes</extension><emulators><emulator name="libretro"><cores>
                <core default="true">fceumm</core></cores></emulator></emulators>
                </system></systemList>""",
                encoding="utf-8",
            )
            defaults = root / "default.conf"
            defaults.write_text("nes.emulator=libretro\nnes.core=nestopia\n")
            user = root / "user.conf"
            user.write_text("nes.core=mgba\n")
            active, cores = active_libretro_cores(roms, systems, defaults, user)
            self.assertEqual(active, ("nes",))
            self.assertEqual(cores, ("mgba",))

    def test_manual_core_missing_has_no_guessed_package(self) -> None:
        assessment = HostAssessment(
            DistroInfo("arch", "Arch", ()),
            (),
            (CoreRequirementStatus("cemu", False, "missing", None),),
            ("wiiu",),
        )
        pacman = Mock()
        plan = create_bootstrap_plan(assessment, pacman)
        self.assertEqual(plan.packages, ())
        pacman.available.assert_not_called()

    def test_package_availability_is_probed_on_each_host(self) -> None:
        first = Mock()
        first.available.return_value = True
        second = Mock()
        second.available.return_value = False
        self.assertEqual(create_bootstrap_plan(_assessment(), first).packages, ("retroarch",))
        self.assertEqual(create_bootstrap_plan(_assessment(), second).packages, ())

    def test_aur_helper_absent_has_no_aur_plan(self) -> None:
        with unittest.mock.patch("embercade.host_requirements.shutil.which", return_value=None):
            self.assertIsNone(AurHelper.detect({"PATH": ""}))

    def test_existing_aur_helper_is_queried_without_repo_changes(self) -> None:
        runner = Mock(return_value=subprocess.CompletedProcess([], 0))
        with unittest.mock.patch(
            "embercade.host_requirements.shutil.which", side_effect=["/usr/bin/paru"]
        ):
            helper = AurHelper.detect({"PATH": "/usr/bin"}, runner)
        self.assertIsNotNone(helper)
        assert helper is not None
        self.assertTrue(helper.available("pcsx2-git"))
        self.assertEqual(runner.call_args.args[0], ["/usr/bin/paru", "-Si", "--", "pcsx2-git"])
        self.assertNotIn("pacman.conf", str(runner.call_args))

    def test_unavailable_stable_package_can_be_offered_by_existing_aur_helper(self) -> None:
        requirement = next(item for item in HOST_REQUIREMENTS if item.key == "pcsx2")
        assessment = HostAssessment(
            DistroInfo("arch", "Arch", ()),
            (RequirementStatus(requirement, False, "missing"),),
            (),
            ("ps2",),
        )
        pacman = Mock()
        pacman.available.return_value = False
        helper = Mock(executable="/usr/bin/paru")
        helper.available.return_value = True
        plan = create_bootstrap_plan(assessment, pacman, helper)
        self.assertEqual(plan.packages, ())
        self.assertEqual(plan.aur_packages, ("pcsx2-git",))
        helper.available.assert_called_once_with("pcsx2-git")

    def test_git_variant_is_not_offered_when_official_package_exists(self) -> None:
        requirement = next(item for item in HOST_REQUIREMENTS if item.key == "pcsx2")
        assessment = HostAssessment(
            DistroInfo("arch", "Arch", ()),
            (RequirementStatus(requirement, False, "missing"),),
            (),
            ("ps2",),
        )
        pacman = Mock()
        pacman.available.return_value = True
        helper = Mock(executable="/usr/bin/paru")
        helper.available.return_value = True
        plan = create_bootstrap_plan(assessment, pacman, helper)
        self.assertEqual(plan.packages, ("pcsx2",))
        self.assertEqual(plan.aur_packages, ())
        helper.available.assert_not_called()

    def test_aur_installation_also_defaults_to_no(self) -> None:
        helper = Mock()
        plan = BootstrapPlan(_assessment(), (), (), ("retroarch-git",), "/usr/bin/paru")
        run_bootstrap(
            plan,
            dry_run=False,
            input_function=lambda _: "",
            stream=StringIO(),
            aur_helper=helper,
        )
        helper.install.assert_not_called()

    def test_selected_git_variant_does_not_also_install_stable_variant(self) -> None:
        helper = Mock()
        pacman = Mock()
        answers = iter(("y", "y"))
        plan = BootstrapPlan(
            _assessment(), ("retroarch",), (), ("retroarch-git",), "/usr/bin/paru"
        )
        result = run_bootstrap(
            plan,
            dry_run=False,
            input_function=lambda _: next(answers),
            stream=StringIO(),
            pacman=pacman,
            aur_helper=helper,
        )
        self.assertEqual(result, helper.install.return_value)
        pacman.install.assert_not_called()
        helper.install.assert_called_once_with(("retroarch-git",))

    def test_simple_output_hides_package_names_and_verbose_shows_them(self) -> None:
        plan = BootstrapPlan(_assessment(), ("retroarch",))
        simple = StringIO()
        verbose = StringIO()
        render_bootstrap_plan(plan, simple)
        render_bootstrap_plan(plan, verbose, verbose=True)
        self.assertNotIn("sudo pacman", simple.getvalue())
        self.assertIn("RetroArch", simple.getvalue())
        self.assertIn("sudo pacman -S --needed retroarch", verbose.getvalue())


class XeniaProviderDiagnosticTests(unittest.TestCase):
    def _environment(self, root: Path) -> dict[str, str]:
        return {"HOME": str(root), "XDG_DATA_HOME": str(root / "data"), "PATH": ""}

    def _provider(self, path: Path, *, executable: bool = True) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(elf(appimage=True, symbols=False))
        path.chmod(0o700 if executable else 0o600)
        return path

    def test_absent_provider_is_optional_or_missing_for_active_collection(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            resolver = ExecutableResolver(environment=environment)
            for needed, expected in ((False, "OPTIONAL"), (True, "MISSING")):
                with self.subTest(needed=needed):
                    status = inspect_xenia_provider(resolver, environment, needed=needed)
                    self.assertEqual(status.status, expected)
                    self.assertEqual(status.needed, needed)
                    self.assertFalse(status.available)

    def test_managed_appimage_is_readonly_validated_and_distinguished(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            path = self._provider(recommended_xenia_directory(environment) / "Emulator.AppImage")
            resolver = ExecutableResolver(
                providers={"xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(path))},
                environment=environment,
            )
            before = (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns)
            with patch("embercade.imports._provider_metadata", return_value=PROVIDER_METADATA):
                status = inspect_xenia_provider(resolver, environment, needed=True)
            self.assertEqual(status.status, "MANAGED")
            self.assertTrue(status.available)
            self.assertEqual(status.path, str(path))
            self.assertEqual((path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns), before)

    def test_explicit_override_precedes_configured_managed_provider(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            override = self._provider(root / "External.AppImage")
            managed = self._provider(recommended_xenia_directory(environment) / "Managed.AppImage")
            resolver = ExecutableResolver(
                {"xenia-edge": str(override)},
                providers={"xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(managed))},
                environment=environment,
            )
            with patch("embercade.imports._provider_metadata", return_value=PROVIDER_METADATA):
                status = inspect_xenia_provider(resolver, environment, needed=True)
            self.assertEqual(status.status, "OVERRIDE")
            self.assertEqual(status.path, str(override))
            self.assertEqual(status.source, "executables override")

    def test_configured_external_appimage_is_not_an_executables_override(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = self._provider(root / "External.AppImage")
            resolver = ExecutableResolver(
                providers={"xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(path))},
                environment=environment,
            )
            with patch("embercade.imports._provider_metadata", return_value=PROVIDER_METADATA):
                status = inspect_xenia_provider(resolver, environment, needed=True)
            self.assertEqual(status.status, "FOUND")
            self.assertEqual(status.summary, "ready, external provider")
            self.assertEqual(status.source, "configured provider")
            self.assertIn("External Xenia Edge AppImage", status.detail)

    def test_explicit_provider_type_is_described_as_override(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = self._provider(root / "External.AppImage")
            resolver = ExecutableResolver(
                providers={"xenia-edge": EmulatorProvider(ProviderType.EXPLICIT, str(path))},
                environment=environment,
            )
            with patch("embercade.imports._provider_metadata", return_value=PROVIDER_METADATA):
                status = inspect_xenia_provider(resolver, environment, needed=True)
            self.assertEqual(status.status, "OVERRIDE")
            self.assertEqual(status.summary, "ready, explicit override")

    def test_inspection_tool_unavailability_or_timeout_does_not_prove_corruption(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = self._provider(root / "External.AppImage")
            resolver = ExecutableResolver({"xenia-edge": str(path)}, environment=environment)
            for error in (
                "cannot inspect AppImage identity: unsquashfs is unavailable",
                "AppImage metadata inspection timed out",
            ):
                with self.subTest(error=error), patch(
                    "embercade.imports._provider_metadata", side_effect=ManagedImportError(error),
                ):
                    status = inspect_xenia_provider(resolver, environment, needed=True)
                    self.assertEqual(status.status, "UNVERIFIED")
                    self.assertFalse(status.available)
                    self.assertIn("not verified", status.summary)
                    self.assertEqual(status.detail, error)

    def test_unselected_discovery_timeout_is_not_described_as_invalid_provider(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            with patch(
                "embercade.setup_flow.detect_xenia_edge",
                side_effect=SetupError("AppImage metadata inspection timed out"),
            ):
                status = inspect_xenia_provider(
                    ExecutableResolver(environment=environment), environment, needed=True,
                )
            self.assertEqual(status.status, "UNVERIFIED")
            self.assertFalse(status.available)

    def test_missing_override_does_not_fall_back_to_managed_discovery(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            self._provider(recommended_xenia_directory(environment) / "Managed.AppImage")
            missing = root / "Missing.AppImage"
            resolver = ExecutableResolver({"xenia-edge": str(missing)}, environment=environment)
            with patch("embercade.setup_flow.detect_xenia_edge") as detect:
                status = inspect_xenia_provider(resolver, environment, needed=True)
            self.assertEqual(status.status, "MISSING")
            self.assertEqual(status.path, str(missing))
            detect.assert_not_called()

    def test_corrupt_appimage_is_not_reported_ready(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = self._provider(root / "Broken.AppImage")
            path.write_bytes(b"\x7fELFbroken")
            resolver = ExecutableResolver({"xenia-edge": str(path)}, environment=environment)
            status = inspect_xenia_provider(resolver, environment, needed=True)
            self.assertEqual(status.status, "INVALID")
            self.assertIn("truncated ELF", status.detail)
            self.assertFalse(status.available)

    def test_unexecutable_provider_is_invalid_even_when_optional(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = self._provider(root / "Not Executable.AppImage", executable=False)
            resolver = ExecutableResolver({"xenia-edge": str(path)}, environment=environment)
            status = inspect_xenia_provider(resolver, environment, needed=False)
            self.assertEqual(status.status, "INVALID")
            self.assertFalse(status.available)

    def test_native_path_provider_is_not_inspected_as_an_appimage(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = root / "xenia_edge"
            path.write_text("#!/bin/sh\nexit 99\n")
            path.chmod(0o700)
            environment["PATH"] = str(root)
            with patch("embercade.imports.inspect_provider") as inspect:
                status = inspect_xenia_provider(
                    ExecutableResolver(environment=environment), environment, needed=True,
                )
            self.assertEqual(status.status, "FOUND")
            self.assertTrue(status.available)
            inspect.assert_not_called()

    def test_unselected_managed_copy_does_not_claim_launch_ready(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            path = self._provider(recommended_xenia_directory(environment) / "Managed.AppImage")
            with patch("embercade.setup_flow.detect_xenia_edge", return_value=path):
                status = inspect_xenia_provider(
                    ExecutableResolver(environment=environment), environment, needed=True,
                )
            self.assertEqual(status.status, "UNSELECTED")
            self.assertIn("setup", status.summary)
            self.assertFalse(status.available)

    def test_ambiguous_managed_discovery_does_not_select_a_candidate(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            with patch(
                "embercade.setup_flow.detect_xenia_edge",
                side_effect=SetupError("Multiple different Xenia Edge AppImages found; choose one explicitly."),
            ):
                status = inspect_xenia_provider(
                    ExecutableResolver(environment=environment), environment, needed=True,
                )
            self.assertEqual(status.status, "AMBIGUOUS")
            self.assertIsNone(status.path)
            self.assertFalse(status.available)

    def test_damaged_unconfigured_managed_file_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            path = self._provider(recommended_xenia_directory(environment) / "Managed.AppImage")
            path.write_bytes(b"broken")
            with patch("embercade.setup_flow.detect_xenia_edge", return_value=None):
                status = inspect_xenia_provider(
                    ExecutableResolver(environment=environment), environment, needed=True,
                )
            self.assertEqual(status.status, "INVALID")
            self.assertEqual(status.path, str(path))

    def test_unknown_managed_appimage_is_ignored(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            self._provider(recommended_xenia_directory(environment) / "Other.AppImage")
            with (
                patch("embercade.setup_flow.detect_xenia_edge", return_value=None),
                patch("embercade.imports._provider_metadata", return_value={"Name": "Other App"}),
            ):
                status = inspect_xenia_provider(
                    ExecutableResolver(environment=environment), environment, needed=False,
                )
            self.assertEqual(status.status, "OPTIONAL")

    def test_host_summary_uses_diagnosis_without_revealing_paths_by_default(self) -> None:
        with TemporaryDirectory() as directory:
            environment = self._environment(Path(directory))
            status = inspect_xenia_provider(
                ExecutableResolver(environment=environment), environment, needed=False,
            )
            assessment = HostAssessment(DistroInfo("arch", "Arch", ()), (), (), (), xenia_provider=status)
            output = StringIO()
            render_host_summary(assessment, output)
            self.assertIn("optional, not needed for this collection", output.getvalue())
            self.assertNotIn(directory, output.getvalue())

    def test_assessment_keeps_invalid_provider_out_of_launch_ready_field(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = self._provider(root / "Broken.AppImage")
            path.write_bytes(b"broken")
            resolver = ExecutableResolver({"xenia-edge": str(path)}, environment=environment)
            with (
                patch("embercade.host_requirements._active_routes", return_value=(("xbox360",), (), ("xenia-edge",))),
                patch("embercade.host_requirements._probe_requirement", side_effect=lambda item, *_: RequirementStatus(item, False, "not installed")),
            ):
                assessment = assess_host(
                    resolver=resolver, core_resolver=Mock(), environment=environment,
                    rom_root=root, systems_config=root / "systems", default_config=root / "defaults",
                    user_config=root / "user", distro=DistroInfo("arch", "Arch", ()),
                )
            self.assertIsNone(assessment.xenia_edge)
            self.assertEqual(assessment.xenia_provider.status, "INVALID")
            self.assertTrue(assessment.xenia_provider.needed)
            self.assertNotIn("fuse2", (item.requirement.key for item in assessment.requirements))

    def test_provider_removed_during_assessment_is_reported_without_crashing(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self._environment(root)
            path = root / "xenia_edge"
            path.write_bytes(b"host binary")
            resolved = ResolvedExecutable("xenia-edge", path, "PATH", ProviderType.NATIVE)
            resolver = ExecutableResolver(environment=environment)
            calls = 0

            def resolve(_name: str):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return resolved
                path.unlink()
                raise ExecutableResolutionError("Provider disappeared during assessment")

            with (
                patch.object(resolver, "resolve", side_effect=resolve),
                patch("embercade.host_requirements._active_routes", return_value=(("xbox360",), (), ("xenia-edge",))),
                patch("embercade.host_requirements._probe_requirement", side_effect=lambda item, *_: RequirementStatus(item, False, "not installed")),
            ):
                assessment = assess_host(
                    resolver=resolver, core_resolver=Mock(), environment=environment,
                    rom_root=root, systems_config=root / "systems", default_config=root / "defaults",
                    user_config=root / "user", distro=DistroInfo("arch", "Arch", ()),
                )
            self.assertIsNone(assessment.xenia_edge)
            self.assertEqual(assessment.xenia_provider.status, "MISSING")
            self.assertNotIn("systemd-run", (item.requirement.key for item in assessment.requirements))

if __name__ == "__main__":
    unittest.main()

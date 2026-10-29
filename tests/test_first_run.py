"""First-run wizard contracts: no source writes, shell strings or setup forks."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import os
import subprocess
import unittest

from embercade.first_run import (
    FirstRunError, action_arguments, branding_icon, friendly_failure, launcher_command,
    read_state, run_action, setup_arguments,
)
from embercade.first_run_ui import Gamepad, Wizard
from embercade.host_requirements import DistroInfo


class FirstRunTests(unittest.TestCase):
    def test_fresh_open_is_read_only_and_unconfigured(self):
        with TemporaryDirectory() as directory:
            config = Path(directory) / "config" / "embercade.toml"
            state = read_state(config, {"HOME": directory})
            self.assertFalse(state.configured)
            self.assertEqual(state.roms, "")
            self.assertFalse(config.parent.exists())

    def test_existing_config_is_recognized_without_rewriting(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios = root / "ROM files", root / "BIOS files"
            roms.mkdir()
            bios.mkdir()
            config = root / "embercade.toml"
            config.write_text(f'[paths]\nroms="{roms}"\nbios="{bios}"\n[controller]\nexit_hotkey="guide-start"\n')
            before = config.stat().st_mtime_ns
            state = read_state(config, {"HOME": directory})
            self.assertTrue(state.configured)
            self.assertEqual(state.exit_hotkey, "guide-start")
            self.assertEqual(config.stat().st_mtime_ns, before)

    def test_invalid_existing_config_is_not_repaired_or_overwritten(self):
        with TemporaryDirectory() as directory:
            config = Path(directory) / "embercade.toml"
            config.write_text("[paths\ninvalid")
            original = config.read_bytes()
            with self.assertRaises(FirstRunError):
                read_state(config)
            self.assertEqual(config.read_bytes(), original)

    def test_setup_argv_keeps_paths_with_spaces_as_single_arguments(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios, cores, providers, ppsspp, xemu = (root / item for item in
                ("ROM files", "BIOS files", "Core files", "AppImage files", "PSP assets", "Xbox files"))
            for path in (roms, bios, cores, providers, ppsspp, xemu):
                path.mkdir()
            (ppsspp / "ppge_atlas.zim").write_bytes(b"atlas")
            (ppsspp / "lang").mkdir()
            (ppsspp / "flash0").mkdir()
            for name in ("Complex_4627.bin", "mcpx_1.0.bin", "xbox_hdd.qcow2"):
                (xemu / name).write_bytes(b"source")
            arguments = setup_arguments(
                root / "config.toml", roms=str(roms), bios=str(bios),
                exit_hotkey="back-start", cores_from=str(cores),
                providers_from=str(providers),
                ppsspp_assets_from=str(ppsspp), xemu_files_from=str(xemu),
            )
            self.assertEqual(arguments[arguments.index("--roms") + 1], str(roms))
            self.assertEqual(arguments[arguments.index("--providers-from") + 1], str(providers))
            self.assertEqual(arguments[arguments.index("--exit-hotkey") + 1], "back-start")
            self.assertEqual(arguments[arguments.index("--ppsspp-assets-from") + 1], str(ppsspp))
            self.assertEqual(arguments[arguments.index("--xemu-files-from") + 1], str(xemu))

    def test_existing_psp_choice_is_shown_without_rewriting_config(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios, assets = root / "roms", root / "bios", root / "psp"
            for path in (roms, bios, assets):
                path.mkdir()
            config = root / "embercade.toml"
            config.write_text(f'[paths]\nroms="{roms}"\nbios="{bios}"\n[libretro]\nppsspp_assets="{assets}"\n')
            original = config.read_bytes()
            self.assertEqual(read_state(config, {"HOME": directory}).ppsspp_assets, str(assets))
            self.assertEqual(config.read_bytes(), original)

    def test_imported_files_show_ready_status_without_requiring_source_paths(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            roms, bios = root / "roms", root / "bios"
            roms.mkdir()
            bios.mkdir()
            data = root / ".local/share/embercade"
            cores = data / "cores"
            cores.mkdir(parents=True)
            (cores / "nestopia_libretro.so").write_bytes(b"core")
            provider = data / "providers/xenia/xenia_edge_linux.AppImage"
            provider.parent.mkdir(parents=True)
            provider.write_bytes(b"provider")
            from embercade.paths import EmbercadePaths
            from embercade.xemu import isolated_xemu_files
            files = isolated_xemu_files(EmbercadePaths.from_environment({"HOME": directory}))
            for path in (files.flashrom, files.bootrom, files.hdd):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"workfile")
            config = root / "embercade.toml"
            config.write_text(f'[paths]\nroms="{roms}"\nbios="{bios}"\n')
            with patch("embercade.first_run.detect_xenia_edge", return_value=provider):
                state = read_state(config, {"HOME": directory})
            self.assertEqual(state.managed_cores, 1)
            self.assertTrue(state.managed_xenia)
            self.assertTrue(state.xemu_prepared)
            self.assertEqual(config.read_text(), f'[paths]\nroms="{roms}"\nbios="{bios}"\n')

    def test_invalid_source_refuses_setup_before_any_backend_call(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FirstRunError):
                setup_arguments(root / "config.toml", roms=directory, bios=directory,
                                exit_hotkey="back-start", cores_from=str(root / "missing"))

    def test_incomplete_psp_and_xbox_sources_are_rejected_before_setup(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            psp, xbox = root / "psp", root / "xbox"
            psp.mkdir()
            xbox.mkdir()
            with self.assertRaisesRegex(FirstRunError, "ppge_atlas.zim"):
                setup_arguments(root / "config.toml", roms=directory, bios=directory,
                                exit_hotkey="back-start", ppsspp_assets_from=str(psp))
            with self.assertRaisesRegex(FirstRunError, "Complex_4627.bin"):
                setup_arguments(root / "config.toml", roms=directory, bios=directory,
                                exit_hotkey="back-start", xemu_files_from=str(xbox))

    def test_blank_optional_sources_never_infer_the_general_bios_folder(self):
        with TemporaryDirectory() as directory:
            # Even a populated general BIOS folder is not an explicit selection.
            with patch("embercade.first_run.validate_ppsspp_assets") as psp, \
                 patch("embercade.first_run.xemu_source_environment") as xbox:
                arguments = setup_arguments(Path(directory) / "fresh.toml", roms=directory,
                    bios=directory, exit_hotkey="back-start")
            self.assertNotIn("--ppsspp-assets-from", arguments)
            self.assertNotIn("--xemu-files-from", arguments)
            psp.assert_not_called()
            xbox.assert_not_called()

    def test_skip_assets_discards_unsubmitted_invalid_sources_only(self):
        for existing in ("", "/saved PSP assets"):
            with self.subTest(existing=existing):
                wizard = Wizard.__new__(Wizard)
                wizard.state = Mock(ppsspp_assets=existing)
                wizard.ppsspp, wizard.xemu = "/incomplete PSP", "/general BIOS"
                wizard.ppsspp_entry, wizard.xemu_entry = Mock(), Mock()
                wizard._apply = Mock()
                with patch("embercade.first_run_ui.validate_asset_sources") as validate:
                    wizard._skip_assets()
                self.assertEqual((wizard.ppsspp, wizard.xemu), (existing, ""))
                wizard._apply.assert_called_once_with(next_page="host")
                validate.assert_not_called()

    def test_blank_asset_fields_advance_and_incomplete_choices_can_be_skipped(self):
        with TemporaryDirectory() as directory:
            wizard = Wizard.__new__(Wizard)
            wizard.state = Mock(ppsspp_assets="")
            wizard.language = "en"
            wizard.ppsspp_entry = Mock(get_text=lambda: "")
            wizard.xemu_entry = Mock(get_text=lambda: "")
            wizard._apply, wizard._message = Mock(), Mock()
            wizard._save_assets()
            wizard._apply.assert_called_once_with(next_page="host")
            wizard._message.assert_not_called()
            for field in (wizard.ppsspp_entry, wizard.xemu_entry):
                wizard._apply.reset_mock(); wizard._message.reset_mock()
                field.get_text = lambda: directory
                wizard._save_assets()
                wizard._apply.assert_not_called()
                self.assertIn("Skip for now", wizard._message.call_args.args[1])
                field.get_text = lambda: ""
            wizard._skip_assets()
            wizard._apply.assert_called_once_with(next_page="host")

    def test_unchanged_psp_configuration_is_not_reimported_when_other_paths_change(self):
        with TemporaryDirectory() as directory:
            from embercade.setup_flow import configure
            from embercade.runtime import load_config
            root = Path(directory)
            roms, bios, assets = (root / name for name in ("ROMs", "BIOS", "PSP"))
            for path in (roms, bios, assets): path.mkdir()
            (assets / "ppge_atlas.zim").write_bytes(b"atlas")
            for name in ("lang", "flash0"): (assets / name).mkdir()
            config = root / "config.toml"
            configure(config, roms_value=str(roms), bios_value=str(bios),
                      ppsspp_assets_value=str(assets))
            state = read_state(config, {"HOME": directory})
            wizard = Wizard.__new__(Wizard)
            wizard.state = state
            wizard.roms, wizard.bios, wizard.hotkey = str(roms), str(bios), "guide-start"
            wizard.ppsspp, wizard.xemu = "/bad draft", "/bad draft"
            wizard.cores = wizard.providers = wizard.shadps4 = ""
            wizard._run_arguments = Mock()
            wizard._skip_assets()
            argv = wizard._run_arguments.call_args.args[0]
            self.assertNotIn("--ppsspp-assets-from", argv)
            self.assertNotIn("--xemu-files-from", argv)
            # The existing writer's omitted-source contract preserves the value.
            configure(config, roms_value=str(roms), bios_value=str(bios), exit_hotkey="guide-start")
            self.assertEqual(load_config(config)["libretro"]["ppsspp_assets"], str(assets))

    def test_backend_actions_are_existing_cli_commands(self):
        config = Path("/tmp/example settings/embercade.toml")
        self.assertEqual(action_arguments(config, "doctor"),
                         ("--config", str(config), "doctor"))
        self.assertEqual(action_arguments(config, "bootstrap-plan")[-2:],
                         ("bootstrap", "--dry-run"))
        self.assertEqual(action_arguments(config, "steam")[-2:], ("steam", "--yes"))
        with self.assertRaises(FirstRunError):
            action_arguments(config, "purge")

    def test_run_action_uses_argv_and_never_a_shell(self):
        with patch("embercade.first_run.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "ok", "")
            run_action(("/bin/embercade",), ("setup", "--roms", "/some ROMs"))
            self.assertEqual(run.call_args.args[0],
                             ["/bin/embercade", "setup", "--roms", "/some ROMs"])
            self.assertNotIn("shell", run.call_args.kwargs)
            self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_installed_launcher_is_resolved_from_same_prefix(self):
        with TemporaryDirectory() as directory:
            launcher = Path(directory) / "bin" / "embercade"
            launcher.parent.mkdir()
            launcher.touch()
            self.assertEqual(launcher_command({"EMBERCADE_PREFIX": directory}), (str(launcher),))

    def test_branding_reuses_staged_product_icon(self):
        with TemporaryDirectory() as directory:
            icon = Path(directory) / "resources/branding/icon/embercade-256.png"
            icon.parent.mkdir(parents=True)
            icon.write_bytes(b"test icon")
            self.assertEqual(branding_icon({"EMBERCADE_PROJECT_ROOT": directory}), icon)
            self.assertIsNone(branding_icon({"EMBERCADE_PROJECT_ROOT": "/missing/icon/root"}))

    def test_friendly_error_does_not_expose_traceback_when_cli_reports_error(self):
        result = subprocess.CompletedProcess([], 2, "", "usage: embercade\nembercade: error: ROM directory does not exist\n")
        self.assertEqual(friendly_failure(result), "ROM directory does not exist")

    def test_gamepad_rising_edges_and_reenumeration(self):
        class FakeSDL:
            pressed = {0, 11}
            attached = True
            opens = 0

            def SDL_PumpEvents(self): pass
            def SDL_NumJoysticks(self): return 1
            def SDL_IsGameController(self, _index): return True
            def SDL_GameControllerOpen(self, _index):
                self.opens += 1
                self.attached = True
                return 123
            def SDL_GameControllerGetAttached(self, _controller): return self.attached
            def SDL_GameControllerGetButton(self, _controller, index): return index in self.pressed
            def SDL_GameControllerClose(self, _controller): pass

        pad = Gamepad.__new__(Gamepad)
        pad.lib, pad.controller, pad.previous = FakeSDL(), None, set()
        self.assertEqual(pad.poll(), {"a", "up"})
        self.assertEqual(pad.poll(), set())
        pad.lib.pressed = {1}
        self.assertEqual(pad.poll(), {"b"})
        pad.lib.attached = False
        pad.lib.pressed = {0}
        self.assertEqual(pad.poll(), {"a"})
        self.assertEqual(pad.lib.opens, 2)
        pad.close()

    def test_back_navigation_preserves_unsubmitted_paths_and_sources(self):
        class Entry:
            def __init__(self, value): self.value = value
            def get_text(self): return self.value

        wizard = Wizard.__new__(Wizard)
        wizard._go = lambda page: setattr(wizard, "page", page)
        wizard.page = "paths"
        wizard.rom_entry, wizard.bios_entry = Entry("/games with spaces"), Entry("/BIOS")
        wizard._back()
        self.assertEqual((wizard.page, wizard.roms, wizard.bios),
                         ("welcome", "/games with spaces", "/BIOS"))

        wizard.page = "sources"
        wizard.core_entry, wizard.provider_entry = Entry("/cores"), Entry("/AppImages")
        wizard._back()
        self.assertEqual((wizard.page, wizard.cores, wizard.providers),
                         ("paths", "/cores", "/AppImages"))

        wizard.page = "assets"
        wizard.ppsspp_entry, wizard.xemu_entry = Entry("/PSP assets"), Entry("/Xbox files")
        wizard._back()
        self.assertEqual((wizard.page, wizard.ppsspp, wizard.xemu),
                     ("shadps4", "/PSP assets", "/Xbox files"))

    def test_unsupported_host_gets_explanation_before_confirmation_or_terminal(self):
        for distro in ('ubuntu','fedora','unknown','unvalidated-derivative'):
            for language in ('de','en'):
                with self.subTest(distro=distro,language=language):
                    wizard=Wizard.__new__(Wizard)
                    wizard.busy,wizard.message_dialog,wizard.language=False,None,language
                    wizard._question=Mock(side_effect=AssertionError('No install confirmation on unsupported systems'))
                    wizard._message=Mock()
                    with patch('embercade.first_run_ui.read_os_release',return_value=DistroInfo(distro,distro,('debian',) if distro=='ubuntu' else ())), patch('embercade.first_run_ui.TerminalInstallation.start') as launch:
                        wizard._bootstrap()
                        launch.assert_not_called()
                    wizard._question.assert_not_called()
                    wizard._message.assert_called_once()
                    title,body=wizard._message.call_args.args
                    self.assertEqual(title,'Unsupported distribution')
                    for text in (distro,'pacman','Arch'):
                        self.assertIn(text,body)
                    self.assertIn('keine Pakete' if language=='de' else 'No packages',body)
                    self.assertFalse(wizard.busy)

    def test_bootstrap_requires_confirmation_and_tracks_own_transaction(self):
        wizard = Wizard.__new__(Wizard)
        wizard.busy, wizard.message_dialog, wizard.language = False, None, "en"
        wizard.state = Mock(config_path=Path("/settings with spaces/config.toml"))
        wizard.command = ("/mounted AppImage/usr/bin/embercade",)
        wizard._question, wizard._message = Mock(return_value=False), Mock()
        wizard.window, wizard.GLib, wizard._label, wizard.root = Mock(), Mock(), Mock(), Mock()
        with patch("embercade.first_run_ui.read_os_release", return_value=DistroInfo("arch", "Arch Linux", ())), patch("embercade.first_run_ui.TerminalInstallation.start") as launch:
            wizard._bootstrap()
            launch.assert_not_called()
            wizard._question.return_value = True
            wizard._bootstrap()
            self.assertEqual(launch.call_args.args[:2], (wizard.command, wizard.state.config_path))
            self.assertEqual(launch.call_args.args[-1], "en")
            self.assertTrue(wizard.busy)
            wizard.GLib.timeout_add.assert_any_call(150, wizard._host_poll, launch.return_value)

    def test_missing_pacman_explained_before_confirmation_or_terminal(self):
        wizard = Wizard.__new__(Wizard)
        wizard.busy, wizard.message_dialog, wizard.language = False, None, "de"
        wizard._message, wizard._question = Mock(), Mock()
        with patch("embercade.first_run_ui.read_os_release", return_value=DistroInfo("endeavouros", "EndeavourOS", ("arch",))), \
             patch("embercade.first_run_ui.Pacman.is_available", return_value=False), \
             patch("embercade.first_run_ui.TerminalInstallation.start") as launch:
            wizard._bootstrap()
        wizard._question.assert_not_called()
        launch.assert_not_called()
        self.assertEqual(wizard._message.call_args.args[0], "Pacman unavailable")
        self.assertFalse(wizard.busy)

    def test_bootstrap_without_terminal_does_not_install_or_close_wizard(self):
        wizard = Wizard.__new__(Wizard)
        wizard.busy, wizard.message_dialog, wizard.language = False, None, "de"
        wizard._message, wizard._question = Mock(), Mock(return_value=True)
        wizard.state, wizard.command = Mock(config_path=Path("/config")), ("embercade",)
        with patch("embercade.first_run_ui.read_os_release", return_value=DistroInfo("arch", "Arch Linux", ())), patch("embercade.first_run_ui.TerminalInstallation.start", side_effect=FileNotFoundError):
            wizard._bootstrap()
            wizard._message.assert_called_once()
            self.assertFalse(wizard.busy)

    def test_terminal_outcomes_always_recheck_and_restore_retry_controls(self):
        for outcome, code in (("success", 0), ("failed", 7), ("cancelled", 130), ("unknown", 0)):
            with self.subTest(outcome=outcome):
                wizard = Wizard.__new__(Wizard)
                wizard.busy = True
                wizard.window, wizard.root, wizard.progress, wizard._run = Mock(), Mock(), Mock(), Mock()
                wizard.progress.get_parent.return_value = wizard.root
                transaction = Mock()
                transaction.result.return_value = dict(outcome=outcome, code=code)
                with patch("embercade.first_run_ui.threading.Thread"):
                    self.assertFalse(wizard._host_poll(transaction))
                self.assertFalse(wizard.busy)
                wizard.window.set_sensitive.assert_called_once_with(True)
                wizard._run.assert_called_once_with("host-status", wizard._host_finished)
                self.assertEqual(wizard.host_result["outcome"], outcome)
        transaction.result.return_value = None
        wizard._run.reset_mock()
        self.assertTrue(wizard._host_poll(transaction))
        wizard._run.assert_not_called()

    def test_worker_failure_restores_wizard_without_advancing(self):
        wizard = Wizard.__new__(Wizard)
        wizard.busy, wizard.page = True, "checks"
        wizard.window, wizard._message = Mock(), Mock()
        callback = Mock()
        self.assertFalse(wizard._done(OSError("backend failed"), callback))
        self.assertFalse(wizard.busy)
        wizard.window.set_sensitive.assert_called_once_with(True)
        callback.assert_not_called()
        self.assertEqual(wizard.page, "checks")

    def test_asset_page_accepts_xbox_source_without_eeprom(self):
        with TemporaryDirectory() as directory:
            source = Path(directory)
            for name in ("Complex_4627.bin", "mcpx_1.0.bin", "xbox_hdd.qcow2"):
                (source/name).write_bytes(b"read-only source")
            wizard = Wizard.__new__(Wizard)
            wizard.ppsspp_entry = Mock(get_text=lambda: "")
            wizard.xemu_entry = Mock(get_text=lambda: directory)
            wizard._go, wizard._message, wizard._apply = Mock(), Mock(), Mock()
            wizard._save_assets()
            wizard._apply.assert_called_once_with(next_page="host")
            wizard._message.assert_not_called()
            (source/"mcpx_1.0.bin").unlink()
            wizard._apply.reset_mock()
            wizard._save_assets()
            wizard._apply.assert_not_called()
            wizard._message.assert_called_once()

    def test_cli_wizard_uses_host_gui_process_without_modifying_config(self):
        from embercade.cli import main
        with TemporaryDirectory() as directory:
            config = Path(directory) / "embercade.toml"
            with (
                patch.dict(os.environ, {"HOME": directory, "DISPLAY": ":1"}, clear=True),
                patch("embercade.cli.subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run,
            ):
                self.assertEqual(main(["--config", str(config), "wizard"]), 0)
            self.assertEqual(run.call_args.args[0],
                             ["/usr/bin/python", "-B", "-m", "embercade.first_run_ui",
                              "--config", str(config)])
            self.assertFalse(config.exists())

    def test_unconfigured_desktop_start_opens_wizard_instead_of_frontend(self):
        from embercade.cli import main
        with TemporaryDirectory() as directory:
            config = Path(directory) / "embercade.toml"
            with (
                patch.dict(os.environ, {"HOME": directory, "DISPLAY": ":1"}, clear=True),
                patch("embercade.cli.subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run,
            ):
                self.assertEqual(main(["--config", str(config), "start"]), 0)
            self.assertIn("embercade.first_run_ui", run.call_args.args[0])
            self.assertFalse(config.exists())


if __name__ == "__main__":
    unittest.main()

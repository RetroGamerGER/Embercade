from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch, Mock
from contextlib import contextmanager
import hashlib
import ctypes
import json
import os
import subprocess
import unittest

from embercade import imports
from embercade.executables import ExecutableResolver, ExecutableResolutionError, EmulatorProvider, ProviderType
from embercade.first_run import FirstRunError, read_state, setup_arguments
from embercade.first_run_ui import Wizard
from embercade.host_requirements import inspect_appimage_provider, _system_has_content
from embercade.installer import install_user, uninstall_user
from embercade.launcher import create_launch_plan, prepare_launch_layout, LaunchError, LaunchPlan, run_launch
from embercade.paths import EmbercadePaths
from embercade.runtime import ProjectRuntime
from embercade.setup_flow import configure
from embercade.shadps4 import execute_dry_run
from embercade.provider_runner import build_host_provider_command, _owned_window_pid, _xenia_x11_windows, _x11_window_pid
from tests.test_imports import elf
from tests.test_installer import _write_payload, _environment


PROJECT = Path(__file__).resolve().parents[1]
IDENTITY = {"Name": "shadPS4", "Exec": "shadps4", "StartupWMClass": "shadps4;"}


def fixture(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(elf(appimage=True, symbols=False))
    return path


def structural_ps4(root: Path):
    """Only a generator fixture, never passed to an emulator process."""
    provider = fixture(root / "Supplied Emulator.AppImage")
    provider.chmod(0o700)
    settings = {"paths": {"roms": str(root / "ROM files"), "bios": str(root / "BIOS")},
                "emulators": {"shadps4": {"provider": "appimage", "executable": str(provider)}},
                "controller": {"exit_hotkey": "back-start"}}
    env = dict(os.environ)
    env.update({"HOME": str(root), "PATH": os.environ.get("PATH", ""),
                "XDG_CONFIG_HOME": str(root / "config"), "XDG_DATA_HOME": str(root / "data"),
                "XDG_CACHE_HOME": str(root / "cache"), "XDG_STATE_HOME": str(root / "state"),
                "EMBERCADE_RUNTIME_HOME": str(root / "runtime"),
                "LANG": "en_US.UTF-8", "EMBERCADE_DISPLAY_WIDTH": "1920", "EMBERCADE_DISPLAY_HEIGHT": "1080"})
    paths = EmbercadePaths.from_environment(env, config=settings)
    prepare_launch_layout(paths, PROJECT)
    rom = paths.rom_root / "ps4/Fixture with spaces.ps4"
    rom.mkdir(parents=True)
    (rom / "eboot.bin").write_bytes(b"generator fixture - never boot")
    before = (rom / "eboot.bin").stat()
    original = {"GPU": {"internal_screen_width": 3840, "internal_screen_height": 2160,
                        "vblank_frequency": 120, "fsr_enabled": True},
                "General": {"volume_slider": 75}, "Vulkan": {"gpu_id": 2}}
    config_file = paths.emulator_configs / "shadPS4/config.json"
    config_file.write_text(json.dumps(original))
    with patch("embercade.imports._provider_metadata", return_value=IDENTITY):
        plan = create_launch_plan(system="ps4", rom=rom, paths=paths,
                                  runtime=ProjectRuntime(PROJECT), config=settings,
                                  environment=env, dry_run=True)
    result = execute_dry_run(plan, paths)
    assert (rom / "eboot.bin").stat().st_mtime_ns == before.st_mtime_ns
    assert result["settings"]["GPU"]["internal_screen_width"] == 3840
    assert result["settings"]["GPU"]["vblank_frequency"] == 120
    assert result["settings"]["GPU"]["fsr_enabled"] is True
    assert result["settings"]["Vulkan"]["gpu_id"] == 2
    assert result["settings"]["GPU"]["full_screen"] is True
    assert result["settings"]["General"]["home_dir"] == str(paths.saves / "shadps4")
    return result


class Shadps4Tests(unittest.TestCase):
    def test_identity_is_embedded_metadata_not_filename(self):
        with TemporaryDirectory() as directory:
            path = fixture(Path(directory) / "anything.AppImage")
            with patch("embercade.imports._provider_metadata", return_value=IDENTITY):
                self.assertEqual(imports.inspect_provider(path, provider="shadps4"), path)
            with patch("embercade.imports._provider_metadata", return_value={"Name": "Other"}):
                with self.assertRaises(imports.ImportError):
                    imports.inspect_provider(path, provider="shadps4")

    def test_invalid_and_symlink_sources_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "shadps4.AppImage"
            path.write_bytes(b"not ELF")
            with self.assertRaises(imports.ImportError):
                imports.inspect_provider(path, provider="shadps4")
            link = path.with_name("link.AppImage")
            link.symlink_to(path)
            self.assertEqual(imports.import_providers(link, Path(directory) / "data", provider="shadps4").valid, 0)

    @patch("embercade.imports._provider_metadata", return_value=IDENTITY)
    def test_copy_never_move_source_permissions_hash_and_idempotence(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = fixture(root / "Original.AppImage")
            before = (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns)
            first = imports.import_providers(path, root / "data", provider="shadps4")
            managed, = first.imported_paths
            managed_before = managed.stat().st_mtime_ns
            again = imports.import_providers(path, root / "data", provider="shadps4")
            self.assertEqual((first.imported, again.present, again.imported), (1, 1, 0))
            self.assertEqual(managed.stat().st_mtime_ns, managed_before)
            self.assertTrue(managed.stat().st_mode & 0o100)
            self.assertEqual((path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns), before)
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), hashlib.sha256(managed.read_bytes()).digest())

    @patch("embercade.imports._provider_metadata", return_value=IDENTITY)
    def test_ambiguity_duplicates_and_conflict_never_overwrite(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            one = fixture(source / "one.AppImage")
            two = fixture(source / "two.AppImage")
            first = imports.import_providers(source, root / "data", provider="shadps4")
            self.assertEqual(first.imported, 1)
            two.write_bytes(two.read_bytes() + b"different build")
            self.assertEqual(len(imports.import_providers(source, root / "other", provider="shadps4").ambiguous), 2)
            before = first.imported_paths[0].read_bytes()
            self.assertTrue(imports.import_providers(two, root / "data", provider="shadps4").conflicts)
            self.assertEqual(first.imported_paths[0].read_bytes(), before)
            self.assertTrue(one.is_file())

    def test_resolver_never_uses_native_path_or_arbitrary_executable(self):
        with self.assertRaises(ExecutableResolutionError):
            ExecutableResolver(environment={"PATH": "/usr/bin"}).resolve("shadps4")
        with self.assertRaises(ExecutableResolutionError):
            ExecutableResolver(providers={"shadps4": EmulatorProvider(ProviderType.NATIVE)}).resolve("shadps4")

    @patch("embercade.imports._provider_metadata", return_value=IDENTITY)
    def test_wizard_cli_share_backend_and_existing_selection_survives(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = fixture(root / "Source with spaces.AppImage")
            args = setup_arguments(root / "config", roms=directory, bios=directory,
                                   exit_hotkey="back-start", shadps4_from=str(provider))
            self.assertEqual(args[args.index("--shadps4-from") + 1], str(provider))
            self.assertNotIn("--shadps4-from", setup_arguments(root / "config", roms=directory, bios=directory, exit_hotkey="back-start"))
            managed, = imports.import_providers(provider, root / ".local/share/embercade", provider="shadps4").imported_paths
            configure(root / "config", roms_value=directory, bios_value=directory, shadps4_value=str(managed), environment={"HOME": directory, "PATH": ""})
            original = (root / "config").read_bytes()
            self.assertEqual(read_state(root / "config", {"HOME": directory, "PATH": ""}).shadps4, str(managed))
            configure(root / "config", roms_value=directory, bios_value=directory, environment={"HOME": directory, "PATH": ""})
            self.assertEqual((root / "config").read_bytes(), original)

    def test_wizard_back_forward_preserves_unsubmitted_appimage(self):
        wizard = Wizard.__new__(Wizard)
        wizard.page = "shadps4"
        wizard.shadps4_entry = SimpleNamespace(get_text=lambda: "/chosen file.AppImage")
        wizard._go = lambda page: setattr(wizard, "page", page)
        wizard._back()
        self.assertEqual(wizard.page, "sources")
        self.assertEqual(wizard.shadps4, "/chosen file.AppImage")

    def test_wizard_bad_file_is_a_friendly_validation_error(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(FirstRunError):
                setup_arguments(Path(directory) / "config", roms=directory, bios=directory,
                                exit_hotkey="back-start", shadps4_from=directory + "/bad.AppImage")

    def test_invalid_existing_provider_table_is_a_friendly_error(self):
        with TemporaryDirectory() as directory:
            config = Path(directory) / "settings.toml"
            config.write_text('[emulators]\nshadps4="not a table"\n')
            with self.assertRaises(FirstRunError):
                read_state(config, {"HOME": directory, "PATH": ""})

    def test_doctor_recognizes_real_ps4_directory_not_empty_folder(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "ps4/Title.ps4"
            game.mkdir(parents=True)
            system = SimpleNamespace(system="ps4", path_name="ps4", extensions=(".ps4", ".zar"))
            self.assertFalse(_system_has_content(root, system))
            (game / "eboot.bin").write_bytes(b"fixture - never boot")
            self.assertTrue(_system_has_content(root, system))

    @patch("embercade.imports._provider_metadata", return_value=IDENTITY)
    def test_doctor_dependency_timeout_does_not_leak_traceback(self, _metadata):
        with TemporaryDirectory() as directory:
            provider = fixture(Path(directory) / "supplied.AppImage")
            provider.chmod(0o700)
            env = {"HOME": directory, "PATH": "/usr/bin"}
            resolver = ExecutableResolver(providers={"shadps4": EmulatorProvider(ProviderType.APPIMAGE, str(provider))}, environment=env)
            with patch("embercade.imports.provider_runtime_dependencies", side_effect=subprocess.TimeoutExpired("ldd", 10)):
                status = inspect_appimage_provider(resolver, env, needed=True, provider_name="shadps4")
            self.assertEqual(status.status, "UNVERIFIED")
            self.assertFalse(status.available)

    def test_host_runner_uses_shad_root_and_forwards_desktop_controller_environment(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = fixture(root / "AppImage with spaces.AppImage")
            provider.chmod(0o700)
            working = root / "isolated/emulators"
            home, tmp = root / "home", root / "tmp"
            for path in (working, home, tmp):
                path.mkdir(parents=True)
            env = {"EMBERCADE_EXTERNAL_PROVIDER_ID": "shadps4",
                   "EMBERCADE_EXTERNAL_PROVIDER_EXECUTABLE": str(provider),
                   "EMBERCADE_EXTERNAL_PROVIDER_HOME": str(home), "EMBERCADE_EXTERNAL_PROVIDER_TMPDIR": str(tmp),
                   "XDG_CONFIG_HOME": str(root / "config"), "XDG_DATA_HOME": str(root / "data"),
                   "XDG_CACHE_HOME": str(root / "cache"), "XDG_STATE_HOME": str(root / "state"),
                   "XDG_RUNTIME_DIR": "/userdata/system/xdg/runtime/embercade",
                   "EMBERCADE_HOST_PRIVATE_RUNTIME_ROOT": str(root / "runtime"),
                   "SDL_GAMECONTROLLERCONFIG": "live-guid,live-controller,a:b0,",
                   "SDL_VIDEODRIVER": "x11", "ENABLE_GAMESCOPE_WSI": "1", "SteamAppId": "123"}
            command = build_host_provider_command(("-g", "/roms/Blood borne.ps4/eboot.bin", "--fullscreen", "true"),
                         environment=env, working_directory=working, systemd_run=Path("/usr/bin/systemd-run"),
                         unit_name="embercade-shadps4")
            self.assertIn(f"--setenv=XDG_DATA_HOME={working}", command)
            self.assertIn("--unit=embercade-shadps4", command)
            self.assertIn("--setenv=ENABLE_GAMESCOPE_WSI=1", command)
            self.assertIn(f"--setenv=XDG_RUNTIME_DIR={root / 'runtime'}", command)
            self.assertIn("--setenv=SDL_GAMECONTROLLERCONFIG=live-guid,live-controller,a:b0,", command)
            self.assertEqual(command[-4:], ("-g", "/roms/Blood borne.ps4/eboot.bin", "--fullscreen", "true"))

    def test_helper_dialog_scope_rejects_foreign_or_disappeared_process(self):
        with patch("embercade.provider_runner.os.getpgid", side_effect=lambda pid: 100 if pid == 102 else 200):
            self.assertTrue(_owned_window_pid(102, 100))
            self.assertFalse(_owned_window_pid(202, 100))
            self.assertFalse(_owned_window_pid(0, 100))
        with patch("embercade.provider_runner.os.getpgid", side_effect=ProcessLookupError):
            self.assertFalse(_owned_window_pid(102, 100))

    def test_gamescope_finds_owned_dialog_without_relying_on_window_class(self):
        x11 = Mock()
        windows = (ctypes.c_ulong * 3)(11, 12, 13)
        x11.XOpenDisplay.return_value = 1
        x11.XDefaultRootWindow.return_value = 2
        def query(display, root, root_return, parent_return, children, count):
            ctypes.cast(children, ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)))[0] = ctypes.cast(windows, ctypes.POINTER(ctypes.c_ulong))
            ctypes.cast(count, ctypes.POINTER(ctypes.c_uint))[0] = 3
            return 1
        x11.XQueryTree.side_effect = query
        with patch("embercade.provider_runner.ctypes.CDLL", return_value=x11), \
             patch("embercade.provider_runner._x11_window_pid", side_effect=(101, 102, 999)), \
             patch("embercade.provider_runner.os.getpgid", side_effect=lambda pid: 100 if pid in (101, 102) else 998):
            self.assertEqual(_xenia_x11_windows(":1", process_group=100), (11, 12))
        x11.XGetClassHint.assert_not_called()
        x11.XCloseDisplay.assert_called_once_with(1)

    def test_x11_dialog_pid_property_is_typed_and_freed(self):
        x11 = Mock()
        x11.XInternAtom.return_value = 42
        pid = ctypes.c_ulong(102)
        def get(display, window, atom, offset, length, delete, kind, actual_type, actual_format, count, remaining, data):
            ctypes.cast(actual_type, ctypes.POINTER(ctypes.c_ulong))[0] = 6
            ctypes.cast(actual_format, ctypes.POINTER(ctypes.c_int))[0] = 32
            ctypes.cast(count, ctypes.POINTER(ctypes.c_ulong))[0] = 1
            ctypes.cast(data, ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)))[0] = ctypes.cast(ctypes.pointer(pid), ctypes.POINTER(ctypes.c_ubyte))
            return 0
        x11.XGetWindowProperty.side_effect = get
        self.assertEqual(_x11_window_pid(x11, 1, 11), 102)
        x11.XFree.assert_called_once()
        x11.XInternAtom.return_value = 0
        self.assertEqual(_x11_window_pid(x11, 1, 11), 0)

    def test_central_exit_stops_only_shad_service_and_returns_zero(self):
        controller = object()
        plan = LaunchPlan(("pinned-launcher",), {"PATH": "/usr/bin", "EMBERCADE_EXTERNAL_PROVIDER_UNIT": "embercade-shadps4",
                         "EMBERCADE_HOST_SESSION_RUNTIME_ROOT": "/run/user/1000", "XDG_RUNTIME_DIR": "/private/runtime"},
                         Path("/owned/shadps4.AppImage"), None, Path("/roms/game.ps4"), controller, system="ps4")
        @contextmanager
        def bridge(selected, *, emulator, on_exit):
            self.assertIs(selected, controller)
            self.assertEqual(emulator, "ps4")
            on_exit()
            yield
        process = Mock()
        process.poll.return_value = None
        process.wait.return_value = 0
        with patch("embercade.launcher.controller_exit_bridge", bridge), \
             patch("embercade.launcher.subprocess.Popen", return_value=process), \
             patch("embercade.launcher.shutil.which", return_value="/usr/bin/systemctl"), \
             patch("embercade.launcher.subprocess.run", return_value=subprocess.CompletedProcess((), 0)) as stop:
            self.assertEqual(run_launch(plan), 0)
        self.assertEqual(stop.call_args.args[0], ("/usr/bin/systemctl", "--user", "stop", "embercade-shadps4.service"))
        self.assertEqual(stop.call_args.kwargs["env"]["XDG_RUNTIME_DIR"], "/run/user/1000")
        process.send_signal.assert_not_called()

    def test_structural_fixture_paths_cannot_inherit_user_xdg_roots(self):
        if not ProjectRuntime(PROJECT).python.exists():
            self.skipTest("prepared pinned runtime required")
        with TemporaryDirectory(dir=PROJECT / ".work") as directory:
            result = structural_ps4(Path(directory))
            self.assertTrue(Path(result["config"]).is_relative_to(directory))
            self.assertTrue(Path(result["settings"]["General"]["home_dir"]).is_relative_to(directory))

    def test_normal_update_noop_uninstall_and_explicit_purge_preserve_external_source(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            env = _environment(root)
            payload = _write_payload(root)
            install = install_user(payload, environment=env)
            source = fixture(root / "External.AppImage")
            paths = (install.paths.data_root / "providers/shadps4/shadps4.AppImage",
                     install.paths.config_root / "emulators/shadPS4/config.json",
                     install.paths.data_root / "saves/shadps4/save.dat")
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"retained")
            config = install.paths.config_root / "embercade.toml"
            config.write_text('[emulators.shadps4]\nprovider="appimage"\nexecutable=' + json.dumps(str(paths[0])) + '\n')
            original = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (*paths, config)}
            install_user(_write_payload(root, "two"), environment=env)
            install_user(payload, environment=env)
            uninstall_user(environment=env)
            self.assertEqual({p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (*paths, config)}, original)
            install_user(payload, environment=env)
            uninstall_user(environment=env, purge=True, purge_confirmed=True)
            self.assertFalse(paths[0].exists())
            self.assertTrue(source.exists())

    def test_doctor_missing_and_invalid_do_not_claim_runtime(self):
        with TemporaryDirectory() as directory:
            env = {"HOME": directory, "PATH": ""}
            resolver = ExecutableResolver(environment=env)
            self.assertEqual(inspect_appimage_provider(resolver, env, needed=True, provider_name="shadps4").status, "MISSING")
            path = fixture(Path(directory) / "broken.AppImage")
            path.chmod(0o700)
            resolver = ExecutableResolver(providers={"shadps4": EmulatorProvider(ProviderType.APPIMAGE, str(path))}, environment=env)
            with patch("embercade.imports._provider_metadata", return_value={"Name": "Unknown"}):
                self.assertEqual(inspect_appimage_provider(resolver, env, needed=True, provider_name="shadps4").status, "INVALID")
            with patch("embercade.imports._provider_metadata", side_effect=imports.ImportError("cannot inspect AppImage identity: tool absent")):
                self.assertEqual(inspect_appimage_provider(resolver, env, needed=True, provider_name="shadps4").status, "UNVERIFIED")

    @patch("embercade.imports._provider_metadata", return_value=IDENTITY)
    def test_doctor_managed_external_dependencies_and_ambiguity(self, _metadata):
        with TemporaryDirectory() as directory:
            env = {"HOME": directory, "PATH": os.environ.get("PATH", "")}
            source = fixture(Path(directory) / "source.AppImage")
            managed, = imports.import_providers(source, Path(directory) / ".local/share/embercade", provider="shadps4").imported_paths
            resolver = ExecutableResolver(providers={"shadps4": EmulatorProvider(ProviderType.APPIMAGE, str(managed))}, environment=env)
            with patch("embercade.imports.provider_runtime_dependencies", return_value=()), patch("embercade.host_requirements.shutil.which", return_value="/tool"), patch("embercade.host_requirements.Path.is_file", return_value=True):
                self.assertEqual(inspect_appimage_provider(resolver, env, needed=True, provider_name="shadps4").status, "MANAGED")
                source.chmod(0o700)
                external = ExecutableResolver(providers={"shadps4": EmulatorProvider(ProviderType.APPIMAGE, str(source))}, environment=env)
                self.assertEqual(inspect_appimage_provider(external, env, needed=True, provider_name="shadps4").status, "FOUND")
            with patch("embercade.imports.provider_runtime_dependencies", return_value=("missing.so",)):
                self.assertEqual(inspect_appimage_provider(resolver, env, needed=True, provider_name="shadps4").status, "RUNTIME_DEPENDENCY_MISSING")
            extra = fixture(managed.with_name("extra.AppImage"))
            extra.write_bytes(extra.read_bytes() + b"different")
            extra.chmod(0o700)
            self.assertEqual(inspect_appimage_provider(ExecutableResolver(environment=env), env, needed=True, provider_name="shadps4").status, "AMBIGUOUS")

    def test_real_pinned_generator_isolation_command_and_setting_preservation(self):
        if not ProjectRuntime(PROJECT).python.exists():
            self.skipTest("prepared pinned runtime required")
        with TemporaryDirectory(dir=PROJECT / ".work") as directory:
            result = structural_ps4(Path(directory))
            self.assertIn("-g", result["command"])
            self.assertNotIn("-b", result["command"])
            self.assertNotIn("/userdata", json.dumps(result))

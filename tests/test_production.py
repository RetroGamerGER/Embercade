from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import csv
import json
import os
import socket
import shutil
import shlex
import subprocess
import unittest

from embercade.paths import EmbercadePaths
from embercade.elf_runtime import ElfRuntimeClosure, FrontendRuntimeReport
from embercade.production import (
    ProductionError,
    ProductionLayout,
    _frontend_splash_arguments,
    _prepare_compatibility_root,
    _optional_host_sources,
    _runtime_mounts,
    production_command,
)
from embercade.runtime import ProjectRuntime
from embercade.staging import (
    StagingError,
    _prune_runtime_bin,
    _prune_runtime_bytecode,
    _prune_runtime_source_records,
    _prune_runtime_test_packages,
    _validate_frontend_runtime,
    render_desktop_entry,
)
from embercade.version import FRONTEND_PRODUCT_LABEL


class ProductionTests(unittest.TestCase):
    def test_optional_host_xemu_mount_does_not_require_eeprom(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / ".local/share/xemu/xemu"
            source.mkdir(parents=True)
            for name in ("Complex_4627.bin", "mcpx_1.0.bin", "xbox_hdd.qcow2"):
                (source/name).write_bytes(b"read-only host source")
            env = {"HOME": directory}
            paths = EmbercadePaths.from_environment(env)
            mounts, variables = _optional_host_sources(paths, {}, env)
            self.assertIn(("--ro-bind", str(source), "/host-xemu-data"),
                          tuple(zip(mounts, mounts[1:], mounts[2:])))
            self.assertNotIn("EMBERCADE_XEMU_EEPROM_SOURCE", variables)
            self.assertIn("EMBERCADE_XEMU_HDD_SOURCE", variables)
            (source/"eeprom.bin").write_bytes(b"optional existing seed")
            _, variables = _optional_host_sources(paths, {}, env)
            self.assertIn("EMBERCADE_XEMU_EEPROM_SOURCE", variables)

    def test_theme_root_and_download_workspace_are_prepared_without_reset(self) -> None:
        with TemporaryDirectory() as directory:
            paths = EmbercadePaths.from_environment({"HOME": directory})
            root, _ = _prepare_compatibility_root(paths)
            self.assertTrue(paths.themes.is_dir())
            self.assertTrue(paths.theme_downloads.is_dir())
            self.assertEqual(
                os.readlink(root / "themes"),
                "/userdata/system/xdg/data/embercade/themes",
            )
            installed = paths.themes / "downloaded/theme.xml"
            installed.parent.mkdir()
            installed.write_bytes(b"user theme")
            partial = paths.theme_downloads / "partial.zip.tmp"
            partial.write_bytes(b"unfinished download")
            _prepare_compatibility_root(paths)
            self.assertEqual(installed.read_bytes(), b"user theme")
            self.assertEqual(partial.read_bytes(), b"unfinished download")

    @unittest.skipUnless(shutil.which("bwrap"), "Bubblewrap is required for namespace test")
    def test_frontend_theme_namespace_is_writable_but_branding_is_read_only(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(base / "home")})
            root, _ = _prepare_compatibility_root(paths)
            branding = base / "branding"
            branding.mkdir()
            splash = branding / "splash.jpg"
            splash.write_bytes(b"Embercade branding")
            code = """
from pathlib import Path
themes = Path('/userdata/themes')
(themes / '.tmp/test.zip.tmp').write_bytes(b'download')
installed = themes / 'downloaded'
installed.mkdir()
(installed / 'theme.xml').write_bytes(b'theme')
try:
    Path('/embercade-branding/splash.jpg').write_bytes(b'replaced')
except OSError:
    pass
else:
    raise AssertionError('theme namespace can overwrite product branding')
"""
            completed = subprocess.run(
                ["bwrap", "--ro-bind", "/usr", "/usr",
                 "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
                 "--bind", str(root), "/userdata",
                 "--bind", str(paths.data), "/userdata/system/xdg/data/embercade",
                 "--ro-bind", str(branding), "/embercade-branding",
                 "--", shutil.which("python"), "-B", "-c", code],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual((paths.theme_downloads / "test.zip.tmp").read_bytes(), b"download")
            self.assertEqual((paths.themes / "downloaded/theme.xml").read_bytes(), b"theme")
            self.assertEqual(splash.read_bytes(), b"Embercade branding")

    def test_theme_selection_cannot_change_product_splash_resource(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            layout = self._layout(root)
            paths = EmbercadePaths.from_environment({"HOME": str(root / "home")})
            layout.splash_image.parent.mkdir(parents=True, exist_ok=True)
            layout.splash_image.write_bytes(b"product image")
            original = _frontend_splash_arguments(layout)
            for selected in ("es-theme-carbon", "downloaded", "es-theme-carbon"):
                theme = paths.themes / selected
                theme.mkdir(parents=True, exist_ok=True)
                (theme / "splash.xml").write_text('<theme><image>replacement.png</image></theme>')
                self.assertEqual(_frontend_splash_arguments(layout), original)
                self.assertEqual(layout.splash_image.read_bytes(), b"product image")

    def test_hyprland_overlay_mounts_only_two_existing_ipc_sockets(self):
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            ipc = runtime / 'hypr/session'
            ipc.mkdir(parents=True)
            (runtime / 'pulse').mkdir()
            from contextlib import ExitStack
            with ExitStack() as stack:
                for path in (runtime / 'pulse/native', runtime / 'wayland-0',
                             ipc / '.socket.sock', ipc / '.socket2.sock'):
                    channel = stack.enter_context(socket.socket(socket.AF_UNIX))
                    channel.bind(str(path))
                mounts, *_ = _runtime_mounts({
                    'XDG_RUNTIME_DIR': str(runtime), 'WAYLAND_DISPLAY': 'wayland-0',
                    'HYPRLAND_INSTANCE_SIGNATURE': 'session',
                })
            self.assertNotIn(str(ipc), mounts)
            for name in ('.socket.sock', '.socket2.sock'):
                index = mounts.index(str(ipc / name))
                self.assertEqual(mounts[index - 1], '--ro-bind')

    def test_user_manager_mount_is_only_the_existing_private_socket(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "pulse").mkdir()
            (runtime / "systemd").mkdir()
            manager_socket = runtime / "systemd/private"
            with socket.socket(socket.AF_UNIX) as pulse:
                pulse.bind(str(runtime / "pulse/native"))
                environment = {"XDG_RUNTIME_DIR": str(runtime), "DISPLAY": ":1"}
                missing, *_ = _runtime_mounts(environment)
                self.assertNotIn(str(manager_socket), missing)
                self.assertNotIn(str(manager_socket.parent), missing)
                with socket.socket(socket.AF_UNIX) as manager:
                    manager.bind(str(manager_socket))
                    mounts, *_ = _runtime_mounts(environment)
            triples = tuple(zip(mounts, mounts[1:], mounts[2:]))
            self.assertIn(("--ro-bind", str(manager_socket), str(manager_socket)), triples)
            self.assertIn(("--dir", str(manager_socket.parent)), tuple(zip(mounts, mounts[1:])))
            self.assertNotIn(("--ro-bind", str(runtime), str(runtime)), triples)
            self.assertNotIn(("--bind", str(runtime), str(runtime)), triples)
            self.assertNotIn(("--ro-bind", str(manager_socket.parent), str(manager_socket.parent)), triples)

    def _layout(self, root: Path) -> ProductionLayout:
        prefix = root / "Prefix with spaces"
        application = prefix / "share/embercade"
        for path in (
            application / "runtime/venv/bin/python",
            application / "runtime/venv/bin/batocera-launch",
            application / "frontend/emulationstation",
            prefix / "bin/embercade-provider-runner",
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test", encoding="utf-8")
            path.chmod(0o755)
        for path in (
            application / "resources/emulationstation/es_systems.cfg",
            application / "resources/emulationstation/es_features.cfg",
            application / "resources/emulationstation/es_input.cfg",
            application / "resources/defaults/batocera.conf",
            application / "resources/defaults/es_settings.cfg",
            application / "resources/branding/icon/embercade-512.png",
            application / "resources/policy/desktop-capabilities.conf",
            application / "stage-manifest.json",
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        (application / "resources/policy/desktop-capabilities.conf").write_text(
            (Path(__file__).resolve().parents[1] / "resources/policy/desktop-capabilities.conf").read_text(),
            encoding="utf-8",
        )
        (application / "resources/emulationstation/es_systems.cfg").write_text("<systemList />")
        for path in (
            application / "resources/emulationstation/resources",
            application / "resources/emulationstation/themes/es-theme-carbon",
            application / "resources/batocera/shaders",
            application / "resources/batocera/datainit/decorations",
        ):
            path.mkdir(parents=True, exist_ok=True)
        return ProductionLayout(prefix)

    def test_installed_runtime_has_no_work_path_dependency(self) -> None:
        application = Path("/opt/embercade/share/embercade")
        runtime = ProjectRuntime(application, application / "runtime")
        self.assertEqual(runtime.root, Path("/opt/embercade/share/embercade/runtime"))
        self.assertNotIn(".work", str(runtime.root))

    def test_splash_path_uses_frontend_native_lifecycle_and_falls_back(self) -> None:
        with TemporaryDirectory() as directory:
            layout = self._layout(Path(directory))
            self.assertEqual(_frontend_splash_arguments(layout), ("--no-splash",))
            layout.splash_image.parent.mkdir(parents=True, exist_ok=True)
            layout.splash_image.write_bytes(b"test image")
            self.assertEqual(
                _frontend_splash_arguments(layout),
                (
                    "--splash-image",
                    "/app/share/embercade/resources/branding/splash/embercade-splash-3840x2160.jpg",
                ),
            )

    def test_missing_collection_config_is_a_first_run_error(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            layout = self._layout(root)
            paths = EmbercadePaths.from_environment({"HOME": str(root / "home")})
            with patch.object(ProductionLayout, "validate", return_value=()):
                with self.assertRaisesRegex(ProductionError, "FIRST RUN / CONFIG MISSING"):
                    production_command(layout, paths, {}, environment={})

    def test_appimage_runtime_refuses_writable_state_inside_read_only_appdir(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            layout = self._layout(root / "installed")
            appdir = root / "AppDir"
            paths = EmbercadePaths.from_environment({
                "HOME": str(root / "home"),
                "XDG_CONFIG_HOME": str(appdir / "config"),
            })
            with self.assertRaisesRegex(ProductionError, "outside the read-only application"):
                production_command(layout, paths, {}, environment={"APPDIR": str(appdir)})
            self.assertFalse(paths.config.exists())

    def test_command_uses_stable_app_paths_and_isolated_xdg(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            layout = self._layout(root)
            roms = root / "ROM collection"
            bios = root / "BIOS collection"
            roms.mkdir()
            bios.mkdir()
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root / "home"),
                    "XDG_CONFIG_HOME": str(root / "xdg/config"),
                    "XDG_DATA_HOME": str(root / "xdg/data"),
                    "XDG_CACHE_HOME": str(root / "xdg/cache"),
                    "XDG_STATE_HOME": str(root / "xdg/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "xdg/runtime/embercade"),
                },
                config={"paths": {"roms": str(roms), "bios": str(bios)}},
            )
            with (
                patch.object(ProductionLayout, "validate", return_value=()),
                patch("embercade.production.shutil.which", return_value="/usr/bin/bwrap"),
                patch(
                    "embercade.production._runtime_mounts",
                    return_value=(
                        [],
                        "/run/user/1",
                        "unix:/pulse",
                        "/run/user/1/embercade-xauthority",
                        "/run/user/1/gamescope-0",
                    ),
                ),
                patch("embercade.production._optional_host_sources", return_value=([], [])),
                patch("embercade.production.enumerate_sdl_game_controllers", return_value=[]),
                patch("embercade.wii.wii_device_mounts", return_value=(
                    "--dev-bind", "/dev/hidraw42", "/dev/hidraw42")),
                patch("embercade.production.Path.is_dir", return_value=True),
            ):
                command = production_command(
                    layout,
                    paths,
                    {"paths": {"roms": str(roms), "bios": str(bios)}},
                    environment={
                        "PATH": "/usr/bin",
                        "HOME": str(root / "home"),
                        "XAUTHORITY": str(root / "home/.Xauthority"),
                        "GAMESCOPE_WAYLAND_DISPLAY": "gamescope-0",
                        "LD_LIBRARY_PATH": "/host/library/leak",
                    },
                    frontend_arguments=("--windowed",),
                )

            joined = "\n".join(command)
            self.assertIn("/app/share/embercade/frontend/emulationstation", command)
            self.assertIn("/app/share/embercade/runtime", command)
            self.assertIn("/userdata/system/xdg/config", command)
            self.assertIn("--windowed", command)
            width_index = command.index("EMBERCADE_DISPLAY_WIDTH")
            height_index = command.index("EMBERCADE_DISPLAY_HEIGHT")
            self.assertEqual(command[width_index + 1], "1920")
            self.assertEqual(command[height_index + 1], "1080")
            self.assertNotIn(".work", joined)
            self.assertIn(str(layout.prefix), command)
            self.assertIn("EMBERCADE_HOST_CONFIG_ROOT", command)
            self.assertIn(str(paths.config), command)
            self.assertIn("EMBERCADE_HOST_ROMS_ROOT", command)
            host_runtime_index = command.index("EMBERCADE_HOST_SESSION_RUNTIME_ROOT")
            self.assertEqual(command[host_runtime_index + 1], "/run/user/1")
            self.assertIn(str(roms), command)
            self.assertEqual(command[0], "bwrap")
            self.assertIn(("--dev-bind", "/dev/hidraw42", "/dev/hidraw42"),
                          tuple(zip(command, command[1:], command[2:])))
            self.assertNotIn(("--dev-bind", "/dev", "/dev"),
                             tuple(zip(command, command[1:], command[2:])))
            self.assertIn(("--setenv", "SDL_JOYSTICK_HIDAPI_WII", "0"),
                          tuple(zip(command, command[1:], command[2:])))
            data_mount = command.index(str(paths.data))
            self.assertEqual(command[data_mount - 1], "--bind")
            self.assertEqual(command[data_mount + 1], "/userdata/system/xdg/data/embercade")
            self.assertTrue(paths.theme_downloads.is_dir())
            self.assertEqual(
                os.readlink(paths.runtime / "frontend-root/themes"),
                "/userdata/system/xdg/data/embercade/themes",
            )
            prefix_mount = command.index("/app")
            self.assertEqual(command[prefix_mount - 2], "--ro-bind")
            overlay_index = command.index("--overlay-src")
            resource_index = command.index("/usr/share/emulationstation")
            self.assertEqual(command[overlay_index + 1], "/usr/share")
            self.assertEqual(command[overlay_index + 2], "--tmp-overlay")
            self.assertEqual(command[overlay_index + 3], "/usr/share")
            self.assertLess(overlay_index, resource_index)
            library_index = command.index("LD_LIBRARY_PATH")
            self.assertEqual(command[library_index + 1], "/app/share/embercade/lib")
            self.assertNotIn("/host/library/leak", joined)
            self.assertIn("--no-splash", command)
            steam_gamepad_index = command.index(
                "SDL_GAMECONTROLLER_ALLOW_STEAM_VIRTUAL_GAMEPAD"
            )
            self.assertEqual(command[steam_gamepad_index + 1], "0")
            for variable in (
                "SDL_GAMECONTROLLER_IGNORE_DEVICES",
                "SDL_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT",
            ):
                variable_index = command.index(variable)
                self.assertEqual(command[variable_index - 1], "--unsetenv")
            authority_index = command.index("XAUTHORITY")
            self.assertEqual(
                command[authority_index + 1],
                "/run/user/1/embercade-xauthority",
            )
            host_authority_index = command.index("EMBERCADE_HOST_XAUTHORITY")
            self.assertEqual(
                command[host_authority_index + 1],
                str((root / "home" / ".Xauthority").absolute()),
            )
            gamescope_index = command.index("GAMESCOPE_WAYLAND_DISPLAY")
            self.assertEqual(command[gamescope_index + 1], "/run/user/1/gamescope-0")

    def test_runtime_mounts_xauthority_read_only_for_xwayland(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            pulse = runtime / "pulse/native"
            pulse.parent.mkdir()
            wayland = runtime / "wayland-0"
            xauthority = runtime / "xauth_cookie"
            xauthority.write_bytes(b"cookie")
            with socket.socket(socket.AF_UNIX) as pulse_socket, socket.socket(
                socket.AF_UNIX
            ) as wayland_socket:
                pulse_socket.bind(str(pulse))
                wayland_socket.bind(str(wayland))
                mounts, _, _, sandbox_xauthority, _ = _runtime_mounts(
                    {
                        "XDG_RUNTIME_DIR": str(runtime),
                        "WAYLAND_DISPLAY": "wayland-0",
                        "DISPLAY": ":0",
                        "XAUTHORITY": str(xauthority),
                    }
                )

            self.assertEqual(
                sandbox_xauthority,
                str(runtime / "embercade-xauthority"),
            )
            authority_index = mounts.index(str(xauthority))
            self.assertEqual(mounts[authority_index - 1], "--ro-bind")
            self.assertEqual(mounts[authority_index + 1], sandbox_xauthority)

    def test_runtime_mounts_gamescope_wsi_socket(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            pulse = runtime / "pulse/native"
            pulse.parent.mkdir()
            gamescope = runtime / "gamescope-0"
            with socket.socket(socket.AF_UNIX) as pulse_socket, socket.socket(
                socket.AF_UNIX
            ) as gamescope_socket:
                pulse_socket.bind(str(pulse))
                gamescope_socket.bind(str(gamescope))
                mounts, _, _, _, gamescope_display = _runtime_mounts(
                    {
                        "XDG_RUNTIME_DIR": str(runtime),
                        "DISPLAY": ":1",
                        "GAMESCOPE_WAYLAND_DISPLAY": "gamescope-0",
                    }
                )

            gamescope_index = mounts.index(str(gamescope))
            self.assertEqual(mounts[gamescope_index - 1], "--ro-bind")
            self.assertEqual(mounts[gamescope_index + 1], str(gamescope))
            self.assertEqual(gamescope_display, str(gamescope))

    def test_layout_validation_rejects_unresolved_frontend_library(self) -> None:
        with TemporaryDirectory() as directory:
            layout = self._layout(Path(directory))
            runtime_report = FrontendRuntimeReport(
                ElfRuntimeClosure((), ("libfreeimage.so.3",)),
                ("libfreeimage.so.3",),
                ("frontend shared libraries missing: libfreeimage.so.3",),
            )
            with (
                patch.object(ProductionLayout, "frontend_runtime", return_value=runtime_report),
                patch("embercade.production.probe_runtime") as runtime_probe,
            ):
                runtime_probe.return_value.healthy = True
                failures = layout.validate()

            self.assertIn(
                "frontend shared libraries missing: libfreeimage.so.3",
                failures,
            )

    def test_desktop_entry_has_normal_linux_application_fields(self) -> None:
        desktop = render_desktop_entry((
            Path(__file__).resolve().parents[1] / "packaging/linux/embercade.desktop"
        ).read_text(encoding="utf-8"))
        self.assertIn(f"Name={FRONTEND_PRODUCT_LABEL}", desktop)
        self.assertIn("Exec=embercade", desktop)
        self.assertIn("Type=Application", desktop)
        self.assertIn("Categories=Game;Emulator;", desktop)
        self.assertIn("Icon=embercade", desktop)

    def test_staged_launcher_resolves_an_installed_symlink_target(self) -> None:
        staging = (
            Path(__file__).resolve().parents[1] / "src/embercade/staging.py"
        ).read_text(encoding="utf-8")
        self.assertIn('self=$(readlink -f -- \\"$0\\")', staging)

    def test_stage_prunes_non_relocatable_virtualenv_entrypoints(self) -> None:
        with TemporaryDirectory() as directory:
            binary_directory = Path(directory)
            leaked = binary_directory / "pip"
            leaked.write_text("#!/old/build/path/python\n", encoding="utf-8")
            interpreter = binary_directory / "python"
            interpreter.symlink_to("/usr/bin/python")

            _prune_runtime_bin(binary_directory)

            self.assertFalse(leaked.exists())
            self.assertTrue(interpreter.is_symlink())

    def test_stage_prunes_dependency_tests_but_keeps_runtime_package(self) -> None:
        with TemporaryDirectory() as directory:
            venv = Path(directory)
            package = venv / "lib/python3.14/site-packages/qrcode"
            tests = package / "tests"
            tests.mkdir(parents=True)
            (package / "main.py").write_text("runtime", encoding="utf-8")
            (tests / "test_main.py").write_text("test", encoding="utf-8")

            _prune_runtime_test_packages(venv)

            self.assertTrue((package / "main.py").is_file())
            self.assertFalse(tests.exists())

    def test_stage_prunes_non_relocatable_python_bytecode(self) -> None:
        with TemporaryDirectory() as directory:
            venv = Path(directory)
            package = venv / "lib/python3.14/site-packages/example"
            cache = package / "__pycache__"
            cache.mkdir(parents=True)
            source = package / "module.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            (cache / "module.cpython-314.pyc").write_bytes(b"build path cache")
            (package / "legacy.pyc").write_bytes(b"legacy cache")

            _prune_runtime_bytecode(venv)

            self.assertTrue(source.is_file())
            self.assertFalse(cache.exists())
            self.assertFalse((package / "legacy.pyc").exists())

    def test_stage_removes_only_local_pip_source_records_and_preserves_package_identity(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "development/runtime/venv"
            site_packages = source / "lib/python3.14/site-packages"
            local = site_packages / "pinned_package-44.0.dist-info"
            public = site_packages / "public_package-1.0.dist-info"
            for path in (local, public):
                path.mkdir(parents=True)
                (path / "METADATA").write_text("Name: pinned-package\nVersion: 44.0\n")
                (path / "LICENSE").write_text("Original license text fixture\n")
                (path / "direct_url.json").write_text(json.dumps({
                    "url": (root / "private build source").as_uri() if path == local
                    else "https://example.invalid/package.whl",
                    "dir_info": {},
                }))
                with (path / "RECORD").open("w", newline="") as stream:
                    csv.writer(stream).writerows([
                        [f"{path.name}/METADATA", "sha256=metadata-fixture", "40"],
                        [f"{path.name}/direct_url.json", "sha256=source-fixture", "90"],
                        [f"{path.name}/LICENSE", "sha256=license-fixture", "30"],
                        [f"{path.name}/RECORD", "", ""],
                    ])
            before = {path.relative_to(source): (path.read_bytes(), path.stat().st_mtime_ns)
                      for path in source.rglob("*") if path.is_file()}
            staged = root / "production/runtime/venv"
            shutil.copytree(source, staged)

            _prune_runtime_source_records(staged)

            copied_local = staged / local.relative_to(source)
            copied_public = staged / public.relative_to(source)
            self.assertFalse((copied_local / "direct_url.json").exists())
            with (copied_local / "RECORD").open(newline="") as stream:
                self.assertEqual([row[0] for row in csv.reader(stream)], [
                    f"{local.name}/METADATA", f"{local.name}/LICENSE", f"{local.name}/RECORD",
                ])
            for name in ("METADATA", "LICENSE"):
                self.assertEqual((copied_local / name).read_bytes(), (local / name).read_bytes())
            for name in ("METADATA", "LICENSE", "direct_url.json", "RECORD"):
                self.assertEqual((copied_public / name).read_bytes(), (public / name).read_bytes())
            self.assertEqual(before, {path.relative_to(source): (path.read_bytes(), path.stat().st_mtime_ns)
                                      for path in source.rglob("*") if path.is_file()})

    def test_stage_rejects_malformed_build_source_metadata_without_exposing_it(self) -> None:
        with TemporaryDirectory() as directory:
            venv = Path(directory)
            direct_url = venv / "lib/python3.14/site-packages/package-1.0.dist-info/direct_url.json"
            direct_url.parent.mkdir(parents=True)
            direct_url.write_text("invalid private build source fixture")
            with self.assertRaisesRegex(StagingError, "PEP 610.*values omitted") as caught:
                _prune_runtime_source_records(venv)
            self.assertNotIn("invalid private build source fixture", str(caught.exception))
            self.assertTrue(direct_url.exists())

    def test_stage_rejects_an_incomplete_frontend_runtime_closure(self) -> None:
        runtime_report = FrontendRuntimeReport(
            ElfRuntimeClosure((), ("libfreeimage.so.3",)),
            ("libfreeimage.so.3",),
            ("frontend shared libraries missing: libfreeimage.so.3",),
        )
        with patch(
            "embercade.staging.inspect_frontend_runtime",
            return_value=runtime_report,
        ):
            with self.assertRaisesRegex(StagingError, "libfreeimage.so.3"):
                _validate_frontend_runtime(Path("frontend"), Path("lib"))

    def test_frontend_build_suppresses_development_runpath(self) -> None:
        ui_build = (
            Path(__file__).resolve().parents[1] / "scripts/ui-build"
        ).read_text(encoding="utf-8")
        self.assertIn("-DCMAKE_SKIP_BUILD_RPATH=ON", ui_build)
        self.assertIn("-march=x86-64 -mtune=generic", ui_build)
        self.assertIn('-DCMAKE_C_FLAGS="$frontend_compile_flags"', ui_build)
        self.assertIn('-DCMAKE_CXX_FLAGS="$frontend_compile_flags"', ui_build)
        self.assertIn("objcopy --remove-section .note.gnu.property --strip-debug", ui_build)
        self.assertIn("rg --text --quiet '/home/[^/[:space:]]+/'", ui_build)

    def test_frontend_flags_strip_native_debug_and_file_paths_with_spaces(self) -> None:
        compiler, objcopy, readelf = (shutil.which(name) for name in ("c++", "objcopy", "readelf"))
        if not all((compiler, objcopy, readelf)):
            self.skipTest("Native compiler and ELF tools needed for build-path contract")
        build = (Path(__file__).resolve().parents[1] / "scripts/ui-build").read_text()
        assignment = next(line for line in build.splitlines() if line.startswith("frontend_compile_flags="))
        with TemporaryDirectory() as directory:
            source_root = Path(directory) / "Source with spaces"
            source_root.mkdir()
            source = source_root / "frontend.cpp"
            source.write_text('const char* source_path = __FILE__;\n'
                              'int main() { return source_path[0] == 0; }\n')
            flags = subprocess.run(
                ["bash", "-c", 'reference_root="$1"\n' + assignment +
                 '\nprintf "%s" "$frontend_compile_flags"', "--", str(source_root)],
                text=True, capture_output=True, check=True,
            ).stdout
            binary = Path(directory) / "frontend"
            subprocess.run([compiler, *shlex.split(flags), "-g", str(source), "-o", str(binary)],
                           capture_output=True, check=True)
            subprocess.run([objcopy, "--remove-section", ".note.gnu.property", "--strip-debug", str(binary)],
                           capture_output=True, check=True)
            data = binary.read_bytes()
            self.assertNotIn(str(source_root).encode(), data)
            self.assertIn(b"/embercade-source/frontend.cpp", data)
            sections = subprocess.run([readelf, "--sections", str(binary)],
                                      text=True, capture_output=True, check=True).stdout
            self.assertNotIn(".debug_info", sections)

    def test_staged_python_entrypoints_disable_bytecode(self) -> None:
        staging = (
            Path(__file__).resolve().parents[1] / "src/embercade/staging.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"$runtime_bin/python\\" -B -m batocera_launch', staging)
        self.assertIn('runtime/venv/bin/python\\" -B -m embercade', staging)

    def test_stage_preserves_primary_upstream_license_notices(self) -> None:
        project = Path(__file__).resolve().parents[1]
        staging = (project / "src/embercade/staging.py").read_text(encoding="utf-8")
        runtime_prepare = (project / "scripts/runtime-prepare").read_text(
            encoding="utf-8"
        )
        self.assertIn("COPYING", runtime_prepare)
        self.assertIn('application / "licenses" / "batocera" / "COPYING"', staging)
        self.assertIn(
            'application / "licenses" / "emulationstation" / "LICENSE.md"', staging
        )
        self.assertIn('application / "licenses" / "carbon-theme" / "readme.txt"', staging)
        self.assertIn('application / "licenses" / "shaders"', staging)

    def test_stage_uses_host_shader_mappings_and_only_official_retrobat_decorations(self) -> None:
        project = Path(__file__).resolve().parents[1]
        staging = (project / "src/embercade/staging.py").read_text(encoding="utf-8")
        stage_build = (project / "scripts/stage-build").read_text(encoding="utf-8")
        ui_prepare = (project / "scripts/ui-prepare").read_text(encoding="utf-8")

        self.assertIn('project_root / ".work" / "shader-mappings"', staging)
        self.assertIn('"shader_provider": "host:libretro-shaders-slang', staging)
        self.assertIn('_copy_tree(decoration_root,', staging)
        self.assertNotIn('bundle_inputs["decorations"]', staging)
        self.assertIn('"slang_shaders": shader_pin', staging)
        self.assertNotIn('bundle_inputs["shaders"]', staging)
        self.assertIn('scripts/shaders-smoke', stage_build)
        self.assertIn('scripts/shaders-prepare', stage_build)
        self.assertIn('ln -sfn -- "$shader_root"', ui_prepare)
        self.assertNotIn(
            'reference_bundle/usr-share-batocera/shaders',
            ui_prepare,
        )

    def test_isolated_test_xdg_can_read_normal_retroarch_profile(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            retroarch = home / ".config/retroarch"
            retroarch.mkdir(parents=True)
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(root / "isolated/config"),
                    "XDG_DATA_HOME": str(root / "isolated/data"),
                    "XDG_CACHE_HOME": str(root / "isolated/cache"),
                    "XDG_STATE_HOME": str(root / "isolated/state"),
                    "EMBERCADE_RUNTIME_HOME": str(root / "isolated/runtime"),
                }
            )
            mounts, variables = _optional_host_sources(
                paths,
                {},
                {
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(root / "isolated/config"),
                    "XDG_DATA_HOME": str(root / "isolated/data"),
                },
            )
            self.assertIn(str(retroarch), mounts)
            self.assertIn("/host-retroarch-profile", mounts)
            self.assertIn("EMBERCADE_LIBRETRO_USER_CORES", variables)

    def test_production_defaults_keep_proven_psx_route(self) -> None:
        defaults = (
            Path(__file__).resolve().parents[1] / "resources/defaults/batocera.conf"
        ).read_text(encoding="utf-8")
        self.assertIn("psx.emulator=libretro", defaults)
        self.assertIn("psx.core=mednafen_psx", defaults)
        self.assertIn("psx.gfxbackend=vulkan", defaults)

    def test_explicit_provider_override_has_read_only_visibility(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "external" / "User Xenia.AppImage"
            provider.parent.mkdir()
            provider.write_bytes(b"unexecuted test fixture")
            paths = EmbercadePaths.from_environment({"HOME": str(root / "home")})
            mounts, _ = _optional_host_sources(
                paths,
                {"executables": {"xenia-edge": str(provider)},
                 "emulators": {"xenia-edge": {"executable": str(provider)}}},
                {"HOME": str(root / "home")},
            )
            index = mounts.index(str(provider))
            self.assertEqual(mounts[index - 1:index + 2], ["--ro-bind", str(provider), str(provider)])
            self.assertEqual(mounts.count(str(provider)), 2)

    def test_tracked_product_code_has_no_developer_home_path_hardcode(self) -> None:
        project = Path(__file__).resolve().parents[1]
        for relative in (
            "src/embercade/production.py",
            "src/embercade/staging.py",
            "scripts/stage-build",
            "packaging/linux/embercade.desktop",
        ):
            self.assertNotRegex(
                (project / relative).read_text(encoding="utf-8"),
                r"/home/[^/\s]+",
            )


if __name__ == "__main__":
    unittest.main()

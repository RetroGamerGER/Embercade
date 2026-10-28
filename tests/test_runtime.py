from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import subprocess
import unittest

from embercade.runtime import (
    DevelopmentLayout,
    ProjectRuntime,
    emulator_provider_config,
    executable_config,
    load_config,
    locked_requirements,
    probe_runtime,
)
from embercade.executables import EmulatorProvider, ProviderType


class RuntimeTests(unittest.TestCase):
    def test_missing_config_is_empty(self) -> None:
        self.assertEqual(load_config(Path("/does/not/exist")), {})

    def test_executable_config(self) -> None:
        with TemporaryDirectory() as directory:
            config = Path(directory) / "embercade.toml"
            config.write_text('[executables]\nretroarch = "/opt/retroarch"\n', encoding="utf-8")
            loaded = load_config(config)
            self.assertEqual(executable_config(loaded), {"retroarch": "/opt/retroarch"})

    def test_emulator_provider_config_supports_explicit_appimage_and_native(self) -> None:
        config = {
            "emulators": {
                "xenia-edge": {
                    "provider": "appimage",
                    "executable": "/opt/Emulators/Xenia Edge.AppImage",
                },
                "retroarch": {"provider": "native"},
            }
        }
        self.assertEqual(
            emulator_provider_config(config),
            {
                "xenia-edge": EmulatorProvider(
                    ProviderType.APPIMAGE, "/opt/Emulators/Xenia Edge.AppImage"
                ),
                "retroarch": EmulatorProvider(ProviderType.NATIVE, None),
            },
        )

    def test_emulator_provider_config_infers_appimage_from_suffix(self) -> None:
        providers = emulator_provider_config(
            {"emulators": {"xenia-edge": {"executable": "/opt/Xenia.AppImage"}}}
        )
        self.assertEqual(providers["xenia-edge"].provider_type, ProviderType.APPIMAGE)

    def test_development_layout_stays_inside_project(self) -> None:
        layout = DevelopmentLayout(Path("/project"))
        self.assertEqual(layout.root, Path("/project/.work/dev"))
        self.assertEqual(layout.userdata, Path("/project/.work/dev/userdata"))

    def test_project_runtime_stays_inside_project(self) -> None:
        runtime = ProjectRuntime(Path("/project"))
        self.assertEqual(runtime.root, Path("/project/.work/runtime"))
        self.assertEqual(runtime.source_root, Path("/project/.work/runtime/src"))
        self.assertEqual(runtime.python, Path("/project/.work/runtime/venv/bin/python"))

    def test_installed_runtime_is_selected_without_a_work_path(self) -> None:
        with TemporaryDirectory() as directory:
            application = Path(directory) / "share/embercade"
            (application / "runtime").mkdir(parents=True)
            runtime = ProjectRuntime.for_application(application)
            self.assertEqual(runtime.root, application / "runtime")
            self.assertNotIn(".work", str(runtime.root))

    def test_missing_runtime_has_concise_status(self) -> None:
        with TemporaryDirectory() as directory:
            status = probe_runtime(ProjectRuntime(Path(directory)))
        self.assertFalse(status.available)
        self.assertFalse(status.healthy)
        self.assertEqual(status.cli_error, "runtime not prepared")

    def test_runtime_probe_disables_bytecode_even_in_isolated_mode(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = ProjectRuntime(root, root / "runtime")
            runtime.python.parent.mkdir(parents=True)
            runtime.python.write_text("python", encoding="utf-8")
            runtime.launcher.write_text("launcher", encoding="utf-8")
            completed = (
                subprocess.CompletedProcess(
                    [],
                    0,
                    '{"python": "3.14.7", "imports": {}}',
                    "",
                ),
                subprocess.CompletedProcess([], 0, "", ""),
            )
            with patch("embercade.runtime.subprocess.run", side_effect=completed) as run:
                probe_runtime(runtime)

            first_command = run.call_args_list[0].args[0]
            self.assertEqual(first_command[1:3], ["-B", "-I"])

    def test_runtime_lock_is_exact_and_contains_import_dependencies(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        requirements = locked_requirements(project_root / "runtime/requirements.lock")
        self.assertTrue(
            {
                "aiohttp",
                "hatchling",
                "pillow",
                "pyudev",
                "pyyaml",
                "qrcode",
                "ruamel.yaml",
                "typing-extensions",
                "uvloop",
            }.issubset(requirements)
        )

    def test_xenia_patch_redirects_binary_and_log_to_embercade_paths(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        patch_text = (
            project_root
            / "patches/batocera-launch/0019-embercade-xenia-edge-host-executable.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("EMBERCADE_XENIA_EDGE_BIN", patch_text)
        self.assertIn("EMBERCADE_XENIA_EDGE_LOG", patch_text)
        self.assertIn("config.setdefault('Logging'", patch_text)
        self.assertIn("f'--log_file={log_file}'", patch_text)

        path_patch_text = (
            project_root
            / "patches/batocera-launch/0020-embercade-xenia-edge-xdg-paths.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("EMBERCADE_XENIA_EDGE_STORAGE_ROOT", path_patch_text)
        self.assertIn("EMBERCADE_XENIA_EDGE_CONTENT_ROOT", path_patch_text)
        self.assertIn("EMBERCADE_XENIA_EDGE_CACHE_ROOT", path_patch_text)

    def test_launch_logs_have_a_bounded_rotating_handler(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        patch_text = (
            project_root
            / "patches/batocera-launch/0021-embercade-bounded-launch-logs.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("RotatingFileHandler", patch_text)
        self.assertIn("maxBytes=8 * 1024 * 1024", patch_text)
        self.assertIn("backupCount=2", patch_text)
        self.assertIn("r.name != 'emulator'", patch_text)

    def test_prepared_runtime_caps_emulator_logs_on_disk(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project_root)
        if not runtime.python.exists():
            self.skipTest("project-local runtime has not been prepared")
        with TemporaryDirectory() as directory:
            log_root = Path(directory)
            environment = dict(os.environ)
            environment.update(
                {
                    "EMBERCADE_DESKTOP": "1",
                    "EMBERCADE_LOGS": str(log_root),
                    "PYTHONNOUSERSITE": "1",
                }
            )
            environment.pop("PYTHONPATH", None)
            completed = subprocess.run(
                [
                    str(runtime.python),
                    "-B",
                    "-I",
                    "-c",
                    "import logging; from batocera_launch.logging import setup_logging; "
                    "c=setup_logging(); c.__enter__(); "
                    "[(logging.getLogger('emulator').error('x'*(1024*1024))) for _ in range(30)]; "
                    "c.__exit__(None,None,None)",
                ],
                check=False,
                capture_output=True,
                env=environment,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            logs = sorted(log_root.glob("batocera-launch-emulator.log*"))
            self.assertEqual(len(logs), 3)
            self.assertTrue(all(path.stat().st_size <= 8 * 1024 * 1024 for path in logs))

    def test_all_native_controller_generators_use_the_central_exit_preset(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        for name in (
            "0006-embercade-retroarch-controller-exit.patch",
            "0009-embercade-dolphin-controller-exit.patch",
            "0011-embercade-pcsx2-desktop-paths.patch",
        ):
            text = (project_root / "patches/batocera-launch" / name).read_text()
            self.assertIn("EMBERCADE_EXIT_HOTKEY", text, name)
            self.assertIn("guide-start", text, name)

    def test_prepared_runtime_imports_without_pythonpath(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project_root)
        if not runtime.python.exists():
            self.skipTest("project-local runtime has not been prepared")
        with patch.dict("os.environ", {"PYTHONPATH": "/definitely/not/embercade"}):
            status = probe_runtime(runtime)
        self.assertTrue(status.healthy, status)

    def test_prepared_runtime_records_pin_and_compatibility_mode(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project_root)
        if not runtime.info.exists():
            self.skipTest("project-local runtime has not been prepared")
        info = dict(
            line.split("=", 1)
            for line in runtime.info.read_text(encoding="utf-8").splitlines()
            if line
        )
        self.assertEqual(info["mode"], "embercade-dev-compatibility")
        self.assertEqual(info["upstream-python-requires"], "==3.14.5")
        self.assertEqual(
            info["batocera-commit"],
            "9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48",
        )
        self.assertTrue(
            (runtime.source_root / "python-src/batocera-launch/pyproject.toml").is_file()
        )
        self.assertTrue(
            (runtime.source_root / "python-src/batocera-launch-dolphin/pyproject.toml").is_file()
        )
        self.assertTrue(
            (runtime.source_root / "python-src/batocera-launch-pcsx2/pyproject.toml").is_file()
        )
        self.assertTrue(
            (runtime.source_root / "python-src/batocera-launch-rpcs3/pyproject.toml").is_file()
        )


if __name__ == "__main__":
    unittest.main()

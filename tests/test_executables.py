from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from embercade.executables import (
    EmulatorProvider,
    ExecutableResolutionError,
    ExecutableResolver,
    ProviderType,
)


class ExecutableResolverTests(unittest.TestCase):
    @staticmethod
    def _make_executable(directory: Path, name: str) -> Path:
        path = directory / name
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
        return path

    def test_path_resolution(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self._make_executable(root, "retroarch")
            resolver = ExecutableResolver(environment={"PATH": str(root)})
            result = resolver.resolve("retroarch")
            self.assertEqual(result.path, executable)
            self.assertEqual(result.source, "PATH")
            self.assertEqual(result.provider_type, ProviderType.NATIVE)

    def test_explicit_config_precedes_path(self) -> None:
        with TemporaryDirectory() as configured_dir, TemporaryDirectory() as path_dir:
            configured = self._make_executable(Path(configured_dir), "custom-retroarch")
            self._make_executable(Path(path_dir), "retroarch")
            resolver = ExecutableResolver(
                {"retroarch": str(configured)},
                environment={"PATH": path_dir},
            )
            result = resolver.resolve("retroarch")
            self.assertEqual(result.path, configured)
            self.assertEqual(result.source, "config")
            self.assertEqual(result.provider_type, ProviderType.EXPLICIT)

    def test_appimage_provider_supports_spaces_and_precedes_path(self) -> None:
        with TemporaryDirectory() as provider_dir, TemporaryDirectory() as path_dir:
            appimage = self._make_executable(
                Path(provider_dir), "Xenia Edge (Linux).AppImage"
            )
            self._make_executable(Path(path_dir), "xenia_edge")
            resolver = ExecutableResolver(
                providers={
                    "xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(appimage))
                },
                environment={"PATH": path_dir},
            )

            result = resolver.resolve("xenia-edge")

            self.assertEqual(result.path, appimage)
            self.assertEqual(result.source, "appimage")
            self.assertEqual(result.provider_type, ProviderType.APPIMAGE)

    def test_legacy_explicit_override_precedes_appimage_provider(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            explicit = self._make_executable(root, "explicit-xenia")
            appimage = self._make_executable(root, "Xenia.AppImage")
            resolver = ExecutableResolver(
                {"xenia-edge": str(explicit)},
                providers={
                    "xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(appimage))
                },
                environment={"PATH": ""},
            )

            result = resolver.resolve("xenia-edge")

            self.assertEqual(result.path, explicit)
            self.assertEqual(result.provider_type, ProviderType.EXPLICIT)

    def test_canary_remains_a_distinct_optional_provider(self) -> None:
        with TemporaryDirectory() as directory:
            appimage = self._make_executable(Path(directory), "Xenia Canary.AppImage")
            resolver = ExecutableResolver(
                providers={
                    "xenia-canary": EmulatorProvider(
                        ProviderType.APPIMAGE, str(appimage)
                    )
                },
                environment={"PATH": ""},
            )

            result = resolver.resolve("xenia-canary")

            self.assertEqual(result.name, "xenia-canary")
            self.assertEqual(result.path, appimage)
            self.assertEqual(result.provider_type, ProviderType.APPIMAGE)

    def test_appimage_provider_rejects_relative_and_non_executable_paths(self) -> None:
        resolver = ExecutableResolver(
            providers={
                "xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, "../Xenia.AppImage")
            },
            environment={"PATH": ""},
        )
        with self.assertRaisesRegex(ExecutableResolutionError, "absolute path"):
            resolver.resolve("xenia-edge")

        with TemporaryDirectory() as directory:
            appimage = Path(directory) / "Xenia.AppImage"
            appimage.write_bytes(b"not executable")
            resolver = ExecutableResolver(
                providers={
                    "xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(appimage))
                },
                environment={"PATH": ""},
            )
            with self.assertRaisesRegex(ExecutableResolutionError, "not executable"):
                resolver.resolve("xenia-edge")

    def test_provider_path_is_data_not_a_shell_command(self) -> None:
        with TemporaryDirectory() as directory:
            appimage = self._make_executable(
                Path(directory), "Xenia $(touch should-not-exist).AppImage"
            )
            resolver = ExecutableResolver(
                providers={
                    "xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(appimage))
                },
                environment={"PATH": ""},
            )
            self.assertEqual(resolver.resolve("xenia-edge").path, appimage)
            self.assertFalse((Path(directory) / "should-not-exist").exists())

    def test_configured_missing_executable_is_clear_error(self) -> None:
        resolver = ExecutableResolver(
            {"xemu": "/does/not/exist"},
            environment={"PATH": ""},
        )
        with self.assertRaisesRegex(ExecutableResolutionError, "Configured executable"):
            resolver.resolve("xemu")

    def test_missing_path_executable_is_clear_error(self) -> None:
        resolver = ExecutableResolver(environment={"PATH": ""})
        with self.assertRaisesRegex(ExecutableResolutionError, "make 'rpcs3' available on PATH"):
            resolver.resolve("rpcs3")


if __name__ == "__main__":
    unittest.main()

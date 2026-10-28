from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest

from embercade.elf_runtime import inspect_elf_runtime, inspect_frontend_runtime


class ElfRuntimeTests(unittest.TestCase):
    @staticmethod
    def _completed(command: list[str], stdout: str = "", returncode: int = 0):
        return subprocess.CompletedProcess(command, returncode, stdout, "")

    def test_existing_binary_with_missing_library_is_unhealthy(self) -> None:
        with TemporaryDirectory(prefix="Payload with spaces ") as directory:
            binary = Path(directory) / "emulationstation"
            binary.write_bytes(b"ELF")

            def runner(command, **_kwargs):
                return self._completed(
                    command,
                    "\tlibfreeimage.so.3 => not found\n"
                    "\tlibc.so.6 => /usr/lib/libc.so.6 (0x1)\n",
                )

            result = inspect_elf_runtime(binary, runner=runner)

            self.assertFalse(result.healthy)
            self.assertEqual(result.missing, ("libfreeimage.so.3",))
            self.assertEqual(result.resolved_path("libc.so.6"), Path("/usr/lib/libc.so.6"))

    def test_payload_library_path_replaces_build_host_environment(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "emulationstation"
            libraries = root / "lib"
            binary.write_bytes(b"ELF")
            libraries.mkdir()
            observed_environment: dict[str, str] = {}

            def runner(command, **kwargs):
                observed_environment.update(kwargs["env"])
                return self._completed(command)

            inspect_elf_runtime(
                binary,
                (libraries,),
                runner=runner,
                environment={"LD_LIBRARY_PATH": "/development/host/path"},
            )

            self.assertEqual(observed_environment["LD_LIBRARY_PATH"], str(libraries))
            self.assertNotIn("/development/host/path", observed_environment["LD_LIBRARY_PATH"])

    def test_frontend_accepts_declared_bundled_libraries_inside_payload(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "emulationstation"
            libraries = root / "lib"
            binary.write_bytes(b"ELF")
            libraries.mkdir()

            def runner(command, **_kwargs):
                if command[0] == "readelf":
                    return self._completed(
                        command,
                        " 0x1 (NEEDED) Shared library: [libfreeimage.so.3]\n"
                        " 0x1 (NEEDED) Shared library: [libSDL2_mixer-2.0.so.0]\n",
                    )
                return self._completed(
                    command,
                    f"libfreeimage.so.3 => {libraries / 'libfreeimage.so.3'} (0x1)\n"
                    f"libSDL2_mixer-2.0.so.0 => {libraries / 'libSDL2_mixer-2.0.so.0'} (0x2)\n",
                )

            result = inspect_frontend_runtime(binary, libraries, runner=runner)

            self.assertTrue(result.healthy, result.failures)

    def test_frontend_rejects_bundled_library_from_host(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "emulationstation"
            libraries = root / "lib"
            binary.write_bytes(b"ELF")
            libraries.mkdir()

            def runner(command, **_kwargs):
                if command[0] == "readelf":
                    return self._completed(
                        command,
                        " 0x1 (NEEDED) Shared library: [libfreeimage.so.3]\n"
                        " 0x1 (NEEDED) Shared library: [libSDL2_mixer-2.0.so.0]\n",
                    )
                return self._completed(
                    command,
                    "libfreeimage.so.3 => /usr/lib/libfreeimage.so.3 (0x1)\n"
                    f"libSDL2_mixer-2.0.so.0 => {libraries / 'libSDL2_mixer-2.0.so.0'} (0x2)\n",
                )

            result = inspect_frontend_runtime(binary, libraries, runner=runner)

            self.assertFalse(result.healthy)
            self.assertIn(
                "bundled frontend dependency escaped payload: libfreeimage.so.3",
                result.failures,
            )

    def test_frontend_rejects_build_host_cpu_isa_requirement(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "emulationstation"
            libraries = root / "lib"
            binary.write_bytes(b"ELF")
            libraries.mkdir()

            def runner(command, **_kwargs):
                if command[:2] == ["readelf", "-n"]:
                    return self._completed(
                        command,
                        "Properties: x86 ISA needed: x86-64-baseline, x86-64-v4\n",
                    )
                if command[0] == "readelf":
                    return self._completed(
                        command,
                        " 0x1 (NEEDED) Shared library: [libfreeimage.so.3]\n"
                        " 0x1 (NEEDED) Shared library: [libSDL2_mixer-2.0.so.0]\n",
                    )
                return self._completed(
                    command,
                    f"libfreeimage.so.3 => {libraries / 'libfreeimage.so.3'} (0x1)\n"
                    f"libSDL2_mixer-2.0.so.0 => {libraries / 'libSDL2_mixer-2.0.so.0'} (0x2)\n",
                )

            result = inspect_frontend_runtime(binary, libraries, runner=runner)

            self.assertIn(
                "frontend requires nonbaseline CPU ISA: x86-64-v4",
                result.failures,
            )


if __name__ == "__main__":
    unittest.main()

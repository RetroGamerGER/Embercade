from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from embercade.paths import EmbercadePaths
from embercade.pcsx2 import (
    Pcsx2RuntimeError,
    pcsx2_writable_directories,
    resolve_pcsx2_runtime,
)


class Pcsx2RuntimeTests(unittest.TestCase):
    @staticmethod
    def _resources(root: Path) -> Path:
        resources = root / "host/share/pcsx2/resources"
        resources.mkdir(parents=True)
        (resources / "GameIndex.yaml").write_text("games: {}\n", encoding="utf-8")
        (resources / "patches.zip").write_bytes(b"host patch database")
        return resources

    def test_existing_bios_is_linked_into_a_writable_private_workspace(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            bios = root / "existing bios"
            bios.mkdir()
            image = bios / "ps2-0230a.bin"
            image.write_bytes(b"bios")
            resources = self._resources(root)

            runtime = resolve_pcsx2_runtime(
                paths,
                {},
                {
                    "EMBERCADE_PCSX2_BIOS_SOURCE": str(bios),
                    "EMBERCADE_PCSX2_RESOURCES_SOURCE": str(resources),
                },
            )

            self.assertEqual(runtime.bios_dir, paths.isolated_bios / "ps2")
            self.assertEqual(runtime.resources_dir, resources)
            self.assertEqual(runtime.as_environment()["EMBERCADE_PCSX2_INSTALL_DIR"], str(resources.parent))
            self.assertEqual(image.read_bytes(), b"bios")
            linked = runtime.bios_dir / image.name
            self.assertTrue(linked.is_symlink())
            self.assertEqual(linked.resolve(), image.resolve())

    def test_configured_paths_override_environment(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            bios = root / "configured-bios"
            bios.mkdir()
            (bios / "bios.bin").write_bytes(b"bios")
            resources = self._resources(root)

            runtime = resolve_pcsx2_runtime(
                paths,
                {"pcsx2": {"bios": str(bios), "resources": str(resources)}},
                {
                    "EMBERCADE_PCSX2_BIOS_SOURCE": "/wrong/bios",
                    "EMBERCADE_PCSX2_RESOURCES_SOURCE": "/wrong/resources",
                },
            )
            self.assertEqual(runtime.bios_dir, paths.isolated_bios / "ps2")
            self.assertEqual(runtime.resources_dir, resources)

    def test_default_resources_accept_distribution_case_variant(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            bios = root / "bios"
            bios.mkdir()
            (bios / "bios.bin").write_bytes(b"bios")
            missing = root / "share/pcsx2/resources"
            resources = self._resources(root)

            with patch(
                "embercade.pcsx2._DEFAULT_RESOURCE_CANDIDATES",
                (missing, resources),
            ):
                runtime = resolve_pcsx2_runtime(
                    paths,
                    {},
                    {"EMBERCADE_PCSX2_BIOS_SOURCE": str(bios)},
                )

            self.assertEqual(runtime.resources_dir, resources)

    def test_nvm_and_mec_are_seeded_without_modifying_the_source(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            bios = root / "read-only BIOS"
            bios.mkdir()
            image = bios / "scph39001.bin"
            nvm = bios / "scph39001.nvm"
            mec = bios / "scph39001.MEC"
            image.write_bytes(b"bios")
            nvm.write_bytes(b"source nvm")
            mec.write_bytes(b"mec!")
            resources = self._resources(root)

            runtime = resolve_pcsx2_runtime(
                paths,
                {},
                {
                    "EMBERCADE_PCSX2_BIOS_SOURCE": str(bios),
                    "EMBERCADE_PCSX2_RESOURCES_SOURCE": str(resources),
                },
            )
            private_nvm = runtime.bios_dir / nvm.name
            private_mec = runtime.bios_dir / mec.name
            self.assertEqual(private_nvm.read_bytes(), b"source nvm")
            self.assertEqual(private_mec.read_bytes(), b"mec!")
            private_nvm.write_bytes(b"private update")
            self.assertEqual(nvm.read_bytes(), b"source nvm")

            # A later launch preserves PCSX2's private mutable state.
            resolve_pcsx2_runtime(
                paths,
                {},
                {
                    "EMBERCADE_PCSX2_BIOS_SOURCE": str(bios),
                    "EMBERCADE_PCSX2_RESOURCES_SOURCE": str(resources),
                },
            )
            self.assertEqual(private_nvm.read_bytes(), b"private update")

    def test_missing_bios_is_rejected_before_plugin_launch(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            resources = self._resources(root)
            with self.assertRaisesRegex(Pcsx2RuntimeError, "BIOS directory is not readable"):
                resolve_pcsx2_runtime(
                    paths,
                    {},
                    {
                        "EMBERCADE_PCSX2_BIOS_SOURCE": str(root / "missing"),
                        "EMBERCADE_PCSX2_RESOURCES_SOURCE": str(resources),
                    },
                )

    def test_every_writable_directory_is_inside_embercade_roots(self) -> None:
        paths = EmbercadePaths.from_environment(
            {
                "HOME": "/host-home",
                "EMBERCADE_CONFIG_HOME": "/project/.work/config",
                "EMBERCADE_DATA_HOME": "/project/.work/data",
                "EMBERCADE_CACHE_HOME": "/project/.work/cache",
                "EMBERCADE_STATE_HOME": "/project/.work/state",
            }
        )
        allowed = (paths.config, paths.data, paths.cache, paths.state)
        for directory in pcsx2_writable_directories(paths):
            self.assertTrue(any(directory.is_relative_to(root) for root in allowed), directory)
            self.assertNotIn("/userdata", str(directory))
            self.assertNotIn("/host-home/.config/PCSX2", str(directory))


if __name__ == "__main__":
    unittest.main()

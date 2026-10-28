from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import unittest

from embercade.batocera_config import (
    BatoceraConfigError,
    resolve_system_choice,
)
from embercade.paths import EmbercadePaths
from embercade.runtime import ProjectRuntime


class BatoceraConfigTests(unittest.TestCase):
    def test_pinned_runtime_uses_pcsx_rearmed_as_psx_default(self) -> None:
        project = Path(__file__).resolve().parents[1]
        runtime = ProjectRuntime(project)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root),
                    "EMBERCADE_CONFIG_HOME": str(root / "config/embercade"),
                    "EMBERCADE_DATA_HOME": str(root / "data/embercade"),
                }
            )
            paths.batocera_conf.parent.mkdir(parents=True)
            paths.batocera_conf.write_text("", encoding="utf-8")
            paths.emulationstation_config.mkdir(parents=True)
            (paths.emulationstation_config / "es_settings.cfg").write_text(
                "<config />\n", encoding="utf-8"
            )
            rom = root / "ROM files/007 - The World Is Not Enough (Europe).chd"

            choice = resolve_system_choice(
                system="psx",
                rom=rom,
                paths=paths,
                runtime=runtime,
                environment={"HOME": str(root), "PATH": "/usr/bin"},
            )

            self.assertEqual(choice.emulator, "libretro")
            self.assertEqual(choice.core, "pcsx_rearmed")
            self.assertFalse(choice.emulator_forced)
            self.assertFalse(choice.core_forced)

    def test_pinned_runtime_resolves_system_without_running_an_emulator(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = ProjectRuntime(root / "project")
            runtime.python.parent.mkdir(parents=True)
            runtime.python.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.python.chmod(0o755)
            paths = EmbercadePaths.from_environment(
                {
                    "HOME": str(root),
                    "EMBERCADE_CONFIG_HOME": str(root / "config/embercade"),
                    "EMBERCADE_DATA_HOME": str(root / "data/embercade"),
                }
            )
            paths.batocera_conf.parent.mkdir(parents=True)
            paths.batocera_conf.write_text("snes.core=snes9x\n", encoding="utf-8")
            rom = root / "ROM files/Super Game (Europe).sfc"
            result = CompletedProcess(
                [],
                0,
                stdout=json.dumps(
                    {
                        "system": "snes",
                        "emulator": "libretro",
                        "core": "snes9x",
                        "emulator_forced": False,
                        "core_forced": True,
                    }
                ),
                stderr="",
            )

            with patch("embercade.batocera_config.subprocess.run", return_value=result) as run:
                choice = resolve_system_choice(
                    system="snes",
                    rom=rom,
                    paths=paths,
                    runtime=runtime,
                    environment={"HOME": str(root), "PATH": "/usr/bin"},
                )

            self.assertEqual(choice.emulator, "libretro")
            self.assertEqual(choice.core, "snes9x")
            self.assertTrue(choice.core_forced)
            argv = run.call_args.args[0]
            self.assertEqual(argv[-2:], ["snes", str(rom)])
            self.assertIn("-I", argv)
            probe_env = run.call_args.kwargs["env"]
            self.assertEqual(probe_env["EMBERCADE_BATOCERA_CONF"], str(paths.batocera_conf))
            self.assertNotIn("PYTHONPATH", probe_env)

    def test_failed_probe_has_a_clear_error(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = ProjectRuntime(root / "project")
            runtime.python.parent.mkdir(parents=True)
            runtime.python.write_text("#!/bin/sh\n", encoding="utf-8")
            runtime.python.chmod(0o755)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            paths.batocera_conf.parent.mkdir(parents=True)
            paths.batocera_conf.write_text("", encoding="utf-8")
            failed = CompletedProcess([], 1, stdout="", stderr="missing default")
            with patch("embercade.batocera_config.subprocess.run", return_value=failed):
                with self.assertRaisesRegex(BatoceraConfigError, "missing default"):
                    resolve_system_choice(
                        system="snes",
                        rom=root / "game.sfc",
                        paths=paths,
                        runtime=runtime,
                        environment={"HOME": str(root)},
                    )


if __name__ == "__main__":
    unittest.main()

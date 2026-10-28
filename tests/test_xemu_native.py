"""Opt-in native initialization probe; --version never boots a game/fixture."""

import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest


@unittest.skipUnless(os.environ.get("EMBERCADE_TEST_XEMU_NATIVE") == "1",
                     "opt-in installed Xemu and graphical session required")
class NativeXemuTests(unittest.TestCase):
    def test_native_xemu_generates_and_reuses_configured_isolated_eeprom(self):
        executable = shutil.which("xemu")
        self.assertIsNotNone(executable)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = dict(os.environ)
            for variable, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"),
                                   ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"),
                                   ("XDG_STATE_HOME", "state")):
                location = root/name
                location.mkdir()
                environment[variable] = str(location)
            eeprom = root/"data/saves/xbox/xemu_eeprom.bin"
            eeprom.parent.mkdir(parents=True)
            config = root/"config/xemu.toml"
            config.write_text('[general]\nshow_welcome = true\n[sys.files]\n'
                              f'eeprom_path = "{eeprom}"\n')
            command = [executable, "-config_path", str(config), "--version"]
            first = subprocess.run(command, env=environment, text=True, capture_output=True, timeout=20)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("xemu_version:", first.stderr + first.stdout)
            self.assertEqual(eeprom.stat().st_size, 256)
            before = (eeprom.read_bytes(), eeprom.stat().st_mtime_ns)
            second = subprocess.run(command, env=environment, text=True, capture_output=True, timeout=20)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual((eeprom.read_bytes(), eeprom.stat().st_mtime_ns), before)
            self.assertFalse((root/"data/xemu/xemu/eeprom.bin").exists())

    def test_installer_codec_accepts_native_generated_image_and_preserves_identity(self):
        from unittest.mock import patch
        from embercade import xbox_eeprom as e
        from embercade.paths import EmbercadePaths
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"HOME":directory,
                "XDG_CONFIG_HOME":directory+"/config", "XDG_DATA_HOME":directory+"/data",
                "XDG_CACHE_HOME":directory+"/cache", "XDG_STATE_HOME":directory+"/state"}):
            paths=EmbercadePaths.from_environment()
            executable=Path(shutil.which("xemu"))
            generated=e.initialize(paths,executable,dict(os.environ))
            self.assertEqual(generated["version"],"1.0")
            from embercade.xemu import isolated_xemu_files
            original=e.read(isolated_xemu_files(paths).eeprom)
            changed=e.edit(original,language="de",region="europe",video="pal")
            self.assertEqual(e.inspect(changed)["language"],3)
            self.assertEqual(e._validated(original)[1][:24],e._validated(changed)[1][:24])
            # Validate the edited native image via the offline format contract;
            # no firmware/game is booted by this probe.
            with e.transaction(paths,executable) as target:e.save(target,changed,replace=True)
            self.assertEqual(e.initialize(paths,executable,dict(os.environ))["language"],3)

from pathlib import Path
from struct import pack_into
from tempfile import TemporaryDirectory
import unittest

from embercade.azahar import (
    AzaharConfigError,
    CONFIG_HEADER_SIZE,
    CONFIG_SIZE,
    LANGUAGE_BLOCK_ID,
    azahar_system_config,
    sync_azahar_system_language,
)


class AzaharConfigTests(unittest.TestCase):
    @staticmethod
    def _config(path: Path, language: int = 1) -> None:
        path.parent.mkdir(parents=True)
        data = bytearray(CONFIG_SIZE)
        pack_into("<HH", data, 0, 1, CONFIG_HEADER_SIZE)
        pack_into("<IIHH", data, 4, LANGUAGE_BLOCK_ID, language, 1, 0xE)
        path.write_bytes(data)

    def test_selected_language_updates_only_valid_isolated_cfg_block(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = azahar_system_config(root / "saves")
            self._config(config)
            before = config.read_bytes()
            batocera_conf = root / "batocera.conf"
            batocera_conf.write_text(
                "3ds.3ds_system_language=German\n", encoding="utf-8"
            )

            self.assertTrue(
                sync_azahar_system_language(
                    batocera_conf=batocera_conf,
                    saves_root=root / "saves",
                )
            )
            after = config.read_bytes()
            differences = [index for index in range(CONFIG_SIZE) if before[index] != after[index]]
            self.assertEqual(differences, [8])
            self.assertEqual(after[8], 3)
            self.assertFalse(
                sync_azahar_system_language(
                    batocera_conf=batocera_conf,
                    saves_root=root / "saves",
                )
            )

    def test_missing_first_launch_config_is_a_safe_noop(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            batocera_conf = root / "batocera.conf"
            batocera_conf.write_text(
                "3ds.3ds_system_language=German\n", encoding="utf-8"
            )
            self.assertFalse(
                sync_azahar_system_language(
                    batocera_conf=batocera_conf,
                    saves_root=root / "saves",
                )
            )

    def test_malformed_config_is_never_modified(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = azahar_system_config(root / "saves")
            config.parent.mkdir(parents=True)
            config.write_bytes(b"not a 3ds config")
            batocera_conf = root / "batocera.conf"
            batocera_conf.write_text(
                "3ds.3ds_system_language=German\n", encoding="utf-8"
            )
            before = config.read_bytes()
            with self.assertRaisesRegex(AzaharConfigError, "Unexpected.*size"):
                sync_azahar_system_language(
                    batocera_conf=batocera_conf,
                    saves_root=root / "saves",
                )
            self.assertEqual(config.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

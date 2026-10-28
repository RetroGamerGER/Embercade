from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET
import unittest

from embercade.ui_data import (
    BLOCKED_DESKTOP_FEATURES,
    REGISTRY_PATHS,
    _customize_systems,
    _filter_desktop_features,
    customize_production_systems,
    load_system_provider_defaults,
    merge_feature_overlay,
)


class UiDataTests(unittest.TestCase):
    def test_production_systems_use_stable_app_and_userdata_paths(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command>"
                "<emulators><emulator><cores><core>fceumm</core><core>nestopia</core>"
                "</cores></emulator></emulators></system>"
                "<system><name>megacd</name><path>x</path><command>x</command></system>"
                "<system><name>xbox360</name><path>x</path>"
                "<command>batocera-launch --rom %ROM%</command></system>"
                "<system><name>ports</name><path>x</path><command>x</command></system>"
                "</systemList>",
                encoding="utf-8",
            )
            customize_production_systems(path, systems=frozenset({"nes", "megacd", "xbox360"}))
            systems = ET.parse(path).getroot().findall("system")
            self.assertEqual([node.findtext("name") for node in systems], ["nes", "megacd", "xbox360"])
            self.assertEqual(systems[0].findtext("path"), "/userdata/roms/nes")
            self.assertEqual(systems[1].findtext("path"), "/userdata/roms/segacd")
            self.assertEqual(
                systems[0].findtext("command"),
                '"/app/bin/embercade" launch --system nes --rom %ROM%',
            )
            self.assertEqual(systems[2].findtext("command"),
                             '"/app/bin/embercade" launch --system xbox360 --rom %ROM%')
    def test_catalogue_uses_real_batocera_nes_definitions(self) -> None:
        joined = "\n".join(REGISTRY_PATHS)
        self.assertIn("nestopia.libretro.core.yml", joined)
        self.assertIn("fceumm.libretro.core.yml", joined)
        self.assertIn("mesen.libretro.core.yml", joined)
        self.assertIn("pcsx_rearmed.libretro.core.yml", joined)
        self.assertIn("swanstation.libretro.core.yml", joined)
        self.assertIn("mednafen_psx.libretro.core.yml", joined)
        self.assertIn("puae.libretro.core.yml", joined)
        self.assertIn("dosbox_pure.libretro.core.yml", joined)
        self.assertIn("mame078plus.libretro.core.yml", joined)
        self.assertIn("vice_x64.libretro.core.yml", joined)
        self.assertIn("melonds.libretro.core.yml", joined)
        self.assertIn("melondsds.libretro.core.yml", joined)
        self.assertIn("ppsspp.libretro.core.yml", joined)
        self.assertIn("azahar.libretro.core.yml", joined)
        self.assertIn("mupen64plus-next.libretro.core.yml", joined)
        self.assertIn("virtualjaguar.libretro.core.yml", joined)
        self.assertIn("flycast.libretro.core.yml", joined)
        self.assertIn("neocd.libretro.core.yml", joined)
        self.assertIn("beetle-saturn.libretro.core.yml", joined)
        self.assertIn("libretro.emulator.yml", joined)
        self.assertIn("dolphin.emulator.yml", joined)
        self.assertIn("xemu.emulator.yml", joined)
        self.assertIn("pcsx2.emulator.yml", joined)
        self.assertIn("rpcs3.emulator.yml", joined)
        self.assertIn("cemu.emulator.yml", joined)
        self.assertIn("xenia-edge.emulator.yml", joined)

    def test_appliance_features_are_explicitly_filtered(self) -> None:
        self.assertEqual(
            BLOCKED_DESKTOP_FEATURES,
            {
                "powermode",
                "batterymode",
                "tdp",
                "videomode",
                "wheel_rotation",
                "wheel_deadzone",
                "wheel_midzone",
                "pcsx2_crisis_fog",
                "pcsx2_crosshairs",
                "mesen_screenrotation",
            },
        )

    def test_special_input_switches_reach_es_without_appliance_calibration(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_features.cfg"
            path.write_text(
                '<features><emulator name="libretro"><cores><core name="nestopia">'
                '<sharedFeature value="use_guns" /><sharedFeature value="use_wheels" />'
                '<feature value="lightgun_map" /><feature value="wheel_rotation" />'
                '</core></cores></emulator></features>',
                encoding="utf-8",
            )
            _filter_desktop_features(path)
            core = ET.parse(path).getroot().find("./emulator/cores/core")
            self.assertIsNotNone(core)
            values = {child.get("value") for child in core}
            self.assertEqual(values, {"use_guns", "use_wheels", "lightgun_map"})

    def test_nestopia_is_the_desktop_default_even_with_real_core_choices(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList><system><name>nes</name><path>x</path><command>x</command>"
                "<emulators><emulator><cores>"
                '<core default="true">fceumm</core><core>nestopia</core>'
                "</cores></emulator></emulators></system></systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch"),
            )
            cores = ET.parse(path).getroot().findall("./system/emulators/emulator/cores/core")
            self.assertEqual(
                [(core.text, core.get("default")) for core in cores],
                [("fceumm", None), ("nestopia", "true")],
            )

    def test_azahar_language_overlay_adds_batocera_choices_once(self) -> None:
        project = Path(__file__).resolve().parents[1]
        overlay = project / "resources/ui/azahar-language.es_features.xml"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_features.cfg"
            path.write_text(
                '<features><emulator name="libretro" features=""><cores>'
                '<core name="azahar" features=""><sharedFeature value="autosave" />'
                "</core></cores></emulator></features>",
                encoding="utf-8",
            )

            merge_feature_overlay(path, overlay)
            merge_feature_overlay(path, overlay)

            root = ET.parse(path).getroot()
            languages = root.findall(
                "./emulator[@name='libretro']/cores/core[@name='azahar']"
                "/feature[@value='3ds_system_language']"
            )
            regions = root.findall(
                "./emulator[@name='libretro']/cores/core[@name='azahar']"
                "/feature[@value='3ds_system_region']"
            )
            self.assertEqual(len(languages), 1)
            self.assertEqual(len(regions), 1)
            self.assertEqual(
                [(choice.get("name"), choice.get("value")) for choice in regions[0]],
                [
                    ("Japan", "Japan"),
                    ("USA", "USA"),
                    ("Europe", "Europe"),
                    ("Australia", "Australia"),
                    ("China", "China"),
                    ("Korea", "Korea"),
                    ("Taiwan", "Taiwan"),
                ],
            )
            self.assertEqual(
                [(choice.get("name"), choice.get("value")) for choice in languages[0]],
                [
                    ("English", "English"),
                    ("Japanese", "Japanese"),
                    ("French", "French"),
                    ("Spanish", "Spanish"),
                    ("German", "German"),
                    ("Italian", "Italian"),
                    ("Dutch", "Dutch"),
                    ("Portuguese", "Portuguese"),
                    ("Russian", "Russian"),
                    ("Korean", "Korean"),
                    ("Traditional Chinese", "Traditional Chinese"),
                    ("Simplified Chinese", "Simplified Chinese"),
                ],
            )

    def test_production_systems_include_configured_provider_for_feature_lookup(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            systems_path = root / "es_systems.cfg"
            defaults_path = root / "batocera.conf"
            systems_path.write_text(
                "<systemList><system><name>3ds</name><path>x</path><command>x</command>"
                '<emulators><emulator name="azahar"><cores>'
                '<core default="true">azahar</core>'
                "</cores></emulator></emulators></system></systemList>",
                encoding="utf-8",
            )
            defaults_path.write_text(
                "# desktop selection\n"
                "3ds.emulator=libretro\n"
                "3ds.core=azahar\n"
                "3ds.3ds_system_language=German\n",
                encoding="utf-8",
            )

            defaults = load_system_provider_defaults(defaults_path)
            customize_production_systems(
                systems_path,
                systems=frozenset({"3ds"}),
                provider_defaults=defaults,
            )
            customize_production_systems(
                systems_path,
                systems=frozenset({"3ds"}),
                provider_defaults=defaults,
            )

            root_node = ET.parse(systems_path).getroot()
            cores = root_node.findall(
                "./system/emulators/emulator[@name='libretro']/cores/core"
            )
            self.assertEqual([core.text for core in cores], ["azahar"])
            self.assertEqual(defaults, {"3ds": ("libretro", "azahar")})

    def test_gamecube_uses_its_own_rom_path_and_wrapper(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command></system>"
                "<system><name>gamecube</name><path>x</path><command>x</command></system>"
                "<system><name>ps2</name><path>x</path><command>x</command></system>"
                "</systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch-nes"),
                gamecube_rom_path=Path("/roms/gamecube"),
                gamecube_launch_command=Path("/project/launch-gamecube"),
            )
            systems = ET.parse(path).getroot().findall("./system")
            self.assertEqual([system.findtext("name") for system in systems], ["nes", "gamecube"])
            self.assertEqual(systems[1].findtext("path"), "/roms/gamecube")
            self.assertEqual(
                systems[1].findtext("command"),
                '"/project/launch-gamecube" --rom %ROM%',
            )

    def test_wii_uses_dolphin_system_data_and_its_own_wrapper(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command></system>"
                "<system><name>wii</name><path>x</path><command>x</command></system>"
                "</systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch-nes"),
                wii_rom_path=Path("/roms/wii"),
                wii_launch_command=Path("/project/launch-wii"),
            )
            systems = ET.parse(path).getroot().findall("./system")
            self.assertEqual([system.findtext("name") for system in systems], ["nes", "wii"])
            self.assertEqual(systems[1].findtext("path"), "/roms/wii")
            self.assertEqual(
                systems[1].findtext("command"),
                '"/project/launch-wii" --rom %ROM%',
            )

    def test_generic_libretro_systems_share_one_system_aware_wrapper(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command></system>"
                "<system><name>snes</name><path>x</path><command>x</command></system>"
                "<system><name>gba</name><path>x</path><command>x</command></system>"
                "<system><name>sega32x</name><path>x</path><command>x</command>"
                "<group>megadrive</group></system>"
                "</systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch-nes"),
                libretro_systems={
                    "snes": Path("/isolated/snes"),
                    "gba": Path("/isolated/gba"),
                    "sega32x": Path("/isolated/sega32x"),
                },
                libretro_launch_command=Path("/project/launch-libretro"),
            )
            systems = ET.parse(path).getroot().findall("./system")
            self.assertEqual(
                [system.findtext("name") for system in systems],
                ["nes", "snes", "gba", "sega32x"],
            )
            self.assertEqual(
                systems[1].findtext("command"),
                '"/project/launch-libretro" --system snes --rom %ROM%',
            )
            self.assertEqual(
                systems[2].findtext("command"),
                '"/project/launch-libretro" --system gba --rom %ROM%',
            )
            self.assertIsNone(systems[3].find("group"))
            self.assertEqual(
                systems[3].findtext("command"),
                '"/project/launch-libretro" --system sega32x --rom %ROM%',
            )

    def test_xbox_uses_its_own_rom_path_and_wrapper(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command></system>"
                "<system><name>xbox</name><path>x</path><command>x</command></system>"
                "</systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch-nes"),
                xbox_rom_path=Path("/roms/xbox"),
                xbox_launch_command=Path("/project/launch-xbox"),
            )
            systems = ET.parse(path).getroot().findall("./system")
            self.assertEqual([system.findtext("name") for system in systems], ["nes", "xbox"])
            self.assertEqual(systems[1].findtext("path"), "/roms/xbox")
            self.assertEqual(
                systems[1].findtext("command"),
                '"/project/launch-xbox" --rom %ROM%',
            )

    def test_generic_external_system_uses_system_aware_wrapper(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command></system>"
                "<system><name>xbox360</name><path>x</path><command>x</command></system>"
                "</systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch-nes"),
                external_systems={"xbox360": Path("/roms/xbox360")},
                external_launch_command=Path("/project/launch-system"),
            )
            systems = ET.parse(path).getroot().findall("./system")
            self.assertEqual([system.findtext("name") for system in systems], ["nes", "xbox360"])
            self.assertEqual(systems[1].findtext("path"), "/roms/xbox360")
            self.assertEqual(
                systems[1].findtext("command"),
                '"/project/launch-system" --system xbox360 --rom %ROM%',
            )

    def test_ps2_uses_modern_plugin_system_and_its_own_wrapper(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command></system>"
                "<system><name>ps2</name><path>x</path><command>x</command></system>"
                "</systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch-nes"),
                ps2_rom_path=Path("/roms/ps2"),
                ps2_launch_command=Path("/project/launch-ps2"),
            )
            systems = ET.parse(path).getroot().findall("./system")
            self.assertEqual([system.findtext("name") for system in systems], ["nes", "ps2"])
            self.assertEqual(systems[1].findtext("path"), "/roms/ps2")
            self.assertEqual(
                systems[1].findtext("command"),
                '"/project/launch-ps2" --rom %ROM%',
            )

    def test_ps3_uses_modern_plugin_system_and_its_own_wrapper(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "es_systems.cfg"
            path.write_text(
                "<systemList>"
                "<system><name>nes</name><path>x</path><command>x</command></system>"
                "<system><name>ps3</name><path>x</path><extension>.iso .ps3 .psn .squashfs</extension>"
                "<command>x</command></system>"
                "</systemList>",
                encoding="utf-8",
            )
            _customize_systems(
                path,
                rom_path=Path("/roms/nes"),
                launch_command=Path("/project/launch-nes"),
                ps3_rom_path=Path("/roms/ps3"),
                ps3_launch_command=Path("/project/launch-ps3"),
            )
            systems = ET.parse(path).getroot().findall("./system")
            self.assertEqual([system.findtext("name") for system in systems], ["nes", "ps3"])
            self.assertEqual(systems[1].findtext("path"), "/roms/ps3")
            self.assertEqual(systems[1].findtext("extension"), ".iso .ps3 .psn")
            self.assertEqual(
                systems[1].findtext("command"),
                '"/project/launch-ps3" --rom %ROM%',
            )


if __name__ == "__main__":
    unittest.main()

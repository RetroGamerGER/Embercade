from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import unittest

PROJECT = Path(__file__).resolve().parents[1]


class DecorationChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("g++"):
            raise unittest.SkipTest("C++ compiler required for native menu policy test")
        cls.temp = TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.binary = Path(cls.temp.name) / "choices"
        code = r'''
#include "EmbercadeDecorationAvailability.h"
#include <algorithm>
#include <filesystem>
#include <iostream>
#include <vector>
namespace fs=std::filesystem;
int main(int,char** argv) {
    if (std::string(argv[1])=="selection") {
        std::cout << EmbercadeDecorations::selectionName(argv[2]); return 0;
    }
    fs::path root=argv[1]; std::string system=argv[2]; bool specific=std::string(argv[3])=="system";
    std::vector<fs::path> folders;
    for(auto& path:fs::directory_iterator(root)) if(path.is_directory()) folders.push_back(path.path());
    std::sort(folders.begin(),folders.end());
    std::vector<std::string> names; EmbercadeDecorations::Sources sources;
    for(auto& folder:folders) {
        auto name=folder.filename().string();
        if(name=="default" || name=="consoles" || fs::exists(folder/".embercade-unavailable")) continue;
        auto image=EmbercadeDecorations::preview(folder.string(),system,specific,
            [](const std::string& file){return fs::is_regular_file(file);});
        if(specific && image.empty()) continue;
        if(specific) {
            auto info=fs::path(image).replace_extension(".info");
            auto png=fs::canonical(image).string(); auto base=fs::canonical(folder).string()+"/";
            auto slot=sources.select(png+"\n"+fs::canonical(info).string(),png.compare(0,base.size(),base)==0,names.size());
            if(slot==EmbercadeDecorations::Sources::skip) continue;
            if(slot<names.size()) {names[slot]=name;continue;}
        }
        names.push_back(name);
    }
    std::sort(names.begin(),names.end());
    for(auto& name:names) std::cout<<name<<"\n";
}
'''
        result = subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
            "-I", str(PROJECT / "patches/emulationstation"), "-x", "c++", "-",
            "-o", str(cls.binary)], input=code, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def choices(self, root, system, scope="system"):
        result = subprocess.run([str(self.binary), str(root), system, scope],
                                capture_output=True, text=True, check=True)
        return result.stdout.splitlines()

    def test_system_menu_omits_generic_previews_and_incomplete_system_pairs(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("default_curve", "default_unglazed", "missing-layout"):
                (root / name / "systems").mkdir(parents=True)
                (root / name / "default.png").write_bytes(b"generic preview")
            (root / "default_unglazed/systems/psp.png").write_bytes(b"PSP art")
            (root / "default_unglazed/systems/psp.info").write_text("{}")
            (root / "missing-layout/systems/psp.png").write_bytes(b"no layout")
            self.assertEqual(self.choices(root, "psp"), ["default_unglazed"])
            self.assertEqual(self.choices(root, "snes"), [])
            self.assertEqual(self.choices(root, "psp", "global"), ["default_curve", "default_unglazed", "missing-layout"])

    def test_exact_source_aliases_offer_the_owning_set_once(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            real = root / "default_unglazed/systems"
            real.mkdir(parents=True)
            (real / "psp.png").write_bytes(b"PSP art")
            (real / "psp.info").write_text("{}")
            alias = root / "ambiance_night/systems"
            alias.mkdir(parents=True)
            for name in ("psp.png", "psp.info"):
                (alias / name).symlink_to("../../default_unglazed/systems/" + name)
            self.assertEqual(self.choices(root, "psp"), ["default_unglazed"])

    def test_different_layouts_for_same_png_are_not_removed(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("normal", "alternative"):
                (root / name / "systems").mkdir(parents=True)
                (root / name / "systems/psp.info").write_text("{}")
            (root / "normal/systems/psp.png").write_bytes(b"PSP art")
            (root / "alternative/systems/psp.png").symlink_to("../../normal/systems/psp.png")
            self.assertEqual(self.choices(root, "psp"), ["alternative", "normal"])

    def test_legacy_name_maps_for_display_without_changing_other_saved_ids(self):
        for value, expected in (("consoles", "default_unglazed"), ("none", "none"), ("my-custom-set", "my-custom-set")):
            run = subprocess.run([str(self.binary), "selection", value], capture_output=True, text=True, check=True)
            self.assertEqual(run.stdout, expected)

    def test_prepared_official_psp_menu_has_one_real_choice_and_global_keeps_13(self):
        root = PROJECT / ".work/decorations"
        if not (root / "embercade-collection.json").is_file():
            self.skipTest("Prepared official collection required")
        self.assertEqual(self.choices(root, "psp"), ["default_unglazed"])
        global_sets = self.choices(root, "psp", "global")
        self.assertEqual(len(global_sets), 13)
        self.assertNotIn("animated", global_sets)
        self.assertNotIn("consoles", global_sets)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.resources import BatoceraResources, ResourceError


class BatoceraResourcesTests(unittest.TestCase):
    def test_shader_and_bezel_resolvers_use_static_project_resources(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            share = project / ".work/ui/share/batocera"
            shader = share / "shaders/crt/crt-easymode.slangp"
            defaults = share / "shaders/configs/rendering-defaults.yml"
            bezel = share / "datainit/decorations/consoles/systems/nes.png"
            info = bezel.with_suffix(".info")
            for path in (shader, defaults, bezel, info):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"resource")

            resources = BatoceraResources.for_project(project, {})
            resources.validate()

            self.assertEqual(
                resources.shader_preset("crt/crt-easymode"), shader.resolve()
            )
            self.assertEqual(
                resources.system_bezel("consoles", "nes"),
                (bezel.resolve(), info.resolve()),
            )
            for path in (resources.shaders, resources.decorations):
                self.assertNotIn("/userdata", str(path))

    def test_missing_shader_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            resources = BatoceraResources(root / "shaders", root / "decorations")
            with self.assertRaisesRegex(ResourceError, "Shader preset is unavailable"):
                resources.shader_preset("crt/missing")

    def test_shader_path_cannot_escape_resource_root(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.slangp"
            outside.write_bytes(b"shader")
            resources = BatoceraResources(root / "shaders", root / "decorations")
            with self.assertRaisesRegex(ResourceError, "Shader preset is unavailable"):
                resources.shader_preset("../outside")


if __name__ == "__main__":
    unittest.main()

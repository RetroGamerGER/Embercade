from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from embercade.shaders import (
    ShaderResourceError,
    dependency_graph,
    load_catalog,
    prepare_runtime,
    validate_runtime,
)


class ShaderResourceTests(unittest.TestCase):
    def _catalog(self, root: Path, upstream: str = "crt/example") -> Path:
        path = root / "catalog.toml"
        path.write_text(
            '[catalog]\nformat = 1\nbackend = "slang"\n\n'
            '[[preset]]\nid = "example"\nlabel = "Example"\n'
            f'upstream = "{upstream}"\nscanlines = true\n'
            'license = "Test license"\nattribution = "Test author"\n',
            encoding="utf-8",
        )
        return path

    def test_prepare_generates_curated_menu_mapping_and_complete_alias(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            preset = source / "crt/example.slangp"
            shader = source / "crt/shaders/example.slang"
            include = source / "crt/shaders/helper.inc"
            texture = source / "crt/shaders/frame.png"
            for path in (preset, shader, include, texture):
                path.parent.mkdir(parents=True, exist_ok=True)
            (source / "README.md").write_text("official source", encoding="utf-8")
            preset.write_text(
                'shaders = 1\nshader0 = "shaders/example.slang"\n'
                'textures = "FRAME"\nFRAME = "shaders/frame.png"\n',
                encoding="utf-8",
            )
            shader.write_text('#include "helper.inc"\n', encoding="utf-8")
            include.write_text("// dependency\n", encoding="utf-8")
            texture.write_bytes(b"png")
            catalogue = self._catalog(root)
            destination = root / "prepared"

            prepare_runtime(source, destination, catalogue)
            graphs = validate_runtime(destination, catalogue)

            config = destination / "configs/example/rendering-defaults.yml"
            alias = destination / "embercade/example.slangp"
            self.assertIn("shader: embercade/example", config.read_text())
            self.assertEqual(
                alias.read_text(encoding="utf-8"),
                '#reference "../crt/example.slangp"\n',
            )
            self.assertEqual(
                {path.relative_to(destination).as_posix() for path in graphs["example"]},
                {
                    "embercade/example.slangp",
                    "crt/example.slangp",
                    "crt/shaders/example.slang",
                    "crt/shaders/helper.inc",
                    "crt/shaders/frame.png",
                },
            )

    def test_missing_transitive_dependency_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            preset = root / "example.slangp"
            preset.write_text("shader0 = missing.slang\n", encoding="utf-8")
            with self.assertRaisesRegex(ShaderResourceError, "Missing shader dependency"):
                dependency_graph(root, (preset,))

    def test_catalogue_rejects_escape_paths(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            catalogue = self._catalog(root, "../outside")
            with self.assertRaisesRegex(ShaderResourceError, "Invalid upstream"):
                load_catalog(catalogue)

    def test_product_catalogue_is_curated_and_includes_required_groups(self) -> None:
        project = Path(__file__).resolve().parents[1]
        entries = load_catalog(project / "resources/shaders/catalog.toml")
        identifiers = {entry.identifier for entry in entries}
        self.assertEqual(len(entries), 26)
        self.assertTrue(
            {
                "newpixie",
                "crt-easymode",
                "crt-lottes",
                "crt-lottes-fast",
                "zfast-crt",
                "mega-bezel",
                "sharp-bilinear",
                "lcd-grid",
                "psp-color",
                "gba-color",
                "gbc-color",
                "advanced-aa",
                "bevel",
                "simpletex",
            } <= identifiers,
        )
        self.assertEqual(
            next(entry.label for entry in entries if entry.identifier == "newpixie"),
            "NewPixie",
        )


if __name__ == "__main__":
    unittest.main()

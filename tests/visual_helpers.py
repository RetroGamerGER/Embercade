"""Synthetic resource provider for generator-only tests; never run in an emulator."""
from pathlib import Path
from embercade.shaders import load_catalog


def shader_provider_fixture(root: Path) -> Path:
    provider = root / "shader package fixture"
    provider.mkdir(parents=True, exist_ok=True)
    (provider / "README.md").write_text("Synthetic generator fixture, not upstream artwork/code")
    catalog = Path(__file__).resolve().parents[1] / "resources/shaders/catalog.toml"
    for entry in load_catalog(catalog):
        preset = provider / (entry.upstream + ".slangp")
        preset.parent.mkdir(parents=True, exist_ok=True)
        preset.write_text('shaders = 1\nshader0 = "fixture.slang"\n')
        (preset.parent / "fixture.slang").write_text("// Not an executable shader; dry-run only\n")
    return provider

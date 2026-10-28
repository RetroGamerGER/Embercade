"""Prepare and validate Embercade's pinned Libretro shader resources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from typing import Mapping


class ShaderResourceError(RuntimeError):
    """A curated shader or one of its dependencies is unavailable."""


@dataclass(frozen=True, slots=True)
class CuratedShader:
    identifier: str
    label: str
    upstream: str
    scanlines: bool
    disable_external_bezel: bool
    license: str
    attribution: str

    @property
    def alias_name(self) -> str:
        suffix = "-noBezel" if self.disable_external_bezel else ""
        return f"{self.identifier}{suffix}"


_IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REFERENCE = re.compile(r'^\s*#reference\s+["\']([^"\']+)["\']')
_INCLUDE = re.compile(r'^\s*#include\s+["\']([^"\']+)["\']')
_ASSIGNMENT = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def load_catalog(path: Path) -> tuple[CuratedShader, ...]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    if document.get("catalog") != {"format": 1, "backend": "slang"}:
        raise ShaderResourceError(f"Unsupported shader catalogue header: {path}")

    entries: list[CuratedShader] = []
    seen: set[str] = set()
    for raw in document.get("preset", ()):
        entry = CuratedShader(
            identifier=str(raw["id"]),
            label=str(raw["label"]),
            upstream=str(raw["upstream"]),
            scanlines=bool(raw["scanlines"]),
            disable_external_bezel=bool(raw.get("disable_external_bezel", False)),
            license=str(raw["license"]),
            attribution=str(raw["attribution"]),
        )
        if not _IDENTIFIER.fullmatch(entry.identifier):
            raise ShaderResourceError(f"Invalid shader identifier: {entry.identifier}")
        if entry.identifier in seen:
            raise ShaderResourceError(f"Duplicate shader identifier: {entry.identifier}")
        upstream = Path(entry.upstream)
        if upstream.is_absolute() or ".." in upstream.parts or upstream.suffix:
            raise ShaderResourceError(f"Invalid upstream shader path: {entry.upstream}")
        if not entry.label.strip():
            raise ShaderResourceError(f"Missing label for shader: {entry.identifier}")
        seen.add(entry.identifier)
        entries.append(entry)
    if not entries:
        raise ShaderResourceError(f"Shader catalogue is empty: {path}")
    return tuple(entries)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _resolve_dependency(root: Path, parent: Path, value: str) -> Path:
    dependency = (parent / value).resolve()
    if not dependency.is_relative_to(root):
        raise ShaderResourceError(f"Shader dependency escapes resource root: {dependency}")
    if not dependency.is_file():
        raise ShaderResourceError(f"Missing shader dependency: {dependency}")
    return dependency


def _preset_dependencies(root: Path, path: Path) -> tuple[Path, ...]:
    assignments: dict[str, str] = {}
    dependencies: list[Path] = []
    for line in path.read_text(encoding="utf-8-sig", errors="strict").splitlines():
        if match := _REFERENCE.match(line):
            dependencies.append(_resolve_dependency(root, path.parent, match.group(1)))
            continue
        if match := _ASSIGNMENT.match(line):
            assignments[match.group(1)] = _unquote(match.group(2))

    for key, value in assignments.items():
        if re.fullmatch(r"shader\d+", key):
            dependencies.append(_resolve_dependency(root, path.parent, value))
    for texture in assignments.get("textures", "").split(";"):
        texture = texture.strip()
        if texture and texture in assignments:
            dependencies.append(
                _resolve_dependency(root, path.parent, assignments[texture])
            )
    return tuple(dependencies)


def _source_dependencies(root: Path, path: Path) -> tuple[Path, ...]:
    dependencies: list[Path] = []
    for line in path.read_text(encoding="utf-8-sig", errors="strict").splitlines():
        if match := _INCLUDE.match(line):
            dependencies.append(_resolve_dependency(root, path.parent, match.group(1)))
    return tuple(dependencies)


def dependency_graph(root: Path, presets: Iterable[Path]) -> frozenset[Path]:
    """Return every local file reachable from the selected shader presets."""
    root = root.resolve()
    pending = [path.resolve() for path in presets]
    visited: set[Path] = set()
    while pending:
        path = pending.pop()
        if not path.is_relative_to(root) or not path.is_file():
            raise ShaderResourceError(f"Shader preset is unavailable: {path}")
        if path in visited:
            continue
        visited.add(path)
        if path.suffix in {".slangp", ".params"}:
            pending.extend(_preset_dependencies(root, path))
        elif path.suffix in {".slang", ".h", ".inc"}:
            pending.extend(_source_dependencies(root, path))
    return frozenset(visited)


def validate_runtime(root: Path, catalog_path: Path) -> dict[str, frozenset[Path]]:
    root = root.resolve()
    if not (root / "README.md").is_file():
        raise ShaderResourceError(f"Official shader README is missing: {root}")
    if not (root / "configs/rendering-defaults.yml").is_file():
        raise ShaderResourceError(f"Default shader configuration is missing: {root}")

    graphs: dict[str, frozenset[Path]] = {}
    for entry in load_catalog(catalog_path):
        config = root / "configs" / entry.identifier / "rendering-defaults.yml"
        alias = root / "embercade" / f"{entry.alias_name}.slangp"
        if not config.is_file():
            raise ShaderResourceError(f"Curated shader configuration is missing: {config}")
        expected = f"shader: embercade/{entry.alias_name}"
        if expected not in config.read_text(encoding="utf-8"):
            raise ShaderResourceError(f"Curated shader mapping is invalid: {config}")
        graphs[entry.identifier] = dependency_graph(root, (alias,))
    return graphs


def prepare_runtime(source: Path, destination: Path, catalog_path: Path) -> None:
    if destination.exists():
        raise ShaderResourceError(f"Shader destination already exists: {destination}")
    shutil.copytree(source, destination, symlinks=True)
    catalogue = load_catalog(catalog_path)
    configs = destination / "configs"
    aliases = destination / "embercade"
    configs.mkdir()
    aliases.mkdir()
    (configs / "rendering-defaults.yml").write_text(
        "default:\n  shader:\n  scanline: false\n", encoding="utf-8"
    )
    for entry in catalogue:
        upstream = destination / f"{entry.upstream}.slangp"
        if not upstream.is_file():
            raise ShaderResourceError(f"Curated upstream preset is missing: {upstream}")
        (aliases / f"{entry.alias_name}.slangp").write_text(
            f'#reference "../{entry.upstream}.slangp"\n', encoding="utf-8"
        )
        config = configs / entry.identifier / "rendering-defaults.yml"
        config.parent.mkdir()
        config.write_text(
            "default:\n"
            f"  shader: embercade/{entry.alias_name}\n"
            f"  scanline: {'true' if entry.scanlines else 'false'}\n",
            encoding="utf-8",
        )
    validate_runtime(destination, catalog_path)


HOST_SLANG_ROOTS = (
    Path("/usr/share/libretro/shaders/shaders_slang"),
    Path("/usr/share/retroarch/shaders/shaders_slang"),
)


def find_host_shader_root(environment: Mapping[str, str] | None = None) -> Path | None:
    """Locate the actual installed collection, including distro package paths.

    The override supports read-only custom providers and isolated package tests;
    it does not enable a shader or change the user's emulator settings.
    """
    env = os.environ if environment is None else environment
    explicit = env.get("EMBERCADE_HOST_SLANG_ROOT")
    candidates = [Path(explicit).expanduser()] if explicit else list(HOST_SLANG_ROOTS)
    if not explicit and not any((p / "README.md").is_file() for p in candidates):
        try:
            result = subprocess.run(["pacman", "-Qlq", "libretro-shaders-slang"],
                env=dict(env), capture_output=True, text=True, timeout=5, check=False)
            if result.returncode == 0:
                candidates += [Path(line).parent for line in result.stdout.splitlines()
                    if line.endswith("/README.md") and "/shaders/" in line]
        except (OSError, subprocess.TimeoutExpired):
            pass
    for candidate in candidates:
        if candidate.is_absolute() and (candidate / "README.md").is_file():
            return candidate.resolve()
    return None


def available_presets(root: Path | None, catalog_path: Path) -> tuple[dict, dict]:
    """Validate presets, includes, textures and LUTs before offering a menu item."""
    available, unavailable = {}, {}
    for entry in load_catalog(catalog_path):
        try:
            if root is None:
                raise ShaderResourceError("Install optional host software: libretro-shaders-slang")
            graph = dependency_graph(root, (root / f"{entry.upstream}.slangp",))
        except (OSError, UnicodeError, ShaderResourceError) as error:
            unavailable[entry.identifier] = str(error)
        else:
            available[entry.identifier] = graph
    return available, unavailable


def prepare_host_template(destination: Path, catalog_path: Path) -> None:
    """Prepare only Embercade's small mappings; no upstream shader tree."""
    destination.mkdir(parents=True)
    (destination / "configs").mkdir()
    (destination / "configs/rendering-defaults.yml").write_text(
        "default:\n  shader:\n  scanline: false\n", encoding="utf-8")
    metadata = destination / "embercade-metadata"
    metadata.mkdir()
    shutil.copy2(catalog_path, metadata / "catalog.toml")
    (metadata / "provider.json").write_text(json.dumps({
        "mode": "host-package", "package": "libretro-shaders-slang",
        "upstream": "https://github.com/libretro/slang-shaders",
        "license": "Original per-file and per-directory upstream terms apply",
    }, indent=2) + "\n")


def prepare_host_runtime(template: Path, session_root: Path,
                         environment: Mapping[str, str]) -> Path:
    """Build a session-only menu from the readable host provider.

    Never writes into a package, AppImage, normal RetroArch profile or the user's
    saved shader directory. Refresh on launch so removed resources cannot leave
    a stale menu mapping active. Invalid saved choices are handled by configgen.
    """
    catalog = template / "embercade-metadata/catalog.toml"
    if not (template / "embercade-metadata/provider.json").is_file():
        return template  # Older private Gold payloads retain their own resources.
    root = find_host_shader_root(environment)
    available, unavailable = available_presets(root, catalog)
    session_root.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="shader-resources-", dir=session_root))
    prepare_host_template(destination / "tree", catalog)
    tree = destination / "tree"
    aliases = tree / "embercade"
    aliases.mkdir()
    if root is not None:
        (tree / "provider").symlink_to(root, target_is_directory=True)
    for entry in load_catalog(catalog):
        if entry.identifier not in available:
            continue
        # Keep aliases/names stable, including configgen's noBezel convention.
        (aliases / f"{entry.alias_name}.slangp").write_text(
            f'#reference "../provider/{entry.upstream}.slangp"\n', encoding="utf-8")
        config = tree / "configs" / entry.identifier / "rendering-defaults.yml"
        config.parent.mkdir()
        config.write_text("default:\n" + f"  shader: embercade/{entry.alias_name}\n"
            + f"  scanline: {'true' if entry.scanlines else 'false'}\n", encoding="utf-8")
    (tree / "embercade-metadata/status.json").write_text(json.dumps({
        "provider": str(root) if root else None, "available": sorted(available),
        "unavailable": unavailable,
    }, indent=2) + "\n")
    return tree


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m embercade.shaders")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--source", required=True, type=Path)
    prepare.add_argument("--destination", required=True, type=Path)
    prepare.add_argument("--catalog", required=True, type=Path)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--root", required=True, type=Path)
    validate.add_argument("--catalog", required=True, type=Path)
    host = subparsers.add_parser("host-template")
    host.add_argument("--destination", required=True, type=Path)
    host.add_argument("--catalog", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "host-template":
            prepare_host_template(args.destination, args.catalog)
            print("Prepared host shader mappings; no Libretro collection embedded.")
            return 0
        elif args.command == "prepare":
            prepare_runtime(args.source, args.destination, args.catalog)
            graphs = validate_runtime(args.destination, args.catalog)
        else:
            graphs = validate_runtime(args.root, args.catalog)
    except (OSError, ShaderResourceError, tomllib.TOMLDecodeError) as error:
        parser.error(str(error))
    print(
        f"Validated {len(graphs)} curated shader presets "
        f"and {len(set().union(*graphs.values()))} dependency files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

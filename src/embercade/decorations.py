"""Prepare the official RetroBat collection without importing legacy artwork."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tomllib

SETS = (
    "ambiance_broadcast", "ambiance_gameroom", "ambiance_monitor_1084s",
    "ambiance_night", "ambiance_vintage_tv", "animated", "arcade_1980s",
    "arcade_1980s_vertical", "arcade_vertical_default", "default_curve",
    "default_curve_night", "default_nocurve", "default_nocurve_night",
    "default_unglazed",
)
FALLBACK = "default_unglazed"


class DecorationResourceError(RuntimeError):
    pass


def prepare_collection(source: Path, destination: Path, lock_path: Path) -> dict:
    """Copy pinned resources unchanged and add only Linux integration links.

    Upstream ambiance/arcade links target an absent `default` directory. RetroBat
    selects a default variant at installation time; we use its unglazed variant.
    `consoles` is a compatibility name for that same RetroBat set, never old art.
    """
    if destination.exists() or destination.is_symlink():
        raise DecorationResourceError(f"Destination already exists: {destination}")
    if {p.name for p in source.iterdir() if p.is_dir()} != set(SETS):
        raise DecorationResourceError("Unexpected RetroBat collection structure")
    lock = tomllib.loads(lock_path.read_text())["retrobat"]
    # A malformed source must not gain access outside its own tree when copied.
    for path in source.rglob("*"):
        if path.is_symlink():
            target = Path(os.path.normpath(path.parent / os.readlink(path)))
            if not target.absolute().is_relative_to(source.absolute()):
                raise DecorationResourceError(f"External upstream link: {path}")
    shutil.copytree(source, destination, symlinks=True)
    (destination / "default").symlink_to(FALLBACK, target_is_directory=True)
    (destination / "consoles").symlink_to(FALLBACK, target_is_directory=True)
    singular = destination / "arcade_vertical_default"
    if (singular / "system").is_dir() and not (singular / "systems").exists():
        (singular / "systems").symlink_to("system", target_is_directory=True)
    aliases = []
    # Some Windows-authored entries are text files containing only the target
    # filename, rather than Git symlinks. Linux's JSON/PNG readers cannot consume
    # those stubs. Materialize the intended links; never rewrite image pixels.
    for path in destination.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix not in {".png", ".info"} or path.stat().st_size > 4096:
            continue
        try:
            value = path.read_text(encoding="utf-8-sig").strip()
        except UnicodeError:
            continue
        if value.endswith(path.suffix) and not value.startswith("{") and "\n" not in value:
            target = (path.parent / value).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise DecorationResourceError(f"External text alias: {path}")
            path.unlink()
            path.symlink_to(value)
            aliases.append(str(path.relative_to(destination)))
    fallbacks = []
    # The unglazed set covers PSP/DS/Amiga while nocurve covers additional
    # computers/rotations. Complete the legacy replacement using only the
    # same-system official RetroBat files, never the old captured collection.
    base = destination / FALLBACK
    other = destination / "default_nocurve"
    for original in (other / "systems").glob("*"):
        target = base / "systems" / original.name
        if original.suffix in {".png", ".info"} and original.is_file() and not target.exists() and not target.is_symlink():
            target.symlink_to("../../default_nocurve/systems/" + original.name)
            fallbacks.append(str(target.relative_to(destination)))
    for name in ("default.png", "default.info"):
        target = base / name
        if not target.exists() and not target.is_symlink() and (other / name).is_file():
            target.symlink_to("../default_nocurve/" + name)
            fallbacks.append(str(target.relative_to(destination)))
    # One upstream vertical-set link uses SegaCD's alternate name `segacd`.
    # Batocera/RetroBat's actual system filename is `megacd`.
    for suffix in (".png", ".info"):
        target = base / "systems" / ("segacd" + suffix)
        if not target.exists() and (target.parent / ("megacd" + suffix)).is_file():
            target.symlink_to("megacd" + suffix)
            fallbacks.append(str(target.relative_to(destination)))
    # Retain the complete upstream animation data, but do not advertise a static
    # preview as functioning animation in the current PNG-only renderer.
    (destination / "animated" / ".embercade-unavailable").write_text(
        "Animated decoration playback is not implemented by this renderer.\n"
    )
    report = validate_collection(destination)
    report.update(commit=lock["commit"], repository=lock["repository"],
                  license_decision=lock["distribution_decision"],
                  legacy_selection={"consoles": FALLBACK}, normalized_text_aliases=sorted(aliases),
                  same_system_fallback_links=sorted(fallbacks))
    (destination / "embercade-collection.json").write_text(json.dumps(report, indent=2) + "\n")
    shutil.copy2(lock_path, destination / "embercade-decorations.lock")
    return report


def validate_collection(root: Path) -> dict:
    if not all((root / name).is_dir() for name in SETS):
        raise DecorationResourceError("Incomplete RetroBat collection")
    if {p.name for p in root.iterdir() if p.is_dir()} != set(SETS) | {"default", "consoles"}:
        raise DecorationResourceError("Unexpected/legacy decoration directory in payload")
    if (root / "consoles").resolve() != (root / FALLBACK).resolve():
        raise DecorationResourceError("Legacy selection must reference RetroBat")
    links = [p for p in root.rglob("*") if p.is_symlink()]
    if any(not p.resolve().is_relative_to(root.resolve()) for p in links):
        raise DecorationResourceError("Decoration link escapes the collection")
    # Missing upstream targets are reported, never replaced with legacy artwork
    # or an arbitrary other system's graphic. Batocera falls back to default.png.
    broken = sorted(str(p.relative_to(root)) for p in links if not p.exists())
    report = {"sets": [], "special_unavailable": ["animated"], "missing_upstream_links": broken}
    for name in SETS:
        path = root / name
        systems = path / "systems"
        # Count selectable PNG+INFO pairs, not preview files or animation frames.
        pairs = sorted(p.stem for p in systems.glob("*.png") if p.with_suffix(".info").is_file())
        for png in systems.glob("*.png"):
            info = png.with_suffix(".info")
            if info.is_file() and name != "animated":
                try:
                    json.loads(info.read_text(encoding="utf-8-sig"))
                except (UnicodeError, ValueError) as error:
                    raise DecorationResourceError(f"Invalid layout: {info}") from error
        report["sets"].append({"id": name, "selectable": name != "animated",
            "systems": pairs, "generic_fallback": (path / "default.png").is_file()
            and (path / "default.info").is_file()})
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()
    result = (prepare_collection(args.source, args.destination, args.lock)
              if args.source else validate_collection(args.destination))
    print(f"Validated {len(result['sets'])} official RetroBat sets; animation remains unavailable.")


if __name__ == "__main__":
    main()

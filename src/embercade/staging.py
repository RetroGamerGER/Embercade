"""Build a relocatable, install-shaped Embercade staging tree."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import argparse
import csv
import json
import os
import shutil
import stat
import subprocess
import tomllib

from embercade.elf_runtime import inspect_frontend_runtime
from embercade.launcher import SUPPORTED_LAUNCH_SYSTEMS
from embercade.shaders import ShaderResourceError, load_catalog
from embercade.decorations import DecorationResourceError, validate_collection
from embercade.ui_data import (
    _filter_desktop_features,
    customize_production_systems,
    load_system_provider_defaults,
    merge_feature_overlay,
)
from embercade.version import FRONTEND_PRODUCT_LABEL, __version__


class StagingError(RuntimeError):
    """A pinned staging prerequisite is missing or inconsistent."""


def render_desktop_entry(template: str) -> str:
    """Keep the visible desktop name aligned with the central product label."""
    placeholder = "@EMBERCADE_PRODUCT_LABEL@"
    if template.count(placeholder) != 1 or f"Name={placeholder}" not in template.splitlines():
        raise StagingError("Desktop template must contain one product-name placeholder")
    return template.replace(placeholder, FRONTEND_PRODUCT_LABEL)


def _file_digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _tree_digest(root: Path) -> str:
    entries: list[Path] = []
    for base, directories, files in os.walk(root, followlinks=False):
        base_path = Path(base)
        entries.extend(base_path / name for name in files)
        entries.extend(
            path
            for name in directories
            if (path := base_path / name).is_symlink()
        )
    digest = sha256()
    for path in sorted(entries, key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"L")
            digest.update(os.readlink(path).encode())
        else:
            digest.update(b"F")
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _copy_tree(
    source: Path,
    destination: Path,
    *,
    ignore: Any = None,
) -> None:
    if not source.is_dir():
        raise StagingError(f"Missing staging directory: {source}")
    shutil.copytree(source, destination, symlinks=True, ignore=ignore)


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _validate_frontend_runtime(binary: Path, library_root: Path) -> None:
    report = inspect_frontend_runtime(binary, library_root)
    if not report.healthy:
        raise StagingError("; ".join(report.failures))


def _prune_runtime_bin(directory: Path) -> None:
    """Keep relocatable interpreter links; product entry points are rebuilt below."""
    for path in directory.iterdir():
        if path.is_file() and not path.is_symlink():
            path.unlink()


def _prune_runtime_test_packages(venv_root: Path) -> None:
    """Remove dependency test suites that are not needed by the installed runtime."""
    for site_packages in venv_root.glob("lib/python*/site-packages"):
        for name in ("test", "tests"):
            for path in sorted(site_packages.rglob(name), reverse=True):
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)


def _prune_runtime_bytecode(venv_root: Path) -> None:
    """Remove build-path-specific caches from the relocatable runtime."""
    for cache in sorted(venv_root.rglob("__pycache__"), reverse=True):
        if cache.is_dir() and not cache.is_symlink():
            shutil.rmtree(cache)
    for bytecode in venv_root.rglob("*.py[co]"):
        if bytecode.is_file() or bytecode.is_symlink():
            bytecode.unlink()


def _payload_license_scope(project: Path, application: Path) -> tuple[dict, list[dict]]:
    """Map only installed originals; source-only tooling stays in the source map."""
    source_bytes = (project / "LICENSES/scope.json").read_bytes()
    scope = json.loads(source_bytes)
    scope["source_scope_sha256"] = sha256(source_bytes).hexdigest()
    scope["source_scope_reference"] = "LICENSES/scope.json at the AppImage manifest source_commit"
    scope["inventory"] = "Installed payload only; the source-project map also covers development tools/tests"
    scope["client_software"]["paths"] = [
        p for p in scope["client_software"]["paths"]
        if (application / "app" / Path(p).relative_to("src")).is_file()
    ]
    scope["integration_contributions"]["paths"] = [
        p for p in scope["integration_contributions"]["paths"]
        if p.startswith("integration/batocera/") and (application / p).is_file()
    ]
    scope["independent_tools_and_tests"]["paths"] = []
    if "paths" in scope.get("branding", {}):
        scope["branding"]["paths"] = [
            p for p in scope["branding"]["paths"] if (application / p).is_file()
        ]
    included = set(scope["client_software"]["paths"]) | set(scope["integration_contributions"]["paths"])
    with (project / "docs/LICENSE_COMPONENT_MAP.csv").open() as stream:
        rows = [row for row in csv.DictReader(stream) if row["path_or_group"] in included]
    return scope, rows


def _prune_runtime_source_records(venv_root: Path) -> None:
    """Drop pip's local build-source URLs from the copied production venv.

    PEP 610 records describe the installation source, not runtime resources or
    package identity. Local file URLs expose build-host paths. Keep public
    source records and package versions, metadata and license notices intact.
    """
    for direct_url in venv_root.glob("lib/python*/site-packages/*.dist-info/direct_url.json"):
        if direct_url.is_symlink() or direct_url.parent.is_symlink():
            raise StagingError("Refusing symlinked PEP 610 build metadata")
        try:
            metadata = json.loads(direct_url.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise StagingError("Unreadable PEP 610 build metadata; values omitted") from error
        url = metadata.get("url") if isinstance(metadata, dict) else None
        if not isinstance(url, str):
            raise StagingError("Invalid PEP 610 build metadata; values omitted")
        if url.partition(":")[0].casefold() != "file":
            continue
        record = direct_url.parent / "RECORD"
        if record.is_symlink():
            raise StagingError("Refusing symlinked Python package RECORD")
        if record.is_file():
            with record.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.reader(stream))
            relative = f"{direct_url.parent.name}/direct_url.json"
            kept = [row for row in rows if not row or row[0] != relative]
            if kept != rows:
                with record.open("w", encoding="utf-8", newline="") as stream:
                    csv.writer(stream).writerows(kept)
        direct_url.unlink()


def _manifest(stage_root: Path, pins: dict[str, str]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    manifest_path = stage_root / "share" / "embercade" / "stage-manifest.json"
    for path in sorted(stage_root.rglob("*")):
        if path == manifest_path:
            continue
        if path.name.casefold() in {"screenscraper.conf", "screenscraper-user.conf", "screenscraper-build.conf", "screenscraperauthorization.h", "retroachievements-build.conf", "retroachievements-user.conf"} or path.name == "secrets":
            raise StagingError("Local account credentials must never enter a payload")
        if path.name == "es_settings.cfg" and path.is_file() and not path.is_symlink():
            if b"ScreenScraperPass" in path.read_bytes() or b"ScreenScraperUser" in path.read_bytes():
                raise StagingError("Personal ScreenScraper account must never enter a payload")
        relative = path.relative_to(stage_root).as_posix()
        if path.is_symlink():
            entries.append({"path": relative, "type": "symlink", "target": os.readlink(path)})
        elif path.is_dir():
            continue
        else:
            entries.append(
                {
                    "path": relative,
                    "type": "file",
                    "size": path.stat().st_size,
                    "sha256": _file_digest(path),
                }
            )
    return {
        "format": 1,
        "embercade_version": __version__,
        "product_label": FRONTEND_PRODUCT_LABEL,
        "pins": pins,
        "entries": entries,
    }


def build_stage(
    *,
    project_root: Path,
    reference_root: Path,
    stage_root: Path,
    development_without_screenscraper: bool = False,
) -> Path:
    expected_stage = project_root / ".work" / "stage"
    if stage_root.absolute() != expected_stage.absolute() or stage_root.is_symlink():
        raise StagingError(f"Refusing unexpected stage root: {stage_root}")

    upstream = tomllib.loads((project_root / "upstream.lock").read_text(encoding="utf-8"))[
        "upstream"
    ]
    batocera_pin = str(upstream["batocera.linux"])
    es_pin = str(upstream["batocera-emulationstation"])
    runtime_root = project_root / ".work" / "runtime"
    ui_root = project_root / ".work" / "ui"
    catalog_root = project_root / ".work" / "system-catalog" / "output"
    if not (catalog_root / "batocera-commit.txt").is_file():
        raise StagingError("Complete pinned system catalog is not prepared")
    if (catalog_root / "batocera-commit.txt").read_text().strip() != batocera_pin:
        raise StagingError("Complete system catalog does not match upstream.lock")
    from embercade.system_coverage import structure_inputs_digest
    proof_path = project_root / ".work/reports/system-structure.json"
    if not proof_path.is_file():
        raise StagingError("Run the complete system structural integration test before staging")
    structure = json.loads(proof_path.read_text())
    if structure.get("source_digest") != structure_inputs_digest(project_root):
        raise StagingError("System structural evidence is stale; rerun integration tests")
    reference_bundle = reference_root / "embercade-reference"
    frontend_libraries = project_root / ".work" / "frontend-libs"
    shader_root = project_root / ".work" / "shader-mappings"
    decoration_root = project_root / ".work" / "decorations"
    decoration_lock_path = project_root / "runtime/decorations.lock"
    decoration_pin = tomllib.loads(decoration_lock_path.read_text())["retrobat"]["commit"]
    shader_catalog = project_root / "resources" / "shaders" / "catalog.toml"
    shader_lock_path = project_root / "runtime" / "shaders.lock"
    shader_lock = tomllib.loads(shader_lock_path.read_text(encoding="utf-8"))
    shader_pin = str(shader_lock["slang"]["commit"])

    runtime_info = runtime_root / "runtime-info.txt"
    frontend = ui_root / "es-source" / "emulationstation"
    source_identity = ui_root / "es-source" / ".embercade-source-commit"
    required = (
        project_root / "integration" / "batocera" / "adapter.py",
        runtime_info,
        runtime_root / "venv" / "bin" / "python",
        frontend,
        source_identity,
        frontend_libraries / "lib" / "libfreeimage.so.3",
        frontend_libraries / "lib" / "libSDL2_mixer-2.0.so.0",
        frontend_libraries / "licenses" / "freeimage" / "NOTICE.txt",
        frontend_libraries / "licenses" / "sdl2_mixer" / "NOTICE.txt",
        runtime_root / "src" / "COPYING",
        ui_root / "es-source" / "LICENSE.md",
        reference_bundle
        / "usr-share-emulationstation"
        / "themes"
        / "es-theme-carbon"
        / "readme.txt",
        shader_root / "embercade-metadata" / "provider.json",
        decoration_root / "embercade-decorations.lock",
        shader_catalog,
        shader_lock_path,
    )
    for path in required:
        if not path.exists():
            raise StagingError(f"Missing prepared pinned prerequisite: {path}")
    runtime_text = runtime_info.read_text(encoding="utf-8")
    if f"batocera-commit={batocera_pin}" not in runtime_text:
        raise StagingError("Prepared runtime does not match upstream.lock")
    if not source_identity.read_text(encoding="utf-8").startswith(es_pin):
        raise StagingError("Prepared frontend does not match upstream.lock")
    if (decoration_root / "embercade-decorations.lock").read_bytes() != decoration_lock_path.read_bytes():
        raise StagingError("Prepared decorations do not match runtime/decorations.lock")
    if (shader_root / "embercade-metadata/catalog.toml").read_bytes() != shader_catalog.read_bytes():
        raise StagingError("Prepared host shader mappings are stale")
    try:
        load_catalog(shader_catalog)
        validate_collection(decoration_root)
    except (ShaderResourceError, DecorationResourceError) as error:
        raise StagingError(str(error)) from error

    lock = tomllib.loads(
        (project_root / "resources" / "resource-bundle.lock").read_text(encoding="utf-8")
    )["bundle"]
    bundle_inputs = {
        "es_systems": reference_bundle / "usr-share-emulationstation" / "es_systems.cfg",
        "es_features": reference_bundle / "usr-share-emulationstation" / "es_features.cfg",
        "es_savestates": reference_bundle
        / "usr-share-emulationstation"
        / "es_savestates.cfg",
        "carbon_theme": reference_bundle
        / "usr-share-emulationstation"
        / "themes"
        / "es-theme-carbon",
    }
    for name, path in bundle_inputs.items():
        actual = _file_digest(path) if path.is_file() else _tree_digest(path)
        if actual != lock[name]:
            raise StagingError(f"Pinned resource bundle mismatch for {name}: {path}")

    from embercade.frontend_build import verify_frontend, INFO_NAME
    verify_frontend(frontend, ui_root / INFO_NAME, development=development_without_screenscraper)

    if stage_root.exists():
        shutil.rmtree(stage_root)
    application = stage_root / "share" / "embercade"
    runtime_destination = application / "runtime"
    resources = application / "resources"
    frontend_root = application / "frontend"
    library_root = application / "lib"

    _copy_tree(runtime_root / "venv", runtime_destination / "venv")
    _prune_runtime_test_packages(runtime_destination / "venv")
    _prune_runtime_bytecode(runtime_destination / "venv")
    _prune_runtime_source_records(runtime_destination / "venv")
    _prune_runtime_bin(runtime_destination / "venv" / "bin")
    _copy_tree(runtime_root / "share", runtime_destination / "share")
    shutil.copy2(runtime_info, runtime_destination / "runtime-info.txt")
    _copy_tree(
        project_root / "src" / "embercade",
        application / "app" / "embercade",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "transfer_payload.py", "appimage.py"),
    )
    _copy_tree(project_root / "integration" / "batocera", application / "integration" / "batocera",
               ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("defaults", "libretro", "policy", "runtime"):
        _copy_tree(project_root / "resources" / name, resources / name)
    shutil.copy2(project_root / "resources" / "resource-bundle.lock", resources)

    branding = resources / "branding"
    for name in ("icon", "splash", "steam"):
        (branding / name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        project_root / "resources" / "branding" / "README.md",
        branding / "README.md",
    )
    shutil.copy2(
        project_root / "resources" / "branding" / "icon" / "embercade-512.png",
        branding / "icon" / "embercade-512.png",
    )
    for name in ("embercade-128.png", "embercade-256.png"):
        shutil.copy2(
            project_root / "resources" / "branding" / "icon" / name,
            branding / "icon" / name,
        )
    shutil.copy2(
        project_root / "resources" / "branding" / "splash" / "embercade-splash-3840x2160.jpg",
        branding / "splash" / "embercade-splash-3840x2160.jpg",
    )
    shutil.copy2(
        project_root / "resources" / "branding" / "steam" / "embercade-grid-900x1800.jpg",
        branding / "steam" / "embercade-grid-900x1800.jpg",
    )
    (branding / "steam" / "embercade-hero.jpg").symlink_to(
        "../splash/embercade-splash-3840x2160.jpg"
    )

    frontend_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(frontend, frontend_root / "emulationstation")
    shutil.copy2(ui_root / INFO_NAME, frontend_root / INFO_NAME)
    (frontend_root / "emulationstation").chmod(0o755)
    (frontend_root / INFO_NAME).chmod(0o644)
    _copy_tree(ui_root / "es-source" / "resources", resources / "emulationstation" / "resources")
    # The build workspace is private; exported nonsecret resources must remain
    # readable in an all-root SquashFS image on another user's machine.
    public_resources = resources / "emulationstation" / "resources"
    for path in (public_resources, *public_resources.rglob("*")):
        if not path.is_symlink():
            executable = path.is_dir() or bool(path.stat().st_mode & 0o111)
            path.chmod(0o755 if executable else 0o644)
    (resources / "emulationstation" / "themes").mkdir(parents=True, exist_ok=True)
    _copy_tree(bundle_inputs["carbon_theme"], resources / "emulationstation" / "themes" / "es-theme-carbon")
    _copy_tree(project_root / "resources/retroarch", resources / "retroarch")
    _copy_tree(shader_root, resources / "batocera" / "shaders")
    shutil.copy2(shader_catalog, resources / "batocera" / "shaders" / "embercade-metadata" / "catalog.toml")
    _copy_tree(decoration_root, resources / "batocera" / "datainit" / "decorations")

    # ES automatically merges es_systems_*.cfg: audit-only metadata must not
    # match that glob and override the actively customized launch commands.
    shutil.copy2(catalog_root / "es_systems.cfg", resources / "emulationstation" / "systems-catalog.xml")
    shutil.copy2(catalog_root / "bios-requirements.json", resources / "emulationstation" / "bios-requirements.json")
    # The portable proof contains no build paths or synthetic content; every
    # host still verifies its actual core ABI/dependencies before PREPARED.
    portable_structure = {system: {key: value for key, value in proof.items() if key != "error"}
                          for system, proof in structure["systems"].items()}
    (resources / "emulationstation" / "system-structure.json").write_text(
        json.dumps(portable_structure, indent=2) + "\n")
    shutil.copy2(catalog_root / "es_systems.cfg", resources / "emulationstation" / "es_systems.cfg")
    shutil.copy2(catalog_root / "es_features.cfg", resources / "emulationstation" / "es_features.cfg")
    merge_feature_overlay(
        resources / "emulationstation" / "es_features.cfg",
        project_root / "resources" / "ui" / "azahar-language.es_features.xml",
    )
    customize_production_systems(
        resources / "emulationstation" / "es_systems.cfg",
        systems=SUPPORTED_LAUNCH_SYSTEMS,
        provider_defaults=load_system_provider_defaults(
            project_root / "resources" / "defaults" / "batocera.conf"
        ),
    )
    _filter_desktop_features(resources / "emulationstation" / "es_features.cfg")

    pinned_input = (
        runtime_root
        / "src/package/batocera/emulationstation/batocera-emulationstation/controllers/es_input.cfg"
    )
    shutil.copy2(pinned_input, resources / "emulationstation" / "es_input.cfg")
    shutil.copy2(
        bundle_inputs["es_savestates"],
        resources / "emulationstation" / "es_savestates.cfg",
    )

    locale_source = ui_root / "es-source" / "locale" / "lang"
    for language in ("de", "en_GB"):
        source = locale_source / language / "LC_MESSAGES" / "emulationstation2.po"
        destination = (
            resources
            / "emulationstation"
            / "locale"
            / language
            / "LC_MESSAGES"
            / "emulationstation2.mo"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["msgfmt", str(source), "-o", str(destination)], check=True)

    _copy_tree(frontend_libraries / "lib", library_root)
    _copy_tree(
        frontend_libraries / "licenses",
        application / "licenses",
    )
    _copy_tree(
        shader_root / "embercade-metadata",
        application / "licenses" / "shaders",
    )
    decoration_notices = application / "licenses/retrobat-decorations"
    decoration_notices.mkdir(parents=True)
    for name in ("README.md", "embercade-collection.json", "embercade-decorations.lock"):
        shutil.copy2(decoration_root / name, decoration_notices / name)
    shutil.copy2(project_root / "resources/decorations/NOTICE.txt", decoration_notices / "NOTICE.txt")
    shutil.copy2(project_root / "LICENSES/prepared/CC-BY-NC-SA-4.0.txt", decoration_notices / "CC-BY-NC-SA-4.0.txt")
    for source, destination in (
        (
            runtime_root / "src" / "COPYING",
            application / "licenses" / "batocera" / "COPYING",
        ),
        (
            ui_root / "es-source" / "LICENSE.md",
            application / "licenses" / "emulationstation" / "LICENSE.md",
        ),
        (
            bundle_inputs["carbon_theme"] / "readme.txt",
            application / "licenses" / "carbon-theme" / "readme.txt",
        ),
    ):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    # Preserve a small source-shaped legal tree alongside the original component
    # notices. This does not replace the complete corresponding-source release.
    legal = application / "licenses" / "embercade"
    _copy_tree(project_root / "LICENSES", legal / "LICENSES")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(project_root / name, legal / name)
    (legal / "docs").mkdir()
    for name in ("LICENSING_1_0.md", "BATOCERA_COMPONENT_LICENSES.md", "SOURCE_ACCESS.md",
                 "LICENSE_COMPONENT_MAP.csv", "ADAPTER_SEPARATION.md", "BRANDING_ORIGIN.md",
                 "THIRD_PARTY_DELIVERY.md", "RETROACHIEVEMENTS_USER_KEYS.md"):
        shutil.copy2(project_root / "docs" / name, legal / "docs" / name)
    (legal / "compliance").mkdir()
    for name in ("README.md", "REBUILDING.md", "sources.lock.json", "notices.lock.json"):
        shutil.copy2(project_root / "compliance" / name, legal / "compliance" / name)
    # A source allowlist is not an installed-file inventory. Keep its immutable
    # identity, but do not ship source-only development launchers as payload rows.
    scope, rows = _payload_license_scope(project_root, application)
    (legal / "LICENSES/scope.json").write_text(json.dumps(scope, indent=2) + "\n")
    with (legal / "docs/LICENSE_COMPONENT_MAP.csv").open("w", newline="") as stream:
        fields = ("path_or_group", "kind", "review_status", "license_treatment",
                  "evidence_or_boundary", "project_grant_activated", "inventory_scope")
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    _validate_frontend_runtime(frontend_root / "emulationstation", library_root)

    launcher = runtime_destination / "venv" / "bin" / "batocera-launch"
    _write_executable(
        launcher,
        "#!/bin/sh\n"
        "runtime_bin=$(CDPATH= cd -- \"$(dirname -- \"$0\")\" && pwd -P)\n"
        "exec \"$runtime_bin/python\" -B -m batocera_launch.cli.main \"$@\"\n",
    )
    pyvenv = runtime_destination / "venv" / "pyvenv.cfg"
    pyvenv.write_text(
        "home = /usr/bin\ninclude-system-site-packages = false\n"
        "version = 3.14.7\nexecutable = /usr/bin/python3.14\n",
        encoding="utf-8",
    )

    wrapper = (
        "#!/bin/sh\n"
        "set -eu\n"
        "self=$(readlink -f -- \"$0\")\n"
        "prefix=$(CDPATH= cd -- \"$(dirname -- \"$self\")/..\" && pwd -P)\n"
        "application=$prefix/share/embercade\n"
        "export EMBERCADE_PREFIX=$prefix\n"
        "export EMBERCADE_PROJECT_ROOT=$application\n"
        "export EMBERCADE_RUNTIME_ROOT=$application/runtime\n"
        "export PYTHONPATH=$application/app\n"
        "export PYTHONDONTWRITEBYTECODE=1\n"
        "exec \"$application/runtime/venv/bin/python\" -B -m embercade \"$@\"\n"
    )
    _write_executable(stage_root / "bin" / "embercade", wrapper)
    provider_wrapper = wrapper.replace("-m embercade \"$@\"", "-m embercade.provider_runner \"$@\"")
    _write_executable(stage_root / "bin" / "embercade-provider-runner", provider_wrapper)

    desktop_root = stage_root / "share" / "applications"
    desktop_root.mkdir(parents=True, exist_ok=True)
    desktop_template = project_root / "packaging" / "linux" / "embercade.desktop"
    (desktop_root / "embercade.desktop").write_text(
        render_desktop_entry(desktop_template.read_text(encoding="utf-8")), encoding="utf-8"
    )

    pins = {
        "batocera": batocera_pin,
        "emulationstation": es_pin,
        "slang_shaders": shader_pin,
        "shader_provider": "host:libretro-shaders-slang (slang_shaders pin is historical reference only)",
        "retrobat_decorations": decoration_pin,
        "architecture": str(upstream["architecture"]),
    }
    manifest_path = application / "stage-manifest.json"
    manifest_path.write_text(
        json.dumps(_manifest(stage_root, pins), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m embercade.staging")
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--reference-root", required=True, type=Path)
    parser.add_argument("--stage-root", required=True, type=Path)
    parser.add_argument("--development-without-screenscraper", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = build_stage(
            project_root=args.project_root.absolute(),
            reference_root=args.reference_root.absolute(),
            stage_root=args.stage_root.absolute(),
            development_without_screenscraper=args.development_without_screenscraper,
        )
    except (OSError, StagingError, subprocess.CalledProcessError, ValueError) as error:
        parser.error(str(error))
    kind = "development (without ScreenScraper authorization)" if args.development_without_screenscraper else "production"
    print(f"Prepared {kind} stage: {args.stage_root.absolute()}")
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

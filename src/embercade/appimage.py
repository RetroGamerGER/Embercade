"""Private, offline-by-default AppImage packaging of an unchanged Production Stage.

This is build tooling, not a second runtime, installer or provider backend.
Compatible host CPython 3.14 and the existing host desktop/library contract
remain intentional requirements of this supported-host image.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import tomllib
import urllib.request

from embercade.elf_runtime import FRONTEND_BUNDLED_SONAMES, FRONTEND_HOST_SONAMES
from embercade.frontend_build import verify_frontend, INFO_NAME
from embercade.installer import APP_ICON_RELATIVE, InstallationError, verify_payload
from embercade.transfer_payload import FORBIDDEN_RUNTIME_MARKERS, TransferPayloadError, audit_stage_payload
from embercade.version import FRONTEND_PRODUCT_LABEL, FRONTEND_PRODUCT_VERSION, __version__


APPDIR_MANIFEST = "embercade-appimage-manifest.json"
EXCLUDED_STATE = (
    "ROMs", "BIOS/firmware/keys", "config/local-secret-files/personal-credentials", "saves/states",
    "screenshots/recordings", "downloaded/user themes", "scraped media",
    "managed Libretro cores", "managed emulator providers/AppImages",
    "PPSSPP user resources", "Xemu working system files", "Steam user state/artwork",
    "personal paths", "host GPU drivers/Mesa/Vulkan ICDs/libdrm",
)
EXTERNAL_DEPENDENCIES = {
    "python": "Compatible host CPython 3.14 interpreter/stdlib; image supplies pinned venv packages",
    "gui": "Host Python GTK3/PyGObject for the existing first-run wizard; Pycairo for standalone decorations",
    "isolation": "Compatible Bubblewrap with the existing overlay namespace support",
    "input": "Compatible host python-evdev ABI, SDL2, permitted input/Wii HID nodes",
    "graphics": "Host OpenGL/Vulkan/Mesa/ICDs/DRI, Wayland/X11/Gamescope",
    "frontend_video": "Host libVLC with distro-matched vlc-plugin-ffmpeg (avcodec/swscale) and vmem output",
    "audio": "Host ALSA and PipeWire/PulseAudio compatibility socket",
    "shaders": "Optional host libretro-shaders-slang package with presets, includes, textures and LUTs; effects remain off by default",
    "providers": "User-supplied emulators, managed cores, Xenia/shadPS4; existing resolvers",
    "external_provider_launch": "Host systemd user manager and compatible provider FUSE support",
    "frontend_direct_sonames": sorted(FRONTEND_HOST_SONAMES),
    "scope": "Supported-host image; not a generic distribution-independent Linux runtime",
}


class AppImageError(RuntimeError):
    """Packaging inputs or a produced artifact cannot be verified."""


@dataclass(frozen=True, slots=True)
class AppImageResult:
    image: Path
    manifest: Path
    checksum: Path
    appdir: Path
    image_sha256: str


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _contained_path(path: Path, project_root: Path) -> Path:
    resolved = path.expanduser().absolute()
    if not resolved.resolve().is_relative_to(project_root.resolve()) or resolved.is_symlink():
        raise AppImageError("Packaging writes must stay in real paths inside this repository")
    return resolved


def load_build_lock(project_root: Path) -> dict[str, Any]:
    lock = tomllib.loads((project_root / "packaging/appimage/build.lock").read_text())
    if lock.get("format") != 1 or lock.get("architecture") != "x86_64":
        raise AppImageError("Unsupported AppImage build lock")
    for name in ("appimagetool", "runtime"):
        item = lock.get(name, {})
        if not re.fullmatch(r"[a-f0-9]{64}", item.get("sha256", "")):
            raise AppImageError(f"Missing locked {name} SHA-256")
        filename = item.get("filename", "")
        if not filename or Path(filename).name != filename:
            raise AppImageError(f"Unsafe locked {name} filename")
        if not item.get("url", "").startswith("https://github.com/AppImage/"):
            raise AppImageError(f"{name} must use its locked official AppImage source")
    return lock


def verify_tools(project_root: Path, lock: Mapping[str, Any]) -> dict[str, Path]:
    tool_root = project_root / ".work/tools/appimage"
    result = {}
    for name in ("appimagetool", "runtime"):
        path = tool_root / lock[name]["filename"]
        if path.is_symlink() or not path.is_file():
            raise AppImageError("Pinned AppImage build tools are missing; run scripts/appimage-tools-prepare once")
        if file_sha256(path) != lock[name]["sha256"]:
            raise AppImageError(f"Locked {name} SHA-256 mismatch; refusing to execute it")
        result[name] = path
    return result


def prepare_tools(project_root: Path, lock: Mapping[str, Any]) -> dict[str, Path]:
    """Explicit network preparation; normal packaging never calls this implicitly."""
    tool_root = _contained_path(project_root / ".work/tools/appimage", project_root)
    tool_root.mkdir(parents=True, exist_ok=True)
    for name in ("appimagetool", "runtime"):
        path = tool_root / lock[name]["filename"]
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file() or file_sha256(path) != lock[name]["sha256"]:
                raise AppImageError(f"Existing {name} does not match the lock; nothing overwritten")
            continue
        descriptor, temporary = tempfile.mkstemp(prefix=f".{name}-", dir=tool_root)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as target:
                with urllib.request.urlopen(lock[name]["url"], timeout=60) as source:
                    shutil.copyfileobj(source, target)
            if file_sha256(temporary_path) != lock[name]["sha256"]:
                raise AppImageError(f"Downloaded {name} does not match the locked SHA-256")
            temporary_path.chmod(0o755)
            temporary_path.rename(path)
        finally:
            temporary_path.unlink(missing_ok=True)
    return verify_tools(project_root, lock)


def _entries(root: Path, *, excluded: str | None = None) -> list[dict[str, Any]]:
    entries = []
    for base, directories, files in os.walk(root, followlinks=False):
        base_path = Path(base)
        names = files + [name for name in directories if (base_path / name).is_symlink()]
        for name in names:
            path = base_path / name
            relative = path.relative_to(root).as_posix()
            if relative == excluded:
                continue
            if path.is_symlink():
                entries.append({"path": relative, "type": "symlink", "target": os.readlink(path)})
            elif path.is_file():
                entries.append({"path": relative, "type": "file", "size": path.stat().st_size,
                                "mode": stat.S_IMODE(path.stat().st_mode), "sha256": file_sha256(path)})
            else:
                raise AppImageError("AppDir contains an unsupported special file")
    return sorted(entries, key=lambda entry: entry["path"])


def _runtime_notices(project_root: Path, lock: Mapping[str, Any]) -> tuple[Path, dict[str, Any]]:
    root = project_root / "packaging/appimage/licenses"
    index = json.loads((root / "index.json").read_text())
    if index.get("format") != 1 or index.get("runtime", {}).get("sha256") != lock["runtime"]["sha256"]:
        raise AppImageError("Runtime notice index does not match the locked runtime")
    expected = {"index.json"}
    for item in index.get("notices", []):
        relative = item.get("path", "")
        path = root / relative
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise AppImageError("Unsafe runtime notice path")
        if path.is_symlink() or not path.is_file() or file_sha256(path) != item.get("sha256"):
            raise AppImageError("Runtime dependency notice SHA-256 mismatch")
        expected.add(relative)
    if len(expected) < 2 or {entry["path"] for entry in _entries(root)} != expected:
        raise AppImageError("Runtime dependency notice file set is incomplete or unexpected")
    return root, index


def _desktop_text() -> str:
    return (
        f"[Desktop Entry]\nType=Application\nName={FRONTEND_PRODUCT_LABEL}\nExec=AppRun\n"
        "Icon=embercade\nCategories=Game;Emulator;\nTerminal=false\n"
        f"X-AppImage-Version={FRONTEND_PRODUCT_VERSION}\n"
        f"X-Embercade-Product={FRONTEND_PRODUCT_LABEL}\n"
    )


def _audit_bundle_boundary(stage_root: Path, *, build_root: Path | None = None) -> None:
    audit_stage_payload(stage_root, build_root=build_root)
    _scan_private_paths(stage_root, build_root=build_root)
    themes = stage_root / "share/embercade/resources/emulationstation/themes"
    carbon = themes / "es-theme-carbon"
    if (themes.is_symlink() or not themes.is_dir()
            or {path.name for path in themes.iterdir()} != {"es-theme-carbon"}
            or carbon.is_symlink() or not carbon.is_dir()):
        raise AppImageError("The AppImage may bundle only the standard es-theme-carbon theme; user themes stay external")
    # Graphics dispatch and device-specific providers must continue to resolve
    # from the compatible host, even if an accidental extra Stage file has a
    # valid Stage manifest entry.
    gpu_libraries = ("libgl.", "libglx.", "libopengl.", "libgldispatch.", "libegl.",
                     "libglapi.", "libgallium", "libvklayer_", "libvulkan.",
                     "libvulkan_", "libdrm", "libgbm.", "libnvidia", "amdvlk")
    for path in stage_root.rglob("*"):
        relative = path.relative_to(stage_root)
        name = path.name.casefold()
        if name.startswith(gpu_libraries) or name.endswith("_dri.so") or (
            "vulkan" in relative.parts and "icd.d" in relative.parts
        ):
            raise AppImageError("Host graphics drivers/dispatch/ICDs must never enter the AppImage")


def _scan_private_paths(root: Path, *, build_root: Path | None = None) -> None:
    """Audit every file, including ELF debug data, without echoing matched values."""
    # Do not limit privacy checks to the two reference-host account names.
    markers = [*FORBIDDEN_RUNTIME_MARKERS, b"/home/", b"/Users/"]
    if build_root is not None:
        markers.append(str(build_root.absolute()).encode())
    # These exact pinned-dependency comments contain generic documentation
    # examples, not build/user paths. Never exempt an entire source file.
    examples = {
        "site-packages/aiohttp/web_urldispatcher.py": b"# e.g. /static/../../../../home/user/webapp/static/",
        "site-packages/pip/_internal/utils/urls.py": b'# On Windows, urlsplit parses the path as something like "/C:/Users/foo".',
    }
    overlap = max(map(len, markers)) - 1
    for path in root.rglob("*"):
        if path.is_symlink():
            if any(marker in os.readlink(path).encode() for marker in markers):
                raise AppImageError("AppImage contains a private/development path in a symlink")
            continue
        if path.is_dir():
            continue
        if any(marker in path.relative_to(root).as_posix().encode() for marker in markers):
            raise AppImageError("AppImage contains a private/development path in a filename")
        with path.open("rb") as stream:
            previous = b""
            while chunk := stream.read(1024 * 1024):
                data = previous + chunk
                audited = data
                for suffix, example in examples.items():
                    if path.as_posix().endswith("/" + suffix):
                        audited = audited.replace(example, b"<generic upstream comment>")
                if any(marker in audited for marker in markers):
                    raise AppImageError("AppImage contains a private/development path; matched value omitted")
                previous = data[-overlap:]


def prepare_appdir(
    *, project_root: Path, stage_root: Path, appdir: Path,
    source_commit: str, source_date_epoch: int, source_tree_dirty: bool = False,
    development_without_screenscraper: bool = False,
    public_candidate: bool = False,
) -> dict[str, Any]:
    """Wrap the exact audited Stage; neither generate nor change runtime behavior."""
    if not re.fullmatch(r"[a-f0-9]{40}", source_commit) or source_date_epoch < 0:
        raise AppImageError("A Git source revision and nonnegative SOURCE_DATE_EPOCH are required")
    if public_candidate and (source_tree_dirty or development_without_screenscraper):
        raise AppImageError("Public preparation requires clean production sources and application authorization")
    destination = _contained_path(appdir, project_root)
    stage_path, destination_path = stage_root.resolve(), destination.resolve()
    if (destination.exists() or stage_path.is_relative_to(destination_path)
            or destination_path.is_relative_to(stage_path)):
        raise AppImageError("AppDir destination must be a fresh path outside the Stage")
    _audit_bundle_boundary(stage_root, build_root=project_root)
    verification = verify_payload(stage_root)
    authorization = verify_frontend(stage_root / "share/embercade/frontend/emulationstation",
        stage_root / "share/embercade/frontend" / INFO_NAME, development=development_without_screenscraper)
    if verification.product_label != FRONTEND_PRODUCT_LABEL:
        raise AppImageError("Production Stage product label is stale; rebuild the Stage first")
    lock = load_build_lock(project_root)
    notice_root, notices = _runtime_notices(project_root, lock)
    template = project_root / "packaging/appimage"
    icon = stage_root / APP_ICON_RELATIVE
    if icon.is_symlink() or not icon.is_file():
        raise AppImageError("Production branding icon is missing")
    destination.mkdir(parents=True)
    destination.chmod(0o755)
    shutil.copytree(stage_root, destination / "usr", symlinks=True)
    shutil.copy2(template / "AppRun", destination / "AppRun")
    (destination / "AppRun").chmod(0o755)
    (destination / "embercade.desktop").write_text(_desktop_text())
    (destination / "embercade.desktop").chmod(0o644)
    shutil.copy2(icon, destination / "embercade.png")
    (destination / "embercade.png").chmod(0o644)
    (destination / ".DirIcon").symlink_to("embercade.png")
    shutil.copy2(template / "CREDITS.txt", destination / "CREDITS.txt")
    (destination / "CREDITS.txt").chmod(0o644)
    shutil.copytree(notice_root, destination / "packaging-notices")
    for path in (destination / "packaging-notices", *(destination / "packaging-notices").rglob("*")):
        path.chmod(0o755 if path.is_dir() else 0o644)
    _audit_bundle_boundary(destination / "usr", build_root=project_root)
    if verify_payload(destination / "usr").manifest_sha256 != verification.manifest_sha256:
        raise AppImageError("AppDir altered the golden Production Stage")
    manifest = {
        "format": 1, "distribution": "PUBLIC" if public_candidate else "PRIVATE",
        "public_release": "PREPARED_NOT_PUBLISHED" if public_candidate else "BLOCKED",
        "architecture": "x86_64", "product_label": FRONTEND_PRODUCT_LABEL,
        "product_version": FRONTEND_PRODUCT_VERSION, "package_version": __version__,
        "source_commit": source_commit, "source_date_epoch": source_date_epoch,
        "source_tree_dirty": source_tree_dirty,
        "frontend_authorization": authorization,
        "build_kind": "development" if development_without_screenscraper else "production-candidate",
        "stage_manifest_sha256": verification.manifest_sha256,
        "upstream_pins": dict(verification.pins), "build_tools": lock,
        "bundled_frontend_sonames": sorted(FRONTEND_BUNDLED_SONAMES),
        "bundled_shared_objects": [entry["path"] for entry in _entries(destination / "usr")
                                   if ".so" in Path(entry["path"]).name],
        "external_dependencies": EXTERNAL_DEPENDENCIES,
        "excluded_user_state": EXCLUDED_STATE, "runtime_notices": notices,
        "file_manifest_excludes_self": APPDIR_MANIFEST,
        "included_files": _entries(destination),
    }
    (destination / APPDIR_MANIFEST).write_text(_json_text(manifest))
    (destination / APPDIR_MANIFEST).chmod(0o644)
    verify_appdir(destination, build_root=project_root)
    return manifest


def verify_appdir(appdir: Path, *, build_root: Path | None = None) -> dict[str, Any]:
    """Verify an extracted image/AppDir without executing it or reading user state."""
    root = appdir.absolute()
    manifest_path = root / APPDIR_MANIFEST
    if root.is_symlink() or manifest_path.is_symlink() or not manifest_path.is_file():
        raise AppImageError("AppDir packaging manifest is unavailable")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("format") != 1 or manifest.get("file_manifest_excludes_self") != APPDIR_MANIFEST:
        raise AppImageError("Unsupported AppDir manifest")
    publication = (manifest.get("distribution"), manifest.get("public_release"))
    if publication not in {("PRIVATE", "BLOCKED"), ("PUBLIC", "PREPARED_NOT_PUBLISHED")}:
        raise AppImageError("Unsupported publication metadata")
    if publication[0] == "PUBLIC" and (manifest.get("source_tree_dirty") or manifest.get("build_kind") != "production-candidate"):
        raise AppImageError("Public preparation requires a clean production candidate")
    if manifest.get("included_files") != _entries(root, excluded=APPDIR_MANIFEST):
        raise AppImageError("AppDir contents differ from the complete packaging manifest")
    _scan_private_paths(root, build_root=build_root)
    _audit_bundle_boundary(root / "usr", build_root=build_root)
    if verify_payload(root / "usr").manifest_sha256 != manifest.get("stage_manifest_sha256"):
        raise AppImageError("AppDir Stage manifest identity mismatch")
    if manifest.get("product_label") != FRONTEND_PRODUCT_LABEL or (root / "embercade.desktop").read_text() != _desktop_text():
        raise AppImageError("AppImage branding/desktop metadata disagrees with the central version")
    authorization = verify_frontend(root / "usr/share/embercade/frontend/emulationstation",
        root / "usr/share/embercade/frontend" / INFO_NAME, development=manifest.get("build_kind") == "development")
    if authorization != manifest.get("frontend_authorization"):
        raise AppImageError("Packaged frontend authorization identity disagrees with manifest")
    if publication[0] == "PUBLIC" and authorization.get("retroachievements_authorization") != "per-user-web-api":
        raise AppImageError("Public preparation requires per-user RetroAchievements keys")
    return manifest


def build_appimage(
    *, project_root: Path, stage_root: Path, output: Path,
    source_commit: str, source_date_epoch: int, source_tree_dirty: bool = False,
    development_without_screenscraper: bool = False,
    public_candidate: bool = False,
) -> AppImageResult:
    lock = load_build_lock(project_root)
    image = _contained_path(output, project_root)
    if image.suffix != ".AppImage" or "\n" in image.name or "\\" in image.name:
        raise AppImageError("Use a simple .AppImage output filename")
    report_path = image.with_suffix(".manifest.json")
    checksum = image.with_suffix(".AppImage.sha256")
    if any(path.resolve().is_relative_to(stage_root.resolve()) for path in (image, report_path, checksum)):
        raise AppImageError("AppImage outputs must stay outside the golden Production Stage")
    if report_path.is_symlink() or checksum.is_symlink():
        raise AppImageError("Refusing symlink metadata destinations")
    work_root = _contained_path(project_root / ".work", project_root)
    if work_root.resolve().is_relative_to(stage_root.resolve()):
        raise AppImageError("Packaging workspace must stay outside the golden Production Stage")
    tools = verify_tools(project_root, lock)  # Validate pins before any tool executes.
    work_root.mkdir(parents=True, exist_ok=True)
    build_root = Path(tempfile.mkdtemp(prefix="appimage-build-", dir=work_root))
    appdir = build_root / "Embercade.AppDir"
    manifest = prepare_appdir(project_root=project_root, stage_root=stage_root, appdir=appdir,
                              source_commit=source_commit, source_date_epoch=source_date_epoch,
                              source_tree_dirty=source_tree_dirty,
                              development_without_screenscraper=development_without_screenscraper,
                              public_candidate=public_candidate)
    environment = dict(os.environ)
    for name in ("APPIMAGE", "APPDIR", "LD_LIBRARY_PATH", "LD_PRELOAD"):
        environment.pop(name, None)
    environment.update({"ARCH": "x86_64", "VERSION": FRONTEND_PRODUCT_VERSION,
                        "SOURCE_DATE_EPOCH": str(source_date_epoch), "LC_ALL": "C", "TZ": "UTC"})
    extracted = subprocess.run([str(tools["appimagetool"]), "--appimage-extract"],
                               cwd=build_root, env=environment, umask=0o022,
                               capture_output=True, text=True, check=False)
    if extracted.returncode:
        raise AppImageError("Verified appimagetool extraction failed; no product image activated")
    prepared_image = build_root / image.name
    command = [str(build_root / "squashfs-root/AppRun"), "--no-appstream", "--comp", "zstd",
               "--runtime-file", str(tools["runtime"])]
    for option in ("-all-root", "-no-xattrs", "-processors", "1", "-all-time", str(source_date_epoch),
                   "-mkfs-time", str(source_date_epoch)):
        command += ["--mksquashfs-opt", option]
    command += [str(appdir), str(prepared_image)]
    # mksquashfs rejects SOURCE_DATE_EPOCH together with explicit timestamp
    # flags. All inode and filesystem times use the supplied epoch here,
    # rather than the environment's weaker "clamp newer files" behavior.
    tool_environment = {name: value for name, value in environment.items() if name != "SOURCE_DATE_EPOCH"}
    completed = subprocess.run(command, cwd=build_root, env=tool_environment, umask=0o022,
                               capture_output=True, text=True, check=False)
    log = completed.stdout + completed.stderr
    for source, replacement in ((str(build_root), "<build>"), (str(project_root), "<project>")):
        log = log.replace(source, replacement)
    (build_root / "build.log").write_text(log)
    if completed.returncode or not prepared_image.is_file():
        detail = "\n".join(log.splitlines()[-12:])
        raise AppImageError("AppImage packaging failed; retained build.log under .work:\n" + detail)
    # Verify actual SquashFS output, not only its source AppDir.
    extraction = build_root / "image-check"
    extraction.mkdir()
    result = subprocess.run([str(prepared_image), "--appimage-extract"], cwd=extraction,
                            env=environment, umask=0o022, capture_output=True, text=True, check=False)
    if result.returncode:
        raise AppImageError("Produced image could not be extracted for verification")
    verify_appdir(extraction / "squashfs-root", build_root=project_root)
    verify_appdir(appdir, build_root=project_root)
    digest = file_sha256(prepared_image)
    report = {**manifest, "appdir_manifest_sha256": file_sha256(appdir / APPDIR_MANIFEST),
              "image": {"filename": image.name, "sha256": digest, "size": prepared_image.stat().st_size},
              "included_files_with_manifest": _entries(appdir),
              "build_recipe": {"compression": "zstd", "all_root": True, "xattrs": False,
                               "processors": 1, "timestamps": source_date_epoch, "network": False}}
    image.parent.mkdir(parents=True, exist_ok=True)
    if image.is_symlink():
        raise AppImageError("Refusing to replace a symlink output image")
    prepared_image.chmod(0o755)
    prepared_image.replace(image)
    report_path.write_text(_json_text(report))
    report_path.chmod(0o644)
    checksum.write_text(f"{digest}  {image.name}\n")
    checksum.chmod(0o644)
    return AppImageResult(image, report_path, checksum, appdir, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m embercade.appimage")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prepare-tools", action="store_true", help="explicitly download SHA-256-pinned build tools")
    parser.add_argument("--tools-only", action="store_true")
    parser.add_argument("--audit-appdir", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--development-without-screenscraper", action="store_true")
    parser.add_argument("--public-candidate", action="store_true",
                        help="prepare a public-distribution candidate locally; never upload or publish")
    parser.add_argument("--source-date-epoch", type=int)
    args = parser.parse_args(argv)
    project_root = args.project_root.absolute()
    try:
        if args.audit_appdir:
            verify_appdir(args.audit_appdir, build_root=project_root)
            print("Extracted AppImage contents verified; Production Stage identity preserved.")
            return 0
        lock = load_build_lock(project_root)
        if args.prepare_tools:
            prepare_tools(project_root, lock)
        if args.tools_only:
            verify_tools(project_root, lock)
            print("Pinned AppImage build tools verified. Normal builds are offline.")
            return 0
        commit = args.source_commit or subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project_root, text=True).strip()
        epoch = args.source_date_epoch
        if epoch is None:
            epoch = int(subprocess.check_output(["git", "show", "-s", "--format=%ct", commit],
                                               cwd=project_root, text=True).strip())
        result = build_appimage(project_root=project_root,
                               stage_root=args.stage_root or project_root / ".work/stage",
                               output=args.output or project_root / "dist" / f"Embercade-{FRONTEND_PRODUCT_VERSION}{'-Development' if args.development_without_screenscraper else ''}-x86_64.AppImage",
                               source_commit=commit, source_date_epoch=epoch,
                               development_without_screenscraper=args.development_without_screenscraper,
                               public_candidate=args.public_candidate,
                               source_tree_dirty=bool(subprocess.check_output(
                                   ["git", "status", "--porcelain"], cwd=project_root, text=True).strip()))
    except (AppImageError, InstallationError, TransferPayloadError, OSError, ValueError,
            subprocess.CalledProcessError) as error:
        parser.error(str(error))
    label = "Private development AppImage (ScreenScraper authorization omitted)" if args.development_without_screenscraper else "Private AppImage"
    print(f"{label}: {result.image}")
    print(f"SHA-256: {result.image_sha256}")
    print(f"Verified manifest: {result.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

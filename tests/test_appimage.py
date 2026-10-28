from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import io
import json
import os
import shutil
import subprocess
import unittest

from embercade.appimage import (
    APPDIR_MANIFEST, AppImageError, build_appimage, file_sha256, load_build_lock,
    prepare_appdir, prepare_tools, verify_appdir, verify_tools,
)
from embercade.cores import LibretroCoreResolver
from embercade.executables import EmulatorProvider, ExecutableResolver, ProviderType
from embercade.installer import APP_ICON_RELATIVE, STAGE_MANIFEST_RELATIVE, verify_payload
from embercade.paths import EmbercadePaths
from embercade.production import ProductionLayout
from embercade.transfer_payload import TransferPayloadError
from embercade.version import FRONTEND_PRODUCT_LABEL, FRONTEND_PRODUCT_VERSION


REPOSITORY = Path(__file__).resolve().parents[1]


def _project(root: Path) -> Path:
    project = root / "Source with spaces"
    packaging = project / "packaging/appimage"
    packaging.mkdir(parents=True)
    for name in ("AppRun", "CREDITS.txt", "build.lock"):
        shutil.copy2(REPOSITORY / "packaging/appimage" / name, packaging / name)
    notices = packaging / "licenses"
    notices.mkdir()
    (notices / "LICENSE.txt").write_text("Test notice fixture; no actual runtime licensing claim.\n")
    lock = load_build_lock(project)
    (notices / "index.json").write_text(json.dumps({
        "format": 1, "runtime": lock["runtime"],
        "notices": [{"component": "fixture", "path": "LICENSE.txt",
                     "sha256": file_sha256(notices / "LICENSE.txt")}],
    }))
    return project


def _stage(project: Path, extra: dict[str, bytes] | None = None) -> Path:
    stage = project / ".work/stage"
    files = {
        "bin/embercade": (
            b"#!/bin/sh\nset -eu\nself=$(readlink -f -- \"$0\")\n"
            b"prefix=$(CDPATH= cd -- \"$(dirname -- \"$self\")/..\" && pwd -P)\n"
            b"export EMBERCADE_PREFIX=$prefix\n"
            b"printf 'prefix=%s\\nappdir=%s\\nhome=%s\\ncwd=%s\\n' \"$prefix\" \"${APPDIR:-}\" \"$HOME\" \"$PWD\"\n"
            b"printf 'arg=%s\\n' \"$@\"\n"
        ),
        "bin/embercade-provider-runner": b"#!/bin/sh\nexit 0\n",
        "share/embercade/frontend/emulationstation": b"fixture frontend EMBERCADE_SCREENSCRAPER_EMBEDDED_V1 EMBERCADE_RETROACHIEVEMENTS_USER_WEB_API_V1\n",
        "share/embercade/runtime/venv/bin/python": b"fixture python\n",
        "share/embercade/resources/defaults/batocera.conf": b"global.bezel=consoles\n",
        "share/embercade/resources/defaults/es_settings.cfg":
            b'<config><string name="ThemeSet" value="es-theme-carbon" /></config>\n',
        "share/embercade/resources/emulationstation/themes/es-theme-carbon/theme.xml":
            b"<theme>Generic Carbon fixture</theme>\n",
        "share/applications/embercade.desktop": b"[Desktop Entry]\nName=Embercade\nExec=embercade\nIcon=embercade\n",
        APP_ICON_RELATIVE.as_posix(): b"fixture generic branding icon\n",
    }
    files.update(extra or {})
    frontend=files["share/embercade/frontend/emulationstation"]
    files["share/embercade/frontend/frontend-build.json"] = json.dumps(dict(format=1, software="Embercade", authorization="embedded" if b"EMBERCADE_SCREENSCRAPER_EMBEDDED_V1" in frontend else "development-local", frontend_sha256=sha256(frontend).hexdigest(), retroachievements_authorization="per-user-web-api")).encode()
    entries = []
    for relative, data in files.items():
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o755 if relative.startswith("bin/") or path.name in {"emulationstation", "python"} else 0o644)
        entries.append({"path": relative, "type": "file", "size": len(data), "sha256": sha256(data).hexdigest()})
    (stage / STAGE_MANIFEST_RELATIVE).write_text(json.dumps({
        "format": 1, "embercade_version": "0.1.dev0", "product_label": FRONTEND_PRODUCT_LABEL,
        "pins": {"test": "pinned"}, "entries": sorted(entries, key=lambda entry: entry["path"]),
    }))
    return stage


def _prepare(project: Path, stage: Path, name: str = "AppDir with spaces") -> Path:
    appdir = project / ".work" / name
    prepare_appdir(project_root=project, stage_root=stage, appdir=appdir,
                   source_commit="a" * 40, source_date_epoch=1700000000)
    return appdir


class AppImageTests(unittest.TestCase):
    @unittest.skipUnless(
        (REPOSITORY / ".work/tools/appimage/appimagetool-1.9.1-x86_64.AppImage").is_file(),
        "Explicitly prepared pinned tools are required for tiny-image integration",
    )
    def test_real_tool_builds_extracts_and_reproduces_tiny_image_offline(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project)
            tools = verify_tools(REPOSITORY, load_build_lock(REPOSITORY))
            tool_root = project / ".work/tools/appimage"
            tool_root.mkdir(parents=True)
            for source in tools.values():
                shutil.copy2(source, tool_root / source.name)
            outputs = []
            for name, umask in (("first", 0o022), ("second", 0o077)):
                previous = os.umask(umask)
                try:
                    with patch("embercade.appimage.urllib.request.urlopen") as network:
                        result = build_appimage(project_root=project, stage_root=stage,
                                                output=project / "dist" / f"{name}.AppImage",
                                                source_commit="a" * 40, source_date_epoch=1700000000)
                        network.assert_not_called()
                finally:
                    os.umask(previous)
                outputs.append(result.image_sha256)
                report = json.loads(result.manifest.read_text())
                self.assertEqual(report["image"]["sha256"], file_sha256(result.image))
                self.assertEqual(report["stage_manifest_sha256"], verify_payload(stage).manifest_sha256)
            self.assertEqual(outputs[0], outputs[1])

    def test_appdir_preserves_exact_stage_and_records_full_boundary(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project)
            before = verify_payload(stage)
            appdir = _prepare(project, stage)
            manifest = verify_appdir(appdir, build_root=project)
            self.assertEqual(verify_payload(appdir / "usr"), before)
            self.assertEqual(verify_payload(stage), before)
            self.assertEqual(manifest["stage_manifest_sha256"], before.manifest_sha256)
            self.assertEqual(manifest["product_label"], "EMBERCADE 1.0")
            self.assertEqual(manifest["product_version"], FRONTEND_PRODUCT_VERSION)
            self.assertEqual(manifest["distribution"], "PRIVATE")
            self.assertEqual(manifest["public_release"], "BLOCKED")
            self.assertIn("CPython 3.14", manifest["external_dependencies"]["python"])
            self.assertIn("host GPU drivers/Mesa/Vulkan ICDs/libdrm", manifest["excluded_user_state"])
            self.assertEqual(manifest["bundled_frontend_sonames"], ["libSDL2_mixer-2.0.so.0", "libfreeimage.so.3"])
            paths = {entry["path"] for entry in manifest["included_files"]}
            self.assertIn("usr/bin/embercade-provider-runner", paths)
            self.assertIn("packaging-notices/LICENSE.txt", paths)
            self.assertNotIn(APPDIR_MANIFEST, paths)
            metadata = (appdir / "embercade.desktop").read_text()
            self.assertIn("X-AppImage-Version=1.0", metadata)
            self.assertIn(f"Name={FRONTEND_PRODUCT_LABEL}\n", metadata)
            self.assertIn("Exec=AppRun", metadata)
            self.assertNotIn(str(project), (appdir / APPDIR_MANIFEST).read_text())
            self.assertEqual(os.readlink(appdir / ".DirIcon"), "embercade.png")

    def test_production_rejects_unconfigured_frontend_and_development_must_be_explicit(self):
        with TemporaryDirectory() as directory:
            project=_project(Path(directory))
            stage=_stage(project,{"share/embercade/frontend/emulationstation":b"explicit development frontend EMBERCADE_RETROACHIEVEMENTS_USER_WEB_API_V1"})
            with self.assertRaisesRegex(ValueError,'Production packaging'):
                _prepare(project,stage)
            destination=project/'.work/Development.AppDir'
            manifest=prepare_appdir(project_root=project,stage_root=stage,appdir=destination,
                source_commit='a'*40,source_date_epoch=1700000000,development_without_screenscraper=True)
            self.assertEqual(manifest['build_kind'],'development')
            self.assertEqual(manifest['frontend_authorization']['authorization'],'development-local')
            self.assertEqual(verify_appdir(destination,build_root=project)['frontend_authorization'],manifest['frontend_authorization'])

    def test_public_candidate_records_preparation_without_publishing_or_changing_stage(self):
        with TemporaryDirectory() as directory:
            project = _project(Path(directory)); stage = _stage(project)
            before = verify_payload(stage)
            appdir = project/'.work/Public.AppDir'
            manifest = prepare_appdir(project_root=project, stage_root=stage, appdir=appdir,
                source_commit='a'*40, source_date_epoch=1700000000, public_candidate=True)
            self.assertEqual((manifest['distribution'],manifest['public_release']),
                             ('PUBLIC','PREPARED_NOT_PUBLISHED'))
            self.assertEqual(verify_appdir(appdir,build_root=project),json.loads(json.dumps(manifest)))
            self.assertEqual(verify_payload(stage),before)
            self.assertEqual(verify_payload(appdir/'usr'),before)
            manifest['public_release']='PUBLISHED'
            (appdir/APPDIR_MANIFEST).write_text(json.dumps(manifest))
            with self.assertRaisesRegex(AppImageError,'publication metadata'):
                verify_appdir(appdir,build_root=project)

    def test_public_candidate_refuses_dirty_or_development_inputs_before_writing(self):
        with TemporaryDirectory() as directory:
            project = _project(Path(directory)); stage = _stage(project)
            for option in ('source_tree_dirty','development_without_screenscraper'):
                destination=project/'.work'/option
                with self.subTest(option=option),self.assertRaisesRegex(AppImageError,'clean production'):
                    prepare_appdir(project_root=project,stage_root=stage,appdir=destination,
                        source_commit='a'*40,source_date_epoch=1700000000,public_candidate=True,**{option:True})
                self.assertFalse(destination.exists())

    def test_public_source_policy_keeps_exact_artwork_and_rejects_changes(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir();(root/'compliance').mkdir()
            script=root/'scripts/public-audit';shutil.copy2(REPOSITORY/'scripts/public-audit',script)
            for name in ('README.md','ROADMAP.md','LICENSE','THIRD_PARTY_NOTICES.md',
                         'docs/PRODUCTION.md','docs/PUBLIC_RELEASE_AUDIT.md'):
                f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('Fixture document.\n')
            f=root/'resources/branding/source/fixture.jpg';f.parent.mkdir(parents=True)
            f.write_bytes(b'x'*(5242880+1))
            policy={'large_source_files':[{'path':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':file_sha256(f)}]}
            (root/'compliance/public-source-files.json').write_text(json.dumps(policy))
            subprocess.run(['git','init','-q',str(root)],check=True,capture_output=True)
            subprocess.run(['git','-C',str(root),'add','.'],check=True,capture_output=True)
            def audit():return subprocess.run([str(script)],cwd=root,capture_output=True,text=True)
            self.assertEqual(audit().returncode,0)
            f.write_bytes(b'y'*(5242880+1));self.assertNotEqual(audit().returncode,0)
            f.write_bytes(b'x'*(5242880+1))
            personal=root/'docs/example.md';personal.write_text('/home/'+'den'+'nis'+'/private')
            subprocess.run(['git','-C',str(root),'add',str(personal)],check=True,capture_output=True)
            result=audit();self.assertNotEqual(result.returncode,0)
            self.assertIn('personal host identifiers',result.stderr)
            self.assertNotIn(personal.read_text(),result.stderr)

    def test_appdir_preparation_is_deterministic(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project)
            first = _prepare(project, stage, "first")
            second = _prepare(project, stage, "second")
            self.assertEqual((first / APPDIR_MANIFEST).read_bytes(), (second / APPDIR_MANIFEST).read_bytes())

    def test_only_default_carbon_is_packaged_while_active_user_theme_and_all_state_stay_external(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = _project(root)
            stage = _stage(project)
            home = root / "External user home"
            paths = EmbercadePaths.from_environment({"HOME": str(home)})
            user_files = {
                paths.themes / "downloaded-user-theme/theme.xml": b"user theme fixture",
                paths.theme_downloads / "pending-download.zip": b"unfinished user download",
                paths.emulationstation_config / "es_settings.cfg":
                    b'<config><string name="ThemeSet" value="downloaded-user-theme" /></config>',
                paths.secrets / "screenscraper.conf": b"developer-secret fixture",
                paths.secrets / "screenscraper-user.conf": b"personal-secret fixture",
                paths.data / "cores/fceumm_libretro.so": b"managed-core fixture",
                paths.data / "providers/shadps4/shadps4.AppImage": b"managed-provider fixture",
                paths.saves / "user-save.dat": b"save fixture",
                paths.data / "states/user-state.dat": b"state fixture",
                paths.screenshots / "user-screenshot.png": b"screenshot fixture",
                paths.data / "ppsspp-assets/user-resource.dat": b"PPSSPP fixture",
                paths.isolated_bios / "xemu/user-eeprom.bin": b"Xemu fixture",
                paths.state / "steam/user-shortcut.vdf": b"Steam user identity fixture",
                paths.logs / "user-log.txt": b"log fixture",
                home / "ROM collection/gamelist.xml": b"scraper metadata fixture",
                home / "ROM collection/images/user-media.png": b"scraper media fixture",
                home / "ROM collection/game.iso": b"ROM fixture",
                home / "BIOS collection/user-firmware.bin": b"BIOS fixture",
            }
            for path, content in user_files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in user_files}
            with patch.dict(os.environ, {"HOME": str(home)}):
                appdir = _prepare(project, stage)
            manifest = verify_appdir(appdir)
            themes = appdir / "usr/share/embercade/resources/emulationstation/themes"
            self.assertEqual({path.name for path in themes.iterdir()}, {"es-theme-carbon"})
            self.assertIn('value="es-theme-carbon"',
                          (appdir / "usr/share/embercade/resources/defaults/es_settings.cfg").read_text())
            self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in user_files})
            self.assertNotIn(str(home), (appdir / APPDIR_MANIFEST).read_text())
            for entry in manifest["included_files"]:
                self.assertNotIn("downloaded-user-theme", entry["path"])
                self.assertNotIn("pending-download.zip", entry["path"])
            bundled_data = [path.read_bytes() for path in appdir.rglob("*")
                            if path.is_file() and not path.is_symlink() and path.name != APPDIR_MANIFEST]
            for content in user_files.values():
                self.assertFalse(any(content in payload for payload in bundled_data))

    def test_valid_stage_manifest_cannot_authorize_bundled_user_themes_or_download_workspace(self) -> None:
        for relative in ("downloaded-user-theme/theme.xml", ".tmp/pending-theme.xml"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                project = _project(Path(directory))
                stage = _stage(project, {
                    f"share/embercade/resources/emulationstation/themes/{relative}": b"user theme fixture",
                })
                verify_payload(stage)
                with self.assertRaisesRegex(AppImageError, "only the standard es-theme-carbon"):
                    _prepare(project, stage)
                self.assertFalse((project / ".work/AppDir with spaces").exists())

    def test_corruption_unlisted_content_and_stale_branding_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project)
            appdir = _prepare(project, stage)
            (appdir / "secret.txt").write_text("unlisted")
            with self.assertRaisesRegex(AppImageError, "complete packaging manifest"):
                verify_appdir(appdir)
            (appdir / "secret.txt").unlink()
            (appdir / "usr/bin/embercade").write_text("tampered")
            with self.assertRaises(AppImageError):
                verify_appdir(appdir)
            data = json.loads((stage / STAGE_MANIFEST_RELATIVE).read_text())
            data["product_label"] = "EMBERCADE 0.5"
            (stage / STAGE_MANIFEST_RELATIVE).write_text(json.dumps(data))
            with self.assertRaisesRegex(AppImageError, "stale"):
                _prepare(project, stage, "stale")

    def test_user_state_secrets_and_provider_payload_are_rejected(self) -> None:
        for relative in ("share/private.iso", "share/providers/Xenia.AppImage",
                         "share/embercade/secrets/screenscraper.conf",
                         "share/embercade/screenscraper-user.conf",
                         "share/embercade/retroachievements-user.conf",
                         "share/embercade/retroachievements-build.conf",
                         "share/embercade/resources/defaults/es_settings.cfg"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                project = _project(Path(directory))
                data = b'<config><string name="ScreenScraperPass" value="fixture" /></config>'
                stage = _stage(project, {relative: data})
                with self.assertRaises(TransferPayloadError):
                    _prepare(project, stage)
                self.assertFalse((project / ".work/AppDir with spaces").exists())

    def test_valid_stage_manifest_cannot_authorize_bundled_host_gpu_stack(self) -> None:
        for name in ("libGL.so.1", "libdrm.so.2", "libvulkan_radeon.so", "radeonsi_dri.so",
                     "libglapi.so.0", "libgallium-25.0.so", "libVkLayer_MESA_overlay.so"):
            with self.subTest(name=name), TemporaryDirectory() as directory:
                project = _project(Path(directory))
                stage = _stage(project, {f"share/embercade/lib/{name}": b"fixture GPU stack"})
                verify_payload(stage)
                with self.assertRaisesRegex(AppImageError, "Host graphics"):
                    _prepare(project, stage)

    def test_full_scan_rejects_elf_embedded_home_or_build_paths_without_echoing(self) -> None:
        for marker in (b"/home/" + b"dennis/private", b"/home/" + b"deck/secret",
                       b"/home/arbitrary-account/build", b"/Users/other-account/build"):
            with self.subTest(marker="private marker"), TemporaryDirectory() as directory:
                project = _project(Path(directory))
                payload = b"\x7fELF" + b"x" * (1024 * 1024 - 8) + marker
                stage = _stage(project, {"share/embercade/frontend/emulationstation": payload})
                with self.assertRaisesRegex(AppImageError, "matched value omitted") as caught:
                    _prepare(project, stage)
                self.assertNotIn(marker.decode(), str(caught.exception))
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project, {"share/embercade/frontend/emulationstation":
                                    b"\x7fELF" + str(project).encode() + b"/.work/build/source.c"})
            with self.assertRaisesRegex(AppImageError, "matched value omitted"):
                _prepare(project, stage)

    def test_generic_upstream_comments_do_not_exempt_private_paths_in_the_same_file(self) -> None:
        examples = {
            "aiohttp/web_urldispatcher.py": b"# e.g. /static/../../../../home/user/webapp/static/\n",
            "pip/_internal/utils/urls.py": b'# On Windows, urlsplit parses the path as something like "/C:/Users/foo".\n',
        }
        for suffix, example in examples.items():
            for private in (False, True):
                with self.subTest(suffix=suffix, private=private), TemporaryDirectory() as directory:
                    project = _project(Path(directory))
                    data = example + (b"# /home/real-build-owner/private\n" if private else b"")
                    stage = _stage(project, {"share/embercade/runtime/venv/lib/python3.14/site-packages/" + suffix: data})
                    if private:
                        with self.assertRaisesRegex(AppImageError, "matched value omitted"):
                            _prepare(project, stage)
                    else:
                        self.assertEqual(verify_appdir(_prepare(project, stage))["product_label"], FRONTEND_PRODUCT_LABEL)

    def test_app_run_relocation_foreign_cwd_and_existing_state(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = _project(root)
            stage = _stage(project)
            appdir = _prepare(project, stage)
            moved = project / "Relocated AppDir"
            appdir.rename(moved)
            home, foreign = root / "User home", root / "foreign cwd"
            home.mkdir()
            foreign.mkdir()
            paths = EmbercadePaths.from_environment({"HOME": str(home)})
            paths.secrets.mkdir(parents=True)
            secret = paths.secrets / "screenscraper-user.conf"
            secret.write_bytes(b"fixture private state")
            before = (secret.read_bytes(), secret.stat().st_mtime_ns)
            completed = subprocess.run([str(moved / "AppRun"), "doctor", "--verbose"], cwd=foreign,
                                       env={"HOME": str(home), "PATH": "/usr/bin:/bin", "APPDIR": "/stale"},
                                       text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(f"prefix={moved / 'usr'}", completed.stdout)
            self.assertIn(f"appdir={moved}", completed.stdout)
            self.assertIn(f"cwd={foreign}", completed.stdout)
            self.assertIn("arg=doctor\narg=--verbose", completed.stdout)
            self.assertEqual((secret.read_bytes(), secret.stat().st_mtime_ns), before)
            self.assertEqual(list(foreign.iterdir()), [])
            self.assertFalse((moved / "usr/share/embercade/.work").exists())

    @unittest.skipUnless(shutil.which("bwrap"), "Bubblewrap is required for read-only runtime test")
    def test_app_run_executes_with_real_read_only_appdir(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = _project(root)
            appdir = _prepare(project, _stage(project))
            before = verify_appdir(appdir)
            completed = subprocess.run(["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--ro-bind", str(appdir), str(appdir),
                                       "--chdir", "/", "--", str(appdir / "AppRun"), "doctor"],
                                       env={"HOME": str(root), "PATH": "/usr/bin:/bin"},
                                       text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(f"prefix={appdir / 'usr'}", completed.stdout)
            self.assertEqual(verify_appdir(appdir), before)

    def test_portable_home_and_config_sidecars_are_rejected_before_runtime(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = _project(root)
            appdir = _prepare(project, _stage(project))
            image = root / "Embercade with spaces.AppImage"
            for suffix in (".home", ".config"):
                sidecar = Path(str(image) + suffix)
                sidecar.symlink_to(root / "missing")
                completed = subprocess.run([str(appdir / "AppRun"), "doctor"],
                                           env={"HOME": str(root), "PATH": "/usr/bin:/bin", "APPIMAGE": str(image)},
                                           text=True, capture_output=True, check=False)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")
                self.assertIn("unsupported", completed.stderr)
                sidecar.unlink()

    @unittest.skipUnless(shutil.which("bwrap"), "Bubblewrap is required for host interpreter boundary test")
    def test_missing_or_wrong_host_python_fails_before_stage_or_state(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = _project(root)
            appdir = _prepare(project, _stage(project))
            fake_python = root / "wrong-python"
            fake_python.write_text("#!/bin/sh\nexit 1\n")
            fake_python.chmod(0o755)
            before = verify_appdir(appdir)
            completed = subprocess.run(["bwrap", "--ro-bind", "/", "/", "--dev", "/dev",
                                       "--ro-bind", str(fake_python), str(Path("/usr/bin/python").resolve()), "--",
                                       str(appdir / "AppRun"), "doctor"],
                                       env={"HOME": str(root), "PATH": "/usr/bin:/bin"},
                                       text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertIn("CPython 3.14", completed.stderr)
            self.assertEqual(verify_appdir(appdir), before)
            self.assertFalse((root / ".config").exists())

    def test_classic_and_appimage_use_same_external_paths_provider_and_core_resolvers(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = _project(root)
            stage = _stage(project)
            appdir = _prepare(project, stage)
            home = root / "home"
            classic_env = {"HOME": str(home), "EMBERCADE_PREFIX": str(stage), "PATH": "/usr/bin"}
            image_env = {**classic_env, "EMBERCADE_PREFIX": str(appdir / "usr"), "APPDIR": str(appdir)}
            self.assertEqual(EmbercadePaths.from_environment(classic_env), EmbercadePaths.from_environment(image_env))
            self.assertEqual(ProductionLayout.from_environment(image_env).application, appdir / "usr/share/embercade")
            self.assertEqual(ProductionLayout.from_environment(classic_env).application, stage / "share/embercade")
            paths = EmbercadePaths.from_environment(image_env)
            core = paths.data / "cores/fceumm_libretro.so"
            core.parent.mkdir(parents=True)
            core.write_bytes(b"\x7fELFfixture")
            provider = paths.data / "providers/xenia/Xenia.AppImage"
            provider.parent.mkdir(parents=True)
            provider.write_text("#!/bin/sh\nexit 0\n")
            provider.chmod(0o755)
            for env in (classic_env, image_env):
                resolver = LibretroCoreResolver.from_host({}, env, fallback_core_directories=())
                self.assertEqual(resolver.resolve("fceumm").path, core)
                executables = ExecutableResolver(providers={"xenia-edge": EmulatorProvider(ProviderType.APPIMAGE, str(provider))}, environment=env)
                self.assertEqual(executables.resolve("xenia-edge").path, provider)
            self.assertNotIn("Xenia.AppImage", {entry["path"] for entry in verify_appdir(appdir)["included_files"]})

    def test_runtime_notice_corruption_and_destination_reuse_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project)
            appdir = _prepare(project, stage)
            with self.assertRaisesRegex(AppImageError, "fresh path"):
                _prepare(project, stage)
            (project / "packaging/appimage/licenses/LICENSE.txt").write_text("tampered")
            with self.assertRaisesRegex(AppImageError, "notice SHA"):
                _prepare(project, stage, "bad notices")
            self.assertTrue((appdir / APPDIR_MANIFEST).is_file())

    def test_packaging_destinations_cannot_contaminate_the_golden_stage(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project)
            before = verify_payload(stage)
            with self.assertRaisesRegex(AppImageError, "outside the Stage"):
                prepare_appdir(project_root=project, stage_root=stage, appdir=stage / "nested",
                               source_commit="a" * 40, source_date_epoch=1700000000)
            self.assertFalse((stage / "nested").exists())
            with patch("embercade.appimage.verify_tools") as tools, patch("embercade.appimage.subprocess.run") as execute:
                with self.assertRaisesRegex(AppImageError, "outside the golden"):
                    build_appimage(project_root=project, stage_root=stage, output=stage / "Embercade.AppImage",
                                   source_commit="a" * 40, source_date_epoch=1700000000)
                tools.assert_not_called()
                execute.assert_not_called()
                before_paths = sorted(path.relative_to(project) for path in project.rglob("*"))
                with self.assertRaisesRegex(AppImageError, "workspace must stay outside"):
                    build_appimage(project_root=project, stage_root=project / ".work",
                                   output=project / "dist/Embercade.AppImage",
                                   source_commit="a" * 40, source_date_epoch=1700000000)
                self.assertEqual(sorted(path.relative_to(project) for path in project.rglob("*")), before_paths)
                tools.assert_not_called()
                execute.assert_not_called()
            self.assertEqual(verify_payload(stage), before)

    def test_missing_or_corrupt_build_tools_never_download_or_execute_implicitly(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            stage = _stage(project)
            with patch("embercade.appimage.urllib.request.urlopen") as download, patch("embercade.appimage.subprocess.run") as execute:
                with self.assertRaisesRegex(AppImageError, "missing"):
                    build_appimage(project_root=project, stage_root=stage, output=project / "dist/Test.AppImage",
                                   source_commit="a" * 40, source_date_epoch=1700000000)
                download.assert_not_called()
                execute.assert_not_called()
            lock = load_build_lock(project)
            tool_root = project / ".work/tools/appimage"
            tool_root.mkdir(parents=True)
            (tool_root / lock["appimagetool"]["filename"]).write_bytes(b"wrong tool")
            with self.assertRaisesRegex(AppImageError, "SHA-256 mismatch"):
                verify_tools(project, lock)

    def test_explicit_tool_preparation_verifies_bytes_before_activation(self) -> None:
        with TemporaryDirectory() as directory:
            project = _project(Path(directory))
            lock = load_build_lock(project)
            data = b"fixture locked tool"
            for name in ("appimagetool", "runtime"):
                lock[name]["sha256"] = sha256(data).hexdigest()
            with patch("embercade.appimage.urllib.request.urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(data)) as download:
                paths = prepare_tools(project, lock)
                self.assertEqual(download.call_count, 2)
                self.assertEqual(paths["runtime"].read_bytes(), data)
                prepare_tools(project, lock)
                self.assertEqual(download.call_count, 2)
            paths["runtime"].write_bytes(b"changed")
            with self.assertRaisesRegex(AppImageError, "nothing overwritten"):
                prepare_tools(project, lock)
            self.assertEqual(paths["runtime"].read_bytes(), b"changed")


if __name__ == "__main__":
    unittest.main()

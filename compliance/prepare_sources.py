#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare local matching sources/notices; never build, upload or run payloads.

Only immutable Git trees, checksum-verified archives and indexed notice files
are inputs. In particular, no build source tree, HOME, credential header or
untracked project file is included by walking the project directory.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile


PROJECT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def child(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Unsafe indexed path")
    target = root / name
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Indexed path leaves its root")
    return target


def checked_file(root, entry):
    path = child(root, entry["file"])
    if not path.is_file() or digest(path) != entry["sha256"]:
        raise ValueError("Missing or changed indexed input: " + entry["file"])
    return path


def extract(archive, destination):
    destination.mkdir()
    with tarfile.open(archive) as stream:
        stream.extractall(destination, filter="data")
    # Our patched source inputs do not need absolute/escaping links or devices.
    for path in destination.rglob("*"):
        if path.is_symlink() and not path.resolve().is_relative_to(destination.resolve()):
            raise ValueError("Source link leaves extraction root")


def tree_archive(repository, revision, destination, prefix):
    commit = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", revision + "^{commit}"], text=True
    ).strip()
    if commit != revision:
        raise ValueError("Use a complete immutable source commit")
    subprocess.run(["git", "-C", str(repository), "archive", "--format=tar.gz",
                    "--prefix=" + prefix + "/", "--output=" + str(destination), commit], check=True)


def apply_patches(source, patches):
    reports = []
    for patch in sorted(patches.glob("*.patch")):
        with patch.open("rb") as stream:
            result = subprocess.run(["patch", "--batch", "--forward", "-p1", "-d", str(source)],
                                    stdin=stream, capture_output=True, text=True)
        if result.returncode:
            raise ValueError("Source patch failed: " + patch.name + "\n" + result.stdout + result.stderr)
        reports.append(patch.name + "\n" + result.stdout + result.stderr)
    return "\n".join(reports)


def archive_tree(root, output):
    # Stable metadata; retain executable bits and original relative symlinks.
    def normalize(info):
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        info.mtime = 0
        return info

    with output.open("xb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed:
        with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as stream:
            stream.add(root, arcname="Embercade-sources", filter=normalize)


def preparation_metadata(manifest):
    publication = (manifest.get("distribution"), manifest.get("public_release"))
    if publication not in {("PRIVATE", "BLOCKED"), ("PUBLIC", "PREPARED_NOT_PUBLISHED")}:
        raise ValueError("Unsupported artifact publication state")
    return {
        "status": "PUBLIC_CANDIDATE_NOT_PUBLISHED" if publication[0] == "PUBLIC" else "LOCAL_PREPARATION_NOT_PUBLISHED",
        "artifact_distribution": publication[0], "public_release_approved": False,
    }


def prepare(cache, output, image, manifest_file, project=PROJECT):
    manifest = json.loads(manifest_file.read_text())
    publication = preparation_metadata(manifest)
    if manifest["source_tree_dirty"]:
        raise ValueError("A dirty source identity needs a separately recorded source snapshot")
    if digest(image) != manifest["image"]["sha256"] or image.stat().st_size != manifest["image"]["size"]:
        raise ValueError("Image does not match its manifest")
    source_commit = manifest["source_commit"]
    inputs = json.loads((project / "compliance/sources.lock.json").read_text())
    notices = json.loads((project / "compliance/notices.lock.json").read_text())
    sources = {e["component"]: e for e in inputs["sources"]}
    if set(sources) != set(inputs["required_components"]):
        raise ValueError("Incomplete source set")
    verified = [(entry, checked_file(cache, entry)) for entry in inputs["sources"]]
    verified_notices = [(entry, checked_file(project, entry)) for entry in notices["notices"]]
    compliance_commit = subprocess.check_output(["git", "-C", str(project), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(project), "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit the release-preparation inputs before freezing the kit")
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="source-kit-", dir=output) as temp:
        root = Path(temp)
        archives = root / "archives"
        archives.mkdir()
        for entry, path in verified:
            shutil.copyfile(path, archives / entry["file"])
        own = archives / ("embercade-" + source_commit + ".tar.gz")
        tree_archive(project, source_commit, own, "Embercade")
        # This committed supplement carries legal corrections/tooling after the
        # frozen binary source, without pretending that binary was rebuilt.
        supplement = archives / ("compliance-" + compliance_commit + ".tar.gz")
        subprocess.run(["git", "-C", str(project), "archive", "--format=tar.gz",
                        "--prefix=legal-supplement/", "--output="+str(supplement), compliance_commit,
                        "LICENSE", "LICENSES", "THIRD_PARTY_NOTICES.md", "compliance", "docs"], check=True)

        modified = root / "modified"
        modified.mkdir()
        with tempfile.TemporaryDirectory(prefix="exact-project-", dir=output) as temp_project:
            exact = Path(temp_project)
            with tarfile.open(own) as stream:
                stream.extractall(exact, filter="data")
            exact = exact / "Embercade"
            for component, patch_dir in (("batocera", "batocera-launch"), ("emulationstation", "emulationstation")):
                container = modified / component
                extract(archives / sources[component]["file"], container)
                source = container / component
                report = apply_patches(source, exact / "patches" / patch_dir)
                (container / "patch-application.log").write_text(report)
                if component == "emulationstation":
                    for header in (exact / "patches/emulationstation").glob("*.h"):
                        subdir = "es-app" if header.name == "EmbercadeDecorationAvailability.h" else "es-core"
                        shutil.copyfile(header, source / subdir / "src" / header.name)
                    shutil.copyfile(exact / "resources/branding/icon/embercade-512.png", source / "resources/window_icon_256.png")
                (container / "EMBERCADE-CHANGES.txt").write_text(
                    "Source pin: " + sources[component]["version"] + "\n"
                    "Embercade modifications: complete patches/" + patch_dir + " at " + source_commit + ".\n"
                    "Original notices/terms retained. All patches applied with the existing build recipe's patch semantics; see patch-application.log.\n"
                    "Generated provider credential headers are intentionally absent; use your own authorized build input.\n")

        supplement_notices = root / "supplemental-notices"
        supplement_notices.mkdir()
        for entry, path in verified_notices:
            target = supplement_notices / entry["file"].removeprefix("LICENSES/third-party/")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        for name in ("sources.lock.json", "notices.lock.json", "REBUILDING.md", "README.md"):
            shutil.copyfile(project / "compliance" / name, root / name)
        receipt = {
            "schema": 1, **publication,
            "binary_sha256": manifest["image"]["sha256"], "binary_source_commit": source_commit,
            "compliance_commit": compliance_commit,
            "source_archives": inputs["sources"] + [
                {"component": "embercade", "file": own.name, "sha256": digest(own)},
                {"component": "legal-supplement", "file": supplement.name, "sha256": digest(supplement)}],
            "excluded": ["credential headers and build cache", "personal profiles/ROMs/BIOS/keys", "Git history/.git"],
            "build_verification": "Patches applied; runtime rebuild/relink recipe included. No new binary built."
        }
        (root / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
        all_files = sorted(f for f in root.rglob("*") if f.is_file() and not f.is_symlink())
        (root / "SHA256SUMS").write_text("".join(digest(f)+"  "+f.relative_to(root).as_posix()+"\n" for f in all_files))
        target = output / "Embercade-1.0-sources-and-notices.tar.gz"
        archive_tree(root, target)
    (output / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "SHA256SUMS").write_text(digest(target) + "  " + target.name + "\n")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cache", "output", "image", "manifest"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.cache.resolve(), args.output.resolve(), args.image.resolve(), args.manifest.resolve()))

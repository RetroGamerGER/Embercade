"""Read-only BIOS and firmware inventory using Batocera's pinned checker data."""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import md5
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
from typing import Any, Iterable, Mapping
import zipfile


BATOCERA_COMMIT = "9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48"
BATOCERA_BIOS_SOURCE = (
    "package/batocera/core/batocera-scripts/scripts/batocera-systems"
)
MATCHED_STATUSES = frozenset({"HASH_MATCH", "PATH_MATCH", "ALTERNATIVE_MATCH"})

# Batocera's pinned checker lists FZ-1, FZ-10 and Goldstar. Opera needs one
# system BIOS, not all three. Additional alternatives and their exact names
# come from libopera/opera_bios.c at the core revision in Batocera's recipe:
# libretro/opera-libretro a501a278d057b952d1ad6165549c59ab178ca497.
# Font ROMs are a separate, game-dependent requirement, not system BIOSes.
OPERA_BIOS_HASHES = {
    "panafz1.bin": "f47264dd47fe30f73ab3c010015c155b",
    "panafz1j.bin": "a496cfdded3da562759be3561317b605",
    "panafz1j-norsa.bin": "f6c71de7470d16abe4f71b1444883dc8",
    "panafz10.bin": "51f2f43ae2f3508a14d9f56597e2d3ce",
    "panafz10-norsa.bin": "1477bda80dc33731a65468c1f5bcbee9",
    "panafz10e-anvil.bin": "a48e6746bd7edec0f40cff078f0bb19f",
    "panafz10e-anvil-norsa.bin": "cf11bbb5a16d7af9875cca9de9a15e09",
    "goldstar.bin": "8639fd5e549bd6238cfee79e3e749114",
    "sanyotry.bin": "35fa1a1ebaaeea286dc5cd15487c13ea",
    "3do_arcade_saot.bin": "8970fc987ab89a7f64da9f8a8c4333ff",
}


@dataclass(frozen=True, slots=True)
class BiosAvailability:
    status: str
    detail: str
    files: tuple[Path, ...] = ()

    @property
    def available(self) -> bool:
        return self.status == "OK"


class BiosInventoryError(RuntimeError):
    """The requested BIOS inventory cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class BiosRequirement:
    system: str
    system_name: str
    source_path: str
    relative_path: str | None
    expected_md5: str | None
    zipped_file: str | None = None
    emulator: str | None = None
    core: str | None = None
    optional: bool = False
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScannedFile:
    relative_path: str
    path: Path
    size: int


@dataclass(slots=True)
class BiosTree:
    root: Path
    files: dict[str, ScannedFile]
    symlinks: set[str]
    directories: int
    total_bytes: int

    @property
    def casefold_index(self) -> Mapping[str, tuple[str, ...]]:
        values: dict[str, list[str]] = defaultdict(list)
        for relative_path in (*self.files, *self.symlinks):
            values[relative_path.casefold()].append(relative_path)
        return {key: tuple(sorted(paths)) for key, paths in values.items()}

    @property
    def basename_index(self) -> Mapping[str, tuple[str, ...]]:
        values: dict[str, list[str]] = defaultdict(list)
        for relative_path in self.files:
            values[PurePosixPath(relative_path).name.casefold()].append(relative_path)
        return {key: tuple(sorted(paths)) for key, paths in values.items()}


def read_pinned_batocera_source(repository: Path) -> str:
    repository = repository.expanduser().absolute()
    if not repository.is_dir():
        raise BiosInventoryError(f"Batocera repository is unavailable: {repository}")
    process = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(repository),
            "show",
            f"{BATOCERA_COMMIT}:{BATOCERA_BIOS_SOURCE}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or "git show failed"
        raise BiosInventoryError(
            f"Cannot read pinned Batocera BIOS metadata: {detail}"
        )
    return process.stdout


def _bios_relative_path(source_path: str) -> str | None:
    path = PurePosixPath(source_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    if not path.parts or path.parts[0] != "bios" or len(path.parts) == 1:
        return None
    return PurePosixPath(*path.parts[1:]).as_posix()


def load_batocera_bios_requirements(source: str) -> tuple[BiosRequirement, ...]:
    try:
        tree = ast.parse(source)
        assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "systems" for target in node.targets)
        )
        systems = ast.literal_eval(assignment.value)
    except (StopIteration, SyntaxError, ValueError, TypeError) as error:
        raise BiosInventoryError("Batocera BIOS metadata cannot be parsed safely") from error
    if not isinstance(systems, dict):
        raise BiosInventoryError("Batocera BIOS metadata has no systems dictionary")

    requirements: list[BiosRequirement] = []
    for system, definition in systems.items():
        if not isinstance(system, str) or not isinstance(definition, dict):
            raise BiosInventoryError("Batocera BIOS system entry is malformed")
        system_name = definition.get("name", system)
        entries = definition.get("biosFiles", ())
        if not isinstance(entries, (list, tuple)):
            raise BiosInventoryError(f"Batocera BIOS list is malformed for {system}")
        system_emulator = definition.get("emulator")
        system_core = definition.get("core")
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("file"), str):
                raise BiosInventoryError(f"Batocera BIOS entry is malformed for {system}")
            source_path = entry["file"]
            expected_md5 = entry.get("md5") or None
            if expected_md5 is not None:
                expected_md5 = str(expected_md5).casefold()
            alternatives = entry.get("alternatives", ())
            if isinstance(alternatives, str):
                alternatives = (alternatives,)
            if not isinstance(alternatives, (list, tuple)) or not all(
                isinstance(value, str) for value in alternatives
            ):
                raise BiosInventoryError(f"Batocera BIOS alternatives are malformed for {system}")
            requirements.append(
                BiosRequirement(
                    system=system,
                    system_name=str(system_name),
                    source_path=source_path,
                    relative_path=_bios_relative_path(source_path),
                    expected_md5=expected_md5,
                    zipped_file=entry.get("zippedFile"),
                    emulator=entry.get("emulator", system_emulator),
                    core=entry.get("core", system_core),
                    optional=bool(entry.get("optional", False)),
                    alternatives=tuple(
                        relative
                        for value in alternatives
                        if (relative := _bios_relative_path(value)) is not None
                    ),
                )
            )
    if not requirements:
        raise BiosInventoryError("Batocera BIOS metadata contains no requirements")
    return tuple(requirements)


def scan_bios_root(root: Path) -> BiosTree:
    root = root.expanduser().absolute()
    if not root.is_dir() or not os.access(root, os.R_OK | os.X_OK):
        raise BiosInventoryError(f"BIOS root is not a readable directory: {root}")
    files: dict[str, ScannedFile] = {}
    symlinks: set[str] = set()
    directories = 0
    total_bytes = 0
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                    except OSError as error:
                        raise BiosInventoryError(
                            f"Cannot read BIOS metadata for {entry.path}: {error}"
                        ) from error
                    path = Path(entry.path)
                    relative_path = path.relative_to(root).as_posix()
                    if stat.S_ISLNK(metadata.st_mode):
                        symlinks.add(relative_path)
                    elif stat.S_ISDIR(metadata.st_mode):
                        directories += 1
                        stack.append(path)
                    elif stat.S_ISREG(metadata.st_mode):
                        files[relative_path] = ScannedFile(
                            relative_path, path, metadata.st_size
                        )
                        total_bytes += metadata.st_size
        except OSError as error:
            raise BiosInventoryError(
                f"Cannot enumerate BIOS directory {directory}: {error}"
            ) from error
    return BiosTree(root, files, symlinks, directories, total_bytes)


def _md5_file(path: Path) -> str:
    digest = md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class RequirementEvaluator:
    def __init__(self, tree: BiosTree) -> None:
        self.tree = tree
        self.casefold_index = tree.casefold_index
        self.basename_index = tree.basename_index
        self.file_hashes: dict[Path, str] = {}
        self.archive_members: dict[Path, dict[str, zipfile.ZipInfo] | None] = {}
        self.archive_hashes: dict[tuple[Path, str], str] = {}
        self.hashes_performed = 0

    def _hash_file(self, path: Path) -> str:
        if path not in self.file_hashes:
            try:
                self.file_hashes[path] = _md5_file(path)
            except OSError as error:
                raise BiosInventoryError(f"Cannot hash BIOS file {path}: {error}") from error
            self.hashes_performed += 1
        return self.file_hashes[path]

    def _zip_infos(self, path: Path) -> dict[str, zipfile.ZipInfo] | None:
        if path not in self.archive_members:
            try:
                with zipfile.ZipFile(path) as archive:
                    self.archive_members[path] = {
                        info.filename: info for info in archive.infolist() if not info.is_dir()
                    }
            except (OSError, zipfile.BadZipFile):
                self.archive_members[path] = None
        return self.archive_members[path]

    def _hash_zip_member(self, path: Path, member: str) -> str:
        key = (path, member)
        if key not in self.archive_hashes:
            digest = md5()
            try:
                with zipfile.ZipFile(path) as archive, archive.open(member) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
            except (OSError, KeyError, zipfile.BadZipFile) as error:
                raise BiosInventoryError(
                    f"Cannot hash {member} inside BIOS archive {path}: {error}"
                ) from error
            self.archive_hashes[key] = digest.hexdigest()
            self.hashes_performed += 1
        return self.archive_hashes[key]

    def _missing_result(self, requirement: BiosRequirement) -> dict[str, Any]:
        assert requirement.relative_path is not None
        relative = requirement.relative_path
        case_matches = self.casefold_index.get(relative.casefold(), ())
        if case_matches:
            actual_hash = None
            size = None
            matched_path = case_matches[0] if len(case_matches) == 1 else None
            diagnostic = "Expected path differs only by case"
            if matched_path is not None and matched_path in self.tree.files:
                scanned = self.tree.files[matched_path]
                size = scanned.size
                if requirement.expected_md5 and requirement.zipped_file is None:
                    actual_hash = self._hash_file(scanned.path)
                    diagnostic += (
                        "; content hash matches"
                        if actual_hash == requirement.expected_md5
                        else "; content hash does not match"
                    )
            return self._result(
                requirement,
                "CASE_MISMATCH",
                actual_hash=actual_hash,
                size=size,
                matched_path=matched_path,
                diagnostic=diagnostic,
                candidates=case_matches,
            )
        basename = PurePosixPath(relative).name.casefold()
        wrong_locations = tuple(
            value for value in self.basename_index.get(basename, ()) if value != relative
        )
        if wrong_locations:
            return self._result(
                requirement,
                "WRONG_LOCATION",
                diagnostic="Expected basename exists at another relative path",
                candidates=wrong_locations,
            )
        status = "OPTIONAL_MISSING" if requirement.optional else "MISSING"
        return self._result(requirement, status)

    @staticmethod
    def _result(
        requirement: BiosRequirement,
        status: str,
        *,
        actual_hash: str | None = None,
        size: int | None = None,
        matched_path: str | None = None,
        diagnostic: str | None = None,
        candidates: Iterable[str] = (),
    ) -> dict[str, Any]:
        return {
            "system": requirement.system,
            "system_name": requirement.system_name,
            "source_path": requirement.source_path,
            "relative_path": requirement.relative_path,
            "zipped_file": requirement.zipped_file,
            "required": not requirement.optional,
            "optional": requirement.optional,
            "emulator": requirement.emulator,
            "core": requirement.core,
            "alternative_group": list(requirement.alternatives),
            "status": status,
            "hash_algorithm": "md5" if requirement.expected_md5 else None,
            "expected_hash": requirement.expected_md5,
            "actual_hash": actual_hash,
            "size": size,
            "matched_path": matched_path,
            "diagnostic": diagnostic,
            "candidates": list(candidates),
        }

    def _evaluate_at_path(
        self,
        requirement: BiosRequirement,
        relative_path: str,
        *,
        alternative: bool,
    ) -> dict[str, Any] | None:
        scanned = self.tree.files.get(relative_path)
        if scanned is None:
            return None
        success_status = "ALTERNATIVE_MATCH" if alternative else None
        if requirement.zipped_file is not None:
            infos = self._zip_infos(scanned.path)
            if infos is None:
                return self._result(
                    requirement,
                    "UNKNOWN",
                    size=scanned.size,
                    matched_path=relative_path,
                    diagnostic="Referenced ZIP container cannot be read",
                )
            member = requirement.zipped_file
            if member not in infos:
                variants = tuple(
                    name for name in infos if name.casefold() == member.casefold()
                )
                status = "CASE_MISMATCH" if variants else (
                    "OPTIONAL_MISSING" if requirement.optional else "MISSING"
                )
                return self._result(
                    requirement,
                    status,
                    size=scanned.size,
                    matched_path=relative_path,
                    diagnostic=(
                        "ZIP member differs only by case"
                        if variants
                        else "Expected member is missing from ZIP container"
                    ),
                    candidates=variants,
                )
            if requirement.expected_md5:
                actual_hash = self._hash_zip_member(scanned.path, member)
                status = (
                    success_status or "HASH_MATCH"
                    if actual_hash == requirement.expected_md5
                    else "HASH_MISMATCH"
                )
                return self._result(
                    requirement,
                    status,
                    actual_hash=actual_hash,
                    size=infos[member].file_size,
                    matched_path=relative_path,
                )
            return self._result(
                requirement,
                success_status or "PATH_MATCH",
                size=infos[member].file_size,
                matched_path=relative_path,
            )
        if requirement.expected_md5:
            actual_hash = self._hash_file(scanned.path)
            status = (
                success_status or "HASH_MATCH"
                if actual_hash == requirement.expected_md5
                else "HASH_MISMATCH"
            )
            return self._result(
                requirement,
                status,
                actual_hash=actual_hash,
                size=scanned.size,
                matched_path=relative_path,
            )
        return self._result(
            requirement,
            success_status or "PATH_MATCH",
            size=scanned.size,
            matched_path=relative_path,
        )

    def evaluate(self, requirement: BiosRequirement) -> dict[str, Any]:
        if requirement.relative_path is None:
            return self._result(
                requirement,
                "UNKNOWN",
                diagnostic="Batocera path is outside BIOS_ROOT",
            )
        if requirement.relative_path in self.tree.symlinks:
            return self._result(
                requirement,
                "UNKNOWN",
                matched_path=requirement.relative_path,
                diagnostic="Expected path is a symlink; symlinks are not followed",
            )
        result = self._evaluate_at_path(
            requirement, requirement.relative_path, alternative=False
        )
        if result is not None:
            return result
        for alternative in requirement.alternatives:
            result = self._evaluate_at_path(requirement, alternative, alternative=True)
            if result is not None and result["status"] in MATCHED_STATUSES:
                return result
        return self._missing_result(requirement)


def inspect_opera_bios(root: Path) -> BiosAvailability:
    """Reuse the read-only inventory evaluator for Opera's one-of BIOS set.

    This reports available firmware, never successful emulation or READY.
    It does not pick/change the core's BIOS option or copy any source files.
    """
    try:
        evaluator = RequirementEvaluator(scan_bios_root(root))
        rows = tuple(evaluator.evaluate(BiosRequirement(
            "3do", "3DO", f"bios/{name}", name, digest,
            emulator="libretro", core="opera",
        )) for name, digest in OPERA_BIOS_HASHES.items())
    except BiosInventoryError as error:
        return BiosAvailability("PATH_UNAVAILABLE", str(error))
    files = tuple(root / row["relative_path"] for row in rows
                  if row["status"] == "HASH_MATCH")
    if files:
        return BiosAvailability("OK", "Available: " + ", ".join(path.name for path in files), files)
    problems = tuple(row for row in rows if row["status"] != "MISSING")
    if problems:
        detail = "; ".join(f"{row['relative_path']}: {row['status']}"
                           + (f" ({', '.join(row['candidates'])})" if row["candidates"] else "")
                           for row in problems)
        return BiosAvailability("INVALID_OR_WRONG_PATH", detail)
    return BiosAvailability(
        "MISSING", "Place one of your own supported BIOS files directly in the selected BIOS folder: "
        + ", ".join(OPERA_BIOS_HASHES),
    )


def _rom_systems(rom_inventory: Mapping[str, Any]) -> dict[str, set[str]]:
    relevant: dict[str, set[str]] = defaultdict(set)
    for row in rom_inventory.get("systems", ()):
        system = row.get("system")
        status = row.get("content_status")
        if system and status in {"ROM_PRESENT", "SPECIAL_LAYOUT_PRESENT"}:
            relevant[system].add(status)
    return relevant


def build_bios_inventory(
    bios_root: Path,
    requirements: Iterable[BiosRequirement],
    rom_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    requirements = tuple(requirements)
    tree = scan_bios_root(bios_root)
    evaluator = RequirementEvaluator(tree)
    results = [evaluator.evaluate(requirement) for requirement in requirements]
    status_counts = Counter(result["status"] for result in results)
    referenced_paths = {
        result["matched_path"]
        for result in results
        if result["matched_path"] in tree.files
    }
    unreferenced = sorted(set(tree.files) - referenced_paths)
    unreferenced_extensions = Counter(
        PurePosixPath(path).suffix.casefold() or "<none>" for path in unreferenced
    )
    unreferenced_top_level = Counter(PurePosixPath(path).parts[0] for path in unreferenced)

    relevant = _rom_systems(rom_inventory)
    by_system: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_system[result["system"]].append(result)
    system_summary: list[dict[str, Any]] = []
    for system in sorted(relevant):
        entries = by_system.get(system, [])
        counts = Counter(entry["status"] for entry in entries)
        system_summary.append(
            {
                "system": system,
                "rom_status": sorted(relevant[system]),
                "requirements_total": len(entries),
                "required_matched": sum(
                    counts[status] for status in MATCHED_STATUSES
                ),
                "required_missing": counts["MISSING"],
                "optional_missing": counts["OPTIONAL_MISSING"],
                "hash_mismatches": counts["HASH_MISMATCH"],
                "case_mismatches": counts["CASE_MISMATCH"],
                "wrong_location": counts["WRONG_LOCATION"],
                "unknown_requirements": counts["UNKNOWN"],
            }
        )

    return {
        "schema_version": 1,
        "batocera_commit": BATOCERA_COMMIT,
        "batocera_source": BATOCERA_BIOS_SOURCE,
        "bios_root": os.fspath(tree.root),
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "source_semantics": {
            "hash_algorithm": "md5",
            "optional_metadata_available": any(req.optional for req in requirements),
            "alternative_groups_available": any(req.alternatives for req in requirements),
            "zip_members_checked_in_memory": True,
        },
        "summary": {
            "requirements_total": len(results),
            "requirements_with_hash": sum(
                result["expected_hash"] is not None for result in results
            ),
            "requirements_without_hash": sum(
                result["expected_hash"] is None for result in results
            ),
            "bios_files": len(tree.files),
            "bios_directories": tree.directories,
            "bios_symlinks": len(tree.symlinks),
            "bios_total_bytes": tree.total_bytes,
            "hashes_performed": evaluator.hashes_performed,
            "unreferenced": len(unreferenced),
            **{status.casefold(): status_counts[status] for status in (
                "HASH_MATCH",
                "PATH_MATCH",
                "ALTERNATIVE_MATCH",
                "MISSING",
                "OPTIONAL_MISSING",
                "HASH_MISMATCH",
                "CASE_MISMATCH",
                "WRONG_LOCATION",
                "NOT_APPLICABLE",
                "UNKNOWN",
            )},
        },
        "systems": system_summary,
        "requirements": results,
        "unreferenced": {
            "count": len(unreferenced),
            "relative_paths": unreferenced,
            "extensions": dict(sorted(unreferenced_extensions.items())),
            "top_level": dict(sorted(unreferenced_top_level.items())),
        },
        "symlinks": sorted(tree.symlinks),
    }


def write_inventory(path: Path, inventory: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(size) < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def render_documentation(inventory: Mapping[str, Any]) -> str:
    summary = inventory["summary"]
    systems = inventory["systems"]
    requirements = inventory["requirements"]
    lines = [
        "# BIOS / Firmware Inventory",
        "",
        f"Batocera reference: `{inventory['batocera_commit']}`.",
        "",
        "This is a read-only snapshot of `BIOS_ROOT`. Batocera's pinned "
        "`batocera-systems` checker is the only requirements source. Its data has "
        "no general machine-readable optional or alternative-group semantics; "
        "therefore no such relationships are inferred from comments or external knowledge.",
        "",
        "The central dictionary is filtered by Batocera at runtime through "
        "`es_systems.cfg` and optional emulator/core gates. This inventory records those "
        "gates but does not infer `NOT_APPLICABLE` from the ROM inventory's default core alone. "
        "For Xemu, the checker lists the user-supplied MCPX and flash ROM files. The pinned "
        "launcher keeps EEPROM and HDD state under `saves/xbox`; Batocera packages the base "
        "HDD image itself, so those two files are not counted as BIOS_ROOT requirements.",
        "",
        "## Summary",
        "",
        f"- Requirements: {summary['requirements_total']}",
        f"- BIOS files: {summary['bios_files']}",
        f"- BIOS data size: {_human_size(summary['bios_total_bytes'])}",
        f"- HASH_MATCH: {summary['hash_match']}",
        f"- PATH_MATCH: {summary['path_match']}",
        f"- ALTERNATIVE_MATCH: {summary['alternative_match']}",
        f"- MISSING: {summary['missing']}",
        f"- OPTIONAL_MISSING: {summary['optional_missing']}",
        f"- HASH_MISMATCH: {summary['hash_mismatch']}",
        f"- CASE_MISMATCH: {summary['case_mismatch']}",
        f"- WRONG_LOCATION: {summary['wrong_location']}",
        f"- UNKNOWN: {summary['unknown']}",
        f"- UNREFERENCED files: {summary['unreferenced']}",
        f"- Targeted MD5 calculations: {summary['hashes_performed']}",
        "",
        "A match describes only the pinned BIOS checker result. It is not an overall "
        "system compatibility or readiness decision.",
        "",
        "## Systems present in ROM collection",
        "",
        "| System | ROM status | Requirements | Matched | Missing | Mismatch | Case/path | Unknown |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for system in systems:
        case_path = system["case_mismatches"] + system["wrong_location"]
        lines.append(
            f"| {system['system']} | {', '.join(system['rom_status'])} | "
            f"{system['requirements_total']} | {system['required_matched']} | "
            f"{system['required_missing']} | {system['hash_mismatches']} | "
            f"{case_path} | {system['unknown_requirements']} |"
        )

    relevant_system_ids = {entry["system"] for entry in systems}

    def add_issue_section(
        title: str,
        statuses: set[str],
        limit: int = 80,
        *,
        relevant_only: bool = False,
    ) -> None:
        matching = [
            entry
            for entry in requirements
            if entry["status"] in statuses
            and (not relevant_only or entry["system"] in relevant_system_ids)
        ]
        lines.extend(["", f"## {title}", ""])
        if not matching:
            lines.append("None.")
            return
        for entry in matching[:limit]:
            target = entry["relative_path"] or entry["source_path"]
            member = f" :: {entry['zipped_file']}" if entry["zipped_file"] else ""
            lines.append(
                f"- `{entry['system']}`: `{target}{member}` — {entry['status']}"
            )
        if len(matching) > limit:
            lines.append(f"- … {len(matching) - limit} additional entries are in the JSON inventory.")

    add_issue_section(
        "Missing required firmware for ROM-present systems",
        {"MISSING", "WRONG_LOCATION", "CASE_MISMATCH"},
        relevant_only=True,
    )
    add_issue_section("Hash mismatches", {"HASH_MISMATCH"})
    add_issue_section("Unknown requirements", {"UNKNOWN"})

    lines.extend(["", "## Selected systems", ""])
    selected = ("ps2", "ps3", "xbox", "dreamcast", "psx", "megacd", "saturn", "neogeo")
    by_system: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for entry in requirements:
        by_system[entry["system"]].append(entry)
    for system in selected:
        entries = by_system.get(system, [])
        counts = Counter(entry["status"] for entry in entries)
        lines.append(
            f"- `{system}`: requirements={len(entries)}, "
            f"matched={sum(counts[value] for value in MATCHED_STATUSES)}, "
            f"missing={counts['MISSING']}, mismatch={counts['HASH_MISMATCH']}, "
            f"case/path={counts['CASE_MISMATCH'] + counts['WRONG_LOCATION']}, "
            f"unknown={counts['UNKNOWN']}"
        )

    extensions = inventory["unreferenced"]["extensions"]
    top_level = inventory["unreferenced"]["top_level"]
    extension_summary = ", ".join(
        f"{name} ({count})"
        for name, count in sorted(extensions.items(), key=lambda item: (-item[1], item[0]))[:12]
    ) or "none"
    top_summary = ", ".join(
        f"{name} ({count})"
        for name, count in sorted(top_level.items(), key=lambda item: (-item[1], item[0]))[:12]
    ) or "none"
    lines.extend(
        [
            "",
            "## Unreferenced BIOS content",
            "",
            f"- Files: {summary['unreferenced']}",
            f"- Common extensions: {extension_summary}",
            f"- Common top-level groups: {top_summary}",
            "",
            "Unreferenced files are not automatically errors and no deletion is implied.",
            "",
        ]
    )
    return "\n".join(lines)


def write_documentation(path: Path, inventory: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_documentation(inventory), encoding="utf-8")

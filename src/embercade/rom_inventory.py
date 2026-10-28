"""Read-only, metadata-only ROM collection inventory."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import os
import stat
import xml.etree.ElementTree as ET


BATOCERA_COMMIT = "9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48"
COMPANION_EXTENSIONS = frozenset(
    {
        ".bmp",
        ".avi",
        ".flac",
        ".gif",
        ".jpeg",
        ".jpg",
        ".json",
        ".log",
        ".m4v",
        ".md",
        ".mkv",
        ".mov",
        ".mp3",
        ".mp4",
        ".nfo",
        ".ogg",
        ".opus",
        ".pdf",
        ".png",
        ".rtf",
        ".sfv",
        ".svg",
        ".txt",
        ".wav",
        ".webm",
        ".webp",
        ".xml",
        ".yaml",
        ".yml",
    }
)


class RomInventoryError(RuntimeError):
    """The requested metadata inventory cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class BatoceraSystem:
    system: str
    fullname: str
    path_name: str
    extensions: tuple[str, ...]
    default_emulator: str | None
    default_core: str | None
    group: str = ""


@dataclass(frozen=True, slots=True)
class DirectoryMatch:
    status: str
    system: BatoceraSystem | None
    candidates: tuple[str, ...] = ()


@dataclass(slots=True)
class DirectoryAggregate:
    file_count: int = 0
    directory_count: int = 0
    total_bytes: int = 0
    symlink_count: int = 0
    extensions: Counter[str] = field(default_factory=Counter)
    special_layouts: Counter[str] = field(default_factory=Counter)
    _ps3_roots: set[Path] = field(default_factory=set, repr=False)

    def as_json(self) -> dict[str, Any]:
        return {
            "file_count": self.file_count,
            "directory_count": self.directory_count,
            "total_bytes": self.total_bytes,
            "symlink_count": self.symlink_count,
            "extensions": dict(sorted(self.extensions.items())),
            "special_layouts": dict(sorted(self.special_layouts.items())),
        }


def _normalized_extension(name: str) -> str:
    suffix = Path(name).suffix.casefold()
    return suffix if suffix else "<none>"


def load_batocera_systems(path: Path) -> tuple[BatoceraSystem, ...]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        raise RomInventoryError(f"Batocera system definition is unavailable: {path}") from error

    systems: list[BatoceraSystem] = []
    for element in root.findall("system"):
        system_id = (element.findtext("name") or "").strip()
        fullname = (element.findtext("fullname") or system_id).strip()
        if not system_id:
            continue
        configured_path = (element.findtext("path") or system_id).rstrip("/")
        path_name = Path(configured_path).name if configured_path else system_id
        extensions = tuple(
            sorted(
                {
                    value.casefold() if value.startswith(".") else f".{value.casefold()}"
                    for value in (element.findtext("extension") or "").split()
                    if value
                }
            )
        )
        default_emulator: str | None = None
        default_core: str | None = None
        for emulator in element.findall("./emulators/emulator"):
            for core in emulator.findall("./cores/core"):
                if core.get("default") == "true":
                    default_emulator = emulator.get("name")
                    default_core = (core.text or "").strip() or None
                    break
            if default_core is not None:
                break
        systems.append(
            BatoceraSystem(
                system_id,
                fullname,
                path_name,
                extensions,
                default_emulator,
                default_core,
                (element.findtext("group") or "").strip(),
            )
        )
    if not systems:
        raise RomInventoryError(f"Batocera system definition contains no systems: {path}")
    return tuple(sorted(systems, key=lambda item: item.system))


class SystemMatcher:
    def __init__(
        self,
        systems: Iterable[BatoceraSystem],
        aliases: Mapping[str, str] | None = None,
        ambiguous_aliases: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        self.systems = {system.system: system for system in systems}
        self.aliases = {name.casefold(): system for name, system in (aliases or {}).items()}
        self.ambiguous_aliases = {
            name.casefold(): tuple(candidates)
            for name, candidates in (ambiguous_aliases or {}).items()
        }
        unknown_aliases = sorted(set(self.aliases.values()) - set(self.systems))
        unknown_ambiguous = sorted(
            {
                candidate
                for candidates in self.ambiguous_aliases.values()
                for candidate in candidates
            }
            - set(self.systems)
        )
        if unknown_aliases or unknown_ambiguous:
            raise RomInventoryError(
                "Directory aliases reference unknown Batocera systems: "
                + ", ".join(sorted(set(unknown_aliases + unknown_ambiguous)))
            )
        self._ids_casefold: dict[str, list[str]] = defaultdict(list)
        self._paths_casefold: dict[str, list[str]] = defaultdict(list)
        for system in self.systems.values():
            self._ids_casefold[system.system.casefold()].append(system.system)
            self._paths_casefold[system.path_name.casefold()].append(system.system)

    def match(self, directory_name: str) -> DirectoryMatch:
        if system := self.systems.get(directory_name):
            return DirectoryMatch("EXACT", system)
        if alias_id := self.aliases.get(directory_name.casefold()):
            return DirectoryMatch("ALIAS", self.systems[alias_id])
        if candidates := self.ambiguous_aliases.get(directory_name.casefold()):
            return DirectoryMatch("AMBIGUOUS", None, tuple(sorted(set(candidates))))

        candidates = set(self._ids_casefold.get(directory_name.casefold(), ()))
        candidates.update(self._paths_casefold.get(directory_name.casefold(), ()))
        if len(candidates) == 1:
            system_id = next(iter(candidates))
            return DirectoryMatch("ALIAS", self.systems[system_id])
        if candidates:
            return DirectoryMatch("AMBIGUOUS", None, tuple(sorted(candidates)))
        return DirectoryMatch("UNKNOWN", None)


def _scan_directory(root: Path, match: DirectoryMatch) -> DirectoryAggregate:
    aggregate = DirectoryAggregate()
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                    except OSError as error:
                        raise RomInventoryError(f"Cannot read metadata for {entry.path}: {error}") from error
                    mode = metadata.st_mode
                    if stat.S_ISLNK(mode):
                        aggregate.symlink_count += 1
                        continue
                    if stat.S_ISDIR(mode):
                        aggregate.directory_count += 1
                        entry_path = Path(entry.path)
                        stack.append(entry_path)
                        if match.system is not None and match.system.system == "ps3":
                            if entry.name.casefold().endswith(".ps3"):
                                aggregate._ps3_roots.add(entry_path)
                            if entry.name.casefold() == "ps3_game":
                                aggregate._ps3_roots.add(entry_path.parent)
                        continue
                    if not stat.S_ISREG(mode):
                        continue
                    aggregate.file_count += 1
                    aggregate.total_bytes += metadata.st_size
                    extension = _normalized_extension(entry.name)
                    aggregate.extensions[extension] += 1
                    if extension == ".m3u":
                        aggregate.special_layouts["multi_disc_m3u_files"] += 1
                    elif extension == ".chd":
                        aggregate.special_layouts["chd_files"] += 1
                    elif extension == ".cue":
                        aggregate.special_layouts["cue_files"] += 1
                    elif extension == ".bin":
                        aggregate.special_layouts["bin_files"] += 1
        except OSError as error:
            raise RomInventoryError(f"Cannot enumerate directory {directory}: {error}") from error
    if aggregate._ps3_roots:
        aggregate.special_layouts["ps3_game_directories"] = len(aggregate._ps3_roots)
    return aggregate


def _extension_status(
    aggregate: DirectoryAggregate,
    system: BatoceraSystem | None,
) -> tuple[str, int, int, int]:
    companion = sum(
        count
        for extension, count in aggregate.extensions.items()
        if extension in COMPANION_EXTENSIONS
    )
    if system is None:
        return "UNKNOWN", 0, aggregate.file_count, companion
    accepted = set(system.extensions)
    recognized = sum(count for extension, count in aggregate.extensions.items() if extension in accepted)
    unrecognized = aggregate.file_count - recognized
    structured = aggregate.special_layouts.get("ps3_game_directories", 0)
    if recognized or structured:
        status = "RECOGNIZED" if unrecognized == 0 else "MIXED"
    else:
        status = "UNRECOGNIZED"
    return status, recognized, unrecognized, companion


def _content_status(
    aggregate: DirectoryAggregate,
    recognized: int,
) -> str:
    structured = aggregate.special_layouts.get("ps3_game_directories", 0)
    if aggregate.file_count == 0 and aggregate.directory_count == 0:
        return "EMPTY"
    if structured:
        return "SPECIAL_LAYOUT_PRESENT"
    if recognized:
        return "ROM_PRESENT"
    companion = sum(
        count
        for extension, count in aggregate.extensions.items()
        if extension in COMPANION_EXTENSIONS
    )
    if aggregate.file_count and aggregate.file_count == companion:
        return "COMPANION_ONLY"
    return "UNCLASSIFIED_CONTENT"


def inventory_rom_root(
    root: Path,
    systems: Iterable[BatoceraSystem],
    *,
    aliases: Mapping[str, str] | None = None,
    ambiguous_aliases: Mapping[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    root = root.expanduser().absolute()
    if not root.is_dir() or not os.access(root, os.R_OK | os.X_OK):
        raise RomInventoryError(f"ROM root is not a readable directory: {root}")
    matcher = SystemMatcher(systems, aliases, ambiguous_aliases)
    try:
        with os.scandir(root) as entries:
            top_level = sorted(
                (Path(entry.path) for entry in entries if entry.is_dir(follow_symlinks=False)),
                key=lambda path: path.name.casefold(),
            )
    except OSError as error:
        raise RomInventoryError(f"Cannot enumerate ROM root {root}: {error}") from error

    results: list[dict[str, Any]] = []
    for directory in top_level:
        match = matcher.match(directory.name)
        aggregate = _scan_directory(directory, match)
        extension_status, recognized, unrecognized, companion = _extension_status(
            aggregate, match.system
        )
        row: dict[str, Any] = {
            "directory": directory.name,
            "path": str(directory),
            "match": match.status,
            "system": match.system.system if match.system is not None else None,
            "fullname": match.system.fullname if match.system is not None else None,
            "candidates": list(match.candidates),
            **aggregate.as_json(),
            "batocera_extensions": list(match.system.extensions) if match.system is not None else [],
            "default_emulator": match.system.default_emulator if match.system is not None else None,
            "default_core": match.system.default_core if match.system is not None else None,
            "extension_match": extension_status,
            "content_status": _content_status(aggregate, recognized),
            "recognized_count": recognized,
            "unrecognized_count": unrecognized,
            "companion_count": companion,
        }
        results.append(row)

    match_counts = Counter(row["match"] for row in results)
    return {
        "schema_version": 3,
        "batocera_commit": BATOCERA_COMMIT,
        "rom_root": str(root),
        "summary": {
            "top_level_directories": len(results),
            "exact": match_counts["EXACT"],
            "alias": match_counts["ALIAS"],
            "ambiguous": match_counts["AMBIGUOUS"],
            "unknown": match_counts["UNKNOWN"],
            "files": sum(row["file_count"] for row in results),
            "directories": sum(row["directory_count"] for row in results),
            "total_bytes": sum(row["total_bytes"] for row in results),
            "empty": sum(row["content_status"] == "EMPTY" for row in results),
            "rom_present": sum(
                row["content_status"] == "ROM_PRESENT" for row in results
            ),
            "special_layout_present": sum(
                row["content_status"] == "SPECIAL_LAYOUT_PRESENT" for row in results
            ),
            "companion_only": sum(
                row["content_status"] == "COMPANION_ONLY" for row in results
            ),
            "unclassified_content": sum(
                row["content_status"] == "UNCLASSIFIED_CONTENT" for row in results
            ),
        },
        "systems": results,
    }


def write_inventory(path: Path, inventory: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(size) < 1024 or unit == "PiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def _extension_summary(extensions: Mapping[str, int], *, limit: int = 6) -> str:
    ordered = sorted(extensions.items(), key=lambda item: (-item[1], item[0]))
    values = [f"{extension} ({count})" for extension, count in ordered[:limit]]
    if len(ordered) > limit:
        values.append(f"+{len(ordered) - limit} more")
    return ", ".join(values) if values else "—"


def render_documentation(inventory: Mapping[str, Any]) -> str:
    summary = inventory["summary"]
    rows = inventory["systems"]
    content_counts = Counter(row["content_status"] for row in rows)
    recognized_files = sum(row["recognized_count"] for row in rows)
    unrecognized_files = sum(row["unrecognized_count"] for row in rows)
    unique_extensions = len(
        {extension for row in rows for extension in row["extensions"]}
    )
    lines = [
        "# ROM system inventory",
        "",
        f"Reference: pinned Batocera `{inventory['batocera_commit']}`.",
        "",
        "This is a metadata-only snapshot. No ROM contents were read, hashed, mounted,",
        "extracted, or started. Counts are filesystem entries and must not be interpreted",
        "as verified game counts. `ROM_ROOT` denotes the host-configured collection root.",
        "",
        "## Summary",
        "",
        f"- Top-level directories: {summary['top_level_directories']}",
        f"- Exact Batocera mappings: {summary['exact']}",
        f"- Alias mappings: {summary['alias']}",
        f"- Ambiguous mappings: {summary['ambiguous']}",
        f"- Unknown directories: {summary['unknown']}",
        f"- Regular files: {summary['files']}",
        f"- Empty top-level directories: {summary['empty']}",
        f"- Directories containing recognized ROM files: {content_counts['ROM_PRESENT']}",
        "- Directories containing recognized special layouts: "
        f"{content_counts['SPECIAL_LAYOUT_PRESENT']}",
        f"- Directories containing only companion files: {content_counts['COMPANION_ONLY']}",
        f"- Directories with unclassified content: {content_counts['UNCLASSIFIED_CONTENT']}",
        f"- Batocera-recognized file entries: {recognized_files}",
        f"- Other file entries: {unrecognized_files}",
        f"- Distinct normalized extensions: {unique_extensions}",
        f"- Aggregate file size: {_human_size(summary['total_bytes'])}",
        "",
        "## Folder occupancy",
        "",
        "`EMPTY` means that no regular file or subdirectory was found. "
        "`COMPANION_ONLY` means that every file has a known metadata, documentation, "
        "artwork, or media extension (for example `.txt`, `.xml`, `.png`, or `.mp4`; "
        "filenames are not interpreted). `ROM_PRESENT` means that at least one filename "
        "extension accepted by the matched Batocera system was found. "
        "`SPECIAL_LAYOUT_PRESENT` means that a recognized directory-based layout was found "
        "(currently PS3 game directories). `UNCLASSIFIED_CONTENT` means that other files or "
        "subdirectories exist without a safe classification; "
        "it does not prove that the folder contains no games, especially for unknown or "
        "ambiguous systems.",
        "",
        "### Empty top-level directories",
        "",
    ]
    empty_rows = [row for row in rows if row["content_status"] == "EMPTY"]
    lines.extend(
        (f"- `ROM_ROOT/{row['directory']}`" for row in empty_rows)
        if empty_rows
        else ["None."]
    )
    lines.extend(["", "### Directories with recognized ROM files", ""])
    recognized_rows = [
        row for row in rows if row["content_status"] == "ROM_PRESENT"
    ]
    lines.append(
        ", ".join(f"`{row['directory']}`" for row in recognized_rows)
        if recognized_rows
        else "None."
    )
    lines.extend(["", "### Directories with recognized special layouts", ""])
    special_layout_rows = [
        row for row in rows if row["content_status"] == "SPECIAL_LAYOUT_PRESENT"
    ]
    lines.append(
        ", ".join(f"`{row['directory']}`" for row in special_layout_rows)
        if special_layout_rows
        else "None."
    )
    lines.extend(["", "### Directories with unclassified content", ""])
    unclassified_rows = [
        row for row in rows if row["content_status"] == "UNCLASSIFIED_CONTENT"
    ]
    lines.extend(
        (
            f"- `ROM_ROOT/{row['directory']}`: "
            f"{_extension_summary(row['extensions'], limit=12)} ({row['match']})"
            for row in unclassified_rows
        )
        if unclassified_rows
        else ["None."]
    )
    lines.extend(
        [
            "",
            "All remaining occupancy results are listed per folder in the collection table.",
            "",
            "## Collection overview",
            "",
            "| Batocera system | Collection path | Content | Files / structured dirs* | Size | Extensions | Match |",
            "|---|---|---|---:|---:|---|---|",
        ]
    )
    for row in rows:
        system = row["system"] or "—"
        structured = row["special_layouts"].get("ps3_game_directories", 0)
        count = f"{row['file_count']} / {structured}"
        match = f"{row['match']} · {row['extension_match']}"
        lines.append(
            f"| {system} | `ROM_ROOT/{row['directory']}` | {row['content_status']} | {count} | "
            f"{_human_size(row['total_bytes'])} | {_extension_summary(row['extensions'])} | {match} |"
        )
    lines.extend(
        [
            "",
            "\\* The second number is a recognized directory-based structure count where",
            "available (currently PS3-style game directories), not a verified game count.",
            "",
            "## Unknown top-level directories",
            "",
        ]
    )
    unknown = [row["directory"] for row in rows if row["match"] == "UNKNOWN"]
    lines.extend((f"- `{name}`" for name in unknown) if unknown else ["None."])
    lines.extend(["", "## Ambiguous mappings", ""])
    ambiguous = [row for row in rows if row["match"] == "AMBIGUOUS"]
    lines.extend(
        (
            f"- `{row['directory']}`: {', '.join(f'`{item}`' for item in row['candidates'])}"
            for row in ambiguous
        )
        if ambiguous
        else ["None."]
    )
    lines.extend(["", "## Unrecognized extensions", ""])
    unrecognized_rows = []
    for row in rows:
        if row["system"] is None:
            continue
        accepted = set(row["batocera_extensions"])
        unknown_extensions = {
            extension: count
            for extension, count in row["extensions"].items()
            if extension not in accepted
        }
        if unknown_extensions:
            unrecognized_rows.append(
                f"- `ROM_ROOT/{row['directory']}` (`{row['system']}`): "
                f"{_extension_summary(unknown_extensions, limit=12)}"
            )
    lines.extend(unrecognized_rows or ["None."])
    lines.extend(["", "## Batocera system directories matched", ""])
    present = sorted({row["system"] for row in rows if row["system"] is not None})
    lines.append(", ".join(f"`{system}`" for system in present) if present else "None.")
    lines.extend(["", "## Notable special layouts", ""])
    special_rows = []
    for row in rows:
        layouts = row["special_layouts"]
        if layouts:
            special_rows.append(
                f"- `ROM_ROOT/{row['directory']}`: "
                + ", ".join(f"{name}={count}" for name, count in sorted(layouts.items()))
            )
    lines.extend(special_rows or ["No special layout markers detected from names and structure."])
    lines.extend(
        [
            "",
            "This document intentionally makes no READY, missing-core, missing-emulator,",
            "or missing-BIOS determination.",
            "",
        ]
    )
    return "\n".join(lines)


def write_documentation(path: Path, inventory: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_documentation(inventory), encoding="utf-8")

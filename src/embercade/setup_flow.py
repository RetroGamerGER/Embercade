"""Terminal first-run configuration with conservative, atomic TOML updates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, TextIO
import json
import os
import stat
import tempfile
import tomllib

from embercade.runtime import load_config, executable_config, emulator_provider_config
from embercade.exit_hotkey import DEFAULT_EXIT_HOTKEY, EXIT_HOTKEYS, resolve_exit_hotkey
from embercade.executables import ExecutableResolver, ExecutableResolutionError, ProviderType
from embercade.imports import ImportError as ManagedImportError, inspect_provider, provider_candidates
from embercade.ppsspp import PpssppAssetsError, validate_ppsspp_assets


class SetupError(RuntimeError):
    """The requested first-run configuration is invalid or unsafe."""


@dataclass(frozen=True, slots=True)
class SetupResult:
    config_path: Path
    roms: Path
    bios: Path
    xenia_edge: Path | None
    exit_hotkey: str
    provider_notice: str | None = None


def validate_collection_path(value: str, label: str) -> Path:
    if not value.strip():
        raise SetupError(f"{label} directory is required")
    path = Path(value).expanduser().absolute()
    if not path.exists():
        raise SetupError(f"{label} directory does not exist: {path}")
    if not path.is_dir():
        raise SetupError(f"{label} path is not a directory: {path}")
    if not os.access(path, os.R_OK | os.X_OK):
        raise SetupError(f"{label} directory is not readable/searchable: {path}")
    return path


def choose_source_directory(
    *,
    label: str,
    suggested: Path | None,
    question: str,
    input_function: Callable[[str], str] = input,
    output: TextIO,
) -> Path | None:
    """Let a person accept discovery, choose a different source, or skip."""
    if suggested is not None:
        print(f"Existing {label} found:\n  {suggested}", file=output)
        print("  1. Use detected directory", file=output)
        print("  2. Choose another directory", file=output)
        print("  3. Skip import", file=output)
        while True:
            choice = input_function("Choose [3]: ").strip() or "3"
            if choice == "1":
                try:
                    return validate_collection_path(str(suggested), label)
                except SetupError as error:
                    print(f"  {error}", file=output)
                    break
            if choice == "2":
                break
            if choice == "3":
                return None
            print("  Choose 1, 2 or 3.", file=output)
    elif input_function(f"{question} [y/N] ").strip().casefold() not in {"y", "yes"}:
        return None
    while True:
        answer = input_function(f"{label} source directory (Enter to skip): ").strip()
        if not answer:
            return None
        try:
            return validate_collection_path(answer, label)
        except SetupError as error:
            print(f"  {error}", file=output)


def validate_provider_path(value: str) -> Path:
    try:
        return inspect_provider(Path(value), require_executable=True)
    except ManagedImportError as error:
        raise SetupError(f"Xenia Edge provider needs attention: {error}") from error


def recommended_xenia_directory(
    environment: Mapping[str, str] | None = None,
) -> Path:
    env = os.environ if environment is None else environment
    home = Path(env.get("HOME", str(Path.home()))).expanduser().absolute()
    data_home = Path(env.get("XDG_DATA_HOME", home / ".local/share")).expanduser().absolute()
    return data_home / "embercade" / "providers" / "xenia"


def detect_xenia_edge(
    config: Mapping[str, object], environment: Mapping[str, str] | None = None
) -> Path | None:
    env = os.environ if environment is None else environment
    try:
        overrides = executable_config(config)
        providers = emulator_provider_config(config)
    except ValueError as error:
        raise SetupError(f"Configured Xenia Edge provider needs attention: {error}") from error
    resolver = ExecutableResolver(overrides, providers=providers, environment=env)
    if overrides.get("xenia-edge") or "xenia-edge" in providers:
        try:
            resolved = resolver.resolve("xenia-edge")
        except ExecutableResolutionError as error:
            raise SetupError(f"Configured Xenia Edge provider needs attention: {error}") from error
        if resolved.provider_type is ProviderType.APPIMAGE or resolved.path.suffix.casefold() == ".appimage":
            return validate_provider_path(str(resolved.path))
        return resolved.path  # preserve existing native/explicit resolver semantics
    provider_directory = recommended_xenia_directory(env)
    if provider_directory.exists() or provider_directory.is_symlink():
        try:
            candidates, _skipped, _found = provider_candidates(provider_directory, require_executable=True)
        except ManagedImportError as error:
            raise SetupError(str(error)) from error
        if len(candidates) > 1:
            raise SetupError("Multiple different Xenia Edge AppImages found; choose one explicitly.")
        if candidates:
            return next(iter(candidates.values()))
    try:
        return resolver.resolve("xenia-edge").path
    except ExecutableResolutionError:
        return None


def _toml_string(value: Path) -> str:
    # JSON string syntax is valid TOML and handles whitespace without shell parsing.
    return json.dumps(str(value), ensure_ascii=False)


def _replace_table_values(text: str, table: str, values: Mapping[str, str]) -> str:
    lines = text.splitlines()
    header = f"[{table}]"
    start: int | None = None
    end = len(lines)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == header:
            start = index
            continue
        if start is not None and index > start and stripped.startswith("[") and stripped.endswith("]"):
            end = index
            break
    assignments = {key: f"{key} = {value}" for key, value in values.items()}
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(header)
        lines.extend(assignments.values())
        return "\n".join(lines) + "\n"

    found: set[str] = set()
    for index in range(start + 1, end):
        stripped = lines[index].lstrip()
        if stripped.startswith("#"):
            continue
        for key, assignment in assignments.items():
            if stripped.startswith(f"{key} ") or stripped.startswith(f"{key}="):
                lines[index] = assignment
                found.add(key)
                break
    lines[end:end] = [assignments[key] for key in values if key not in found]
    return "\n".join(lines) + "\n"


def update_config_text(
    original: str,
    *,
    roms: Path,
    bios: Path,
    xenia_edge: Path | None,
    exit_hotkey: str = DEFAULT_EXIT_HOTKEY,
    ppsspp_assets: Path | None = None,
    shadps4: Path | None = None,
) -> str:
    text = _replace_table_values(
        original,
        "paths",
        {"roms": _toml_string(roms), "bios": _toml_string(bios)},
    )
    if xenia_edge is not None:
        text = _replace_table_values(
            text,
            "emulators.xenia-edge",
            {"provider": json.dumps("appimage"), "executable": _toml_string(xenia_edge)},
        )
    if shadps4 is not None:
        text = _replace_table_values(
            text, "emulators.shadps4",
            {"provider": json.dumps("appimage"), "executable": _toml_string(shadps4)},
        )
    if exit_hotkey not in EXIT_HOTKEYS:
        raise SetupError(f"unknown exit-hotkey preset: {exit_hotkey}")
    text = _replace_table_values(
        text,
        "controller",
        {"exit_hotkey": json.dumps(exit_hotkey)},
    )
    if ppsspp_assets is not None:
        text = _replace_table_values(
            text, "libretro", {"ppsspp_assets": _toml_string(ppsspp_assets)}
        )
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise SetupError(f"generated configuration is invalid: {error}") from error
    if not isinstance(parsed, dict):
        raise SetupError("generated configuration has no TOML table root")
    return text


def write_config_atomic(path: Path, text: str) -> None:
    if path.is_symlink():
        raise SetupError(f"refusing to replace symlinked configuration: {path}")
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise SetupError(f"configuration directory is unsafe: {path.parent}")
    descriptor, raw = tempfile.mkstemp(prefix=".embercade.toml.", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(stat.S_IRUSR | stat.S_IWUSR)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def configure(
    config_path: Path,
    *,
    roms_value: str,
    bios_value: str,
    xenia_value: str | None = None,
    exit_hotkey: str | None = None,
    ppsspp_assets_value: str | None = None,
    shadps4_value: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> SetupResult:
    if config_path.exists() and (config_path.is_symlink() or not config_path.is_file()):
        raise SetupError(f"configuration is not a regular file: {config_path}")
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    try:
        current = load_config(config_path)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        raise SetupError(f"existing configuration is invalid: {error}") from error
    roms = validate_collection_path(roms_value, "ROM")
    bios = validate_collection_path(bios_value, "BIOS")
    shadps4 = None
    if shadps4_value:
        try:
            shadps4 = inspect_provider(Path(shadps4_value), require_executable=True, provider="shadps4")
        except ManagedImportError as error:
            raise SetupError(f"shadPS4 needs attention: {error}") from error
        if executable_config(current).get("shadps4"):
            raise SetupError("An explicit shadPS4 override has priority; change it explicitly before selecting an AppImage.")
    try:
        ppsspp_assets = (
            validate_ppsspp_assets(Path(ppsspp_assets_value))
            if ppsspp_assets_value is not None else None
        )
    except PpssppAssetsError as error:
        raise SetupError(str(error)) from error
    notice = None
    if xenia_value:
        xenia = validate_provider_path(xenia_value)
        override = executable_config(current).get("xenia-edge")
        if override and Path(override).expanduser().absolute() != xenia:
            raise SetupError("An explicit Xenia Edge override has priority; change it explicitly before selecting another provider.")
    else:
        try:
            xenia = detect_xenia_edge(current, environment)
        except SetupError as error:
            # Optional provider damage does not prevent ROM/BIOS setup; retain
            # its configured path for diagnosis and allow a deliberate import.
            xenia, notice = None, str(error)
    if exit_hotkey is None:
        try:
            exit_hotkey = resolve_exit_hotkey(current).key
        except ValueError:
            exit_hotkey = DEFAULT_EXIT_HOTKEY
    text = update_config_text(
        original,
        roms=roms,
        bios=bios,
        xenia_edge=xenia if xenia and xenia.suffix.casefold() == ".appimage" else None,
        exit_hotkey=exit_hotkey,
        ppsspp_assets=ppsspp_assets,
        shadps4=shadps4,
    )
    write_config_atomic(config_path, text)
    return SetupResult(config_path, roms, bios, xenia, exit_hotkey, notice)


def interactive_setup(
    config_path: Path,
    *,
    input_function: Callable[[str], str] = input,
    output: TextIO,
    environment: Mapping[str, str] | None = None,
) -> SetupResult:
    try:
        current = load_config(config_path)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        raise SetupError(f"existing configuration is invalid: {error}") from error
    paths = current.get("paths", {}) if isinstance(current.get("paths", {}), Mapping) else {}
    rom_default = paths.get("roms", "") if isinstance(paths.get("roms", ""), str) else ""
    bios_default = paths.get("bios", "") if isinstance(paths.get("bios", ""), str) else ""

    def ask_path(label: str, default: str) -> str:
        while True:
            suffix = f" [{default}]" if default else ""
            answer = input_function(f"{label} directory{suffix}: ").strip() or default
            try:
                return str(validate_collection_path(answer, label))
            except SetupError as error:
                print(f"  {error}", file=output)

    print("Embercade first-run setup", file=output)
    print("Your game and BIOS folders will only be referenced, never copied or changed.", file=output)
    roms = ask_path("ROM", rom_default)
    bios = ask_path("BIOS", bios_default)
    try:
        current_hotkey = resolve_exit_hotkey(current).key
    except ValueError:
        current_hotkey = DEFAULT_EXIT_HOTKEY
    print("Exit hotkey:", file=output)
    print("  1. Back/Select + Start (recommended for SteamOS/handheld sessions)", file=output)
    print("  2. Guide + Start (recommended for desktop sessions)", file=output)
    default_choice = "2" if current_hotkey == "guide-start" else "1"
    while True:
        choice = input_function(f"Choose exit hotkey [{default_choice}]: ").strip() or default_choice
        if choice in {"1", "back-start"}:
            exit_hotkey = "back-start"
            break
        if choice in {"2", "guide-start"}:
            exit_hotkey = "guide-start"
            break
        print("  Choose 1 or 2.", file=output)
    try:
        detected = detect_xenia_edge(current, environment)
    except SetupError:
        detected = None
        print("Xenia Edge needs attention. Existing settings will be kept; you can select an import folder next.", file=output)
    if detected:
        print("Xenia Edge found.", file=output)
        xenia = str(detected) if detected.suffix.casefold() == ".appimage" else ""
    else:
        xenia = ""
    return configure(
        config_path,
        roms_value=roms,
        bios_value=bios,
        xenia_value=xenia,
        exit_hotkey=exit_hotkey,
        environment=environment,
    )

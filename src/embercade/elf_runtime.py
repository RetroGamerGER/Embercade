"""Read-only ELF runtime-closure checks for the production frontend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence
import os
import re
import subprocess


FRONTEND_BUNDLED_SONAMES = frozenset(
    {
        "libfreeimage.so.3",
        "libSDL2_mixer-2.0.so.0",
    }
)
FRONTEND_HOST_SONAMES = frozenset(
    {
        "libfreetype.so.6",
        "libfribidi.so.0",
        "libSDL2-2.0.so.0",
        "libcurl.so.4",
        "libvlc.so.5",
        "libudev.so.1",
        "libasound.so.2",
        "libGL.so.1",
        "libGLU.so.1",
        "libpugixml.so.1",
        "libstdc++.so.6",
        "libm.so.6",
        "libgcc_s.so.1",
        "libc.so.6",
    }
)


@dataclass(frozen=True, slots=True)
class ElfRuntimeClosure:
    resolved: tuple[tuple[str, Path], ...]
    missing: tuple[str, ...]
    error: str | None = None

    @property
    def healthy(self) -> bool:
        return self.error is None and not self.missing

    def resolved_path(self, soname: str) -> Path | None:
        return dict(self.resolved).get(soname)


@dataclass(frozen=True, slots=True)
class FrontendRuntimeReport:
    closure: ElfRuntimeClosure
    direct_sonames: tuple[str, ...]
    failures: tuple[str, ...]

    @property
    def healthy(self) -> bool:
        return not self.failures


Runner = Callable[..., subprocess.CompletedProcess[str]]


def inspect_elf_runtime(
    binary: Path,
    library_directories: Sequence[Path] = (),
    *,
    runner: Runner = subprocess.run,
    environment: Mapping[str, str] | None = None,
) -> ElfRuntimeClosure:
    if not binary.is_file():
        return ElfRuntimeClosure((), (), f"ELF binary is missing: {binary}")
    env = dict(os.environ if environment is None else environment)
    if library_directories:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(
            str(path.absolute()) for path in library_directories
        )
    else:
        env.pop("LD_LIBRARY_PATH", None)
    try:
        completed = runner(
            ["ldd", "--", str(binary)],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    except OSError as error:
        return ElfRuntimeClosure((), (), f"cannot execute ldd: {error}")
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    missing: set[str] = set()
    resolved: dict[str, Path] = {}
    for line in output.splitlines():
        if match := re.match(r"^\s*(\S+)\s+=>\s+not found\s*$", line):
            missing.add(match.group(1))
            continue
        if match := re.match(
            r"^\s*(\S+)\s+=>\s+(.+?)\s+\(0x[0-9a-fA-F]+\)\s*$",
            line,
        ):
            resolved[match.group(1)] = Path(match.group(2))
    error = None
    if completed.returncode != 0:
        detail = next((line.strip() for line in output.splitlines() if line.strip()), "")
        error = f"ldd failed with exit code {completed.returncode}: {detail}"
    return ElfRuntimeClosure(
        tuple(sorted(resolved.items())),
        tuple(sorted(missing)),
        error,
    )


def direct_elf_sonames(
    binary: Path,
    *,
    runner: Runner = subprocess.run,
) -> tuple[tuple[str, ...], str | None]:
    try:
        completed = runner(
            ["readelf", "-d", str(binary)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        return (), f"cannot execute readelf: {error}"
    if completed.returncode != 0:
        detail = next(
            (line.strip() for line in completed.stderr.splitlines() if line.strip()), ""
        )
        return (), f"readelf failed with exit code {completed.returncode}: {detail}"
    sonames = {
        match.group(1)
        for line in completed.stdout.splitlines()
        if (match := re.search(r"\(NEEDED\).*Shared library: \[(.+)]", line))
    }
    return tuple(sorted(sonames)), None


def nonbaseline_x86_isa_requirements(
    binary: Path,
    *,
    runner: Runner = subprocess.run,
) -> tuple[tuple[str, ...], str | None]:
    try:
        completed = runner(
            ["readelf", "-n", str(binary)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        return (), f"cannot inspect frontend CPU ISA: {error}"
    if completed.returncode != 0:
        detail = next(
            (line.strip() for line in completed.stderr.splitlines() if line.strip()), ""
        )
        return (), f"frontend CPU ISA inspection failed with exit code {completed.returncode}: {detail}"
    required: set[str] = set()
    for line in completed.stdout.splitlines():
        if "x86 ISA needed:" in line:
            required.update(re.findall(r"x86-64-v[234]", line))
    return tuple(sorted(required)), None


def inspect_frontend_runtime(
    binary: Path,
    library_root: Path,
    *,
    runner: Runner = subprocess.run,
    environment: Mapping[str, str] | None = None,
) -> FrontendRuntimeReport:
    closure = inspect_elf_runtime(
        binary,
        (library_root,),
        runner=runner,
        environment=environment,
    )
    direct, direct_error = direct_elf_sonames(binary, runner=runner)
    isa_requirements, isa_error = nonbaseline_x86_isa_requirements(
        binary,
        runner=runner,
    )
    failures: list[str] = []
    if closure.error:
        failures.append(closure.error)
    if closure.missing:
        failures.append("frontend shared libraries missing: " + ", ".join(closure.missing))
    if direct_error:
        failures.append(direct_error)
    if isa_error:
        failures.append(isa_error)
    if isa_requirements:
        failures.append(
            "frontend requires nonbaseline CPU ISA: " + ", ".join(isa_requirements)
        )
    classified = FRONTEND_BUNDLED_SONAMES | FRONTEND_HOST_SONAMES
    unknown = sorted(set(direct) - classified)
    if unknown:
        failures.append("unclassified frontend shared libraries: " + ", ".join(unknown))
    absent_contract = sorted(FRONTEND_BUNDLED_SONAMES - set(direct))
    if absent_contract:
        failures.append("expected bundled frontend dependencies absent: " + ", ".join(absent_contract))
    library_root_resolved = library_root.resolve()
    for soname in sorted(FRONTEND_BUNDLED_SONAMES & set(direct)):
        resolved = closure.resolved_path(soname)
        if resolved is None or not resolved.resolve().is_relative_to(library_root_resolved):
            failures.append(f"bundled frontend dependency escaped payload: {soname}")
    return FrontendRuntimeReport(closure, direct, tuple(failures))

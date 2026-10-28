#!/usr/bin/env python3
# Copyright (c) 2026 Embercade contributors
# SPDX-License-Identifier: MIT
"""Standalone Batocera API backend. Never import the Embercade client package."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib
import json
from pathlib import Path
import platform
import sys


RUNTIME_IMPORTS = (
    ("batocera-common", "batocera_common"),
    ("batocera-launch", "batocera_launch"),
    ("configgen", "configgen"),
    ("configgen.launch", "configgen.launch"),
    ("libretro generator", "configgen.generators.libretro.libretroGenerator"),
    ("Dolphin generator", "batocera_launch_dolphin"),
    ("PCSX2 generator", "batocera_launch_pcsx2"),
    ("RPCS3 generator", "batocera_launch_rpcs3"),
    ("Xemu generator", "batocera_launch.emulators.xemu"),
    ("Xenia Edge generator", "batocera_launch.emulators.xenia_edge"),
    ("shadPS4 generator", "batocera_launch.emulators.shadps4"),
)


def load_configuration(system: str, rom: str):
    from batocera_launch.cli.arguments import Arguments
    from batocera_launch.config.config import SystemConfig

    args = Arguments(
        system=system, rom=Path(rom), emulator=None, core=None,
        players=(None,) * 8, netplaymode=None, netplaypass=None,
        netplayip=None, netplayport=None, netplaysession=None,
        state_slot=None, state_filename=None, autosave=None, systemname=None,
        gameinfoxml=Path('/dev/null'), lightgun=False, wheel=False,
        trackball=False, spinner=False,
    )
    return SystemConfig.load(args)


def resolve_system(system: str, rom: str) -> dict:
    config = load_configuration(system, rom)
    return {
        'system': system, 'emulator': config.emulator, 'core': config.core,
        'emulator_forced': config.emulator_forced, 'core_forced': config.core_forced,
    }


def resolve_decoration(system: str, rom: str) -> dict:
    config = load_configuration(system, rom)
    from batocera_launch.emulator import Emulator
    from batocera_launch.profiler import Profiler

    emulator = Emulator._load_class(config.emulator)(config, Profiler('/dev/null/disabled'))
    emulator.rom = Path(rom)
    files = emulator.bezel_files
    return {
        'emulator': config.emulator,
        'png': str(files.png) if files else None,
        'info': str(files.info) if files else None,
        'options': {key: config.get_str(key, '') for key in (
            'pcsx2_ratio', 'pcsx2_fmv_ratio', 'xemu_aspect', 'xemu_scaling',
            'dolphin_aspect_ratio', 'tv_mode')},
    }


def probe_runtime() -> dict:
    results = {}
    for label, module_name in RUNTIME_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            results[label] = f'{type(error).__name__}: {error}'
        else:
            results[label] = None
    return {'python': platform.python_version(), 'imports': results}


def build_ui(args: argparse.Namespace) -> dict:
    # Only the pinned builder source is added, never Embercade's src directory.
    builder = args.source / 'python-src/batocera-es-system'
    if not (builder / 'batocera_es_system').is_dir():
        raise FileNotFoundError(f'Batocera UI builder is unavailable: {builder}')
    sys.path.insert(0, str(builder.resolve()))
    from batocera_es_system.es_features import build as build_es_features
    from batocera_es_system.es_systems import build as build_es_systems
    from batocera_es_system.registry import Registry
    from batocera_es_system.shared import Defaults

    files = (
        sorted(set(args.source.rglob('*.emulator.yml')) | set(args.source.rglob('*.core.yml')))
        if args.mode == 'complete'
        else [args.source / relative for relative in args.registry]
    )
    registry = Registry.load_files(files)
    args.output.mkdir(parents=True, exist_ok=True)
    build_es_systems(
        registry.get_systems_metadata(Defaults.for_directory(args.defaults)),
        args.source / 'package/batocera/emulationstation/batocera-es-system/es_systems.yml',
        args.output,
    )
    build_es_features(registry, args.output)
    return {'systems': str(args.output / 'es_systems.cfg'),
            'features': str(args.output / 'es_features.cfg')}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=int, choices=(1,), default=1)
    operations = parser.add_subparsers(dest='operation', required=True)
    for name in ('resolve-system', 'resolve-decoration'):
        operation = operations.add_parser(name)
        operation.add_argument('system')
        operation.add_argument('rom')
    operations.add_parser('probe-runtime')
    builder = operations.add_parser('build-ui')
    builder.add_argument('--source', required=True, type=Path)
    builder.add_argument('--defaults', required=True, type=Path)
    builder.add_argument('--output', required=True, type=Path)
    builder.add_argument('--mode', choices=('selected', 'complete'), required=True)
    builder.add_argument('--registry', action='append', default=[])
    args = parser.parse_args(argv)
    # Upstream's builder prints progress. Keep stdout exclusively for JSON.
    with redirect_stdout(sys.stderr):
        if args.operation == 'resolve-system':
            result = resolve_system(args.system, args.rom)
        elif args.operation == 'resolve-decoration':
            result = resolve_decoration(args.system, args.rom)
        elif args.operation == 'probe-runtime':
            result = probe_runtime()
        else:
            result = build_ui(args)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

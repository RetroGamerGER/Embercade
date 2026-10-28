# Copyright (c) 2026 Embercade contributors
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Locate a separately executed backend without importing its Python code."""

from pathlib import Path


def backend_command(python: Path, operation: str, *arguments: str) -> list[str]:
    # Both layouts have two directories between this module and application root:
    # source/src/embercade and installed/share/embercade/app/embercade.
    application = Path(__file__).resolve().parents[2]
    adapter = application / "integration" / "batocera" / "adapter.py"
    return [str(python), "-B", "-I", str(adapter), "--protocol", "1", operation, *arguments]

# Upstream

Machine-readable pins live in `upstream.lock`.

- `batocera.linux`: `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`
- `batocera-emulationstation`: `1750dded8c0fdff70630026f756a69fcad0bb995`
- architecture: `batocera-launch-44`

Both commit objects were verified in the sibling reference repositories without checkout, fetch or reset. Their working trees were clean when this backbone was created. The references are never modified; any future extracted source must be written below Embercade's ignored `.work` directory.

The existing desktop-test binary was built from a different checkout location and contains that old path in its RUNPATH. `scripts/dev-run` deliberately supplies the current read-only dependency directory through `LD_LIBRARY_PATH` instead of modifying or rebuilding the binary.

## Launcher import compatibility

Upstream `batocera-common` declares `requires-python == 3.14.5`, while the host provides Python 3.14.7. Static inspection found no patch-version checks, patch-specific APIs, native source, or Batocera build rule that makes 3.14.5 a technical runtime requirement for these three packages. The exact constraint is treated as Batocera's reproducible image pin, not silently edited.

`scripts/runtime-prepare` installs the unmodified package with pip's explicit `--ignore-requires-python` switch in a disposable development-compatibility Venv. The exception and both versions are recorded in `.work/runtime/runtime-info.txt`. This does not claim upstream support for 3.14.7.

The source trees are produced with `git archive` from the locked Batocera commit. No reference checkout is changed.

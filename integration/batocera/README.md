# Batocera API backend

This independently executable program is the only production Embercade source
that imports Batocera's Python APIs. Its original Embercade implementation is
MIT licensed; [LICENSE](LICENSE) is the complete contribution grant. This
compatible contribution license does not replace the LGPL/GPL terms of the
libraries used by a particular operation.

Run it using the prepared runtime Python with `-B -I`, an absolute script path
and `--protocol 1`. No Embercade package, GUI, daemon or `PYTHONPATH` is needed.

| Operation | Input | Output |
| --- | --- | --- |
| `resolve-system` | System ID, one ROM path; existing scoped environment | Five primitive choice/forced fields |
| `resolve-decoration` | System ID, ROM path; same configuration environment | Emulator, optional PNG/INFO paths and six string options |
| `probe-runtime` | None | Python version and eleven named import results |
| `build-ui` | Pinned source, defaults, output, selected/complete mode and optional registry file list | Raw `es_systems.cfg` and `es_features.cfg`; JSON paths |

Stdout contains only JSON. Upstream progress and errors use stderr. The client
retains XML customization, filesystem validation, graphics/geometry, controller
handling, setup and lifecycle ownership. Configuration priority is still
implemented by the unchanged Batocera APIs. No object graph, executable Python,
callback, private class or pickle crosses the process boundary.

The build-only source insertion points only at the supplied Batocera builder,
not the client source. Runtime operations use the pinned runtime's installed
packages. Packaging installs this directory beside `app`, so execution needs
no development checkout or `.work` directory.

See [component terms](../../docs/BATOCERA_COMPONENT_LICENSES.md) and
[architecture and verification](../../docs/ADAPTER_SEPARATION.md). The
communication contract supports a reasoned separation; the existence of a
process or JSON alone is not a legal exemption.

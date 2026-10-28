# Batocera component licenses

This corrects the older analysis that relied only on the repository's Buildroot
`COPYING`. The official [Batocera licensing policy](https://wiki.batocera.org/license)
specifies LGPLv3 for Batocera-team code unless another upstream license applies.
The existing Buildroot notice remains intact; it cannot be substituted for that
component distinction. Checked on 27 October 2026 against the actual pin below.

Batocera pin: `9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48`.

| Used source/component | Recorded terms and limits |
| --- | --- |
| `python-src/python-batocera-common` | Batocera-team LGPLv3 default; no package-specific contrary license field or code notice found in the targeted pinned check |
| `python-src/batocera-launch` Python package | Same LGPLv3 default; separately marked source files remain exceptions |
| `python-src/batocera-launch-{dolphin,pcsx2,rpcs3}` | Same LGPLv3 default, subject to original upstream-derived portions; no package-specific contrary notice found in the targeted check |
| `python-src/batocera-es-system` builder | Same LGPLv3 default; generated/captured foreign configuration remains foreign data |
| `package/batocera/core/batocera-configgen/configgen` | Explicit `BATOCERA_CONFIGGEN_LICENSE = GPL` in the [pinned package definition](https://github.com/batocera-linux/batocera.linux/blob/9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48/package/batocera/core/batocera-configgen/batocera-configgen.mk). The field specifies no version; do not invent a GPLv3-only or LGPL label for it. Preserve the pinned COPYING and individual source notices. |
| `python-src/batocera-launch/resources/scripts/tdp_hooks.sh` | Explicit GPL version 3 header, retained as an exception. This hook is not present in the inspected Python runtime or current AppImage payload. |
| Batocera EmulationStation | Original MIT notice, Alec Lofquist (2014), at its separate pin `1750dded8c0fdff70630026f756a69fcad0bb995`; nested dependencies retain their own terms |

The package `pyproject.toml` files do not themselves declare license fields.
The LGPL assignments above are based on the team's express default statement
and absence of a contrary notice in these checked package paths, not a new
per-file grant by Embercade. Retain a separately licensed or derived upstream
portion whenever identified; the table is not a license for everything in the
Batocera repository. Only the relevant code paths were examined; no artwork
investigation was repeated.

The backend health operation intentionally loads both legacy Configgen and
modern packages. Concrete generators can also have dependencies with their
own terms. An operation's complete combined scope is therefore not established
just by the name of its first import. Conversely, importing an LGPL library
is not by itself a requirement to license an independent application under GPL.
The relevant LGPL source/replacement requirements still apply when distributing
that library. [GNU's explanation](https://www.gnu.org/licenses/gpl-faq.en.html#IfInterpreterIsGPL)
and [aggregation guidance](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)
explain why communication mechanism and semantics both matter.

Embercade's original adapter and integration contributions use MIT, compatible
with GPL/LGPL, while foreign code/context keeps its original grant. Mixed-target
patches are not labelled wholly GPL or wholly LGPL. The standard LGPLv3 and
GPLv3 texts, the exact Batocera COPYING and original MIT notice are available
under [LICENSES](../LICENSES/README.md). LGPLv3 incorporates GPLv3 terms, so both
texts accompany it. A generic package field does not authorize changing a
foreign file's license or erasing the rights granted by its actual license.

The team's noncommercial project request is recorded respectfully. It is not
an additional restriction imposed by Embercade on upstream GPL/LGPL commercial
permissions. Public distribution must provide the matching covered sources,
modifications, notices and applicable replacement/relinking opportunities;
see [source access](SOURCE_ACCESS.md). No public-source or binary publication
occurred as part of this correction.

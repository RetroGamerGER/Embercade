# Embercade shader resources

New stages provide small mappings for 26 curated effects from the official host
`libretro-shaders-slang` package. They do not embed the full shader/texture tree.
`catalog.toml` retains the 14 existing IDs and adds 12 RetroBat-inspired mappings
using paths verified in the actual official Arch package. The runtime discovers
the installed root (normally `/usr/share/libretro/shaders/shaders_slang`, with
alternative layouts/package file-list discovery), then validates every selected
preset's includes, textures, LUTs and references before populating the menu.

Each frontend session/game launch creates only mappings/aliases in private
runtime state. The package remains read-only, including inside the production
namespace. A missing or incomplete preset disappears from the available menu;
a previously saved choice starts without the unavailable effect and uses the
existing localized launch notice. It is not erased. User shader directories,
manual backend choices and the existing core exceptions remain supported.
Shaders stay **OFF** in fresh profiles (`global.shaderset=none`). Vulkan preference
where supported does not enable a shader.

NewPixie and all 26 selected package presets passed complete dependency checks
and real frame-limited compilation/execution on Garuda. This does not establish
appearance, performance or compatibility on every host. See the integration
[report and manual matrix](../../docs/RETROBAT_AND_HOST_SHADERS.md).

`scripts/shaders-prepare` creates `.work/shader-mappings`; `shaders-smoke` checks
its catalogue and absence of a copied full shader/texture tree. The full old
`.work/shaders` and accepted Gold image remain rollback/audit references.
`runtime/shaders.lock` retains historical pinned Slang/GLSL sources; it is not
an assertion that the host distribution package has that exact commit. Actual
package version and verified test artifact identity are in the integration report.
GLSL is not installed or enabled as a substitute for the required Slang presets.

Original per-file/directory licenses and credits remain with the official
[Slang collection](https://github.com/libretro/slang-shaders) and
[GLSL reference](https://github.com/libretro/glsl-shaders). Arch's package license
label is not a uniform license for every effect/texture. Existing resolved
NewPixie frame, Simpletex paper and Pokefan531 LUT credits are preserved in the
catalogue and [scope review](../../docs/LICENSE_SCOPE_REVIEW.md); previously
recorded legacy-code notice gaps stay separate. New mappings point at unchanged
host-package resources. No Embercade CC/PolyForm grant relicenses those files.

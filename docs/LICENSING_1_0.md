# Embercade 1.0 license assignment

The owner authorized the component grants below after implementing the targeted
backend separation. [LICENSE](../LICENSE) is the routing notice;
[scope.json](../LICENSES/scope.json) enumerates the actual first-party paths.
This is a component assignment, not one license for the mixed AppImage.

| Component | License / attribution |
| --- | --- |
| Independent original Embercade Python client implementation, exact paths in scope.json | PolyForm Noncommercial 1.0.0; Embercade contributors |
| Original backend and upstream integration contributions, including separately mapped API tests/smoke | MIT for Embercade-owned additions; original LGPL/GPL/MIT/other source context and dependencies unchanged |
| Original Embercade prose | CC BY-NC-SA 4.0; copied notices, legal texts, code and foreign graphics excluded |
| Embercade branding masters and derivatives | Owner-confirmed creation with Canva AI; CC BY-NC-SA 4.0 for rights actually held. [Origin record](BRANDING_ORIGIN.md); no exclusive AI-copyright assertion or relicensing of foreign material. |
| Official RetroBat decorations | Published RetroBat project CC BY-NC-SA 4.0 basis adopted by the owner; original author credits, watermarks and individual licenses, including ND notices, preserved |
| Libretro shader collection | External `libretro-shaders-slang` host package under its original mixed component terms; no full shader/texture tree is shipped in the current candidate |
| Carbon theme | Original CC BY-NC-SA notice and exact supplied legal text; Fabrice Caruso, Eric Hettervik/Rookervik, Nils Bonenberger and maioni; independently licensed embedded material retains its terms |
| Batocera packages, frontend, native/Python libraries and AppImage runtime | Original per-component terms, including LGPL, GPL, MIT, BSD and others; no Embercade NC restriction |

## Basis for the independent client scope

The existing source analysis found first-party introduction/history and no
identified whole-file or substantial normalized-window copies of the compared
Batocera Python source. It did not certify ownership of unknown third-party
expression. Those findings are reused, not replaced by a new resource audit.

The client implements its own user state, transactions, file validation,
installation/Steam registration, input handling and desktop presentation.
Its file-processing helpers, XML transformations and GUI are not modules of
Batocera's Python program. With the API programs extracted, it never imports
Batocera/Configgen or the backend implementation. It exchanges file paths,
primitive choices/statuses and raw configuration files over bounded executable
operations. The backend cannot import client helpers; it uses no client object,
callback or executable-code payload. Pure client operations remain usable without
loading the backend. These are substantive purpose, code-origin and data-contract
reasons for the selected independent client scope, not merely a JSON wrapper.
[The implementation report](ADAPTER_SEPARATION.md) records executable checks.

`xbox_eeprom.py` retains its exact Xemu format reference. Public field layouts,
continuation states and standard algorithms are format facts, not a grant to
relicense Xemu's C implementation; the assignment covers Embercade's own Python
inspection/edit/transaction implementation only. Likewise, reading/copying a
foreign controller database or catalog does not make that input Embercade-owned.
Generated XML, copied mappings, upstream descriptors, legal texts and foreign
resources are excluded from the own-code grant and retain their source terms.
No personal EEPROM, authentication value or secret is licensed or redistributed.

The owner's grant is limited to rights actually held. A process boundary alone
cannot establish legal independence or cure copied protected code. No claim of
court/provider approval or blanket GPL exception is made. A future backend
change introducing shared internal structures, reverse imports, callbacks or
foreign source copying requires a fresh scoped review before extending the grant.
See the [corrected GPL/LGPL component distinction](BATOCERA_COMPONENT_LICENSES.md).

## Resources and historical audits

The current private image uses only the official RetroBat collection at
`5ce1f6ed32eb9f3df8ae14483afc4d1e3ef35d65`, from
[retrobat-bezels](https://github.com/RetroBat-Official/retrobat-bezels).
The published project basis is [RetroBat's pinned license notice](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/license.txt).
Existing individual notices remain operative. Technical link aliases and Linux
materialization are recorded; original pixels and credits are unchanged. The
old 302/35-path captured-bezel audits are historical evidence for a removed
payload, not outstanding blockers for this replacement collection. No new
pack-wide PNG/hash/history investigation was performed and no specific new
license contradiction was established by this work.

The image ships small original shader mappings and catalog metadata, not
`.slang`, `.slangp`, frames or LUT resources from the full collection. The actual
shader programs/textures stay in the official host package under their original
per-file licenses. The old captured shader-source questions do not describe
bundled files in the current candidate. Existing resolved NewPixie/texture/LUT
credits are retained; no foreign shader is assigned PolyForm or Embercade CC.

Only Carbon is bundled: `fabricecaruso/es-theme-carbon` at
`b921e1734d88d6bc7b9e8cb97dd8f8b91ba2058a`.
Its original readme has a 2.0 heading followed by 4.0 legal text; that upstream
inconsistency is recorded without rewriting it or inventing a new version grant.
Its original theme-license identification and author credit remain resolved.
Downloaded themes are separate user acquisitions and keep their own notices.
Brand logos/trademarks and original third-party subresources are not relicensed.

## Release conditions still distinct from these grants

- The new frontend uses each user's protected runtime RetroAchievements Web
  API key, retaining the existing Web API views and normal emulator login.
  [Implementation and tests](RETROACHIEVEMENTS_USER_KEYS.md) replace the former
  compiled shared-key approach. Older installed/Gold images retain their private
  identity; they are not public release candidates. User acceptance and explicit
  publication approval remain separate. ScreenScraper's build flow is intact.
- The prior missing branding origin is resolved by the owner's Canva AI
  declaration; the scoped grant is documented in [BRANDING_ORIGIN.md](BRANDING_ORIGIN.md).
- Matching covered sources, nested notices and LGPL replacement/relinking
  instructions are now prepared locally for the frozen candidate, including
  its actual native/Python components. [The delivery review](THIRD_PARTY_DELIVERY.md)
  records this completion. [SOURCE_ACCESS.md](SOURCE_ACCESS.md) distinguishes
  the verified local kit from the still unperformed public delivery; the
  eventual public artifact must include these notices and its matching sources.
- Repository publication/privacy hygiene remains separate. No new public release,
  tag, push, visibility change or deployment is authorized here.

The project is free to use under the applicable terms and intended for a
noncommercial community. PolyForm is **source-available**, not an OSI open-source
license. Its unmodified organization/distribution permissions apply as written;
there is no additional universal commercial-use or resale prohibition. GPL,
LGPL, MIT and other upstream commercial permissions remain intact.

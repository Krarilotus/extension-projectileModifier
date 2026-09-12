# Native integration audit, 12 September 2026

This is an audit of the implemented 1.8.6 candidate, not a release acceptance
statement. Original source branch `main` and the store PR branch are preserved.
Corrections are being prepared in `fix/native-binding-audit`. Store PR #31
remains provisional. User scope also includes aiming before a retargeted shot,
optional threat priorities and investigation of reported monk targeting.

## Confirmed findings

| Finding in 1.8.6 | Evidence and required correction | Status |
|---|---|---|
| Fixed normal/Extreme unit-array roots | `addresses.lua` selected VAs. Decode the two native dispatcher operands and verified update-loop capacity. | Removed in this branch; issue #2. |
| Discovery bypassed the framework cache | `init.lua:resolve` called bounded `scanForAOB` twice. Use `core.AOBScan` for discovery and check ambiguity on both sides of a cached match. | Corrected; real framework cache exercised in tests, including a new earlier match. |
| Unconditional accuracy hooks | Both native scatter stages were patched even with accuracy omitted everywhere. | Corrected; only effective profiles with explicit accuracy require these bindings and three assembly routines. |
| Retargeting can fire before turning | 1.8.5 live trace records a trebuchet shooting at new coordinates before its next aiming phase. Initial-state comparisons did not cover this transition. | Open; reproduce loaded/reload/release transitions before correction. |
| Full-world automatic target scans | `templates.lua:scanUnit` visits every unit slot per search; building/wall scans and the 256-candidate cluster loop also need review. Multiple shooters multiply the cost. | Open; investigate native spatial/target owners before extending priorities. |
| Full entity scans every update | `spriteUpdate` invokes `spriteAll` twice, each visiting 2999 slots. Decorations additionally rebuild a 10000-cell grid and scan the entity pool. | Open; owner-side render/lifecycle integration is required before claiming this efficient. |
| Private GM slot allocator/loader interception | `sprite_resources.clone/install` duplicate GM header/offset discovery and intercept the native loader inside gmResourceModifier's own loading lifecycle. | Open; extend the resource owner to reserve additional sheets before its replacers are initialized; remove the consumer's clone and loader hook. |
| English-only validation and conflict errors | `configuration.lua`, `state.lua`, resource validation and native resolver diagnostics are English-only. Nine GUI preview catalogs do not cover these errors. | Open; inspect native-language and launcher diagnostic owners. |
| No separate OFF controls for simple corrections | One file picker exists; previous automatic bug corrections were not exposed separately. | Open; preserve the user's compact, file-based interface and explicit existing choices. |
| Redundant legacy settings | `suppress_default`, `sync_to_animation`, `sync_max_wait`, `preload` and unit/tile aliases require a semantic/caller audit before removal. | Open; do not break existing presets or silently reinterpret omitted fields. |
| Coverage is narrower than declared acceptance | Automated native evidence uses one normal and one Extreme 1.41 image; live evidence is normal Crusader. | Other applicable variants, actual all-locale GUI, paired multiplayer, replay and performance remain open. |
| Recorder integration does not enroll projectile-owned state | Existing optional save registration and `serializeSimulationState` do not enroll this provider in required captures. | Open consumer integration; reuse existing Map PR3 and Recorder fork PR3, coordinated in Corax34/ucp_recorder#47. No competing capture implementation. |
| Stale UI dependency warning | UI 1.0.1 is now in the 3.0.7 store at the same `d3a807c...` commit bundled earlier. | Public and package documentation needs reconciliation; UI upstream PR6 alone is not store availability evidence. |

The monk symptom is **not yet reproduced**. In isolated native tests on both
reference EXEs, an enemy Monk (type 37), Priest, spearman and archer were selected
by the catapult's `targets: units` policy and entered native aiming state 8.
`scanUnit` has no unit-type whitelist. This does not establish every real monk
state or configuration works: ownership, native eligibility, visibility, range,
cluster thresholds and current commands need examination in the failing match.

## Reuse and ownership inventory

| Capability | Implementation inspected and decision |
|---|---|
| AOB discovery/cache | Framework `content/ucp/code/core.lua:core.AOBScan` and `data/cache.lua:AOB.retrieve`, revision `02a7a6bc8ab956a91fc752e8c8ed215c149855e7`. The cache validates hits through the native scanner; reuse directly, with no module-private cache. |
| Native allocation/assembly/patches | The same framework's `core.allocateAssembly`, `core.insertCode` and memory APIs. Existing module assembly wrappers filter unused constants for the framework assembler budget; no alternate assembler or allocator is introduced by this correction. Remaining manual trampoline ownership needs audit. |
| Working unit/projectile balance extension | `rebalancer/init.lua`, `templates.lua`, `constants.lua`, revision `8d5b47e1d61cab8c0f4b1f301669d2541788facd`. It exposes native table/operand balance changes; it does not provide a runtime projectile-target query service. Preserve its source and resolve actual overlap before changing target ownership. |
| Effective configuration profiles | `configuration.validate` already merges sparse base/wall/decoration fields before installation. `cadence.enabled` privately repeated profile traversal. The small `configuration.any_profile` helper now owns traversal for cadence and conditional accuracy; no independent cache, resolver or per-tick traversal. |
| Native aim/projectile/damage ownership | Original `UnitsState::acquireShootTarget`, `shootProjectile`, siege state handlers and tile-facing function, plus OpenSHC declarations at `126f25c9a53c14270ccd10c6a5db6f05bd143204`. Reference annotations are research evidence, not deployed bindings. Existing native dispatch remains responsible for allocation, projectile physics, damage and lifecycle. No copied damage/turning implementation is justified by this audit. |
| Save/new-world callbacks | Existing `map-extensions:registerSection` registration in `init.lua` and `state.lua`. Retain the owner and saved layout; actual multiplayer/replay acceptance is still outstanding. |
| GM resource loading | gmResourceModifier 0.2.0 `init.lua` and `ColorAdapter::detouredLoadGmFiles`, `SetGm`, `Replacer::readyOrigResource` at `019039afcb29f3806aa30c7157ae5a1253c06673`. It loads assets, initializes 240 replacers from native headers, then applies queued replacements. `SetGm` requires compatible existing image counts; it exposes no additional-sheet reservation. Extend this lifecycle, not a second loader intercept. Current open PR5 is discovery metadata, issue4 is GUI texture packs; neither supplies this missing API. |
| UI and synchronized commands | UI 1.0.1 `ui/game.lua`, `ui/modalmenu.lua`, and protocol 1.0.0 `init.lua`, `game/interface.lua` in the original worktree. Keep native menu creation and lockstep decoration commands with these owners; no new input/command handler is introduced for unit aiming. |
| Localization/category registry | `UCP3-GUI/resources/lang/languages.yaml` currently lists de/en/fr/ru/hu/tr/ch/es/fa. Existing file selection is under Legacy's Balance Changes taxonomy. No Legacy source changes. Runtime error localization is not supplied by the GUI preview loader. |

## Binding correction evidence

Normal and Extreme native dispatcher paths independently read the unit cow-mode
field at offset 0x3B0; both absolute operands must decode to the same aligned
unit-array root. Verified opcode context precedes each operand. UnitState `this`
is the decoded root minus its established 0x614 layout offset.

The update-loop limit must be a CMP immediate followed by the same cursor store
and a relative branch back to this loop. Its decoded capacity remains restricted
to the framework's normal/Extreme supported capacities. This is a capacity/layout
constraint, not a fixed executable address or a claim that modified pools work.
Resolution of these unit/accuracy bindings precedes allocation, resource loading
and patch installation; later sprite/decorative bindings still need the separate
ownership correction described above.

The first six focused native-binding tests passed on the reference images, including the
real framework cache Lua, ambiguous/missing/occupied sites, conflicting operands,
wrong opcode/cursor/branch/capacity, synthetic operand relocation, conditional
accuracy hook ownership and effective decoration-profile activation. Synthetic
relocation proves decoder behavior only, not support for another game build.
The full 112-test regression suite then passed at `099a271` in 815.893 seconds,
but live startup exposed an assumption missing from that suite: RPS's upper bound
is checked after scanning a whole memory region. The earlier-duplicate check
therefore rejected its own selected site. A seventh binding test reproduces the
failure before the correction. The check now rejects only a hit strictly below
the selected site; the later-match check remains in place. This is a consumer
bound check using the existing scanner, not another scan implementation.
All 23 GUI component/archive checks pass. These use the real launcher discovery
and category resolver with substituted native I/O, not the installed GUI.

The isolated native installation uses framework 3.0.7 developer revision
`77c6accf14a55fb95434fe6ffd96516e005568b5`. Its packaged `core.AOBScan`,
`data/cache.lua` and `data/version.lua` match the inspected checkout after newline
normalization. This checks the actual dependency used by prior live tests, not
just the current source branch.

The actual native scanner owner is RPS 1.5.2 (`dll/Directory.Build.props`), exposed
by `dll/core/initialization/ucp-internal.cpp:RPS_initializeLuaAPI`. Inspected
[`AOB::Scan` at v1.5.2](https://github.com/gynt/RuntimePatchingSystem/blob/v1.5.2/AOB.cpp):
it scans the current VirtualQuery region before testing `address > max`.

## Further native/owner evidence

The normal reference `findClosestEnemyByAreaAndRange` performs its own unit loop,
with area, native eligibility and score filters. It is not a spatial query merely
because of its name. `getEnemyUnitIDNearby` traverses a native linked unit bucket
and calls the original enemy-eligibility routine; its caller and bucket semantics
must be established before reuse for configurable ranges/priorities. Neither was
copied or replaced in this correction. `isBrazierNearby` likewise walks the native
active entity range; invoking it does not justify an additional per-frame census.

Launcher `resources/gameinfo/game-version.yaml` currently identifies Steam normal
1.41.0 (`3bb0a8c1...`) and Extreme 1.41.1 (`55648e6b...`), both Latin/Western.
Framework `data/version.verifyGameDependency` compares SHC/SHCE and major/minor,
not an extension-private executable hash. This module declares both 1.41 families.
The registry is identification data, not proof that all applicable distributions
or language variants share these two binaries. Further fixtures remain outstanding.

Startup error localization has an owner prerequisite: framework `getGameLanguage`
returns nil before `afterInit` and maps only seven native language indices, while
the launcher supports nine locales independently. `dll/core/Core.cpp` currently
shows Lua failures with `MessageBoxA`. Adding UTF-8 strings to the module alone
does not establish correct non-ASCII error rendering. The launcher/runtime locale
handoff and diagnostic display must be solved through their owners.

The resource prerequisite is tracked in
[gmResourceModifier issue 6](https://github.com/UnofficialCrusaderPatch/ucp_gmResourceModifier/issues/6).
Recorder state support already has a reusable draft: Map Extensions
[PR3](https://github.com/gynt/ucp-extension-map-extensions/pull/3) at `04449b7`
extends `registerSection` with required provider options and read-only callbacks;
Recorder [fork PR3](https://github.com/Krarilotus/ucp_recorder/pull/3) at `7b6217f`
uses that API in the existing initial/frozen captures and checkpoint boundaries.
Both implementations and the real framework proxy regression were inspected.
The projectile consumer still needs validate/capture/integrity plus cheap paired
boundary observation, required registration and actual acceptance. Coordination
is in [existing issue 47](https://github.com/Corax34/ucp_recorder/issues/47#issuecomment-5646119542).
Those owner branches were not modified.

## Completion gates

No normal merge or final completion is claimed while avoidable scan/ownership
debt, native prerequisites, localization/default controls or required acceptance
remain open. Threat priority is a deliberate balance policy and must default to
the existing behavior until explicitly configured. Any verified eligibility or
retargeting correction needs an ON default and OFF baseline without another
overwhelming Customizations panel. Existing file schemas and saved RNG order must
remain compatible unless an explicit user option changes behavior.

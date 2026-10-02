# Native integration audit, 12 September 2026

## 1.8.16 manual range without reload customization

Inspected the existing consumer at d1bbe93: `install` only enabled the native
manual range guard for an interval using native synchronization, and the
acquisition hook required NATIVECYCLET. A reproducible Mangonel range-only
configuration therefore bypassed the configured range. Extend those existing
owners: enable the existing guard for an explicit range, and encode eligibility
in bit 1 of the existing immutable STRICTRANGET profile flag (bit 0 retains
scheduled exact checks). There is no new flag table, persistent block or cache.
The native original acquisition still runs exactly once before the existing
SHOOTTARGETINRANGE helper. Reuse ISAIOWNED to preserve AI-only human behavior.
OFF remains strict_range false; unconfigured/native range retains native timing.

Runtime discovery stays with the existing UCP AOB-resolved ACQUIRE entry,
displaced prologue/trampoline and ABI; no new binding or competing hook is added.
OpenSHC EntityState initializer/velocity declarations and the actual reference
solver confirm native pebbles use fixed-angle speed solving. Execute the real
native Mangonel handler, then projectile allocator/initializer/movement in both
1.41 families using the supplied settings. Target admission is separate from
intentional projectile scatter: preserve spread/RNG order and native physics,
allocation, ownership, damage and cleanup. Final diff adds no physics solver,
world scan, per-frame allocation, private resolver or copied dispatcher.
The framework's `dll/lua/yaml/LuaYamlParser.cpp:parseTableNode` iterates mapping
entries and writes each with `lua_setfield`; later duplicate Catapult keys thus
replace earlier values. The cleaned example consolidates them without adding a
private YAML parser or changing the supplied effective values.

## 2 October 2026: replacement projectile flight

| Capability | Existing owner reused / precise gap |
|---|---|
| Global flight properties | Rebalancer `init.lua:edit_projectiles` and exported `namespace.apply_rebalance`, inspected at `8d5b47e` (1.1.4) and the Store's `b3e1a36` (1.1.3). Its existing `enable` caller applies the same tables. Add only a validated config adapter: fixed-speed mode maps to arch 0, fixed-angle to 1, Catapult-style adaptive-angle to 2. The owner's legacy `velocity` parameter represents degrees in the latter modes; do not expose a misleading speed/angle pair. |
| Startup ordering | Framework `hooks.lua:registerHookCallback('afterInit', ...)`, already used by version/resource owners. Native event fires before the Windows message loop, after extension enable. Reuse it to apply flight settings after all balance files without introducing a private dispatcher or native hook. |
| Native binding | Rebalancer already resolves the two property tables through `core.scanForAOB`. No consumer scan, binding, fixed address or fallback. Tests verify those table roots against decoded operands of the native property-setup reader on both PE families. Existing unrelated Rebalancer bindings are outside this delta. |
| Solver and entity state | Verified original `setProjectileEntityValues2`, `initializeProjectileVelocities`, `computeVelocity`, angle solver and `moveProjectileEntity` against OpenSHC declarations and original instructions. Modes 0/1/2 reuse native setup and motion. An unreachable fixed-speed shot reaches native angle fallback; fixed-angle mode calculates launch speed for the existing aim. No copy of the ballistic equations, collision path or allocator. |
| Normalized projectile forms | Native allocator converts untargeted/fire forms to their base type. Canonical physics entries target the nine shared native types. Fire-ballista bolts share type-20 `ballista_bolt` physics; exposing the owner's separate type-37 table as independently effective would be misleading. Custom sprites already inherit their native base. |
| Configuration/persistence | Extend `configuration.validate` with opt-in global `projectile_physics`. Add its normalized result to existing save identity only when nonempty, preserving old fingerprints. Existing Map Extensions retuning/strict matching remains the owner. No additional per-unit blocks, RNG draws, allocations during firing or world scans. |

Rebalancer is an **optional active prerequisite for these settings**, not an
unconditional module dependency: its `enable` requires a balance file and also
installs general balance hooks. Automatically enabling it would change existing
configurations. Missing owner/event support rejects before native mutation.
Global flight tuning is deliberate balance configuration, default omitted/native,
not a silent change to every ordinary archer or firethrower.

## 2 October 2026: save retuning and rejected manual shots

Inspected the current module at `94a5804`, the Map Extensions validate-before-
restore caller/tests at `aic-tactics-map-required-state` revision `04449b7`
(1.1.0, with the optional-section API retained from 1.0.0), and the framework
AOB/assembly owners previously recorded at `02a7a6b`.

| Capability | Existing owner reused / precise gap |
|---|---|
| Saved configuration edits | `state.new` and Map Extensions' existing validate/deserialize callbacks. Format 5 gains an optional asset identity header; validation remains read-only before any extension restores. Changed gameplay settings discard only obsolete module firing queues/timers, preserving the saved seed and visual identities. Same settings restore the same blocks. No private loader, migration cache or save service. |
| Visual identity safety | Existing immutable GM slot/hash blocks must match. Definitions also match via the new asset header. Legacy saves lacking that header permit retuning only with no custom visual identities; custom-graphics saves require one unchanged resave. No remapping of native entity ownership or resources. |
| Manual range admission | Reuse the existing native acquisition entry hook and decoded original continuation. The original thiscall executes once with its native eligibility rules, then the existing prepared aim point is checked against the configured range. The shared `shootTargetInRange` is the former `pickTarget` exact check, extracted once for both callers. No command replacement, additional signature or target search. |
| ABI and discovery | Existing UCP AOB resolution verifies the six displaced prologue bytes (`83 EC 40 53 56 57`) and the native continuation. The original trampoline preserves the native thiscall/`ret 4` contract. Existing bindings cover Crusader and Extreme; no new fixed VA/RVA or fallback. |
| Existing stuck animation | `configuredAnimationHold` reuses `NATIVETARGET` before native scatter and the existing `NATIVEBLOCKT` release gate. A rejected manual target passes the animation through; existing release cancellation/refund handles ammunition. It does not run acquisition inside the late projectile dispatcher. |
| Defaults/performance | Range correction is default ON for configured native-timed profiles, OFF with existing `strict_range: false`. Save retuning is default ON, OFF with root `allow_config_changes_on_load: false`. Guarded O(1) checks, no extra scan, allocation, RNG draw or saved per-unit block. |

Native damage, allocation, target identity, projectile scatter and world-state
serialization remain owned by their existing subsystems. Changing a gameplay
configuration intentionally changes a save's continuation; unchanged settings
retain the previous resume semantics. Actual desktop, multiplayer and recorder
acceptance remain distinct from emulated production-code regressions.

## 1 October 2026: ammunition by victim type

Based on source main `cf063d9` (merged 1.8.12), inspected before this change:

| Capability | Existing owner reused / precise gap |
|---|---|
| Configuration and profile inheritance | `configuration.validate` / `merge_fields` / `any_profile`; add optional maps and expand flat named groups during existing validation. Extract the existing native/custom projectile field validation into `projectile` so both slot fields and target rules share it, rather than introducing a second resolver. Group names do not create new runtime unit classes. |
| Ammunition choice | `templates.ammo_code:chooseAmmo`, called by `automatic_code:t_shoot`; already receives the effective shooter profile and accepted native victim. Missing per-victim choice is added here, with a small shared `targetAmmo` lookup used by this selector and the existing random volley. No parallel selector or targeting service. |
| Identity/layout | OpenSHC `Map/Units/Unit.hpp` confirms 0x490 stride, short shootTargetedUnit at +0x344, victim UID at +0xA0, unit type +0x8E/UID +0x98. Existing `PICKTARGET` and native acquisition prepare these fields. Guard slot, live state and UID; never find a new victim here. |
| Native projectile dispatch | Existing `volley_code:v_fire` and UCP-resolved `FIREPROJ` keep projectile allocation, launch metadata, attribution, damage and cleanup. Reuse existing regular/cow remaps and `CURRENTVARIANT` for GM-owner sprites. Reset the temporary cow flag per mixed shot and restore the original afterward. |
| Manual orders | Existing `manual_order_code:manualOrder` keeps supported native human attack orders out of the new automatic rule path. `fire_hook_code:h_fire` clears rule scratch before existing native volleys. Native cow orders stay in their existing native path. |
| Runtime discovery | Framework `content/ucp/code/core.lua` at `02a7a6b`: `core.AOBScan` delegates unbounded discovery to `data.cache.AOB.retrieve`; bounded uniqueness checks use `scanForAOB`. Existing module `resolve` decodes shoot/acquire/unit roots. No new binding, scan, hook, VA/RVA table or fallback. Assembly allocation remains `core.allocateAssembly`. |
| Persistence/synchronization | Existing `state.new` / Map Extensions format 5 canonicalizes the expanded rule map. Unused groups do not affect identity; equivalent groups/direct maps do. Only immutable init tables and scratch are added, not persistent blocks or commands. Existing volley RNG order is retained. |

Lookup is O(1) per projectile, with no search, RNG draw or allocation. One
80-type x 12-byte table is allocated at initialization per ruled effective
profile, plus the optional profile-pointer table. Omitted rules compile out
the new firing instructions and allocate no ammunition maps/helper. The final
diff extends these owners; it adds no loader, cache, hook or native dispatch copy.
Rules are opt-in balance policy, not a default bug correction. Runtime startup
diagnostics retain the existing configuration owner's English errors; this is
an existing localization gap, not a new GUI error/translation resolver.

The new native tests exercise both 1.41 reference images, direct/group precedence,
mixed victims, cow remaps, custom sprites and deterministic saved continuation.
Actual rendered firing/impact, paired multiplayer/replay and broader variants
remain acceptance gaps. On 1 October the queued native probe again returned
`Native app bindings are unavailable for windows`; its slot was released.


This audit began with the 1.8.6 candidate and tracks provisional 1.8.10 source;
it is not release acceptance. Original source `main` and Store PR #31 remain
preserved. User scope also includes combined live retargeting, optional threat
priorities and investigation of reported monk targeting.

**28 September correction:** The game's `UnitsState::acquireShootTarget` does
have a distance-, attention- and target-type-sensitive automatic selection
policy. The 1.8.10 flat-rank prototype was not integrated with it and has been
reverted. [NATIVE-TARGET-RESEARCH.md](NATIVE-TARGET-RESEARCH.md) records the
native owner, separate AI pathfinding query and remaining integration boundary.

## Confirmed findings

| Finding in 1.8.6 | Evidence and required correction | Status |
|---|---|---|
| Fixed normal/Extreme unit-array roots | `addresses.lua` selected VAs. Decode the two native dispatcher operands and verified update-loop capacity. | Removed in this branch; issue #2. |
| Discovery bypassed the framework cache | `init.lua:resolve` called bounded `scanForAOB` twice. Use `core.AOBScan` for discovery and check ambiguity on both sides of a cached match. | Corrected; real framework cache exercised in tests, including a new earlier match. |
| Unconditional accuracy hooks | Both native scatter stages were patched even with accuracy omitted everywhere. | Corrected; only effective profiles with explicit accuracy require these bindings and three assembly routines. |
| Retargeting can fire before turning | 1.8.5 live trace records a trebuchet shooting at new coordinates before its next aiming phase. | Provisional accepted-aim correction in PR #8; emulated normal/Extreme Halt, death and slot-reuse regressions pass; combined live direct-click test remains open. |
| Full-world automatic target scans | `templates.lua:scanUnit` visits every unit slot per search; building/wall scans and the 256-candidate cluster loop also need review. Multiple shooters multiply the cost. | Existing cost remains for cluster, random volleys and configurations without the opt-in score map. Configured non-random unit targeting with a score map uses the native scheduled candidate list. No second world scan was added; broader performance/eligibility review remains open. |
| Full entity scans every update | 1.8.8 `spriteUpdate` invoked `spriteAll` twice across 2999 slots, while decorations cleared 10000 cells and scanned 2999 entities each update. | 1.8.9 replaces these per-update sweeps with active IDs and touched grid cells within the existing spawn/update hooks. One bounded census remains at new-world/load and decoration placement. Live rendered performance acceptance remains open. |
| Private GM slot allocator/loader interception | `sprite_resources.clone/install` duplicated GM header/offset discovery and intercepted the native loader inside gmResourceModifier's own loading lifecycle. | Removed in PR #8. GM owner PR #7 now also implements complete-sheet validation and content identity; 1.8.8 removes the consumer parser, file read and hash. Live acceptance remains open. |
| English-only validation and conflict errors | `configuration.lua`, `state.lua`, resource validation and native resolver diagnostics are English-only. Nine GUI preview catalogs do not cover these errors. | Open; inspect native-language and launcher diagnostic owners. |
| No separate OFF controls for simple corrections | One file picker exists; previous automatic bug corrections were not exposed separately. | Open; preserve the user's compact, file-based interface and explicit existing choices. |
| Redundant legacy settings | `suppress_default`, `sync_to_animation`, `sync_max_wait`, `preload` and unit/tile aliases require a semantic/caller audit before removal. | Open; do not break existing presets or silently reinterpret omitted fields. |
| Coverage is narrower than declared acceptance | Automated native evidence uses one normal and one Extreme 1.41 image; live evidence is normal Crusader. | Other applicable variants, actual all-locale GUI, paired multiplayer, replay and performance remain open. |
| Recorder integration does not enroll projectile-owned state | Existing optional save registration and `serializeSimulationState` do not enroll this provider in required captures. | Open consumer integration; reuse existing Map PR3 and Recorder fork PR3, coordinated in Corax34/ucp_recorder#47. No competing capture implementation. |
| Stale UI dependency warning | UI 1.0.1 is now in the 3.0.7 store at the same `d3a807c...` commit bundled earlier. | README and store PR31 corrected; published tester ZIPs remain unchanged. |

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
| Ambiguous AOB rejection | That framework returns one cached match but exposes no match-count result. `init.lua:resolve().locate` calls its `scanForAOB` only around the framework result to reject second matches, then decodes operands from verified context. This is an initialization-only guard, not a competing discovery cache or fixed-address fallback. |
| Complete GM1 loading/identity | gmResourceModifier PR #7 `Gm1ResourceManager::CreateGm1Resource` owns file loading and native resource lifetime. Its new `LoadCompleteGm1Resource` validates an exact inherited layout and returns a SHA-256 digest of the same loaded bytes. `sprite_resources.prepare` calls that owner once and passes its ID to `ReserveGm`; its Lua parser, file read and framework hash call were deleted. |
| Digest service | The framework's Lua `sha.sha256` accepts a Lua byte string, but the GM owner already holds the file in native buffers before renderer preparation. Passing or rereading it through Lua would duplicate loading. The owner uses Windows CryptoAPI on those buffers; it does not implement another SHA algorithm or cache. |
| Entity/render lifecycle | Framework `content/ucp/code` at `02a7a6b` exposes no entity spawn/removal/render callback. The module's existing native spawn and whole-entity update hooks already own its visual GM swap. 1.8.9 indexes only entities admitted by those hooks, validates UID/type on update, and reconstructs unsaved scratch indices via the existing Map Extensions callback. No new hook, allocator, cache or competing dispatcher was added. Issue #9 still requires live/MP/performance acceptance. |
| Entity-state binding | The 1.8.8 visual path read `fire+0x416` twice without checking the operand or its call. 1.8.9 resolves the `mov ecx, EntityState; call spawnProjectileEntity` instruction through the same cached UCP AOB API, decodes both operands, verifies the relative call reaches the independently resolved native spawner, and compares the pointer with the decoration command receiver when configured. This resolves once before GM admission/allocation; both previous offset reads are gone. A changed call, invalid pointer or duplicate signature fails before patching. |
| Decoration map receiver | `decorations.lua` derives the native map receiver as the AOB-decoded `TILEFLAGS` data layer minus its `0x165160` structure offset. This number is a map-layout field offset, not an executable VA/RVA. The native validation, height, ownership and construction tests exercise the receiver on normal/Extreme; broader live variant acceptance remains open. |
| Native allocation/assembly/patches | The same framework's `core.allocateAssembly`, `core.insertCode` and memory APIs. Existing module assembly wrappers filter unused constants for the framework assembler budget; no alternate assembler or allocator is introduced by this correction. Remaining manual trampoline ownership needs audit. |
| Working unit/projectile balance extension | `rebalancer/init.lua`, `templates.lua`, `constants.lua`, revision `8d5b47e1d61cab8c0f4b1f301669d2541788facd`. It exposes native table/operand balance changes; it does not provide a runtime projectile-target query service. Preserve its source and resolve actual overlap before changing target ownership. |
| Effective configuration profiles | `configuration.validate` already merges sparse base/wall/decoration fields before installation. `cadence.enabled` privately repeated profile traversal. The small `configuration.any_profile` helper now owns traversal for cadence and conditional accuracy; no independent cache, resolver or per-tick traversal. |
| Native aim/projectile/damage ownership | Original `UnitsState::acquireShootTarget`, `shootProjectile`, siege state handlers and tile-facing function, plus OpenSHC declarations at `126f25c9a53c14270ccd10c6a5db6f05bd143204`. Reference annotations are research evidence, not deployed bindings. Existing native dispatch remains responsible for allocation, projectile physics, damage and lifecycle. No copied damage/turning implementation is justified by this audit. |
| Automatic threat scoring owner | The game already has a distance-and-attention scorer inside `UnitsState::acquireShootTarget`, fed by its scheduled per-player candidate list. The framework/rebalancer do not expose its score or the Catapult/Trebuchet early gate. This change resolves those native instruction contexts with UCP AOB facilities, adjusts only the pre-transform base score for opted-in shooter/target types, and bypasses the siege early gate only during this module's synchronous scheduled call. The native owner keeps candidate enumeration, range/LOS/type/engagement policy, target preparation and attention updates. No independent scorer is retained. |
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

After the scanner correction, all ten focused regressions passed in 38.633
seconds: seven binding tests, omitted/cow scatter, explicit-zero scatter and the
manual-ground last-stone case. No wider gameplay changes followed the full suite.

Live normal Crusader at `fdcc38a` passed startup and loaded the existing `w.sav`
wall attack with unchanged Reconquista configuration. A read-only 45.1-second
trace (420 samples) recorded catapult slot 121 retaining order 23, with stones
12 -> 11 -> 10 -> 9. Each debit coincided with three new native mangonel pebbles;
the three groups appeared at native clocks 37666, 38367 and 39068 (701 ticks
apart, consistent with configured 700 at 10 Hz sampling). Every pebble moved
through 13-19 sampled positions and disappeared after its flight. 330 samples
showed reload phase 2/cycle 12. The wall visibly took damage.

The test ZIP SHA256 was
`3b0b41b65cad1fc19666452441b82d19257314ee2e6b5770b9b53c3744663d0c`.
It is an internal package under the old version label, never uploaded or supplied
as another 1.8.6 release. The process exited normally, error log contained only
its header, and the desktop was released at 15:23:41 CEST. Evidence is retained
in `tests/output/live-bindings-fdcc38a.jsonl`, `native-binding-live-summary.json`
and `native-binding-fdcc38a.png`. This trace does not prove damage attribution:
the sampled entity+0xA0 field is zero for these artillery shots. It also does not
cover retargeting, live Extreme, multiplayer, replay or installed-GUI locales.

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

## Save validation consumer correction

Related to projectile issue #6. `state.lua` validated only in `deserialize`.
Map Extensions PR3 at `04449b7f7b38dccf52e376a5fe62cc230fa5f596` already calls
every section's optional `validate` callback before its first extension restore.
The consumer now exposes its existing validator at that boundary, and direct
deserialization calls the same function. No validation cache, alternate save
dispatcher, native hook, serializer or per-tick work is added. The fixed field
limits are constructed once per state provider instead of once per saved block.

The real `mapextensions.callbacks.afterReadSav`, `required.validate` and handle
implementations reproduced an earlier section being restored before invalid
projectile state failed. With this correction, invalid format/configuration,
length, field range, graphics layout and a missing final block all fail before
that restore. Only ZIP/native I/O is substituted in this test; it is not a live
game load. Four focused tests pass in 10.123 seconds, including read-only
validation and byte-identical format-5 round trips for normal and Extreme layouts.
Six existing continuation tests pass in 22.573 seconds: stagger/scatter RNG,
atomic malformed restore, trebuchet reload/crew wait, native custom-sprite flight
and identity, and decoration/fortification restoration.

Old saves without a required manifest retain the existing missing-section
initialization behavior. A read handle marked required cannot silently initialize
if its format is absent. No new diagnostics, config fields or GUI controls are
introduced. Map Extensions 1.0.0 still ignores this additional callback; global
preflight requires the existing owner PR to land. Source required-provider
registration, package identity, boundary observation and live multiplayer/replay
acceptance remain unfinished. The internal package contains 47 files/100861
bytes, 132 bytes above the config-owner parent; no archive was uploaded.

Live normal Crusader acceptance subsequently passed at `a938089`, with Map
Extensions `04449b7` Lua files and the existing 1.0.0 `luamemzip.dll` (unchanged
native ABI, SHA256 `a4dfd1beb49b09f8e2c52ad680101bd8843c9c008988268610442b7b85e1cc7c`).
The game loaded existing `w.sav`, wrote a separate `v.sav`, and reloaded it through
the native menu. Every saved custom ZIP entry matches the read-back entry byte for
byte. The manifest has `providers: []`, as expected: this is optional-section
preflight acceptance, not required-provider enrollment.

The 30.010-second post-reload trace contains 280 samples. Catapult 121 retained
wall order 23; stones 12 -> 11 -> 10 coincided with three-pebble volleys at clocks
37667 and 38368. All six kind-4 projectiles moved through 11-18 sampled positions
and disappeared before the trace ended. Its lowered reload pause remained phase
2/cycle 12. Normal exit succeeded, error log contained only its header, and the
desktop was released at 16:02:57 CEST. Exact pre-test config/module bytes were
restored and the temporary Map Extensions package removed from the test install.
[Trace summary](tests/evidence/native-save-a938089.json) and
[native screenshot](tests/evidence/native-save-a938089.png) retain the evidence.
This does not cover native Extreme, changed-target rotation, damage attribution,
multiplayer or recorder replay.

Further inspected identity ownership: framework `extensions/loader.lua` and
`environment.lua` load module files; native `ModuleHandleManager::verifyZipFile`
hashes secure ZIPs, but does not expose that identity to consumers and skips this
verification path in developer mode. `ExtensionHandle` owns file enumeration and
access. AIC's `package-identity.lua` currently verifies its own generated file list;
copying that implementation would add another private package verifier here.
Required capture needs a content identity supplied through the loader/resource
owner before claiming that integration complete. This is a distinct prerequisite
from the read-only validation correction; no fingerprint or compatibility lock
has been fabricated in this module.

## Completion gates

No normal merge or final completion is claimed while avoidable scan/ownership
debt, native prerequisites, localization/default controls or required acceptance
remain open. Threat priority is a deliberate balance policy and must default to
the existing behavior until explicitly configured. Any verified eligibility or
retargeting correction needs an ON default and OFF baseline without another
overwhelming Customizations panel. Existing file schemas and saved RNG order must
remain compatible unless an explicit user option changes behavior.


## Human siege retargeting correction

The existing cooldown hook could preserve a loaded pose while a human changed
its attack order, then release at the new position without rotating. The
correction stays in `cadence.configuredAnimationHold`; no siege handler,
projectile dispatcher, command handler or additional animation site is patched.

Reuse review (base `506358a`; framework `02a7a6bc`, native reference images as
recorded in the test harness):

| Responsibility | Existing owner and decision |
| --- | --- |
| Human/native order precedence | `templates.manualOrder`, already used by cadence and dispatch. Reused without changing automatic selection or its RNG. |
| Point-facing direction and camera adjustment | Native `UnitsState::setUnitFacingDirectionForTargetXandY`, already bound for hunters. Its binding is renamed `FACEPOINT` and shared; UCP AOB context now includes argument reads, tile/facing offsets, direction call and `ret 12`. |
| Facing a moving unit | Native `UnitsState::setUnitFacingDirectionTowardsTarget`, thiscall `(unit ID, target ID)`, `ret 8`. UCP AOB resolves its ID check and both verified stride operands. The existing order's ID/UID is checked before calling it. |
| Building aim position | Native siege state 8 uses the building centre. The generic native building-facing routine instead uses its corner, so it is not equivalent. A bounded read of the existing building ID/UID, tile and width supplies the same centre to the point-facing owner. No building search or target eligibility implementation is introduced. |
| Turn timing and reload progress | Existing native animation clock, phase and cycle. Retain phase/cycle and delay its clock for the native six-tick direction step; no private turn timer, target cache or new save block. |
| Configuration | Existing validated effective profiles, including fortification/decorations, own `turn_before_shot`. The native writer defaults omitted values ON and preserves explicit false. One immutable profile table is added, not per-unit persistent state. |
| UI and translations | The user's explicit file-only configuration direction takes precedence over adding a separate checkbox. Keep the existing file picker under Legacy's Balance Changes category, with the OFF instruction in all nine locale help/preview catalogs. No Legacy edits. |

The correction is limited to human attack orders during native reload/firing
phases. Initial state-8 aiming, movement, native cow phases, pending accepted
volleys and automatic target selection keep their existing owners. Turning does
not call `ACQUIRE` or consume RNG. It uses the selected unit's current tile, and
wall/ground commands use the native stored target tiles.

New regression coverage includes changing a ground target from east to west,
unit/ground/building/wall retargets during the loaded cooldown, save/load during
the direction steps, absence of target queries while turning, unchanged module
RNG and an explicit OFF baseline. Normal and Extreme pass the focused checks.
The changed-target test and framework-cache binding test also pass against the
official PL and EFIGS executables for both families. All four official images
have identical mapped section contents to their corresponding reference family;
their whole-file identities differ. This is native instruction execution in the
harness, not live language-asset or multiplayer acceptance.

All 23 GUI component/archive tests pass, including the installed Legacy category
resolver and all nine locale catalogs. They caught help/preview drift and a
PowerShell stdin encoding conversion in the first generated translation pass;
both are corrected and the ZIP was regenerated with intact UTF-8. This does not
replace actual installed-GUI checks. The current internal archive is 47 files,
103598 bytes, SHA256
`873654d30a79bf6e494de74afd610a6c7d7d084be6262c0a8dede0b9b8d8d473`.
It is not a published replacement for the existing 1.8.6 tester download.

The full suite passes: 121 tests in 964.040 seconds. The expanded changed-ground
case covers all five siege engines on both families, and loaded-turn checks
assert six ticks between direction steps (two expanded tests pass in 100.863
seconds). Live normal Crusader loads and retains three successive wall volleys.
The attempted GUI target changes did not change the recorded native order, so
live retargeting acceptance is still pending; see
[the bounded live trace](tests/evidence/native-retarget-attempt.json).
The UI attempts omitted `screenshotId`, so clicks on the scaled game capture
landed at different coordinates. Supplying it closed the game normally at
20:12:34 CEST; the desktop was released immediately and the original test ZIP
restored with its hash verified. The target-selection attempts must be repeated
with correctly scaled input. They are not evidence of a game-command defect.
No existing save was overwritten. Resource/render lifecycle ownership, automatic threat targeting,
required replay enrollment, complete runtime diagnostic localization and the
remaining multiplayer/performance/GUI acceptance still prevent completion.

## Inherited-sheet owner correction in progress

The consumer now calls `gmResourceModifier:ReserveGm` and consumes
`GetReservedGm` through the framework's existing `afterInit` callback (the same
lifecycle used by aiSwapper). Its private `sprite_resources.clone`, memory-copy
helper, rescans of GM arrays and nested native loader hook are removed. The
`locate` argument to `sprites.install` is removed with its only use. The owner
dependency becomes `^0.3.1`; there is no fallback to the old private loader.

The owner change is isolated at `ucp-gm-inherited-sheets`, based on 019039a and
coordinated in gmResourceModifier issue 6. It admits a complete reservation batch
before constructing the existing Replacers, uses their existing original/reset
state and SetGm reference counts, and preserves queued texture replacement order.
The native loader remains called exactly once. No capacities are expanded.

Consumer failure resolves the entire batch before exposing variant IDs. A missing
required sheet uses the existing framework fatal logger: `luaLog` reaches
`VLOG_F`, whose pinned loguru 4adaa185 implementation aborts at FATAL; ordinary
afterInit assertions are caught. Actual fatal-path acceptance remains outstanding.

Six consumer sprite tests pass, including native inherited projectile kinds,
normal/Extreme flight, saved continuation and no partially exposed layout on
owner admission failure. Six owner host scenarios and its real-framework binding
tests on the two reference families plus official PL/EFIGS files also pass. These
do not replace real rendering, multiplayer, save/replay and GUI acceptance.
The 1.8.8 consumer removes the GM1 validation/hash read through the owner API.
Full entity render scans remained at that revision; 1.8.9 corrects them below.

## 27 September 2026: accepted aim and owner review

The new `acceptedTargetValid` runs only for a configured siege engine waiting in
native loaded state 2 with an automatic accepted unit target. It checks the
native unit slot's live state, health and matching UID, then returns control to
the original idle/aiming transition if that particular target vanished. The
native `ACQUIRE` routine was reused at initial acquisition. Calling it again
while a loaded shot is waiting changes the accepted order and coordinates, so
it is not a read-only liveness API for this boundary. This O(1) check adds no
hook, scan, RNG draw, persistent table or alternate damage/shot allocator.
Native `FIREPROJ` continues to own release, ammunition and projectile creation.
The correction still needs a combined live direct-click test with Fixed
Engineers PR #4 and paired multiplayer/replay acceptance.

Explicit `random_targets` still uses the existing `PICKTARGET` candidate list;
only that opted-in native-release path refreshes it, then restores the native
accepted order. A random volley temporarily sets each victim's native target
ID/UID for damage attribution and restores the accepted ID/UID afterward.
Normal native release performs no target search. A normal and Extreme harness
test confirms candidate coordinates and order/identity restoration.
The GM owner API is now proposed in
[gmResourceModifier PR #7](https://github.com/UnofficialCrusaderPatch/ucp_gmResourceModifier/pull/7),
with two passing CI checks at that revision. Later 0.3.1 owner work adds
content validation/identity and removes the private consumer GM1 parser.
Actual rendering remained open at that revision; 1.8.9 removes the scans below.

## 28 September 2026: active visual indices

The existing `spriteSpawn` hook registers a custom projectile ID once. The
existing `spriteUpdate` hook now restores/applies GMs only for registered IDs,
using the same UID/type guard and removing stale entries. The decoration update
relinks only active custom braziers and clears only cells touched on the previous
update. Stable compaction retains ascending entity-ID order, so equal-priority
proximity ties still query the highest ID first. One full scan reconstructs
scratch indices after Map Extensions new-world/load and after custom placement;
none of these lists or grid cells are serialized. No new native hook, RNG draw,
projectile allocator, targeting owner or fixed executable address was added.

This uses the module's already-installed render and spawn lifecycle. Framework
`core.lua` at `02a7a6b` has no generic entity callback; gmResourceModifier owns
sheet loading/storage, not per-entity visual selection. Native sprite/damage
ownership is unchanged. Focused x86 tests assert empty render passes call no
per-entity routine, one active projectile calls it once, and two decorations
update in under 1000 emulated instructions while preserving grid/tie behavior.
Crowded live frame timing, both rendered games, multiplayer and replay still
need acceptance under issue #9.

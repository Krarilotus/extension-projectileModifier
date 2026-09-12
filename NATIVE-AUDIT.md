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

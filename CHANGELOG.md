# Changelog

## 1.8.4 (test candidate)

- Preserve the game's accepted human shot at native projectile dispatch. Do not
  reacquire after the native catapult/trebuchet has consumed its last stone:
  that rejected the shot and cleared wall, ground and building attack orders.
- Human explicit orders take precedence over every automatic search policy,
  including the default units policy. Native targeting, animation and stone
  consumption remain in place; configured volleys use the native shot coordinates.
- Finish staggered manual volleys with the accepted native aim, including after
  save/load. No new configuration fields or persistent state are introduced.

## 1.8.3 (test candidate)

- Apply cluster-density targeting restrictions only to AI owners. Human native
  shooters with a cluster policy retain their chosen unit, building, ground or
  wall target, with native acquisition and configured range checks. Without an
  order, human units use ordinary unit targeting instead of a density threshold.
- Keep human manual volleys on the chosen target even with random targeting
  enabled. Preserve AI search priorities, crew, ammunition and reload timing.
- Document the targeting distinction in the schema, template and all nine GUI
  previews. The projectile preset must contain only units/projectiles/decorations;
  GitHub workflow fields such as name and on are not valid preset sections.

## 1.8.2 (test candidate)

- Fix trebuchets waiting mid-swing during a configured reload interval. Wait
  in the final loaded pose of the reload phase and reserve the native swing
  time, retaining shot-to-shot intervals and the minimum complete cycle.
- Resolve and validate the loaded pose and firing speed from the executable.
  Preserve late release checks, stone accounting and independent native cows.
- Add both-executable regressions for loaded waits and uninterrupted swings,
  plus save/load and missing-crew recovery. No configuration changes required.

## 1.8.1 (unreleased test candidate)

- Require UI 1.0.1, which fixes the menu-array overrun observed at game startup.
- Compare native opcode signatures by their bit patterns. UCP's signed integer
  reads previously caused decoration initialization to reject a valid executable.
- Match signed UCP memory reads in the native regression harness.
- Consume the decoration modal's closing click through the native mouse reset,
  preventing the same click from reaching the map after selecting a build variant.
- Clarify valid wall/tower placement in all nine localized previews; the native
  manor house cannot hold braziers. Record live placement/removal/save-load checks.

## 1.8.0 (unreleased test candidate)

- Complete native reload timing for horse archers and hunters. Mounted weapon
  timing leaves the horse's movement animation running; hunter firing retains
  the native bow script, facing and unrelated work states.
- Add named projectiles inheriting native damage/flight behavior with independent
  complete GM1 sheets. Validate formats, image tokens and shared graphics capacity;
  keep pixel allocation/conversion owned by gmResourceModifier.
- Add build-menu decoration variants using the standard UCP modal and native
  brazier placement. Synchronize selection through a dedicated lockstep command;
  preserve native cost, wall/tower ownership, placement validity and removal.
- Add ordered near_decorations overrides with native brazier distance/height
  semantics, a bounded spatial index, separate ordinary braziers and save/load.
- Save format 5 preserves mounted clocks and projectile/decoration identities,
  verifies sprite hashes and slot bindings, and rejects incompatible old state.
- Ship an inert all-unit template, editor schema, runnable sprite/decorations
  example and short instructions in all nine GUI locales. The customization tab
  still contains only the standard file picker under Legacy's Balance Changes.

Implementation is complete for the requested feature list. Rendered gameplay,
paired multiplayer/replay and long-session acceptance remain required before
release; see VALIDATION.md. No licensed graphics are distributed.

## 1.7.0 (unreleased test candidate)

- Extend native reload timing to European/Arabian foot archers, crossbowmen,
  slingers and firethrowers. Keep the native firing frame and full cycle minimum.
- Hand configured infantry targets to native wind-up and release checks,
  including buildings, replacement targets and fortification profiles.
- Prevent pending archer retries from bypassing the cooldown.
- Keep native cooldowns running during stance/crew holds; only release is held.
- Resolve release scripts only for unit types needing native timing, so an
  unrelated animation modification does not prevent installation.
- Save format 4 rejects earlier scheduler semantics. Update short timing
  instructions in all nine locales; no additional customization controls.

Mounted/hunter native timing, custom GM1 projectiles and build-menu decorations
remain unfinished. Named custom projectiles will inherit a native base's damage
and flight behavior and use independent sprites; no separate physics is planned.

## 1.6.0 (unreleased test candidate)

- Drive catapult, trebuchet, mangonel and both ballista intervals through their
  native reload/release animations. Long intervals wait before the firing frame;
  short intervals retain the full native cycle. No stone charges while waiting.
- Integrate crew/state/target gating, staggered volleys, separate cow ammunition
  and saved continuation. Keep seven mangonel shots when count is omitted.
- Bound failed target scans with the configured preload polling policy.
- Preserve normal crew requirements unless explicitly overridden. Prepare reload
  during long staggered volleys without releasing before the previous one ends.
- Keep `sync_to_animation: false` as the independent timer compatibility mode.
  Only install the animation hook when a supported engine actually needs it.
- Save format 3 rejects earlier timing state. Update setup hints in all nine
  languages; the GUI remains a single file picker.

Infantry/mounted/hunter native timing, custom GM1 projectiles and build-menu
decorations remain unfinished. Live rendering and multiplayer checks are pending.

## 1.5.0 (unreleased, work in progress)

- Rename the module identifier to `custom-projectiles`.
- Make stance intervals independently enable firing and use `interval` only as
  a fallback. Add separate regular/cow ammunition and fortification overrides.
- Correct `firethrower_pot` to entity 34 and extend the verified projectile catalog.
- Make explicit `inaccuracy_tiles: 0` / `inaccuracy: 0` remove native ground and
  height-dependent aim error. Omission keeps native error; unchanged cow orders
  retain their original behavior.
- Interpret inaccuracy as a bounded circular radius, with 8 micro units per tile,
  instead of additional square scatter. Keep volley `spread` independent.
- Update the schema, reference and all nine localized previews for accuracy.
- Use native coordinate units in the examples: `inaccuracy: 1` is an eighth-tile
  radius, `inaccuracy: 8` is one tile. Keep older whole-tile aliases compatible.

Reload-animation timing, custom sprites and placeable decoration triggers remain
in development. This entry does not announce a finished release.

## 1.4.0

- Replace every per-unit customization control with one standard FileInput.
- Make the selected YAML file authoritative; remove the legacy GUI merge code.
  Reject old hidden customizations/inline UCP unit settings with a migration error.
- Ship an inert vanilla template containing all 77 units and a commented reference
  to every one of the 30 supported settings. Omitted units/fields remain valid.
- Follow UCP's normal required-value/suggested-value and omitted sparse-setting
  semantics on the file selection; include standard plugin configuration examples.
- Replace long preview text with short localized instructions in all nine languages.
- Retain native hooks, scheduling, save-state format and projectile settings syntax.


## 1.3.2

- Fix untranslated `{{...}}` labels in installed ZIP modules: include the explicit
  `locale/` directory entry required by UCP's locale discovery, matching Legacy.
- Validate directory entries during packaging. Add archive integration tests
  through the launcher's ZIP handle, locale discovery and localization code;
  reproduce the broken archive and verify every supported language against the
  packaged Legacy reference. Earlier component tests bypassed ZIP discovery.
- No changes to runtime Lua, settings, native hooks or translation keys.


## 1.3.1

- Complete all nine GUI languages, including 121 customization strings per
  language, all unit names, dropdown choices, help and module descriptions.
- Merge into Legacy's exact Balance Changes category; use one collapsed section,
  five unit families, native dropdowns and optional sword-checkbox sliders.
- Reduce the visible form to six common controls per unit plus relevant crew
  counts. Keep specialist settings in the optional YAML file and add an editor
  schema. Native configuration parsing still accepts older advanced overrides.
- Document the Rebalancer ownership decision and GUI audit. No native hook,
  scheduler, save-state or configuration parser changes in this release.


- Add per-unit GUI controls in Balance Changes, using UCP's existing widgets;
  include complete English and German option strings.
- Retain YAML presets and allow enabled GUI controls to override them.
- Reject unknown keys, unsafe IDs, non-integers, out-of-range values and conflicting
  settings before native code is patched. Keep unused configurations inert.
- Fix scratch variables overwriting the first candidate entries.
- Bound unit scans to 2500 slots in Crusader and 10000 in Extreme instead of
  interpreting adjacent Crusader memory as extra units. Size per-unit storage
  accordingly and verify the native capacity before installation.
- Restore target coordinates and native targeting fields after automatic shots,
  failed searches, failed acquisition and boarding vetoes.
- Exclude neutral/allied/dead/transitioning candidates; only living, owned units
  receive automatic attacks. Verify placed-tower type, ID bounds and UID.
- Use current manned-engineer count, not engineers dispatched or stale references.
- Reset reused unit slots by UID, owner and type. Initialize stationary units
  correctly instead of treating their initial coordinates as movement.
- Preserve pending volleys through animation waits and missing targets. Count
  down the main interval while a staggered volley is firing.
- Make configured counts replace native mangonel volleys instead of multiplying
  each of the seven native projectile calls.
- Default timed attacks to suppress native shots, avoiding accidental double
  fire; keep the native projectile when an interval alone is selected.
- Apply height/inaccuracy-only native settings. Preserve native cow mode for
  count-only changes; make explicit projectile choices take precedence over it.
- Save timers, pending shots, movement, identity and deterministic random state
  with map-extensions; validate saved sizes, ranges and configuration before writes.
- Resolve bounded, unique signatures on demand and verify the unit-array base.
  Compile every injected routine before installing the entry hooks; reject repeat
  enable/hot reconfiguration. Split routines to fit the framework assembler budget.
- Add original-executable x86 tests, real GUI component tests and reproducible
  packaging. Live multiplayer and broad gameplay acceptance remain outstanding.

## Migration from 1.2.0

Unknown/misspelled settings now stop startup instead of being skipped or clamped.
Numeric values must be integers within the documented bounds. Do not set both
micro-unit and tile aliases for one setting. A timed attack suppresses native
shots unless `suppress_default: false` is explicit. This prevents an unexpected
second firing schedule. The mangonel's configured count is now its total volley.
The old module had no custom save state; old saves start with fresh firing timers.

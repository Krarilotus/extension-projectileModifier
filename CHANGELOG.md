# 1.3.0 (local test candidate)

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

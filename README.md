# Projectile Modifier 1.3.2

Configure projectiles, volley sizes and automatic firing intervals, including
for units without an original ranged attack. Based on the supplied Projectile
Modifier 1.2.0 by Monsterfish.

Requires **UCP 3.0.7+**, **map-extensions 1.x**, and **Crusader / Extreme 1.41**.
This is a local test candidate; [VALIDATION.md](VALIDATION.md) records automated
evidence and the remaining live-game acceptance cases.

## Installation and GUI

Import `projectileModifier-1.3.2.zip` through the launcher's local extension import,
or extract it into `ucp/modules/projectileModifier-1.3.2/`. Enable the module and
its dependency. This unsigned development archive requires UCP's development
module-loading mode; it is not a store-signed release.

Open **Balance Changes → Projectiles**. Expand a family, then a unit. All 77
unit IDs remain available in five collapsed families. Each unit exposes projectile,
count, automatic interval, range, targets and spread; crew-operated siege engines
also expose the required engineer count. Sword checkboxes enable numeric
overrides, dropdowns select projectile/target enums, and help stays collapsed or
in native tooltips. The module uses stock `GroupBox`, `Choice`, `UCP2Slider` and
`FileInput` views; no custom menu styling is required.

Version 1.3.2 fixes locale loading from ZIP archives. Replace the 1.3.1 module
with this version, refresh the extension list (or restart the launcher), and
ensure only 1.3.2 is active. No manual editing of translation files is needed.

All nine GUI languages are included: English, German, French, Russian, Hungarian,
Turkish, Chinese (`ch`), Spanish and Persian (`fa`). Every visible customization
string, unit name, choice, tooltip and module description is localized. The
category name intentionally matches Legacy's English fallback in this checkout,
so the settings merge into its existing Balance Changes category.

For a catapult firing three mangonel stones, select **Catapult → Projectile →
Mangonel stone**, enable **Projectiles per volley**, and enter **3**. Leave the
interval disabled to keep the original attack timing.

For an armed siege tower, select a projectile and enable **Automatic firing
interval**. Set its volley count and range. Set
**Required engineers** to **4** to require a full crew. Without that setting,
custom fire is allowed on an uncrewed engine.

An optional YAML picker accepts the original `units: {Unit name: settings}`
format. [example-projectiles.yml](example-projectiles.yml) demonstrates both
cases. Enabled GUI controls override the file. Disabled sliders and “Unchanged /
use file setting” preserve file values. With no file and no overrides the module
does not scan, allocate memory or install hooks. Change settings by relaunching
the game; hot reconfiguration is not supported.

## Behavior

- `projectile` alone replaces native shots; it does not make a melee unit fire.
- `count` sets 1–64 projectiles per volley. It replaces the mangonel's native
  seven-projectile volley. Leaving count unset preserves native volley size.
- `interval` enables automatic fire, using the native projectile or arrows for
  units without one unless a projectile is selected. Native shots are suppressed
  by default. Set `suppress_default: false` to combine automatic and native fire.
  Set it true without an interval to disarm native fire.
- Intervals use simulation ticks, not milliseconds. Wall-clock timing depends
  on game speed and pauses. The first eligible shot is immediately ready.
- Moving/standing overrides require `interval`. Zero holds fire in that state.
  Movement lasts 20 ticks after the last measured step. New stationary units
  start stationary. Unmanned or hold-fire units pause their firing timers.
- Staggering fires one projectile now and queues the rest. The main interval
  advances during the volley; volleys cannot overlap. Target loss and animation
  waits do not consume queued projectiles.
- Automatic fire adds targeting and projectiles, not new unit animations or
  manual attack commands. Native collision, damage and entity allocation remain
  owned by the game.

## Settings reference

The GUI exposes the common settings. **Advanced configuration file (optional)**
accepts all specialist settings below, including movement intervals, staggered
volleys, animation timing and booleans. This follows Rebalancer's file-based
preset approach while retaining this module's native scheduler. The complete
reference is a table; it is not duplicated into a long panel for every unit.
`spread` and `inaccuracy` use eight micro units per tile. Numeric values must be integers.
Invalid values, unknown names and contradictory settings fail before hooks are
installed. [all-settings-reference.yml](all-settings-reference.yml) is a valid
advanced example. Copy only the fields needed for your configuration. The included
[projectile-config.schema.json](projectile-config.schema.json) supplies editor
completion, field bounds, known unit names and dependency checks. The examples
include a YAML language-server schema comment; keep the schema beside your file
or update that relative path. Lua additionally checks cross-field comparisons.
GUI overrides apply before runtime validation, so the editor validates the file
as a standalone preset; keep required companion values in the file for clarity.

The native runtime also still accepts advanced GUI values saved by 1.3.0. If
migrating such a configuration, move the enabled specialist values into your
preset and reset those old overrides before editing through the file. See
[GUI-AUDIT.md](GUI-AUDIT.md) for the layout and compatibility decisions.

| Setting | Values and defaults |
|---|---|
| `projectile` | `arrow`, `catapult_rock`, `trebuchet_rock`, `mangonel_pebble`, `crossbow_bolt`, `ballista_bolt`, `cow`, `slinger_stone`, `firethrower_pot`, `firethrower_pot_untargeted`, `fire_ballista_bolt`; their known numeric IDs are also accepted |
| `count` | 1–64; unset preserves native volley size |
| `interval` | 1–60000 ticks; enables automatic fire |
| `interval_moving`, `interval_standing` | 0–60000; inherit interval; zero holds fire |
| `targets` | One to four distinct target kinds in priority order; default `units` |
| `range` | 1–100 tiles, default 20; automatic targeting only |
| `spread_tiles`, `inaccuracy_tiles` | 0–100 tiles; default 0 |
| `spread`, `inaccuracy` | 0–800 micro units; alternatives to the corresponding tile values |
| `wall_min_distance` | 0–100 tiles; default 3 |
| `require_manned` | 0–4 engineers currently aboard; `true` means 1, `false` means 0 |
| `random_targets` | Boolean; picks a candidate per projectile; default false |
| `shoot_height` | 0–500 added native height units; default 0 |
| `stagger_min`, `stagger_max` | Minimum 1–60000, maximum 0–60000 ticks; maximum 0 disables staggering; requires interval |
| `density_min`, `density_radius` | 1–256 enemies (default 1), within 1–100 tiles (default 5) |
| `attached_interval` | 0–60000 ticks; inherits ordinary interval; zero holds fire |
| `attached_ignore_crew` | Boolean; default true |
| `attached_stop_when_boarded` | Boolean; default true; proximity approximation using target candidates |
| `attached_board_radius` | 0–100 tiles; default 2 |
| `ai_only` | Boolean; all settings for this type apply only to AI owners; default false |
| `ai_cow_vs_units` | Boolean; automatic unit-targeted shots use cows if the owner's AIC enables them; default false; does not enforce the AIC cow interval |
| `preload` | Boolean; more frequent target searches after reload; default false |
| `preload_poll` | 1–60000 ticks, default 5; ordinary retries take at most 20 ticks |
| `sync_to_animation` | Boolean; waits for an animation cycle; default false |
| `sync_max_wait` | 1–60000 ticks, default 40; fires when this wait expires |
| `suppress_default` | Boolean; defaults true with an interval, false otherwise |

Spread offsets additional projectiles in simultaneous volleys; inaccuracy offsets
every projectile, including first and staggered shots. Scattered aim coordinates
are clamped and use the destination ground height.

Targets: `units`, `cluster`, `buildings`, `fortifications`, `siege_towers`, `walls`.
Unit scans exclude neutral owners, allies, dead and transitioning units. Cluster
and random targeting consider at most 256 candidates in slot order. Building
scans exclude allies. **Wall targeting includes your own walls**; minimum distance
does not establish ownership. The simple preset targets enemy units only.

Attachment requires a siege tower linked to a live placed-tower building with
the matching UID. Boarding detection is proximity to target candidates, not a
native climbing-state check. See the live visibility/boarding acceptance cases.

## Saves and compatibility

The `map-extensions` section saves the random generator, identities, cooldowns,
movement tracking and pending volleys. New maps and saves without this section
initialize fresh state. Saved state with different settings is rejected: restore
the settings used to make the save. Loading with this module disabled does not
retain its gameplay changes.

Rebalancer damage, speed and projectile physics tables remain owned by Rebalancer.
This module hooks the unit projectile dispatcher and unit-update loop. A module
replacing either site conflicts; startup rejects a missing signature. Read-only
reference comparison does not prove compatibility with every mod combination.

Multiplayer peers need identical versions and settings. Scheduling and random
state are deterministic, but live multiplayer, recorder integration, visibility
edge cases and long sessions still need the tests listed in VALIDATION.md.

## Development

Maintain translations in `locale/*.yml`. Generate and validate options with
`python tools/generate_options.py` (lupa, PyYAML); incomplete or obsolete catalogs
fail the build. Generate the editor schema with `python tools/generate_schema.py`.
Test: `python -m unittest discover -s tests -p "test_*.py" -v` (lupa, pefile,
unicorn, capstone, PyYAML, jsonschema). `SHC_REFERENCE_DIR` selects licensed 1.41 executables;
`FASM` selects FASM.EXE. Tests use production Lua/FASM and the original native
dispatcher/acquisition code with an observed entity-spawner stand-in. The 62 KiB
assembler test budget is below UCP's 64000 bytes.

GUI tests use the adjacent UCP3-GUI-extension-dependents checkout. Point this
module's development node_modules at that checkout's installed dependencies and
run `node ../UCP3-GUI-extension-dependents/node_modules/vitest/vitest.mjs run --config tests/gui.config.mjs`.
Selectors, sliders and localization are real GUI components; application state
and host integrations are test substitutes.

Build: `python tools/package.py`. Only explicitly listed runtime/docs files are
archived, including explicit parent directory entries required by UCP locale
discovery. The script records SHA-256; it does not sign, publish or install.

The archive integration suite uses the real UCP ZIP handle and locale discovery
code with a native-bridge substitute that reads actual ZIP entries. It reproduces
the missing-directory failure and checks the repaired ZIP in every language
against a packaged Legacy module. `UCP_TEST_PYTHON` selects Python and
`UCP_TEST_LEGACY_ZIP` selects the reference Legacy archive.

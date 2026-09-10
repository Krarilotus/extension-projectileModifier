# Projectile Modifier 1.4.0

Configure projectile types, volley sizes and automatic firing for all 77 unit
types using one readable YAML file. Based on Monsterfish's supplied 1.2.0 module.
Requires UCP 3.0.7+, map-extensions 1.x and Crusader/Extreme 1.41.

## Installation and use

Import `projectileModifier-1.4.0.zip` into the launcher and enable the module and
map-extensions. This unsigned local test candidate requires development module
loading. It is not a signed store release; see VALIDATION.md for test limits.

There is **one file picker** under **Customizations → Balance Changes**. There
are no per-unit sliders, dropdowns, checkboxes or hidden override controls.
The picker and short module-preview instructions are localized in all nine GUI
languages: de, en, fr, ru, hu, tr, ch, es and fa. The shared category matches
Legacy's displayed category name, including its English fallback.

1. Extract `vanilla-projectiles.yml` and `projectile-config.schema.json` from the
   module ZIP. Copy them into your game's `ucp/resources/projectileModifier/`
   directory, creating it if needed. Keep your editable file outside the module
   archive so replacing the module does not overwrite your settings.
2. Edit the copy, then select it with the file picker. The vanilla file lists all
   77 units with empty `{}` mappings and documents all 30 settings in comments.
   It makes no changes until you add settings. To edit a unit, replace its `{}`
   with indented fields.
3. Restart the game after changing the selected file or its contents. No live
   reconfiguration is supported. An empty file path means this module makes no
   changes, unless another UCP preset supplies a path through normal resolution.

For example, this complete file makes catapults fire three mangonel stones while
keeping their original firing schedule:

```yaml
units:
  Catapult:
    projectile: mangonel_pebble
    count: 3
```

`example-projectiles.yml` also arms a siege tower. `all-settings-reference.yml`
is an active advanced example. The vanilla template is the no-change starting
point; it preserves other modules rather than reverting their balance changes.

Missing units and missing fields are allowed. Empty unit mappings are ignored.
Omission preserves native behavior, except that explicitly enabling an automatic
interval activates the documented automatic-fire defaults. Do not use null,
`undefined`, required-value or suggested-value inside projectile settings.
Wrong names, types, bounds and contradictory settings fail before native hooks.
Negative scatter radii are invalid; zero means no added scatter.

## UCP required, suggested and unspecified settings

The file picker uses the standard Rebalancer-style UCP option:
`projectileModifier.projectile_config_file_selector`. UCP resolves its qualifiers
before passing a plain path to the module. The projectile file is one preset;
UCP does not merge or lock its individual numeric fields.

| UCP configuration | Meaning |
|---|---|
| `contents.required-value: path` | Require this path; native GUI locks apply. Conflicting required paths are handled by UCP. |
| `contents.suggested-value: path` | Suggest this path; normal user/preset overrides remain possible. |
| Option omitted from `config-sparse` | Unspecified: inherit other active presets or the empty default. There is no invented `undefined-value` syntax. |
| `contents.value: path` in `config-full` | The launcher's resolved value passed to the module. |
| Explicit empty string | Select no projectile changes; may itself be required or suggested. This is different from omitting a sparse setting. |

For a balance plugin's standard `config.yml`:

```yaml
meta:
  version: 1.0.0
config-sparse:
  modules:
    projectileModifier:
      config:
        projectile_config_file_selector:
          contents:
            suggested-value: ucp/plugins/MyBalancePreset-*/projectiles.yml
  plugins: {}
```

Use your actual plugin name, ship `projectiles.yml` in that plugin and declare a
dependency on projectileModifier in its definition. Full required, suggested and
unspecified examples are supplied in `examples/ucp-plugin-*.yml`. These are UCP
configuration examples, **not projectile files to select in the picker**.

The GUI's normal qualifier/reset controls remain available in creator mode.
Reset removes the local sparse choice and returns to resolved preset defaults.
A required path locks selection, not edits to an external file. Distribute the
same preset contents to every multiplayer tester, preferably as a versioned
balance plugin; identical path strings alone are insufficient.

## Upgrade from 1.3.x

Move any enabled per-unit GUI values to the YAML file. Then remove obsolete
`customizations` or inline `units` entries from projectileModifier in your UCP
`config-sparse` and `config-full` sections, or recreate that module's settings.
Only keep `projectile_config_file_selector`. The runtime rejects old overrides
with a migration message rather than silently applying invisible settings.
The original projectile YAML format (`units: ...`) remains supported.

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

## Complete settings reference

All settings are optional. Keep the schema next to the YAML file for editor
completion and validation; Lua also checks cross-field comparisons.

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

Maintain translations in `locale/*.yml`. `python tools/generate_options.py`
validates all nine catalogs and emits the single native file picker.
`python tools/generate_vanilla.py` builds the inert template from the runtime's
unit list; `python tools/generate_schema.py` builds editor bounds/completions.
The complete settings table above remains the behavioral reference.

Build an unsigned ZIP with `python tools/package.py` (lupa and PyYAML required).
The standard UCP `files.xml` manifest and development package are checked for
agreement. Explicit ZIP directory entries are retained for locale discovery.

Run `python -m unittest discover -s tests -p "test_*.py" -v` with lupa, pefile,
unicorn, capstone, PyYAML and jsonschema installed. `SHC_REFERENCE_DIR` selects
licensed 1.41 executables and `FASM` selects FASM.EXE. Native tests execute
production Lua/FASM and original dispatcher/acquisition code in an emulator;
the projectile spawner is an observed stand-in, not a rendered game session.

GUI tests use the adjacent UCP3-GUI-extension-dependents checkout and its installed
dependencies (point this module's development node_modules there). Run:
`node ../UCP3-GUI-extension-dependents/node_modules/vitest/vitest.mjs run --config tests/gui.config.mjs`.
They use real FileInput, qualifier/reset controls, UCP serialization and merge
rules. Host services/state storage are test substitutes. Archive tests use the
real ZIP handle/discovery TypeScript with an exact-entry native-bridge substitute.
`UCP_TEST_PYTHON` selects Python; `UCP_TEST_LEGACY_ZIP` selects packaged Legacy.

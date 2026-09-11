# Custom Projectiles 1.8.1 (test candidate)

Configure projectile types, volley sizes and automatic firing for all 77 unit
types using one readable YAML file. Based on Monsterfish's supplied 1.2.0 module.
Requires UCP 3.0.7+, Crusader/Extreme 1.41 and the declared map-extensions,
gmResourceModifier, protocol and ui dependencies (the launcher resolves them).
The ui dependency requires version 1.0.1 or later and launcher 1.0.12 or later.
UI 1.0.0 has a native menu-array overrun that can crash startup.
Until [the UI fix](https://github.com/gynt/ucp-extension-ui/pull/6) reaches the
store, import its unsigned `ui-1.0.1.zip` before this candidate. The tester bundle
includes that dependency built from commit `d3a807cfee70308f707ea81ddb92ac8b1d375bd9`.

## Installation and use

Import `custom-projectiles-1.8.1.zip` into the launcher and enable the module and its dependencies. This unsigned local test candidate requires development module
loading. It is not a signed store release; see VALIDATION.md for test limits.

Native reload timing covers catapults, trebuchets, mangonels, both ballistas,
European/Arabian foot archers, crossbowmen, slingers, firethrowers, horse archers
and hunters. Named GM1 variants and placeable decoration triggers are implemented.
See VALIDATION.md for the distinction between automated and live acceptance.

There is **one file picker** under **Customizations → Balance Changes**. There
are no per-unit sliders, dropdowns, checkboxes or hidden override controls.
The picker and short module-preview instructions are localized in all nine GUI
languages: de, en, fr, ru, hu, tr, ch, es and fa. The shared category matches
Legacy's displayed category name, including its English fallback.

1. Extract `vanilla-projectiles.yml` and `projectile-config.schema.json` from the
   module ZIP. Copy them into your game's `ucp/resources/custom-projectiles/`
   directory, creating it if needed. Keep your editable file outside the module
   archive so replacing the module does not overwrite your settings.
2. Edit the copy, then select it with the file picker. The vanilla file lists all
   77 units with empty `{}` mappings and documents the settings in comments.
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
Negative scatter radii are invalid. Explicit zero accuracy removes random aim
error; zero spread adds no volley spread.

## UCP required, suggested and unspecified settings

The file picker uses the standard Rebalancer-style UCP option:
`custom-projectiles.projectile_config_file_selector`. UCP resolves its qualifiers
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
    custom-projectiles:
      config:
        projectile_config_file_selector:
          contents:
            suggested-value: ucp/plugins/MyBalancePreset-*/projectiles.yml
  plugins: {}
```

Use your actual plugin name, ship `projectiles.yml` in that plugin and declare a
dependency on custom-projectiles in its definition. Full required, suggested and
unspecified examples are supplied in `examples/ucp-plugin-*.yml`. These are UCP
configuration examples, **not projectile files to select in the picker**.

The GUI's normal qualifier/reset controls remain available in creator mode.
Reset removes the local sparse choice and returns to resolved preset defaults.
A required path locks selection, not edits to an external file. Distribute the
same preset contents to every multiplayer tester, preferably as a versioned
balance plugin; identical path strings alone are insufficient.

## Upgrade from projectileModifier

Enable only `custom-projectiles`, disabling the old `projectileModifier` module.
Move its file-selector settings and plugin dependency to the new module ID.
Existing YAML preset paths may stay where they are; the new resource folder is
a suggested location. Start a new match: saved simulation state uses format 5
and deliberately rejects older states with different timing semantics. The internal save-section key
remains `projectileModifier` so old state is detected instead of silently reset.

For profiles from 1.3.x:

Move any enabled per-unit GUI values to the YAML file. Then remove obsolete
`customizations` or inline `units` entries from projectileModifier in your UCP
`config-sparse` and `config-full` sections, or recreate that module's settings.
Only keep `projectile_config_file_selector`. The runtime rejects old overrides
with a migration message rather than silently applying invisible settings.
The original projectile YAML format (`units: ...`) remains supported.

## Behavior

- `projectile` alone replaces regular native shots; it does not make a melee unit fire.
- `cow_projectile` and `cow_count` separately change siege cow ammunition.
  If omitted, native cows remain unchanged, including their single-shot count,
  even when normal catapult stones are replaced by three mangonel pebbles.
- `count` sets 1–64 projectiles per volley. It replaces the mangonel's native
  seven-projectile volley. Leaving count unset preserves native volley size.
- `interval` enables automatic fire, using the native projectile or arrows for
  units without one unless a projectile is selected. For the twelve native shooters
  listed above, it controls starts of volleys on their native
  firing frame. Reload proceeds during the interval, then waits before release.
  Short intervals cannot cut the native animation cycle short. The mangonel
  retains seven projectiles when `count` is omitted.
- These twelve unit types use native animation timing by default. Horse archers
  have a separate bow clock, preserving their movement animation. Hunters keep
  their non-shooting work states and turn toward configured targets. Other native
  shooters finish movement before attacking. `sync_to_animation: false` selects
  the independent timer, including automatic fire while moving. Other unit types
  retain that timer by default; adding projectiles does not invent a new animation.
- Native cooldowns continue during stance/crew holds; release waits until the
  unit is eligible. A loaded foot shooter rechecks its configured target before
  release. Target loss earlier in wind-up may restart the native attack cycle.
- `suppress_default` defaults true with an interval. False combines native and
  automatic shots only with the independent timer; it cannot bypass a native
  reload interval. True without an interval disarms regular native fire.
- Intervals use simulation ticks, not milliseconds. Wall-clock timing depends
  on game speed and pauses. Native timing starts the first windup immediately
  when eligible; independent timers can release their first shot immediately.
- Each moving/standing/docked interval can enable automatic fire independently.
  `interval` is only a fallback where no matching state override applies.
  With neither a state override nor a fallback, hold fire. Explicit zero also
  holds fire. Docked `attached_interval` takes precedence over moving/standing.
  Movement lasts 20 ticks after the last measured step. New stationary units
  start stationary. Unmanned or hold-fire units pause their firing timers.
- Staggering fires one projectile now and queues the rest. The main interval
  advances during the volley; volleys cannot overlap. Target loss and animation
  waits do not consume queued projectiles.
- Automatic fire adds targeting and projectiles, not new unit animations or
  manual attack commands. Native collision, damage and entity allocation remain
  owned by the game.
- `on_fortification` is a sparse mapping overriding the unit's settings only
  while it stands on a wall/fortification. It requires positive structure height
  and the native tile flags; hills and ground beside walls do not qualify.
  Missing fields inherit the base settings. Leaving cancels queued conditional
  shots while preserving the main cooldown.

## Complete settings reference

All settings are optional. Keep the schema next to the YAML file for editor
completion and validation; Lua also checks cross-field comparisons.

| Setting | Values and defaults |
|---|---|
| `projectile`, `cow_projectile` | Native names/IDs below, or a name defined in `projectiles`; cow ammunition is independent |
| `count` | 1–64; unset preserves native volley size |
| `cow_count` | 1–64; unset preserves one native cow |
| `near_decorations` | Ordered list of sparse rules, each with a `decoration` name; first nearby match wins; cannot nest triggers |
| `on_fortification` | Sparse mapping of the same settings; inherits base fields; cannot nest itself |
| `interval` | 1–60000 ticks; optional fallback automatic-fire interval |
| `interval_moving`, `interval_standing` | 0–60000; independently enable firing; inherit fallback or hold fire if omitted |
| `targets` | One to four distinct target kinds in priority order; default `units` |
| `range` | 1–100 tiles, default 20; automatic targeting only |
| `spread`, `inaccuracy` | 0–800 whole native coordinate units: **1 = ⅛ tile, 8 = 1 tile** |
| `spread_tiles`, `inaccuracy_tiles` | Compatibility aliases, 0–100 whole tiles; use only one unit system per effect |
| `wall_min_distance` | 0–100 tiles; default 3 |
| `require_manned` | 0–4 engineers currently aboard; `true` means 1, `false` means 0. Native reload defaults: trebuchet 3, other supported engines 2; independent timer default 0. |
| `random_targets` | Boolean; picks a candidate per projectile; default false |
| `shoot_height` | 0–500 added native height units; default 0 |
| `stagger_min`, `stagger_max` | Minimum 1–60000, maximum 0–60000 ticks; maximum 0 disables staggering; requires any automatic-fire interval |
| `density_min`, `density_radius` | 1–256 enemies (default 1), within 1–100 tiles (default 5) |
| `attached_interval` | 0–60000 ticks while docked; omission keeps the moving/standing rate or fallback; zero holds fire |
| `attached_ignore_crew` | Boolean; default true |
| `attached_stop_when_boarded` | Boolean; default true; proximity approximation using target candidates |
| `attached_board_radius` | 0–100 tiles; default 2 |
| `ai_only` | Boolean; all settings for this type apply only to AI owners; default false |
| `ai_cow_vs_units` | Boolean; automatic unit-targeted shots use cows if the owner's AIC enables them; default false; does not enforce the AIC cow interval |
| `preload` | Boolean; more frequent target searches after reload; default false |
| `preload_poll` | 1–60000 ticks, default 5; ordinary retries take at most 20 ticks |
| `sync_to_animation` | Boolean; native reload timing defaults on for the twelve shooters listed above. False selects the independent timer. Other units default false; true uses their legacy bounded animation wait. |
| `sync_max_wait` | 1–60000 ticks, default 40; only the legacy animation wait, never a bypass of a native firing frame |
| `suppress_default` | Boolean; defaults true with any interval, false otherwise; unchanged native cow orders remain available |

| Projectile name | Native ID |
|---|---:|
| `arrow` | 1 |
| `catapult_rock` | 2 |
| `trebuchet_rock` | 3 |
| `mangonel_pebble` | 4 |
| `crossbow_bolt` | 7 |
| `ballista_bolt` | 20 |
| `cow` | 23 |
| `arrow_untargeted` | 24 |
| `crossbow_bolt_untargeted` | 25 |
| `slinger_stone` | 33 |
| `firethrower_pot` | 34 |
| `slinger_stone_untargeted` | 35 |
| `firethrower_pot_untargeted` | 36 |
| `fire_ballista_bolt` | 37 |
| `fire_arrow` | 91 |
| `fire_arrow_untargeted` | 92 |

The old `firethrower_pot` mapping to 35 was incorrect (a slinger variant); it is
now 34. Untargeted/burning modes may share the final entity type while differing
in native flags. Numeric IDs retain their native meaning.

Use `inaccuracy` for the maximum random aim-error **radius** in the game's native
coordinate units. Values are whole numbers: **1 = ⅛ tile, 4 = ½ tile, 8 = 1 tile**.
Write `inaccuracy: 1` for an eighth-tile radius, not `inaccuracy: 0.125` or `1/8`.
Older `_tiles` aliases remain readable for compatibility and multiply whole-tile
values by 8; do not combine both forms. An explicit **0 removes native random aim error**, including
siege ground scatter and height-dependent error. Omission preserves native error.
Native cow orders retain their own accuracy. Target prediction remains native:
exact aim is not a guarantee that a moving target will still be there at impact.

The configured radius applies once per projectile, including first and staggered
shots. `spread` independently offsets additional simultaneous projectiles on
each axis; set it to 0 as well if the entire volley should share an aim point.
Scattered aim coordinates are clamped to map limits and use destination ground
height. Unscattered shots retain their original target height.

Targets: `units`, `cluster`, `buildings`, `fortifications`, `siege_towers`, `walls`.
Unit scans exclude neutral owners, allies, dead and transitioning units. Cluster
and random targeting consider at most 256 candidates in slot order. Building
scans exclude allies. **Wall targeting includes your own walls**; minimum distance
does not establish ownership. The simple preset targets enemy units only.

Attachment requires a siege tower linked to a live placed-tower building with
the matching UID. Boarding detection is proximity to target candidates, not a
native climbing-state check. See the live visibility/boarding acceptance cases.

## Named projectiles and placeable decorations

`examples/custom-sprites-and-decorations.yml` is a runnable starting point. It
uses the game's existing sheets, so its names initially have the native look.
Copy a matching GM1 sheet, edit its artwork, and change `sprites` to your copy's
path relative to the game folder, for example `ucp/resources/custom-projectiles/frost.gm1`.
No game artwork is included in the module.

```yaml
projectiles:
  frost_arrow:
    inherits: arrow
    sprites: ucp/resources/custom-projectiles/frost-arrow.gm1
decorations:
  frost:
    label: Frost brazier
    sprites: ucp/resources/custom-projectiles/frost-brazier.gm1
units:
  European archer:
    near_decorations:
      - decoration: frost
        projectile: frost_arrow
        count: 2
```

Named projectiles inherit the base's damage, trajectory, speed, collision and
impact behavior. They change the flying projectile's sheet only; there are no
independent damage/speed fields. Use the name wherever `projectile` or
`cow_projectile` is accepted, including fortification and decoration rules.

| Base projectile or decoration | Required complete GM1 sheet | Images | GM1 type |
|---|---|---:|---:|
| Arrows, crossbow bolts, catapult/trebuchet/mangonel stones | `body_missile.gm1` | 184 | 2 |
| Ballista and fire-ballista bolts | `body_missile_2.gm1` | 144 | 2 |
| Cows | `body_missile_cow.gm1` | 29 | 2 |
| Fire arrows | `body_missile_fire.gm1` | 144 | 2 |
| Slinger stones and firethrower pots | `rock_chips.gm1` | 32 | 1 |
| Placeable decorations | `body_brazier.gm1` | 8 | 6 |

Preserve frame order, count, format and anchors. Type 2 uses indexed pixels and
its GM1 palette; types 1 and 6 use native RGB555 pixels. Frames must be
self-contained, without tiled/linked-image metadata. The loader validates
headers, dimensions, offsets and image tokens before handing pixels to the game.
It rejects missing files, incompatible sheets, absolute paths and parent traversal.

Open the **brazier button in the castle decorations build menu**. The standard
UCP modal offers the original brazier followed by the configured decorations,
eight choices per page. Select one, then place it with the normal brazier cursor.
Place on valid owned walls, towers or supported stone keeps; the starting
manor house cannot hold braziers. Native placement, cost and removal rules apply.
Omit a decoration's `sprites` to retain the native brazier appearance.
`label` is an optional short build-menu name (defaults to the configuration name);
use text supported by the installed game's font.

The first matching `near_decorations` rule wins. A match uses the native brazier
three-tile square in each axis and a height difference below 45 native height
units; ownership does not restrict proximity. Fortification fields are applied
first, then the winning rule's sparse fields. Missing fields inherit; rules do
not stack. Leaving a trigger cancels its pending volley without resetting the
main reload cooldown. Custom decorations do not enable native brazier fire arrows
unless the selected rule explicitly requests a fire projectile.

Names use lowercase letters, digits, `_` or `-`, starting with a letter, at most
48 characters. There are at most 33 projectile names, 33 decoration names and
33 rules per unit. Graphics share the remaining native GM slots: normally 33
for both features combined, fewer if another extension uses them. Identical
base-sheet/path pairs share one slot. Loading refuses occupied slots or a total
above the native 66,000-image capacity; it never overwrites another sheet.

All peers need the same module versions, YAML and sprite bytes. Saves record
variant identities and sheet hashes/slot bindings. Changing a sheet, name or
binding requires restoring the original files to load that save, or starting
a new match. Build selections travel in a lockstep command; remote execution
does not depend on another player's currently selected menu item.

## Saves and compatibility

The `map-extensions` section saves the random generator, identities, cooldowns,
movement tracking, pending volleys, mounted bow clocks and custom projectile/decoration identities. New maps and saves without this section
initialize fresh state. Saved state with different settings is rejected: restore
the settings used to make the save. Loading with this module disabled does not
retain its gameplay changes.

Rebalancer damage, speed and projectile physics tables remain owned by Rebalancer.
This module hooks native firing, timing and aim-error stages. When configured,
it also hooks entity rendering selection, GM loading and brazier placement/menu entry points. A module replacing these sites conflicts; startup
rejects missing or ambiguous signatures. Read-only
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
production Lua/FASM and original dispatcher/acquisition code in an emulator.
Most scheduling tests observe a spawner stand-in; the 77-unit × 16-projectile
matrix additionally executes actual native entity creation and first update.
Neither test path renders a game session.

GUI tests use the adjacent UCP3-GUI-extension-dependents checkout and its installed
dependencies (point this module's development node_modules there). Run:
`node ../UCP3-GUI-extension-dependents/node_modules/vitest/vitest.mjs run --config tests/gui.config.mjs`.
They use real FileInput, qualifier/reset controls, UCP serialization and merge
rules. Host services/state storage are test substitutes. Archive tests use the
real ZIP handle/discovery TypeScript with an exact-entry native-bridge substitute.
`UCP_TEST_PYTHON` selects Python; `UCP_TEST_LEGACY_ZIP` selects packaged Legacy.

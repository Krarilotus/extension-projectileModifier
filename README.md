# Custom Projectiles 1.8.6 (test candidate)

Configure projectile types, volley sizes and automatic firing for all 77 unit
types using one readable YAML file. Based on Monsterfish's supplied 1.2.0 module.
Requires UCP 3.0.7+, Crusader/Extreme 1.41 and the declared map-extensions,
gmResourceModifier, protocol and ui dependencies (the launcher resolves them).
The ui dependency requires version 1.0.1 or later and launcher 1.0.12 or later.
UI 1.0.0 has a native menu-array overrun that can crash startup.
UI 1.0.1 is available in the 3.0.7 store. The tester bundle's companion uses
the same source commit `d3a807cfee70308f707ea81ddb92ac8b1d375bd9`.

The [native integration audit](https://github.com/Krarilotus/extension-projectileModifier/blob/1d1b291/NATIVE-AUDIT.md) records the remaining work;
this branch does not replace the published 1.8.6 tester archive.

## Quick configuration guide

In VS Code, install the **YAML extension by Red Hat**. Keep
`projectile-config.schema.json` beside your editable YAML and put this on its
first line for completion, allowed values and validation:

```yaml
# yaml-language-server: $schema=./projectile-config.schema.json
```

Use the schema from the **same module build** as your configuration. The detailed
field table below explains every supported setting; the schema also catches
misspelled names and invalid types. Additional cross-field checks run at startup.

**Automatic attack is per unit type**, under `units`, not a separate GUI category.
The only GUI control is the file picker in **Customizations ? Balance Changes**.
A setting under `Catapult` applies to all catapults (or AI-owned catapults only
with `ai_only: true`), not one individually selected catapult.

| What you want | What to edit |
|---|---|
| Change ordinary ammunition | `projectile`; omit `cow_projectile` to leave cows alone |
| Change cow ammunition separately | `cow_projectile` and `cow_count` |
| More shots in one volley | `count`; `spread` offsets additional simultaneous shots |
| Longer time between volleys | `interval`, measured in simulation ticks, not milliseconds; game speed changes real elapsed time |
| Fire only while standing | `interval_standing: 700`, `interval_moving: 0` |
| A fallback rate for other stances | `interval`; moving/standing/docked overrides take precedence; zero on an override holds fire |
| Automatically search for buildings | `targets: [buildings, units]`; first kind that finds a target wins; boulders alone do not enable building searches |
| Search distance | `range` in tiles for the module's automatic search; this is not the native manual-order range override |
| Exact aim | `inaccuracy: 0` and `spread: 0`; moving targets can still move before impact |
| An eighth-tile aim-error radius | `inaccuracy: 1`; **8 native coordinate units = 1 tile**; use whole numbers |
| Restrict changes to AI owners | `ai_only: true`; this controls whose settings change, not an autonomous-fire toggle |
| Different behavior on walls | Put sparse overrides under `on_fortification` |
| Fire near a decoration | Add an ordered `near_decorations` rule; see the GM1 example below |

This complete example replaces catapult stones with three mangonel pebbles,
leaves cow ammunition unchanged, and enables automatic building-then-unit
searches while stationary:

```yaml
# yaml-language-server: $schema=./projectile-config.schema.json
units:
  Catapult:
    projectile: mangonel_pebble
    count: 3
    interval_standing: 700
    interval_moving: 0
    targets: [buildings, units]
    range: 30
    inaccuracy: 0
    spread: 0
```

Keep native animation synchronization enabled for siege engines. A short interval
cannot skip native aiming/reload/firing frames; turning or missing crew may delay
release. A human's explicit native attack order takes priority over automatic
search priorities. `cluster` adds a density threshold for AI owners.

**Build distinction:** the existing 1.8.6 tester uses omission or `{}` to leave
settings alone. The follow-up development branch adds `native` for dynamic rules,
`auto_targeting: false` to disable autonomous attacks per unit type while retaining
human manual orders, and `strict_range`. Those fields require that follow-up
build and its schema; they are not supported by the old downloadable 1.8.6 ZIP.
Neither source merging nor committing the pending movement/aiming fixes publishes
a tested release. See [VALIDATION.md](VALIDATION.md) for acceptance limits.

Only `units`, `projectiles` and `decorations` belong at the top of a projectile
file. Do not paste GitHub workflow keys (`name`, `on`) or UCP `config-sparse`
wrappers into it. Use spaces for indentation and restart the game after edits.

## Installation and use

Import `custom-projectiles-1.8.6.zip` into the launcher and enable the module and its dependencies. This unsigned local test candidate requires development module
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
   77 units with every canonical setting written explicitly. `native` delegates
   that field to the game instead of replacing its dynamic rules. The unchanged
   file installs no hooks or timers. Replace individual `native` values to edit.
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
`native` explicitly leaves a field unmodified, like omission. In a conditional
override it clears that field's configured base override. Enabling an automatic
interval still activates the documented module defaults: for example,
`range: native` with an interval uses the existing 20-tile automatic-search
default, not a fixed snapshot of the troop's vanilla range. The complete vanilla
file leaves the interval native as well, so the original range, height bonuses,
reloads, ammunition and autonomy remain owned by the game. Do not use null,
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
  firing frame. Reload proceeds during the interval. Catapults wait with their
  arm lowered; trebuchets wait in their loaded pose. Both pause before the swing
  and allow time for that swing before release;
  other shooters retain their release gate.
  Siege engines turn through their original aiming state before reloading;
  turning to a new target can delay a shot. Short intervals cannot cut the native
  aiming/reload/firing cycle short. The mangonel
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
| `range` | 1–100 tiles, default 20; automatic targeting only  Projectile choice does not change this limit. |
| `strict_range` | Default true; exact automatic range checks using unit positions, building centres and wall aim points. False restores rounded tile checks. |
| `auto_targeting` | False requires human attack orders, including without an interval. True permits native acquisition and configured automatic searches. Native preserves the game when no interval is set. |
| `spread`, `inaccuracy` | 0–800 whole native coordinate units: **1 = ⅛ tile, 8 = 1 tile** |
| `spread_tiles`, `inaccuracy_tiles` | Compatibility aliases, 0–100 whole tiles; use only one unit system per effect |
| `wall_min_distance` | 0–100 tiles; default 3 |
| `require_manned` | 0–4 engineers currently aboard; `true` means 1, `false` means 0. Native reload defaults: trebuchet 3, other supported engines 2; independent timer default 0. |
| `random_targets` | Boolean; picks a candidate per projectile; default false |
| `shoot_height` | 0–500 added native height units; default 0 |
| `stagger_min`, `stagger_max` | Minimum 1–60000, maximum 0–60000 ticks; maximum 0 disables staggering; requires any automatic-fire interval |
| `density_min`, `density_radius` | AI cluster threshold: 1–256 enemies (default 1), within 1–100 tiles (default 5) |
| `attached_interval` | 0–60000 ticks while docked; omission keeps the moving/standing rate or fallback; zero holds fire |
| `attached_ignore_crew` | Boolean; default true |
| `attached_stop_when_boarded` | Boolean; default true; proximity approximation using target candidates |
| `attached_board_radius` | 0–100 tiles; default 2 |
| `ai_only` | Boolean; all settings for this type apply only to AI owners; default false |
| `ai_cow_vs_units` | Boolean; automatic unit-targeted shots use cows if the owner's AIC enables them; default false; does not enforce the AIC cow interval |
| `preload` | Boolean; more frequent target searches after reload; default false |
| `preload_poll` | 1–60000 ticks, default 5; ordinary retries take at most 20 ticks |
| `turn_before_shot` | Defaults true for human siege engines using native reload timing. Turns toward the current attack order while reloading, before firing. False preserves the previous module behavior. Native cow shots and automatic targeting keep their existing paths. |
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

For a catapult that fires firethrower pots only when commanded, while retaining
its original reload schedule:

```yaml
units:
  Catapult:
    projectile: firethrower_pot
    auto_targeting: false
```

Add `interval: 700` to slow repeated shots under native animation timing.
`auto_targeting: true` permits configured automatic search; an interval enables
that search for units which do not already have it. False also disables AI-owned
acquisition; `ai_only: true` can restrict the entire profile to AI owners.
Units without native attack commands cannot gain a manual attack button from
this switch. The unchanged vanilla file preserves each unit's own autonomy:
archers can defend themselves, while catapults retain their original orders.

Automatic range is measured to the unit position, building centre or wall aim
point before scattering. A projectile may land outside the radius because of
spread/inaccuracy, or continue flying after a target moves out of range; the
range check does not truncate native flight.

`cluster` applies its density threshold only to AI-controlled units. For a human
native shooter, its existing unit, building, ground or wall
attack order takes precedence over the search list. Native target acquisition
and the configured range still apply; random-target volleys do not redirect that
order. Without such an order, a human unit treats `cluster` like `units`, with no
density threshold. AI owners retain the configured search priorities and density.

At a human native release, the module uses the coordinates already supplied by
the game. It does not reacquire the target after the engine charges ammunition;
this preserves wall/ground/building orders when firing the last stone. Queued
shots finish that accepted aim without charging another stone.

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

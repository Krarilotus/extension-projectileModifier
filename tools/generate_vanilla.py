"""An inert preset with every legal unit name and a commented settings reference."""
from generate_options import ROOT, cfg, constants
import yaml

HEADER='''# yaml-language-server: $schema=./projectile-config.schema.json
# VANILLA / NO CHANGES
# Empty unit mappings are intentional: this file installs no projectile hooks.
# It preserves the game and other modules; it does not undo their balance changes.
# Copy this file and the schema into ucp/resources/custom-projectiles/ and select
# your edited copy in the launcher. Restart the game after changing a file.
#
# Replace a unit's {} with indented settings, for example:
#   Catapult:
#     projectile: mangonel_pebble
#     count: 3
# Missing units and missing keys are allowed. Do not write null/undefined for
# an omitted value. Unknown names and invalid values are errors, not defaults.
#
# FIELD REFERENCE (all fields optional; do not uncomment everything at once)
# Original attacks:
#   projectile: mangonel_pebble  # Replace the native projectile; no timer added.
#   count: 3                     # 1..64; omitted keeps native volley count.
#   cow_projectile: cow          # Optional separate replacement for cow ammunition.
#   cow_count: 1                 # 1..64; independent of regular count; default 1.
#   suppress_default: false      # Add native shots only in independent timer mode.
# Automatic attacks:
#   interval: 100                # Optional fallback; 1..60000 ticks, not ms.
#                                # Applies only without a matching state rate.
#   interval_moving: 200          # 0..60000; 0 holds fire while moving.
#   interval_standing: 100        # 0..60000; while stopped, not specifically docked.
#   targets: [units, buildings]   # 1..4 distinct kinds, in priority order.
#   range: 20                    # 1..100 tiles; automatic targeting only.
#   require_manned: 1            # 0..4 engineers aboard; true=1, false=0.
#   random_targets: false        # Pick per projectile; targets can repeat.
#   shoot_height: 0              # 0..500 extra native height units.
#   ai_only: false               # Restrict all this unit's changes to AI owners.
# Accuracy (whole native coordinate units: 1 = 1/8 tile, 8 = 1 tile):
#   spread: 0                    # 0..800; extra simultaneous shots, per-axis offset.
#   inaccuracy: 0                # 0..800 radius; 0 = exact aim, omitted = native error.
#                               # Example: inaccuracy: 1 gives a 1/8-tile radius.
#                               # Separate spread still applies.
# Older tile-unit aliases (optional; never combine with the matching native field):
#   spread_tiles: 0              # 0..100 whole tiles; prefer spread for finer steps.
#   inaccuracy_tiles: 0          # 0..100 whole tiles; prefer inaccuracy for finer steps.
# Staggered volleys:
#   stagger_min: 1               # 1..60000; requires stagger_max.
#   stagger_max: 0               # 0..60000; needs automatic fire; 0 disables.
#                                # When enabled, min must not exceed max.
# Cluster targeting:
#   density_min: 1               # 1..256 enemies; used by targets: cluster.
#   density_radius: 5            # 1..100 tiles around each candidate.
# Wall targeting:
#   wall_min_distance: 3         # 0..100 tiles; does NOT exclude your own walls.
# Docked siege towers (attached to a wall):
#   attached_interval: 100       # Overrides moving/standing; 0 holds fire.
#                                # Omission keeps moving/standing rate or fallback.
#   attached_ignore_crew: true   # Continue after engineers leave when attached.
#   attached_stop_when_boarded: true # Pause for nearby enemies (proximity test).
#   attached_board_radius: 2     # 0..100 tiles for that proximity test.
# Optional AI/timing behavior:
#   ai_cow_vs_units: false       # Automatic unit shots; checks owner's AIC cow flag.
#   preload: false               # Check targets more often when already loaded.
#   preload_poll: 5              # 1..60000 ticks between loaded target checks.
#   sync_to_animation: true      # Default for catapult/trebuchet/mangonel/ballistas:
#                               # native release frame; interval cannot cut the cycle.
#                               # false restores their old independent timer.
#                               # Other units default false; true uses legacy wait.
#   sync_max_wait: 40            # 1..60000; legacy wait only, not native reload.
#                               # Native crew defaults: trebuchet 3, other engines 2;
#                               # require_manned overrides them, including 0.
# Conditional override (a mapping, not a checkbox):
#   on_fortification:            # Only when standing ON a wall/fortification.
#     projectile: crossbow_bolt # Other fields inherit this unit's base settings.
#     count: 2
#                              # Stepping off restores the base settings.
#
# Any interval setting enables automatic fire; no base interval is required.
# With automatic fire, suppress_default defaults to true and projectile defaults
# to the native type (or arrow for units without one). In independent timer mode,
# set suppression false to supplement original attacks. In native reload mode,
# it cannot bypass the interval. Native engines finish moving before firing;
# use sync_to_animation: false for independent automatic fire while moving.
# Missing moving/standing intervals inherit interval, or hold fire without it.
# Docked towers keep that state rate unless attached_interval is set.
# Explicit zero in a state means hold fire, even when interval is present.
# Other automatic-fire defaults and exact bounds are in README.md.
# These are module settings, not UCP config.yml: do not put required-value or
# suggested-value wrappers here. UCP qualifiers apply to the FILE SELECTION.
# A required file path locks selection, not editing of the file's contents.
# Multiplayer peers must have identical files as well as identical paths.
#
'''

def generate():
    fields=set(cfg.numbers.keys())|set(cfg.booleans.keys())|{'projectile','cow_projectile','targets'}
    assert all(f'#   {name}:' in HEADER for name in fields)
    text=HEADER+'# Projectile names: '+', '.join(sorted(constants.projectile_names.keys()))+'\n'
    text+='# Target kinds: '+', '.join(sorted(constants.target_kinds.keys()))+'\n\n'
    text+=yaml.safe_dump({'units':{name:{} for _,name in sorted(constants.unit_names.items())}},sort_keys=False)
    (ROOT/'vanilla-projectiles.yml').write_text(text,encoding='utf-8',newline='\n')

if __name__ == '__main__': generate()

# Custom Projectiles 1.8.15

Long-range replacements: optional projectile_physics: {firethrower_pot: {mode: fixed_angle, angle: 30}} lets the native game compute launch speed. Requires active Rebalancer 1.1.3+ with a balance config. Global per type, including sprite variants; native preserves existing values. Target range and collisions still apply.

Gameplay edits can load existing saves; old module firing queues/timers reset. Custom graphics definitions must match. allow_config_changes_on_load: false requires the original settings. strict_range: false also disables the new manual range guard.

Automatic ammunition: define target lists in unit_groups, then ammo_by_target.groups: {siege: regular} per shooter, or ammo_by_target.units: {Monk: cow}. Exact units win; unmatched targets keep existing behavior. Requires an interval; native clears rules. Reconquista example included.

Configure all 77 unit types in YAML. Regular and cow ammunition are independent. Intervals respect supported firing animations; inaccuracy uses native units: 1 = 1/8 tile, 8 = 1 tile, 0 = exact aim.

Cluster thresholds apply only to AI; human attack orders remain available. For automatic unit targets, target_bias_tiles: {Monk: 3} treats monks as up to three tiles closer in the native score; range and other game rules still apply.

Copy the complete vanilla-projectiles.yml from the ZIP, edit it and select the copy. native preserves the game’s rules; an empty path changes nothing. auto_targeting: false requires manual attack orders. strict_range: false restores rounded range checks; turn_before_shot: false disables the turning correction. Required/suggested applies to the whole file selection. Restart after editing.

Custom sprites: add a name under projectiles with inherits and sprites (a complete matching GM1 sheet). Decorations: define decorations, then near_decorations rules for units; place them through the brazier button. See README.md and examples/custom-sprites-and-decorations.yml for formats. Use valid walls or towers; manor houses do not support braziers.

Requires UCP 3.0.7+, Crusader/Extreme 1.41 and the module dependencies. Test candidate; see VALIDATION.md.

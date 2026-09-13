# Custom Projectiles 1.8.6

Configure all 77 unit types in YAML. Regular and cow ammunition are independent. Intervals respect supported firing animations; inaccuracy uses native units: 1 = 1/8 tile, 8 = 1 tile, 0 = exact aim.

Cluster thresholds apply only to AI; human attack orders remain available.

Copy the complete vanilla-projectiles.yml from the ZIP, edit it and select the copy. native preserves the game’s rules; an empty path changes nothing. auto_targeting: false requires manual attack orders. strict_range: false restores rounded range checks; turn_before_shot: false disables the turning correction. Required/suggested applies to the whole file selection. Restart after editing.

Custom sprites: add a name under projectiles with inherits and sprites (a complete matching GM1 sheet). Decorations: define decorations, then near_decorations rules for units; place them through the brazier button. See README.md and examples/custom-sprites-and-decorations.yml for formats. Use valid walls or towers; manor houses do not support braziers.

Requires UCP 3.0.7+, Crusader/Extreme 1.41 and the module dependencies. Test candidate; see VALIDATION.md.

# Custom Projectiles 1.8.4

Configure all 77 unit types in YAML. Regular and cow ammunition are independent. Intervals respect supported firing animations; inaccuracy uses native units: 1 = 1/8 tile, 8 = 1 tile, 0 = exact aim.

Cluster thresholds apply only to AI; human attack orders remain available.

Copy vanilla-projectiles.yml from the module ZIP into ucp/resources/custom-projectiles/, edit the copy and select it here. Omitted settings stay unchanged; an empty path makes no changes. UCP required/suggested rules apply to the selected file as a whole. Restart the game after changes.

Custom sprites: add a name under projectiles with inherits and sprites (a complete matching GM1 sheet). Decorations: define decorations, then near_decorations rules for units; place them through the brazier button. See README.md and examples/custom-sprites-and-decorations.yml for formats. Use valid walls or towers; manor houses do not support braziers.

Requires UCP 3.0.7+, Crusader/Extreme 1.41 and the module dependencies. Test candidate; see VALIDATION.md.

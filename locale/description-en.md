# Projectile Modifier

Choose projectiles, volley sizes and automatic firing intervals for all 77 unit types. Catapults can fire mangonel stones; siege towers and melee units can gain an automatic ranged attack.

**Balance Changes → Projectiles**

Open a family, then a unit. Tick the sword checkbox to override a numeric value; expand the setting to read its help. Disabled settings preserve file values or the original behavior. Relaunch the game to apply changes.

Enables automatic fire, including for melee units and siege towers. Replaces native shots unless suppression is explicitly disabled. Uses the original projectile, or arrows for units without one. A tick is a simulation step, not a millisecond.

Targets for the interval attack. Units and buildings exclude allies. Wall targeting includes your own walls. Custom priority lists can be entered in the YAML file.

Load a YAML preset for advanced movement, staggered volleys, accuracy, height and animation settings. Enabled controls below override its values. Without a file, use the common settings. Examples and the complete table are in README.md; the editor schema is projectile-config.schema.json.

Requires UCP 3.0.7+, map-extensions 1.x and Crusader/Extreme 1.41. Timers and pending volleys are saved; loading requires matching settings. This unsigned 1.3.2 test candidate is based on Monsterfish’s 1.2.0. Live gameplay, multiplayer and recorder acceptance remain outstanding; see VALIDATION.md. The developer reference is in English.

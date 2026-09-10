# Custom Projectiles 1.6.0

Choose projectiles, volley sizes and automatic firing intervals for all 77 unit types. Catapults can fire mangonel stones; siege towers and melee units can gain an automatic ranged attack.

Copy vanilla-projectiles.yml from the module ZIP into ucp/resources/custom-projectiles/, edit the copy and select it here. Omitted settings stay unchanged; an empty path makes no changes. UCP required/suggested rules apply to the selected file as a whole. Restart the game after changes.

Requires UCP 3.0.7+, map-extensions 1.x and Crusader/Extreme 1.41. All 33 settings and 77 unit names are documented in vanilla-projectiles.yml and README.md. Local test candidate; live acceptance remains pending.

Accuracy: inaccuracy uses whole native coordinate units: 1 = 1/8 tile, 8 = 1 tile. 0 removes random aim error; omission keeps native accuracy. spread is separate.

Catapults, trebuchets, mangonels and ballistas: interval follows the firing animation and cannot shorten it. sync_to_animation: false restores the independent timer. Start a new match after upgrading.

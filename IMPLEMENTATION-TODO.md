# Remaining implementation

Only checked items have implementation evidence. This checklist is not a release
or live acceptance report; see VALIDATION.md for the test boundaries.

- [ ] Reload-animation timing
  - [x] Native artillery release hold: preserve release frame and ammunition
    (catapult, trebuchet, mangonel and both ballistas; both EXEs).
  - [x] Integrate siege interval/state/crew/target and volley scheduling.
  - [x] Preserve siege native cycle minimum, omitted mangonel count, cow settings,
    bounded target polling and saved continuation.
  - [ ] Cover native infantry and mounted ranged animations.
  - [ ] Live animation/crew/multiplayer acceptance and remaining ranged units.
- [ ] Named custom projectiles with independent GM1 sprites
  - [ ] Validate GM1 compatibility, native capacity and load ownership.
  - [ ] Implement per-projectile selection, persistence and config validation.
- [ ] Build-menu decorations with proximity projectile overrides
  - [ ] Synchronized variant selection, placement, removal and save/load.
  - [ ] Proximity/height checks and deterministic override precedence.
- [ ] Final localized instructions, private Reconquista tester preset and PR update.

Live rendering, multiplayer and replay acceptance remain separate from emulator
checks. Research or an isolated helper does not complete a feature.

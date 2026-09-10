# Remaining implementation

Only checked items have implementation evidence. This checklist is not a release
or live acceptance report; see VALIDATION.md for the test boundaries.

- [ ] Reload-animation timing
  - [x] Native artillery release hold: preserve release frame and ammunition
    (catapult, trebuchet, mangonel and both ballistas; both EXEs).
  - [x] Integrate siege interval/state/crew/target and volley scheduling.
  - [x] Preserve siege native cycle minimum, omitted mangonel count, cow settings,
    bounded target polling and saved continuation.
  - [x] Cover native foot infantry animations and loaded target handoff
    (European/Arabian foot archers, crossbowmen, slingers and firethrowers).
  - [ ] Cover mounted ranged animations without freezing movement.
  - [ ] Live animation/crew/multiplayer acceptance and remaining ranged units.
- [ ] Named custom projectiles with independent GM1 sprites
  - Scope agreed: inherit the native base's damage and flight behavior; custom
    sprites only. Do not add independent damage/speed settings.
  - [ ] Validate GM1 compatibility, native capacity and load ownership.
  - [ ] Implement per-projectile selection, persistence and config validation.
- [ ] Build-menu decorations with proximity projectile overrides
  - [ ] Synchronized variant selection, placement, removal and save/load.
  - [ ] Proximity/height checks and deterministic override precedence.
- [ ] Final localized instructions, private Reconquista tester preset and PR update.

Live rendering, multiplayer and replay acceptance remain separate from emulator
checks. Research or an isolated helper does not complete a feature.

## Next integration boundaries

- Horse archers share the main animation counter with movement. Hold only the
  weapon animation; do not freeze the horse's movement cycle. Hunters use a
  separate working/attack state machine and still need their own integration.
- Custom sprite scope is inherited native behavior plus a separate GM1 sheet.
  Native launch probes identify `body_missile` (184 images), `body_missile_2`
  (144), `body_missile_cow` (29), `body_missile_fire` (144), and `rock_chips`
  (32). The first four use GM1 type 2, rock chips type 1. A matching complete
  base sheet is the initial compatibility target, not arbitrary frame indices.
- Investigate cloning a loaded base sheet into unused GM slots, then applying
  gmResourceModifier's resource conversion/replacement. Its SetGm API alone
  cannot initialize an empty slot. Validate the actual post-load image count
  against the 66,000 image-header capacity, reserve unoccupied GM IDs below 240,
  and verify ownership, rendering, impact transitions and saved identity.
  The original filename list leaves 33 slots; other modules may use them.
- Decoration placement's native command carries only tile X/Y. A custom variant
  must travel through the synchronized command, not receiver-local UI state.
  Audit encoding/validation, menu placement, removal and save/replay paths before
  implementing a deterministic proximity index. This remains unimplemented.

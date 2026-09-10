# Implementation and acceptance checklist

Implementation is complete for the requested scope. Checked items have code and
automated evidence; live release acceptance is listed separately below.

- [x] Native reload timing for all 12 ranged types: five siege engines, five foot
  shooters, horse archers and hunters. Preserve release frames/minimum cycles,
  movement, stance/crew/target gating, volleys and saved continuation.
- [x] Configurable projectile behavior for all 77 unit types; independent regular
  and cow ammunition; stance-only rates and fallback intervals.
- [x] Native accuracy units: 0 exact, 1 = 1/8 tile, 8 = one tile; sparse wall overrides.
- [x] Named custom projectiles inheriting native damage/flight behavior, with
  independent complete GM1 sprites, format/capacity checks and saved identities.
- [x] Build-menu decoration selection using the standard UCP modal and native
  brazier cursor, deterministic lockstep payload, cost/ownership checks and removal.
- [x] Ordered decoration proximity overrides with native distance/height bounds,
  separate ordinary brazier effects, bounded spatial lookup and save/load.
- [x] Config-only GUI: one Legacy Balance Changes file picker with standard UCP
  required/suggested/unspecified handling, all nine locale catalogs and previews.
- [x] Inert vanilla configuration, full setting reference, editor schema and a
  runnable custom-sprite/decorations example without distributed game artwork.

## Delivery

- [x] Final full regression/archive checks and private Reconquista 1.8 tester bundle.
- [x] Prepare source and store PR update for 1.8.0 (base 3.0.7), including TL;DR
  and testing instructions. Release acceptance remains open below.

## Release acceptance still requiring live play

- [ ] Rendered animation, sprites and build-menu interaction on both EXEs.
- [ ] Intended Legacy/Rebalancer combinations and long crowded sessions.
- [ ] Paired multiplayer, recorder/replay and save/load during active firing.

See VALIDATION.md for exact automated boundaries and manual testing steps. The
isolated developer-game security prompt needs manual user handling before live
checks; the shared desktop is not reserved while waiting. No signed release or
merge is implied by implementation completion.

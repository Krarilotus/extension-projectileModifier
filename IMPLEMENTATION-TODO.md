# Implementation and acceptance checklist

The checkmarks below record bounded implementation milestones, not completion of
the requested release. Earlier live results apply to their recorded prototype
versions. The native integration audit identified unfinished ownership work and
the new cooldown retarget correction still needs a successful live changed-order
test. No new completed release is implied by the older tester delivery entries.

- [x] Native reload timing for all 12 ranged types: five siege engines, five foot
  shooters, horse archers and hunters. Preserve release frames/minimum cycles,
  movement, stance/crew/target gating, volleys and saved continuation.
- [x] Reviewer trebuchet correction: hold the loaded reload pose before the
  swing, retaining shot spacing and complete native swing frame durations.
- [x] Catapult cooldown correction: hold the lowered reload pose before the
  full swing; native comparison on both EXEs and live Crusader wall volleys.
- [x] AI-only cluster threshold; human native attack orders retain their target,
  range checks and native cleanup when the selected target disappears.
- [x] Preserve accepted native human dispatch after the last stone debit,
  including wall/ground/building orders and staggered saved continuation.
- [x] Restore the original siege aiming state before reload; compare all five
  engines' turning steps with both original executables across directions/cameras.
- [x] Configurable projectile behavior for all 77 unit types; independent regular
  and cow ammunition; stance-only rates and fallback intervals.
- [x] Native accuracy units: 0 exact, 1 = 1/8 tile, 8 = one tile; sparse wall overrides.
- [ ] Named custom projectiles inheriting native damage/flight behavior, with
  independent complete GM1 sprites, format/capacity checks and saved identities.
- [ ] Build-menu decoration selection using the standard UCP modal and native
  brazier cursor, deterministic lockstep payload, cost/ownership checks and removal.
- [ ] Ordered decoration proximity overrides with native distance/height bounds,
  separate ordinary brazier effects, bounded spatial lookup and save/load.
- [x] Config-only GUI: one Legacy Balance Changes file picker with standard UCP
  required/suggested/unspecified handling, all nine locale catalogs and previews.
- [x] Inert vanilla configuration, full setting reference, editor schema and a
  runnable custom-sprite/decorations example without distributed game artwork.

## Earlier provisional 1.8.6 delivery

- [x] Final regression/archive checks and revised downloadable Reconquista 1.8.6 tester bundle.
- [x] Prepare source and store PR update for 1.8.6 (base 3.0.7), including TL;DR
  and testing instructions. Release acceptance remains open below.

## Release acceptance still requiring live play

- [ ] Finish inherited-sheet reservation in gmResourceModifier and remove private
  GM1 validation/loading/identity work from this consumer. The nested native loader
  hook and sheet-copying code are removed in this branch; the owner API remains a
  prerequisite under development.
- [ ] Replace full entity/world scans and competing render/decorations lifecycle
  work with the responsible native/framework owners.
- [ ] Add opt-in threat priorities through native target eligibility/spatial
  ownership; confirm monk/priest selection in a real mixed-unit scenario.
- [ ] Verify the new default-ON `turn_before_shot` correction for changed human
  orders during cooldown, including an explicit OFF baseline.
- [ ] Finish required save/recorder enrollment and owner-supplied content identity.
- [ ] Localize runtime diagnostics through the proper locale/error owner and
  verify actual GUI behavior in representative long/RTL locales.

- [x] Crusader startup, custom-resource initialization and decoration selector rendering.
- [x] Live Crusader: custom and ordinary wall placement, custom removal and saved identity restoration.
- [ ] Rendered animation, sprites and build-menu interaction on both EXEs.
- [x] Live 1.8.5 catapult/trebuchet rotation and ground retargeting with Reconquista.
- [ ] Live 1.8.5 remaining siege types and Extreme rotation/retargeting.
- [ ] Live reviewer confirmation of the 1.8.2 trebuchet loaded wait and firing swing.
- [ ] Live human manual orders versus AI cluster thresholds with 1.8.4 and the Reconquista preset.
- [ ] Intended Legacy/Rebalancer combinations and long crowded sessions.
- [ ] Paired multiplayer, recorder/replay and save/load during active firing.

See VALIDATION.md for exact automated boundaries and manual testing steps. UCP's
developer warning has been accepted with explicit user authorization. No signed
release or merge is implied by this test candidate.
# Latest reported movement/aiming gap

See [MOVING-CATAPULT-STATUS.md](MOVING-CATAPULT-STATUS.md): direct enemy clicks
omit native path cleanup; a separate local module correction preserves accepted
aim after Halt. Both are local candidates, with corrected in-game/composition
acceptance still outstanding. No updated public ZIP is claimed.

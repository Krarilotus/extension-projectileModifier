# Moving catapult and wrong-facing release: local work, not a shipped fix

13 September 2026. Direct enemy clicking is confirmed by the user.

The missing movement cleanup is in the original tribe command dispatcher. A
focused correction is isolated in `../ucp3-fixes-siege-target-stop`, branch
`fix/siege-target-stop`, preserving the existing fixes worker's branch. See its
`SIEGE-TARGET-STOP-STATUS.md` for native owner, AOB/ABI evidence and acceptance
gaps. No duplicate command hook was added to this projectile module.

A second defect is in this module: automatic target selection at the loaded
release transition can replace a previously accepted aim without running the
native turn state again. The local correction retains the native accepted aim
through that volley and lets the next selection pass through native aiming.
The existing `turn_before_shot: false` control retains the old behavior.
`cadence.context_code` shares this decision between the existing animation gate,
release and stagger continuation, using existing MANUALORDER/profile tables
and native target coordinates. It introduces no target cache, hook or timer.

## Evidence

- Native Halt probe: catapult loaded facing west, accepted target (288,320),
  nearby automatic enemy east at (352,320), interval 700. With correction OFF,
  tick 27 fired east while facing west (6). With correction ON, tick 27 fired
  west while facing west, then tick 727 fired east while facing east (2).
- All three manual-release regressions passed, including last-stone unit,
  ground, wall and building orders and saved stagger continuation.
- Earlier range/autonomy/native-config revision passed 130 tests and 23
  GUI/archive checks. Those runs PRECEDE this final accepted-aim change and
  must not be presented as validation of the final diff.
- Actual game control: the native/no-op configuration loaded; a catapult moved,
  accepted a wall order, aimed and discharged its remaining ammunition. This
  did not exercise the corrected direct-enemy-click path.

## Explicit gap / next PR status

**Implementation is local and unshipped.** The final accepted-aim change still
needs full regression coverage, especially automatic target disappearance,
range/crew eligibility, random/stagger behavior and save/replay. Corrected
movement plus facing needs an actual enemy-click gameplay test and multiplayer
acceptance. Do not distribute the stale local 1.8.6 archive as this correction.
No public ZIP or PR has been updated for these changes in this session.

The larger architecture gaps remain open: GM content validation/identity owner,
render/decorations world scans, threat priorities, synchronized persistence
integration, runtime error localization and complete supported-variant/GUI
acceptance. This focused report does not waive them or claim the whole module
complete. The desktop is released and the isolated test files restored.

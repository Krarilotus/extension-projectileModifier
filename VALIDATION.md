# Validation — unreleased work

## Foot-shooter reload integration, 1.7.0

Final native/configuration run: **66 Python/Lua/x86 tests passed**. The complete
GUI/archive suite also passes **23 checks** (13 component/qualifier and 10
archive/locale tests). The private Reconquista preset passes both production
Lua validation and the editor schema and is packaged separately.

Five integrated tests execute the native European archer, crossbowman, Arabian
archer, slinger and firethrower updates along with real animation advancement.
Both executables cover release-frame intervals, comparison against the native
minimum cycle, building targets, fortification/stance holds and save/load while
loaded. Further cases cover stale-target replacement and native pending archer
retries. Sound/device calls and projectile-spawn observation are substituted;
rendered gameplay, multiplayer and replay acceptance remain outstanding.

The slinger's initial script pose is at index 0 but its first executable release
is index 1. Crossbows compare cycle 2 across their three elevation scripts. The
other infantry scripts are resolved from each executable. Only configured native
types need their release signatures; an unrelated modified archer signature no
longer prevents a catapult-only configuration from loading.

A regression reproduced a native stance hold freezing the cooldown as well as
release. Native clocks now continue through crew/stance holds; an eligible loaded
unit can release immediately once both the interval and hold have ended. The
native crew-hold test verifies releases at ticks 99 and 420 after a crew return
at 420, rather than applying an additional remainder of the interval.

Save format 4 rejects the older scheduler semantics. The saved unit animation
and module timers reproduce loaded building-target volleys, including staggered
shots. Test observation now hooks only requested native boundaries instead of
calling Python for every instruction; native code and instruction limits remain
in use. The complete module assembles to 6,229 bytes across 31 routines under the
63,488-byte FASM budget. Data uses 143,504 / 503,504 bytes (Crusader / Extreme).

For live acceptance, add all five foot shooters to the siege checks below.
Compare interval 400 and 1 against units/buildings, replace a target while loaded,
move onto/off fortifications, and save/load during holds and staggered fire.
Earlier target loss during wind-up can restart the native cycle; the loaded
release check does not promise that every interrupted attack retains its timing.

Mounted/hunter timing, custom GM1 variants and build-menu decoration triggers
remain unfinished. The agreed custom variant scope is native damage/flight
behavior with independent sprites. See IMPLEMENTATION-TODO.md for the remaining
integration boundaries.

## Historical siege reload integration, 1.6.0

Final run: all **59 Python/Lua/x86 tests** passed, along with the complete
**23 GUI/archive checks** (13 component/qualifier and 10 archive/locale tests).
The private Reconquista conversion also passes the schema and production Lua
validator; it is distributed separately from the public module.

The cadence tests execute original animation advancement and catapult,
trebuchet, mangonel, tower-ballista and fire-ballista update functions in both
1.41 executables. They check actual release frames, shot-to-shot intervals and
stone stock. Requested intervals below the native cycle are compared with the
unconfigured native cycle; no animation frames are skipped.

Additional cases cover crew defaults and explicit overrides, moving/standing
holds, target loss, bounded preload polling, long staggered volleys, separate AI
cow ammunition, omitted mangonel count, conditional hook installation and saved
continuation. Save tests restore both the game-owned unit animation and the
module's saved timers; old format-2 state is rejected before changing timers.
Regression tests reproduced both bypassed default crew gates and the extra
reload delay after a long staggered volley before their fixes.

With the native reload hook enabled, 31 routines assemble under the 63,488-byte
FASM test budget and total 6,104 executable bytes. Runtime data occupies
142,864 bytes in Crusader and 502,864 in Extreme. These are allocation/code-size
measurements, not a frame-rate benchmark. The new animation patch sites are
0x579E62 and 0x57A282 respectively, resolved and checked before patching.

Sound/device calls and projectile-spawn observation are substituted in these
reload tests. They do not establish rendered animation, crew rendering, complete
game-loop behavior, multiplayer synchronization or replay acceptance. The tests
use full native engine updates, but supply a small simulated world and explicit
simulation ticks rather than launching the game.

For live acceptance, compare interval 400 and interval 1 with the native engine
cycle, on both EXEs. Remove/restore crew and targets while loaded; stone stock
must not decrease during a hold. Test long staggered volleys, ordinary cow
orders and AI cows, moving commands, and save/load while waiting and while a
volley is pending. Repeat with the intended Legacy/Rebalancer configuration and
paired multiplayer/replays using identical module and preset files.

Infantry/mounted/hunter native timing, custom GM1 projectiles and build-menu
decorations remain unfinished. See IMPLEMENTATION-TODO.md. This is an unsigned
candidate and not a live acceptance report.

## Accuracy correction, 10 September 2026

Follow-up native-unit check: `inaccuracy: 1` produces only the five integer points
within an eighth-tile radius (center and four axial neighbors), verified in both
executables. Examples now use whole native units, with 8 equal to one tile.

All 48 Python/Lua/x86 tests passed, including accuracy granularity and
fortification/AI scope on both EXEs. All 13 launcher component/qualifier tests
and 10 ZIP localization tests passed. The ZIP test builds an unsigned
`custom-projectiles-1.5.0.zip` from the working tree.

Accuracy tests execute the original ground-target preparation and subsequent
height-dependent error stage in Crusader and Extreme 1.41. Explicit zero preserves
the exact input aim point across repeated preparation calls and consumes no
module scatter RNG. Omitted accuracy and unchanged cow ammunition retain native
scatter. Positive tile and micro-unit settings produce identical shot coordinates
for equivalent values; tested radii are 1, 2 and 100 tiles, with every sample
inside the stated circular radius. The extra regression verifies transitions onto
and off fortifications and the AI-only gate.

The projectile matrix also executes actual native allocation, velocity setup and
first update for 77 unit types × 16 projectiles × both executables. These checks
do not render the game or establish full-flight collision/damage behavior.

For live accuracy acceptance: issue repeated shots at a stationary ground point
with accuracy 0 and spread 0; compare with omitted accuracy; then compare tile
radius 1 with micro radius 8. Repeat on raised terrain and with siege cow orders.
Moving targets may move away after release. Nonzero spread remains independent.

Source is proposed through extension-store PR #31 targeting 3.0.7. Reload timing,
custom graphics and build-menu decoration work is unfinished; this is not a
signed release or a live acceptance report.

## Historical 1.4.0 validation (figures below describe that version)

Work date: 10 September 2026. The original attachments and reference checkouts
remain unchanged. The source and store PR are separate from a signed release.

## Current validation scope

The suite contains 34 Python/Lua/x86 tests, 13 launcher component/qualifier tests
and 10 archive localization tests. Native tests use production Lua/FASM and mapped
licensed PE sections. They execute original dispatcher/acquisition code with an
observed projectile-spawner stand-in; they do not prove rendered effects/damage.

The file-only update tests the real file-loading path with parsed YAML, the inert
77-unit vanilla template, omitted fields, invalid files and rejection of old
hidden GUI overrides before native changes. Native scheduling and save-state
tests remain in the suite; assembly templates and save format are unchanged.

Actual launcher FileInput, QualifierControl and ResetSettingButton components
are exercised, including all nine languages, plugin-path generalization,
required/suggested toggles, required locks, reset/omission and config-full output.
Shipped UCP examples are checked using the real extension merge logic, including
conflicting required paths. Application state and host services are substitutes.

Archive tests use real RustZipExtensionHandle, ZipReader, readLocales, readUISpec
and applyLocale TypeScript functions with an exact-entry native ZIP bridge
substitute. They recreate the absent locale/ entry failure and verify the repaired
archive against Legacy 2.15.1 in every language. Catalog checks read the archive,
not just loose source files. No full native launcher session is claimed.

The module contains one configuration option, three localization keys per
language, nine short localized previews, all 30 supported settings in the vanilla
template/reference, and standard required/suggested/unspecified UCP examples.

All 20 routines assemble under **FASM 1.73.35 with 63488 bytes**, slightly below
the framework's 64000-byte budget. They total **4595 executable bytes**. Module
data occupies **100704 bytes** in Crusader and **370704 bytes** in Extreme; custom
saved blocks total 80004 and 320004 bytes respectively before ZIP compression.
These are memory/code-size measurements, not frame-rate benchmarks. Target scans
remain bounded full-array scans and cluster evaluation is bounded by 256 candidates.

## Reference identity

| Fixture | SHA-256 |
|---|---|
| Supplied projectileModifier 1.2.0 ZIP | `4b4f2e0ae983ff4b2e66956ef7a7d4d36cc6f0b9d2481c5e46e5f4ce49a032a2` |
| Stronghold Crusader.exe | `3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a` |
| Stronghold_Crusader_Extreme.exe | `55648e6b05d67d37a5773fe699bbb17a2d6ad4de1bb9dbded9a21caef82bd7fb` |

Crusader hook sites: fire `0x532700`, acquire `0x54B0D0`, unit update `0x579398`.
Extreme: fire `0x532B20`, acquire `0x54B4F0`, unit update `0x5797B8`.
The native update-loop compares against 2500 at `0x57973A` and against 10000 at
`0x579B5A`. Those operands and unit-array bases are checked before installation.
The native mangonel loop is at `0x56ADF0`–`0x56AE3C` in Crusader and initializes
seven dispatches. Only the two entry sites are patched; acquisition is called.

Read-only reference revisions:

- Rebalancer: `8d5b47e1d61cab8c0f4b1f301669d2541788facd`.
- UCP2 Legacy: `caa50aba9fc85c5fc766c413b23085ddfbba4a79`.
- GUI component checkout: `b9924f3c78152890877bee8326f31907d17f3e09`.
- Framework checkout: `02a7a6bc8ab956a91fc752e8c8ed215c149855e7`.
- map-extensions API and lifecycle callbacks inspected at upstream revision
  `d9399125831c96a46701a510542e09f2a031971f` in `gynt/ucp-extension-map-extensions`.

No OpenSHC reconstruction was changed. OpenSHC headers informed layout checks;
the cited original assembly supplied capacity, dispatch and hook evidence.
Roadmap R077 (terrain aiming) and R112 (cow impact/carcass behavior) were consulted
as adjacent scopes, not folded into this module or claimed fixed.

## Remaining live acceptance

Before a public release, run both executables with this module in a supported
UCP installation and record the exact module list and settings:

1. Import the archive in the native GUI, verify all nine languages and the single
   file selection at normal/small window sizes, including Persian mixed-direction
   text and wrapping; export settings and launch.
2. Exercise each projectile type against troops, structures and terrain; inspect
   actual trajectories, collision, damage, fire, cow effects and sounds.
3. Exercise siege-tower movement, crew arrival/loss, attachment/detachment,
   nearby enemies above/below it and boarding. The candidate-based boarding
   option is a proximity approximation; it does not promise native climb detection.
4. Check assassins at different visibility levels, troops on walls, trapped units,
   map edges and small maps. No claim is made that the custom target scan fully
   reproduces every native visibility/line-of-sight predicate.
5. Save/load through the real map-extensions DLL, load older saves, start a second
   match, and stress death/recruitment/reuse and projectile-pool exhaustion.
6. Test Rebalancer/Legacy combinations in game. Signature and table ownership
   review is not a universal module-compatibility result.
7. Compare paired multiplayer sessions with identical settings and saved
   continuation. Recorder integration and offline replay need their owner's
   acceptance; the read-only state export alone does not establish support.

The archive is ready for this testing, not represented as a signed or fully
validated public release.

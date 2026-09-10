# Validation — local 1.3.2 candidate

Work date: 10 September 2026. No active game installation or reference checkout
was modified. The supplied ZIP remains unchanged. This directory contains the
implementation, tests and build tools; `dist/` contains the unsigned module ZIP.

## Evidence and scope

The automated suites contain **32 Python/Lua/x86 tests**, **18 launcher component
tests** and **10 archive localization integration tests**. Production Lua builds production FASM routines, which run in Unicorn
against mapped sections of the licensed executable. Native unit firing and
building-target acquisition execute their original machine code. The entity
spawner is an observed stand-in: these tests verify call arguments, counts, timing,
stack/register boundaries and state changes, not rendered projectile trajectories
or final damage. No complete Windows game session was exercised.

Coverage includes:

- catapult → mangonel remapping, explicit count and preserved native shots;
- exact automatic siege-tower counts and intervals on both executable variants;
- the native seven-shot mangonel replaced by the configured volley count;
- current crew versus dispatched engineers/stale references;
- allied, neutral, dead and transitioning target exclusion;
- array boundaries at 2500 (Crusader) and 10000 (Extreme);
- slot reuse, stationary/moving transitions, AI-only behavior and cow selection;
- animation waits and staggered volleys without dropped projectiles;
- random/cluster candidates without scratch overlap;
- native building-target acquisition and restoration of unit targeting fields;
- attached-tower type/UID validation;
- saved continuation reproducing staggered/scattered shots, fresh-world reset,
  and rejection of malformed saved blocks before writes;
- inert defaults, invalid-input rejection, safe assembler failure, repeat-enable
  rejection, YAML examples and complete GUI localization;
- actual UCP Choice/UCP2Slider selection, checkbox and numeric-value interaction
  in all nine GUI languages; actual nested GroupBox collapse and category merging
  with Legacy. Host services/application state are mocked. This is a
  component test, not a full launcher import/publish test.

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

## 1.3.1 GUI audit and checks

All 32 Python/Lua/x86 tests and 18 actual launcher component tests passed after
this update. The native/runtime Lua files are byte-for-byte identical to the
previous 1.3.0 artifact. The additional checks cover compact layout, all nine
complete catalogs, preset schema validation and advanced preset/old GUI override
compatibility. The component suite checks dropdown editing, numeric overrides,
sword checkbox styling hooks, initially collapsed help, recursive accordion
expansion and merging with Legacy's existing localized categories in every
language. When catalogs are supplied directly to the component tests, every referenced
localization token resolves without English catalog fallback; the shared Balance Changes category deliberately matches Legacy.

There are 121 strings per language and nine localized module descriptions.
The editor uses one top-level category entry, five unit families and 467 unit
controls plus one optional file picker. The complete settings reference remains
a Markdown table. See GUI-AUDIT.md for the Rebalancer ownership decision and
advanced configuration migration notes. Native-window visual validation and
native-speaker review of translations have not been performed.

## 1.3.2 archive regression

The 1.3.1 source/component checks passed but missed that its ZIP lacked an explicit
`locale/` entry. The user's screenshot showed the consequence: UCP skipped all
catalogs and rendered raw placeholders. This was a packaging bug, not missing
translation text. The corrected packager emits and validates directory entries.

The archive suite exercises the actual RustZipExtensionHandle, ZipReader,
readLocales, readUISpec and applyLocale TypeScript code. Only the native ZIP IPC
bridge is replaced, using actual ZIP entries with the exact-name lookup semantics
of `src-tauri/src/zip_support.rs`. One test recreates the old missing-directory
archive and confirms that discovery returns no locales. Nine tests read the
repaired archive and verify complete catalogs, resolved placeholders, localized
descriptions and shared categories against the packaged Legacy 2.15.1 reference.
This is archive integration testing, not a complete Tauri installation session.

The native/runtime Lua files and option definitions are unchanged from 1.3.1;
its 32 passing native/configuration tests remain the runtime baseline. The GUI
component and archive suites are rerun for this packaging fix. No new live-game
acceptance result is claimed.

## Remaining live acceptance

Before a public release, run both executables with this module in a supported
UCP installation and record the exact module list and settings:

1. Import the archive in the native GUI, verify all nine languages and category
   navigation at normal/small window sizes, including Persian mixed-direction
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

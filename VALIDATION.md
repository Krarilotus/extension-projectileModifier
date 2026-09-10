# Validation — local 1.4.0 candidate

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

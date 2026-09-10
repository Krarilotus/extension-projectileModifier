# File-only customization audit — 1.8.0

The user requested removing the unit editor after trying the earlier layout.
The module now exposes one standard FileInput, following Rebalancer's option
shape and Legacy's exact Balance Changes category. No custom view or bulk unit
controls remain. The input label, tooltip and module preview are localized in
all nine launcher languages. The native launcher's Browse button and qualifier
icons remain owned by the launcher.

The selected YAML file owns every projectile value. Its `units` mapping remains
sparse: missing units/fields and empty unit mappings are valid. The vanilla
template is inert and includes all 77 unit names plus comments for every supported setting.
The complete setting/value table and UCP qualifier examples are in README.md.

UCP qualifiers belong on the file selector in config-sparse, as in Rebalancer
balance plugins. Required selection, suggested selection, omitted selection,
explicit empty selection and resolved config-full values are distinct. The
module receives a resolved string; it does not invent a second priority engine
inside the projectile file. A locked path does not make external bytes immutable.

Old GUI overrides are rejected with a migration message before native scanning.
They cannot silently override the file. The direct namespace.apply API remains
available for module callers and native tests, but inline units are not UCP options.

Native UI tests exercise file selection, version-independent plugin paths,
required/suggested toggling, reset to an omitted sparse value, locked browsing,
and conflicting required presets using the launcher's real merge/serialization
code. Archive tests still reproduce the 1.3.1 missing-directory bug and verify
all nine catalogs through UCP's ZIP discovery against packaged Legacy.

The packaging fix remains mandatory: include `locale/` as an explicit ZIP entry.
UCP's readLocales checks that exact entry before loading files; the backend uses
ZipArchive.by_name. Files merely sharing the prefix do not satisfy that lookup.

Rebalancer still owns its balance tables. This module owns its native firing
hooks, scheduler and saved state; there is no Rebalancer registration API for
those features. The 1.8.0 candidate adds native reload, custom sprites and decoration triggers
with save format 5. Decoration choices belong to the in-game build menu; they
do not add customization-tab controls. The modal uses the standard ui module
API, callback-group header, eight rows per page and bounded pagination.
Live-game, multiplayer and native-window acceptance remain outstanding.

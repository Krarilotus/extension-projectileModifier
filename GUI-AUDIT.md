# Customization audit — 1.3.1

Reviewed before implementation on 10 September 2026 against the local UCP2
Legacy, Rebalancer and launcher sources. Reference revisions are in VALIDATION.md.

| Finding | Decision and implemented result |
|---|---|
| The previous menu repeated approximately 30 controls for each of 77 unit types. | One collapsed Projectiles entry under Legacy's Balance Changes category, containing a collapsed preset section and five collapsed unit families. Each unit has six common controls; five crew-operated siege types also show the engineer count. |
| Long help repeated in every unit panel. | Shared instructions appear only inside the outer accordion. Numeric help stays inside the launcher's collapsed UCP2Slider body. Choice help uses the native tooltip. |
| Numeric overrides need to distinguish “use the file” from an explicit zero. | Retain native UCP2Slider sword checkboxes and their enabled/value representation. Projectile and target enums use native Choice dropdowns with an unchanged option. |
| Specialist booleans have three states when layered over a file. | Advanced behavior stays in the optional YAML preset. No misleading two-state checkbox that silently overwrites the file. Existing 1.3.0 advanced GUI configuration values are still accepted by the unchanged runtime, although they no longer have individual visible controls. |
| The GUI supports de, en, fr, ru, hu, tr, ch, es and fa. | All nine catalogs contain the same 121 nonempty keys, including all unit names, options, tooltips and dropdown values; each has a localized module description. Chinese uses ch and Persian uses fa, as required by the launcher. |
| Category identity depends on the translated string, not an internal ID. | Match Legacy's loaded balance_changes value exactly. This checkout falls back to “Balance Changes” in all nine languages. Its fr.yaml and Chinese.yml are not locale/fr.yml and locale/ch.yml, so the launcher's loader ignores those files. Translating our category independently would split it. |
| Launcher views include GroupBox, UCP2Slider, Choice and FileInput; there is no built-in Table view. | Use these stock controls for editable settings. Keep the complete setting/value reference as a real Markdown table in README.md. No synthetic table made from layout columns and no custom HTML/CSS menu. |
| Rebalancer's apply_rebalance edits fixed balance tables; its projectiles section changes physics. It has no registration API for this scheduler, dispatcher hook or save state. | Keep native behavior in projectileModifier. Use the same optional file-based configuration approach for advanced balance presets, with a local editor schema. A balance preset can configure this module alongside Rebalancer; moving native code into Rebalancer would require changes to that independently maintained module. |

The advanced preset keeps the original `units: {Unit name: settings}` format.
The schema supplies field completion, bounds, known names, alias exclusions and
required companion fields without inserting defaults. The Lua validator remains
authoritative, including the comparison between minimum and maximum volley delay.
Enabled GUI values override a file; unchecked controls preserve it.

Native hooks, scheduler, save format and configuration parsing are unchanged in
1.3.1. Old advanced GUI values remain runtime-compatible. To edit those specialist
values in 1.3.1, transfer their enabled values to a YAML preset and clear the old
GUI overrides using the launcher's configuration reset controls; otherwise those
old overrides still take precedence. New configurations have no hidden overrides.

Automated component tests check localization, collapsed controls, dropdowns and
sword checkbox behavior. Native-window visual checks, including Persian mixed
direction text and small-window wrapping, remain part of live acceptance.

## 1.3.2 correction: archive discovery

The user's installed 1.3.1 screenshot exposed a gap in the initial audit: source
catalog completeness does not establish that UCP can discover those catalogs in
an archive. Our ZIP contained locale files without a `locale/` directory entry.
`readLocales` first calls `doesEntryExist('locale/')`; the Rust ZIP backend uses
an exact `ZipArchive.by_name` lookup. That returned false and skipped every
language. The installed Legacy 2.15.1 reference archive includes that entry.

The 1.3.2 packager now emits explicit parent-directory entries, with directory
attributes, and checks them after building. Archive integration tests preserve
exact-entry existence semantics, reproduce the old failure and load all nine
catalogs through the real launcher discovery functions. They also compare
category merging with Legacy 2.15.1 loaded from its ZIP. The native bridge is
substituted with a Python ZIP reader; no full native GUI session is claimed.

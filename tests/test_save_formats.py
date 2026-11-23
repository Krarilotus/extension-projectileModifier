"""Versioned saved-state formats: every accepted difference is a defined migration.

Format 6 records the unit capacity. Format 5 (1.8.x up to 1.8.19) is read with
the capacity derived from its per-unit blocks. Test-build formats 1-4 start the
module's timers fresh. Damaged data and unknown formats are refused, and
`allow_config_changes_on_load: false` keeps the earlier exact-match rules.
"""
import unittest
from harness import Harness
import test_decorations as decoration_tests
import test_feedback_fixes as feedback
import test_sprite_resources as sprite_tests

CONFIG = {'units': {'Catapult': {'interval': 700}}}
STRICT = {'allow_config_changes_on_load': False, 'units': {'Catapult': {'interval': 700}}}


class SaveFormatTests(unittest.TestCase):
    def setUp(self):
        self.helper = feedback.FeedbackFixTests()

    def game(self, extreme=False, config=CONFIG):
        return self.helper.prepare(config, extreme)

    def transfer(self, old, new):
        return self.helper.transfer(old, new)

    def as_format_five(self, handle):
        handle.files[b'format'] = b'5'
        handle.files[b'capacity'] = None

    def test_format_five_saves_load_unchanged_and_resave_as_six(self):
        for extreme in (False, True):
            old, new = self.game(extreme), self.game(extreme)
            old.put(old.v['COOLDOWNT'] + 8, 432)
            old.put(old.v['PENDINGT'] + 12, 5)
            state, handle = self.transfer(old, new)
            self.as_format_five(handle)
            pending = state.validate(state, handle)
            self.assertFalse(pending[b'reconfigure'])
            self.assertFalse(pending[b'reset_visuals'])
            state.deserialize(state, handle)
            self.assertEqual(new.get(new.v['COOLDOWNT'] + 8), 432)
            self.assertEqual(new.get(new.v['PENDINGT'] + 12), 5)
            resaved = feedback.native_tests.NativeTests().state_handle(new)
            state.serialize(state, resaved)
            self.assertEqual(resaved.files[b'format'], b'6')

    def test_format_five_per_unit_blocks_must_agree_on_one_capacity(self):
        old, new = self.game(), self.game()
        state, handle = self.transfer(old, new)
        self.as_format_five(handle)
        handle.files[b'lastpos.bin'] = handle.files[b'lastpos.bin'] + bytes(4)
        with self.assertRaisesRegex(Exception, 'invalid saved state: lastpos.bin'):
            state.validate(state, handle)
        handle.files[b'lastpos.bin'] = handle.files[b'lastpos.bin'][:4]
        with self.assertRaisesRegex(Exception, 'invalid saved'):
            state.validate(state, handle)

    def test_format_six_capacity_must_match_its_blocks(self):
        old, new = self.game(), self.game()
        state, handle = self.transfer(old, new)
        handle.files[b'capacity'] = b'10000'
        with self.assertRaisesRegex(Exception, 'invalid saved state'):
            state.validate(state, handle)
        for value in (None, b'0', b'2500.5', b'-1'):
            handle.files[b'capacity'] = value
            with self.assertRaisesRegex(Exception, 'invalid saved unit capacity'):
                state.validate(state, handle)

    def test_test_build_formats_start_fresh_unless_strict(self):
        old, new = self.game(), self.game()
        old.put(old.v['COOLDOWNT'] + 4, 99)
        state, handle = self.transfer(old, new)
        new.put(new.v['COOLDOWNT'] + 4, 77)
        for legacy in (b'1', b'2', b'3', b'4'):
            handle.files[b'format'] = legacy
            self.assertTrue(state.validate(state, handle)[b'fresh'])
        state.deserialize(state, handle)
        self.assertEqual(new.get(new.v['COOLDOWNT'] + 4), 0)
        self.assertEqual(new.get(new.v['SEED']), 0x1d872b41)
        strict = self.game(config=STRICT)
        strict_state, strict_handle = self.transfer(old, strict)
        strict_handle.files[b'format'] = b'4'
        with self.assertRaisesRegex(Exception, 'unsupported saved state format'):
            strict_state.validate(strict_state, strict_handle)
        for unknown in (b'0', b'7', b'5.0', b''):
            handle.files[b'format'] = unknown
            with self.assertRaisesRegex(Exception, 'unsupported saved state format'):
                state.validate(state, handle)

    def test_crusader_state_widens_into_extreme_unit_slots(self):
        for five in (False, True):
            crusader, extreme = self.game(False), self.game(True)
            crusader.put(crusader.v['COOLDOWNT'] + 4 * 2499, 321)
            crusader.put(crusader.v['UIDT'] + 4 * 7, 4242)
            extreme.put(extreme.v['COOLDOWNT'] + 4 * 2500, 55)
            state, handle = self.transfer(crusader, extreme)
            if five: self.as_format_five(handle)
            pending = state.validate(state, handle)
            self.assertTrue(any(b'unit slots' in note for note in pending[b'notes'].values()))
            state.deserialize(state, handle)
            self.assertEqual(extreme.get(extreme.v['COOLDOWNT'] + 4 * 2499), 321)
            self.assertEqual(extreme.get(extreme.v['UIDT'] + 4 * 7), 4242)
            self.assertEqual(extreme.get(extreme.v['COOLDOWNT'] + 4 * 2500), 0)

    def test_extreme_state_narrows_only_when_dropped_slots_are_empty(self):
        extreme, crusader = self.game(True), self.game(False)
        extreme.put(extreme.v['COOLDOWNT'] + 4 * 2499, 222)
        state, handle = self.transfer(extreme, crusader)
        state.deserialize(state, handle)
        self.assertEqual(crusader.get(crusader.v['COOLDOWNT'] + 4 * 2499), 222)
        extreme.put(extreme.v['PENDINGT'] + 4 * 2500, 3)
        state, handle = self.transfer(extreme, crusader)
        crusader.put(crusader.v['COOLDOWNT'] + 4 * 2499, 1)
        with self.assertRaisesRegex(Exception, 'beyond this game.s unit limit: pending.bin'):
            state.deserialize(state, handle)
        self.assertEqual(crusader.get(crusader.v['COOLDOWNT'] + 4 * 2499), 1)

    def test_strict_mode_refuses_a_different_unit_capacity(self):
        crusader, strict = self.game(False), self.game(True, STRICT)
        state, handle = self.transfer(crusader, strict)
        with self.assertRaisesRegex(Exception, 'different unit limit'):
            state.validate(state, handle)


class GraphicsMigrationTests(unittest.TestCase):
    """Changed graphics must leave the game's own entity records consistent."""

    def sprites(self):
        tests = sprite_tests.SpriteResourcesTests()
        tests.addCleanup = self.addCleanup
        return tests.prepare(False)

    def record(self, state, entity):
        return state + 20 + entity * 232

    def live_arrow(self, h, record, uid, gm=207):
        for offset, value, size in ((0x30, uid, 4), (0x28, 2, 2), (0x2A, 1, 2), (0x06, gm, 2)):
            h.put(record + offset, value, size)

    def transfer(self, old, new):
        return feedback.FeedbackFixTests().transfer(old, new)

    def test_projectiles_in_flight_get_their_native_graphics_back(self):
        for change in ('definition', 'layout'):
            with self.subTest(change=change):
                h, entities, _ = self.sprites()
                self.assertEqual(h.get(h.v['VARIANTGM'] + 4), 207)
                for entity, uid in ((25, 777), (26, 778)):
                    h.put(h.v['ENTITYVARIANT'] + entity * 4, 1)
                    h.put(h.v['ENTITYUID'] + entity * 4, uid)
                    h.put(h.v['ENTITYTYPE'] + entity * 4, 1)  # arrow
                    self.live_arrow(h, self.record(entities, entity), uid)
                state = h.sections[b'projectileModifier']
                handle = feedback.native_tests.NativeTests().state_handle(h)
                state.serialize(state, handle)
                # Entity 26 was recycled after the save: not the saved projectile.
                h.put(self.record(entities, 26) + 0x30, 999)
                if change == 'definition':
                    handle.files[b'config'] = b'{edited}'
                    handle.files[b'assets'] = b'{edited}'
                else:
                    h.put(h.v['VARIANTGM'] + 4, 208)
                state.deserialize(state, handle)
                self.assertEqual(h.get(h.v['ENTITYVARIANT'] + 25 * 4), 0)
                self.assertEqual(h.get(self.record(entities, 25) + 0x06, 2), 34)  # native arrow sheet
                self.assertEqual(h.get(self.record(entities, 26) + 0x06, 2), 207)

    def decorations(self, names, extreme=False):
        return decoration_tests.DecorationTests().prepare_module(
            {'decorations': {name: {} for name in names}}, extreme)

    def brazier(self, h, entity, uid):
        """The game's own record of a live brazier (restored by the native load)."""
        record = h.native_decor[b'entityState'] + 20 + entity * 232
        for offset, value, size in ((0x30, uid, 4), (0x28, 2, 2), (0x2A, 14, 2), (0x44, 40, 2), (0x46, 40, 2)):
            h.put(record + offset, value, size)

    def place(self, h, entity, decoration, uid):
        h.put(h.v['DECORVARIANT'] + entity * 4, decoration)
        h.put(h.v['DECORUID'] + entity * 4, uid)
        self.brazier(h, entity, uid)

    def move(self, old, new, five=False):
        for entity in range(1, 3000):
            uid = old.get(old.v['DECORUID'] + entity * 4)
            if uid: self.brazier(new, entity, uid)
        saved = feedback.native_tests.NativeTests().state_handle(old)
        original = old.sections[b'projectileModifier']
        original.serialize(original, saved)
        loaded = feedback.native_tests.NativeTests().state_handle(new)
        for name, content in saved.files.items(): loaded.files[name] = content
        if five:
            for name in (b'capacity', b'decoration-names'): loaded.files[name] = None
            loaded.files[b'format'] = b'5'
        return new.sections[b'projectileModifier'], loaded

    def test_placed_decorations_keep_their_kind_by_name(self):
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                old = self.decorations(['frost', 'smoke'], extreme)
                self.place(old, 40, 1, 4001)  # frost
                self.place(old, 41, 2, 4002)  # smoke
                new = self.decorations(['alpha', 'frost'], extreme)
                state, handle = self.move(old, new)
                pending = state.validate(state, handle)
                self.assertTrue(any(b'ordinary braziers' in note for note in pending[b'notes'].values()))
                state.deserialize(state, handle)
                self.assertEqual(new.get(new.v['DECORVARIANT'] + 40 * 4), 2)  # frost is id 2 now
                self.assertEqual(new.get(new.v['DECORUID'] + 40 * 4), 4001)
                self.assertEqual(new.get(new.v['DECORVARIANT'] + 41 * 4), 0)  # smoke removed
                self.assertEqual(new.get(new.v['DECORUID'] + 41 * 4), 0)

    def test_unchanged_decorations_keep_their_ids(self):
        old = self.decorations(['frost'])
        self.place(old, 40, 1, 4001)
        new = self.decorations(['frost'])
        state, handle = self.move(old, new)
        self.assertFalse(state.validate(state, handle)[b'reset_visuals'])
        state.deserialize(state, handle)
        self.assertEqual(new.get(new.v['DECORVARIANT'] + 40 * 4), 1)

    def test_format_five_refuses_changed_definitions_of_placed_decorations(self):
        old = self.decorations(['frost'])
        self.place(old, 40, 1, 4001)
        new = self.decorations(['alpha', 'frost'])
        state, handle = self.move(old, new, five=True)
        new.put(new.v['DECORVARIANT'] + 40 * 4, 9)
        with self.assertRaisesRegex(Exception, 'placed custom decorations changed in a save from an older version'):
            state.deserialize(state, handle)
        self.assertEqual(new.get(new.v['DECORVARIANT'] + 40 * 4), 9)
        # Without placed decorations the same edit loads.
        old.put(old.v['DECORVARIANT'] + 40 * 4, 0)
        state, handle = self.move(old, new, five=True)
        state.deserialize(state, handle)

    def test_damaged_decoration_names_are_refused(self):
        old = self.decorations(['frost'])
        self.place(old, 40, 1, 4001)
        new = self.decorations(['alpha', 'frost'])
        state, handle = self.move(old, new)
        for value in (b'1=Frost;', b'1=frost', b'x=frost;'):
            handle.files[b'decoration-names'] = value
            with self.assertRaisesRegex(Exception, 'invalid saved graphics names'):
                state.validate(state, handle)

    def test_removed_decoration_with_its_own_graphics_gets_the_brazier_look(self):
        old = self.decorations(['frost', 'smoke'])
        old.put(old.v['DECORGM'] + 2 * 4, 207)  # smoke had its own sheet slot
        self.place(old, 41, 2, 4002)
        record = old.native_decor[b'entityState'] + 20 + 41 * 232
        old.put(record + 0x06, 207, 2)
        new = self.decorations(['frost'])
        state, handle = self.move(old, new)
        new_record = new.native_decor[b'entityState'] + 20 + 41 * 232
        new.put(new_record + 0x06, 207, 2)
        state.deserialize(state, handle)
        self.assertEqual(new.get(new.v['DECORVARIANT'] + 41 * 4), 0)
        self.assertEqual(new.get(new_record + 0x06, 2), 138)

    def test_undefined_saved_decoration_ids_are_refused(self):
        old = self.decorations(['frost'])
        self.place(old, 40, 1, 4001)
        new = self.decorations(['alpha', 'frost'])
        state, handle = self.move(old, new)
        handle.files[b'decoration-variant.bin'] = (bytes(40 * 4) + (5).to_bytes(4, 'little')
                                                   + bytes((3000 - 41) * 4))
        with self.assertRaisesRegex(Exception, 'invalid saved state: decoration-variant.bin'):
            state.validate(state, handle)
        same = self.decorations(['frost'])
        same_state, same_handle = self.move(old, same)
        same_handle.files[b'decoration-variant.bin'] = handle.files[b'decoration-variant.bin']
        same.put(same.v['DECORGM'] + 4, 300)  # layout-only change
        with self.assertRaisesRegex(Exception, 'invalid saved state: decoration-variant.bin'):
            same_state.validate(same_state, same_handle)

    def projectile_in_flight(self):
        h, entities, _ = self.sprites()
        h.put(h.v['ENTITYVARIANT'] + 25 * 4, 1)
        h.put(h.v['ENTITYUID'] + 25 * 4, 777)
        h.put(h.v['ENTITYTYPE'] + 25 * 4, 1)
        self.live_arrow(h, self.record(entities, 25), 777)
        self.assertEqual(h.get(h.v['VARIANTBASEGM'] + 4), 34)
        return h

    def units_only(self, before=None):
        h = Harness()
        if before: before(h)
        h.module.apply(h.config(CONFIG))
        h.v = {k: v for _, _, values in h.blobs.values() for k, v in values.items()}
        return h

    def test_a_file_without_graphics_still_restores_saved_projectile_records(self):
        old = self.projectile_in_flight()
        new = self.units_only()
        state, handle = self.transfer(old, new)
        entities = new.get(new.v['FIREPROJ'] + 0x416)
        self.live_arrow(new, self.record(entities, 25), 777)
        state.deserialize(state, handle)
        self.assertEqual(new.get(self.record(entities, 25) + 0x06, 2), 34)

    def test_restore_skips_a_record_of_another_kind(self):
        old = self.projectile_in_flight()
        new = self.units_only()
        state, handle = self.transfer(old, new)
        entities = new.get(new.v['FIREPROJ'] + 0x416)
        record = self.record(entities, 25)
        self.live_arrow(new, record, 777)
        new.put(record + 0x2A, 14, 2)  # same index, UID and slot, but a brazier
        state.deserialize(state, handle)
        self.assertEqual(new.get(record + 0x06, 2), 207)

    def test_save_is_refused_when_game_records_cannot_be_found(self):
        old = self.projectile_in_flight()
        def hide_records(h):
            spawn = h.scan(b'83 EC 08 53 8B 5C 24 34 83 FB 2B 56 8B F1')
            h.put(spawn, 0x90, 1)
        new = self.units_only(hide_records)
        new.put(new.v['COOLDOWNT'] + 4, 55)
        state, handle = self.transfer(old, new)
        with self.assertRaisesRegex(Exception, 'cannot be reset here'):
            state.deserialize(state, handle)
        self.assertEqual(new.get(new.v['COOLDOWNT'] + 4), 55)


class DamagedSaveTests(unittest.TestCase):
    """Save data is untrusted: damage is refused before anything is written."""

    def setUp(self):
        self.graphics = GraphicsMigrationTests()
        self.graphics.addCleanup = self.addCleanup

    def changed_handle(self):
        old = self.graphics.projectile_in_flight()
        new = self.graphics.units_only()
        state, handle = self.graphics.transfer(old, new)
        return new, state, handle

    def assert_refused(self, state, handle, message):
        with self.assertRaisesRegex(Exception, message):
            state.validate(state, handle)

    def test_graphics_ids_outside_native_sheets_or_16_bits_are_refused(self):
        new, state, handle = self.changed_handle()
        bases = bytearray(handle.files[b'variant-base-gm.bin'])
        bases[4:8] = (9999).to_bytes(4, 'little')
        handle.files[b'variant-base-gm.bin'] = bytes(bases)
        self.assert_refused(state, handle, 'variant-base-gm.bin')
        bases[4:8] = (0).to_bytes(4, 'little')
        handle.files[b'variant-base-gm.bin'] = bytes(bases)
        self.assert_refused(state, handle, 'variant-base-gm.bin')
        new, state, handle = self.changed_handle()
        slots = bytearray(handle.files[b'variant-gm.bin'])
        slots[4:8] = (0x100CF).to_bytes(4, 'little')
        handle.files[b'variant-gm.bin'] = bytes(slots)
        self.assert_refused(state, handle, 'out-of-range saved state: variant-gm.bin')

    def test_a_section_without_its_format_entry_is_refused(self):
        new, state, handle = self.changed_handle()
        handle.files[b'format'] = None
        self.assert_refused(state, handle, 'invalid saved state: format')

    def test_projectile_sheets_must_fit_the_saved_kind_and_definition(self):
        new, state, handle = self.changed_handle()
        bases = bytearray(handle.files[b'variant-base-gm.bin'])
        bases[4:8] = (135).to_bytes(4, 'little')  # cow sheet for an arrow
        handle.files[b'variant-base-gm.bin'] = bytes(bases)
        self.assert_refused(state, handle, 'variant-base-gm.bin')
        new, state, handle = self.changed_handle()
        variants = bytearray(handle.files[b'entity-variant.bin'])
        variants[26 * 4:27 * 4] = (5).to_bytes(4, 'little')  # no variant 5 in the saved definitions
        handle.files[b'entity-variant.bin'] = bytes(variants)
        self.assert_refused(state, handle, 'variant-base-gm.bin')

    def test_entity_zero_is_refused(self):
        new, state, handle = self.changed_handle()
        handle.files[b'entity-variant.bin'] = (1).to_bytes(4, 'little') + handle.files[b'entity-variant.bin'][4:]
        self.assert_refused(state, handle, 'entity-variant.bin')

    def test_undefined_variant_with_unchanged_settings_is_refused(self):
        old = self.graphics.units_only()
        new = self.graphics.units_only()
        state, handle = self.graphics.transfer(old, new)
        variants = bytearray(handle.files[b'entity-variant.bin'])
        variants[4:8] = (5).to_bytes(4, 'little')
        handle.files[b'entity-variant.bin'] = bytes(variants)
        self.assert_refused(state, handle, 'entity-variant.bin')
        strict = self.graphics.units_only()
        strict_state, strict_handle = self.graphics.transfer(old, strict)
        strict_state[b'allow_config_changes'] = False
        strict_handle.files[b'entity-variant.bin'] = bytes(variants)
        self.assert_refused(strict_state, strict_handle, 'entity-variant.bin')

    def test_format_six_metadata_must_be_complete_and_canonical(self):
        old = self.graphics.units_only()
        for name, value, message in (
                (b'decoration-names', None, 'invalid saved graphics names'),
                (b'decoration-names', b'1=frost;1=smoke;', 'invalid saved graphics names'),
                (b'decoration-names', b'1=frost;2=frost;', 'invalid saved graphics names'),
                (b'decoration-names', b'0=frost;', 'invalid saved graphics names'),
                (b'decoration-names', b'34=frost;', 'invalid saved graphics names'),
                (b'assets', None, 'invalid saved state: assets'),
                (b'assets', b'garbage', 'invalid saved state: assets'),
                (b'capacity', b'0x9C4', 'invalid saved unit capacity'),
                (b'capacity', b'2500.0', 'invalid saved unit capacity'),
                (b'capacity', b' 2500', 'invalid saved unit capacity')):
            with self.subTest(entry=name, value=value):
                new = self.graphics.units_only()
                state, handle = self.graphics.transfer(old, new)
                handle.files[name] = value
                self.assert_refused(state, handle, message)

    def test_placed_decorations_must_be_named_even_when_nothing_changed(self):
        old = self.graphics.decorations(['frost'])
        self.graphics.place(old, 40, 1, 4001)
        new = self.graphics.decorations(['frost'])
        state, handle = self.graphics.move(old, new)
        handle.files[b'decoration-names'] = b''
        self.assert_refused(state, handle, 'decoration-variant.bin')


if __name__ == '__main__':
    unittest.main()

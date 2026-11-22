"""Versioned saved-state formats: every accepted difference is a defined migration.

Format 6 records the unit capacity. Format 5 (1.8.x up to 1.8.19) is read with
the capacity derived from its per-unit blocks. Test-build formats 1-4 start the
module's timers fresh. Damaged data and unknown formats are refused, and
`allow_config_changes_on_load: false` keeps the earlier exact-match rules.
"""
import unittest
import test_feedback_fixes as feedback

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


if __name__ == '__main__':
    unittest.main()

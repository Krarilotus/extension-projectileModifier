"""Tester save retuning and native manual range admission regressions."""
import unittest
import json
from jsonschema import Draft202012Validator
from harness import Harness, ROOT, r
import test_projectiles as native_tests
import test_cadence as cadence_tests
import test_manual_cluster as manual_tests


class FeedbackFixTests(unittest.TestCase):
    def prepare(self, source, extreme=False, sprites=False):
        h = Harness(extreme)
        if sprites:
            h.lua.execute(b'''modules.gmResourceModifier={
                LoadCompleteGm1Resource=function() return 1,string.rep('a',64) end,
                FreeGm1Resource=function() end, ReserveGm=function() return 0 end,
                GetReservedGm=function() return 207 end}
                hooks={registerHookCallback=function() end}''')
        h.module.apply(h.config(source))
        h.v = {k: v for _, _, values in h.blobs.values() for k, v in values.items()}
        for owner in range(9): h.put(h.v['TEAMTBL'] + owner * 4, owner)
        return h

    def transfer(self, old, new):
        observer = native_tests.NativeTests()
        saved = observer.state_handle(old)
        original = old.sections[b'projectileModifier']
        original.serialize(original, saved)
        loaded = observer.state_handle(new)
        for name, content in saved.files.items(): loaded.files[name] = content
        return new.sections[b'projectileModifier'], loaded

    def test_gameplay_config_edits_load_reset_old_firing_state_and_retain_seed(self):
        for extreme in (False, True):
            old = self.prepare({'units': {'Catapult': {'interval': 700, 'count': 3}}}, extreme)
            new = self.prepare({'units': {'Catapult': {'interval': 300, 'count': 1,
                'projectile': 'firethrower_pot', 'ammo_by_target': {'units': {'Monk': 'regular'}}}}}, extreme)
            for symbol, value in (('COOLDOWNT', 500), ('PENDINGT', 2), ('PENDCDT', 20),
                                  ('SYNCWAITT', 3), ('PROFILESTATET', 39), ('UIDT', 1)):
                old.put(old.v[symbol] + 4, value)
                new.put(new.v[symbol] + 4, 99)
            old.put(old.v['SEED'], 123456)
            state, handle = self.transfer(old, new)
            before = [bytes(new.uc.mem_read(b[2], b[3])) for b in state.blocks.values()]
            plan = state.validate(state, handle)
            self.assertTrue(plan[b'reconfigure'])
            self.assertEqual(before, [bytes(new.uc.mem_read(b[2], b[3])) for b in state.blocks.values()])
            state.deserialize(state, handle)
            self.assertEqual(new.get(new.v['SEED']), 123456)
            for symbol in ('COOLDOWNT', 'PENDINGT', 'PENDCDT', 'SYNCWAITT', 'PROFILESTATET', 'UIDT'):
                self.assertEqual(new.get(new.v[symbol] + 4), 0)
            current = native_tests.NativeTests().state_handle(new)
            state.serialize(state, current)
            self.assertEqual(current.files[b'config'], state[b'config'])
            self.assertEqual(new.get(new.v['INTERVALT'] + 39 * 4), 300)

    def test_legacy_format_five_without_assets_can_be_retuned_when_visual_state_is_empty(self):
        for extreme in (False, True):
            old = self.prepare({'units': {'Catapult': {'interval': 700}}}, extreme)
            new = self.prepare({'units': {'Catapult': {'interval': 300}}}, extreme)
            state, handle = self.transfer(old, new)
            handle.files[b'assets'] = None  # Exact legacy format 5 payload.
            state.deserialize(state, handle)
            self.assertEqual(new.get(new.v['COOLDOWNT'] + 4), 0)
            # Unknown legacy visual IDs must not be silently reinterpreted.
            handle.files[b'entity-variant.bin'] = b'\1\0\0\0' + handle.files[b'entity-variant.bin'][4:]
            with self.assertRaisesRegex(Exception, 'legacy save contains custom graphics'):
                state.validate(state, handle)

    def test_strict_load_control_retains_old_rejection_and_is_not_gameplay_identity(self):
        schema = Draft202012Validator(json.loads((ROOT / 'projectile-config.schema.json').read_text(encoding='utf-8')))
        for value in (True, False):
            schema.validate({'allow_config_changes_on_load': value})
        old = self.prepare({'units': {'Catapult': {'interval': 700}}})
        strict = self.prepare({'allow_config_changes_on_load': False, 'units': {'Catapult': {'interval': 300}}})
        state, handle = self.transfer(old, strict)
        with self.assertRaisesRegex(Exception, 'saved projectile settings differ'):
            state.validate(state, handle)
        same = self.prepare({'allow_config_changes_on_load': False, 'units': {'Catapult': {'interval': 700}}})
        matching, saved = self.transfer(old, same)
        self.assertFalse(matching.validate(matching, saved)[b'reconfigure'])
        for invalid in ('true', 1, {}, 'native'):
            self.assertFalse(schema.is_valid({'allow_config_changes_on_load': invalid}))
            h = Harness()
            with self.assertRaisesRegex(Exception, 'allow_config_changes_on_load'):
                h.module.apply(h.config({'allow_config_changes_on_load': invalid}))
            self.assertEqual(h.allocations, [])

    def test_unchanged_graphics_survive_retuning_but_changed_definitions_are_rejected(self):
        for extreme in (False, True):
            assets = {'custom_arrow': {'inherits': 'arrow', 'sprites': 'gm/custom.gm1'}}
            old = self.prepare({'projectiles': assets, 'units': {'Catapult': {'interval': 700}}}, extreme, True)
            new = self.prepare({'projectiles': assets, 'units': {'Catapult': {'interval': 300}}}, extreme, True)
            old.put(old.v['ENTITYVARIANT'] + 4, 1)
            old.put(old.v['ENTITYUID'] + 4, 123)
            old.put(old.v['ENTITYTYPE'] + 4, 1)
            state, handle = self.transfer(old, new)
            state.deserialize(state, handle)
            self.assertEqual(new.get(new.v['ENTITYVARIANT'] + 4), 1)
            self.assertEqual(new.get(new.v['ENTITYUID'] + 4), 123)
            altered = self.prepare({'projectiles': {'custom_arrow': {'inherits': 'crossbow_bolt',
                'sprites': 'gm/custom.gm1'}}, 'units': {'Catapult': {'interval': 300}}}, extreme, True)
            incompatible, saved = self.transfer(old, altered)
            with self.assertRaisesRegex(Exception, 'custom projectile/decorations changed'):
                incompatible.validate(incompatible, saved)
            handle.files[b'assets'] = None
            with self.assertRaisesRegex(Exception, 'legacy save has no asset identity'):
                state.validate(state, handle)

    def test_manual_native_acquisition_rejects_out_of_range_before_windup_and_respects_off(self):
        for extreme in (False, True):
            for enabled in (True, False):
                h = native_tests.NativeTests().prepare({'Mangonel': {'interval': 400,
                    'range': 3, 'strict_range': enabled}}, extreme)
                a = h.unit(1, 41)
                h.unit(2, 22, owner=2, x=44)
                manual_tests.ManualClusterTests().order_unit(h, a, 2)
                self.assertEqual(h.call(h.v['ACQUIRE'], [1], {r.UC_X86_REG_ECX: h.v['UNITSTATE']}),
                                 0 if enabled else 1)
                self.assertEqual(h.uc.reg_read(r.UC_X86_REG_ESP), 0x53f0008)
                self.assertEqual(h.get(a + 0x39e, 2), 2)  # Native order retains approach/retry.
                h.unit(2, 22, owner=2, x=43)
                self.assertEqual(h.call(h.v['ACQUIRE'], [1], {r.UC_X86_REG_ECX: h.v['UNITSTATE']}), 1)

    def test_already_winding_up_out_of_range_mangonel_finishes_without_projectiles_or_freeze(self):
        for extreme in (False, True):
            h, a, tick = cadence_tests.CadenceTests().integrated('Mangonel', 41, 0x56a3f0,
                {'interval': 400, 'range': 3}, extreme)
            manual_tests.ManualClusterTests().order_unit(h, a, 2)
            h.call(h.v['ACQUIRE'], [1], {r.UC_X86_REG_ECX: h.v['UNITSTATE']})
            h.put(a + 0x2c0, 8, 2)  # A command accepted by an older build / saved wind-up.
            phases = []
            for _ in range(300):
                self.assertEqual(tick(), ([], []))
                phases.append(h.get(a + 0x2c0, 2))
            self.assertIn(4, phases)
            self.assertEqual(phases[-1], 0)  # Native engine finished/cancelled the swing.
            h.unit(2, 22, owner=2, x=42)
            manual_tests.ManualClusterTests().order_unit(h, a, 2)
            self.assertEqual(h.call(h.v['ACQUIRE'], [1], {r.UC_X86_REG_ECX: h.v['UNITSTATE']}), 1)
            h.put(a + 0x2c0, 8, 2)
            h.put(a + 0x2b0, 0)
            self.assertTrue(any(tick()[1] for _ in range(300)), 'valid retarget must fire again')

    def test_in_range_native_mangonel_retains_manual_aim_volley_and_reload(self):
        for extreme in (False, True):
            h, a, tick = cadence_tests.CadenceTests().integrated('Mangonel', 41, 0x56a3f0,
                {'interval': 400, 'range': 4, 'inaccuracy': 0}, extreme)
            manual_tests.ManualClusterTests().order_unit(h, a, 2)
            events = []
            for t in range(650):
                queued, shots = tick()
                self.assertEqual(queued, [])
                if shots:
                    events.append(t)
                    self.assertEqual(len(shots), 7)
                    self.assertTrue(all(s[6:8] == (352, 320) for s in shots))
            self.assertEqual(len(events), 2)
            self.assertEqual(events[1] - events[0], 400)


if __name__ == '__main__': unittest.main()

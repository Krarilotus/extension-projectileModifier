"""Optional target ammunition through the existing native firing/volley owner."""
import json
import unittest
import yaml
from jsonschema import Draft202012Validator
from harness import Harness, ROOT, r
import test_projectiles as native_tests


class TargetAmmunitionTests(unittest.TestCase):
    def prepare(self, config, extreme=False):
        h = Harness(extreme)
        h.module.apply(h.config(config))
        h.v = {k: v for _, _, values in h.blobs.values() for k, v in values.items()}
        for owner in range(9): h.put(h.v['TEAMTBL'] + owner * 4, owner)
        return h

    def settings(self, **extra):
        settings = dict(interval=1, sync_to_animation=False, projectile='mangonel_pebble',
                        count=3, ai_cow_vs_units=True)
        settings.update(extra)
        return settings

    def ai(self, h, kind=39, target=39):
        shooter = h.unit(1, kind)
        h.unit(2, target, 2, x=44)
        h.put(h.v['PLAYERAIC'] + 0x39f4, 1)
        h.put(h.v['AICCOW'] + 0x2a4, 1)
        return shooter

    def validate(self, source):
        h = Harness()
        return h.lua.execute(b"return (require('configuration'))").validate(h.config(source))

    def test_groups_expand_and_exact_rules_win_without_changing_save_identity(self):
        source = {'unit_groups': {'siege': ['Catapult', 'Trebuchet']}, 'units': {
            'Catapult': self.settings(ammo_by_target={
                'groups': {'siege': 'regular'}, 'units': {'Trebuchet': 'cow'}})}}
        grouped = self.validate(source)
        self.assertIsNone(grouped[b'unit_groups'])
        rules = grouped[b'units'][b'Catapult'][b'ammo_by_target']
        self.assertEqual(dict(rules.items()), {b'Catapult': b'regular', b'Trebuchet': b'cow'})
        direct = {'units': {'Catapult': self.settings(ammo_by_target={
            'units': {'Catapult': 'regular', 'Trebuchet': 'cow'}})}}
        h = Harness()
        cfg = h.lua.execute(b"return (require('configuration'))")
        state = h.lua.execute(b"return (require('state'))")
        self.assertEqual(state.new(h.config([]), cfg.validate(h.config(source)))[b'config'],
                         state.new(h.config([]), cfg.validate(h.config(direct)))[b'config'])

    def test_invalid_groups_ammunition_and_dependencies_fail_before_patching(self):
        cases = [({'unit_groups': False}, 'expected a mapping'),
                 ({'unit_groups': {'Siege': ['Catapult']}}, 'lowercase'),
                 ({'unit_groups': {'siege': []}}, 'unit names'),
                 ({'unit_groups': {'siege': ['Catapult', 'Catapult']}}, 'distinct'),
                 ({'unit_groups': {'siege': ['Cata-pult']}}, 'known'),
                 ({'units': {'Catapult': {'ammo_by_target': {'units': {'Monk': 'cow'}}}}}, 'interval'),
                 ({'units': {'Catapult': self.settings(ammo_by_target={'groups': {'siege': 'regular'}})}}, 'unknown unit group'),
                 ({'units': {'Catapult': self.settings(ammo_by_target={'units': False})}}, 'mapping'),
                 ({'units': {'Catapult': self.settings(ammo_by_target={'units': {'Monk': 'typo'}})}}, 'projectile type')]
        for source, message in cases:
            with self.subTest(source=source):
                h = Harness()
                with self.assertRaisesRegex(Exception, message): h.module.apply(h.config(source))
                self.assertEqual((h.scans, h.writes, h.allocations), ([], [], []))

    def test_overlapping_conflicting_groups_require_exact_rule(self):
        source = {'unit_groups': {'a': ['Catapult'], 'b': ['Catapult']}, 'units': {
            'Catapult': self.settings(ammo_by_target={'groups': {'a': 'regular', 'b': 'cow'}})}}
        with self.assertRaisesRegex(Exception, 'conflicting group'): self.validate(source)
        source['units']['Catapult']['ammo_by_target']['units'] = {'Catapult': 'arrow'}
        self.assertEqual(self.validate(source)[b'units'][b'Catapult'][b'ammo_by_target'][b'Catapult'], 1)

    def test_maps_replace_and_native_clears_inherited_rules(self):
        source = {'unit_groups': {'siege': ['Catapult']}, 'units': {'Catapult': self.settings(
            ammo_by_target={'groups': {'siege': 'regular'}},
            on_fortification={'ammo_by_target': 'native'})}}
        cfg = self.validate(source)[b'units'][b'Catapult']
        self.assertIsNone(cfg[b'on_fortification'][b'ammo_by_target'])
        source['units']['Catapult']['on_fortification']['ammo_by_target'] = {'units': {'Monk': 'cow'}}
        wall = self.validate(source)[b'units'][b'Catapult'][b'on_fortification'][b'ammo_by_target']
        self.assertEqual(dict(wall.items()), {b'Monk': b'cow'})

    def test_regular_rules_override_ai_cows_but_unmatched_troops_keep_cows(self):
        for extreme in (False, True):
            for kind in (39, 40):
                for target, projectile, count in ((39, 4, 3), (22, 23, 1)):
                    with self.subTest(extreme=extreme, kind=kind, target=target):
                        name = 'Catapult' if kind == 39 else 'Trebuchet'
                        h = self.prepare({'unit_groups': {'siege': ['Catapult']}, 'units': {
                            name: self.settings(ammo_by_target={'groups': {'siege': 'regular'}})}}, extreme)
                        shooter = self.ai(h, kind, target)
                        shots = native_tests.NativeTests().tick(h, 1)
                        self.assertEqual([s[9] for s in shots], [projectile] * count)
                        self.assertEqual(h.get(shooter + 0x3b0, 2), 0)

    def test_explicit_cow_slot_uses_cow_remap_and_count_without_aic_cow_permission(self):
        for extreme in (False, True):
            h = self.prepare({'units': {'Catapult': self.settings(cow_projectile='arrow', cow_count=2,
                ammo_by_target={'units': {'Monk': 'cow'}})}}, extreme)
            self.ai(h, target=37)
            h.put(h.v['AICCOW'] + 0x2a4, 0)
            self.assertEqual([s[9] for s in native_tests.NativeTests().tick(h, 1)], [1, 1])

    def test_native_artillery_release_chooses_regular_for_siege_and_cows_for_troops(self):
        import test_cadence as cadence_tests
        for extreme in (False, True):
            for name, kind, handler in (('Catapult', 39, 0x568320), ('Trebuchet', 40, 0x569410)):
                for target, expected in ((39, [4, 4, 4]), (22, [23])):
                    with self.subTest(extreme=extreme, shooter=name, target=target):
                        h, a, tick = cadence_tests.CadenceTests().integrated(name, kind, handler,
                            self.settings(interval=400, sync_to_animation=True,
                                ammo_by_target={'units': {'Catapult': 'regular'}}), extreme)
                        h.unit(2, target, 2, x=44)
                        h.put(h.v['PLAYERAIC'] + 0x39f4, 1)
                        h.put(h.v['AICCOW'] + 0x2a4, 1)
                        emitted = []
                        for _ in range(300):
                            queued, shots = tick()
                            self.assertEqual(queued, [])
                            if shots: emitted.append([shot[9] for shot in shots])
                        self.assertEqual(emitted, [expected])
                        self.assertEqual(h.get(a + 0x362, 2), 999)

    def test_mixed_random_volley_selects_actual_victim_and_resets_cow_dispatch(self):
        for extreme in (False, True):
            h = self.prepare({'units': {'Catapult': self.settings(count=16, cow_count=16,
                random_targets=True, ammo_by_target={'units': {'Monk': 'cow', 'Catapult': 'regular'}})}}, extreme)
            shooter = self.ai(h, target=37)
            h.unit(3, 39, 2, x=45)
            emitted = []
            def spawn(observed):
                target = observed.get(shooter + 0x344, 2)
                esp = observed.uc.reg_read(r.UC_X86_REG_ESP)
                emitted.append((target, observed.get(esp + 40), observed.get(shooter + 0x3b0, 2)))
                native_tests.NativeTests().spawn_callback([])(observed)
            h.put(h.v['CURUNIT'], 1)
            h.call(h.blobs['tickHook'][0], registers={r.UC_X86_REG_EDX: 1, r.UC_X86_REG_ESI: h.v['UNITSTATE']},
                   stop=h.blobs['tickHook'][2]['RESUME'], callbacks={h.spawner: spawn})
            self.assertEqual(len(emitted), 16)
            self.assertEqual({shot[0] for shot in emitted}, {2, 3})
            self.assertTrue(all((projectile, flag) == ((23, 1) if target == 2 else (4, 0))
                                for target, projectile, flag in emitted), emitted)
            self.assertEqual(h.get(shooter + 0x3b0, 2), 0)

    def test_native_manual_and_cow_orders_do_not_inherit_automatic_rules(self):
        for extreme in (False, True):
            h = self.prepare({'units': {'Catapult': {'interval': 700, 'projectile': 'mangonel_pebble',
                'ammo_by_target': {'units': {'Monk': 'cow'}}}}}, extreme)
            a = h.unit(1, 39)
            h.unit(2, 37, 2, x=44)
            h.put(a + 0x344, 2, 2); h.put(a + 0xa0, 2)
            h.put(a + 0x39c, 4, 2)
            h.put(h.v['S_ID'], 1); h.put(h.v['S_UNITPTR'], a); h.put(h.v['S_MODE'], 1)
            h.call(h.v['CHOOSEAMMO'], registers={r.UC_X86_REG_EDX: 39})
            self.assertEqual(h.get(h.v['S_PROJ']), 4)
            self.assertEqual(h.get(h.v['S_TARGETAMMO']), 0)
            # Stale rule scratch from an automatic volley cannot affect native cows.
            h.put(h.v['S_TARGETAMMO'], h.get(h.v['AMMOPTRT'] + 39 * 4))
            h.put(a + 0x3b0, 1, 2)
            self.assertEqual([s[9] for s in native_tests.NativeTests().fire(h, 1)], [23])

    def test_lookup_rejects_reused_target_identity_and_invalid_ids(self):
        h = self.prepare({'units': {'Catapult': self.settings(ammo_by_target={'units': {'Monk': 'cow'}})}})
        a = self.ai(h, target=37)
        h.put(h.v['S_TARGETAMMO'], h.get(h.v['AMMOPTRT'] + 39 * 4))
        h.put(h.v['S_UNITPTR'], a)
        for target, uid in ((2, 99), (0, 0), (h.v['MAXUNITS'], 0)):
            h.put(a + 0x344, target, 2); h.put(a + 0xa0, uid)
            h.put(h.v['S_PROJ'], 4)
            self.assertEqual(h.call(h.v['TARGETAMMO']), 0)
            self.assertEqual(h.get(h.v['S_PROJ']), 4)

    def test_rule_uses_existing_custom_sprite_owner_and_regular_count(self):
        for extreme in (False, True):
            h = Harness(extreme)
            h.lua.execute(b'''modules.gmResourceModifier={
                LoadCompleteGm1Resource=function() return 1,string.rep('a',64) end,
                FreeGm1Resource=function() end, ReserveGm=function() return 0 end,
                GetReservedGm=function() return 207 end}
                hooks={registerHookCallback=function() end}''')
            h.module.apply(h.config({'projectiles': {'custom_arrow': {
                'inherits': 'arrow', 'sprites': 'gm/custom.gm1'}}, 'units': {
                'Catapult': self.settings(ammo_by_target={'units': {'Monk': 'custom_arrow'}})}}))
            h.v = {k: v for _, _, values in h.blobs.values() for k, v in values.items()}
            for owner in range(9): h.put(h.v['TEAMTBL'] + owner * 4, owner)
            self.ai(h, target=37)
            emitted = []
            def spawn(observed):
                emitted.append(observed.get(observed.v['CURRENTVARIANT']))
                native_tests.NativeTests().spawn_callback([])(observed)
            h.put(h.v['CURUNIT'], 1)
            h.call(h.blobs['tickHook'][0], registers={r.UC_X86_REG_EDX: 1, r.UC_X86_REG_ESI: h.v['UNITSTATE']},
                   stop=h.blobs['tickHook'][2]['RESUME'], callbacks={h.spawner: spawn})
            self.assertEqual(emitted, [1, 1, 1])

    def test_saved_staggered_mixed_volley_replays_deterministically_without_allocations(self):
        for extreme in (False, True):
            h = self.prepare({'units': {'Catapult': self.settings(interval=13, count=4,
                cow_count=4, stagger_max=3, random_targets=True,
                ammo_by_target={'units': {'Monk': 'cow', 'Catapult': 'regular'}})}}, extreme)
            self.ai(h, target=37)
            h.unit(3, 39, 2, x=45)
            observer = native_tests.NativeTests()
            observer.tick(h, 1)
            state = h.sections[b'projectileModifier']
            handle = observer.state_handle(h)
            state.serialize(state, handle)
            allocations = list(h.allocations)
            scans = list(h.scans)
            first = [observer.tick(h, 1) for _ in range(30)]
            end = observer.state_handle(h)
            state.serialize(state, end)
            state.deserialize(state, handle)
            second = [observer.tick(h, 1) for _ in range(30)]
            replayed = observer.state_handle(h)
            state.serialize(state, replayed)
            self.assertEqual(first, second)
            self.assertEqual(dict(end.files.items()), dict(replayed.files.items()))
            self.assertTrue(any(first))
            self.assertEqual((h.allocations, h.scans), (allocations, scans))

    def test_rules_are_opt_in_and_apply_to_previously_non_shooting_unit_types(self):
        h = self.prepare({'units': {'Catapult': self.settings()}})
        self.assertNotIn('targetAmmo', h.blobs)
        empty = Harness()
        empty.module.apply(empty.config({'unit_groups': {'siege': ['Catapult']}, 'units': {
            'Catapult': {'ammo_by_target': 'native'}}}))
        self.assertEqual((empty.allocations, empty.scans, empty.writes), ([], [], []))
        for extreme in (False, True):
            h = self.prepare({'units': {name: self.settings(ammo_by_target={'units': {'Monk': 'arrow'}})
                for name in ('Engineer', 'Siege tower', 'European spearman')}}, extreme)
            self.ai(h, target=37)
            for kind in (30, 58, 24):
                h.unit(1, kind)
                h.put(h.v['UIDT'] + 4, 0)
                self.assertEqual([s[9] for s in native_tests.NativeTests().tick(h, 1)], [1, 1, 1])

    def test_schema_and_supplied_presets_cover_native_and_group_rules(self):
        schema = Draft202012Validator(json.loads((ROOT / 'projectile-config.schema.json').read_text()))
        for name in ('vanilla-projectiles.yml', 'examples/reconquista-projectiles.yml'):
            source = yaml.safe_load((ROOT / name).read_text(encoding='utf-8'))
            schema.validate(source)
            self.validate(source)
        native = yaml.safe_load((ROOT / 'vanilla-projectiles.yml').read_text())
        self.assertTrue(all(unit['ammo_by_target'] == 'native' for unit in native['units'].values()))


if __name__ == '__main__': unittest.main()

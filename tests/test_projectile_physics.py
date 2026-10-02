"""Delegate to the actual Rebalancer API and execute the native flight owner."""
import json
import struct
import unittest
import yaml
from jsonschema import Draft202012Validator
from harness import Harness, ROOT, r
import test_projectiles as native_tests

OWNER = ROOT.parent / 'rebalancer'


def install_rebalancer_api(h):
    # Execute the actual owner's projectiles routine and exported caller, not a
    # second implementation. Unrelated balance sections remain absent.
    source = (OWNER / 'init.lua').read_bytes()
    edit = source[source.index(b'local function edit_projectiles('):source.index(b'local function edit_leather_per_cow(')]
    call = source[source.index(b'local function apply_rebalance_function('):source.index(b'namespace.enable =')]
    addresses = []
    for name in (b'proj_velocity_table_addr', b'proj_archtype_table_addr'):
        start = source.index(b'local ' + name + b' = locate_aob(')
        addresses.append(source[start:source.index(b'\n', start)])
    h.lua.globals().core.writeCodeInteger = h.lua.globals().core.writeInteger
    h.lua.execute(b'local locate_aob=core.AOBScan; local namespace={};\n' + b'\n'.join(addresses) + b'\n' + edit + call + b'\nmodules.rebalancer=namespace')
    framework = ROOT.parent / 'UnofficialCrusaderPatch3/content/ucp/code/hooks.lua'
    events = framework.read_bytes()
    register = events[events.index(b'local function registerHookCallback'):events.index(b'local function fireCallbacksForHook')]
    h.lua.execute(b'HOOKS={afterInit={}};\n'+register+b'\nhooks={registerHookCallback=registerHookCallback}')


class ProjectilePhysicsTests(unittest.TestCase):
    def prepare(self, physics, units=None, extreme=False):
        h = Harness(extreme)
        install_rebalancer_api(h)
        h.module.apply(h.config({'projectile_physics': physics, 'units': units or {}}))
        h.lua.execute(b'for _, callback in ipairs(HOOKS.afterInit) do callback() end')
        h.v = {k: v for _, _, values in h.blobs.values() for k, v in values.items()}
        return h

    def test_reuses_owner_tables_on_both_families_and_native_is_inert(self):
        for extreme in (False, True):
            h = self.prepare({'firethrower_pot': {'mode':'fixed_angle','angle':30},
                              'arrow': {'mode':'fixed_speed','speed':150}}, extreme=extreme)
            # Original property-setup reader, resolved by identifying code;
            # operands agree with the owner's existing AOB-selected data tables.
            code = h.scan(b'8B 14 8D ? ? ? ? 85 D2 5E 74 1B 83 FA 06 74 16 83 FA 09 74 11')
            arcs = h.get(code+3)
            speed = h.get(code+0x1a)
            self.assertEqual(h.get(arcs + 34*4), 1)
            self.assertEqual(h.get(speed + 34*4), 30)
            self.assertEqual(h.get(arcs + 4), 0)
            self.assertEqual(h.get(speed + 4), 150)
            self.assertEqual(h.allocations, [])  # Physics-only uses the owner alone.
            inert = Harness(extreme)
            inert.module.apply(inert.config({'projectile_physics':{'firethrower_pot':'native'}}))
            self.assertEqual(inert.scans, [])
            self.assertEqual(inert.writes, [])

    def test_invalid_inputs_and_missing_owner_fail_before_mutation(self):
        invalid = [False, {'wrong':{'mode':'fixed_angle','angle':30}},
            {'firethrower_pot':{}}, {'firethrower_pot':{'mode':'fixed_speed','angle':30}},
            {'firethrower_pot':{'mode':'fixed_angle','angle':0}},
            {'firethrower_pot':{'mode':'fixed_angle','angle':90}},
            {'firethrower_pot':{'mode':'fixed_speed','speed':1001}},
            {'firethrower_pot':{'mode':'fixed_speed','speed':80.5}},
            {'firethrower_pot':{'mode':'fixed_angle','angle':30,'damage':2}}]
        for physics in invalid:
            h = Harness()
            with self.assertRaisesRegex(Exception, 'projectile_physics'):
                h.module.apply(h.config({'projectile_physics':physics}))
            self.assertEqual(h.allocations, [])
            self.assertEqual(h.writes, [])
        h = Harness()
        with self.assertRaisesRegex(Exception, 'requires active Rebalancer'):
            h.module.apply(h.config({'projectile_physics':{'arrow':{'mode':'fixed_speed','speed':125}},
                                    'units':{'Catapult':{'projectile':'arrow'}}}))
        self.assertEqual(h.allocations, [])
        self.assertEqual(h.writes, [])
        h=Harness()
        install_rebalancer_api(h)
        h.lua.globals().hooks=None
        with self.assertRaisesRegex(Exception,'requires the framework afterInit'):
            h.module.apply(h.config({'projectile_physics':{'arrow':{'mode':'fixed_speed','speed':125}}}))
        self.assertEqual(h.allocations,[])
        self.assertEqual(h.writes,[])

    def test_framework_event_applies_after_owner_balance_enable(self):
        h=Harness()
        install_rebalancer_api(h)
        h.module.apply(h.config({'projectile_physics':{'arrow':{'mode':'fixed_speed','speed':150}}}))
        # Simulate a later-enabled owner's balance preset overwriting the same
        # value. Actual framework registration defers ours until game init.
        h.lua.execute(b'modules.rebalancer.apply_rebalance({projectiles={arrow={velocity=100}}})')
        code=h.scan(b'8B 14 8D ? ? ? ? 85 D2 5E 74 1B 83 FA 06 74 16 83 FA 09 74 11')
        speed=h.get(code+0x1a)
        self.assertEqual(h.get(speed+4),100)
        h.lua.execute(b'for _, callback in ipairs(HOOKS.afterInit) do callback() end')
        self.assertEqual(h.get(speed+4),150)
        self.assertEqual(h.allocations,[])

    def test_schema_and_examples_and_complete_vanilla_reference(self):
        schema = Draft202012Validator(json.loads((ROOT/'projectile-config.schema.json').read_text(encoding='utf-8')))
        for name in ('vanilla-projectiles.yml', 'examples/long-range-replacements.yml'):
            config = yaml.safe_load((ROOT/name).read_text(encoding='utf-8'))
            schema.validate(config)
            h = Harness()
            h.lua.execute(b"return require('configuration')").validate(h.config(config))
        for name in ('fixed_speed','fixed_angle','adaptive_angle'):
            field = 'speed' if name=='fixed_speed' else 'angle'
            schema.validate({'projectile_physics':{'arrow':{'mode':name,field:30}}})
        self.assertFalse(schema.is_valid({'projectile_physics':{'arrow':{'mode':'fixed_angle','speed':30}}}))
        self.assertFalse(schema.is_valid({'projectile_physics':[]}))

    def test_native_fixed_angle_long_range_flight_all_five_engines_both_families(self):
        for extreme in (False, True):
            h = self.prepare({name:{'mode':'fixed_angle','angle':30} for name in
                             ('firethrower_pot','arrow','crossbow_bolt','slinger_stone')},
                {name:{'projectile':'firethrower_pot','count':1} for name in
                    ('Catapult','Trebuchet','Mangonel','Tower ballista','Fire ballista')}, extreme)
            state = h.get(h.v['FIREPROJ']+0x416)
            raw = bytes(h.uc.mem_read(h.spawner,0x500))
            validity = struct.unpack_from('<I',raw,raw.index(b'\x80\xbc\x01')+3)[0]
            h.uc.mem_write(validity,b'\1'*160000)
            for y in range(1,399): h.put(h.v['TILEROWS']+12*y,400*y)
            # Native move owner shares identifying code on both EXEs.
            mover = h.scan(b'83 EC 10 53 55 56 57 8B 7C 24 24 8B C7 69 C0 E8 00 00 00 8B D9')
            for kind, ammo in ((39,2),(40,3),(41,4),(61,20),(77,37)):
                for projectile, type_id in (('firethrower_pot',34),('arrow',1),('crossbow_bolt',7),('slinger_stone',33)):
                  h.put(h.v['REMAPT']+kind*4,type_id)
                  for distance in (30,40,50):
                    with self.subTest(extreme=extreme,kind=kind,distance=distance,projectile=projectile):
                        h.unit(1,kind)
                        h.put(h.v['NATIVESEENT']+4,0)
                        shots=[]
                        target=320+distance*8
                        h.call(h.v['FIREPROJ'],[1,ammo,target,320,0],
                            {r.UC_X86_REG_ECX:h.v['UNITSTATE']},callbacks={h.spawner:native_tests.NativeTests().spawn_callback(shots)})
                        self.assertEqual(len(shots),1)
                        self.assertEqual(shots[0][9],type_id)
                        h.put(state+8,25)
                        entity=state+20+25*232
                        h.uc.mem_write(entity,b'\0'*232)
                        self.assertEqual(h.call(h.spawner,shots[0],{r.UC_X86_REG_ECX:state}),25)
                        self.assertEqual(h.get(entity+0x2a,2),type_id)
                        self.assertEqual(h.get(entity+0x2c,2),1)
                        self.assertEqual(h.get(entity+0xa2,2),1)
                        self.assertGreater(h.get(entity+0x96,2),0)
                        for tick in range(200):
                            h.call(mover,[25],{r.UC_X86_REG_ECX:state})
                            if h.get(entity+0x6c,2): break
                        self.assertLess(tick,199)
                        self.assertLessEqual(abs(h.get(entity+0x38,2)-target),8)
                        self.assertLessEqual(abs(h.get(entity+0x3a,2)-320),8)

    def test_physics_retuning_participates_in_existing_save_identity(self):
        old=self.prepare({'firethrower_pot':{'mode':'fixed_angle','angle':30}},
                         {'Catapult':{'interval':700}})
        new=self.prepare({'firethrower_pot':{'mode':'fixed_angle','angle':45}},
                         {'Catapult':{'interval':700}})
        saved=native_tests.NativeTests().state_handle(old)
        state=old.sections[b'projectileModifier']
        state.serialize(state,saved)
        loaded=native_tests.NativeTests().state_handle(new)
        for key,value in saved.files.items(): loaded.files[key]=value
        current=new.sections[b'projectileModifier']
        self.assertTrue(current.validate(current,loaded)[b'reconfigure'])
        current.allow_config_changes=False
        with self.assertRaisesRegex(Exception,'saved projectile settings differ'):
            current.validate(current,loaded)


if __name__ == '__main__': unittest.main()

"""Explicit native inheritance must not install overrides or lose old presets."""
import json
import unittest
import yaml
from jsonschema import Draft202012Validator
from harness import Harness, ROOT
import test_projectiles as projectile_tests


class NativeConfigTests(unittest.TestCase):
    def test_complete_reference_is_inert_on_both_families(self):
        source=yaml.safe_load((ROOT/'vanilla-projectiles.yml').read_text(encoding='utf-8'))
        schema=Draft202012Validator(json.loads((ROOT/'projectile-config.schema.json').read_text()))
        schema.validate(source)
        for extreme in (False,True):
            h=Harness(extreme)
            c=h.lua.execute(b"return (require('configuration'))")
            canonical={key.decode() for key in c.numbers.keys() if not key.endswith(b'_tiles')}
            canonical|={key.decode() for key in c.booleans.keys()}
            canonical|={'projectile','cow_projectile','targets','target_bias_tiles','ammo_by_target','on_fortification','near_decorations'}
            self.assertEqual(len(source['units']),77)
            self.assertTrue(all(set(fields)==canonical for fields in source['units'].values()))
            projectile_tests.ConfigTests().load_file(h,ROOT/'vanilla-projectiles.yml')
            self.assertEqual(h.scans,[])
            self.assertEqual(h.allocations,[])
            self.assertEqual(h.writes,[])

    def test_editing_one_native_value_only_changes_that_value(self):
        source=yaml.safe_load((ROOT/'vanilla-projectiles.yml').read_text(encoding='utf-8'))
        source['units']['Catapult']['projectile']='firethrower_pot'
        source['units']['Catapult']['auto_targeting']=False
        h=Harness();c=h.lua.execute(b"return (require('configuration'))")
        result=c.validate(h.config(source))[b'units']
        self.assertEqual(list(result.keys()),[b'Catapult'])
        self.assertEqual(dict(result[b'Catapult'].items()),{b'projectile':34,b'auto_targeting':False})

    def test_native_overrides_reset_parent_values_and_allow_concrete_aliases(self):
        h=Harness();c=h.lua.execute(b"return (require('configuration'))")
        validator=Draft202012Validator(json.loads((ROOT/'projectile-config.schema.json').read_text()))
        for fields in ({'spread':'native'},{'spread':'native','spread_tiles':2},
                       {'spread':3,'spread_tiles':'native'}):
            source={'units':{'Catapult':{'spread':8,'auto_targeting':False,
                'on_fortification':dict(fields,auto_targeting='native')}}}
            validator.validate(source)
            result=c.validate(h.config(source))[b'units'][b'Catapult'][b'on_fortification']
            self.assertIsNone(result[b'auto_targeting'])
            expected={k.encode():v for k,v in fields.items() if v!='native'}
            self.assertEqual(dict(result.items()),expected)

    def test_native_does_not_hide_invalid_keys_or_rename_an_existing_variant(self):
        h=Harness();c=h.lua.execute(b"return (require('configuration'))")
        with self.assertRaisesRegex(Exception,'unknown setting'):
            c.validate(h.config({'units':{'Catapult':{'typo':'native'}}}))
        source={'projectiles':{'native':{'inherits':'arrow','sprites':'gm/body_missile.gm1'}},
                'units':{'Catapult':{'projectile':'native'}}}
        result=c.validate(h.config(source))
        self.assertEqual(result[b'units'][b'Catapult'][b'projectile'],result[b'projectiles'][b'native'][b'id'])

    def test_threat_priority_validates_and_can_be_cleared_by_native(self):
        h=Harness();c=h.lua.execute(b"return (require('configuration'))")
        validator=Draft202012Validator(json.loads((ROOT/'projectile-config.schema.json').read_text()))
        source={'units':{'Catapult':{'interval':700,'threat_priority':{'Monk':10},
            'on_fortification':{'threat_priority':'native'}}}}
        validator.validate(source)
        result=c.validate(h.config(source))[b'units'][b'Catapult']
        self.assertEqual(result[b'threat_priority'][b'Monk'],10)
        self.assertIsNone(result[b'on_fortification'][b'threat_priority'])
        source['units']['Catapult']['threat_priority']={'Monk':0}
        validator.validate(source)
        self.assertIsNone(c.validate(h.config(source))[b'units'][b'Catapult'][b'threat_priority'])
        for invalid in ({'Unknown':1},{'Monk':256},{'Monk':-1},{'Monk':1.5}):
            source['units']['Catapult']['threat_priority']=invalid
            self.assertFalse(validator.is_valid(source))
            with self.assertRaisesRegex(Exception,'threat_priority'):
                c.validate(h.config(source))

    def test_target_bias_aliases_preserve_normalized_config_and_override_order(self):
        h=Harness();c=h.lua.execute(b"return (require('configuration'))")
        validator=Draft202012Validator(json.loads((ROOT/'projectile-config.schema.json').read_text()))
        old={'units':{'Catapult':{'threat_priority':{'Monk':3}}}}
        new={'units':{'Catapult':{'target_bias_tiles':{'Monk':3}}}}
        for source in (old,new): validator.validate(source)
        def normalized(source):
            unit=c.validate(h.config(source))[b'units'][b'Catapult']
            return {key:dict(value.items()) if hasattr(value,'items') else value
                    for key,value in unit.items()}
        self.assertEqual(normalized(old),normalized(new))
        source={'units':{'Catapult':{
            'target_bias_tiles':{'Monk':3},
            'on_fortification':{'threat_priority':'native'}}}}
        validator.validate(source)
        result=c.validate(h.config(source))[b'units'][b'Catapult']
        self.assertEqual(result[b'threat_priority'][b'Monk'],3)
        self.assertIsNone(result[b'on_fortification'][b'threat_priority'])
        source['units']['Catapult']['on_fortification']={'threat_priority':{'Monk':2}}
        validator.validate(source)
        self.assertEqual(c.validate(h.config(source))[b'units'][b'Catapult'][b'on_fortification'][b'threat_priority'][b'Monk'],2)
        source['units']['Catapult']['target_bias_tiles']='native'
        source['units']['Catapult']['on_fortification']={'threat_priority':{'Monk':2}}
        validator.validate(source)
        self.assertIsNone(c.validate(h.config(source))[b'units'][b'Catapult'][b'threat_priority'])
        for location in ('base','wall'):
            conflict={'target_bias_tiles':{'Monk':3},'threat_priority':{'Monk':2}}
            source={'units':{'Catapult':conflict if location=='base' else
                {'on_fortification':conflict}}}
            self.assertFalse(validator.is_valid(source))
            with self.assertRaisesRegex(Exception,'use only one of target_bias_tiles and threat_priority'):
                c.validate(h.config(source))
        source={'decorations':{'training':{}},'units':{'Catapult':{
            'threat_priority':{'Monk':3},
            'near_decorations':[{'decoration':'training',
                'target_bias_tiles':{'Monk':2}}]}}}
        validator.validate(source)
        self.assertEqual(c.validate(h.config(source))[b'units'][b'Catapult'][b'near_decorations'][1][b'ground'][b'threat_priority'][b'Monk'],2)
        source['units']['Catapult']['near_decorations'][0]['threat_priority']={'Monk':1}
        self.assertFalse(validator.is_valid(source))
        with self.assertRaisesRegex(Exception,'use only one of target_bias_tiles and threat_priority'):
            c.validate(h.config(source))


if __name__ == '__main__':
    unittest.main()

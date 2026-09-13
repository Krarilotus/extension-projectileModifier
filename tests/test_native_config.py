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
            canonical|={'projectile','cow_projectile','targets','on_fortification','near_decorations'}
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


if __name__ == '__main__':
    unittest.main()

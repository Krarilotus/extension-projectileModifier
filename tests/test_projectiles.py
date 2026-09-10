import unittest
import yaml
import re
from harness import Harness, ROOT, r

class NativeTests(unittest.TestCase):
    def prepare(self, units, extreme=False):
        h=Harness(extreme); h.enable(units)
        values={}
        for _,_,v in h.blobs.values(): values.update(v)
        h.v=values
        for owner in range(9): h.put(values['TEAMTBL']+owner*4,owner)
        return h

    def spawn_callback(self, shots):
        def spawn(h):
            esp=h.uc.reg_read(r.UC_X86_REG_ESP)
            shots.append(tuple(h.get(esp+4+i*4) for i in range(11)))
            h.uc.reg_write(r.UC_X86_REG_EIP,h.get(esp))
            h.uc.reg_write(r.UC_X86_REG_ESP,esp+48)
        return spawn

    def fire(self,h,id,kind=2):
        shots=[]
        h.call(h.v['FIREPROJ'],[id,kind,352,320,30],
            {r.UC_X86_REG_ECX:h.v['UNITSTATE']},callbacks={h.spawner:self.spawn_callback(shots)})
        self.assertEqual(h.uc.reg_read(r.UC_X86_REG_ESP),0x53f0018)
        return shots

    def tick(self,h,id):
        h.put(h.v['CURUNIT'],id)
        shots=[]
        entry=h.blobs['tickHook'][0]
        # Resume address is different for the two hooks; read it from this blob.
        stop=h.blobs['tickHook'][2]['RESUME']
        h.call(entry,registers={r.UC_X86_REG_EDX:id,r.UC_X86_REG_ESI:h.v['UNITSTATE']},
            stop=stop,callbacks={h.spawner:self.spawn_callback(shots)})
        self.assertEqual(h.uc.reg_read(r.UC_X86_REG_ESP),0x53f0000)
        self.assertEqual(h.uc.reg_read(r.UC_X86_REG_EDX),id+1)
        self.assertEqual(h.get(h.v['UNITSTATE']),id+1)
        return shots

    def test_native_dispatcher_remap_and_count_both_executables(self):
        for extreme in [False,True]:
            h=self.prepare({'Catapult':{'projectile':'mangonel_pebble','count':3}},extreme)
            h.unit(1,39)
            shots=self.fire(h,1)
            self.assertEqual(len(shots),3)
            self.assertTrue(all(s[9]==4 for s in shots),shots)
            self.assertEqual(h.get(h.v['REENTRY']),0)

    def test_unconfigured_shot_passes_through(self):
        h=self.prepare({'Catapult':{'count':3}}); h.unit(1,22)
        shots=self.fire(h,1,1)
        self.assertEqual(len(shots),1); self.assertEqual(shots[0][9],1)

    def test_tower_fires_exact_count_and_interval_both_executables(self):
        for extreme in [False,True]:
            h=self.prepare({'Siege tower':{'interval':3,'count':2,'projectile':'crossbow_bolt'}},extreme)
            a=h.unit(1,58); h.unit(2,22,2,x=44)
            before=bytes(h.uc.mem_read(a+0xbe,8))
            series=[len(self.tick(h,1)) for _ in range(7)]
            self.assertEqual(series,[2,0,0,2,0,0,2])
            self.assertEqual(bytes(h.uc.mem_read(a+0xbe,8)),before)

    def test_allied_neutral_dead_and_transitioning_units_are_not_targets(self):
        h=self.prepare({'Siege tower':{'interval':1}}); h.unit(1,58)
        for id,owner in [(2,0),(3,1),(4,2),(5,3),(6,4)]: h.unit(id,22,owner,x=44)
        h.put(h.base+4*0x490+0x3c8,0)
        h.put(h.base+5*0x490+0x8c,3,2)
        h.put(h.v['TEAMTBL']+4*4,1)
        self.assertEqual(self.tick(h,1),[])

    def test_new_unit_in_reused_slot_has_fresh_timers(self):
        h=self.prepare({'Siege tower':{'interval':100}})
        h.unit(1,58); h.unit(2,22,2,x=44)
        self.assertEqual(len(self.tick(h,1)),1)
        self.assertEqual(self.tick(h,1),[])
        h.unit(1,58,uid=99)
        self.assertEqual(len(self.tick(h,1)),1)

    def test_no_native_additional_shots_with_interval(self):
        h=self.prepare({'Catapult':{'interval':100}}); h.unit(1,39)
        self.assertEqual(self.fire(h,1),[])
        self.assertEqual(h.get(h.v['FORCEDT']+39*4),2)

    def test_scratch_cannot_overlap_candidates(self):
        h=self.prepare({'Catapult':{'count':3}})
        for key,address in h.v.items():
            if key.startswith('S_') and key!='S_CANDS': self.assertLess(address+3,h.v['S_CANDS'],key)

    def test_animation_wait_does_not_consume_queued_projectiles(self):
        h=self.prepare({'Siege tower':{'interval':100,'count':3,'stagger_max':1,
            'sync_to_animation':True,'sync_max_wait':3}})
        h.unit(1,58); h.unit(2,22,2,x=44)
        counts=[len(self.tick(h,1)) for _ in range(15)]
        self.assertEqual(sum(counts),3,counts)

    def test_no_target_retry_restores_unit_fields(self):
        h=self.prepare({'Siege tower':{'interval':1}}); a=h.unit(1,58)
        h.put(a+0x39c,8,2); h.put(a+0xa0,777)
        before=bytes(h.uc.mem_read(a,0x490))
        self.assertEqual(self.tick(h,1),[])
        self.assertEqual(bytes(h.uc.mem_read(a,0x490)),before)

    def test_only_sent_engineers_do_not_enable_fire(self):
        h=self.prepare({'Siege tower':{'interval':1,'require_manned':2}})
        a=h.unit(1,58); h.unit(2,22,2,x=44); h.put(a+0x3b6,2,2)
        h.put(a+0x314,123,2); h.put(a+0x316,124,2)
        self.assertEqual(self.tick(h,1),[])
        h.put(a+0x3b4,2,2)
        self.assertEqual(len(self.tick(h,1)),1)

    def test_scan_stays_within_each_executable_unit_array(self):
        for extreme,limit in [(False,2500),(True,10000)]:
            h=self.prepare({'Siege tower':{'interval':1}},extreme); h.unit(1,58)
            h.unit(limit,22,2,x=44)  # plausible bytes just outside the actual array
            self.assertEqual(h.v['MAXUNITS'],limit)
            self.assertEqual(self.tick(h,1),[])

    def test_mangonel_count_replaces_native_seven_projectile_volley(self):
        for count in [1,4]:
            h=self.prepare({'Mangonel':{'count':count}}); h.unit(1,41)
            self.tick(h,1)
            shots=sum((self.fire(h,1,4) for _ in range(7)),[])
            self.assertEqual(len(shots),count)
            self.tick(h,1)
            self.assertEqual(len(self.fire(h,1,4)),count)

    def test_explicit_rock_remap_overrides_native_cow_flag_and_restores_it(self):
        h=self.prepare({'Catapult':{'projectile':'trebuchet_rock'}}); a=h.unit(1,39)
        h.put(a+0x3b0,1,2)
        self.assertEqual(self.fire(h,1)[0][9],3)
        self.assertEqual(h.get(a+0x3b0,2),1)

    def test_count_alone_preserves_native_cow_flag(self):
        h=self.prepare({'Catapult':{'count':2}}); a=h.unit(1,39)
        h.put(a+0x3b0,1,2)
        self.assertTrue(all(s[9]==23 for s in self.fire(h,1)))

    def test_movement_can_hold_fire_without_marking_new_stationary_unit_moving(self):
        h=self.prepare({'Siege tower':{'interval':1,'interval_moving':0}})
        a=h.unit(1,58); h.unit(2,22,2,x=44)
        self.assertEqual(len(self.tick(h,1)),1)
        h.put(a+0xb6,321,2)
        self.assertEqual(self.tick(h,1),[])
        for _ in range(19): self.assertEqual(self.tick(h,1),[])
        self.assertEqual(len(self.tick(h,1)),1)

    def test_ai_only_preserves_human_native_fire(self):
        h=self.prepare({'Catapult':{'interval':1,'ai_only':True}}); h.unit(1,39)
        self.assertEqual(len(self.fire(h,1)),1)
        h.put(h.v['PLAYERAIC']+0x39f4,1)
        self.assertEqual(self.fire(h,1),[])

    def test_cluster_candidates_survive_scratch_and_random_volley_restores_target(self):
        h=self.prepare({'Siege tower':{'interval':1,'count':16,'targets':['cluster'],
            'density_min':3,'random_targets':True}})
        a=h.unit(1,58)
        for id in range(2,8): h.unit(id,22,2,x=44+id%2)
        h.put(a+0x344,123,2); h.put(a+0xa0,456)
        shots=self.tick(h,1)
        self.assertEqual(len(shots),16)
        self.assertGreater(len(set(s[10] for s in shots)),1)
        self.assertTrue(all(2<=s[10]<8 for s in shots))
        self.assertEqual(h.get(a+0x344,2),123); self.assertEqual(h.get(a+0xa0),456)

    def test_building_target_calls_native_acquisition_and_restores_orders(self):
        for extreme in [False,True]:
            h=self.prepare({'Siege tower':{'interval':1,'targets':['buildings']}},extreme)
            a=h.unit(1,58); b=h.v['BLDBASE']+0x32c
            for off,v,size in [(0xd0,1,2),(0xd2,1,2),(0xd6,2,2),(0xd8,77,4),
                              (0xee,44,2),(0xf0,40,2),(0xf8,2,4)]: h.put(b+off,v,size)
            before=bytes(h.uc.mem_read(a,0x490))
            shots=self.tick(h,1)
            self.assertEqual(len(shots),1)
            self.assertEqual(shots[0][10],0xffffffff)
            self.assertEqual(bytes(h.uc.mem_read(a,0x490)),before)

    def test_attached_detection_requires_correct_type_and_uid(self):
        h=self.prepare({'Siege tower':{'interval':1}}); a=h.unit(1,58)
        b=h.v['BLDBASE']+0x32c
        h.put(a+0x338,1,2); h.put(a+0x368,123)
        h.put(b+0xd0,1,2); h.put(b+0xd2,69,2); h.put(b+0xd8,999)
        self.assertEqual(h.call(h.v['CHECKATTACHED'],[1]),0)
        h.put(b+0xd8,123)
        self.assertEqual(h.call(h.v['CHECKATTACHED'],[1]),1)
        h.put(b+0xd2,1,2)
        self.assertEqual(h.call(h.v['CHECKATTACHED'],[1]),0)

    def state_handle(self,h):
        return h.lua.execute(b"local files={}; return {files=files,put=function(self,n,v) files[n]=v end,get=function(self,n) return files[n] end,exists=function(self,n) return files[n]~=nil end}")

    def test_saved_continuation_reproduces_staggered_scattered_shots(self):
        h=self.prepare({'Siege tower':{'interval':13,'count':4,'stagger_max':3,'inaccuracy_tiles':1}})
        h.unit(1,58); h.unit(2,22,2,x=44)
        # Valid flat map row offsets for the scatter height lookup.
        for y in range(400): h.put(h.v['TILEROWS']+12*y,400*y)
        for _ in range(5): self.tick(h,1)
        handle=self.state_handle(h); state=h.sections[b'projectileModifier']
        state.serialize(state,handle)
        first=[self.tick(h,1) for _ in range(30)]
        state.deserialize(state,handle)
        second=[self.tick(h,1) for _ in range(30)]
        self.assertEqual(first,second)
        self.assertGreater(sum(map(len,first)),0)

    def test_new_world_reset_and_malformed_state_is_atomic(self):
        h=self.prepare({'Siege tower':{'interval':4}}); h.unit(1,58); h.unit(2,22,2,x=44)
        self.tick(h,1)
        state=h.sections[b'projectileModifier']; handle=self.state_handle(h)
        state.serialize(state,handle)
        original=h.get(h.v['COOLDOWNT']+4)
        handle[b'files'][b'pending.bin']=b'bad'
        with self.assertRaises(Exception): state.deserialize(state,handle)
        self.assertEqual(h.get(h.v['COOLDOWNT']+4),original)
        state.initialize(state)
        self.assertEqual(h.get(h.v['COOLDOWNT']+4),0)
        self.assertEqual(h.get(h.v['SEED']),0x1d872b41)

class ConfigTests(unittest.TestCase):
    def test_inactive_module_does_not_scan_allocate_or_patch(self):
        h=Harness(); before=h.cursor
        h.module.enable(h.module,h.config({}))
        self.assertEqual(h.scans,[]); self.assertEqual(h.cursor,before); self.assertEqual(h.writes,[])

    def test_invalid_config_never_patches(self):
        cases=[{'Cataplut':{'count':2}}, {'Catapult':{'count':0}}, {'Catapult':{'count':65}},
            {'Catapult':{'count':1.5}}, {'Catapult':{'count':'3'}}, {'Catapult':{'count':float('nan')}},
            {'Catapult':{'projectile':99}}, {'Catapult':{'interval_moving':3}},
            {'Catapult':{'interval':5,'stagger_min':4,'stagger_max':2}},
            {'Catapult':{'spread':2,'spread_tiles':2}}, {'Catapult':{'targets':['units','units']}},
            {'Catapult':{'suppress_default':'false'}}, {'Catapult':False}]
        h=Harness()
        for cfg in cases:
            with self.subTest(config=cfg), self.assertRaises(Exception): h.enable(cfg)
            self.assertEqual(h.scans,[]); self.assertEqual(h.writes,[])

    def test_disabled_gui_controls_preserve_file_and_enabled_override(self):
        h=Harness()
        c=h.lua.execute(b"return (require('configuration'))")
        value=c.merge(h.config({'units':{'Catapult':{'count':3,'spread':8}}}),
            h.config({'catapult':{'projectile':'inherit','count':{'enabled':False,'sliderValue':10},
            'spread_tiles':{'enabled':True,'sliderValue':2}}}))
        self.assertEqual(value[b'units'][b'Catapult'][b'count'],3)
        self.assertIsNone(value[b'units'][b'Catapult'][b'spread'])
        self.assertEqual(value[b'units'][b'Catapult'][b'spread_tiles'],2)

    def test_second_enable_rejected_without_second_patch(self):
        h=Harness(); h.enable({'Catapult':{'count':2}}); writes=list(h.writes)
        with self.assertRaises(Exception): h.enable({'Catapult':{'count':3}})
        self.assertEqual(h.writes,writes)

    def test_assembler_failure_does_not_patch_entrypoints(self):
        h=Harness()
        def fail(*args): raise RuntimeError('simulated assembler failure')
        h.lua.globals().core.allocateAssembly=fail
        with self.assertRaises(Exception): h.enable({'Catapult':{'count':3}})
        self.assertEqual(h.writes,[])

    def test_gui_defaults_are_inert_and_every_control_is_understood(self):
        options=yaml.safe_load((ROOT/'options.yml').read_text(encoding='utf-8'))
        h=Harness(); config={}
        def visit(node):
            if 'url' in node:
                parts=node['url'].split('.')[1:]; dest=config
                for key in parts[:-1]: dest=dest.setdefault(key,{})
                dest[parts[-1]]=node['contents']['value']
            for child in node.get('children',[]): visit(child)
        for option in options['options']: visit(option)
        h.module.enable(h.module,h.config(config))
        self.assertEqual(h.writes,[]); self.assertEqual(h.scans,[])
        self.assertEqual(len(config['customizations']),77)

    def test_every_gui_string_is_localized_and_categories_match_legacy(self):
        options=(ROOT/'options.yml').read_text(encoding='utf-8')
        keys=set(re.findall(r'\{\{([^}]+)\}\}',options))
        languages=yaml.safe_load((ROOT.parent/'UCP3-GUI/resources/lang/languages.yaml').read_text(encoding='utf-8'))
        self.assertEqual(set(languages),{p.stem for p in (ROOT/'locale').glob('*.yml')})
        for lang in languages:
            locale=yaml.safe_load((ROOT/'locale'/f'{lang}.yml').read_text(encoding='utf-8'))
            self.assertEqual(keys,set(locale))
            self.assertTrue(all(isinstance(v,str) and v.strip() for v in locale.values()))
            self.assertFalse(any('\ufffd' in v or '{{' in v for v in locale.values()))
            self.assertTrue((ROOT/'locale'/f'description-{lang}.md').is_file())
            legacy_path=ROOT.parent/'extension-ucp2-legacy'/'locale'/f'{lang}.yml'
            legacy=yaml.safe_load(legacy_path.read_text(encoding='utf-8')) if legacy_path.exists() else {}
            self.assertEqual(locale['balance_changes'],legacy.get('balance_changes','Balance Changes'))

    def test_compact_layout_preserves_all_units_and_stock_views(self):
        options=yaml.safe_load((ROOT/'options.yml').read_text(encoding='utf-8'))['options']
        self.assertEqual(len(options),1)
        self.assertEqual(options[0]['category'],['{{balance_changes}}'])
        families=options[0]['children'][1:]
        self.assertEqual([x['name'] for x in families],['projectile_'+x for x in ['siege','european','arabian','civilian','wildlife']])
        units=[u for f in families for u in f['children']]
        self.assertEqual(len({u['name'] for u in units}),77)
        self.assertTrue(all(6<=len(u['children'])<=7 for u in units))
        def visit(node):
            self.assertIn(node['display'],['GroupBox','UCP2Slider','Choice','FileInput'])
            if node['display']=='GroupBox': self.assertEqual(node['accordion'],{'enabled':True})
            for child in node.get('children',[]): visit(child)
        visit(options[0])

    def test_editor_schema_accepts_presets_and_rejects_common_mistakes(self):
        import json
        from jsonschema import Draft202012Validator
        schema=json.loads((ROOT/'projectile-config.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema)
        for name in ['example-projectiles.yml','all-settings-reference.yml']:
            validator.validate(yaml.safe_load((ROOT/name).read_text(encoding='utf-8')))
        for unit in ['Catapult','Siege tower']:
            for field,value in [('count',65),('interval_moving',5),('projectile',99),('typo',True),('targets',['units','units'])]:
                self.assertFalse(validator.is_valid({'units':{unit:{field:value}}}))
        self.assertFalse(validator.is_valid({'units':{'Cataplut':{'count':2}}}))
        self.assertFalse(validator.is_valid({'units':{'Catapult':{'spread':1,'spread_tiles':1}}}))
        self.assertTrue(validator.is_valid({'units':{'Siege tower':{'interval':40,'require_manned':True,'preload':False}}}))

    def test_advanced_preset_and_old_gui_overrides_remain_compatible(self):
        h=Harness(); c=h.lua.execute(b"return (require('configuration'))")
        value=c.merge(h.config({'units':{'Siege tower':{'interval':40,'interval_moving':0,
            'preload':True,'sync_to_animation':True,'stagger_max':3}}}),
            h.config({'siege_tower':{'projectile':'crossbow_bolt','count':{'enabled':True,'sliderValue':3},
                'interval':{'enabled':False,'sliderValue':100},'preload':'no'}}))
        tower=value[b'units'][b'Siege tower']
        self.assertEqual(tower[b'interval'],40)
        self.assertEqual(tower[b'interval_moving'],0)
        self.assertEqual(tower[b'count'],3)
        self.assertFalse(tower[b'preload'])
        self.assertTrue(tower[b'sync_to_animation'])

    def test_shipped_yaml_presets_validate(self):
        h=Harness(); config=h.lua.execute(b"return (require('configuration'))")
        for path in ROOT.glob('*projectiles.yml'):
            config.validate(h.config(yaml.safe_load(path.read_text(encoding='utf-8'))))
        config.validate(h.config(yaml.safe_load((ROOT/'all-settings-reference.yml').read_text(encoding='utf-8'))))

if __name__ == '__main__': unittest.main()

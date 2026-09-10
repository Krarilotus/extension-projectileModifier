import unittest
import yaml
import re
from pathlib import Path
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

    def test_all_unit_types_create_every_supported_projectile_both_executables(self):
        # Execute the real entity allocator, projectile initialization, velocity
        # setup and first update. Graphics remain unrendered in this emulator.
        for extreme in [False,True]:
            h=Harness(extreme)
            constants=h.lua.execute(b"return (require('constants'))")
            names={i:name.decode() for i,name in constants.unit_names.items()}
            h.enable({name:{'count':1} for name in names.values()})
            h.v={key:value for _,_,values in h.blobs.values() for key,value in values.items()}
            self.assertEqual(h.get(h.v['FIREPROJ']+0x415,1),0xb9)
            entity_state=h.get(h.v['FIREPROJ']+0x416)
            # Valid flat terrain in a small area; map validity base is taken from
            # the original allocator's bounds check (same layout on both EXEs).
            original=bytes(h.uc.mem_read(h.spawner,0x500))
            import struct
            pattern=b'\x80\xbc\x01'
            offset=original.index(pattern)
            validity=struct.unpack_from('<I',original,offset+3)[0]
            for y in range(35,50):
                h.put(h.v['TILEROWS']+12*y,400*y)
                h.uc.mem_write(validity+400*y+35,b'\x01'*15)
            normalized={24:1,25:7,35:33,36:34,37:20,91:1,92:1}
            for kind,name in names.items():
                for projectile in constants.projectile_names.values():
                    with self.subTest(extreme=extreme,unit=name,projectile=projectile):
                        h.unit(1,kind)
                        h.put(h.v['NATIVESEENT']+4,0)
                        h.put(h.v['REMAPT']+kind*4,projectile)
                        args=self.fire(h,1)[0]
                        self.assertEqual(args[9],projectile)
                        h.put(entity_state+8,25)
                        entity=entity_state+20+25*232
                        h.uc.mem_write(entity,b'\0'*232)
                        result=h.call(h.spawner,args,{r.UC_X86_REG_ECX:entity_state})
                        self.assertEqual(result,25)
                        self.assertGreater(h.get(entity+0x28,2),0)
                        self.assertEqual(h.get(entity+0x2a,2),normalized.get(projectile,projectile))
                        self.assertGreater(h.get(entity+6,2),0) # Native projectile GM selection exists.

    def test_unconfigured_shot_passes_through(self):
        h=self.prepare({'Catapult':{'count':3}}); h.unit(1,22)
        shots=self.fire(h,1,1)
        self.assertEqual(len(shots),1); self.assertEqual(shots[0][9],1)

    def prepare_native_aim(self,h,id,x=352,y=320,z=0):
        a=h.base+id*0x490
        for offset,value in [(0xbe,x),(0xc0,y),(0xc2,z)]: h.put(a+offset,value,2)
        # Run the real ground scatter AND height-dependent scatter stages used
        # by catapult/trebuchet/mangonel just before firing, including their calls.
        address=h.scan(b'8B 44 24 08 55 56 33 ED 83 F8 FF 57')
        h.call(address,[id,0xffffffff,200],{r.UC_X86_REG_ECX:h.v['UNITSTATE']})
        self.assertEqual(h.uc.reg_read(r.UC_X86_REG_ESP),0x53f0010)
        return tuple(h.get(a+offset,2) for offset in [0xbe,0xc0,0xc2])

    def test_explicit_zero_removes_both_native_accuracy_stages(self):
        for extreme in [False,True]:
            h=self.prepare({name:{'inaccuracy_tiles':0} for name in
                            ['Catapult','Trebuchet','Mangonel','European archer']},extreme)
            for kind in [39,40,41,22]:
                for height in [0,80]:
                    with self.subTest(extreme=extreme,kind=kind,height=height):
                        a=h.unit(1,kind)
                        h.put(a+0xba,height,2)
                        for _ in range(8):
                            self.assertEqual(self.prepare_native_aim(h,1),(352,320,0))
                        # Zero does not consume the module RNG either.
                        seed=h.get(h.v['SEED'])
                        self.assertEqual(self.fire(h,1)[0][6:9],(352,320,30))
                        self.assertEqual(h.get(h.v['SEED']),seed)

    def test_accuracy_omitted_and_native_cow_orders_retain_original_scatter(self):
        for extreme in [False,True]:
            baseline=self.prepare({'Catapult':{'count':1}},extreme)
            changed=self.prepare({'Catapult':{'inaccuracy_tiles':0}},extreme)
            for cow in [False,True]:
                for h in [baseline,changed]:
                    a=h.unit(1,39); h.put(a+0x3b0,int(cow),2)
                before=self.prepare_native_aim(baseline,1)
                after=self.prepare_native_aim(changed,1)
                self.assertNotEqual(before,(352,320,0))
                if cow: self.assertEqual(before,after)
                else: self.assertEqual(after,(352,320,0))

    def test_inaccuracy_tiles_is_a_radius_and_matches_micro_units(self):
        for extreme in [False,True]:
            for tiles in [1,2,100]:
                sequences=[]
                for key,value in [('inaccuracy_tiles',tiles),('inaccuracy',tiles*8)]:
                    h=self.prepare({'Catapult':{key:value,'count':64}},extreme)
                    h.unit(1,39)
                    self.assertEqual(self.prepare_native_aim(h,1),(352,320,0))
                    shots=[]
                    h.call(h.v['FIREPROJ'],[1,2,1600,1600,0],
                           {r.UC_X86_REG_ECX:h.v['UNITSTATE']},
                           callbacks={h.spawner:self.spawn_callback(shots)})
                    self.assertEqual(len(shots),64)
                    offsets=[(s[6]-1600,s[7]-1600) for s in shots]
                    self.assertTrue(all(x*x+y*y <= (tiles*8)**2 for x,y in offsets))
                    self.assertTrue(any(x or y for x,y in offsets))
                    sequences.append(offsets)
                self.assertEqual(*sequences)

    def test_accuracy_override_follows_fortification_and_ai_scope(self):
        for extreme in [False,True]:
            h=self.prepare({'Catapult':{'on_fortification':{'inaccuracy_tiles':0}},
                            'Trebuchet':{'inaccuracy_tiles':0,'ai_only':True}},extreme)
            a=h.unit(1,39)
            h.put(h.v['TILEROWS']+40*12,400*40)
            h.put(h.v['TILEFLAGS']+(400*40+40)*4,0x100)
            self.assertNotEqual(self.prepare_native_aim(h,1),(352,320,0))
            h.put(a+0xbc,80,2)
            self.assertEqual(self.prepare_native_aim(h,1),(352,320,0))
            h.put(a+0xbc,0,2)
            self.assertNotEqual(self.prepare_native_aim(h,1),(352,320,0))
            h.unit(2,40,owner=1)
            # Same AI ownership table as the native firing gate.
            h.put(h.v['PLAYERAIC']+0x39f4,0)
            self.assertNotEqual(self.prepare_native_aim(h,2),(352,320,0))
            h.put(h.v['PLAYERAIC']+0x39f4,1)
            self.assertEqual(self.prepare_native_aim(h,2),(352,320,0))

    def test_native_accuracy_one_supports_eighth_tile_steps(self):
        for extreme in [False,True]:
            h=self.prepare({'Catapult':{'inaccuracy':1,'count':64}},extreme)
            h.unit(1,39)
            self.assertEqual(self.prepare_native_aim(h,1),(352,320,0))
            offsets={(s[6]-352,s[7]-320) for s in self.fire(h,1)}
            # Integer points in a radius of one micro unit (one eighth tile).
            self.assertEqual(offsets,{(0,0),(-1,0),(1,0),(0,-1),(0,1)})

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
        self.assertLessEqual(h.v['ORDERT']+h.v['MAXPROFILES']*4,h.v['RANGET'])
        for key,address in h.v.items():
            if key.startswith('S_') and key!='S_CANDS': self.assertLess(address+3,h.v['S_CANDS'],key)

    def test_fortification_override_requires_structure_height_and_native_tile_flags(self):
        for extreme in [False,True]:
            h=self.prepare({'European archer':{'projectile':'arrow','count':1,
                'on_fortification':{'projectile':'crossbow_bolt','count':2}}},extreme)
            a=h.unit(1,22)
            h.put(h.v['TILEROWS']+40*12,400*40)
            tile=400*40+40
            for height,flags,expected in [(0,0,[1]),(30,0,[1]),(0,0x100,[1]),
                                           (30,0x100,[7,7]),(30,0x10000000,[7,7]),(0,0,[1])]:
                h.put(h.v['NATIVESEENT']+4,0)
                h.put(a+0xbc,height,2); h.put(h.v['TILEFLAGS']+tile*4,flags)
                self.assertEqual([s[9] for s in self.fire(h,1,1)],expected)

    def test_fortification_only_automatic_fire_cancels_queued_shots_on_exit(self):
        h=self.prepare({'European spearman':{'on_fortification':{
            'projectile':'arrow','interval_standing':4,'count':3,'stagger_max':1}}})
        a=h.unit(1,24); h.unit(2,22,2,x=44)
        h.put(h.v['TILEROWS']+40*12,400*40)
        h.put(h.v['TILEFLAGS']+(400*40+40)*4,0x100)
        self.assertEqual(self.tick(h,1),[])
        h.put(a+0xbc,30,2)
        self.assertEqual(len(self.tick(h,1)),1)
        self.assertEqual(h.get(h.v['PENDINGT']+4),2)
        h.put(a+0xbc,0,2)
        self.assertEqual(self.tick(h,1),[])
        self.assertEqual(h.get(h.v['PENDINGT']+4),0)
        self.assertGreater(h.get(h.v['COOLDOWNT']+4),0)

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

    def test_regular_rock_remap_preserves_native_cow_ammunition(self):
        h=self.prepare({'Catapult':{'projectile':'trebuchet_rock'}}); a=h.unit(1,39)
        h.put(a+0x3b0,1,2)
        self.assertEqual(self.fire(h,1)[0][9],23)
        self.assertEqual(h.get(a+0x3b0,2),1)

    def test_count_alone_preserves_native_cow_flag(self):
        h=self.prepare({'Catapult':{'count':2}}); a=h.unit(1,39)
        h.put(a+0x3b0,1,2)
        shots=self.fire(h,1)
        self.assertEqual(len(shots),1)
        self.assertEqual(shots[0][9],23)

    def test_cow_and_regular_projectile_settings_are_independent_both_executables(self):
        for extreme in [False,True]:
            h=self.prepare({name:{'projectile':'mangonel_pebble','count':3,
                                  'cow_projectile':'trebuchet_rock','cow_count':2}
                            for name in ['Catapult','Trebuchet']},extreme)
            for kind,mode in [(39,2),(40,3)]:
                a=h.unit(1,kind)
                for cow,projectile,count in [(0,4,3),(1,3,2)]:
                    h.put(h.v['NATIVESEENT']+4,0); h.put(a+0x3b0,cow,2)
                    shots=self.fire(h,1,mode)
                    self.assertEqual([s[9] for s in shots],[projectile]*count)
                    self.assertEqual(h.get(a+0x3b0,2),cow)

    def test_native_cow_orders_survive_regular_automatic_fire_suppression(self):
        h=self.prepare({'Catapult':{'interval':100,'projectile':'mangonel_pebble','count':3}})
        a=h.unit(1,39)
        self.assertEqual(self.fire(h,1),[])
        h.put(a+0x3b0,1,2)
        self.assertEqual([s[9] for s in self.fire(h,1)],[23])

    def test_ai_cow_volley_uses_separate_ammunition_and_count(self):
        h=self.prepare({'Catapult':{'interval':30,'projectile':'mangonel_pebble','count':3,
                                   'ai_cow_vs_units':True,'cow_projectile':'arrow','cow_count':2,
                                   'stagger_max':1}})
        h.unit(1,39); h.unit(2,22,2,x=44)
        h.put(h.v['PLAYERAIC']+0x39f4,1); h.put(h.v['AICCOW']+0x2a4,1)
        shots=sum((self.tick(h,1) for _ in range(5)),[])
        self.assertEqual([s[9] for s in shots],[1,1])

    def test_explicit_cows_use_native_siege_launch_metadata_both_executables(self):
        for extreme in [False,True]:
            h=self.prepare({'Catapult':{'count':1},'Trebuchet':{'count':1}},extreme)
            for kind,mode in [(39,2),(40,3)]:
                h.put(h.v['NATIVESEENT']+4,0)
                a=h.unit(1,kind); h.put(a+0x344,2,2); h.put(a+0x3b0,1,2)
                native=self.fire(h,1,mode)
                h.put(h.v['NATIVESEENT']+4,0)
                h.put(h.v['REMAPT']+kind*4,23); h.put(a+0x3b0,0,2)
                explicit=self.fire(h,1,mode)
                self.assertEqual(explicit,native)
                self.assertEqual(explicit[0][9],23)
                self.assertEqual(explicit[0][10],0)
                self.assertEqual(h.get(a+0x3b0,2),0)

    def test_movement_can_hold_fire_without_marking_new_stationary_unit_moving(self):
        h=self.prepare({'Siege tower':{'interval':1,'interval_moving':0}})
        a=h.unit(1,58); h.unit(2,22,2,x=44)
        self.assertEqual(len(self.tick(h,1)),1)
        h.put(a+0xb6,321,2)
        self.assertEqual(self.tick(h,1),[])
        for _ in range(19): self.assertEqual(self.tick(h,1),[])
        self.assertEqual(len(self.tick(h,1)),1)

    def test_stance_intervals_independently_enable_fire_both_executables(self):
        cases = [
            ({'interval_moving': 3}, (0, 3, 0)),
            ({'interval_standing': 4}, (4, 0, 4)),
            ({'attached_interval': 2}, (0, 0, 2)),
            ({'interval_moving': 3, 'interval_standing': 4, 'attached_interval': 2}, (4, 3, 2)),
            ({'interval': 5, 'interval_moving': 0, 'attached_interval': 2}, (5, 0, 2)),
        ]
        for extreme in [False, True]:
            for settings, rates in cases:
                with self.subTest(extreme=extreme, settings=settings):
                    h=self.prepare({'Siege tower': settings}, extreme)
                    a=h.unit(1,58); h.unit(2,22,2,x=44)
                    b=h.v['BLDBASE']+0x32c
                    for state, rate in zip(['standing', 'moving', 'docked'], rates):
                        h.put(h.v['COOLDOWNT']+4,0)
                        h.put(h.v['MOVECDT']+4,20 if state=='moving' else 0)
                        h.put(a+0x338,1 if state=='docked' else 0,2)
                        h.put(a+0x368,123)
                        h.put(b+0xd0,1,2); h.put(b+0xd2,69,2); h.put(b+0xd8,123)
                        shots=[len(self.tick(h,1)) for _ in range(rate+1 if rate else 6)]
                        expected=[1]+[0]*(rate-1)+[1] if rate else [0]*6
                        self.assertEqual(shots,expected,(settings,state))
                    self.assertEqual(self.fire(h,1),[]) # Automatic fire suppresses native shots.

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
            {'Catapult':{'projectile':99}}, {'Catapult':{'interval_moving':-1}},
            {'Catapult':{'stagger_max':3}},
            {'Catapult':{'interval':5,'stagger_min':4,'stagger_max':2}},
            {'Catapult':{'spread':2,'spread_tiles':2}}, {'Catapult':{'targets':['units','units']}},
            {'Catapult':{'suppress_default':'false'}}, {'Catapult':False}]
        h=Harness()
        for cfg in cases:
            with self.subTest(config=cfg), self.assertRaises(Exception): h.enable(cfg)
            self.assertEqual(h.scans,[]); self.assertEqual(h.writes,[])

    def test_old_hidden_overrides_and_unresolved_qualifiers_fail_before_patching(self):
        for config in [{'customizations':{}},{'units':{}},
                       {'projectile_config_file_selector':{'required-value':'file.yml'}},
                       {'projectile_config_file_selector':False}]:
            h=Harness()
            with self.assertRaises(Exception): h.module.enable(h.module,h.config(config))
            self.assertEqual(h.scans,[]); self.assertEqual(h.writes,[])

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
        self.assertEqual(config,{'projectile_config_file_selector':''})

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

    def test_only_one_standard_file_option_is_exposed(self):
        options=yaml.safe_load((ROOT/'options.yml').read_text(encoding='utf-8'))['options']
        self.assertEqual(len(options),1)
        self.assertEqual(options[0]['category'],['{{balance_changes}}'])
        self.assertEqual(options[0]['display'],'FileInput')
        self.assertNotIn('children',options[0])
        self.assertEqual(options[0]['contents']['value'],'')

    def test_editor_schema_accepts_presets_and_rejects_common_mistakes(self):
        import json
        from jsonschema import Draft202012Validator
        schema=json.loads((ROOT/'projectile-config.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema)
        for name in ['example-projectiles.yml','all-settings-reference.yml','vanilla-projectiles.yml']:
            validator.validate(yaml.safe_load((ROOT/name).read_text(encoding='utf-8')))
        for unit in ['Catapult','Siege tower']:
            for field,value in [('count',65),('interval_moving',-1),('stagger_max',3),('projectile',99),('typo',True),('targets',['units','units'])]:
                self.assertFalse(validator.is_valid({'units':{unit:{field:value}}}))
        self.assertFalse(validator.is_valid({'units':{'Cataplut':{'count':2}}}))
        self.assertFalse(validator.is_valid({'units':{'Catapult':{'spread':1,'spread_tiles':1}}}))
        self.assertTrue(validator.is_valid({'units':{'Siege tower':{'interval':40,'require_manned':True,'preload':False}}}))

    def test_interval_schema_and_runtime_agree_on_all_fallback_combinations(self):
        import itertools, json
        from jsonschema import Draft202012Validator
        validator=Draft202012Validator(json.loads((ROOT/'projectile-config.schema.json').read_text(encoding='utf-8')))
        h=Harness(); config=h.lua.execute(b"return (require('configuration'))")
        fields=['interval','interval_moving','interval_standing','attached_interval']
        for values in itertools.product([None,5],[None,0,3],[None,0,4],[None,0,2]):
            settings={key:value for key,value in zip(fields,values) if value is not None}
            source={'units':{'Siege tower':settings}}
            with self.subTest(settings=settings):
                validator.validate(source)
                normalized=config.validate(h.config(source))[b'units'][b'Siege tower']
                if not settings:
                    self.assertIsNone(normalized)
                    continue
                self.assertGreater(normalized[b'interval'],0)
                for key in ['interval_moving','interval_standing']:
                    actual=normalized[key.encode()]
                    if actual is None: actual=normalized[b'interval']
                    self.assertEqual(actual,settings.get(key,settings.get('interval',0)))
                self.assertEqual(normalized[b'attached_interval'],settings.get('attached_interval'))
                self.assertTrue(normalized[b'suppress_default'])
                self.assertEqual(normalized[b'projectile'],1)
                # Staggering accepts every kind of automatic-fire schedule.
                settings['stagger_max']=2
                validator.validate(source); config.validate(h.config(source))
                settings['suppress_default']=False
                self.assertFalse(config.validate(h.config(source))[b'units'][b'Siege tower'][b'suppress_default'])

    def load_file(self,h,path):
        h.lua.globals().yaml.parse=lambda source:h.config(yaml.safe_load(source.decode('utf-8-sig')))
        h.module.enable(h.module,h.config({'projectile_config_file_selector':str(path)}))

    def test_vanilla_file_is_inert_and_documents_all_settings_and_units(self):
        path=ROOT/'vanilla-projectiles.yml'; text=path.read_text(encoding='utf-8')
        parsed=yaml.safe_load(text)
        self.assertEqual(len(parsed['units']),77)
        self.assertTrue(all(value=={} for value in parsed['units'].values()))
        h=Harness(); before=h.cursor
        self.load_file(h,path)
        self.assertEqual(h.scans,[]); self.assertEqual(h.writes,[]); self.assertEqual(h.cursor,before)
        c=h.lua.execute(b"return (require('configuration'))")
        for key in list(c.numbers.keys())+list(c.booleans.keys())+[b'projectile',b'targets']:
            self.assertIn('#   '+key.decode()+':',text)

    def test_real_file_loading_applies_sparse_settings_and_rejects_missing_file(self):
        import tempfile
        h=Harness()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'preset.yml'
            path.write_text('units:\n  Catapult:\n    projectile: mangonel_pebble\n    count: 3\n',encoding='utf-8')
            self.load_file(h,path)
            self.assertTrue(h.writes)
        failed=Harness()
        with self.assertRaises(Exception): self.load_file(failed,ROOT/'not-a-preset.yml')
        self.assertEqual(failed.scans,[]); self.assertEqual(failed.writes,[])

    def test_invalid_preset_file_and_ucp_wrappers_fail_before_patching(self):
        import tempfile
        for text in ['units: false\n', 'units:\n  Catapult:\n    count: 65\n',
                     'units:\n  Catapult:\n    count: {required-value: 3}\n',
                     'config-sparse: {modules: {}}\n']:
            h=Harness()
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'bad.yml'; path.write_text(text,encoding='utf-8')
                with self.assertRaises(Exception): self.load_file(h,path)
            self.assertEqual(h.scans,[]); self.assertEqual(h.writes,[])

    def test_shipped_yaml_presets_validate(self):
        h=Harness(); config=h.lua.execute(b"return (require('configuration'))")
        for path in ROOT.glob('*projectiles.yml'):
            config.validate(h.config(yaml.safe_load(path.read_text(encoding='utf-8'))))
        config.validate(h.config(yaml.safe_load((ROOT/'all-settings-reference.yml').read_text(encoding='utf-8'))))

if __name__ == '__main__': unittest.main()

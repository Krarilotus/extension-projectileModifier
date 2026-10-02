"""Native manual range admission without replacing the Mangonel scheduler."""
import unittest
import struct
import yaml
from harness import ROOT, r
import test_projectiles as native_tests
import test_manual_cluster as manual_tests
import test_cadence as cadence_tests


class MangonelRangeTests(unittest.TestCase):
    def test_explicit_range_independent_of_reload_and_projectile_on_both_families(self):
        for extreme in (False, True):
            for timing in ({}, {'interval': 400}, {'interval': 400, 'sync_to_animation': False}):
                for projectile in ('mangonel_pebble', 'firethrower_pot'):
                    h = native_tests.NativeTests().prepare({'Mangonel': dict(
                        range=3, projectile=projectile, **timing)}, extreme)
                    a = h.unit(1, 41)
                    for distance, expected in ((25, 0), (24, 1), (23, 1)):
                        with self.subTest(extreme=extreme, timing=timing, projectile=projectile, distance=distance):
                            h.unit(2, 22, owner=2)
                            h.put(h.base+2*0x490+0xb6, 320+distance, 2)
                            manual_tests.ManualClusterTests().order_unit(h, a, 2)
                            self.assertEqual(h.call(h.v['ACQUIRE'], [1],
                                {r.UC_X86_REG_ECX: h.v['UNITSTATE']}), expected)
                            self.assertEqual(h.uc.reg_read(r.UC_X86_REG_ESP), 0x53f0008)
                            self.assertEqual(h.get(a+0x39e, 2), 2)
                    if not timing:
                        self.assertNotIn('configuredAnimationHold', h.blobs)
                        self.assertEqual(h.get(h.v['NATIVECYCLET']+41*4), 0)

    def test_off_ai_only_and_inherited_profiles_preserve_native_paths(self):
        for extreme in (False, True):
            for settings, expected in (({'range':3,'strict_range':False},1),
                    ({'range':3,'ai_only':True},1), ({'count':1},1),
                    ({'range':'native','count':1},1),
                    ({'on_fortification':{'range':3}},1)):
                h = native_tests.NativeTests().prepare({'Mangonel':settings},extreme)
                a=h.unit(1,41);h.unit(2,22,owner=2,x=44)
                manual_tests.ManualClusterTests().order_unit(h,a,2)
                self.assertEqual(h.call(h.v['ACQUIRE'],[1],
                    {r.UC_X86_REG_ECX:h.v['UNITSTATE']}),expected)
                if 'on_fortification' in settings:
                    h.put(a+0xbc,40,2)
                    h.put(h.v['TILEROWS']+12*40,400*40)
                    h.put(h.v['TILEFLAGS']+(400*40+40)*4,0x100)
                    self.assertEqual(h.call(h.v['ACQUIRE'],[1],
                        {r.UC_X86_REG_ECX:h.v['UNITSTATE']}),0)

    def test_untimed_native_mangonel_keeps_seven_shots_and_completes_animation(self):
        for extreme in (False,True):
            h,a,tick=cadence_tests.CadenceTests().integrated('Mangonel',41,0x56a3f0,
                {'range':4,'inaccuracy':0},extreme,native=True)
            manual_tests.ManualClusterTests().order_unit(h,a,2)
            self.assertEqual(h.call(h.v['ACQUIRE'],[1],
                {r.UC_X86_REG_ECX:h.v['UNITSTATE']}),1)
            h.put(a+0x2c0,8,2)
            volleys=[];phases=[]
            for t in range(160):
                queued,shots=tick()
                self.assertEqual(queued,[])
                phases.append(h.get(a+0x2c0,2))
                if shots:
                    volleys.append(shots)
                    self.assertEqual(len(shots),7)
                    self.assertTrue(all(s[6:8]==(352,320) for s in shots))
            self.assertTrue(volleys)
            self.assertIn(0,phases)
            self.assertNotIn('configuredAnimationHold',h.blobs)

    def test_supplied_reconquista_boundary_and_actual_eight_pebble_flights(self):
        cfg=yaml.safe_load((ROOT/'examples/reconquista-monsterfish.yml').read_text(encoding='utf-8'))['units']['Mangonel']
        impacts=[]
        for extreme in (False,True):
            h,a,tick=cadence_tests.CadenceTests().integrated('Mangonel',41,0x56a3f0,cfg,extreme)
            h.unit(2,22,owner=2,x=70)
            manual_tests.ManualClusterTests().order_unit(h,a,2)
            h.put(h.base+2*0x490+0xb6,561,2)  # 30 tiles plus one eighth-tile.
            self.assertEqual(h.call(h.v['ACQUIRE'],[1],{r.UC_X86_REG_ECX:h.v['UNITSTATE']}),0)
            self.assertEqual(h.call(h.v['PICKTARGET'],[1,41]),0)
            h.call(h.v['RESTORETARGET'])
            h.put(h.base+2*0x490+0xb6,560,2)
            self.assertEqual(h.call(h.v['ACQUIRE'],[1],{r.UC_X86_REG_ECX:h.v['UNITSTATE']}),1)
            state=h.get(h.v['FIREPROJ']+0x416)
            raw=bytes(h.uc.mem_read(h.spawner,0x500))
            validity=struct.unpack_from('<I',raw,raw.index(b'\x80\xbc\x01')+3)[0]
            h.uc.mem_write(validity,b'\1'*160000)
            for y in range(1,399):h.put(h.v['TILEROWS']+12*y,400*y)
            mover=h.scan(b'83 EC 10 53 55 56 57 8B 7C 24 24 8B C7 69 C0 E8 00 00 00 8B D9')
            for t in range(200):
                queued,shots=tick()
                self.assertEqual(queued,[])
                if shots:break
            self.assertEqual(len(shots),8)
            self.assertEqual(shots[0][6:8],(560,320))
            result=[]
            for shot in shots:
                self.assertEqual(shot[9],4)
                self.assertLessEqual(abs(shot[6]-560),48)
                self.assertLessEqual(abs(shot[7]-320),48)
                h.put(state+8,25)
                entity=state+20+25*232
                h.uc.mem_write(entity,b'\0'*232)
                self.assertEqual(h.call(h.spawner,shot,{r.UC_X86_REG_ECX:state}),25)
                for step in range(200):
                    h.call(mover,[25],{r.UC_X86_REG_ECX:state})
                    if h.get(entity+0x6c,2):break
                self.assertLess(step,199)
                x,y=h.get(entity+0x38,2),h.get(entity+0x3a,2)
                self.assertLessEqual(abs(x-shot[6]),8)
                self.assertLessEqual(abs(y-shot[7]),8)
                result.append((shot[6:8],x,y,h.get(entity+0x96,2)))
            impacts.append(result)
            self.assertTrue(any(x>560 for _,x,_,_ in result),'configured spread can land beyond the selected-target radius')
            self.assertGreater(len({speed for _,_,_,speed in result}),1,'native solver adapts speed for each scattered aim')
        self.assertEqual(impacts[0],impacts[1])


if __name__ == '__main__': unittest.main()

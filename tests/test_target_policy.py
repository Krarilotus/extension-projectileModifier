"""Range and manual-only regressions against both real reference PE images."""
import unittest
from harness import r
import test_projectiles as projectile_tests
import test_infantry_cadence as infantry_tests
import test_cadence as cadence_tests
import test_mounted_cadence as mounted_tests
import test_hunter_cadence as hunter_tests


class TargetPolicyTests(unittest.TestCase):
    def test_fractional_unit_range_and_exact_boundary(self):
        for extreme in (False, True):
            for strict in (True, False):
                with self.subTest(extreme=extreme, strict=strict):
                    observer = projectile_tests.NativeTests()
                    h = observer.prepare({'Catapult': {'interval': 100, 'range': 20,
                        'projectile': 'firethrower_pot', 'sync_to_animation': False,
                        'strict_range': strict}}, extreme)
                    a = h.unit(1, 39)
                    b = h.unit(2, 22, owner=2, x=59, y=46)
                    h.put(b+0xb6, 479, 2); h.put(b+0xb8, 375, 2)
                    # Rounded distance <20, actual distance >21 tiles.
                    shots = observer.tick(h, 1)
                    self.assertEqual(len(shots), 0 if strict else 1)
                    h.put(b+0xc4, 60, 2); h.put(b+0xc6, 40, 2)
                    h.put(b+0xb6, 480, 2); h.put(b+0xb8, 320, 2)
                    self.assertEqual(h.call(h.v['PICKTARGET'], [1, 39]), 1 if strict else 0)
                    h.call(h.v['RESTORETARGET'])
                    h.put(b+0xb6, 481, 2)
                    self.assertEqual(h.call(h.v['PICKTARGET'], [1, 39]), 0)
                    h.call(h.v['RESTORETARGET'])
                    # Moving the shooter, not just the target, changes eligibility.
                    h.put(a+0xb6, 322, 2)
                    self.assertEqual(h.call(h.v['PICKTARGET'], [1, 39]), 1 if strict else 0)

    def test_building_centre_and_wall_range(self):
        for extreme in (False, True):
            for strict in (True, False):
                with self.subTest(extreme=extreme, strict=strict):
                    h = projectile_tests.NativeTests().prepare({'Catapult': {'interval': 100,
                        'range': 20, 'strict_range': strict, 'targets': ['buildings', 'walls']}}, extreme)
                    a = h.unit(1, 39); h.put(a+0x362, 100, 2)
                    b = h.v['BLDBASE']+0x32c
                    for off, value, size in [(0xd0,1,2),(0xd2,1,2),(0xd6,2,2),
                            (0xd8,77,4),(0xee,59,2),(0xf0,40,2),(0xf8,4,4)]:
                        h.put(b+off, value, size)
                    # Corner is 19 tiles away; native aim (61,42) is outside 20.
                    self.assertEqual(h.call(h.v['PICKTARGET'], [1,39]), 0 if strict else 2)
                    h.call(h.v['RESTORETARGET'])
                    h.put(b+0xee,55,2)
                    self.assertEqual(h.call(h.v['PICKTARGET'], [1,39]), 2)
                    h.call(h.v['RESTORETARGET'])
                    h.put(b+0xd0,0,2)
                    h.put(a+0xb6,327,2);h.put(a+0xb8,327,2)
                    h.put(h.v['TILEROWS']+12*34,400*34)
                    h.put(h.v['TILEFLAGS']+(400*34+21)*4,0x100)
                    self.assertEqual(h.call(h.v['PICKTARGET'], [1,39]), 0 if strict else 2)

    def test_manual_only_preserves_native_orders_and_has_no_rng_draw_on_rejection(self):
        for extreme in (False, True):
            h = projectile_tests.NativeTests().prepare({'Catapult': {'interval': 100,
                'auto_targeting': False, 'projectile': 'firethrower_pot'}}, extreme)
            a=h.unit(1,39);h.put(a+0x362,100,2);h.unit(2,22,owner=2,x=44)
            seed=h.get(h.v['SEED'])
            self.assertEqual(h.call(h.v['PICKTARGET'],[1,39]),0)
            self.assertEqual(h.get(h.v['SEED']),seed)
            h.put(a+0x39c,4,2);h.put(a+0x39e,2,2);h.put(a+0x3a0,2)
            self.assertEqual(h.call(h.v['PICKTARGET'],[1,39]),2)
            h.call(h.v['RESTORETARGET'])
            h.put(h.v['PLAYERAIC']+0x39f4,1)
            self.assertEqual(h.call(h.v['PICKTARGET'],[1,39]),0,
                'an AI order is not a human command')

    def test_native_acquisition_restriction_without_an_interval(self):
        for extreme in (False, True):
            for enabled in (False, True):
                h=projectile_tests.NativeTests().prepare({'European archer': {'auto_targeting':enabled}},extreme)
                self.assertEqual('acquirePolicy' in h.blobs,not enabled)
                a=h.unit(1,22);h.unit(2,22,owner=2,x=44)
                h.put(a+0x39c,3,2);h.put(a+0x344,2,2);h.put(a+0xa0,2)
                # Feed the existing native per-player target list, as the
                # game's preceding update does. This is not the module scan.
                site=h.scan(b'69 C9 F4 39 00 00 69 C0 ? ? ? ? 05')
                h.put(h.get(site+19)+0x39f4,1)
                h.put(h.get(site+43)+0x39f4,2,2)
                h.put(h.get(site+13)+h.get(site+8),2)
                self.assertEqual(h.call(h.v['ACQUIRE'],[1],{r.UC_X86_REG_ECX:h.v['UNITSTATE']}),int(enabled))
                h.put(a+0x39c,4,2);h.put(a+0x39e,2,2);h.put(a+0x3a0,2)
                self.assertEqual(h.call(h.v['ACQUIRE'],[1],{r.UC_X86_REG_ECX:h.v['UNITSTATE']}),1)
                self.assertEqual(h.uc.reg_read(r.UC_X86_REG_ESP),0x53f0008)

    def test_native_infantry_manual_only_stops_automatic_shots_without_retiming_manual_fire(self):
        for extreme in (False, True):
            for unit in infantry_tests.FOOT:
                with self.subTest(extreme=extreme,unit=unit[0]):
                    traces=[]
                    for enabled, manual in ((True,True),(False,True),(False,False)):
                        h,a,tick=infantry_tests.InfantryCadenceTests().prepare(unit,
                            {'count':1,'auto_targeting':enabled},extreme,native=True)
                        if manual:
                            h.put(a+0x39c,4,2);h.put(a+0x39e,2,2);h.put(a+0x3a0,2)
                        traces.append([t for t in range(160) if any(tick())])
                    self.assertTrue(traces[0])
                    self.assertEqual(traces[0],traces[1])
                    self.assertEqual(traces[2],[])

    def test_loaded_siege_manual_only_preserves_ammunition_and_native_manual_volley(self):
        for extreme in (False,True):
            for name,kind,handler in [('Catapult',39,0x568320),('Trebuchet',40,0x569410),
                    ('Mangonel',41,0x56a3f0),('Tower ballista',61,0x56ecd0),('Fire ballista',77,0x577cc0)]:
                with self.subTest(extreme=extreme,unit=name):
                    traces=[]
                    for enabled,manual in ((True,True),(False,True),(False,False)):
                        h,a,tick=cadence_tests.CadenceTests().integrated(name,kind,handler,
                            {'auto_targeting':enabled},extreme,native=True)
                        h.put(a+0x2c0,2,2)
                        if manual:
                            h.put(a+0x39c,4,2);h.put(a+0x39e,2,2);h.put(a+0x3a0,2)
                        events=[]
                        for t in range(270):
                            queued,shots=tick()
                            if queued or shots:events.append((t,len(queued)+len(shots)))
                        traces.append(events)
                        if not enabled and not manual:self.assertEqual(h.get(a+0x362,2),1000)
                    self.assertTrue(traces[0])
                    self.assertEqual(traces[0],traces[1])
                    self.assertEqual(traces[2],[])

    def test_horse_archer_and_hunter_manual_only(self):
        for extreme in (False,True):
            for cls in (mounted_tests.MountedCadenceTests,hunter_tests.HunterCadenceTests):
                with self.subTest(extreme=extreme,unit=cls.__name__):
                    h,a,tick=cls().prepare({'auto_targeting':False},extreme,native=True)
                    for _ in range(120):self.assertEqual(tick(),([],[]))

    def test_manual_only_keeps_independent_timer_mode_and_ai_only_scope(self):
        for extreme in (False,True):
            for ai_only in (False,True):
                h=projectile_tests.NativeTests().prepare({'Catapult':{'interval':10,
                    'auto_targeting':False,'sync_to_animation':False,'ai_only':ai_only}},extreme)
                a=h.unit(1,39);h.put(a+0x362,100,2);h.unit(2,22,owner=2,x=44)
                self.assertEqual(h.get(h.v['NATIVECYCLET']+39*4),0)
                h.put(a+0x39c,4,2);h.put(a+0x39e,2,2);h.put(a+0x3a0,2)
                self.assertEqual(h.call(h.v['ACQUIRE'],[1],{r.UC_X86_REG_ECX:h.v['UNITSTATE']}),1)


if __name__ == '__main__':
    unittest.main()

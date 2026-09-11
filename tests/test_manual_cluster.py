"""Cluster thresholds belong to AI; human orders retain native acquisition."""
import unittest
import test_cadence as cadence_tests
import test_projectiles as projectile_tests
from harness import r


class ManualClusterTests(unittest.TestCase):
    def order_unit(self,h,a,target):
        h.put(a+0x39c,4,2)
        h.put(a+0x39e,target,2)
        h.put(a+0x3a0,h.get(h.base+target*0x490+0x98))

    def test_manual_unit_order_for_all_twelve_native_shooters(self):
        names={6:'Hunter',22:'European archer',23:'European crossbowman',
               39:'Catapult',40:'Trebuchet',41:'Mangonel',61:'Tower ballista',
               70:'Arabian archer',72:'Arabian slinger',74:'Arabian horse archer',
               76:'Arabian firethrower',77:'Fire ballista'}
        for extreme in (False,True):
            h=projectile_tests.NativeTests().prepare({name:{'interval':700,
                'targets':'cluster','density_min':30,'inaccuracy':0} for name in names.values()},extreme)
            h.unit(2,22,owner=2,x=41)
            for kind,name in names.items():
                with self.subTest(extreme=extreme,unit=name):
                    a=h.unit(1,kind);h.put(a+0x362,100,2)
                    self.order_unit(h,a,2)
                    self.assertEqual(h.call(h.v['PICKTARGET'],[1,kind]),2)
                    self.assertEqual(h.get(a+0xbe,2),328)
                    self.assertEqual(h.get(a+0xc0,2),320)
                    h.call(h.v['RESTORETARGET'])

    def test_human_artillery_keeps_manual_target_and_configured_intervals(self):
        for extreme in (False,True):
            for name,kind,handler,interval in [('Catapult',39,0x568320,700),
                    ('Trebuchet',40,0x569410,800),('Mangonel',41,0x56a3f0,400)]:
                with self.subTest(extreme=extreme,unit=name):
                    h,a,tick=cadence_tests.CadenceTests().integrated(name,kind,handler,{
                        'interval':interval,'targets':['buildings','cluster'],
                        'density_min':30,'density_radius':10,'projectile':'mangonel_pebble',
                        'count':3,'inaccuracy':0,'spread':0,'random_targets':True},extreme)
                    h.unit(3,22,owner=2,x=46)
                    self.order_unit(h,a,3)  # farther than the automatic candidate
                    events=[]
                    for t in range(interval+270):
                        queued,shots=tick()
                        self.assertFalse(queued)
                        if shots:
                            events.append(t)
                            self.assertEqual(len(shots),3)
                            self.assertTrue(all(s[6:8]==(368,320) for s in shots),shots)
                    self.assertEqual(len(events),2,events)
                    self.assertEqual(events[1]-events[0],interval)
                    self.assertEqual(h.get(a+0x39e,2),3)
                    self.assertEqual(h.get(a+0x3a0),3)
                    if kind in (39,40):self.assertEqual(h.get(a+0x362,2),998)

    def test_ai_cluster_threshold_still_blocks_and_resumes(self):
        for extreme in (False,True):
            h,a,tick=cadence_tests.CadenceTests().integrated('Catapult',39,0x568320,{
                'interval':300,'targets':'cluster','density_min':30,'density_radius':10,
                'projectile':'mangonel_pebble','count':3},extreme)
            h.put(h.v['PLAYERAIC']+0x39f4,1)
            for i in range(2,31):h.unit(i,22,owner=2,x=44)
            self.order_unit(h,a,2)  # an AI order must not bypass its policy
            for _ in range(160):self.assertEqual(tick(),([],[]))
            self.assertEqual(h.get(a+0x362,2),1000)
            h.unit(31,22,owner=2,x=44)
            events=[]
            for t in range(600):
                queued,shots=tick()
                if queued or shots:events.append((t,len(queued)+len(shots)))
            self.assertEqual(len(events),2,events)
            self.assertEqual(events[1][0]-events[0][0],300)
            self.assertTrue(all(n==3 for _,n in events))

    def test_human_cluster_falls_back_to_units_without_manual_order(self):
        for extreme in (False,True):
            h,a,tick=cadence_tests.CadenceTests().integrated('Catapult',39,0x568320,{
                'interval':300,'targets':'cluster','density_min':30},extreme)
            events=[]
            for t in range(450):
                queued,shots=tick()
                if queued or shots:events.append(t)
            self.assertEqual(events,[99,399])

    def test_manual_building_and_ground_orders_use_native_aim(self):
        for extreme in (False,True):
            for order in (9,5,22,23):
                with self.subTest(extreme=extreme,order=order):
                    h=projectile_tests.NativeTests().prepare({'Catapult':{'interval':700,
                        'targets':'cluster','density_min':30,'inaccuracy':0}},extreme)
                    a=h.unit(1,39);h.put(a+0x362,100,2)
                    h.put(a+0x39c,order,2)
                    h.put(a+0x3e8,44,2);h.put(a+0x3ea,40,2)
                    map_site=h.scan(b'B9 ? ? ? ? 66 C7 84 37 9E 09 00 00 FF FF E8')
                    h.put(h.get(map_site+1)+0xc0+400*40+44,1,1)
                    h.put(h.v['TILEROWS']+12*40,400*40)
                    h.put(h.v['TILEFLAGS']+(400*40+44)*4,0x100)
                    if order==9:
                        b=h.v['BLDBASE']+0x32c
                        for off,v,n in [(0xd0,1,2),(0xd2,1,2),(0xd6,2,2),
                                (0xd8,77,4),(0xee,44,2),(0xf0,40,2),(0xf8,2,4)]:h.put(b+off,v,n)
                        h.put(a+0x336,1,2);h.put(a+0x3a0,77)
                    snapshot=bytes(h.uc.mem_read(a,0x490))
                    result=h.call(h.v['ACQUIRE'],[1],{r.UC_X86_REG_ECX:h.v['UNITSTATE']})
                    self.assertEqual(result,1,'fixture must contain a valid native target')
                    expected=bytes(h.uc.mem_read(a+0xbe,6))
                    h.uc.mem_write(a,snapshot)
                    selected=h.call(h.v['PICKTARGET'],[1,39])
                    self.assertEqual(selected,2 if result else 0)
                    if result:self.assertEqual(bytes(h.uc.mem_read(a+0xbe,6)),expected)
                    h.call(h.v['RESTORETARGET'])
                    for off,n in [(0x39c,2),(0x336,2),(0x3a0,4),(0x3e8,2),(0x3ea,2)]:
                        self.assertEqual(bytes(h.uc.mem_read(a+off,n)),snapshot[off:off+n])
                    h.put(h.v['RANGET']+39*4,1)
                    self.assertEqual(h.call(h.v['PICKTARGET'],[1,39]),0,
                        'native ground/building orders cannot bypass module range')

    def test_manual_unit_target_uid_is_validated(self):
        h=projectile_tests.NativeTests().prepare({'Catapult':{'interval':700,'targets':'cluster','density_min':30}})
        a=h.unit(1,39);h.put(a+0x362,100,2);h.unit(2,22,owner=2,x=44)
        self.order_unit(h,a,2)
        self.assertEqual(h.call(h.v['PICKTARGET'],[1,39]),2)
        h.call(h.v['RESTORETARGET'])
        h.put(a+0x3a0,999)
        self.assertEqual(h.call(h.v['PICKTARGET'],[1,39]),0)
        h.call(h.v['RESTORETARGET'])
        self.assertEqual(h.get(a+0x39c,2),3,'retain native cleanup of a stale manual order')
        self.assertEqual(h.call(h.v['PICKTARGET'],[1,39]),1,
            'a stale order must not leave the human shooter permanently blocked')

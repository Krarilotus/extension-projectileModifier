"""Native accepted artillery dispatch must survive consumption of its last stone."""
import unittest
from unicorn import UC_HOOK_CODE
from harness import r
import test_cadence as cadence_tests
import test_projectiles as projectile_tests


class ManualReleaseTests(unittest.TestCase):
    def prepare(self, name, kind, handler, order, extreme=False, **settings):
        config = dict(interval=300, targets='cluster', density_min=30,
                      projectile='mangonel_pebble', count=3, inaccuracy=0)
        config.update(settings)
        h,a,tick = cadence_tests.CadenceTests().integrated(name,kind,handler,config,extreme)
        h.put(h.base+2*0x490+0x3c8,0)  # no automatic target can hide a lost order
        h.put(a+0x362,1,2)
        h.put(a+0x39c,order,2)
        h.put(a+0x3e8,44,2); h.put(a+0x3ea,40,2)
        site=h.scan(b'B9 ? ? ? ? 66 C7 84 37 9E 09 00 00 FF FF E8')
        h.put(h.get(site+1)+0xc0+400*40+44,1,1)
        h.put(h.v['TILEROWS']+12*40,400*40)
        h.put(h.v['TILEFLAGS']+(400*40+44)*4,0x100)
        if order==9:
            b=h.v['BLDBASE']+0x32c
            for off,v,n in [(0xd0,1,2),(0xd2,1,2),(0xd6,2,2),
                    (0xd8,77,4),(0xee,44,2),(0xf0,40,2),(0xf8,2,4)]:h.put(b+off,v,n)
            h.put(a+0x336,1,2);h.put(a+0x3a0,77)
        elif order==4:
            h.unit(2,22,owner=2,x=44)
            h.put(a+0x39e,2,2);h.put(a+0x3a0,2)
        return h,a,tick

    def test_last_stone_fires_native_unit_ground_wall_and_building_orders(self):
        for extreme in (False,True):
            # Native aiming from facing 0 to east precedes the reload cycle.
            for name,kind,handler,release in [('Catapult',39,0x568320,117),
                                             ('Trebuchet',40,0x569410,235)]:
                for order in (4,5,9,23):
                    with self.subTest(extreme=extreme,unit=name,order=order):
                        h,a,tick=self.prepare(name,kind,handler,order,extreme)
                        dispatch=[]; late_acquisitions=[]; events=[]
                        def record_dispatch(uc,ip,size,data):
                            if h.get(h.v['REENTRY']): return
                            sp=uc.reg_read(r.UC_X86_REG_ESP)
                            dispatch.append(tuple(h.get(sp+4+i*4) for i in range(5)))
                        def record_acquire(uc,ip,size,data):
                            if h.get(a+0x362,2)==0:late_acquisitions.append(ip)
                        tokens=[h.uc.hook_add(UC_HOOK_CODE,record_dispatch,
                                    begin=h.v['FIREPROJ'],end=h.v['FIREPROJ']),
                                h.uc.hook_add(UC_HOOK_CODE,record_acquire,
                                    begin=h.v['ACQUIRE'],end=h.v['ACQUIRE'])]
                        try:
                            for t in range(release+1):
                                queued,shots=tick()
                                self.assertFalse(queued)
                                if shots:events.append((t,shots))
                        finally:
                            for token in tokens:h.uc.hook_del(token)
                        self.assertEqual([t for t,_ in events],[release])
                        self.assertEqual(len(events[0][1]),3)
                        self.assertEqual(len(dispatch),1)
                        self.assertTrue(all(s[6:9]==dispatch[0][2:5] for s in events[0][1]))
                        self.assertEqual(late_acquisitions,[], 'do not acquire after native ammunition debit')
                        self.assertEqual(h.get(a+0x362,2),0)
                        self.assertEqual(h.get(a+0x39c,2),order)

    def test_explicit_ground_order_also_wins_over_default_units_policy(self):
        for extreme in (False,True):
            h,a,tick=self.prepare('Catapult',39,0x568320,5,extreme,targets='units')
            h.unit(2,22,owner=2,x=41)
            events=[]
            for t in range(118):
                queued,shots=tick()
                if queued or shots:events.extend(queued+shots)
            self.assertEqual(len(events),3)
            self.assertTrue(all(s[6:8]==(352,320) for s in events))

    def test_last_stone_long_stagger_finishes_and_restores_across_save_load(self):
        for extreme in (False,True):
            h,a,tick=self.prepare('Catapult',39,0x568320,23,extreme,
                                 count=4,stagger_min=80,stagger_max=80)
            for _ in range(118):tick()
            self.assertEqual(h.get(a+0x362,2),0)
            handle=projectile_tests.NativeTests().state_handle(h);state=h.sections[b'projectileModifier']
            state.serialize(state,handle)
            native=bytes(h.uc.mem_read(a,0x490))
            first=[tick() for _ in range(240)]
            shots=[(i+118,q+s) for i,(q,s) in enumerate(first) if q or s]
            self.assertEqual([t for t,_ in shots],[197,277,357])
            self.assertTrue(all(s[6:8]==(352,320) for _,ss in shots for s in ss))
            self.assertEqual(h.get(a+0x362,2),0)
            h.uc.mem_write(a,native);state.deserialize(state,handle)
            self.assertEqual(first,[tick() for _ in range(240)])

"""Configured hunter animation, native minimum, work dispatch and ground targets."""
import unittest
from harness import r
import test_projectiles as projectile_tests


class HunterCadenceTests(unittest.TestCase):
    def prepare(self, config, extreme=False, native=False):
        observer=projectile_tests.NativeTests()
        h=observer.prepare({'Hunter':config},extreme)
        a=h.unit(1,6);h.unit(2,22,owner=2,x=44)
        for y in range(400):h.put(h.v['TILEROWS']+y*12,y*400)
        delta=h.v['FIREPROJ']-0x532700
        animation=(h.blobs['configuredAnimationHold'][2]['RESUME']-18
            if 'configuredAnimationHold' in h.blobs else
            h.scan(b'A1 ? ? ? ? 69 C0 90 04 00 00 01 9C 30 54 06 00 00'))
        h.put(a+0x44,2)
        if native:
            h.put(a+0x344,2,2);h.put(a+0xa0,2);h.put(a+0x2c0,10,2)
        def stub(cleanup,result=0):
            def callback(h):
                esp=h.uc.reg_read(r.UC_X86_REG_ESP)
                h.uc.reg_write(r.UC_X86_REG_EIP,h.get(esp))
                h.uc.reg_write(r.UC_X86_REG_ESP,esp+4+cleanup)
                h.uc.reg_write(r.UC_X86_REG_EAX,result)
            return callback
        def tick():
            queued=observer.tick(h,1);shots=[]
            h.put(h.v['CURUNIT'],1)
            h.call(animation,registers={r.UC_X86_REG_ESI:h.v['UNITSTATE'],
                r.UC_X86_REG_EBX:1,r.UC_X86_REG_EBP:0},stop=animation+0xa1)
            h.call(0x54f860+delta,callbacks={h.spawner:observer.spawn_callback(shots),
                0x449dc0+(0x2e0 if extreme else 0):stub(12),
                0x537880+delta:stub(4,1)})
            if native and h.get(a+0x2c0,2)==0:
                h.put(a+0x2c0,10,2);h.put(a+0x2b0,0)
            return queued,shots
        return h,a,tick

    def test_native_cycle_and_configured_intervals(self):
        for extreme in [False,True]:
            with self.subTest(extreme=extreme):
                h,a,tick=self.prepare({'inaccuracy':0},extreme,native=True)
                natural=[t for t in range(400) if tick()[1]]
                self.assertGreaterEqual(len(natural),3,natural)
                minimum=natural[1]-natural[0]
                for interval in [1,300]:
                    h,a,tick=self.prepare({'interval':interval,'count':2,
                        'projectile':'mangonel_pebble','inaccuracy':0},extreme)
                    events=[]
                    for t in range(750):
                        queued,shots=tick()
                        self.assertFalse(queued)
                        if shots:
                            events.append(t)
                            self.assertEqual([s[9] for s in shots],[4,4])
                    self.assertGreaterEqual(len(events),3,events)
                    self.assertEqual(events[0],natural[0])
                    self.assertEqual({b-a for a,b in zip(events,events[1:])},{max(interval,minimum)})

    def test_building_target_and_save_continuation(self):
        observer=projectile_tests.NativeTests()
        for extreme in [False,True]:
            h,a,tick=self.prepare({'interval':300,'targets':['buildings'],
                'count':2,'inaccuracy':0},extreme)
            b=h.v['BLDBASE']+0x32c
            for off,value,size in [(0xd0,1,2),(0xd2,1,2),(0xd6,2,2),(0xd8,77,4),
                (0xee,44,2),(0xf0,40,2),(0xf8,2,4)]:h.put(b+off,value,size)
            events=[t for t in range(260) if tick()[1]]
            self.assertEqual(len(events),1,events)
            handle=observer.state_handle(h);state=h.sections[b'projectileModifier']
            state.serialize(state,handle);unit=bytes(h.uc.mem_read(a,0x490))
            first=[tick() for _ in range(350)]
            self.assertTrue(any(s for q,s in first))
            for q,shots in first:
                self.assertTrue(all(s[10]==0xffffffff for s in shots))
            h.uc.mem_write(a,unit);state.deserialize(state,handle)
            self.assertEqual(first,[tick() for _ in range(350)])

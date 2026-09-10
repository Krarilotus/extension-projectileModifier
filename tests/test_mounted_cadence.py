"""Execute the original mounted bow with independent production weapon timing."""
import unittest
from harness import r
import test_projectiles as projectile_tests


class MountedCadenceTests(unittest.TestCase):
    def prepare(self, config, extreme=False, native=False, moving=False, body=False):
        observer=projectile_tests.NativeTests()
        h=observer.prepare({'Arabian horse archer':config},extreme)
        a=h.unit(1,74);h.unit(2,22,owner=2,x=44)
        for y in range(400):h.put(h.v['TILEROWS']+y*12,y*400)
        delta=h.v['FIREPROJ']-0x532700
        bow=0x575820+delta
        animation=(h.blobs['configuredAnimationHold'][2]['RESUME']-18
            if 'configuredAnimationHold' in h.blobs else
            h.scan(b'A1 ? ? ? ? 69 C0 90 04 00 00 01 9C 30 54 06 00 00'))
        h.put(a+0x44,1)
        if native:
            h.put(a+0x344,2,2);h.put(a+0xa0,2)
            h.put(a+0x39c,3,2);h.put(a+0x2c0,4,2);h.put(a+0x424,4,2)
        if moving:h.put(a+0x2c0,101,2)
        def stub(cleanup,result=0):
            def callback(h):
                esp=h.uc.reg_read(r.UC_X86_REG_ESP)
                h.uc.reg_write(r.UC_X86_REG_EIP,h.get(esp))
                h.uc.reg_write(r.UC_X86_REG_ESP,esp+4+cleanup)
                h.uc.reg_write(r.UC_X86_REG_EAX,result)
            return callback
        def tick():
            queued=observer.tick(h,1)
            h.put(h.v['CURUNIT'],1)
            h.call(animation,registers={r.UC_X86_REG_ESI:h.v['UNITSTATE'],
                r.UC_X86_REG_EBX:1,r.UC_X86_REG_EBP:0},stop=animation+0xa1)
            fields=[0x2b0,0x40,0x44,0x3c,0x48,0x50,0x58]
            before=[h.get(a+off) for off in fields]
            shots=[]
            callbacks={h.spawner:observer.spawn_callback(shots),
                0x449dc0+(0x2e0 if extreme else 0):stub(12)}
            if body:
                # External movement/group management remains outside this unit
                # fixture; execute the real body's state dispatch and bow calls.
                callbacks[0x5254c0+delta]=stub(4)
                callbacks[0x5339a0+delta]=stub(4)
                h.call(0x57ab50+delta,callbacks=callbacks)
            else:
                h.call(bow,args=[1],callbacks=callbacks)
                if not native:
                    self.assertEqual(before,[h.get(a+off) for off in fields])
            if native and h.get(a+0x424,2)==0:
                h.put(a+0x424,4,2);h.put(a+0x2b0,0)
                if not moving:h.put(a+0x2c0,4,2)
            return queued,shots
        return h,a,tick

    def test_intervals_cycle_minimum_and_body_clock(self):
        for extreme in [False,True]:
            with self.subTest(extreme=extreme):
                h,a,tick=self.prepare({'count':1,'inaccuracy':0},extreme,native=True)
                natural=[t for t in range(400) if tick()[1]]
                self.assertGreaterEqual(len(natural),3,natural)
                minimum=natural[1]-natural[0]
                for moving in [False,True]:
                    for interval in [1,300]:
                        h,a,tick=self.prepare({'interval':interval,'count':2,
                            'projectile':'mangonel_pebble','inaccuracy':0},extreme,moving=moving)
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

    def test_real_body_dispatch_standing_and_moving(self):
        for extreme in [False,True]:
            for moving in [False,True]:
                with self.subTest(extreme=extreme,moving=moving):
                    h,a,tick=self.prepare({'interval':200,'inaccuracy':0},extreme,moving=moving,body=True)
                    events=[t for t in range(550) if tick()[1]]
                    self.assertGreaterEqual(len(events),3,events)
                    self.assertEqual({b-a for a,b in zip(events,events[1:])},{200})
                    if moving:self.assertEqual(h.get(a+0x2c0,2),101)

    def test_loaded_save_and_slot_reuse(self):
        observer=projectile_tests.NativeTests()
        for extreme in [False,True]:
            h,a,tick=self.prepare({'interval':300,'inaccuracy':0},extreme,moving=True)
            for _ in range(260):tick()
            handle=observer.state_handle(h);state=h.sections[b'projectileModifier']
            state.serialize(state,handle)
            unit=bytes(h.uc.mem_read(a,0x490))
            first=[tick() for _ in range(400)]
            self.assertTrue(any(s for q,s in first))
            h.uc.mem_write(a,unit);state.deserialize(state,handle)
            self.assertEqual(first,[tick() for _ in range(400)])
            h.put(a+0x98,999)
            observer.tick(h,1)
            for name in ['WEAPONCYCLET','WEAPONTICKT','WEAPONPHASET']:
                self.assertEqual(h.get(h.v[name]+4),0)

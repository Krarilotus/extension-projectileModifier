"""Run native foot-shooter wind-up, release and recoil in both reference EXEs."""
import unittest
from harness import r
import test_projectiles as projectile_tests

FOOT = [('European archer',22,0x55a800),('European crossbowman',23,0x55c7b0),
        ('Arabian archer',70,0x570400),('Arabian slinger',72,0x572e80),
        ('Arabian firethrower',76,0x5769f0)]


class InfantryCadenceTests(unittest.TestCase):
    def prepare(self, unit, config, extreme=False, native=False):
        name,kind,handler=unit
        observer=projectile_tests.NativeTests()
        h=observer.prepare({name:config},extreme)
        a=h.unit(1,kind);h.unit(2,22,owner=2,x=44)
        for y in range(400): h.put(h.v['TILEROWS']+y*12,y*400)
        # Start with stale targeting data. Configured automatic fire must hand
        # its selected target to native wind-up/UID checks without test repair.
        h.put(a+0x344,17,2);h.put(a+0xa0,1234)
        if native:
            h.put(a+0x344,2,2);h.put(a+0xa0,2)
            h.put(a+0x39c,3,2);h.put(a+0x2c0,4,2)
        if 'configuredAnimationHold' in h.blobs:
            animation=h.blobs['configuredAnimationHold'][2]['RESUME']-18
        else:
            animation=h.scan(b'A1 ? ? ? ? 69 C0 90 04 00 00 01 9C 30 54 06 00 00')
        handler+=h.v['FIREPROJ']-0x532700
        sound=0x449dc0+(0x2e0 if extreme else 0)
        def no_sound(h):
            esp=h.uc.reg_read(r.UC_X86_REG_ESP)
            h.uc.reg_write(r.UC_X86_REG_EIP,h.get(esp))
            h.uc.reg_write(r.UC_X86_REG_ESP,esp+16)
        def tick():
            queued=observer.tick(h,1)
            h.put(h.v['CURUNIT'],1)
            h.call(animation,registers={r.UC_X86_REG_ESI:h.v['UNITSTATE'],
                       r.UC_X86_REG_EBX:1,r.UC_X86_REG_EBP:0},stop=animation+0xa1)
            shots=[]
            h.call(handler,callbacks={h.spawner:observer.spawn_callback(shots),sound:no_sound})
            if shots and not native:
                self.assertEqual(h.get(a+0x2b0),h.get(h.v['NATIVECYCLET']+kind*4))
                self.assertEqual(h.get(a+0x50),1)
            if native and h.get(a+0x2c0,2)==0:
                h.put(a+0x2c0,4,2);h.put(a+0x2b0,0)
            return queued,shots
        return h,a,tick

    def test_native_infantry_intervals_and_cycle_minimum(self):
        for extreme in [False,True]:
            for unit in FOOT:
                with self.subTest(extreme=extreme,unit=unit[0]):
                    natural=[]
                    h,a,tick=self.prepare(unit,{'count':1,'inaccuracy':0},extreme,native=True)
                    for t in range(600):
                        queued,shots=tick()
                        self.assertFalse(queued)
                        if shots: natural.append(t)
                    self.assertGreaterEqual(len(natural),2,natural)
                    minimum=natural[1]-natural[0]
                    for interval in [400,1]:
                        h,a,tick=self.prepare(unit,{'interval':interval,'count':3,
                            'projectile':'mangonel_pebble','inaccuracy':0},extreme)
                        events=[]
                        for t in range(natural[0]+max(interval,minimum)*2+10):
                            queued,shots=tick()
                            self.assertFalse(queued)
                            if shots:
                                events.append(t)
                                self.assertEqual([s[9] for s in shots],[4]*3)
                        self.assertGreaterEqual(len(events),3,events)
                        self.assertEqual(events[0],natural[0])
                        self.assertEqual({b-a for a,b in zip(events,events[1:])},{max(interval,minimum)})

    def test_stale_target_replaced_at_loaded_release(self):
        for unit in FOOT:
            with self.subTest(unit=unit[0]):
                h,a,tick=self.prepare(unit,{'interval':300,'inaccuracy':0})
                events=[]
                for t in range(750):
                    if events and t==events[0][0]+295:
                        h.put(h.base+2*0x490+0x3c8,0)
                        h.put(h.base+2*0x490+0x8c,0,2)
                        h.unit(3,22,owner=2,x=46)
                    queued,shots=tick()
                    self.assertFalse(queued)
                    if shots: events.append((t,h.get(a+0x344,2),h.get(a+0xa0)))
                self.assertGreaterEqual(len(events),2,events)
                self.assertEqual(events[0][1:],(2,2))
                self.assertEqual(events[1][1:],(3,3))
                self.assertEqual(events[1][0]-events[0][0],300)

    def test_native_infantry_building_target_and_loaded_save_continuation(self):
        observer=projectile_tests.NativeTests()
        for extreme in [False,True]:
            for unit in FOOT:
                with self.subTest(extreme=extreme,unit=unit[0]):
                    h,a,tick=self.prepare(unit,{'interval':300,'targets':['buildings'],
                        'count':2,'stagger_min':2,'stagger_max':2,'inaccuracy':0},extreme)
                    b=h.v['BLDBASE']+0x32c
                    for off,value,size in [(0xd0,1,2),(0xd2,1,2),(0xd6,2,2),(0xd8,77,4),
                                          (0xee,44,2),(0xf0,40,2),(0xf8,2,4)]: h.put(b+off,value,size)
                    events=[]
                    for t in range(270):
                        queued,shots=tick()
                        if queued or shots:
                            events.append(t)
                            self.assertTrue(all(s[10]==0xffffffff for s in queued+shots))
                    self.assertEqual(len(events),2,events)
                    self.assertEqual(events[1]-events[0],2)
                    handle=observer.state_handle(h);state=h.sections[b'projectileModifier']
                    state.serialize(state,handle)
                    native=bytes(h.uc.mem_read(a,0x490))
                    first=[tick() for _ in range(200)]
                    self.assertTrue(any(queued or shots for queued,shots in first))
                    h.uc.mem_write(a,native)
                    state.deserialize(state,handle)
                    self.assertEqual(first,[tick() for _ in range(200)])

    def test_native_foot_stance_and_fortification_overrides(self):
        for extreme in [False,True]:
            h,a,tick=self.prepare(FOOT[0],{'interval':300,'interval_moving':0,
                'inaccuracy':0,'on_fortification':{'projectile':'crossbow_bolt','count':2}},extreme)
            h.put(a+0xbc,30,2)
            h.put(h.v['TILEFLAGS']+(40*400+40)*4,0x100)
            events=[]
            for t in range(600):
                if 250<=t<440: h.put(a+0xb6,320+(t%2)*8,2)
                queued,shots=tick()
                self.assertFalse(queued)
                if shots:
                    events.append(t)
                    self.assertEqual([s[9] for s in shots],[7,7])
            self.assertEqual(len(events),2,events)
            self.assertGreaterEqual(events[1],440)

    def test_inf_pending_flag_does_not_bypass_cooldown(self):
        for unit in [FOOT[0],FOOT[2]]:
            h,a,tick=self.prepare(unit,{'interval':300,'inaccuracy':0})
            events=[]
            for t in range(800):
                h.put(a+0x40e,1,1)  # native archers may retry a pending shot
                queued,shots=tick()
                self.assertFalse(queued)
                if shots: events.append(t)
            self.assertGreaterEqual(len(events),3,events)
            self.assertEqual({b-a for a,b in zip(events,events[1:])},{300})

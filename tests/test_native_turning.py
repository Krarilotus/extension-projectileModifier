"""Compare configured siege aiming with the unmodified executable's state 8."""
import unittest
from harness import r
import test_projectiles as projectile_tests
import test_manual_release as manual_tests
import test_infantry_cadence as infantry_tests
from unicorn import UC_HOOK_CODE


SIEGE = [('Catapult',39,0x568320), ('Trebuchet',40,0x569410),
         ('Mangonel',41,0x56a3f0), ('Tower ballista',61,0x56ecd0),
         ('Fire ballista',77,0x577cc0)]


class NativeTurningTests(unittest.TestCase):
    def test_foot_shooters_keep_original_facing_through_first_release(self):
        for extreme in (False,True):
            for unit in infantry_tests.FOOT:
                with self.subTest(extreme=extreme,unit=unit[0]):
                    traces=[]
                    for native in (True,False):
                        settings={'count':1,'inaccuracy':0} if native else {'interval':400,'inaccuracy':0}
                        h,a,tick=infantry_tests.InfantryCadenceTests().prepare(unit,settings,extreme,native=native)
                        trace=[]
                        for _ in range(300):
                            queued,shots=tick()
                            self.assertFalse(queued)
                            trace.append((h.get(a+0x2b4,2),h.get(a+0x54,2)))
                            if shots:break
                        self.assertTrue(shots)
                        self.assertEqual(trace[-1],(2,2))
                        traces.append(trace)
                    self.assertEqual(traces[0],traces[1])

    def test_manual_aiming_acquires_once_and_preserves_the_order(self):
        for extreme in (False,True):
            for name,kind,handler in SIEGE[:2]:
                for order in (4,5,9,23):
                    with self.subTest(extreme=extreme,unit=name,order=order):
                        h,a,_=manual_tests.ManualReleaseTests().prepare(name,kind,handler,order,extreme)
                        calls=[]
                        token=h.uc.hook_add(UC_HOOK_CODE,lambda *args:calls.append(1),
                            begin=h.v['ACQUIRE'],end=h.v['ACQUIRE'])
                        try: projectile_tests.NativeTests().tick(h,1)
                        finally: h.uc.hook_del(token)
                        self.assertEqual(calls,[1])
                        self.assertEqual(h.get(a+0x39c,2),order)
                        self.assertEqual(h.get(a+0x362,2),1)
                        self.assertEqual(h.get(a+0x2c0,2),8)

    def test_aiming_matches_original_steps_in_all_directions_and_camera_rotations(self):
        observer = projectile_tests.NativeTests()
        for extreme in (False, True):
            for name, kind, handler in SIEGE:
                configured = observer.prepare({name: {'interval':700}}, extreme)
                original = observer.prepare({name: {'count':1}}, extreme)
                delta = configured.v['FIREPROJ'] - 0x532700
                turn = configured.scan(b'8B 44 24 04 8B 54 24 08 69 C0 90 04 00 00 53 0F BF 9C 08 C8 08 00 00')
                # No patch to the native direction helper or siege handlers.
                self.assertEqual(bytes(configured.uc.mem_read(turn,0xec)),
                                 bytes(original.uc.mem_read(turn,0xec)))
                self.assertEqual(bytes(configured.uc.mem_read(handler+delta,0x1000)),
                                 bytes(original.uc.mem_read(handler+delta,0x1000)))
                for camera in (0,2,4,6):
                    for index, (dx,dy) in enumerate(((0,-4),(4,-4),(4,0),(4,4),
                                                     (0,4),(-4,4),(-4,0),(-4,-4))):
                        with self.subTest(extreme=extreme,unit=name,camera=camera,target=(dx,dy)):
                            traces = []
                            for h, active in ((original,False),(configured,True)):
                                a = h.unit(1,kind,uid=100+camera*8+index)
                                h.unit(2,22,owner=2,x=40+dx,y=40+dy)
                                h.put(a+0x3b4,3 if kind==40 else 2,2)
                                h.put(a+0x362,20,2)
                                h.put(a+0x39c,3,2)
                                h.put(a+0x3e8,40+dx,2); h.put(a+0x3ea,40+dy,2)
                                h.put(a+0xbe,(40+dx)*8,2); h.put(a+0xc0,(40+dy)*8,2)
                                h.put(a+0x54,(-camera)%8,2)
                                # Native camera-facing subtraction operand.
                                h.put(h.get(turn+0xc2),camera)
                                if not active: h.put(a+0x2c0,8,2)
                                animation = (h.blobs['configuredAnimationHold'][2]['RESUME']-18
                                    if active else h.scan(b'A1 ? ? ? ? 69 C0 90 04 00 00 01 9C 30 54 06 00 00'))
                                trace = []
                                for tick in range(40):
                                    if active: self.assertEqual(observer.tick(h,1),[])
                                    h.put(h.v['CURUNIT'],1)
                                    h.call(animation,registers={r.UC_X86_REG_ESI:h.v['UNITSTATE'],
                                        r.UC_X86_REG_EBX:1,r.UC_X86_REG_EBP:0},stop=animation+0xa1)
                                    h.call(handler+delta)
                                    trace.append(tuple(h.get(a+off,size) for off,size in
                                        ((0x2c0,2),(0x2b4,2),(0x54,2),(0x74,4),(0x40,4),(0x44,4))))
                                    self.assertEqual(h.get(a+0x362,2),20)
                                    if h.get(a+0x2c0,2)==2: break
                                self.assertEqual(h.get(a+0x2c0,2),2,'native aiming must reach reload')
                                traces.append(trace)
                            self.assertEqual(traces[0],traces[1])
                            self.assertTrue(any(row[1] for row in traces[1]) or (dx,dy)==(0,-4))

    def test_changed_ground_target_is_faced_before_next_release(self):
        for extreme in (False, True):
            for name, kind, handler in SIEGE:
                with self.subTest(extreme=extreme, unit=name):
                    h, a, tick = manual_tests.ManualReleaseTests().prepare(
                        name, kind, handler, 5, extreme, interval=700)
                    h.put(a+0x362, 20, 2)
                    first = None
                    for t in range(1400):
                        queued, shots = tick()
                        self.assertFalse(queued)
                        if not shots:
                            continue
                        if first is None:
                            first = t
                            self.assertEqual(h.get(a+0x2b4, 2), 2)
                            # Native command coordinates: select ground west of the engine.
                            site = h.scan(b'B9 ? ? ? ? 66 C7 84 37 9E 09 00 00 FF FF E8')
                            h.put(h.get(site+1)+0xc0+400*40+36, 1, 1)
                            h.put(a+0x3e8, 36, 2)
                            h.put(a+0x3ea, 40, 2)
                        else:
                            self.assertGreaterEqual(t-first, 700)
                            self.assertEqual(h.get(a+0x2b4, 2), 6,
                                'the engine must face its newly accepted target before firing')
                            self.assertTrue(all(s[6:8] == (288, 320) for s in shots))
                            break
                    else:
                        self.fail('both shots must reach the native release')

    def test_turning_during_loaded_cooldown_uses_no_target_query_and_survives_save(self):
        observer = projectile_tests.NativeTests()
        for extreme in (False, True):
            for name, kind, handler in SIEGE[:2]:
                for order in (4, 5, 9, 23):
                    with self.subTest(extreme=extreme, unit=name, order=order):
                        h, a, tick = manual_tests.ManualReleaseTests().prepare(
                            name, kind, handler, order, extreme, interval=700)
                        h.put(a+0x362, 20, 2)
                        rest = (2, 12 if kind == 39 else 35)
                        for _ in range(650):
                            tick()
                            if (h.get(a+0x362, 2) == 19 and
                                (h.get(a+0x2c0, 2), h.get(a+0x2b0)) == rest):
                                break
                        else:
                            self.fail('the native reload must reach its loaded hold')
                        if order == 4:
                            h.unit(3, 37, owner=2, x=36, y=40)
                            h.put(a+0x39e, 3, 2); h.put(a+0x3a0, 3)
                        elif order == 9:
                            b = h.v['BLDBASE']+0x32c
                            h.put(b+0xee, 35, 2); h.put(b+0xf0, 39, 2)
                        else:
                            h.put(a+0x3e8, 36, 2); h.put(a+0x3ea, 40, 2)
                        acquisitions = []
                        token = h.uc.hook_add(UC_HOOK_CODE, lambda *args: acquisitions.append(1),
                            begin=h.v['ACQUIRE'], end=h.v['ACQUIRE'])
                        seed = h.get(h.v['SEED'])
                        try:
                            def advance(count):
                                trace = []
                                for _ in range(count):
                                    self.assertEqual(tick(), ([], []))
                                    self.assertEqual((h.get(a+0x2c0, 2),h.get(a+0x2b0)), rest)
                                    trace.append((h.get(a+0x2b4, 2),h.get(a+0x54, 2),h.get(a+0x40)))
                                return trace
                            start = advance(9)
                            self.assertNotEqual(start[-1][0], 2, 'turn while the long cooldown is still active')
                            saved = observer.state_handle(h); state = h.sections[b'projectileModifier']
                            state.serialize(state, saved)
                            native = bytes(h.uc.mem_read(a, 0x490))
                            first = advance(24)
                            self.assertEqual(first[-1][0], 6)
                            turns = [i for i in range(1,len(start+first))
                                     if (start+first)[i][0] != (start+first)[i-1][0]]
                            self.assertGreaterEqual(len(turns), 3)
                            self.assertEqual({b-a for a,b in zip(turns,turns[1:])}, {6})
                            h.uc.mem_write(a, native); state.deserialize(state, saved)
                            self.assertEqual(first, advance(24))
                            self.assertEqual(acquisitions, [], 'turning must not reroll or replace the target')
                            self.assertEqual(h.get(h.v['SEED']), seed)
                            self.assertGreater(h.get(h.v['COOLDOWNT']+4), 300)
                        finally:
                            h.uc.hook_del(token)

    def test_explicit_off_retains_previous_manual_turning_behavior(self):
        for extreme in (False, True):
            h, a, tick = manual_tests.ManualReleaseTests().prepare(
                'Catapult', 39, 0x568320, 5, extreme, interval=700, turn_before_shot=False)
            h.put(a+0x362, 20, 2)
            for _ in range(200): tick()
            h.put(a+0x3e8, 36, 2)
            for _ in range(40): tick()
            self.assertEqual(h.get(a+0x2b4, 2), 2)
            self.assertEqual(h.get(h.v['TURNBEFORET']+39*4), 0)
            self.assertEqual(h.v['FACEPOINT'], 0)
            self.assertEqual(h.v['FACEUNIT'], 0)

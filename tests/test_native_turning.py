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

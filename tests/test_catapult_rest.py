"""Catapult delay belongs to the lowered reload pose, before the entire swing."""
import unittest
import test_cadence as cadence_tests


class CatapultRestTests(unittest.TestCase):
    def test_conflicting_reload_pose_or_speed_is_rejected_before_patching(self):
        from harness import Harness
        for extreme in (False, True):
            for changed in ('engine', 'crew', 'speed'):
                with self.subTest(extreme=extreme, changed=changed):
                    h = Harness(extreme)
                    site = h.scan(b'8B 1D ? ? ? ? 8B C3 69 C0 90 04 00 00 8B 88 ? ? ? ? 0F BE 89 ? ? ? ? 3B CD 89 88 ? ? ? ? 7F 17 5F 5E') + 8
                    if changed == 'engine': h.put(h.get(site+15)+12, 22, 1)
                    elif changed == 'crew': h.put(h.get(site+0x4e)+12, 50, 1)
                    else: h.put(site-0x8c+1, 3)
                    with self.assertRaisesRegex(Exception, 'unsupported catapult'):
                        h.enable({'Catapult': {'interval': 700}})
                    self.assertEqual(h.writes, [])

    def test_lowered_gate_preserves_cows_movement_and_late_release_checks(self):
        for extreme in (False, True):
            _, h, v, *_ = cadence_tests.CadenceTests().prepare('Catapult', 39, 23, 0x568320, extreme)
            a = h.unit(1, 39)
            for off, value, size in ((0x2c0,2,2), (0x2b0,12,4), (0x40,5,4), (0x44,5,4)):
                h.put(a+off, value, size)
            def hold(remaining, blocked=0):
                return h.call(v['SHOULDHOLD'], [1, v['RELEASECYCLE'], remaining, blocked])
            self.assertEqual(hold(28), 1)
            self.assertEqual(hold(27), 0)
            self.assertEqual(hold(27, 1), 1)
            h.put(a+0x3b0, 1, 2)
            self.assertEqual(hold(700, 1), 0)
            h.put(a+0x3b0, 0, 2)
            for phase in (0, 8, 101):
                h.put(a+0x2c0, phase, 2)
                self.assertEqual(hold(700, 1), 0)
            h.put(a+0x2c0, 4, 2); h.put(a+0x2b0, v['RELEASECYCLE']-1)
            self.assertEqual(hold(0), 0)
            self.assertEqual(hold(0, 1), 1)

    def test_long_interval_waits_lowered_and_preserves_the_complete_swing(self):
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                swings = []
                for interval in (1, 700):
                    h, a, tick = cadence_tests.CadenceTests().integrated(
                        'Catapult', 39, 0x568320, {'interval': interval}, extreme)
                    events = []; resting = []; current = []; completed = []
                    for t in range(1600 if interval == 700 else 450):
                        queued, shots = tick()
                        self.assertFalse(queued)
                        if shots: events.append(t)
                        state, cycle = h.get(a+0x2c0, 2), h.get(a+0x2b0)
                        if state == 4:
                            current.append((cycle, h.get(a+4), h.get(a+0x74), bool(shots)))
                        elif current:
                            completed.append(current); current = []
                        if interval == 700 and 300 <= t < 700:
                            resting.append(t)
                            self.assertEqual((state, cycle), (2, 12))
                            # Native engine pose 13 and engineer pose 41, facing east.
                            self.assertEqual(h.get(a+4), (13-1)*8+3)
                            self.assertEqual(h.get(a+0x74), (41-1)*8+3)
                    self.assertGreaterEqual(len(completed), 3)
                    self.assertTrue(all(s == completed[0] for s in completed))
                    swings.append(completed[0])
                    if interval == 700:
                        self.assertEqual(events, [117, 817, 1517])
                        self.assertEqual(len(resting), 400)
                        self.assertEqual(h.get(a+0x362, 2), 997)
                self.assertEqual(swings[0], swings[1])


if __name__ == '__main__':
    unittest.main()

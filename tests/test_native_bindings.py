"""Binding provenance and fail-closed context; relocation is not variant acceptance."""
from pathlib import Path
import unittest
from harness import Harness, ROOT


class NativeBindingTests(unittest.TestCase):
    def use_framework_cache(self, h):
        framework = ROOT.parent / 'UnofficialCrusaderPatch3/content/ucp/code'
        h.lua.globals().data.cache = h.lua.execute((framework/'data/cache.lua').read_bytes())
        code = (framework/'core.lua').read_bytes()
        start = code.index(b'function core.AOBScan(')
        end = code.index(b'---Hook game code', start)
        h.lua.execute(code[start:end])

    def test_rps_region_scan_may_return_the_requested_upper_bound_or_beyond(self):
        # RPS v1.5.2 AOB::Scan checks max only after scanning a complete
        # VirtualQuery region. Model a region containing the selected site:
        # a search ending at that site can still return it (or a later match).
        for extreme in (False, True):
            h = Harness(extreme)
            def region_scan(pattern, start=0x400000, end=0x700000):
                try: return h.scan(pattern, start, 0x700000)
                except RuntimeError: return 0
            h.lua.globals().core.scanForAOB = region_scan
            self.use_framework_cache(h)
            h.enable({'Catapult': {'count': 3}})
            self.assertEqual(h.blobs['tickHook'][2]['UNITARRAY'], h.base)

    def test_framework_cache_resolves_both_native_layouts(self):
        for extreme in (False, True):
            h = Harness(extreme); self.use_framework_cache(h)
            h.enable({'Catapult': {'interval': 700}})
            values = h.blobs['tickHook'][2]
            self.assertEqual(values['UNITARRAY'], h.base)
            self.assertEqual(values['MAXUNITS'], 10000 if extreme else 2500)

    def test_operands_and_loop_context_reject_conflicts_before_allocation(self):
        for extreme in (False, True):
            for changed in ('array', 'opcode', 'cursor', 'branch', 'capacity'):
                with self.subTest(extreme=extreme, changed=changed):
                    h = Harness(extreme)
                    fire = h.scan(b'53 56 57 8B 7C 24 14 33 C0 33 D2 83 FF 03 0F 85')
                    tick = h.scan(b'83 C2 01 89 16 8B 15 ? ? ? ? 69 D2 90 04 00 00 33 C9 66 89 8C 32 AE 09 00 00')
                    if changed == 'array': h.put(fire+0x12d, h.get(fire+0x12d)+4)
                    elif changed == 'opcode': h.put(fire+0x22, 0xbf, 1)
                    elif changed == 'cursor': h.put(tick+0x3aa, h.get(tick+0x3aa)+4)
                    elif changed == 'branch': h.put(tick+0x3b0, h.get(tick+0x3b0)+1)
                    else: h.put(tick+0x3a4, 4096)
                    with self.assertRaisesRegex(Exception, 'unit.array'):
                        h.enable({'Catapult': {'count': 3}})
                    self.assertEqual(h.writes, [])
                    self.assertEqual(h.allocations, [])

    def test_missing_ambiguous_and_cached_occupied_sites_are_rejected(self):
        for changed in ('missing', 'ambiguous', 'cached-earlier-duplicate', 'cached-occupied'):
            with self.subTest(changed=changed):
                h = Harness(); self.use_framework_cache(h)
                pattern = b'53 56 57 8B 7C 24 14 33 C0 33 D2 83 FF 03 0F 85'
                fire = h.lua.globals().core.AOBScan(pattern)
                if changed == 'ambiguous':
                    h.uc.mem_write(0x6f0000, bytes(h.uc.mem_read(fire, 20)))
                elif changed == 'cached-earlier-duplicate':
                    h.uc.mem_write(0x401000, bytes(h.uc.mem_read(fire, 20)))
                else:
                    h.put(fire, 0xe9, 1)
                    if changed == 'missing': self.use_framework_cache(h)
                with self.assertRaisesRegex(Exception, 'unsupported executable|ambiguous native'):
                    h.enable({'Catapult': {'count': 3}})
                self.assertEqual(h.writes, [])

    def test_binding_decodes_operands_instead_of_selecting_a_fixed_array(self):
        # Synthetic operand relocation exercises decoding only. It does not
        # establish that a third executable, or a relocated game, is supported.
        h = Harness()
        fire = h.scan(b'53 56 57 8B 7C 24 14 33 C0 33 D2 83 FF 03 0F 85')
        moved = h.base + 0x100000
        for offset in (0x23, 0x12d): h.put(fire+offset, moved+0x3b0)
        h.enable({'Catapult': {'count': 3}})
        values = h.blobs['tickHook'][2]
        self.assertEqual(values['UNITARRAY'], moved)
        self.assertFalse((ROOT/'addresses.lua').exists())

    def test_unrequested_accuracy_does_not_claim_occupied_native_sites(self):
        patterns = (
            b'51 8B 44 24 08 8B 54 24 0C 69 C0 90 04 00 00 53 55 56 8D 34 08',
            b'0F B7 86 CE 06 00 00 0F B7 8E D6 06 00 00 66 3B C1')
        for extreme in (False, True):
            for requested in (False, True):
                h = Harness(extreme)
                sites = [h.scan(pattern) for pattern in patterns]
                for site in sites: h.put(site, 0xe9, 1)
                h.scans.clear()
                cfg = {'count': 3}
                if requested: cfg['on_fortification'] = {'inaccuracy': 0}
                if requested:
                    with self.assertRaisesRegex(Exception, 'unsupported executable'):
                        h.enable({'Catapult': cfg})
                    self.assertEqual(h.writes, [])
                    self.assertEqual(h.allocations, [])
                else:
                    h.enable({'Catapult': cfg})
                    self.assertTrue(all(pattern not in h.scans for pattern in patterns))
                    self.assertTrue(all(h.get(site, 1) == 0xe9 for site in sites))
                    self.assertTrue(all(site not in [a for a, _ in h.writes] for site in sites))
                    self.assertNotIn('accuracySet', h.blobs)
                    self.assertNotIn('groundAimHook', h.blobs)
                    self.assertNotIn('aimErrorHook', h.blobs)

    def test_accuracy_and_cadence_include_effective_decoration_profiles(self):
        from test_decorations import DecorationTests
        for extreme in (False, True):
            config = {'decorations': {'frost': {}}, 'units': {'Catapult': {
                'near_decorations': [{'decoration': 'frost', 'inaccuracy': 0, 'interval': 700}]}}}
            h = DecorationTests().prepare_module(config, extreme)
            self.assertIn('groundAimHook', h.blobs)
            self.assertIn('aimErrorHook', h.blobs)
            self.assertIn('configuredAnimationHold', h.blobs)
            # Both inherited effective profiles retain the explicitly configured zero.
            self.assertEqual(h.get(h.v['INACCSETT'] + 160*4), 1)
            self.assertEqual(h.get(h.v['INACCSETT'] + 161*4), 1)

    def test_facing_binding_is_conditional_and_rejects_occupied_native_owners(self):
        for extreme in (False, True):
            for enabled in (False, True):
                h = Harness(extreme)
                point = h.scan(b'8B 44 24 04 8B 54 24 08 69 C0 90 04 00 00 53 0F BF 9C 08 C8 08 00 00')
                h.put(point, 0xe9, 1)
                cfg = {'interval': 700, 'turn_before_shot': enabled}
                if enabled:
                    with self.assertRaisesRegex(Exception, 'unsupported executable'):
                        h.enable({'Catapult': cfg})
                    self.assertEqual(h.allocations, [])
                    self.assertEqual(h.writes, [])
                else:
                    h.enable({'Catapult': cfg})
                    self.assertEqual(h.get(point, 1), 0xe9)


if __name__ == '__main__':
    unittest.main()

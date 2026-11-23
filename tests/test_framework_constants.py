"""Configured startup must assemble the way the framework formats constants.

Framework 3.0.7 and 3.0.8 write each assembler constant as `0x%X`. A negative
constant became `0xFFFFFFFFFFFFFFFF`, and the game stopped at startup with
`error in script: -121` (value out of range) on both editions. The harness
used to convert constants to 32 bits first, which hid it.
"""
import tempfile
import unittest
from pathlib import Path
from lupa.lua54 import LuaError
from harness import AssemblyError, Harness, ROOT
import test_projectiles as projectile_tests

# The configurations from the failed 2026-11-22 player-baseline launches:
# the guide's archer, Catapult and Mangonel examples on Crusader, and the
# target-ammunition Catapult example alone on Extreme.
CRUSADER_STARTUP = '''\
units:
  European archer:
    interval: 600
  Catapult:
    interval: 700
    range: 40
  Mangonel:
    count: 10
    spread: 48
'''
EXTREME_STARTUP = '''\
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
'''
PROBE = b'probe:\n    cmp dword [eax+0x2B0], VALUE\n    ret\n'


class FrameworkConstantTests(unittest.TestCase):
    def load_text(self, h, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'projectiles.yml'
            path.write_text(text, encoding='utf-8')
            projectile_tests.ConfigTests().load_file(h, path)

    def assert_unsigned_dwords(self, h):
        self.assertTrue(h.blobs)
        for name, (_, _, values) in h.blobs.items():
            for key, value in values.items():
                with self.subTest(blob=name, constant=key):
                    self.assertGreaterEqual(value, 0)
                    self.assertLessEqual(value, 0xFFFFFFFF)

    def test_harness_formats_constants_like_the_framework(self):
        h = Harness()
        with self.assertRaises(AssemblyError):
            h.assemble(PROBE, h.config({'VALUE': -1}))
        with self.assertRaises(LuaError):
            h.assemble(PROBE, h.config({'VALUE': 1.5}))
        h.assemble(PROBE, h.config({'VALUE': 0xFFFFFFFF}))

    def test_failed_startup_configs_assemble_on_their_editions(self):
        for extreme, text in ((False, CRUSADER_STARTUP), (True, EXTREME_STARTUP)):
            with self.subTest(extreme=extreme):
                h = Harness(extreme)
                self.load_text(h, text)
                hold = h.blobs['shouldHold'][2]
                # No Trebuchet entry: its rest check must never match.
                self.assertEqual(hold['TREBRESTCYCLE'], 0xFFFFFFFF)
                self.assertLess(hold['CATRESTCYCLE'], 0x100)
                self.assert_unsigned_dwords(h)

    def test_both_rest_checks_inactive_use_the_unsigned_sentinel(self):
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                h = Harness(extreme)
                self.load_text(h, 'units:\n  European archer:\n    interval: 600\n')
                hold = h.blobs['shouldHold'][2]
                self.assertEqual(hold['CATRESTCYCLE'], 0xFFFFFFFF)
                self.assertEqual(hold['TREBRESTCYCLE'], 0xFFFFFFFF)
                self.assert_unsigned_dwords(h)

    def test_target_ammunition_example_assembles_on_both_editions(self):
        text = (ROOT / 'examples' / 'targeted-ammunition.yml').read_text(encoding='utf-8')
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                h = Harness(extreme)
                self.load_text(h, text)
                self.assert_unsigned_dwords(h)


if __name__ == '__main__':
    unittest.main()

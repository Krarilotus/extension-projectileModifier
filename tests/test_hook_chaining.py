"""Shared sites: continue into another extension's handler instead of refusing.

Smarter Walls (unit update loop), Improved Siegeengines and the ghost-object
fix (entity update) and Improved Tunnelers (toolbar handler) each replace the
first instructions with a jump to a handler that replays them once and jumps
back. The fakes below have exactly that shape. When such a handler is already
installed, this module must run its own handler first, then theirs, and the
replaced instructions must still run exactly once.
"""
import struct
import unittest
from harness import Harness, r
import test_decorations as decoration_tests
import test_sprite_resources as sprite_tests

TICK = (b'83 C2 01 89 16', 5, b'8B 15 ? ? ? ? 69 D2 90 04 00 00 33 C9 66 89 8C 32 AE 09 00 00')
ENTITY = (b'51 53 55 56 8B F1', 6, b'8B 0D ? ? ? ? B8 67 66 66 66 F7 E9')
TOOLBAR = (b'53 33 DB 39 1D ? ? ? ?', 9, b'0F 85 ? ? ? ? 39 1D ? ? ? ? 0F 85 ? ? ? ? A1 ? ? ? ? 8B C8')


def redirect(h, site, size, target):
    h.uc.mem_write(site, b'\xe9' + struct.pack('<i', target - (site + 5)) + b'\x90' * (size - 5))


def other_extension(h, signature, replay):
    """Install a handler shaped like the other extension's, return (site, handler, counter)."""
    displaced, size, tail = signature
    site = h.scan(displaced + b' ' + tail)
    counter = h.allocate(4)
    source = b'otherHandler:\n    inc dword [COUNTER]\n' + replay + b'\n    jmp BACK\n'
    handler = h.assemble(source, h.config({'COUNTER': counter, 'BACK': site + size,
                                           'OPERAND': h.get(site + 5)}))
    redirect(h, site, size, handler)
    return site, handler, counter


class HookChainingTests(unittest.TestCase):
    def test_unit_loop_runs_this_handler_then_the_other_and_the_loop_step_once(self):
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                h = Harness(extreme)
                site, handler, counter = other_extension(h, TICK,
                    b'    add edx, 1\n    mov [esi], edx')
                h.enable({'Catapult': {'count': 3}})
                values = h.blobs['tickHook'][2]
                self.assertEqual(values['TICKCONTINUE'], handler)
                self.assertNotIn('tickOriginal', h.blobs)
                self.assertEqual(h.get(site, 1), 0xE9)
                self.assertEqual(site + 5 + struct.unpack('<i', bytes(h.uc.mem_read(site + 1, 4)))[0],
                                 h.blobs['tickHook'][0])
                order = []
                state = h.allocate(4)
                h.put(values['CURUNIT'], 1)
                h.call(site, registers={r.UC_X86_REG_EDX: 1, r.UC_X86_REG_ESI: state}, stop=site + 5,
                       callbacks={h.blobs['tickHook'][0]: lambda _: order.append('this'),
                                  handler: lambda _: order.append('other')})
                self.assertEqual(order, ['this', 'other'])
                self.assertEqual(h.get(counter), 1)
                self.assertEqual(h.uc.reg_read(r.UC_X86_REG_EDX), 2)
                self.assertEqual(h.get(state), 2)

    def test_unredirected_unit_loop_still_replays_its_own_step(self):
        h = Harness()
        site = h.scan(TICK[0] + b' ' + TICK[2])
        h.enable({'Catapult': {'count': 3}})
        self.assertEqual(h.blobs['tickHook'][2]['TICKCONTINUE'], h.blobs['tickOriginal'][0])
        state = h.allocate(4)
        h.call(site, registers={r.UC_X86_REG_EDX: 4, r.UC_X86_REG_ESI: state}, stop=site + 5)
        self.assertEqual((h.uc.reg_read(r.UC_X86_REG_EDX), h.get(state)), (5, 5))

    def test_a_jump_into_the_game_is_refused_before_any_write(self):
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                h = Harness(extreme)
                site = h.scan(TICK[0] + b' ' + TICK[2])
                redirect(h, site, 5, site + 0x200)
                with self.assertRaisesRegex(Exception, 'conflicting module'):
                    h.enable({'Catapult': {'count': 3}})
                self.assertEqual(h.writes, [])
                self.assertEqual(h.allocations, [])

    def test_entity_update_calls_the_other_handler_as_the_original(self):
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                installed = {}
                def mutate(h):
                    installed['site'], installed['handler'], installed['counter'] = other_extension(
                        h, ENTITY, b'    push ecx\n    push ebx\n    push ebp\n    push esi\n    mov esi, ecx')
                tests = sprite_tests.SpriteResourcesTests()
                tests.addCleanup = self.addCleanup
                h, state, _ = tests.prepare(extreme, mutate)
                self.assertEqual(h.v['ENTITYORIGINAL'], installed['handler'])
                self.assertNotIn('spriteUpdateOriginal', h.blobs)
                order = []
                h.call(installed['site'], registers={r.UC_X86_REG_ECX: state},
                       callbacks={h.blobs['spriteUpdate'][0]: lambda _: order.append('this'),
                                  installed['handler']: lambda _: order.append('other')})
                self.assertEqual(order, ['this', 'other'])
                self.assertEqual(h.get(installed['counter']), 1)

    def test_toolbar_handler_is_hooked_through_a_stub_that_continues_into_the_other(self):
        nops = bytes([0x90])
        for extreme in (False, True):
            with self.subTest(extreme=extreme):
                installed = {}
                def before(h):
                    installed['site'], installed['handler'], installed['counter'] = other_extension(
                        h, TOOLBAR, b'    push ebx\n    xor ebx, ebx\n    cmp [OPERAND], ebx')
                h = decoration_tests.DecorationTests().prepare_module(
                    {'decorations': {'frost': {}}}, extreme, before)
                site, handler, counter = installed['site'], installed['handler'], installed['counter']
                hooked = [address for _, address, _, _, size in h.hooks if size == 9]
                self.assertEqual(len(hooked), 1)
                stub = hooked[0]
                self.assertNotEqual(stub, site)
                self.assertEqual(bytes(h.uc.mem_read(stub, 9)), nops * 9)
                self.assertEqual(site + 5 + struct.unpack('<i', bytes(h.uc.mem_read(site + 1, 4)))[0], stub)
                self.assertEqual(bytes(h.uc.mem_read(site + 5, 4)), nops * 4)
                # The framework detour is stubbed here; the stub itself falls
                # through into the other handler, which returns after the site.
                h.call(stub, stop=site + 9)
                self.assertEqual(h.get(counter), 1)


if __name__ == '__main__':
    unittest.main()

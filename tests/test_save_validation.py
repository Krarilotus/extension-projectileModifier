"""Read-only validation through the actual Map Extensions restore owner."""
import os
from pathlib import Path
import unittest

from harness import ROOT
import test_projectiles

MAP_OWNER = Path(os.environ.get('MAP_EXTENSIONS_REFERENCE',
    ROOT.parent / 'aic-tactics-map-required-state'))


class SaveValidationTests(unittest.TestCase):
    prepare = test_projectiles.NativeTests.prepare
    state_handle = test_projectiles.NativeTests.state_handle

    def state(self, extreme=False):
        h = self.prepare({'Catapult': {'interval': 700}}, extreme)
        state = h.sections[b'projectileModifier']
        state.initialize(state)
        h.put(h.v['COOLDOWNT'] + 4, 531)
        handle = self.state_handle(h)
        state.serialize(state, handle)
        return h, state, handle

    def blocks(self, h, state):
        return [bytes(h.uc.mem_read(b[2], b[3])) for b in state.blocks.values()]

    def test_validation_is_read_only_and_preserves_format_five(self):
        for extreme in (False, True):
            h, state, handle = self.state(extreme)
            before, allocations = self.blocks(h, state), list(h.allocations)
            state.validate(state, handle)
            self.assertEqual(self.blocks(h, state), before)
            self.assertEqual(h.allocations, allocations)
            self.assertEqual(handle.files[b'format'], b'5')
            saved = dict(handle.files.items())
            h.put(h.v['COOLDOWNT'] + 4, 123)
            state.deserialize(state, handle)
            state.serialize(state, handle)
            self.assertEqual(dict(handle.files.items()), saved)

    def test_absent_legacy_section_validates_without_resetting_live_state(self):
        h, state, _ = self.state()
        empty = self.state_handle(h)
        before = self.blocks(h, state)
        state.validate(state, empty)
        self.assertEqual(self.blocks(h, state), before)
        state.deserialize(state, empty)
        self.assertEqual(h.get(h.v['COOLDOWNT'] + 4), 0)
        self.assertEqual(h.get(h.v['SEED']), 0x1d872b41)

    def test_required_missing_section_is_rejected_without_reset(self):
        h, state, _ = self.state()
        empty = self.state_handle(h)
        empty[b'required'] = True
        before = self.blocks(h, state)
        with self.assertRaisesRegex(Exception, 'unsupported saved state format'):
            state.validate(state, empty)
        self.assertEqual(self.blocks(h, state), before)

    def test_owner_rejects_bad_projectile_state_before_any_extension_restore(self):
        h, state, handle = self.state()
        g = h.lua.globals()
        g.MAP_OWNER = MAP_OWNER.as_posix().encode()
        g.projectile_state, g.saved = state, handle.files
        g.read_address = h.v['SEED']
        h.lua.execute(b'''
          package.path=MAP_OWNER..'/?.lua;'..package.path
          local entries={}
          for name,data in pairs(saved) do entries['projectileModifier/'..name]=data end
          local current
          local zip={open_entry=function(_,name)
            assert(current==nil)
            if entries[name]==nil then return false end
            current=name;return true
          end,read_entry=function()return entries[current] end,
          close_entry=function()current=nil;return true end,close=function()end}
          other_restores=0
          package.loaded['mapextensions.registry']={registry={
            aaa={deserialize=function()other_restores=other_restores+1 end},
            projectileModifier=projectile_state}}
          package.loaded['mapextensions.memory']={customSectionAddress=read_address,
            customSectionInfoObject={size=1}}
          package.loaded['mapextensions.game']={}
          package.loaded['luamemzip.dll']={MemoryZip=function()return zip end}
          io.open=function()return {write=function()end,close=function()end} end
          owner_callbacks=require('mapextensions.callbacks')
          invalid_entries=entries
        ''')
        before = self.blocks(h, state)
        cases = {
            b'pending.bin': b'bad',
            b'cooldown.bin': (60001).to_bytes(4, 'little') + handle.files[b'cooldown.bin'][4:],
            b'config': b'changed',
            b'variant-gm.bin': b'\1' + handle.files[b'variant-gm.bin'][1:],
            b'format': b'4',
            b'decoration-uid.bin': None,
        }
        for name, invalid in cases.items():
            with self.subTest(entry=name):
                key = b'projectileModifier/' + name
                saved = g.invalid_entries[key]
                g.invalid_entries[key] = invalid
                try:
                    with self.assertRaises(Exception): g.owner_callbacks.afterReadSav()
                    self.assertEqual(g.other_restores, 0)
                    self.assertEqual(self.blocks(h, state), before)
                finally:
                    g.invalid_entries[key] = saved
        g.owner_callbacks.afterReadSav()
        self.assertEqual(g.other_restores, 1)
        self.assertEqual(self.blocks(h, state), before)


if __name__ == '__main__':
    unittest.main()

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from lupa.lua54 import LuaError
from harness import Harness, ROOT, r
import test_projectiles as projectile_tests


def gm1(count=184,kind=2):
    header=bytearray(5208)
    struct.pack_into('<I',header,12,count);struct.pack_into('<I',header,20,kind)
    pixels=(b'\x00\x01\x80\x80' if kind==2 else b'\x00\xff\x7f\x80')*count
    struct.pack_into('<I',header,80,len(pixels))
    offsets=b''.join(struct.pack('<I',i*4) for i in range(count))
    sizes=struct.pack('<I',4)*count
    images=struct.pack('<HH12x',1,1)*count
    return bytes(header)+offsets+sizes+images+pixels


class SpriteResourcesTests(unittest.TestCase):
    def module(self,h):return h.lua.execute(b"return (require('sprite_resources'))")

    def test_native_sheets_and_malformed_streams(self):
        h=Harness();m=self.module(h)
        root=Path('C:/Program Files (x86)/Steam/steamapps/common/Stronghold Crusader Extreme/gm')
        for gm,sheet in m.sheets.items():
            with self.subTest(gm=gm):
                m.validate_gm1(gm1(sheet[b'count'],sheet[b'kind']),gm)
                m.validate_gm1((root/(sheet[b'name'].decode()+'.gm1')).read_bytes(),gm)
        good=gm1()
        invalid=[good[:5207],good[:-1],good+b'x',gm1(183),gm1(184,1)]
        for off,value in [(5208,0xffffffff),(5208+184*4,0xffffffff),(5208+184*8,0)]:
            b=bytearray(good);struct.pack_into('<I',b,off,value);invalid.append(bytes(b))
        for value in [0xff,0x1f,0x60]:
            b=bytearray(good);b[5208+184*24]=value;invalid.append(bytes(b))
        for b in invalid:
            with self.assertRaises(LuaError):m.validate_gm1(b,34)

    def prepare(self,extreme=False):
        h=Harness(extreme);m=self.module(h)
        (ROOT/'tests/output').mkdir(parents=True,exist_ok=True)
        directory=tempfile.TemporaryDirectory(dir=ROOT/'tests/output')
        self.addCleanup(directory.cleanup)
        asset=Path(directory.name)/'arrow.gm1';asset.write_bytes(gm1())
        path=asset.relative_to(ROOT).as_posix()
        h.lua.globals().sha=h.lua.table_from({b'sha256':lambda b:hashlib.sha256(b).hexdigest().encode()})
        requests=[];callbacks=[]
        h.lua.globals().load_resource=lambda path:1
        h.lua.globals().reserve_resource=lambda base,resource:requests.append((base,resource)) or 0
        h.lua.globals().get_reserved=lambda token:207
        h.lua.globals().register_after=lambda hook,callback:callbacks.append((hook,callback))
        h.lua.execute(b"modules.gmResourceModifier={LoadGm1Resource=function(self,p) return load_resource(p) end, ReserveGm=function(self,b,r) return reserve_resource(b,r) end, GetReservedGm=function(self,t) return get_reserved(t) end}; hooks={registerHookCallback=function(h,f) register_after(h,f) end}")
        def unexpected_hook(*args):raise AssertionError('consumer installed a private resource loader hook')
        h.lua.globals().core.hookCode=unexpected_hook
        config={'projectiles':{'test_arrow':{'inherits':'arrow','sprites':path}},
                'units':{'Catapult':{'projectile':'test_arrow','count':1}}}
        h.module.apply(h.config(config))
        h.v={k:v for _,_,values in h.blobs.values() for k,v in values.items()}
        for owner in range(9):h.put(h.v['TEAMTBL']+owner*4,owner)
        self.assertEqual(requests,[(34,1)])
        self.assertEqual(len(callbacks),1)
        self.assertEqual(callbacks[0][0],b'afterInit')
        self.assertEqual(h.get(h.v['VARIANTGM']+4),0)
        # The owner host suite exercises actual admission and SetGm. This
        # consumer boundary receives the completed owner's stable native ID.
        callbacks[0][1]()
        self.assertEqual(h.get(h.v['VARIANTGM']+4),207)
        state=h.get(h.v['FIREPROJ']+0x416)
        data=bytes(h.uc.mem_read(h.spawner,0x500));offset=data.index(b'\x80\xbc\x01')
        validity=h.get(h.spawner+offset+3)
        for y in range(35,50):
            h.put(h.v['TILEROWS']+12*y,400*y)
            h.uc.mem_write(validity+400*y+35,b'\x01'*15)
        h.unit(1,39);h.put(state+8,25)
        return h,state,config

    def test_native_spawn_selects_variant_and_preserves_simulation_fields(self):
        for extreme in [False,True]:
            with self.subTest(extreme=extreme):
                h,state,config=self.prepare(extreme)
                entity=state+20+25*232
                h.call(h.v['FIREPROJ'],[1,2,352,320,30],{r.UC_X86_REG_ECX:h.v['UNITSTATE']})
                self.assertEqual(h.get(h.v['ENTITYVARIANT']+25*4),1)
                self.assertEqual(h.get(entity+6,2),207)
                before=bytes(h.uc.mem_read(entity,232))
                h.call(h.v['SPRITEALL'],registers={r.UC_X86_REG_EDX:0})
                self.assertEqual(h.get(entity+6,2),34)
                h.call(h.v['SPRITEALL'],registers={r.UC_X86_REG_EDX:1})
                self.assertEqual(bytes(h.uc.mem_read(entity,232)),before)
                # Impact/type changes and reused IDs lose the variant.
                h.put(entity+0x2a,14,2)
                h.call(h.v['SPRITEALL'],registers={r.UC_X86_REG_EDX:1})
                self.assertEqual(h.get(h.v['ENTITYVARIANT']+25*4),0)

    def test_failed_admission_exposes_no_partial_variant_layout(self):
        h=Harness();m=self.module(h);callbacks=[];bound=[];fatal=[];reservations=[]
        h.lua.globals().load_resource=lambda path:1
        h.lua.globals().reserve_resource=lambda base,resource:reservations.append((base,resource)) or len(reservations)-1
        h.lua.globals().get_reserved=lambda token:207 if token==0 else -1
        h.lua.globals().register_after=lambda hook,callback:callbacks.append(callback)
        h.lua.globals().fatal_message=lambda level,message:fatal.append((level,message))
        h.lua.execute(b"FATAL=-3; log=function(l,m) fatal_message(l,m) end; modules.gmResourceModifier={LoadGm1Resource=function(self,p) return load_resource(p) end, ReserveGm=function(self,b,r) return reserve_resource(b,r) end, GetReservedGm=function(self,t) return get_reserved(t) end}; hooks={registerHookCallback=function(h,f) register_after(h,f) end}")
        m.install(h.config([{'gm':34,'path':'a.gm1'},{'gm':135,'path':'b.gm1'}]),lambda asset:bound.append(asset))
        self.assertEqual(bound,[])
        callbacks[0]()
        self.assertEqual(bound,[])
        self.assertEqual(len(fatal),1)
        self.assertEqual(fatal[0][0],-3)
        self.assertEqual(h.writes,[])

    def test_all_inherited_projectile_kinds_select_the_matching_sheet(self):
        for extreme in [False,True]:
            h,state,_=self.prepare(extreme);m=self.module(h)
            constants=h.lua.execute(b"return (require('constants'))")
            entity=state+20+25*232
            for name,kind in constants.projectile_names.items():
                with self.subTest(extreme=extreme,projectile=name):
                    gm=m.projectile_gm[kind];count=m.sheets[gm][b'count']
                    h.put(h.v['VARIANTBASEGM']+4,gm);h.put(h.v['VARIANTCOUNT']+4,count)
                    h.put(h.v['REMAPT']+39*4,kind)
                    h.put(h.v['NATIVESEENT']+4,0);h.put(h.v['ENTITYVARIANT']+25*4,0)
                    h.put(state+8,25);h.uc.mem_write(entity,b'\0'*232)
                    h.call(h.v['FIREPROJ'],[1,2,352,320,30],{r.UC_X86_REG_ECX:h.v['UNITSTATE']})
                    self.assertEqual(h.get(h.v['ENTITYVARIANT']+25*4),1)
                    self.assertEqual(h.get(entity+6,2),207)
                    h.call(h.v['SPRITEALL'],registers={r.UC_X86_REG_EDX:0})
                    self.assertEqual(h.get(entity+6,2),gm)
                    h.call(h.v['SPRITEALL'],registers={r.UC_X86_REG_EDX:1})
                    self.assertEqual(h.get(entity+6,2),207)
    def test_native_flight_is_unchanged_and_saved_variant_continues(self):
        for extreme in [False,True]:
            with self.subTest(extreme=extreme):
                custom,state,_=self.prepare(extreme)
                ordinary,other,_=self.prepare(extreme)
                ordinary.put(ordinary.v['SPRITET']+39*4,0)
                for h,s in [(custom,state),(ordinary,other)]:
                    h.call(h.v['FIREPROJ'],[1,2,352,320,30],{r.UC_X86_REG_ECX:h.v['UNITSTATE']})
                for _ in range(16):
                    snapshots=[]
                    for h,s in [(custom,state),(ordinary,other)]:
                        address=h.blobs['spriteUpdateOriginal'][2]['ENTITYRESUME']-6
                        h.call(address,registers={r.UC_X86_REG_ECX:s})
                        entity=bytearray(h.uc.mem_read(s+20+25*232,232))
                        entity[6:8]=b'\0\0';snapshots.append(entity)
                    self.assertEqual(*snapshots)
                    self.assertEqual(custom.get(state+20+25*232+6,2),207)
                handle=projectile_tests.NativeTests().state_handle(custom)
                saved=custom.sections[b'projectileModifier'];saved.serialize(saved,handle)
                original=bytes(custom.uc.mem_read(state,3000*232+20))
                address=custom.blobs['spriteUpdateOriginal'][2]['ENTITYRESUME']-6
                custom.call(address,registers={r.UC_X86_REG_ECX:state})
                expected=bytes(custom.uc.mem_read(state+20+25*232,232))
                custom.uc.mem_write(state,original);saved.deserialize(saved,handle)
                custom.call(address,registers={r.UC_X86_REG_ECX:state})
                self.assertEqual(bytes(custom.uc.mem_read(state+20+25*232,232)),expected)

    def test_saved_sprite_layout_rejects_conflicts(self):
        h,state,config=self.prepare()
        observer=projectile_tests.NativeTests();handle=observer.state_handle(h)
        saved=h.sections[b'projectileModifier'];saved.serialize(saved,handle)
        saved.initialize(saved)
        self.assertEqual(h.get(h.v['VARIANTGM']+4),207)
        h.put(h.v['VARIANTGM']+4,208)
        with self.assertRaisesRegex(LuaError,'graphics-slot layout'):saved.deserialize(saved,handle)

"""Production Lua + FASM + isolated x86 execution against reference PE images."""
from pathlib import Path
import os
import re
import struct
import subprocess
import tempfile
import pefile
from lupa.lua54 import LuaRuntime
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as r

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = Path(os.environ.get('SHC_REFERENCE_DIR', 'C:/UCPTools/Original-SHC141'))
FASM = Path(os.environ.get('FASM', 'C:/UCPTools/fasm-1.73.35/FASM.EXE'))

class Harness:
    def __init__(self, extreme=False):
        self.path = ORIGINAL / ('Stronghold_Crusader_Extreme.exe' if extreme else 'Stronghold Crusader.exe')
        pe = pefile.PE(str(self.path))
        self.image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(0x400000, 0x4000000)
        self.uc.mem_write(0x400000, self.image)
        self.uc.mem_map(0x5000000, 0x400000)
        self.cursor = 0x5000000
        self.allocations = []
        self.lua = LuaRuntime(unpack_returned_tuples=True, encoding=None)
        self.writes, self.blobs, self.scans = [], {}, []
        self.sections = {}
        g = self.lua.globals()
        g.ROOT = str(ROOT).replace('\\','/').encode()
        self.lua.execute(b"package.path=ROOT..'/?.lua;'..package.path; INFO=1; WARNING=2; ERROR=3; log=function() end; table.find=function(t,v) for i,x in ipairs(t) do if v==x then return i end end end")
        g.extreme = extreme
        self.lua.execute(b'data={version={isExtreme=function() return extreme end}}; core={}; modules={}; yaml={}; modules["map-extensions"]={registerSection=function(self,n,s) register(n,s) end}')
        g.register = lambda n,s: self.sections.__setitem__(n,s)
        c = g.core
        c.scanForAOB = self.scan
        # Match UCP's signed native int/short API, including opcode bit patterns.
        c.readInteger = lambda a: int.from_bytes(self.uc.mem_read(a,4),'little',signed=True)
        c.readSmallInteger = lambda a: int.from_bytes(self.uc.mem_read(a,2),'little',signed=True)
        c.readByte = lambda a: self.get(a,1)
        c.readString = lambda a,n: bytes(self.uc.mem_read(a,n))
        c.readBytes = lambda a,n: self.lua.table_from(list(self.uc.mem_read(a,n)))
        c.allocate = self.allocate
        c.allocateAssembly = self.assemble
        c.writeInteger = lambda a,v: self.put(a,v)
        c.writeSmallInteger = lambda a,v: self.put(a,v,2)
        c.writeByte = lambda a,v: self.put(a,v,1)
        c.writeCode = self.write_code
        c.writeBytes = lambda a,v: self.uc.mem_write(a,bytes(v.values()))
        c.setMemory = lambda a,v,n: self.uc.mem_write(a,bytes([v])*n)
        c.itob = lambda v: self.lua.table_from(list(struct.pack('<I', v & 0xffffffff)))
        c.getRelativeAddress = lambda a,b,o=0: b-a+o
        self.module = self.lua.execute(b"return require('init')")[0]
        self.base = 0x145D03C if extreme else 0x138854C
        self.spawner = 0x404af0 if extreme else 0x404ae0

    def scan(self, pattern, start=0x400000, end=0x700000):
        parts=pattern.decode().split()
        regex=b''.join(b'.' if p=='?' else re.escape(bytes([int(p,16)])) for p in parts)
        # Live bytes make conflicts and repeat installation visible.
        matches=list(re.finditer(regex,bytes(self.uc.mem_read(start,end-start)),re.DOTALL))
        self.scans.append(pattern)
        if not matches: raise RuntimeError('AOB missing: '+pattern.decode())
        return start+matches[0].start()

    def allocate(self, size, zero=True):
        a=self.cursor; self.cursor=(a+size+15)&~15
        self.allocations.append((a,size))
        assert self.cursor < 0x5300000
        self.uc.mem_write(a,b'\0'*size)
        return a

    def get(self,a,size=4): return int.from_bytes(self.uc.mem_read(a,size),'little')
    def put(self,a,v,size=4): self.uc.mem_write(a,(int(v)&((1<<(size*8))-1)).to_bytes(size,'little'))
    def write_code(self,a,values):
        def flat(t):
            for x in t.values():
                if isinstance(x,(int,float)): yield int(x)
                else: yield from flat(x)
        code=bytes(flat(values)); self.writes.append((a,code)); self.uc.mem_write(a,code)

    def assemble(self, source, values):
        address=self.allocate(0x4000)
        constants={k.decode():int(v) for k,v in values.items()}
        script='use32\norg '+hex(address)+'\n'
        script+='\n'.join(k+' = '+hex(v & 0xffffffff) for k,v in constants.items())+'\n'+source.decode()
        with tempfile.TemporaryDirectory() as directory:
            src=Path(directory)/'code.asm'; out=Path(directory)/'code.bin'
            src.write_text(script)
            # Framework uses 64,000 bytes; 62 KiB is a slightly tighter budget.
            result=subprocess.run([str(FASM),'-m','62',str(src),str(out)],capture_output=True,text=True)
            if result.returncode: raise RuntimeError(source.decode().splitlines()[1]+'\n'+result.stdout+result.stderr)
            code=out.read_bytes()
        assert len(code) < 0x4000
        self.uc.mem_write(address,code)
        name=next((s.strip()[:-1] for s in source.decode().splitlines() if s.strip().endswith(':')), 'hook')
        self.blobs[name]=(address,code,constants)
        return address

    def config(self, obj):
        if isinstance(obj,dict): return self.lua.table_from({k.encode():self.config(v) for k,v in obj.items()})
        if isinstance(obj,list): return self.lua.table_from([self.config(v) for v in obj])
        if isinstance(obj,str): return obj.encode()
        return obj

    def enable(self, units):
        # Native behavior tests use the programmatic API. File-loading tests
        # exercise namespace.enable separately with the real preset contents.
        self.module.apply(self.config({'units':units}))

    def call(self,address,args=(),registers=None,stop=None,callbacks=None):
        stack=0x53f0000
        self.put(stack,0x53ff000)
        for i,arg in enumerate(args): self.put(stack+4+4*i,arg)
        for reg,value in [(r.UC_X86_REG_ESP,stack),(r.UC_X86_REG_EFLAGS,0x202)]: self.uc.reg_write(reg,value)
        for reg,value in (registers or {}).items(): self.uc.reg_write(reg,value)
        reached=[]
        def hook(uc,ip,size,_):
            if ip == (stop or 0x53ff000): reached.append(ip); uc.emu_stop()
            elif callbacks and ip in callbacks: callbacks[ip](self)
        # Observe only the requested boundaries. A global instruction hook made
        # long native animation/target scans spend most of their time in Python.
        points={(stop or 0x53ff000), *(callbacks or {}).keys()}
        tokens=[self.uc.hook_add(UC_HOOK_CODE,hook,begin=ip,end=ip) for ip in points]
        try: self.uc.emu_start(address,0,count=8000000)
        finally:
            for token in tokens: self.uc.hook_del(token)
        assert reached, 'instruction budget exceeded'
        return self.uc.reg_read(r.UC_X86_REG_EAX)

    def unit(self,id,kind,owner=1,x=40,y=40,uid=None):
        a=self.base+id*0x490
        self.uc.mem_write(a,b'\0'*0x490)
        for off,v,size in [(0x8c,2,2),(0x8e,kind,2),(0x96,owner,2),(0x98,uid or id,4),
                           (0xc4,x,2),(0xc6,y,2),(0xb6,x*8,2),(0xb8,y*8,2),(0x3c8,1000,4)]: self.put(a+off,v,size)
        return a

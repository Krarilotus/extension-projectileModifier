"""Read-only signature and disassembly report for the licensed reference images."""
from pathlib import Path
import re
import hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = Path('C:/UCPTools/Original-SHC141')

def matches(image, pattern):
    pattern = b''.join(b'.' if x == '?' else re.escape(bytes([int(x,16)])) for x in pattern.split())
    return [m.start()+0x400000 for m in re.finditer(pattern, image, re.DOTALL)]

if __name__ == '__main__':
    source = (ROOT/'init.lua').read_text()
    patterns = re.findall(r'locate\(\s*"([0-9A-F? ]+)"', source)
    for path in ORIGINAL.glob('*.exe'):
        pe = pefile.PE(str(path)); image = pe.get_memory_mapped_image()
        print(path.name, hashlib.sha256(path.read_bytes()).hexdigest())
        for pattern in patterns:
            hits = matches(image, pattern)
            print(pattern, [hex(x) for x in hits])
            if hits and (pattern.startswith('53 56') or pattern.startswith('83 C2')):
                address = hits[0]
                for ins in Cs(CS_ARCH_X86, CS_MODE_32).disasm(image[address-0x400000-40:address-0x400000+80], address-40):
                    print(f'  {ins.address:08x} {ins.mnemonic} {ins.op_str}')

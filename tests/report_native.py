"""Record code sizes and fixture hashes without shipping licensed executable data."""
import hashlib
import json
from harness import Harness, ROOT

report=[]
for extreme in [False,True]:
    h=Harness(extreme)
    h.enable({'Catapult':{'projectile':'mangonel_pebble','count':3},
              'Siege tower':{'interval':50,'count':2}})
    report.append(dict(executable=h.path.name,sha256=hashlib.sha256(h.path.read_bytes()).hexdigest(),
        data_bytes=h.allocations[0][1],code_bytes=sum(len(v[1]) for v in h.blobs.values()),
        routines={k:len(v[1]) for k,v in h.blobs.items()},
        hooks=[dict(address=hex(a),bytes=b.hex()) for a,b in h.writes],
        assembler='FASM 1.73.35',assembler_budget_bytes=62*1024))
destination=ROOT/'tests/output'; destination.mkdir(exist_ok=True)
(destination/'native-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))

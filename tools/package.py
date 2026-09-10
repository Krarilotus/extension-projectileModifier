"""Build a deterministic, unsigned UCP module archive with an explicit file list."""
from pathlib import Path
import hashlib
import zipfile
import json
import xml.etree.ElementTree as ET
import yaml
from generate_options import LANGUAGES, generate
from generate_schema import build_schema
from generate_vanilla import generate as generate_vanilla

ROOT=Path(__file__).resolve().parents[1]
definition=yaml.safe_load((ROOT/'definition.yml').read_text(encoding='utf-8'))
generate()  # Reject missing/stale localization before building.
generate_vanilla()
(ROOT/'projectile-config.schema.json').write_text(
    json.dumps(build_schema(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
files=['definition.yml','options.yml','init.lua','addresses.lua','constants.lua',
       'templates.lua','cadence.lua','mounted.lua','hunter.lua','configuration.lua','state.lua','example-projectiles.yml',
       'sprite_resources.lua','sprite_runtime.lua',
       'decorations.lua','decoration_runtime.lua','decoration_ui.lua','ui/decorations.lua',
       'all-settings-reference.yml','README.md','CHANGELOG.md','VALIDATION.md','IMPLEMENTATION-TODO.md',
       'projectile-config.schema.json','GUI-AUDIT.md','vanilla-projectiles.yml',
       'examples/ucp-plugin-required.yml','examples/ucp-plugin-suggested.yml',
       'examples/ucp-plugin-unspecified.yml']
files.append('examples/custom-sprites-and-decorations.yml')
for lang in LANGUAGES:
    files.extend([f'locale/{lang}.yml', f'locale/description-{lang}.md'])

# Keep the store's standard manifest and the development archive in agreement.
store_files=set()
for entry in ET.parse(ROOT/'files.xml').findall('./files/file'):
    source=ROOT/entry.attrib['src']
    assert entry.attrib.get('target','.')=='.'
    if source.is_dir():
        store_files.update(p.relative_to(ROOT).as_posix() for p in source.rglob('*') if p.is_file())
    else:
        store_files.add(source.relative_to(ROOT).as_posix())
assert store_files==set(files), 'Store manifest and development package differ'
destination=ROOT/'dist'; destination.mkdir(exist_ok=True)
archive=destination/(definition['name']+'-'+definition['version']+'.zip')
directories=sorted({parent.as_posix()+'/' for name in files
                    for parent in Path(name).parents if parent != Path('.')})
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    # UCP's readLocales first asks whether the exact ZIP entry 'locale/' exists.
    # Files under that prefix do not satisfy Rust ZipArchive.by_name('locale/').
    for name in directories:
        info=zipfile.ZipInfo(name,(2026,9,10,0,0,0))
        info.external_attr=(0o40755<<16)|0x10
        z.writestr(info,b'')
    for name in sorted(files):
        info=zipfile.ZipInfo(name,(2026,9,10,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        z.writestr(info,(ROOT/name).read_bytes())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert sorted(z.namelist())==sorted(files+directories)
    assert z.getinfo('locale/').is_dir()
    assert yaml.safe_load(z.read('definition.yml'))==definition
checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(checksum+'  '+archive.name+'\n',encoding='ascii')
print(str(archive)); print(checksum); print(f'{len(files)} files, {len(directories)} directories; {archive.stat().st_size} bytes')

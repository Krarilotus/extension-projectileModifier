"""Generate the single standard UCP file picker; catalogs live in locale/*.yml."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
import yaml
import re

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('de', 'en', 'fr', 'ru', 'hu', 'tr', 'ch', 'es', 'fa')
lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().root = ROOT.as_posix()
lua.execute("package.path=root..'/?.lua;'..package.path")
cfg = lua.execute("return (require('configuration'))")
constants = lua.execute("return (require('constants'))")

def build_options():
    return [dict(name='projectile_config_file_selector', category=['{{balance_changes}}'],
                 display='FileInput', text='{{config_file}}', tooltip='{{config_help}}',
                 url='projectileModifier.projectile_config_file_selector',
                 contents=dict(type='string', value='', filter='files', generalizeExtensionPaths=True))]

def generate():
    document=yaml.safe_dump(dict(meta=dict(version='1.0.0'), options=build_options()),
                            allow_unicode=True, sort_keys=False, width=110)
    keys=set(re.findall(r'\{\{([^}]+)\}\}', document))
    for lang in LANGUAGES:
        locale=yaml.safe_load((ROOT/'locale'/f'{lang}.yml').read_text(encoding='utf-8'))
        if set(locale)!=keys or any(not isinstance(v,str) or not v.strip() for v in locale.values()):
            raise ValueError(f'{lang}: missing={keys-set(locale)}, obsolete={set(locale)-keys}')
    (ROOT/'options.yml').write_text(document,encoding='utf-8',newline='\n')
    print(f'One file picker; {len(keys)} UI strings in {len(LANGUAGES)} languages.')

if __name__ == '__main__':
    generate()

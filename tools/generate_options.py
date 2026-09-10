"""Generate compact stock UCP controls; translations are maintained in locale/*.yml."""
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

def token(key):
    return '{{' + key + '}}'

def group(name, header, children, **kwargs):
    return dict(name=name, display='GroupBox', header=token(header),
                accordion=dict(enabled=True), children=children, **kwargs)

def choice(key, url, choices):
    return dict(name=url.replace('.', '_'), display='Choice', text=token(key),
                tooltip=token(key+'_descr'), url=url,
                contents=dict(type='string', value='inherit', choices=[
                    dict(name=v, text=token(t)) for v, t in [('inherit', 'inherit')]+choices]))

def slider(key, url):
    limits = cfg.numbers[key]
    return dict(name=url.replace('.', '_'), display='UCP2Slider', header=token(key),
                text=token(key+'_descr'), hasHeader=True, url=url,
                contents=dict(min=limits[1], max=limits[2], step=1, decimals=0,
                              value=dict(enabled=False, sliderValue=limits[3])))

def build_options():
    families = {key: [] for key in ['siege', 'european', 'arabian', 'civilian', 'wildlife']}
    projectiles = sorted(constants.projectile_names.items(), key=lambda p: p[1])
    for unit_id, name in sorted(constants.unit_names.items()):
        slug = re.sub('[^a-z0-9]+', '_', name.lower())
        family = 'civilian'
        if unit_id in [39, 40, 41, 50, 58, 59, 60, 61, 77]: family = 'siege'
        elif 70 <= unit_id <= 76: family = 'arabian'
        elif 22 <= unit_id <= 30 or unit_id in [5, 37, 55]: family = 'european'
        elif unit_id in [2, 38, 43, 44, 45, 46, 47, 48, 49, 51, 52, 54, 62, 67, 68, 69]: family = 'wildlife'
        prefix = 'projectileModifier.customizations.'+slug+'.'
        controls = [choice('projectile', prefix+'projectile', [(p, 'p_'+p) for p, _ in projectiles]),
                    slider('count', prefix+'count'), slider('interval', prefix+'interval'),
                    slider('range', prefix+'range'),
                    choice('targets', prefix+'targets', [(x, x) for x in [
                        'units', 'units_buildings', 'fortifications', 'buildings', 'siege_towers', 'cluster', 'walls']]),
                    slider('spread_tiles', prefix+'spread_tiles')]
        if unit_id in [39, 40, 58, 59, 77]:
            controls.append(slider('require_manned', prefix+'require_manned'))
        families[family].append(group(slug, 'unit_'+slug, controls))
    picker = dict(name='projectile_config_file_selector', display='FileInput',
                  header=token('projectile_config_file_selector'),
                  text=token('projectile_config_file_selector_descr'),
                  url='projectileModifier.projectile_config_file_selector',
                  contents=dict(generalizeExtensionPaths=True, filter='files', type='string', value=''))
    children = [group('projectile_presets', 'advanced', [picker])]
    children += [group('projectile_'+family, family, units) for family, units in families.items()]
    return [group('projectile_settings', 'projectiles', children,
                  category=[token('balance_changes')], text=token('unit_description'))]

def generate():
    document = yaml.safe_dump(dict(meta=dict(version='1.0.0'), options=build_options()),
                              allow_unicode=True, sort_keys=False, width=110)
    keys = set(re.findall(r'\{\{([^}]+)\}\}', document))
    for lang in LANGUAGES:
        path = ROOT/'locale'/f'{lang}.yml'
        locale = yaml.safe_load(path.read_text(encoding='utf-8'))
        if set(locale) != keys or any(not isinstance(v, str) or not v.strip() for v in locale.values()):
            raise ValueError(f'{lang}: missing={keys-set(locale)}, obsolete={set(locale)-keys}')
    (ROOT/'options.yml').write_text(document, encoding='utf-8')
    print(f'77 units, 467 unit settings, 1 category entry; {len(keys)} strings in {len(LANGUAGES)} languages.')

if __name__ == '__main__':
    generate()

"""Generate editor validation for YAML presets from Lua bounds, without defaults."""
import json
from generate_options import ROOT, cfg, constants

def build_schema():
    fields = {name: dict(type='integer', minimum=bounds[1], maximum=bounds[2])
              for name, bounds in sorted(cfg.numbers.items())}
    fields['require_manned'] = dict(anyOf=[fields['require_manned'], dict(type='boolean')])
    fields.update({name: dict(type='boolean') for name in sorted(cfg.booleans.keys())})
    fields['projectile'] = dict(enum=[name for name, _ in sorted(constants.projectile_names.items())]
                               + sorted(constants.projectile_names.values()))
    target = dict(type='string', enum=sorted(constants.target_kinds.keys()))
    fields['targets'] = dict(oneOf=[target, dict(type='array', items=target,
                                               minItems=1, maxItems=4, uniqueItems=True)])
    fields['stagger_min']['description'] = 'Requires stagger_max; must not exceed it when staggering is enabled. Checked by the game loader.'
    unit = dict(type='object', additionalProperties=False, properties=fields,
                dependentRequired={name: ['interval'] for name in
                                   ['interval_moving', 'interval_standing', 'attached_interval', 'stagger_max']},
                allOf=[{'not': dict(required=[name, name+'_tiles'])} for name in ['spread', 'inaccuracy']])
    unit['dependentRequired']['stagger_min'] = ['stagger_max']
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            'title': 'Projectile Modifier preset', 'type': 'object', 'additionalProperties': False,
            'description': 'Optional advanced preset. Enabled GUI overrides are applied before runtime validation. See README.md for the full settings table.',
            'properties': {'units': {'type': 'object', 'additionalProperties': False,
                          'properties': {name: {'$ref': '#/$defs/unit'} for _, name in sorted(constants.unit_names.items())}}},
            '$defs': {'unit': unit}}

if __name__ == '__main__':
    (ROOT/'projectile-config.schema.json').write_text(
        json.dumps(build_schema(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

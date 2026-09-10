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
    fields['cow_projectile'] = dict(fields['projectile'], description='Separate replacement for native siege cow ammunition and automatic AI cow shots. Omission preserves cows.')
    fields['inaccuracy']['description'] = 'Maximum random aim-error radius in whole native coordinate units: 1 = 1/8 tile, 8 = 1 tile. Explicit 0 removes native random error; omission preserves it. Separate spread still applies. Do not combine with inaccuracy_tiles.'
    fields['inaccuracy_tiles']['description'] = 'Compatibility alias in whole tiles, converted by multiplying by 8. Prefer inaccuracy for native 1/8-tile steps. Do not combine both fields.'
    fields['spread']['description'] = 'Additional simultaneous-shot spread per axis, in whole native coordinate units: 1 = 1/8 tile, 8 = 1 tile. Zero adds no spread. Independent of inaccuracy.'
    fields['spread_tiles']['description'] = 'Compatibility alias in whole tiles, converted by multiplying by 8. Prefer spread for native 1/8-tile steps. Do not combine both fields.'
    target = dict(type='string', enum=sorted(constants.target_kinds.keys()))
    fields['targets'] = dict(oneOf=[target, dict(type='array', items=target,
                                               minItems=1, maxItems=4, uniqueItems=True)])
    fields['stagger_min']['description'] = 'Requires stagger_max; must not exceed it when staggering is enabled. Checked by the game loader.'
    fields['interval']['description'] = 'Optional fallback automatic-fire interval in simulation ticks. Applies only where no state interval overrides it.'
    fields['interval_moving']['description'] = 'Enables firing while moving; 0 holds fire. If omitted, use interval, or hold fire if neither is set.'
    fields['interval_standing']['description'] = 'Enables firing while stopped, not specifically docked; 0 holds fire. If omitted, use interval, or hold fire if neither is set.'
    fields['attached_interval']['description'] = 'Enables firing for a siege tower docked to a wall, overriding moving/standing intervals; 0 holds fire. Omission keeps the current moving/standing rate or fallback.'
    unit = dict(type='object', additionalProperties=False, properties=fields,
                dependentSchemas={'stagger_max': {'anyOf': [{'required': [name]} for name in
                                  ['interval', 'interval_moving', 'interval_standing', 'attached_interval']]}},
                allOf=[{'not': dict(required=[name, name+'_tiles'])} for name in ['spread', 'inaccuracy']])
    unit['dependentRequired'] = {'stagger_min': ['stagger_max']}
    override = dict(type='object', additionalProperties=False, properties=dict(fields),
                    description='Sparse overrides while on a wall or fortification. Missing fields inherit the ground settings. Runtime validates the merged settings.',
                    allOf=[{'not': dict(required=[name, name+'_tiles'])} for name in ['spread', 'inaccuracy']])
    fields['on_fortification'] = {'$ref': '#/$defs/override'}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            'title': 'Custom Projectiles preset', 'type': 'object', 'additionalProperties': False,
            'description': 'Projectile preset. All unit entries and settings are optional; omitted settings preserve native behavior or documented automatic-fire defaults. UCP required/suggested qualifiers apply to the file selector, not fields inside this file. See README.md.',
            'properties': {'units': {'type': 'object', 'additionalProperties': False,
                          'properties': {name: {'$ref': '#/$defs/unit'} for _, name in sorted(constants.unit_names.items())}}},
            '$defs': {'unit': unit, 'override': override}}

if __name__ == '__main__':
    (ROOT/'projectile-config.schema.json').write_text(
        json.dumps(build_schema(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

"""Generate editor validation for YAML presets from Lua bounds, without defaults."""
import json
from generate_options import ROOT, cfg, constants

def build_schema():
    fields = {name: dict(type='integer', minimum=bounds[1], maximum=bounds[2])
              for name, bounds in sorted(cfg.numbers.items())}
    fields['require_manned'] = dict(anyOf=[fields['require_manned'], dict(type='boolean')])
    fields['require_manned']['description'] = 'Engineers currently aboard. Native reload defaults: trebuchet 3, other supported siege engines 2. Independent timer defaults 0. Explicit true means 1; false or 0 allows unmanned fire.'
    fields.update({name: dict(type='boolean') for name in sorted(cfg.booleans.keys())})
    native_projectiles=[name for name, _ in sorted(constants.projectile_names.items())]
    fields['projectile'] = dict(anyOf=[dict(enum=native_projectiles+sorted(constants.projectile_names.values())),
        dict(type='string',pattern='^[a-z][a-z0-9_-]{0,47}$')],
        description='Native projectile or a name defined in projectiles. The game loader rejects undefined variant names.')
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
    fields['sync_to_animation']['description'] = 'Defaults to native firing-frame timing for catapult, trebuchet, mangonel, both ballistas, European/Arabian archers, horse archers, crossbowmen, slingers, firethrowers and hunters. Reload while waiting; never truncate the animation. Horse archers keep an independent bow clock while moving. Configured hunter shots use the native bow animation and retain other work states. False selects the independent timer. Other units default false; true uses the legacy bounded animation wait.'
    fields['sync_max_wait']['description'] = 'Legacy animation wait only; never bypasses a native reload firing frame.'
    fields['suppress_default']['description'] = 'Defaults true with an interval. False combines native and automatic shots only in independent timer mode; it cannot bypass native reload timing. Unchanged cow orders remain available.'
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
    rule = dict(type='object',additionalProperties=False,required=['decoration'],minProperties=2,
                properties=dict(override['properties'],decoration={'type':'string','pattern':'^[a-z][a-z0-9_-]{0,47}$'}),
                allOf=override['allOf'],
                description='First matching rule wins within the native brazier 3-tile square and height difference below 45. Sparse fields apply after fortification overrides. Names must exist in decorations.')
    fields['on_fortification'] = {'$ref': '#/$defs/override'}
    fields['near_decorations'] = dict(type='array',maxItems=33,items={'$ref':'#/$defs/decorationRule'})
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            'title': 'Custom Projectiles preset', 'type': 'object', 'additionalProperties': False,
            'description': 'Projectile preset. All unit entries and settings are optional; omitted settings preserve native behavior or documented automatic-fire defaults. UCP required/suggested qualifiers apply to the file selector, not fields inside this file. See README.md.',
            'properties': {'decorations': {'type':'object','maxProperties':33,'additionalProperties':False,
                          'patternProperties':{'^[a-z][a-z0-9_-]{0,47}$':{'type':'object','additionalProperties':False,
                              'properties':{'label':{'type':'string','minLength':1,'maxLength':96},
                                  'sprites':{'type':'string','minLength':5,'maxLength':240,'pattern':'\\.[gG][mM]1$',
                                      'description':'Optional complete body_brazier sheet: 8 images, GM1 type 6. Omission uses native brazier graphics. Build from the brazier button.'}}}}},
                          'projectiles': {'type':'object','maxProperties':33,'additionalProperties':False,
                          'propertyNames':{'not':{'enum':native_projectiles}},
                          'patternProperties':{'^[a-z][a-z0-9_-]{0,47}$':{'type':'object','additionalProperties':False,
                              'required':['inherits','sprites'],'properties':{
                                  'inherits':{'enum':native_projectiles},
                                  'sprites':{'type':'string','minLength':5,'maxLength':240,'pattern':'\\.[gG][mM]1$',
                                      'description':'GM1 path relative to the game folder. Use a complete matching base sheet; see README for counts and formats.'}}}}},
                          'units': {'type': 'object', 'additionalProperties': False,
                          'properties': {name: {'$ref': '#/$defs/unit'} for _, name in sorted(constants.unit_names.items())}}},
            '$defs': {'unit': unit, 'override': override, 'decorationRule':rule}}

if __name__ == '__main__':
    (ROOT/'projectile-config.schema.json').write_text(
        json.dumps(build_schema(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

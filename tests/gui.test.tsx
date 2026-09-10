import React from 'react';
import { readFileSync } from 'node:fs';
import { parse } from 'yaml';
import { expect, test, vi } from 'vitest';
import { atom, createStore, Provider } from 'jotai';
import { render, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { changeLocale } from '../../UCP3-GUI-extension-dependents/src/function/extensions/locale/locale';

// Render the actual launcher controls. Only application-wide state and native
// host integrations are replaced; selectors, sliders and localization are real.
vi.mock('../../UCP3-GUI-extension-dependents/src/function/configuration/state', async () => {
  const { atom } = await import('jotai');
  const reducer = () => {
    const data = atom({});
    return atom(get => get(data), (get,set,action:any) => set(data,{...get(data),...action.value}));
  };
  return Object.fromEntries(['FULL','USER','WARNINGS','TOUCHED'].map(k=>['CONFIGURATION_'+k+'_REDUCER_ATOM',reducer()]));
});
vi.mock('../../UCP3-GUI-extension-dependents/src/function/configuration/derived-state', async () => {
  const { atom } = await import('jotai');
  return Object.fromEntries(['DEFAULTS','LOCKS','SUGGESTIONS'].map(k=>['CONFIGURATION_'+k+'_REDUCER_ATOM',atom({})]));
});
vi.mock('../../UCP3-GUI-extension-dependents/src/components/footer/footer', async () => ({STATUS_BAR_MESSAGE_ATOM:(await import('jotai')).atom(undefined)}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/popover/ConfigPopover',()=>({ConfigPopover:()=>null}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/specified/SpecifiedStyle',()=>({createSpecifiedStyleIfSpecifiedAndTouched:()=>''}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/QualifierControl',()=>({default:()=>null}));
// Limit the factory to the stock views used here; avoid unrelated sandbox/host imports.
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/CreateUIElement',()=>({default:(args:any)=> {
  if(args.spec.display==='GroupBox') return <CreateGroupBox {...args}/>;
  if(args.spec.display==='Choice') return <CreateChoice {...args}/>;
  if(args.spec.display==='UCP2Slider') return <CreateUCP2Slider {...args}/>;
  throw new Error('Unexpected test view '+args.spec.display);
}}));
import CreateChoice from '../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/CreateChoice';
import CreateUCP2Slider from '../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/CreateUCP2Slider';
import CreateGroupBox from '../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/CreateGroupBox';
import { optionEntriesToHierarchical } from '../../UCP3-GUI-extension-dependents/src/config/ucp/extension-util';
import { CONFIGURATION_FULL_REDUCER_ATOM } from '../../UCP3-GUI-extension-dependents/src/function/configuration/state';
import { CONFIGURATION_DEFAULTS_REDUCER_ATOM } from '../../UCP3-GUI-extension-dependents/src/function/configuration/derived-state';

const options=parse(readFileSync('options.yml','utf8')).options;
const languages=Object.keys(parse(readFileSync('../UCP3-GUI/resources/lang/languages.yaml','utf8')));
function flatten(nodes:any[]):any[] { return nodes.flatMap(x=>[x,...flatten(x.children??[])]); }
for(const lang of languages) {
  test('native controls localize and edit catapult and tower settings in '+lang,()=>{
    const locale=parse(readFileSync('locale/'+lang+'.yml','utf8'));
    const localized=changeLocale(locale,options) as any[];
    expect(JSON.stringify(localized)).not.toContain('{{');
    const cat=flatten(localized).find(x=>x.name==='catapult').children;
    const tower=flatten(localized).find(x=>x.name==='siege_tower').children;
    const store=createStore();
    const specs=[cat[0],cat[1],tower[2]];
    const defaults=Object.fromEntries(specs.map(x=>[x.url,x.contents.value]));
    store.set(CONFIGURATION_DEFAULTS_REDUCER_ATOM as any,defaults);
    store.set(CONFIGURATION_FULL_REDUCER_ATOM,{type:'set-multiple',value:defaults});
    const rendered=render(<Provider store={store}><CreateChoice spec={cat[0]} disabled={false} className=""/><CreateUCP2Slider spec={cat[1]} disabled={false} className=""/><CreateUCP2Slider spec={tower[2]} disabled={false} className=""/></Provider>);
    const choice=rendered.getByLabelText(locale.projectile) as HTMLSelectElement;
    fireEvent.change(choice,{target:{value:'mangonel_pebble'}});
    expect(store.get(CONFIGURATION_FULL_REDUCER_ATOM)[cat[0].url]).toBe('mangonel_pebble');
    expect(choice.className).toContain('form-control');
    expect(rendered.getByText(locale.count)).toBeTruthy();
    expect(rendered.getByText(locale.interval)).toBeTruthy();
    const checkbox=rendered.container.querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(checkbox.checked).toBe(false);
    expect(checkbox.closest('.sword-checkbox')).not.toBeNull();
    const help=rendered.getByText(locale.count_descr).closest('.accordion-collapse');
    expect(help).not.toBeNull();
    expect(help!.classList.contains('show')).toBe(false);
    fireEvent.click(checkbox);
    expect((store.get(CONFIGURATION_FULL_REDUCER_ATOM)[cat[1].url] as any).enabled).toBe(true);
    const number=rendered.container.querySelector('[id="'+cat[1].url+'-input"]') as HTMLInputElement;
    fireEvent.change(number,{target:{value:'3'}});
    expect((store.get(CONFIGURATION_FULL_REDUCER_ATOM)[cat[1].url] as any).sliderValue).toBe(3);
    cleanup();
  });
  test('nested sections start collapsed and merge with Legacy in '+lang,async()=>{
    const locale=parse(readFileSync('locale/'+lang+'.yml','utf8'));
    const localized=changeLocale(locale,options) as any[];
    const legacy=parse(readFileSync('../extension-ucp2-legacy/options.yml','utf8')).options;
    const english=parse(readFileSync('../extension-ucp2-legacy/locale/en.yml','utf8'));
    let translated={};
    try { translated=parse(readFileSync('../extension-ucp2-legacy/locale/'+lang+'.yml','utf8')); } catch {}
    const legacyLocalized=changeLocale({...english,...translated},legacy) as any[];
    const before=optionEntriesToHierarchical(legacyLocalized);
    const after=optionEntriesToHierarchical([...legacyLocalized,...localized]);
    expect(Object.keys(after.sections)).toEqual(Object.keys(before.sections));
    expect(after.sections[locale.balance_changes].elements).toContain(localized[0]);
    const root=localized[0];
    const family=root.children.find((x:any)=>x.name==='projectile_siege');
    const cat=family.children.find((x:any)=>x.name==='catapult');
    // Exercise the real recursive accordion path with one representative leaf.
    const spec={...root,children:[{...family,children:[{...cat,children:[]}]}]};
    const rendered=render(<CreateGroupBox spec={spec} disabled={false} className=""/>);
    for(const label of [locale.projectiles,locale.siege,locale.unit_catapult]) {
      const button=rendered.getByRole('button',{name:label});
      expect(button.getAttribute('aria-expanded')).toBe('false');
      fireEvent.click(button);
      await waitFor(()=>expect(button.getAttribute('aria-expanded')).toBe('true'));
    }
    expect(rendered.getByText(locale.unit_description).closest('.accordion-collapse')!.classList.contains('show')).toBe(true);
    cleanup();
  });
}

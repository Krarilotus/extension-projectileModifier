import React from 'react';
import { readFileSync } from 'node:fs';
import { parse } from 'yaml';
import { expect, test, vi, afterEach } from 'vitest';
import { createStore, Provider } from 'jotai';
import { render, fireEvent, cleanup, waitFor } from '@testing-library/react';

vi.mock('../../UCP3-GUI-extension-dependents/src/function/configuration/state',async()=>{
  const {atom}=await import('jotai');
  const reducer=()=>{const state=atom({}); return atom(get=>get(state),(get,set,a:any)=>{
    const next={...get(state)}; if(a.type==='clear-key') delete next[a.key]; else Object.assign(next,a.value); set(state,next);
  });};
  return Object.fromEntries(['FULL','USER','WARNINGS','TOUCHED','QUALIFIER'].map(k=>['CONFIGURATION_'+k+'_REDUCER_ATOM',reducer()]));
});
vi.mock('../../UCP3-GUI-extension-dependents/src/function/configuration/derived-state',async()=>{
  const {atom}=await import('jotai');
  return Object.fromEntries(['DEFAULTS','LOCKS','SUGGESTIONS'].map(k=>['CONFIGURATION_'+k+'_REDUCER_ATOM',atom({})]));
});
vi.mock('../../UCP3-GUI-extension-dependents/src/function/gui-settings/settings',async()=>({CREATOR_MODE_ATOM:(await import('jotai')).atom(true)}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/footer/footer',async()=>({STATUS_BAR_MESSAGE_ATOM:(await import('jotai')).atom(undefined)}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/common/buttons/config-serialized-state',async()=>({CONFIG_EXTENSIONS_DIRTY_STATE_ATOM:(await import('jotai')).atom(false)}));
vi.mock('../../UCP3-GUI-extension-dependents/src/function/game-folder/utils',()=>({useCurrentGameFolder:()=> 'C:/Game'}));
vi.mock('../../UCP3-GUI-extension-dependents/src/function/extensions/state/focus',async()=>({ACTIVE_EXTENSIONS_FULL_ATOM:(await import('jotai')).atom([{name:'MyBalancePreset'}])}));
vi.mock('../../UCP3-GUI-extension-dependents/src/tauri/tauri-dialog',()=>({openFileDialog:vi.fn(),openFolderDialog:vi.fn()}));
vi.mock('../../UCP3-GUI-extension-dependents/src/tauri/tauri-files',()=>({writeTextFile:vi.fn(),loadYaml:vi.fn()}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/modals/modal-ok-cancel',()=>({showModalOkCancel:vi.fn()}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/general/message',()=>({useMessage:()=> (s:any)=>typeof s==='string'?s:s.key}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/popover/ConfigPopover',()=>({ConfigPopover:()=>null}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/popover/CompactResetOverlay',()=>({default:({children}:any)=>children}));
vi.mock('../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/specified/SpecifiedStyle',()=>({createSpecifiedStyleIfSpecifiedAndTouched:()=>''}));
vi.mock('../../UCP3-GUI-extension-dependents/src/util/scripts/logging',()=>({default:class {msg(){return this;} obj(){return this;} info(){} debug(){} error(){} warn(){}}}));

import CreateFileInput from '../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/CreateFileInput';
import QualifierControl from '../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/QualifierControl';
import ResetSettingButton from '../../UCP3-GUI-extension-dependents/src/components/ucp-tabs/config-editor/ui-elements/ui-factory/popover/ResetSettingButton';
import { CONFIGURATION_FULL_REDUCER_ATOM as FULL, CONFIGURATION_USER_REDUCER_ATOM as USER, CONFIGURATION_QUALIFIER_REDUCER_ATOM as QUALIFIER } from '../../UCP3-GUI-extension-dependents/src/function/configuration/state';
import { CONFIGURATION_DEFAULTS_REDUCER_ATOM as DEFAULTS, CONFIGURATION_LOCKS_REDUCER_ATOM as LOCKS } from '../../UCP3-GUI-extension-dependents/src/function/configuration/derived-state';
import { changeLocale } from '../../UCP3-GUI-extension-dependents/src/function/extensions/locale/locale';
import { openFileDialog } from '../../UCP3-GUI-extension-dependents/src/tauri/tauri-dialog';
import { serializeUCPConfig } from '../../UCP3-GUI-extension-dependents/src/config/ucp/config-files/config-files';
import { buildExtensionConfigurationDB } from '../../UCP3-GUI-extension-dependents/src/function/configuration/extension-configuration/build-extension-configuration-db';

const options=parse(readFileSync('options.yml','utf8')).options;
const url=options[0].url;
const languages=Object.keys(parse(readFileSync('../UCP3-GUI/resources/lang/languages.yaml','utf8')));
const extension={name:'projectileModifier',version:'1.4.0',type:'module',ui:options,configEntries:{}} as any;
afterEach(cleanup);
function setup(lang='en',lock=false) {
  const locale=parse(readFileSync('locale/'+lang+'.yml','utf8'));
  const spec=(changeLocale(locale,options) as any[])[0];
  const store=createStore();
  store.set(DEFAULTS as any,{[url]:''});
  store.set(FULL,{type:'set-multiple',value:{[url]:lock?'locked.yml':''}});
  if(lock) store.set(LOCKS as any,{[url]:{lockedBy:'MyBalancePreset',lockedValue:'locked.yml'}});
  const view=render(<Provider store={store}><QualifierControl roots={[url]} single/><ResetSettingButton url={url} compact/><CreateFileInput spec={spec} disabled={false} className=""/></Provider>);
  return {store,view,locale};
}
for(const lang of languages) {
  test('one localized native file picker selects a preset in '+lang,async()=>{
    expect(options).toHaveLength(1);
    expect(options[0].display).toBe('FileInput');
    const {store,view,locale}=setup(lang);
    const input=view.getByLabelText(locale.config_file) as HTMLInputElement;
    expect(input.value).toBe('');
    expect(view.getByText(locale.config_file).getAttribute('title')).toContain(locale.config_help);
    expect(view.container.querySelectorAll('select,input[type="range"],input[type="checkbox"]')).toHaveLength(0);
    vi.mocked(openFileDialog).mockResolvedValue({isPresent:()=>true,isEmpty:()=>false,get:()=> 'C:/Game/ucp/resources/projectileModifier/custom.yml'} as any);
    fireEvent.click(view.getByRole('button',{name:'Browse'}));
    await waitFor(()=>expect(store.get(USER)[url]).toBe('ucp/resources/projectileModifier/custom.yml'));
    expect(store.get(FULL)[url]).toBe('ucp/resources/projectileModifier/custom.yml');
  });
}
test('native qualifier toggles required/suggested and reset makes the option unspecified',()=>{
  const {store,view}=setup();
  const toggle=view.container.querySelector('.qualifier-control')!;
  fireEvent.click(toggle);
  expect(store.get(QUALIFIER)[url]).toBe('required');
  expect(store.get(USER)[url]).toBe(''); // Explicit empty is a real choice.
  let saved=serializeUCPConfig(store.get(USER),store.get(FULL),[extension],[extension],store.get(QUALIFIER));
  expect(saved['config-sparse'].modules.projectileModifier.config.projectile_config_file_selector.contents).toEqual({'required-value':''});
  fireEvent.click(toggle);
  expect(store.get(QUALIFIER)[url]).toBe('suggested');
  saved=serializeUCPConfig(store.get(USER),store.get(FULL),[extension],[extension],store.get(QUALIFIER));
  expect(saved['config-sparse'].modules.projectileModifier.config.projectile_config_file_selector.contents).toEqual({'suggested-value':''});
  fireEvent.click(view.getByRole('button',{name:'config.popover.reset'}));
  expect(store.get(USER)[url]).toBeUndefined();
  expect(store.get(FULL)[url]).toBe('');
  saved=serializeUCPConfig(store.get(USER),store.get(FULL),[extension],[extension],store.get(QUALIFIER));
  expect(saved['config-sparse'].modules.projectileModifier.config).toEqual({});
  expect(saved['config-full'].modules.projectileModifier.config.projectile_config_file_selector.contents).toEqual({value:''});
});
test('a required preset locks browsing and qualifier edits',()=>{
  const {view}=setup('en',true);
  expect((view.getByRole('button',{name:'Browse'}) as HTMLButtonElement).disabled).toBe(true);
  expect((view.container.querySelector('.qualifier-control') as HTMLButtonElement).disabled).toBe(true);
});
test('extension paths use the standard version-independent UCP spelling',async()=>{
  const {store,view}=setup();
  vi.mocked(openFileDialog).mockResolvedValue({isPresent:()=>true,isEmpty:()=>false,get:()=> 'C:/Game/ucp/plugins/MyBalancePreset-1.0.0/projectiles.yml'} as any);
  fireEvent.click(view.getByRole('button',{name:'Browse'}));
  await waitFor(()=>expect(store.get(USER)[url]).toBe('ucp/plugins/MyBalancePreset-*/projectiles.yml'));
});
test('shipped UCP examples resolve using the real qualifier merge rules',()=>{
  const preset=(qualifier:string)=>{
    const doc=parse(readFileSync('examples/ucp-plugin-'+qualifier+'.yml','utf8'));
    const entry=doc['config-sparse'].modules.projectileModifier.config.projectile_config_file_selector;
    return {name:qualifier,type:'plugin',version:'1.0.0',ui:[],configEntries:entry?{[url]:entry}:{}};
  };
  const resolve=(...plugins:any[])=>buildExtensionConfigurationDB({activeExtensions:[...plugins,extension]} as any).configuration;
  expect(resolve(preset('unspecified')).defined[url]).toBe('');
  const suggested=resolve(preset('suggested'));
  expect(suggested.defined[url]).toBe('ucp/plugins/MyBalancePreset-*/projectiles.yml');
  expect(suggested.locks[url]).toBeUndefined();
  const required=preset('required');
  expect(resolve(required).locks[url]).toBeDefined();
  const different={name:'Other',type:'plugin',ui:[],configEntries:{[url]:{contents:{'suggested-value':'other.yml'}}}};
  expect(resolve(different,required).defined[url]).toBe('ucp/plugins/MyBalancePreset-*/projectiles.yml');
  different.configEntries[url].contents={'required-value':'other.yml'} as any;
  expect(resolve(different,required).errors).not.toHaveLength(0);
});

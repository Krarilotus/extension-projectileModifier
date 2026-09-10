import { beforeAll, expect, test, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { parse } from 'yaml';

// Only the native ZIP bridge is substituted. Read the real central directory;
// never synthesize parent entries. This matches zip_support.rs::exist/by_name.
vi.mock('../../UCP3-GUI-extension-dependents/src/tauri/tauri-invoke', async()=>{
  const { execFileSync }=await import('node:child_process');
  const readers=new Map<number,Record<string,string>>();
  let next=0;
  return {
    loadZipReader:async(path:string)=>{
      const script="import sys,json,zipfile; z=zipfile.ZipFile(sys.argv[1]); print(json.dumps({n:z.read(n).decode('utf-8-sig') for n in z.namelist() if n.endswith(('.yml','.yaml','.md','/'))}))";
      const files=JSON.parse(execFileSync(process.env.UCP_TEST_PYTHON??'C:/UCPTools/python/Scripts/python.exe',
        ['-c',script,path],{encoding:'utf8',maxBuffer:16*1024*1024}));
      readers.set(++next,files); return next;
    },
    closeZipReader:async(id:number)=>{readers.delete(id);},
    existZipReaderEntry:async(id:number,path:string)=>Object.hasOwn(readers.get(id)!,path),
    getZipReaderEntryAsText:async(id:number,path:string)=>readers.get(id)![path],
    slashify:async(path:string)=>path.replaceAll('\\','/'),
  };
});
vi.mock('../../UCP3-GUI-extension-dependents/src/tauri/tauri-files',()=>({renameFile:vi.fn()}));
vi.mock('../../UCP3-GUI-extension-dependents/src/util/scripts/logging',()=>({default:class {
  msg(){return this;} info(){} error(){} warn(){}
}}));

import RustZipExtensionHandle from '../../UCP3-GUI-extension-dependents/src/function/extensions/handles/rust-zip-extension-handle';
import { readLocales, readUISpec } from '../../UCP3-GUI-extension-dependents/src/function/extensions/discovery/io';
import { applyLocale } from '../../UCP3-GUI-extension-dependents/src/function/extensions/discovery/translation';
import { optionEntriesToHierarchical } from '../../UCP3-GUI-extension-dependents/src/config/ucp/extension-util';

const python=process.env.UCP_TEST_PYTHON??'C:/UCPTools/python/Scripts/python.exe';
const definition=parse(readFileSync('definition.yml','utf8'));
const archive='dist/'+definition.name+'-'+definition.version+'.zip';
const languages=Object.keys(parse(readFileSync('../UCP3-GUI/resources/lang/languages.yaml','utf8')));
const broken='tests/output/omitted-locale-directory.zip';
const legacy=process.env.UCP_TEST_LEGACY_ZIP??'../Roadmap/Investigations/Interface-Visual/framework-release/ucp/modules/ucp2-legacy-2.15.1.zip';

beforeAll(()=>{
  execFileSync(python,['tools/package.py']);
  execFileSync(python,['-c',
    "import sys,zipfile,pathlib; pathlib.Path(sys.argv[2]).parent.mkdir(parents=True,exist_ok=True); src=zipfile.ZipFile(sys.argv[1]); dst=zipfile.ZipFile(sys.argv[2],'w'); [dst.writestr(i,src.read(i.filename)) for i in src.infolist() if not i.is_dir()]; dst.close()",
    archive,broken]);
});

test('reproduces untranslated placeholders when locale files exist without the directory entry',async()=>{
  const handle=await RustZipExtensionHandle.fromPath(broken);
  try {
    expect(await handle.doesEntryExist('locale/en.yml')).toBe(true);
    expect(await handle.doesEntryExist('locale/')).toBe(false);
    const locales=await readLocales(handle,definition.name,languages);
    expect(locales).toEqual({});
    const ui=(await readUISpec(handle)).options;
    expect(JSON.stringify(applyLocale({ui} as any,locales.en??{}))).toContain('{{balance_changes}}');
  } finally { await handle.close(); }
});

for(const lang of languages) {
  test('packaged '+lang+' locale loads through UCP ZIP discovery and joins the installed Legacy category',async()=>{
    const handle=await RustZipExtensionHandle.fromPath(archive);
    const legacyHandle=await RustZipExtensionHandle.fromPath(legacy);
    try {
      expect(await handle.doesEntryExist('locale/')).toBe(true);
      expect(await legacyHandle.doesEntryExist('locale/')).toBe(true);
      const locales=await readLocales(handle,definition.name,languages);
      expect(Object.keys(locales).sort()).toEqual([...languages].sort());
      expect(Object.keys(locales[lang])).toHaveLength(121);
      const ui=(await readUISpec(handle)).options;
      const localized=applyLocale({ui} as any,locales[lang]);
      expect(JSON.stringify(localized)).not.toContain('{{');
      expect(localized[0].header).toBe(locales[lang].projectiles);
      expect(localized[0].text).toBe(locales[lang].unit_description);
      expect(await handle.getTextContents('locale/description-'+lang+'.md')).toContain(locales[lang].unit_description);
      const legacyLocales=await readLocales(legacyHandle,'ucp2-legacy',languages);
      const legacyUI=(await readUISpec(legacyHandle)).options;
      const legacyLocalized=applyLocale({ui:legacyUI} as any,{...legacyLocales.en,...legacyLocales[lang]});
      const before=optionEntriesToHierarchical(legacyLocalized as any);
      const after=optionEntriesToHierarchical([...legacyLocalized,...localized] as any);
      expect(Object.keys(after.sections)).toEqual(Object.keys(before.sections));
      expect(after.sections[locales[lang].balance_changes].elements).toContain(localized[0]);
    } finally { await handle.close(); await legacyHandle.close(); }
  });
}

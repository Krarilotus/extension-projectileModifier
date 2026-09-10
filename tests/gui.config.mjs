import path from 'node:path';
const gui = path.resolve('../UCP3-GUI-extension-dependents');
export default {
  resolve: { alias: Object.fromEntries(['components','function','hooks','config','localization','util','tauri']
    .map(name => [name, path.join(gui,'src',name)])) },
  esbuild: { jsx: 'automatic' },
  test: { environment: 'jsdom', include: ['tests/gui.test.tsx','tests/archive-locales.test.ts'] },
};

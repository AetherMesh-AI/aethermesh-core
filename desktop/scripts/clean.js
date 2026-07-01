const fs = require('node:fs');
const path = require('node:path');

for (const relativePath of ['dist/desktop', 'dist/runtime', 'dist/source', 'desktop/.vite', 'desktop/out', 'desktop/resources/runtime', 'build/pyinstaller', 'build/pyinstaller-spec']) {
  fs.rmSync(path.resolve(relativePath), { recursive: true, force: true });
  console.log(`removed ${relativePath}`);
}

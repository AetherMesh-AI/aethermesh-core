const fs = require('node:fs');
const path = require('node:path');

for (const relativePath of ['dist/desktop', 'desktop/.vite', 'desktop/out']) {
  fs.rmSync(path.resolve(relativePath), { recursive: true, force: true });
  console.log(`removed ${relativePath}`);
}

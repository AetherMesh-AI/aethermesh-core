const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..', '..');
const platform = process.env.AETHERMESH_TARGET_PLATFORM || process.platform;
const arch = process.env.AETHERMESH_TARGET_ARCH || process.arch;
const exeName = platform === 'win32' ? 'aethermesh-node.exe' : 'aethermesh-node';
const source = process.env.AETHERMESH_RUNTIME_PATH
  || path.join(root, 'dist', 'runtime', `${platform}-${arch}`, exeName);
const targetDir = path.join(root, 'desktop', 'resources', 'runtime');
const target = path.join(targetDir, exeName);

if (!fs.existsSync(source)) {
  throw new Error(`Runtime sidecar not found: ${source}. Run npm run runtime:build first or set AETHERMESH_RUNTIME_PATH.`);
}
fs.rmSync(targetDir, { recursive: true, force: true });
fs.mkdirSync(targetDir, { recursive: true });
fs.copyFileSync(source, target);
if (platform !== 'win32') {
  fs.chmodSync(target, 0o755);
}
console.log(`Copied runtime sidecar to ${target}`);

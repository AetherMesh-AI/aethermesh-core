const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..', '..');
const platform = process.env.AETHERMESH_TARGET_PLATFORM || process.platform;
const arch = process.env.AETHERMESH_TARGET_ARCH || process.arch;
const exeName = platform === 'win32' ? 'aethermesh-node.exe' : 'aethermesh-node';
const runtimeOut = path.join(root, 'dist', 'runtime', `${platform}-${arch}`);
const entry = path.join(root, 'desktop', 'pyinstaller', 'aethermesh_node.py');

fs.rmSync(runtimeOut, { recursive: true, force: true });
fs.mkdirSync(runtimeOut, { recursive: true });

const args = [
  '-m',
  'PyInstaller',
  '--clean',
  '--noconfirm',
  '--onefile',
  '--name',
  'aethermesh-node',
  '--distpath',
  runtimeOut,
  '--workpath',
  path.join(root, 'build', 'pyinstaller', `${platform}-${arch}`),
  '--specpath',
  path.join(root, 'build', 'pyinstaller-spec'),
  '--paths',
  path.join(root, 'src'),
  '--collect-all',
  'aethermesh_core',
  '--hidden-import',
  'uvicorn',
  '--hidden-import',
  'fastapi',
  entry,
];

console.log(`Building AetherMesh runtime sidecar: ${platform}-${arch}`);
console.log(`$ ${process.env.PYTHON || 'python'} ${args.join(' ')}`);
const result = spawnSync(process.env.PYTHON || 'python', args, {
  cwd: root,
  stdio: 'inherit',
});
if (result.status !== 0) {
  process.exit(result.status || 1);
}

const built = path.join(runtimeOut, exeName);
if (!fs.existsSync(built)) {
  throw new Error(`Expected runtime sidecar was not produced: ${built}`);
}
console.log(`Runtime sidecar ready: ${built}`);

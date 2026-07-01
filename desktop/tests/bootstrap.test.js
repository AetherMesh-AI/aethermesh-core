const assert = require('node:assert/strict');
const { test } = require('node:test');
const path = require('node:path');

const {
  getDefaultAetherMeshHome,
  getAetherMeshPaths,
} = require('../src/bootstrap/storage');
const {
  isUsablePythonVersion,
  parsePythonVersion,
  detectPython,
} = require('../src/bootstrap/python');
const {
  buildPackageInstallCommand,
  normalizePackageSettings,
} = require('../src/bootstrap/packageInstaller');
const {
  buildCreateVenvCommand,
  getVenvPythonPath,
} = require('../src/bootstrap/venv');
const { NodeSupervisor } = require('../src/bootstrap/supervisor');
const { LocalApiClient } = require('../src/bootstrap/apiClient');
const {
  getRuntimeExecutableName,
  resolveRuntimeCommand,
} = require('../src/bootstrap/runtime');

test('platform storage paths are per-user and app-managed', () => {
  assert.equal(
    getDefaultAetherMeshHome({ platform: 'darwin', homeDir: '/Users/trevor' }),
    path.join('/Users/trevor', 'Library', 'Application Support', 'AetherMesh'),
  );
  assert.equal(
    getDefaultAetherMeshHome({
      platform: 'win32',
      homeDir: 'C:/Users/Trevor',
      env: { APPDATA: 'C:/Users/Trevor/AppData/Roaming' },
    }),
    path.join('C:/Users/Trevor/AppData/Roaming', 'AetherMesh'),
  );
  assert.equal(
    getDefaultAetherMeshHome({
      platform: 'linux',
      homeDir: '/home/trevor',
      env: { XDG_DATA_HOME: '/home/trevor/.local/state' },
    }),
    path.join('/home/trevor/.local/state', 'AetherMesh'),
  );

  const paths = getAetherMeshPaths('/tmp/AetherMesh');
  assert.equal(paths.venvDir, path.join('/tmp/AetherMesh', 'venv'));
  assert.equal(paths.logsDir, path.join('/tmp/AetherMesh', 'logs'));
  assert.equal(paths.configDir, path.join('/tmp/AetherMesh', 'config'));
  assert.equal(paths.metadataDir, path.join('/tmp/AetherMesh', 'metadata'));
  assert.equal(paths.installStatusPath, path.join('/tmp/AetherMesh', 'metadata', 'install-status.json'));
});

test('python version detection accepts 3.11+ and rejects old versions', async () => {
  assert.deepEqual(parsePythonVersion('Python 3.12.4'), { major: 3, minor: 12, patch: 4 });
  assert.deepEqual(parsePythonVersion('3.11.9'), { major: 3, minor: 11, patch: 9 });
  assert.equal(isUsablePythonVersion('Python 3.10.14'), false);
  assert.equal(isUsablePythonVersion('Python 3.11.0'), true);
  assert.equal(isUsablePythonVersion('Python 3.12.1'), true);

  const detected = await detectPython({
    candidates: ['python3.10', 'python3.12'],
    execFile: async (binary, args) => {
      assert.deepEqual(args, ['--version']);
      return binary === 'python3.12' ? 'Python 3.12.2' : 'Python 3.10.14';
    },
  });
  assert.equal(detected.usable, true);
  assert.equal(detected.executable, 'python3.12');
});

test('venv commands stay inside the app-managed environment', () => {
  assert.deepEqual(
    buildCreateVenvCommand('/usr/bin/python3.12', '/tmp/AetherMesh/venv'),
    ['/usr/bin/python3.12', ['-m', 'venv', '/tmp/AetherMesh/venv']],
  );
  assert.equal(
    getVenvPythonPath('/tmp/AetherMesh/venv', 'darwin'),
    path.join('/tmp/AetherMesh/venv', 'bin', 'python'),
  );
  assert.equal(
    getVenvPythonPath('C:/Users/Trevor/AppData/Roaming/AetherMesh/venv', 'win32'),
    path.join('C:/Users/Trevor/AppData/Roaming/AetherMesh/venv', 'Scripts', 'python.exe'),
  );
});

test('runtime resolver uses bundled sidecar in packaged app and dev fallback only outside production', () => {
  assert.equal(getRuntimeExecutableName('darwin'), 'aethermesh-node');
  assert.equal(getRuntimeExecutableName('linux'), 'aethermesh-node');
  assert.equal(getRuntimeExecutableName('win32'), 'aethermesh-node.exe');

  assert.equal(
    resolveRuntimeCommand({
      isPackaged: true,
      resourcesPath: '/Applications/AetherMesh.app/Contents/Resources',
      platform: 'darwin',
      arch: 'arm64',
      existsSync: () => true,
    }),
    path.join('/Applications/AetherMesh.app/Contents/Resources', 'runtime', 'aethermesh-node'),
  );
  assert.equal(
    resolveRuntimeCommand({
      isPackaged: true,
      resourcesPath: 'C:/Program Files/AetherMesh/resources',
      platform: 'win32',
      arch: 'x64',
      existsSync: () => true,
    }),
    path.join('C:/Program Files/AetherMesh/resources', 'runtime', 'aethermesh-node.exe'),
  );
  assert.throws(
    () => resolveRuntimeCommand({
      isPackaged: true,
      resourcesPath: '/missing',
      platform: 'linux',
      arch: 'x64',
      existsSync: () => false,
    }),
    /bundled AetherMesh runtime is missing/,
  );
  assert.equal(
    resolveRuntimeCommand({
      isPackaged: false,
      appRoot: '/repo',
      platform: 'linux',
      arch: 'x64',
      env: { AETHERMESH_RUNTIME_PATH: '/tmp/aethermesh-node' },
      existsSync: () => false,
    }),
    '/tmp/aethermesh-node',
  );
  assert.equal(
    resolveRuntimeCommand({
      isPackaged: false,
      appRoot: '/repo',
      platform: 'linux',
      arch: 'x64',
      env: {},
      existsSync: () => false,
    }),
    'aethermesh',
  );
});

test('package install command supports pypi github and local development sources', () => {
  assert.deepEqual(normalizePackageSettings({}), {
    source: 'github',
    packageName: 'aethermesh[ui]',
    githubUrl: 'https://github.com/AetherMesh-AI/aethermesh-core/releases/latest/download/aethermesh-0.1.0a0-py3-none-any.whl',
    localPath: '',
    autoUpdateOnLaunch: false,
  });
  assert.deepEqual(
    buildPackageInstallCommand('/venv/bin/python', { source: 'pypi', packageName: 'aethermesh[ui]' }, { update: false }),
    ['/venv/bin/python', ['-m', 'pip', 'install', '--upgrade', 'aethermesh[ui]']],
  );
  assert.deepEqual(
    buildPackageInstallCommand('/venv/bin/python', { source: 'github', githubUrl: 'https://example.invalid/aethermesh.whl' }, { update: true }),
    ['/venv/bin/python', ['-m', 'pip', 'install', '--upgrade', '--force-reinstall', 'aethermesh[ui] @ https://example.invalid/aethermesh.whl']],
  );
  assert.deepEqual(
    buildPackageInstallCommand('/venv/bin/python', { source: 'local', localPath: '../aethermesh-core' }, { update: false }),
    ['/venv/bin/python', ['-m', 'pip', 'install', '--upgrade', '-e', '../aethermesh-core[ui]']],
  );
  assert.throws(
    () => buildPackageInstallCommand('/venv/bin/python', { source: 'local', localPath: '' }),
    /local development path is required/,
  );
});

test('supervisor runs init before node API start and captures logs', async () => {
  const calls = [];
  const children = [];
  const supervisor = new NodeSupervisor({
    env: { AETHERMESH_HOME: '/tmp/AetherMesh' },
    spawn: (command, args, options) => {
      calls.push({ command, args, env: options.env });
      const child = createFakeChild();
      children.push(child);
      return child;
    },
  });

  const startPromise = supervisor.start({ host: '127.0.0.1', port: 7280 });
  children[0].stdout.emit('data', Buffer.from('initialized\n'));
  children[0].emit('exit', 0, null);
  await new Promise((resolve) => setImmediate(resolve));
  children[1].stdout.emit('data', Buffer.from('api started\n'));
  await startPromise;

  assert.deepEqual(calls.map((call) => call.command), ['aethermesh-node', 'aethermesh-node']);
  assert.deepEqual(calls.map((call) => call.args), [
    ['init'],
    ['node', 'start', '--host', '127.0.0.1', '--port', '7280'],
  ]);
  assert.equal(supervisor.state.status, 'running');
  assert.match(supervisor.logs.join('\n'), /initialized/);
  assert.match(supervisor.logs.join('\n'), /api started/);

  await assert.rejects(() => supervisor.start(), /already running/);
  supervisor.stop();
  assert.equal(children[1].killedWith, 'SIGTERM');
  assert.equal(supervisor.state.status, 'stopped');
});

test('local API client reports reachable and unreachable states', async () => {
  const okClient = new LocalApiClient({
    baseUrl: 'http://127.0.0.1:7280',
    fetch: async (url) => ({
      ok: true,
      json: async () => ({ url }),
    }),
  });
  assert.deepEqual(await okClient.getJson('/api/status'), { url: 'http://127.0.0.1:7280/api/status' });
  assert.equal((await okClient.health()).reachable, true);

  const badClient = new LocalApiClient({
    fetch: async () => {
      throw new Error('connection refused');
    },
  });
  const health = await badClient.health();
  assert.equal(health.reachable, false);
  assert.match(health.error, /connection refused/);
});

function createFakeChild() {
  const EventEmitter = require('node:events');
  const child = new EventEmitter();
  child.stdout = new EventEmitter();
  child.stderr = new EventEmitter();
  child.kill = (signal) => {
    child.killedWith = signal;
    child.emit('exit', 0, signal);
  };
  return child;
}

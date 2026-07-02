const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const { test } = require('node:test');
const path = require('node:path');

const {
  getDefaultAetherMeshHome,
  getDefaultAetherMeshLogsDir,
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
const {
  BackgroundNodeManager,
  buildLaunchAgentPlist,
  buildSystemdUserService,
  buildWindowsTaskXml,
  getStableRuntimePath,
} = require('../src/bootstrap/backgroundNodeManager');
const { shouldLeaveBackgroundNodeRunning, shouldStopTemporaryNode } = require('../src/bootstrap/lifecycle');

test('platform storage paths are per-user and app-managed', () => {
  assert.equal(
    getDefaultAetherMeshHome({ platform: 'darwin', homeDir: '/Users/trevor' }),
    path.join('/Users/trevor', 'Library', 'Application Support', 'AetherMesh'),
  );
  assert.equal(
    getDefaultAetherMeshHome({
      platform: 'win32',
      homeDir: 'C:/Users/Trevor',
      env: { LOCALAPPDATA: 'C:/Users/Trevor/AppData/Local' },
    }),
    path.join('C:/Users/Trevor/AppData/Local', 'AetherMesh'),
  );
  assert.equal(
    getDefaultAetherMeshHome({
      platform: 'linux',
      homeDir: '/home/trevor',
      env: { XDG_DATA_HOME: '/home/trevor/.local/share' },
    }),
    path.join('/home/trevor/.local/share', 'aethermesh'),
  );

  const paths = getAetherMeshPaths('/tmp/AetherMesh');
  assert.equal(paths.runtimeDir, path.join('/tmp/AetherMesh', 'runtime'));
  assert.equal(getDefaultAetherMeshLogsDir({ platform: 'darwin', homeDir: '/Users/trevor' }), path.join('/Users/trevor', 'Library', 'Logs', 'AetherMesh'));
  assert.equal(getDefaultAetherMeshLogsDir({ platform: 'win32', home: 'C:/Users/Trevor/AppData/Local/AetherMesh' }), path.join('C:/Users/Trevor/AppData/Local/AetherMesh', 'logs'));
  assert.equal(getDefaultAetherMeshLogsDir({ platform: 'linux', homeDir: '/home/trevor', env: { XDG_STATE_HOME: '/home/trevor/.local/state' } }), path.join('/home/trevor/.local/state', 'aethermesh', 'logs'));
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
    githubUrl: 'https://github.com/AetherMesh-AI/aethermesh-core/releases/latest/download/aethermesh-0.2.0a0-py3-none-any.whl',
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

test('background manager copies runtime atomically and records metadata', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aethermesh-bg-'));
  try {
    const bundled = path.join(root, 'bundle', 'aethermesh-node');
    fs.mkdirSync(path.dirname(bundled), { recursive: true });
    fs.writeFileSync(bundled, 'runtime-v1');
    const paths = getAetherMeshPaths(path.join(root, 'home'), { platform: 'linux', homeDir: root, logsDir: path.join(root, 'logs') });
    const manager = new BackgroundNodeManager({
      paths,
      bundledRuntimePath: bundled,
      version: '0.2.0-alpha',
      platform: 'linux',
      now: () => new Date('2026-07-02T00:00:00Z'),
      execFile: fakeExecFile([]),
    });

    const first = manager.copyOrUpdateRuntime();
    assert.equal(first.updated, true);
    assert.equal(fs.readFileSync(manager.stableRuntimePath, 'utf8'), 'runtime-v1');
    assert.equal(fs.statSync(manager.stableRuntimePath).mode & 0o111, 0o111);
    assert.equal(first.metadata.version, '0.2.0-alpha');
    assert.equal(first.metadata.installedPath, manager.stableRuntimePath);
    assert.equal(first.metadata.sourcePath, bundled);

    const second = manager.copyOrUpdateRuntime();
    assert.equal(second.updated, false);

    fs.writeFileSync(bundled, 'runtime-v2');
    const update = await manager.checkForRuntimeUpdates();
    assert.equal(update.available, true);
    const applied = await manager.applyRuntimeUpdate();
    assert.equal(applied.updated, true);
    assert.equal(fs.readFileSync(manager.stableRuntimePath, 'utf8'), 'runtime-v2');
    assert.ok(fs.existsSync(manager.backupMetadataPath));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('background manager generates per-platform user startup registrations', async () => {
  const macPlist = buildLaunchAgentPlist({
    runtimePath: '/Users/trevor/Library/Application Support/AetherMesh/runtime/aethermesh-node',
    homeDir: '/Users/trevor/Library/Application Support/AetherMesh',
    logsDir: '/Users/trevor/Library/Logs/AetherMesh',
    host: '127.0.0.1',
    port: 7280,
  });
  assert.match(macPlist, /dev\.aethermesh\.node/);
  assert.match(macPlist, /RunAtLoad/);
  assert.match(macPlist, /KeepAlive/);
  assert.match(macPlist, /node\.log/);

  const systemd = buildSystemdUserService({
    runtimePath: '/home/trevor/.local/share/aethermesh/runtime/aethermesh-node',
    homeDir: '/home/trevor/.local/share/aethermesh',
    logsDir: '/home/trevor/.local/state/aethermesh/logs',
    host: '127.0.0.1',
    port: 7280,
  });
  assert.match(systemd, /ExecStart=.*aethermesh-node node start --host 127\.0\.0\.1 --port 7280/);
  assert.match(systemd, /Restart=always/);
  assert.match(systemd, /WantedBy=default\.target/);

  const windowsXml = buildWindowsTaskXml({
    runtimePath: 'C:\\Users\\Trevor\\AppData\\Local\\AetherMesh\\runtime\\aethermesh-node.exe',
    homeDir: 'C:\\Users\\Trevor\\AppData\\Local\\AetherMesh',
    host: '127.0.0.1',
    port: 7280,
  });
  assert.match(windowsXml, /<LogonTrigger>/);
  assert.match(windowsXml, /<RunLevel>LeastPrivilege<\/RunLevel>/);
  assert.match(windowsXml, /node start --host 127\.0\.0\.1 --port 7280/);
});

test('background manager invokes OS helpers without admin-only services', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aethermesh-bg-os-'));
  try {
    const bundled = path.join(root, 'bundle', 'aethermesh-node');
    fs.mkdirSync(path.dirname(bundled), { recursive: true });
    fs.writeFileSync(bundled, 'runtime');
    const paths = getAetherMeshPaths(path.join(root, 'home'), { logsDir: path.join(root, 'logs') });
    const calls = [];
    const manager = new BackgroundNodeManager({
      paths,
      bundledRuntimePath: bundled,
      version: '0.2.0-alpha',
      platform: 'linux',
      execFile: fakeExecFile(calls),
    });
    manager.copyOrUpdateRuntime();
    await manager.enableStartAtLogin();
    await manager.startBackgroundNode();
    await manager.stopBackgroundNode();
    await manager.disableStartAtLogin();
    assert.deepEqual(calls.map((call) => [call.command, call.args.slice(0, 3)]), [
      ['systemctl', ['--user', 'daemon-reload']],
      ['systemctl', ['--user', 'enable', 'aethermesh-node.service']],
      ['systemctl', ['--user', 'start', 'aethermesh-node.service']],
      ['systemctl', ['--user', 'stop', 'aethermesh-node.service']],
      ['systemctl', ['--user', 'stop', 'aethermesh-node.service']],
      ['systemctl', ['--user', 'disable', 'aethermesh-node.service']],
      ['systemctl', ['--user', 'daemon-reload']],
    ]);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('close and quit lifecycle keeps OS-managed nodes running', () => {
  assert.equal(shouldStopTemporaryNode({ backgroundNodeEnabled: false, keepNodeRunningAfterClose: false }), true);
  assert.equal(shouldStopTemporaryNode({ backgroundNodeEnabled: false, keepNodeRunningAfterClose: true }), false);
  assert.equal(shouldStopTemporaryNode({ backgroundNodeEnabled: true, keepNodeRunningAfterClose: false }), false);
  assert.equal(shouldLeaveBackgroundNodeRunning({ backgroundNodeEnabled: true }), true);
  assert.equal(shouldLeaveBackgroundNodeRunning({ backgroundNodeEnabled: false }), false);
});

test('runtime update checks can be scheduled for gossip-trigger-compatible refreshes', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aethermesh-bg-update-'));
  try {
    const bundled = path.join(root, 'bundle', 'aethermesh-node');
    fs.mkdirSync(path.dirname(bundled), { recursive: true });
    fs.writeFileSync(bundled, 'runtime');
    const paths = getAetherMeshPaths(path.join(root, 'home'), { logsDir: path.join(root, 'logs') });
    const manager = new BackgroundNodeManager({
      paths,
      bundledRuntimePath: bundled,
      version: '0.2.0-alpha',
      platform: 'linux',
      execFile: fakeExecFile([]),
    });
    const results = [];
    manager.schedulePeriodicUpdateChecks({ intervalMs: 5, onResult: (error, result) => results.push({ error, result }) });
    await new Promise((resolve) => setTimeout(resolve, 20));
    manager.clearPeriodicUpdateChecks();
    assert.ok(results.length >= 1);
    assert.equal(results[0].error, null);
    assert.equal(results[0].result.updated, true);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('periodic update checks do not install stable runtime until background mode applies updates', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aethermesh-bg-check-only-'));
  try {
    const bundled = path.join(root, 'bundle', 'aethermesh-node');
    fs.mkdirSync(path.dirname(bundled), { recursive: true });
    fs.writeFileSync(bundled, 'runtime');
    const paths = getAetherMeshPaths(path.join(root, 'home'), { logsDir: path.join(root, 'logs') });
    const manager = new BackgroundNodeManager({
      paths,
      bundledRuntimePath: bundled,
      version: '0.2.0-alpha',
      platform: 'linux',
      execFile: fakeExecFile([]),
    });
    const results = [];
    manager.schedulePeriodicUpdateChecks({
      intervalMs: 5,
      shouldApply: () => false,
      onResult: (error, result) => results.push({ error, result }),
    });
    await new Promise((resolve) => setTimeout(resolve, 20));
    manager.clearPeriodicUpdateChecks();
    assert.ok(results.length >= 1);
    assert.equal(results[0].error, null);
    assert.equal(results[0].result.updated, false);
    assert.equal(results[0].result.update.available, true);
    assert.equal(fs.existsSync(manager.stableRuntimePath), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

function fakeExecFile(calls) {
  return (command, args, options, callback) => {
    calls.push({ command, args, options });
    callback(null, '', '');
  };
}

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

const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');

const { LocalApiClient } = require('./bootstrap/apiClient');
const { buildPackageInstallCommand, normalizePackageSettings } = require('./bootstrap/packageInstaller');
const { detectPython } = require('./bootstrap/python');
const { getDefaultAetherMeshHome, getAetherMeshPaths } = require('./bootstrap/storage');
const { NodeSupervisor } = require('./bootstrap/supervisor');
const { buildCreateVenvCommand, getVenvPythonPath } = require('./bootstrap/venv');
const { platformNotes } = require('./platform');

const execFileAsync = promisify(execFile);
const apiHost = '127.0.0.1';
const apiPort = 7280;
const apiClient = new LocalApiClient({ baseUrl: `http://${apiHost}:${apiPort}` });

let mainWindow;
let supervisor;
let bootstrapState = {
  status: 'idle',
  error: null,
  python: { usable: false },
  package: { installed: false },
  storage: {},
  process: { status: 'stopped' },
  logs: [],
};

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 760,
    minWidth: 960,
    minHeight: 640,
    title: 'AetherMesh',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.loadFile(path.join(__dirname, 'ui', 'index.html'));
}

async function bootstrap() {
  try {
    updateBootstrap({ status: 'checking-python', error: null });
    const home = getDefaultAetherMeshHome();
    const paths = getAetherMeshPaths(home);
    fs.mkdirSync(paths.logsDir, { recursive: true });
    fs.mkdirSync(paths.configDir, { recursive: true });
    fs.mkdirSync(paths.metadataDir, { recursive: true });
    updateBootstrap({ storage: paths });

    const python = await detectPython();
    updateBootstrap({ python });
    if (!python.usable) {
      updateBootstrap({
        status: 'python-missing',
        error: 'Python 3.11+ was not found. Install Python or configure a bundled runtime before continuing.',
      });
      return;
    }

    updateBootstrap({ status: 'creating-venv' });
    const venvPython = getVenvPythonPath(paths.venvDir);
    if (!fs.existsSync(venvPython)) {
      await runLogged(buildCreateVenvCommand(python.executable, paths.venvDir));
    }

    updateBootstrap({ status: 'installing-package' });
    const settings = readSettings(paths);
    const [installCommand, installArgs] = buildPackageInstallCommand(
      venvPython,
      settings.package,
      { update: Boolean(settings.package.autoUpdateOnLaunch) },
    );
    await runLogged([installCommand, installArgs]);
    await writeInstallStatus(paths, venvPython, settings.package);
    updateBootstrap({ package: { installed: true, source: settings.package.source } });

    await startNode(paths, settings);
  } catch (error) {
    updateBootstrap({ status: 'error', error: error.message });
  }
}

async function startNode(paths, settings = readSettings(paths)) {
  updateBootstrap({ status: 'starting-node' });
  const health = await apiClient.health();
  if (health.reachable) {
    updateBootstrap({
      status: 'running',
      process: { status: 'running', error: null, pid: null, external: true },
      logs: [...bootstrapState.logs, 'connected to existing local AetherMesh API'].slice(-500),
    });
    return;
  }
  const command = getAetherMeshCommand(paths.venvDir);
  supervisor = new NodeSupervisor({
    aethermeshCommand: command,
    env: {
      ...process.env,
      AETHERMESH_HOME: paths.home,
    },
  });
  await supervisor.start({ host: settings.api.host, port: settings.api.port });
  updateBootstrap({ status: 'waiting-api', process: supervisor.state, logs: supervisor.logs });
  await waitForApi();
  updateBootstrap({ status: 'running', process: supervisor.state, logs: supervisor.logs });
}

async function waitForApi({ attempts = 30, delayMs = 500 } = {}) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const health = await apiClient.health();
    if (health.reachable) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw new Error('local AetherMesh API did not become reachable');
}

function stopNode(keepRunning = false) {
  if (supervisor) {
    supervisor.stop({ keepRunning });
  }
  updateBootstrap({ process: supervisor ? supervisor.state : { status: 'stopped' }, logs: supervisor ? supervisor.logs : [] });
}

function getAetherMeshCommand(venvDir) {
  if (process.platform === 'win32') {
    return path.join(venvDir, 'Scripts', 'aethermesh.exe');
  }
  return path.join(venvDir, 'bin', 'aethermesh');
}

function readSettings(paths) {
  const settingsPath = path.join(paths.configDir, 'desktop-settings.json');
  const defaults = {
    package: normalizePackageSettings({}),
    api: { host: apiHost, port: apiPort },
    keepNodeRunningAfterClose: false,
    advancedLogs: false,
  };
  if (!fs.existsSync(settingsPath)) {
    fs.writeFileSync(settingsPath, `${JSON.stringify(defaults, null, 2)}\n`);
    return defaults;
  }
  return { ...defaults, ...JSON.parse(fs.readFileSync(settingsPath, 'utf8')) };
}

async function writeInstallStatus(paths, venvPython, packageSettings) {
  const status = {
    installedAt: new Date().toISOString(),
    venvPython,
    package: packageSettings,
  };
  fs.writeFileSync(paths.installStatusPath, `${JSON.stringify(status, null, 2)}\n`);
}

async function runLogged([command, args]) {
  appendBootstrapLog(`$ ${command} ${args.join(' ')}`);
  const { stdout, stderr } = await execFileAsync(command, args, { maxBuffer: 1024 * 1024 * 10 });
  if (stdout) appendBootstrapLog(stdout.trimEnd());
  if (stderr) appendBootstrapLog(stderr.trimEnd());
}

function appendBootstrapLog(message) {
  if (!message) return;
  bootstrapState.logs = [...bootstrapState.logs, message].slice(-500);
  if (mainWindow) {
    mainWindow.webContents.send('aethermesh:state', bootstrapState);
  }
}

function updateBootstrap(partial) {
  bootstrapState = { ...bootstrapState, ...partial };
  if (mainWindow) {
    mainWindow.webContents.send('aethermesh:state', bootstrapState);
  }
}

ipcMain.handle('aethermesh:get-state', () => bootstrapState);
ipcMain.handle('aethermesh:get-dashboard', async () => apiClient.dashboardSnapshot());
ipcMain.handle('aethermesh:get-health', async () => apiClient.health());
ipcMain.handle('aethermesh:start-node', async () => {
  const paths = getAetherMeshPaths(getDefaultAetherMeshHome());
  if (!supervisor || supervisor.state.status !== 'running') {
    await startNode(paths);
  }
  return bootstrapState;
});
ipcMain.handle('aethermesh:stop-node', async () => {
  const paths = getAetherMeshPaths(getDefaultAetherMeshHome());
  stopNode(readSettings(paths).keepNodeRunningAfterClose);
  return bootstrapState;
});
ipcMain.handle('aethermesh:platform-notes', () => platformNotes());

app.whenReady().then(() => {
  createWindow();
  bootstrap();
});

app.on('window-all-closed', () => {
  const paths = getAetherMeshPaths(getDefaultAetherMeshHome());
  try {
    stopNode(readSettings(paths).keepNodeRunningAfterClose);
  } finally {
    if (process.platform !== 'darwin') app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

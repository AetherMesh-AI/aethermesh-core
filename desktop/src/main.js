const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('node:fs');
const path = require('node:path');

const { LocalApiClient } = require('./bootstrap/apiClient');
const { normalizePackageSettings } = require('./bootstrap/packageInstaller');
const { resolveRuntimeCommand } = require('./bootstrap/runtime');
const { getDefaultAetherMeshHome, getAetherMeshPaths } = require('./bootstrap/storage');
const { NodeSupervisor } = require('./bootstrap/supervisor');
const { platformNotes } = require('./platform');

const apiHost = '127.0.0.1';
const apiPort = 7280;
const apiClient = new LocalApiClient({ baseUrl: `http://${apiHost}:${apiPort}` });

let mainWindow;
let supervisor;
let bootstrapState = {
  status: 'idle',
  error: null,
  runtime: { mode: 'bundled', command: null, available: false },
  python: { usable: false, mode: 'developer-fallback' },
  package: { installed: true, source: 'bundled-runtime' },
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
    updateBootstrap({ status: 'checking-runtime', error: null });
    const home = getDefaultAetherMeshHome();
    const paths = getAetherMeshPaths(home);
    ensureStorage(paths);
    const settings = readSettings(paths);
    updateBootstrap({ storage: paths, package: { installed: true, source: 'bundled-runtime' } });

    const runtimeCommand = getRuntimeCommand();
    updateBootstrap({
      runtime: {
        mode: app.isPackaged ? 'bundled' : 'development',
        command: runtimeCommand,
        available: true,
      },
      status: 'runtime-ready',
    });

    await startNode(paths, settings, runtimeCommand);
  } catch (error) {
    updateBootstrap({ status: 'error', error: error.message });
  }
}

function ensureStorage(paths) {
  fs.mkdirSync(paths.logsDir, { recursive: true });
  fs.mkdirSync(paths.configDir, { recursive: true });
  fs.mkdirSync(paths.metadataDir, { recursive: true });
}

async function startNode(paths, settings = readSettings(paths), runtimeCommand = getRuntimeCommand()) {
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
  supervisor = new NodeSupervisor({
    aethermeshCommand: runtimeCommand,
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

function getRuntimeCommand() {
  return resolveRuntimeCommand({
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
    appRoot: path.resolve(__dirname, '..', '..'),
    platform: process.platform,
    arch: process.arch,
    env: process.env,
  });
}

function readSettings(paths) {
  const settingsPath = path.join(paths.configDir, 'desktop-settings.json');
  const defaults = {
    runtime: {
      source: 'bundled',
      allowDeveloperPythonFallback: !app.isPackaged,
    },
    package: normalizePackageSettings({ autoUpdateOnLaunch: false }),
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
  ensureStorage(paths);
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

module.exports = { appendBootstrapLog };

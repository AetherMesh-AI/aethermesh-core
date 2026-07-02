const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('node:fs');
const path = require('node:path');

const { BackgroundNodeManager, UPDATE_INTERVAL_MS } = require('./bootstrap/backgroundNodeManager');
const { CliManager } = require('./bootstrap/cliManager');
const { LocalApiClient } = require('./bootstrap/apiClient');
const { shouldStopTemporaryNode } = require('./bootstrap/lifecycle');
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
let backgroundManager;
let cliManager;
let shutdownStarted = false;
let bootstrapState = {
  status: 'idle',
  error: null,
  runtime: { mode: 'bundled', command: null, available: false },
  python: { usable: false, mode: 'developer-fallback' },
  package: { installed: true, source: 'bundled-runtime' },
  storage: {},
  process: { status: 'stopped', mode: 'temporary-app-managed' },
  background: { enabled: false, startAtLogin: false, status: 'disabled' },
  cli: { installed: false, status: 'not installed', command: 'aethermesh' },
  update: { status: 'idle', lastCheck: null },
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
    const paths = getPaths();
    ensureStorage(paths);
    const settings = readSettings(paths);
    const runtimeCommand = getRuntimeCommand();
    backgroundManager = createBackgroundManager(paths, runtimeCommand, settings);
    updateBootstrap({
      storage: paths,
      package: { installed: true, source: 'bundled-runtime' },
      background: backgroundStateFromSettings(settings),
      runtime: {
        mode: app.isPackaged ? 'bundled' : 'development',
        command: runtimeCommand,
        stablePath: backgroundManager.stableRuntimePath,
        available: true,
      },
      status: 'runtime-ready',
    });

    let activeSettings = settings;
    if (runtimeCommand && fs.existsSync(runtimeCommand)) {
      const cliInstall = await ensureStableRuntimeAndCli(paths, settings);
      activeSettings = cliInstall.settings;
    } else {
      updateBootstrap({ cli: { ...bootstrapState.cli, status: 'Broken', error: `stable runtime source is not a file: ${runtimeCommand}` } });
    }
    await reconcileStartupNode(paths, activeSettings, runtimeCommand);
    await checkRuntimeUpdates({ restart: activeSettings.backgroundNodeEnabled, apply: true });
    scheduleRuntimeUpdateChecks(paths);
  } catch (error) {
    updateBootstrap({ status: 'error', error: error.message });
  }
}

function getPaths() {
  return getAetherMeshPaths(getDefaultAetherMeshHome());
}

function ensureStorage(paths) {
  fs.mkdirSync(paths.home, { recursive: true });
  fs.mkdirSync(paths.logsDir, { recursive: true });
  fs.mkdirSync(paths.configDir, { recursive: true });
  fs.mkdirSync(paths.metadataDir, { recursive: true });
  fs.mkdirSync(paths.runtimeDir, { recursive: true });
}

function createBackgroundManager(paths, runtimeCommand = getRuntimeCommand(), settings = readSettings(paths)) {
  return new BackgroundNodeManager({
    paths,
    bundledRuntimePath: runtimeCommand,
    version: app.getVersion(),
    host: settings.nodeHost,
    port: settings.nodePort,
    healthCheck: () => apiClient.health(),
    log: appendBootstrapLog,
  });
}

function createCliManager(paths, runtimeMetadata = backgroundManager?.readRuntimeMetadata() || null) {
  const manager = new CliManager({
    paths,
    stableRuntimePath: (backgroundManager || createBackgroundManager(paths)).stableRuntimePath,
    runtimeMetadata,
  });
  cliManager = manager;
  return manager;
}

async function ensureStableRuntimeAndCli(paths, settings) {
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  let metadata = manager.readRuntimeMetadata();
  try {
    const copy = manager.copyOrUpdateRuntime();
    metadata = copy.metadata;
  } catch (error) {
    updateBootstrap({ cli: { ...bootstrapState.cli, status: 'Broken', error: error.message } });
    throw error;
  }
  const cli = createCliManager(paths, metadata);
  const cliMetadata = await cli.installOrRepair({ configurePath: true });
  const nextSettings = writeSettings(paths, settingsFromCliMetadata(settingsFromRuntimeMetadata(settings, metadata, { checkedAt: new Date().toISOString() }), cliMetadata));
  updateBootstrap({
    background: { ...backgroundStateFromSettings(nextSettings), runtime: metadata },
    cli: cliStateFromSettings(nextSettings, cliMetadata),
  });
  return { metadata, cliMetadata, settings: nextSettings };
}

async function reconcileStartupNode(paths, settings, runtimeCommand) {
  const health = await apiClient.health();
  if (health.reachable) {
    updateBootstrap({
      status: 'running',
      process: { status: 'running', error: null, pid: null, external: true, mode: settings.backgroundNodeEnabled ? 'background-os-managed' : 'existing-local-api' },
      logs: [...bootstrapState.logs, 'connected to existing local AetherMesh API'].slice(-500),
    });
    return;
  }
  assertPortAvailableForAetherMesh(health);

  if (settings.backgroundNodeEnabled) {
    await startBackgroundNode(paths, settings);
    return;
  }

  await startTemporaryNode(paths, settings, runtimeCommand);
}

async function startTemporaryNode(paths, settings = readSettings(paths), runtimeCommand = getRuntimeCommand()) {
  updateBootstrap({ status: 'starting-node', process: { status: 'starting', mode: 'temporary-app-managed' } });
  const health = await apiClient.health();
  if (health.reachable) {
    updateBootstrap({
      status: 'running',
      process: { status: 'running', error: null, pid: null, external: true, mode: 'existing-local-api' },
      logs: [...bootstrapState.logs, 'connected to existing local AetherMesh API'].slice(-500),
    });
    return;
  }
  assertPortAvailableForAetherMesh(health);
  supervisor = new NodeSupervisor({
    aethermeshCommand: runtimeCommand,
    env: {
      ...process.env,
      AETHERMESH_HOME: paths.home,
    },
  });
  await supervisor.start({ host: settings.nodeHost, port: settings.nodePort });
  updateBootstrap({ status: 'waiting-api', process: { ...supervisor.state, mode: 'temporary-app-managed' }, logs: supervisor.logs });
  await waitForApi();
  updateBootstrap({ status: 'running', process: { ...supervisor.state, mode: 'temporary-app-managed' }, logs: supervisor.logs });
}

async function startBackgroundNode(paths = getPaths(), settings = readSettings(paths)) {
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  updateBootstrap({ status: 'starting-background-node', background: { ...backgroundStateFromSettings(settings), status: 'starting' } });
  const health = await apiClient.health();
  if (!health.reachable) {
    await manager.startBackgroundNode();
    await waitForApi();
  }
  updateBootstrap({
    status: 'running',
    background: { ...backgroundStateFromSettings(settings), status: 'running', runtime: manager.readRuntimeMetadata() },
    process: { status: 'running', pid: null, mode: 'background-os-managed' },
  });
}

function assertPortAvailableForAetherMesh(health) {
  if (health?.error && /failed with HTTP/i.test(health.error)) {
    throw new Error(`port ${apiPort} is in use but is not serving the AetherMesh API: ${health.error}`);
  }
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

function stopTemporaryNode(settings = readSettings(getPaths())) {
  if (!shouldStopTemporaryNode(settings)) {
    return;
  }
  if (supervisor) {
    supervisor.stop();
  }
  updateBootstrap({ process: supervisor ? { ...supervisor.state, mode: 'temporary-app-managed' } : { status: 'stopped', mode: 'temporary-app-managed' }, logs: supervisor ? supervisor.logs : [] });
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

function defaultSettings() {
  return {
    runtime: {
      source: 'bundled',
      allowDeveloperPythonFallback: !app.isPackaged,
    },
    package: normalizePackageSettings({ autoUpdateOnLaunch: false }),
    backgroundNodeEnabled: false,
    startNodeAtLogin: false,
    keepNodeRunningAfterClose: false,
    nodeHost: apiHost,
    nodePort: apiPort,
    installedRuntimePath: null,
    installedRuntimeVersion: null,
    installedRuntimeSha256: null,
    lastUpdateCheckTimestamp: null,
    cliInstalled: false,
    cliCommandName: 'aethermesh',
    cliShimPath: null,
    cliTargetRuntimePath: null,
    cliInstalledAt: null,
    cliLastVerifiedAt: null,
    cliRuntimeVersion: null,
    cliRuntimeSha256: null,
    cliPathStatus: 'not installed',
    cliPathSetupCommand: null,
    advancedLogs: false,
  };
}

function readSettings(paths) {
  const settingsPath = path.join(paths.configDir, 'desktop-settings.json');
  const defaults = defaultSettings();
  if (!fs.existsSync(settingsPath)) {
    fs.mkdirSync(paths.configDir, { recursive: true });
    fs.writeFileSync(settingsPath, `${JSON.stringify(defaults, null, 2)}\n`);
    return defaults;
  }
  return normalizeSettings({ ...defaults, ...JSON.parse(fs.readFileSync(settingsPath, 'utf8')) });
}

function normalizeSettings(settings) {
  return {
    ...defaultSettings(),
    ...settings,
    package: normalizePackageSettings(settings.package || {}),
    nodeHost: settings.nodeHost || settings.api?.host || apiHost,
    nodePort: settings.nodePort || settings.api?.port || apiPort,
  };
}

function writeSettings(paths, partial) {
  const current = readSettings(paths);
  const next = normalizeSettings({ ...current, ...partial });
  fs.mkdirSync(paths.configDir, { recursive: true });
  fs.writeFileSync(path.join(paths.configDir, 'desktop-settings.json'), `${JSON.stringify(next, null, 2)}\n`);
  return next;
}

function backgroundStateFromSettings(settings) {
  return {
    enabled: Boolean(settings.backgroundNodeEnabled),
    startAtLogin: Boolean(settings.startNodeAtLogin),
    keepNodeRunningAfterClose: Boolean(settings.keepNodeRunningAfterClose),
    status: settings.backgroundNodeEnabled ? 'enabled' : 'disabled',
    apiUrl: `http://${settings.nodeHost}:${settings.nodePort}`,
    installedRuntimePath: settings.installedRuntimePath,
    installedRuntimeVersion: settings.installedRuntimeVersion,
    installedRuntimeSha256: settings.installedRuntimeSha256,
    lastUpdateCheckTimestamp: settings.lastUpdateCheckTimestamp,
  };
}

function cliStateFromSettings(settings, cliMetadata = null) {
  const installed = Boolean(cliMetadata?.cliInstalled ?? settings.cliInstalled);
  const verificationOk = cliMetadata?.cliVerificationOk;
  const pathStatus = cliMetadata?.cliPathStatus || settings.cliPathStatus || 'not installed';
  return {
    installed,
    status: installed ? (verificationOk === false ? 'Broken' : 'Installed') : 'Not installed',
    command: cliMetadata?.cliCommandName || settings.cliCommandName || 'aethermesh',
    shimPath: cliMetadata?.cliShimPath || settings.cliShimPath,
    targetRuntimePath: cliMetadata?.cliTargetRuntimePath || settings.cliTargetRuntimePath || settings.installedRuntimePath,
    runtimeVersion: cliMetadata?.cliRuntimeVersion || settings.cliRuntimeVersion || settings.installedRuntimeVersion,
    runtimeSha256: cliMetadata?.cliRuntimeSha256 || settings.cliRuntimeSha256 || settings.installedRuntimeSha256,
    pathStatus,
    pathSetupCommand: cliMetadata?.cliPathSetupCommand || settings.cliPathSetupCommand,
    lastVerifiedAt: cliMetadata?.cliLastVerifiedAt || settings.cliLastVerifiedAt,
    error: cliMetadata?.cliVerificationError || null,
  };
}

function settingsFromCliMetadata(settings, metadata = {}) {
  return {
    ...settings,
    cliInstalled: Boolean(metadata.cliInstalled),
    cliCommandName: metadata.cliCommandName || settings.cliCommandName,
    cliShimPath: metadata.cliShimPath || settings.cliShimPath,
    cliTargetRuntimePath: metadata.cliTargetRuntimePath || settings.cliTargetRuntimePath,
    cliInstalledAt: metadata.cliInstalledAt || settings.cliInstalledAt,
    cliLastVerifiedAt: metadata.cliLastVerifiedAt || settings.cliLastVerifiedAt,
    cliRuntimeVersion: metadata.cliRuntimeVersion || settings.cliRuntimeVersion,
    cliRuntimeSha256: metadata.cliRuntimeSha256 || settings.cliRuntimeSha256,
    cliPathStatus: metadata.cliPathStatus || settings.cliPathStatus,
    cliPathSetupCommand: metadata.cliPathSetupCommand || settings.cliPathSetupCommand,
  };
}

function settingsFromRuntimeMetadata(settings, metadata, update = {}) {
  return {
    ...settings,
    installedRuntimePath: metadata?.installedPath || settings.installedRuntimePath,
    installedRuntimeVersion: metadata?.version || settings.installedRuntimeVersion,
    installedRuntimeSha256: metadata?.sha256 || settings.installedRuntimeSha256,
    lastUpdateCheckTimestamp: update.checkedAt || settings.lastUpdateCheckTimestamp,
  };
}

async function checkRuntimeUpdates({ restart = false, apply = true } = {}) {
  const paths = getPaths();
  ensureStorage(paths);
  const settings = readSettings(paths);
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  updateBootstrap({ update: { ...bootstrapState.update, status: 'checking' } });
  const check = await manager.checkForRuntimeUpdates();
  let result = { updated: false, update: check };
  if (apply && (settings.backgroundNodeEnabled || settings.cliInstalled) && check.available) {
    result = await manager.applyRuntimeUpdate({ restart: settings.backgroundNodeEnabled && restart });
  }
  const metadata = result.metadata || manager.readRuntimeMetadata();
  let nextSettings = writeSettings(paths, settingsFromRuntimeMetadata(settings, metadata, result.update || check));
  if (nextSettings.cliInstalled && metadata) {
    const cliMetadata = await createCliManager(paths, metadata).installOrRepair({ configurePath: false });
    nextSettings = writeSettings(paths, settingsFromCliMetadata(nextSettings, cliMetadata));
  }
  updateBootstrap({
    update: { status: result.updated ? 'updated' : 'current', lastCheck: nextSettings.lastUpdateCheckTimestamp, available: check.available, error: null },
    background: { ...backgroundStateFromSettings(nextSettings), runtime: metadata },
    cli: cliStateFromSettings(nextSettings),
  });
  return { ...result, settings: nextSettings };
}

function scheduleRuntimeUpdateChecks(paths = getPaths()) {
  const settings = readSettings(paths);
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  manager.schedulePeriodicUpdateChecks({
    intervalMs: UPDATE_INTERVAL_MS,
    shouldApply: () => {
      const current = readSettings(paths);
      return current.backgroundNodeEnabled || current.cliInstalled;
    },
    shouldRestart: () => readSettings(paths).backgroundNodeEnabled,
    onResult: (error, result) => {
      if (error) {
        updateBootstrap({ update: { ...bootstrapState.update, status: 'error', error: error.message } });
        return;
      }
      const latest = result?.metadata || manager.readRuntimeMetadata();
      const currentSettings = readSettings(paths);
      let nextSettings = writeSettings(paths, settingsFromRuntimeMetadata(currentSettings, latest, result?.update || {}));
      if (nextSettings.cliInstalled && latest) {
        createCliManager(paths, latest).installOrRepair({ configurePath: false }).then((cliMetadata) => {
          const refreshed = writeSettings(paths, settingsFromCliMetadata(readSettings(paths), cliMetadata));
          updateBootstrap({ cli: cliStateFromSettings(refreshed, cliMetadata) });
        }).catch((cliError) => {
          updateBootstrap({ cli: { ...bootstrapState.cli, status: 'Broken', error: cliError.message } });
        });
      }
      updateBootstrap({
        update: { status: result?.updated ? 'updated' : 'current', lastCheck: nextSettings.lastUpdateCheckTimestamp, available: result?.update?.available || false, error: null },
        background: { ...backgroundStateFromSettings(nextSettings), runtime: latest },
        cli: cliStateFromSettings(nextSettings),
      });
    },
  });
}

async function repairCli({ configurePath = true } = {}) {
  const paths = getPaths();
  ensureStorage(paths);
  const settings = readSettings(paths);
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  const runtime = manager.copyOrUpdateRuntime();
  const cli = createCliManager(paths, runtime.metadata);
  const cliMetadata = await cli.installOrRepair({ configurePath });
  const nextSettings = writeSettings(paths, settingsFromCliMetadata(settingsFromRuntimeMetadata(settings, runtime.metadata, { checkedAt: new Date().toISOString() }), cliMetadata));
  updateBootstrap({ cli: cliStateFromSettings(nextSettings, cliMetadata), background: { ...backgroundStateFromSettings(nextSettings), runtime: runtime.metadata } });
  return bootstrapState;
}

async function uninstallCli() {
  const paths = getPaths();
  const settings = readSettings(paths);
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  const cli = createCliManager(paths, manager.readRuntimeMetadata());
  const cliMetadata = await cli.uninstall();
  const nextSettings = writeSettings(paths, settingsFromCliMetadata(settings, cliMetadata));
  updateBootstrap({ cli: cliStateFromSettings(nextSettings, cliMetadata) });
  return bootstrapState;
}

async function refreshCliStatus() {
  const paths = getPaths();
  const settings = readSettings(paths);
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  const cli = createCliManager(paths, manager.readRuntimeMetadata());
  const cliMetadata = await cli.getStatus();
  const nextSettings = writeSettings(paths, settingsFromCliMetadata(settings, cliMetadata));
  updateBootstrap({ cli: cliStateFromSettings(nextSettings, cliMetadata) });
  return bootstrapState;
}

async function enableBackgroundNode() {
  const paths = getPaths();
  ensureStorage(paths);
  let settings = writeSettings(paths, { backgroundNodeEnabled: true, startNodeAtLogin: true, keepNodeRunningAfterClose: true });
  const manager = createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  const install = await manager.installBackgroundNode();
  settings = writeSettings(paths, settingsFromRuntimeMetadata(settings, install.metadata, { checkedAt: new Date().toISOString() }));
  const cliMetadata = await createCliManager(paths, install.metadata).installOrRepair({ configurePath: false });
  settings = writeSettings(paths, settingsFromCliMetadata(settings, cliMetadata));
  updateBootstrap({
    status: 'running',
    background: { ...backgroundStateFromSettings(settings), status: 'running', runtime: install.metadata },
    cli: cliStateFromSettings(settings, cliMetadata),
    process: { status: 'running', pid: null, mode: 'background-os-managed' },
  });
  await waitForApi();
  return bootstrapState;
}

async function disableBackgroundNode({ removeData = false } = {}) {
  const paths = getPaths();
  const settings = readSettings(paths);
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  backgroundManager = manager;
  await manager.uninstallBackgroundNode();
  const nextSettings = writeSettings(paths, { backgroundNodeEnabled: false, startNodeAtLogin: false, keepNodeRunningAfterClose: false });
  if (removeData) {
    throw new Error('Removing local AetherMesh data is intentionally not implemented in this release');
  }
  updateBootstrap({
    status: 'stopped',
    background: backgroundStateFromSettings(nextSettings),
    process: { status: 'stopped', mode: 'temporary-app-managed' },
  });
  return bootstrapState;
}

async function removeLocalAetherMeshData() {
  const paths = getPaths();
  const settings = readSettings(paths);
  if (settings.backgroundNodeEnabled) {
    await disableBackgroundNode();
  } else {
    stopTemporaryNode(settings);
  }
  if (paths.logsDir && paths.logsDir !== paths.home && fs.existsSync(paths.logsDir)) {
    fs.rmSync(paths.logsDir, { recursive: true, force: true });
  }
  if (fs.existsSync(paths.home)) {
    fs.rmSync(paths.home, { recursive: true, force: true });
  }
  updateBootstrap({
    status: 'removed-local-data',
    storage: {},
    background: { enabled: false, startAtLogin: false, status: 'disabled' },
    process: { status: 'stopped', mode: 'temporary-app-managed' },
    logs: ['local AetherMesh data removed'],
  });
  return bootstrapState;
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
  const paths = getPaths();
  ensureStorage(paths);
  const settings = readSettings(paths);
  if (settings.backgroundNodeEnabled) {
    await startBackgroundNode(paths, settings);
  } else if (!supervisor || supervisor.state.status !== 'running') {
    await startTemporaryNode(paths, settings);
  }
  return bootstrapState;
});
ipcMain.handle('aethermesh:stop-node', async () => {
  const paths = getPaths();
  const settings = readSettings(paths);
  if (settings.backgroundNodeEnabled) {
    const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
    await manager.stopBackgroundNode();
    updateBootstrap({ process: { status: 'stopped', mode: 'background-os-managed' }, background: { ...backgroundStateFromSettings(settings), status: 'stopped' } });
  } else {
    stopTemporaryNode(settings);
  }
  return bootstrapState;
});
ipcMain.handle('aethermesh:restart-node', async () => {
  const paths = getPaths();
  const settings = readSettings(paths);
  if (settings.backgroundNodeEnabled) {
    const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
    await manager.stopBackgroundNode({ ignoreErrors: true });
    await manager.startBackgroundNode();
    await waitForApi();
  } else {
    stopTemporaryNode(settings);
    await startTemporaryNode(paths, settings);
  }
  return bootstrapState;
});
ipcMain.handle('aethermesh:enable-background-node', enableBackgroundNode);
ipcMain.handle('aethermesh:disable-background-node', () => disableBackgroundNode());
ipcMain.handle('aethermesh:remove-local-data', removeLocalAetherMeshData);
ipcMain.handle('aethermesh:repair-cli', () => repairCli({ configurePath: true }));
ipcMain.handle('aethermesh:reinstall-cli', () => repairCli({ configurePath: true }));
ipcMain.handle('aethermesh:uninstall-cli', uninstallCli);
ipcMain.handle('aethermesh:get-cli-status', refreshCliStatus);
ipcMain.handle('aethermesh:check-runtime-updates', () => checkRuntimeUpdates({ restart: true, apply: true }));
ipcMain.handle('aethermesh:read-background-logs', () => {
  const paths = getPaths();
  const settings = readSettings(paths);
  const manager = backgroundManager || createBackgroundManager(paths, getRuntimeCommand(), settings);
  return manager.readRecentLogs();
});
ipcMain.handle('aethermesh:platform-notes', () => platformNotes());

app.whenReady().then(() => {
  createWindow();
  bootstrap();
});

app.on('before-quit', () => {
  shutdownStarted = true;
  const paths = getPaths();
  const settings = readSettings(paths);
  stopTemporaryNode(settings);
  if (backgroundManager && !settings.backgroundNodeEnabled) {
    backgroundManager.clearPeriodicUpdateChecks();
  }
});

app.on('window-all-closed', () => {
  const paths = getPaths();
  const settings = readSettings(paths);
  try {
    if (!shutdownStarted) {
      stopTemporaryNode(settings);
    }
  } finally {
    if (process.platform !== 'darwin') app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

module.exports = { appendBootstrapLog, backgroundStateFromSettings, defaultSettings, normalizeSettings };

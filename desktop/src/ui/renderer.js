const els = {
  node: document.getElementById('node-status'),
  bootstrap: document.getElementById('bootstrap-status'),
  package: document.getElementById('package-status'),
  api: document.getElementById('api-status'),
  background: document.getElementById('background-status'),
  onboarding: document.getElementById('background-onboarding'),
  peers: document.getElementById('peer-list'),
  capabilities: document.getElementById('capability-list'),
  logs: document.getElementById('logs'),
  settings: document.getElementById('settings'),
  refresh: document.getElementById('refresh'),
  start: document.getElementById('start'),
  stop: document.getElementById('stop'),
  restart: document.getElementById('restart'),
  enableBackground: document.getElementById('enable-background'),
  enableBackgroundOnboarding: document.getElementById('enable-background-onboarding'),
  disableBackground: document.getElementById('disable-background'),
  checkUpdates: document.getElementById('check-updates'),
  viewBackgroundLogs: document.getElementById('view-background-logs'),
  removeLocalData: document.getElementById('remove-local-data'),
};

let bootstrapState = {};

function setRows(target, rows) {
  target.replaceChildren();
  for (const [key, value] of rows) {
    const dt = document.createElement('dt');
    dt.textContent = key;
    const dd = document.createElement('dd');
    dd.textContent = value ?? 'unknown';
    target.append(dt, dd);
  }
}

function formatBool(value) {
  return value ? 'enabled' : 'disabled';
}

function shortHash(value) {
  return value ? `${value.slice(0, 12)}…` : 'not installed';
}

function setBootstrap(state) {
  bootstrapState = state || {};
  setRows(els.bootstrap, [
    ['Desktop status', bootstrapState.status],
    ['Runtime', bootstrapState.runtime?.command || 'checking'],
    ['Runtime mode', bootstrapState.runtime?.mode || 'bundled'],
    ['Process', bootstrapState.process?.status || 'stopped'],
    ['Process mode', bootstrapState.process?.mode || 'temporary-app-managed'],
    ['Storage', bootstrapState.storage?.home || 'pending'],
    ['Error', bootstrapState.error || 'none'],
  ]);
  renderBackground(bootstrapState);
  els.logs.textContent = (bootstrapState.logs || []).join('\n') || 'Waiting for bootstrap...';
}

function renderBackground(state) {
  const bg = state.background || {};
  const update = state.update || {};
  setRows(els.background, [
    ['Node status', state.process?.status || 'stopped'],
    ['Mode', bg.enabled ? 'Background OS-managed' : 'Temporary app-managed'],
    ['API URL', bg.apiUrl || 'http://127.0.0.1:7280'],
    ['Start at login', formatBool(bg.startAtLogin)],
    ['Runtime path', bg.installedRuntimePath || state.runtime?.stablePath || 'not installed'],
    ['Runtime version', bg.installedRuntimeVersion || bg.runtime?.version || 'not installed'],
    ['Runtime sha256', shortHash(bg.installedRuntimeSha256 || bg.runtime?.sha256)],
    ['Last update check', bg.lastUpdateCheckTimestamp || update.lastCheck || 'never'],
    ['Update status', update.error || update.status || 'idle'],
  ]);
  els.onboarding.hidden = Boolean(bg.enabled);
}

async function refreshDashboard() {
  const [state, health] = await Promise.all([
    window.aethermesh.getState(),
    window.aethermesh.getHealth(),
  ]);
  setBootstrap(state);
  setRows(els.api, [
    ['Connection', health.reachable ? 'reachable' : 'unreachable'],
    ['Endpoint', 'http://127.0.0.1:7280'],
    ['Error', health.error || 'none'],
  ]);

  if (!health.reachable) {
    setRows(els.node, [['Status', state.process?.status || 'starting']]);
    setRows(els.package, [
      ['Installed', state.package?.installed ? 'yes' : 'no'],
      ['Source', state.package?.source || 'bundled-runtime'],
    ]);
    return;
  }

  const dashboard = await window.aethermesh.getDashboard();
  setRows(els.node, [
    ['Status', dashboard.status.status],
    ['Node ID', dashboard.status.node_id],
    ['Uptime', dashboard.status.uptime_seconds === null ? 'not running' : `${dashboard.status.uptime_seconds}s`],
    ['Peer count', dashboard.status.peer_count],
    ['Config', dashboard.status.config_path],
  ]);
  setRows(els.package, [
    ['Installed', state.package?.installed ? 'yes' : 'no'],
    ['Version', dashboard.package.version],
    ['Source', state.package?.source || dashboard.package.source],
  ]);
  setRows(els.settings, [
    ['Runtime source', state.runtime?.mode || 'bundled'],
    ['Package updates', 'bundled runtime updates'],
    ['Keep node running after close', formatBool(state.background?.keepNodeRunningAfterClose)],
    ['API bind', `${dashboard.status.api.host}:${dashboard.status.api.port}`],
    ['Advanced logs', 'off'],
  ]);
  renderPeers(dashboard.peers.peers);
  renderCapabilities(dashboard.capabilities.capabilities);
  els.logs.textContent = [
    ...(state.logs || []),
    ...(dashboard.logs.events || []),
  ].slice(-120).join('\n') || 'No logs yet.';
}

function renderPeers(peers) {
  els.peers.replaceChildren();
  if (!peers || peers.length === 0) {
    els.peers.textContent = 'No peers discovered yet.';
    return;
  }
  for (const peer of peers) {
    const row = document.createElement('div');
    row.textContent = `${peer.node_id} ${peer.status || ''}`;
    els.peers.append(row);
  }
}

function renderCapabilities(capabilities) {
  els.capabilities.replaceChildren();
  for (const capability of capabilities || []) {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = capability;
    els.capabilities.append(chip);
  }
}

function runAction(action) {
  return action().then(refreshDashboard).catch(showError);
}

els.refresh.addEventListener('click', () => refreshDashboard().catch(showError));
els.start.addEventListener('click', () => runAction(() => window.aethermesh.startNode()));
els.stop.addEventListener('click', () => runAction(() => window.aethermesh.stopNode()));
els.restart.addEventListener('click', () => runAction(() => window.aethermesh.restartNode()));
els.enableBackground.addEventListener('click', () => runAction(() => window.aethermesh.enableBackgroundNode()));
els.enableBackgroundOnboarding.addEventListener('click', () => runAction(() => window.aethermesh.enableBackgroundNode()));
els.disableBackground.addEventListener('click', () => runAction(() => window.aethermesh.disableBackgroundNode()));
els.checkUpdates.addEventListener('click', () => runAction(() => window.aethermesh.checkRuntimeUpdates()));
els.viewBackgroundLogs.addEventListener('click', () => window.aethermesh.readBackgroundLogs().then((logs) => {
  els.logs.textContent = logs || 'No background logs yet.';
}).catch(showError));
els.removeLocalData.addEventListener('click', () => {
  const confirmed = window.confirm('Remove local AetherMesh data, config, runtime metadata, and logs from this user account? This cannot be undone.');
  if (confirmed) {
    runAction(() => window.aethermesh.removeLocalData());
  }
});
window.aethermesh.onState(setBootstrap);

function showError(error) {
  els.logs.textContent = error.stack || String(error);
  els.logs.classList.add('error');
}

refreshDashboard().catch(showError);
setInterval(() => refreshDashboard().catch(() => {}), 2500);

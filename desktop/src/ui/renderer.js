const els = {
  node: document.getElementById('node-status'),
  bootstrap: document.getElementById('bootstrap-status'),
  package: document.getElementById('package-status'),
  api: document.getElementById('api-status'),
  peers: document.getElementById('peer-list'),
  capabilities: document.getElementById('capability-list'),
  logs: document.getElementById('logs'),
  settings: document.getElementById('settings'),
  refresh: document.getElementById('refresh'),
  start: document.getElementById('start'),
  stop: document.getElementById('stop'),
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

function setBootstrap(state) {
  bootstrapState = state || {};
  setRows(els.bootstrap, [
    ['Desktop status', bootstrapState.status],
    ['Runtime', bootstrapState.runtime?.command || 'checking'],
    ['Runtime mode', bootstrapState.runtime?.mode || 'bundled'],
    ['Process', bootstrapState.process?.status || 'stopped'],
    ['Storage', bootstrapState.storage?.home || 'pending'],
    ['Error', bootstrapState.error || 'none'],
  ]);
  els.logs.textContent = (bootstrapState.logs || []).join('\n') || 'Waiting for bootstrap...';
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
    ['Package updates', 'manual app/runtime updates'],
    ['Keep node running after close', 'off'],
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

els.refresh.addEventListener('click', () => refreshDashboard().catch(showError));
els.start.addEventListener('click', () => window.aethermesh.startNode().then(refreshDashboard).catch(showError));
els.stop.addEventListener('click', () => window.aethermesh.stopNode().then(refreshDashboard).catch(showError));
window.aethermesh.onState(setBootstrap);

function showError(error) {
  els.logs.textContent = error.stack || String(error);
  els.logs.classList.add('error');
}

refreshDashboard().catch(showError);
setInterval(() => refreshDashboard().catch(() => {}), 2500);

"""Local FastAPI app for the AetherMesh node dashboard."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from aethermesh_core.runtime_service import NodeRuntimeService


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    service: NodeRuntimeService = app.state.service
    service.start_node_runtime()
    try:
        yield
    finally:
        service.mark_runtime_stopped()


def create_app(service: NodeRuntimeService | None = None) -> FastAPI:
    """Create the localhost API/dashboard app used by CLI and UI frontends."""

    runtime_service = service or NodeRuntimeService.default()
    app = FastAPI(
        title="AetherMesh Local Node API",
        version="0.2.0-alpha",
        lifespan=_lifespan,
    )
    app.state.service = runtime_service

    @app.get("/health")
    def health() -> dict[str, Any]:
        return runtime_service.health()

    @app.get("/status")
    @app.get("/api/status")
    def status() -> dict[str, Any]:
        return runtime_service.get_node_status()

    @app.get("/version")
    def version() -> dict[str, Any]:
        return runtime_service.package_info()

    @app.get("/node")
    @app.get("/api/node")
    def node() -> dict[str, Any]:
        return runtime_service.get_node_status()

    @app.get("/peers")
    @app.get("/api/peers")
    def peers() -> dict[str, Any]:
        return runtime_service.list_peers()

    @app.get("/api/jobs")
    def jobs() -> dict[str, Any]:
        return runtime_service.list_jobs()

    @app.get("/capabilities")
    @app.get("/api/capabilities")
    def capabilities() -> dict[str, Any]:
        return runtime_service.list_capabilities()

    @app.get("/api/package")
    def package() -> dict[str, Any]:
        return runtime_service.package_info()

    @app.get("/api/network")
    def network() -> dict[str, Any]:
        return runtime_service.network_health()

    @app.get("/logs")
    @app.get("/api/logs")
    def logs() -> dict[str, Any]:
        return runtime_service.recent_logs()

    @app.get("/api/events")
    def events() -> dict[str, Any]:
        return runtime_service.recent_logs()

    @app.post("/shutdown")
    def shutdown() -> dict[str, Any]:
        app.state.shutdown_requested = True
        return {"shutdown_requested": True, "restart_requested": False}

    @app.post("/restart")
    def restart() -> dict[str, Any]:
        app.state.restart_requested = True
        return {"shutdown_requested": True, "restart_requested": True}

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return DASHBOARD_HTML

    return app


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AetherMesh Local Node</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    body { margin: 0; background: #090d14; color: #eef3ff; }
    header { padding: 24px 28px; border-bottom: 1px solid #202838; background: #0d1420; }
    h1 { margin: 0 0 6px; font-size: 24px; }
    main { padding: 24px; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
    section { border: 1px solid #243044; border-radius: 14px; background: #101827; padding: 18px; box-shadow: 0 12px 30px rgba(0,0,0,.25); }
    h2 { margin: 0 0 12px; font-size: 17px; color: #b9cdfb; }
    dl { margin: 0; }
    dt { color: #8ea0bd; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; margin-top: 10px; }
    dd { margin: 3px 0 0; word-break: break-word; }
    button { margin-top: 14px; padding: 9px 12px; border: 0; border-radius: 10px; background: #6aa9ff; color: #06111f; font-weight: 700; cursor: pointer; }
    pre { white-space: pre-wrap; background: #080c13; border: 1px solid #202838; border-radius: 10px; padding: 10px; max-height: 220px; overflow: auto; }
    .muted { color: #9aa8bf; }
  </style>
</head>
<body>
  <header>
    <h1>AetherMesh Local Node</h1>
    <div class="muted">Localhost dashboard backed by the reusable Python node service and API.</div>
    <button onclick="refreshAll()">Refresh</button>
  </header>
  <main>
    <section><h2>Node</h2><dl id="node"></dl></section>
    <section><h2>Network</h2><dl id="network"></dl></section>
    <section><h2>Work</h2><dl id="work"></dl></section>
    <section><h2>System</h2><dl id="system"></dl></section>
    <section style="grid-column: 1 / -1"><h2>Logs / Events</h2><pre id="logs">Loading...</pre></section>
  </main>
<script>
async function getJson(path) {
  const response = await fetch(path, {cache: 'no-store'});
  if (!response.ok) throw new Error(path + ' failed: ' + response.status);
  return await response.json();
}
function dl(target, rows) {
  const list = document.getElementById(target);
  list.replaceChildren();
  for (const [key, value] of rows) {
    const term = document.createElement('dt');
    term.textContent = key;
    const description = document.createElement('dd');
    description.textContent = value ?? 'unknown';
    list.append(term, description);
  }
}
async function refreshAll() {
  const [status, peers, jobs, logs] = await Promise.all([
    getJson('/api/status'), getJson('/api/peers'), getJson('/api/jobs'), getJson('/api/logs')
  ]);
  dl('node', [
    ['Node ID', status.node_id], ['Node Name', status.node_name], ['Status', status.status],
    ['Version', status.version],
    ['Uptime', status.uptime_seconds === null ? 'not running' : status.uptime_seconds + 's'],
    ['Config', status.config_path], ['Data directory', status.data_dir]
  ]);
  dl('network', [
    ['Connected peers', peers.peer_count], ['Bootstrap', peers.bootstrap_status],
    ['Peer list', peers.peers.length ? JSON.stringify(peers.peers) : 'No peers discovered']
  ]);
  dl('work', [
    ['Current jobs', jobs.current.length], ['Completed jobs', jobs.completed.length],
    ['Failed jobs', jobs.failed.length], ['Validation', jobs.validation_status]
  ]);
  dl('system', [
    ['Platform', status.system.platform], ['Python', status.system.python_version],
    ['CPU count', status.system.cpu_count], ['RAM total', status.system.memory_total_bytes || 'unknown'],
    ['Data disk free', status.system.disk_data_path_free_bytes]
  ]);
  document.getElementById('logs').textContent = logs.events.length ? logs.events.join('\n') : 'No events yet.';
}
refreshAll().catch(err => { document.getElementById('logs').textContent = err.stack || String(err); });
</script>
</body>
</html>
"""

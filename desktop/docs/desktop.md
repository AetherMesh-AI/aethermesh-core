# AetherMesh Desktop

AetherMesh Desktop is an Electron controller/viewer with a bundled AetherMesh runtime sidecar.

## Runtime model

The UI is not the node process. The packaged app includes a platform-specific runtime binary:

- macOS: `aethermesh-node`
- Windows: `aethermesh-node.exe`
- Linux: `aethermesh-node`

Production desktop builds do not ask normal users to install Python, run pip, or install a global CLI. Python detection, venv creation, and package install helpers remain development/repair fallback utilities only.

## Two node modes

### Temporary app-managed mode

This is the default when the user has not enabled background mode:

```text
AetherMesh Desktop
  -> bundled runtime sidecar in app resources
  -> aethermesh-node init
  -> aethermesh-node node start --host 127.0.0.1 --port 7280
  -> stop supervised child process when the app/window closes
```

### Background OS-managed mode

When the user enables **Run AetherMesh in the background**, the app copies the bundled runtime into a stable per-user runtime directory and registers it with the operating system:

- macOS: `~/Library/Application Support/AetherMesh/runtime/aethermesh-node`
- Windows: `%LOCALAPPDATA%/AetherMesh/runtime/aethermesh-node.exe`
- Linux: `~/.local/share/aethermesh/runtime/aethermesh-node`

The OS then manages startup/restart:

- macOS: per-user LaunchAgent at `~/Library/LaunchAgents/dev.aethermesh.node.plist`
- Windows: per-user Task Scheduler task named `AetherMesh Node`
- Linux: systemd user service at `~/.config/systemd/user/aethermesh-node.service`

Closing the Electron window or quitting the app does not stop the OS-managed node while background mode is enabled. Disabling background mode stops/unregisters the OS-managed node but leaves user data intact.

## Storage

The launcher uses per-user app storage:

- macOS: `~/Library/Application Support/AetherMesh/`
- Windows: `%LOCALAPPDATA%/AetherMesh/`
- Linux: `${XDG_DATA_HOME}/aethermesh/` or `~/.local/share/aethermesh/`

Recommended log locations:

- macOS: `~/Library/Logs/AetherMesh/node.log`
- Windows: `%LOCALAPPDATA%/AetherMesh/logs/node.log`
- Linux: `${XDG_STATE_HOME}/aethermesh/logs/node.log` or `~/.local/state/aethermesh/logs/node.log`

Inside the data folder it keeps:

- `runtime/` stable copied runtime
- `config/desktop-settings.json`
- `metadata/runtime.json`
- `metadata/runtime.previous.json` when a runtime update replaces an older runtime
- local node data owned by the runtime via `AETHERMESH_HOME`

## Startup flow

1. Create per-user storage/log/runtime directories.
2. Resolve the bundled runtime sidecar from app resources.
3. Health-check `http://127.0.0.1:7280/health`.
4. If healthy, reconnect the UI to the already-running node.
5. If unhealthy and background mode is enabled, ask the OS background manager to start the registered node, then health-check again.
6. If background mode is disabled, use the temporary supervised sidecar process.
7. Check whether the stable runtime needs to be updated from the bundled runtime.
8. Schedule periodic runtime update checks every 60 seconds.

## Runtime update behavior

Runtime updates compare the installed stable runtime metadata with the bundled runtime from the current app build:

- version
- sha256
- source path
- installed path
- installed timestamp

When the bundled runtime is newer or has a different hash, the app:

1. Stops the background node if it is running.
2. Copies the new runtime to a temporary file.
3. Marks it executable on macOS/Linux.
4. Atomically renames it over the stable runtime.
5. Writes backup metadata for the previous runtime.
6. Re-runs `aethermesh-node init`.
7. Restarts the background node if background mode was enabled.

Updates preserve config, data, node identity, keys, peers, and contribution data. Future gossip-triggered update checks should call this same update path.

## Development commands

From the repo root:

```bash
npm install
npm run test:desktop
npm run desktop:dev
npm run runtime:build
npm run runtime:copy
npm run desktop:build
npm run desktop:build:mac
npm run desktop:build:win
npm run desktop:build:linux
npm run desktop:clean
```

Development mode can run against `AETHERMESH_RUNTIME_PATH=/path/to/aethermesh-node` or fall back to the local `aethermesh` command when no sidecar has been built yet.

## Packaging targets

Electron Builder is configured for:

- macOS `.dmg`
- Windows NSIS `.exe`
- Linux `.deb`

The release workflow builds one installer per platform/architecture matrix and attaches exactly those installers to the latest GitHub release. Release names use the actual source archive hash suffix:

```text
0.2.0-alpha - (...<last 5 chars of source archive sha256>)
```

## Manual validation

See `desktop/docs/background-node.md` for the platform-specific manual test plan.

## Security defaults

- No Docker.
- No curl/bash remote script execution.
- No silent system Python install.
- No global pip install.
- No PATH mutation by default.
- Local API binds to `127.0.0.1` by default.
- No LAN/WAN API exposure by default.
- No admin/root daemon by default.
- No telemetry.
- No centralized AetherMesh infrastructure.

## Deferred work

- Developer ID signing and notarization for frictionless macOS first launch.
- Optional terminal CLI exposure via an explicit future install action.
- Advanced admin/system-wide service mode.
- Dynamic update check intervals driven by gossip/outdated-version signals.

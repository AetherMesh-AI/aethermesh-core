# AetherMesh Desktop MVP

AetherMesh Desktop is an Electron launcher with a bundled AetherMesh runtime sidecar.

## Why Electron

The repo does not currently contain a JavaScript/React/Vite web app to wrap, and the existing UI/API boundary is already localhost-oriented. Electron is the smallest practical cross-platform path here because it can ship a packaged HTML/CSS/JS shell while supervising a bundled node runtime process.

The desktop app remains a controller/viewer:

```text
AetherMesh Desktop
  -> packaged HTML/CSS/JS dashboard
  -> bundled runtime sidecar in app resources
  -> runs aethermesh-node init
  -> supervises aethermesh-node node start --host 127.0.0.1 --port 7280
  -> reads local API JSON endpoints
```

The UI is not the node process.

## Runtime sidecar

Production desktop builds do not ask normal users to install Python, open a terminal, or run pip. The installer includes a platform-specific runtime binary:

- macOS: `aethermesh-node`
- Windows: `aethermesh-node.exe`
- Linux: `aethermesh-node`

The runtime is built from the Python package with PyInstaller and copied into Electron resources under `runtime/`. The Electron main process resolves that bundled binary in packaged builds and starts it directly.

Python detection, venv creation, and package install helpers remain in the source tree as development/repair fallback utilities only. They are not the normal user startup path.

## Storage

The launcher uses per-user app storage:

- macOS: `~/Library/Application Support/AetherMesh/`
- Windows: `%APPDATA%/AetherMesh/`
- Linux: `${XDG_DATA_HOME}/AetherMesh/` or `~/.local/share/AetherMesh/`

Inside that folder it keeps:

- `logs/` launcher/node logs
- `config/desktop-settings.json`
- `metadata/process-state.json`
- local node data owned by the bundled runtime via `AETHERMESH_HOME`

## Startup flow

1. Resolve bundled runtime sidecar from app resources.
2. Create app data directories.
3. Reconnect to an already-running local API if one is reachable.
4. Otherwise run `aethermesh-node init`.
5. Start `aethermesh-node node start --host 127.0.0.1 --port 7280`.
6. Wait for the local API to become reachable.
7. Load dashboard data from the local API.

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

- macOS `.app`/`.dmg`
- Windows NSIS `.exe`
- Linux `AppImage` and `.deb`

The release workflow builds the sidecar and desktop app per platform/architecture matrix and attaches artifacts to tagged GitHub releases. Release names use the actual source archive hash suffix:

```text
0.2.0-alpha - (...<last 5 chars of source archive sha256>)
```

GitHub releases are created/edited with `--latest` so the newest release is marked current/latest when GitHub supports it.

## Security defaults

- No Docker.
- No curl/bash remote script execution.
- No silent system Python install.
- No global pip install.
- No PATH mutation by default.
- Local API binds to `127.0.0.1` by default.
- No telemetry.
- No centralized AetherMesh infrastructure.

## Current MVP limits

- Runtime sidecars are built with PyInstaller, not signed app-update infrastructure yet.
- Normal app/runtime updates are manual release downloads for now.
- Optional terminal CLI exposure is intentionally deferred; future versions can add a safe shim/symlink button.

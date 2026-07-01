# CLI and Local UI Architecture

AetherMesh now has first-class local frontends while keeping the node logic in reusable Python modules.

## Shape

```text
pipx / Python environment
  |
  v
aethermesh command
  |
  +-- CLI commands (Typer + Rich)
  |     |
  |     v
  |  NodeRuntimeService
  |
  +-- local API daemon (FastAPI + Uvicorn, localhost by default)
        |
        v
     NodeRuntimeService
        |
        v
  reusable AetherMesh core modules
  identity, jobs, scheduling, dispatch, validation, ledger, receipts, transport

browser / future desktop shell
  |
  v
http://127.0.0.1:7280
  |
  v
FastAPI dashboard routes and JSON API
```

The UI is not the core of the system. The local dashboard talks to the local API, and the API calls the same Python service layer that the CLI uses. Future desktop packaging should keep this boundary instead of importing node internals directly from a UI shell.

## Install

Minimal CLI and node package:

```bash
pipx install aethermesh
```

CLI plus local API/UI dependencies:

```bash
pipx install "aethermesh[ui]"
```

Development install from the repo root:

```bash
python -m pip install -e ".[dev,ui]"
```

The legacy prototype command remains available as `aethermesh-core` for the existing local flow demos and tests.

## Commands

```bash
aethermesh --version
aethermesh init
aethermesh status
aethermesh node status
aethermesh node start
aethermesh peers
aethermesh jobs
aethermesh ui
```

`aethermesh init` creates local config, identity, data, and log directories. By default these live under:

```text
~/.aethermesh
```

For tests or isolated development, set:

```bash
AETHERMESH_HOME=/tmp/aethermesh-dev aethermesh init
```

## Local API

`aethermesh node start` starts the foreground local node API daemon. It binds to localhost by default:

```text
http://127.0.0.1:7280
```

Current routes:

```text
GET /health
GET /status
GET /version
GET /node
GET /peers
GET /capabilities
GET /logs
POST /shutdown
POST /restart
GET /api/status
GET /api/node
GET /api/peers
GET /api/jobs
GET /api/capabilities
GET /api/package
GET /api/network
GET /api/logs
GET /api/events
GET /
```

The first API version exposes read-only status and dashboard data. It has no destructive admin endpoints.

## Local dashboard

`aethermesh ui` starts the same local API server and opens the browser at:

```text
http://127.0.0.1:7280
```

The first dashboard is intentionally plain. It shows:

- node id, status, version, uptime, config path, and data path
- peer count and discovered peers, currently empty unless a peer source is added later
- current, completed, and failed jobs, currently empty until a persistent daemon queue exists
- basic system information and data-path disk space
- recent local runtime events

The dashboard reads JSON from `/api/status`, `/api/peers`, `/api/jobs`, `/api/capabilities`, `/api/package`, `/api/network`, and `/api/logs`. Desktop-friendly aliases such as `/status`, `/node`, `/peers`, `/capabilities`, and `/logs` are available for the packaged app.

## Security default

The API binds to `127.0.0.1` by default. Do not expose it to the LAN until the project adds explicit operator intent, authentication, authorization, and safer admin controls. The current implementation is for local status and development only.

## Desktop launcher

The desktop MVP lives under `desktop/` and uses Electron because this repo is currently Python-first with a FastAPI-served local dashboard rather than an existing React/Vite app. Normal users do not install Python or run pip. Release builds bundle a PyInstaller-built `aethermesh-node` runtime sidecar inside Electron resources, then the shell runs `aethermesh-node init`, supervises `aethermesh-node node start --host 127.0.0.1 --port 7280`, and reads local API routes from the packaged UI.

Desktop commands:

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

See [../desktop/docs/desktop.md](../desktop/docs/desktop.md) for packaging, storage, and troubleshooting notes.

# AetherMesh Desktop MVP

AetherMesh Desktop is a small Electron launcher around the existing local web/API architecture.

## Why Electron

The repo does not currently contain a JavaScript/React/Vite web app to wrap, and the existing UI is a FastAPI-served local dashboard. Electron is the smallest practical cross-platform path here because it can ship a packaged HTML/CSS/JS shell while supervising the existing Python CLI/API process. This avoids adding Rust/Tauri setup before the UI surface is large enough to benefit from it.

The desktop app remains a controller/viewer:

```text
AetherMesh Desktop
  -> packaged HTML/CSS/JS dashboard
  -> app-managed Python detection + venv
  -> installs/updates aethermesh[ui]
  -> runs aethermesh init
  -> supervises aethermesh node start --host 127.0.0.1 --port 7280
  -> reads local API JSON endpoints
```

The UI is not the node process.

## Storage

The launcher uses per-user app storage:

- macOS: `~/Library/Application Support/AetherMesh/`
- Windows: `%APPDATA%/AetherMesh/`
- Linux: `${XDG_DATA_HOME}/AetherMesh/` or `~/.local/share/AetherMesh/`

Inside that folder it keeps:

- `venv/` private Python environment
- `logs/` launcher/node logs
- `config/desktop-settings.json`
- `metadata/install-status.json`
- `metadata/process-state.json`

## Python and package bootstrap

Startup flow:

1. Detect Python 3.11+ from normal platform executables.
2. If no usable Python is found, show a UI error instead of installing anything silently.
3. Create the private app-managed venv.
4. Install/update `aethermesh[ui]` into that venv.
5. Run `aethermesh init`.
6. Start `aethermesh node start --host 127.0.0.1 --port 7280`.
7. Read dashboard data from the local API.

The default package source is the latest GitHub release wheel. Settings support PyPI and local development paths as well.

## Development commands

From the repo root:

```bash
npm install
npm run test:desktop
npm run desktop:dev
npm run desktop:build
npm run desktop:build:mac
npm run desktop:build:win
npm run desktop:build:linux
npm run desktop:clean
```

## Packaging targets

Electron Builder is configured for:

- macOS `.app`/`.dmg`
- Windows NSIS `.exe`
- Linux `AppImage` and `.deb`

Dev builds are unsigned. Release signing, Windows reputation handling, macOS notarization, and Linux distro-specific dependency notes belong in the release pipeline.

## Security defaults

- No Docker.
- No curl/bash remote script execution.
- No silent global Python or global pip installs.
- No admin/root privileges by default.
- Local API binds to `127.0.0.1` by default.
- No telemetry.
- No centralized AetherMesh infrastructure.

## Current MVP limits

This is the smallest launcher that proves the full local flow. It does not yet bundle a portable Python runtime. If Python 3.11+ is missing, it surfaces a setup error and leaves installation to the user until a signed bundled runtime strategy is added.

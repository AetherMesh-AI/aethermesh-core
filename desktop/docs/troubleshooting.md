# Desktop Troubleshooting

## Python not found

Install Python 3.11+ from a trusted platform source, then reopen AetherMesh Desktop. The app does not silently install system Python.

## Python version too old

AetherMesh Desktop requires Python 3.11+. Install a newer Python and reopen the app.

## Venv creation failed

Check permissions in the app storage folder. Delete the `venv/` directory only if you want the app to recreate its private environment.

## Package install failed

Check internet connectivity and package source settings. For local development, set package source to `local` and point it at the repo root.

## API did not start

The desktop app starts `aethermesh node start --host 127.0.0.1 --port 7280`. If port 7280 is already in use, change the desktop settings or stop the conflicting process.

## Node already running

The app avoids launching duplicate supervised node processes. If an external node is already running on the configured API URL, use Refresh to reconnect.

## Windows antivirus or quarantine

Unsigned dev builds can trigger warnings. Use signed release builds for normal distribution.

## macOS Gatekeeper

Unsigned dev builds may require manual approval in System Settings. Release builds should be signed and notarized.

## Linux system dependency missing

Electron AppImage/deb builds may require common desktop libraries depending on distro. Prefer the `.deb` on Debian/Ubuntu-like systems when available.

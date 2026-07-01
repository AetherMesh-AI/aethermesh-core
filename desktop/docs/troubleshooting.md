# Desktop Troubleshooting

## Bundled runtime missing

Packaged builds must include `runtime/aethermesh-node` or `runtime/aethermesh-node.exe` in Electron resources. Run `npm run runtime:build` and `npm run runtime:copy` before packaging, or check the release workflow artifact.

## API did not start

The desktop app starts `aethermesh-node node start --host 127.0.0.1 --port 7280`. If port 7280 is already in use, change the desktop settings or stop the conflicting process.

## Node already running

The app avoids launching duplicate supervised node processes. If an external node is already running on the configured API URL, use Refresh to reconnect.

## Runtime crashes on launch

Open the Logs panel. The launcher captures stdout/stderr from `aethermesh-node init` and `aethermesh-node node start`. Release builds should write the same logs under the app data directory.

## Development fallback

Development builds can use a local runtime with:

```bash
AETHERMESH_RUNTIME_PATH=/path/to/aethermesh-node npm run desktop:dev
```

If no sidecar is built and no environment override is set, development mode falls back to the local `aethermesh` command. That fallback is for developers only and is not the normal installer path.

## Windows antivirus or quarantine

Unsigned dev builds can trigger warnings. Use signed release builds for normal distribution.

## macOS Gatekeeper

Unsigned dev builds may require manual approval in System Settings. Release builds should be signed and notarized.

## Linux system dependency missing

Electron AppImage/deb builds may require common desktop libraries depending on distro. Prefer the `.deb` on Debian/Ubuntu-like systems when available.

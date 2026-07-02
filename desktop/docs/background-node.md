# Background Node Manual Test Plan

AetherMesh Desktop supports two modes:

- Temporary app-managed sidecar: the Electron app supervises the bundled runtime and stops it when the app closes.
- Background OS-managed node: the bundled runtime is copied to a stable per-user runtime path and registered with the operating system.

The packaged app must not install Python, pip install packages, install a global CLI, or create an admin/root system service by default.

## Shared checks

1. Install/open AetherMesh Desktop.
2. Confirm the Node & Background section shows:
   - Mode: Temporary app-managed
   - API URL: `http://127.0.0.1:7280`
   - Start at login: disabled
3. Click **Enable background node**.
4. Confirm the UI reports Background OS-managed mode and a reachable local API.
5. Confirm the stable runtime exists:
   - macOS: `~/Library/Application Support/AetherMesh/runtime/aethermesh-node`
   - Windows: `%LOCALAPPDATA%\AetherMesh\runtime\aethermesh-node.exe`
   - Linux: `~/.local/share/aethermesh/runtime/aethermesh-node`
6. Confirm runtime metadata exists under the AetherMesh metadata directory and includes version, sha256, source path, installed path, and installed timestamp.
7. Confirm no global `aethermesh` or `aethermesh-node` shell command was installed unless it was already present before the test.
8. Confirm app data, config, node identity, peer data, keys, and contribution data remain intact after runtime update checks.

## macOS LaunchAgent

1. Enable background node.
2. Confirm `~/Library/LaunchAgents/dev.aethermesh.node.plist` exists.
3. Run:
   ```bash
   launchctl print gui/$(id -u)/dev.aethermesh.node
   curl http://127.0.0.1:7280/health
   ```
4. Close the Electron window.
5. Confirm the node still responds:
   ```bash
   curl http://127.0.0.1:7280/health
   ```
6. Reopen the app and confirm it reconnects instead of launching a duplicate.
7. Press Cmd-Q.
8. Confirm the node still responds.
9. Click **Disable background node**.
10. Confirm the LaunchAgent is unloaded/removed and the node no longer responds.
11. Confirm user data was not deleted.

## Windows Task Scheduler

1. Enable background node.
2. Confirm a scheduled task named `AetherMesh Node` exists:
   ```powershell
   schtasks /Query /TN "AetherMesh Node"
   ```
3. Confirm the task action points at `%LOCALAPPDATA%\AetherMesh\runtime\aethermesh-node.exe` with arguments:
   ```text
   node start --host 127.0.0.1 --port 7280
   ```
4. Run or restart the task:
   ```powershell
   schtasks /Run /TN "AetherMesh Node"
   curl.exe http://127.0.0.1:7280/health
   ```
5. Close the Electron window and confirm the node still responds.
6. Log out/in or reboot and confirm the node starts automatically.
7. Reopen the app and confirm it reconnects instead of launching a duplicate.
8. Click **Disable background node**.
9. Confirm the scheduled task is removed and the node stops.
10. Confirm user data was not deleted.

## Linux systemd user service

1. Enable background node.
2. Confirm `~/.config/systemd/user/aethermesh-node.service` exists.
3. Run:
   ```bash
   systemctl --user status aethermesh-node.service
   curl http://127.0.0.1:7280/health
   ```
4. Close the Electron window and confirm the node still responds.
5. Restart the user session and confirm the node starts automatically:
   ```bash
   systemctl --user is-enabled aethermesh-node.service
   systemctl --user is-active aethermesh-node.service
   curl http://127.0.0.1:7280/health
   ```
6. Reopen the app and confirm it reconnects instead of launching a duplicate.
7. Click **Disable background node**.
8. Confirm the service is stopped/disabled/removed and the node stops.
9. Confirm user data was not deleted.

If systemd user services are unavailable, the app should report the failure clearly. It must not silently fail or ask for sudo.

## Runtime update checks

1. Enable background mode.
2. Confirm the UI records a last update check timestamp shortly after startup.
3. Leave the app open for at least 60 seconds.
4. Confirm the timestamp updates again.
5. Replace the bundled runtime in a test build with a different file/hash.
6. Open the app.
7. Confirm the app:
   - detects the changed runtime
   - stops the background node if needed
   - replaces the stable runtime atomically
   - re-runs `aethermesh-node init`
   - restarts the node if background mode was enabled/running
   - preserves user data and node identity

Future gossip-triggered update checks should call the same update path used by the startup and periodic timers.

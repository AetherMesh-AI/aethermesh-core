# AetherMesh CLI

AetherMesh Desktop automatically installs a per-user terminal command during first run:

```bash
aethermesh --help
aethermesh init
aethermesh node start
aethermesh node status
aethermesh node stop
```

The CLI is a shim/wrapper, not a second independent binary. It forwards all arguments to the stable runtime used by the desktop app and background node.

## Stable runtime targets

- macOS: `~/Library/Application Support/AetherMesh/runtime/aethermesh-node`
- Windows: `%LOCALAPPDATA%\AetherMesh\runtime\aethermesh-node.exe`
- Linux: `~/.local/share/aethermesh/runtime/aethermesh-node`

## CLI shim paths

- macOS/Linux: `~/.local/bin/aethermesh`
- Windows CMD: `%LOCALAPPDATA%\AetherMesh\bin\aethermesh.cmd`
- Windows PowerShell: `%LOCALAPPDATA%\AetherMesh\bin\aethermesh.ps1`

A second `aethermesh-node` shim may be created for advanced/debug use, but `aethermesh` is the documented command.

## PATH setup

The app detects whether the CLI bin directory is on PATH.

macOS/Linux default:

```bash
~/.local/bin
```

If needed, the app attempts a safe user-level shell config update:

```bash
# zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# fish
fish_add_path ~/.local/bin
```

Windows default:

```text
%LOCALAPPDATA%\AetherMesh\bin
```

If needed, the app updates the user PATH with `setx`. Users may need to reopen terminals before `aethermesh` is visible.

## Runtime updates

Runtime updates replace the stable runtime atomically. The CLI shim stays in place and automatically uses the new runtime path contents.

The updater:

1. Verifies runtime sha256 metadata.
2. Writes the replacement to a temporary file.
3. Marks it executable on macOS/Linux.
4. Atomically renames it over the stable runtime.
5. Preserves CLI shims, user data, node identity, config, peer data, keys, and contribution data.
6. Re-verifies CLI metadata.

## Repair CLI

Use **Repair CLI** if the shim is missing, PATH changed, or the target runtime was repaired. Repair:

1. Ensures the stable runtime exists.
2. Recreates `aethermesh` and optional `aethermesh-node` shims.
3. Rechecks PATH.
4. Verifies direct shim execution with `--version`.
5. Updates CLI metadata.

## Uninstall CLI

Use **Uninstall CLI** to remove the CLI wrappers only. This does not remove:

- stable runtime used by desktop/background node
- user data
- config
- node identity
- keys
- peer/contribution data

PATH entries are not removed automatically unless they can be safely identified in a future implementation. If cleanup is needed, remove the AetherMesh CLI line from your shell config or remove `%LOCALAPPDATA%\AetherMesh\bin` from the user PATH.

## Manual tests

### macOS

1. Install/open AetherMesh Desktop.
2. Open a new terminal.
3. Run `aethermesh --version`.
4. Run `aethermesh --help`.
5. Enable background node.
6. Run `aethermesh node status`.
7. Update runtime with a test build.
8. Run `aethermesh --version` and confirm it reports the updated runtime.
9. Use **Uninstall CLI**.
10. Confirm the shim is removed and AetherMesh data remains.

### Windows

1. Install/open AetherMesh Desktop.
2. Reopen PowerShell or cmd.
3. Run `aethermesh --version`.
4. Confirm `%LOCALAPPDATA%\AetherMesh\bin` is on the user PATH or shown as requiring terminal restart.
5. Update runtime with a test build.
6. Run `aethermesh --version` and confirm it still works.
7. Use **Uninstall CLI** and confirm only wrappers are removed.

### Linux

1. Install/open AetherMesh Desktop.
2. Confirm `~/.local/bin` path handling.
3. Open a new terminal.
4. Run `aethermesh --version`.
5. Enable systemd user background node.
6. Run `aethermesh node status`.
7. Update runtime with a test build.
8. Run `aethermesh --version` and confirm it still works.
9. Use **Uninstall CLI** and confirm user data remains.

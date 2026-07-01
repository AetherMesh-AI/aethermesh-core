function platformNotes(platform = process.platform) {
  if (platform === 'darwin') {
    return {
      runtime: 'Normal builds bundle a signed/notarized aethermesh-node runtime sidecar inside the .app resources.',
      packaging: 'Builds macOS .app and .dmg artifacts. Notarization is a release-signing step, not performed by dev builds.',
      permissions: 'No admin permissions, system Python install, global pip install, or PATH mutation is required by default.',
    };
  }
  if (platform === 'win32') {
    return {
      runtime: 'Normal builds bundle aethermesh-node.exe inside the app resources.',
      packaging: 'Builds NSIS .exe installers.',
      permissions: 'No global Python install, global pip install, or PATH mutation is performed by default.',
    };
  }
  return {
    runtime: 'Normal builds bundle an aethermesh-node sidecar binary inside the app resources.',
    packaging: 'Builds AppImage and deb artifacts.',
    permissions: 'The API remains localhost-only; no system Python install, global pip install, or PATH mutation is required.',
  };
}

module.exports = { platformNotes };

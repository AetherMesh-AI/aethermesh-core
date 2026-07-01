function platformNotes(platform = process.platform) {
  if (platform === 'darwin') {
    return {
      pythonSetup: 'Use an existing Python 3.11+ install or install from python.org/Homebrew after user approval.',
      packaging: 'Builds macOS .app and .dmg artifacts. Notarization is a release-signing step, not performed by dev builds.',
      permissions: 'No admin permissions are required for the app-managed virtual environment.',
    };
  }
  if (platform === 'win32') {
    return {
      pythonSetup: 'Use py/python when present; otherwise show setup guidance before using winget or python.org installers.',
      packaging: 'Builds NSIS .exe installers.',
      permissions: 'No global pip install or admin install is performed by default.',
    };
  }
  return {
    pythonSetup: 'Use python3.11/python3.12 when present; otherwise guide the user to their distro package manager.',
    packaging: 'Builds AppImage and deb artifacts.',
    permissions: 'The API remains localhost-only and the venv lives in XDG/app data storage.',
  };
}

module.exports = { platformNotes };

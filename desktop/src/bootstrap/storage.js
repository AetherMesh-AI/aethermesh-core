const os = require('node:os');
const path = require('node:path');

function getDefaultAetherMeshHome({
  platform = process.platform,
  homeDir = os.homedir(),
  env = process.env,
} = {}) {
  if (platform === 'darwin') {
    return path.join(homeDir, 'Library', 'Application Support', 'AetherMesh');
  }
  if (platform === 'win32') {
    return path.join(env.APPDATA || path.join(homeDir, 'AppData', 'Roaming'), 'AetherMesh');
  }
  return path.join(env.XDG_DATA_HOME || path.join(homeDir, '.local', 'share'), 'AetherMesh');
}

function getAetherMeshPaths(home = getDefaultAetherMeshHome()) {
  return {
    home,
    venvDir: path.join(home, 'venv'),
    logsDir: path.join(home, 'logs'),
    configDir: path.join(home, 'config'),
    metadataDir: path.join(home, 'metadata'),
    installStatusPath: path.join(home, 'metadata', 'install-status.json'),
    processStatePath: path.join(home, 'metadata', 'process-state.json'),
  };
}

module.exports = { getDefaultAetherMeshHome, getAetherMeshPaths };

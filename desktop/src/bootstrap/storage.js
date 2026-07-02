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
    return path.join(env.LOCALAPPDATA || path.join(homeDir, 'AppData', 'Local'), 'AetherMesh');
  }
  return path.join(env.XDG_DATA_HOME || path.join(homeDir, '.local', 'share'), 'aethermesh');
}

function getDefaultAetherMeshLogsDir({
  platform = process.platform,
  homeDir = os.homedir(),
  env = process.env,
  home = getDefaultAetherMeshHome({ platform, homeDir, env }),
} = {}) {
  if (platform === 'darwin') {
    return path.join(homeDir, 'Library', 'Logs', 'AetherMesh');
  }
  if (platform === 'win32') {
    return path.join(home, 'logs');
  }
  return path.join(env.XDG_STATE_HOME || path.join(homeDir, '.local', 'state'), 'aethermesh', 'logs');
}

function getAetherMeshPaths(home = getDefaultAetherMeshHome(), options = {}) {
  const logsDir = options.logsDir || getDefaultAetherMeshLogsDir({ ...options, home });
  return {
    home,
    logsDir,
    runtimeDir: path.join(home, 'runtime'),
    configDir: path.join(home, 'config'),
    metadataDir: path.join(home, 'metadata'),
    installStatusPath: path.join(home, 'metadata', 'install-status.json'),
    processStatePath: path.join(home, 'metadata', 'process-state.json'),
  };
}

module.exports = { getDefaultAetherMeshHome, getDefaultAetherMeshLogsDir, getAetherMeshPaths };

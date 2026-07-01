const fs = require('node:fs');
const path = require('node:path');

function getRuntimeExecutableName(platform = process.platform) {
  return platform === 'win32' ? 'aethermesh-node.exe' : 'aethermesh-node';
}

function getBundledRuntimePath({
  resourcesPath,
  platform = process.platform,
} = {}) {
  if (!resourcesPath) {
    throw new Error('resourcesPath is required to resolve bundled runtime');
  }
  return path.join(resourcesPath, 'runtime', getRuntimeExecutableName(platform));
}

function resolveRuntimeCommand({
  isPackaged = false,
  resourcesPath = process.resourcesPath,
  appRoot = path.resolve(__dirname, '..', '..'),
  platform = process.platform,
  arch = process.arch,
  env = process.env,
  existsSync = fs.existsSync,
} = {}) {
  if (env.AETHERMESH_RUNTIME_PATH) {
    return env.AETHERMESH_RUNTIME_PATH;
  }

  if (isPackaged) {
    const bundled = getBundledRuntimePath({ resourcesPath, platform });
    if (!existsSync(bundled)) {
      throw new Error(`bundled AetherMesh runtime is missing at ${bundled}`);
    }
    return bundled;
  }

  const devBuilt = path.join(
    appRoot,
    'desktop',
    'resources',
    'runtime',
    `${platform}-${arch}`,
    getRuntimeExecutableName(platform),
  );
  if (existsSync(devBuilt)) {
    return devBuilt;
  }

  return 'aethermesh';
}

module.exports = {
  getBundledRuntimePath,
  getRuntimeExecutableName,
  resolveRuntimeCommand,
};

const path = require('node:path');

function buildCreateVenvCommand(pythonExecutable, venvDir) {
  return [pythonExecutable, ['-m', 'venv', venvDir]];
}

function getVenvPythonPath(venvDir, platform = process.platform) {
  if (platform === 'win32') {
    return path.join(venvDir, 'Scripts', 'python.exe');
  }
  return path.join(venvDir, 'bin', 'python');
}

module.exports = { buildCreateVenvCommand, getVenvPythonPath };

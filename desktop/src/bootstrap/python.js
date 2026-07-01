const { execFile } = require('node:child_process');
const { promisify } = require('node:util');

const execFileAsync = promisify(execFile);
const DEFAULT_PYTHON_CANDIDATES = process.platform === 'win32'
  ? ['py', 'python', 'python3']
  : ['python3.12', 'python3.11', 'python3', 'python'];

function parsePythonVersion(output) {
  const match = String(output).match(/(?:Python\s+)?(\d+)\.(\d+)\.(\d+)/);
  if (!match) {
    return null;
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
  };
}

function isUsablePythonVersion(output) {
  const version = parsePythonVersion(output);
  if (!version) {
    return false;
  }
  return version.major > 3 || (version.major === 3 && version.minor >= 11);
}

async function detectPython({ candidates = DEFAULT_PYTHON_CANDIDATES, execFile: runner = runVersion } = {}) {
  const attempts = [];
  for (const candidate of candidates) {
    try {
      const versionOutput = await runner(candidate, ['--version']);
      attempts.push({ executable: candidate, versionOutput });
      if (isUsablePythonVersion(versionOutput)) {
        return {
          usable: true,
          executable: candidate,
          version: parsePythonVersion(versionOutput),
          versionOutput,
          attempts,
        };
      }
    } catch (error) {
      attempts.push({ executable: candidate, error: error.message });
    }
  }
  return { usable: false, executable: null, version: null, attempts };
}

async function runVersion(executable, args) {
  const { stdout, stderr } = await execFileAsync(executable, args);
  return `${stdout}${stderr}`.trim();
}

module.exports = {
  DEFAULT_PYTHON_CANDIDATES,
  parsePythonVersion,
  isUsablePythonVersion,
  detectPython,
};

const DEFAULT_SETTINGS = Object.freeze({
  source: 'github',
  packageName: 'aethermesh[ui]',
  githubUrl: 'https://github.com/AetherMesh-AI/aethermesh-core/releases/latest/download/aethermesh-0.2.0a0-py3-none-any.whl',
  localPath: '',
  autoUpdateOnLaunch: false,
});

function normalizePackageSettings(settings = {}) {
  return { ...DEFAULT_SETTINGS, ...settings };
}

function buildPackageInstallCommand(venvPython, settings = {}, { update = false } = {}) {
  const normalized = normalizePackageSettings(settings);
  const args = ['-m', 'pip', 'install', '--upgrade'];
  if (update) {
    args.push('--force-reinstall');
  }
  if (normalized.source === 'pypi') {
    args.push(normalized.packageName || DEFAULT_SETTINGS.packageName);
  } else if (normalized.source === 'github') {
    if (!normalized.githubUrl) {
      throw new Error('GitHub wheel URL is required');
    }
    args.push(`${normalized.packageName || DEFAULT_SETTINGS.packageName} @ ${normalized.githubUrl}`);
  } else if (normalized.source === 'local') {
    if (!normalized.localPath) {
      throw new Error('local development path is required');
    }
    args.push('-e', `${normalized.localPath}[ui]`);
  } else {
    throw new Error(`unsupported package source: ${normalized.source}`);
  }
  return [venvPython, args];
}

module.exports = {
  DEFAULT_SETTINGS,
  normalizePackageSettings,
  buildPackageInstallCommand,
};

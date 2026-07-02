const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFile: defaultExecFile } = require('node:child_process');

const CLI_COMMAND_NAME = 'aethermesh';
const CLI_NODE_COMMAND_NAME = 'aethermesh-node';
const PATH_MARKER = 'AetherMesh CLI';

function getCliBinDir({ platform = process.platform, homeDir = os.homedir(), env = process.env, home } = {}) {
  if (platform === 'win32') {
    const localAppData = env.LOCALAPPDATA || path.join(homeDir, 'AppData', 'Local');
    return path.join(localAppData, 'AetherMesh', 'bin');
  }
  return path.join(home || homeDir, '.local', 'bin');
}

function getCliShimPaths({ platform = process.platform, binDir }) {
  if (platform === 'win32') {
    return {
      commandPath: path.join(binDir, `${CLI_COMMAND_NAME}.cmd`),
      powershellPath: path.join(binDir, `${CLI_COMMAND_NAME}.ps1`),
      nodeCommandPath: path.join(binDir, `${CLI_NODE_COMMAND_NAME}.cmd`),
      nodePowerShellPath: path.join(binDir, `${CLI_NODE_COMMAND_NAME}.ps1`),
    };
  }
  return {
    commandPath: path.join(binDir, CLI_COMMAND_NAME),
    nodeCommandPath: path.join(binDir, CLI_NODE_COMMAND_NAME),
  };
}

function quoteShell(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`;
}

function buildPosixShim({ runtimePath, homeDir }) {
  return `#!/usr/bin/env sh\nAETHERMESH_HOME=${quoteShell(homeDir)} exec ${quoteShell(runtimePath)} "$@"\n`;
}

function buildWindowsCmdShim({ runtimePath, homeDir }) {
  return `@echo off\r\nset "AETHERMESH_HOME=${homeDir}"\r\n"${runtimePath}" %*\r\n`;
}

function buildWindowsPowerShellShim({ runtimePath, homeDir }) {
  const escapedRuntime = String(runtimePath).replaceAll("'", "''");
  const escapedHome = String(homeDir).replaceAll("'", "''");
  return `$env:AETHERMESH_HOME='${escapedHome}'\r\n& '${escapedRuntime}' @args\r\n`;
}

function pathEntries(pathValue = '') {
  return String(pathValue)
    .split(path.delimiter)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function isDirOnPath(binDir, pathValue = process.env.PATH || '') {
  const normalized = path.resolve(binDir);
  return pathEntries(pathValue).some((entry) => path.resolve(entry) === normalized);
}

function getPathSetupCommand({ platform = process.platform, shell = process.env.SHELL || '', binDir }) {
  if (platform === 'win32') {
    return `[Environment]::SetEnvironmentVariable('Path', $env:Path + ';${binDir}', 'User')`;
  }
  if (shell.endsWith('fish')) {
    return `fish_add_path ${quoteShell(binDir)}`;
  }
  const rc = shell.endsWith('bash') ? '~/.bashrc' : '~/.zshrc';
  return `echo 'export PATH="${binDir}:$PATH"' >> ${rc}`;
}

function getShellConfigPath({ platform = process.platform, shell = process.env.SHELL || '', homeDir = os.homedir() } = {}) {
  if (platform === 'win32') return null;
  if (shell.endsWith('fish')) return path.join(homeDir, '.config', 'fish', 'config.fish');
  if (shell.endsWith('bash')) return path.join(homeDir, '.bashrc');
  if (shell.endsWith('zsh') || !shell) return path.join(homeDir, '.zshrc');
  return null;
}

function buildShellPathBlock({ binDir, shell = process.env.SHELL || '' }) {
  if (shell.endsWith('fish')) {
    return `\n# ${PATH_MARKER}\nfish_add_path ${quoteShell(binDir)}\n`;
  }
  return `\n# ${PATH_MARKER}\nexport PATH="${binDir}:$PATH"\n`;
}

function execFilePromise(execFile, command, args, options = {}) {
  return new Promise((resolve, reject) => {
    execFile(command, args, options, (error, stdout, stderr) => {
      if (error) {
        error.stdout = stdout;
        error.stderr = stderr;
        reject(error);
        return;
      }
      resolve({ stdout, stderr });
    });
  });
}

function readJson(filePath, fallback = null, { fsModule = fs } = {}) {
  if (!fsModule.existsSync(filePath)) return fallback;
  return JSON.parse(fsModule.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value, { fsModule = fs } = {}) {
  fsModule.mkdirSync(path.dirname(filePath), { recursive: true });
  fsModule.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

class CliManager {
  constructor({
    paths,
    stableRuntimePath,
    runtimeMetadata = null,
    platform = process.platform,
    homeDir = os.homedir(),
    env = process.env,
    fsModule = fs,
    execFile = defaultExecFile,
    now = () => new Date(),
  }) {
    this.paths = paths;
    this.stableRuntimePath = stableRuntimePath;
    this.runtimeMetadata = runtimeMetadata;
    this.platform = platform;
    this.homeDir = homeDir;
    this.env = env;
    this.fs = fsModule;
    this.execFile = execFile;
    this.now = now;
    this.binDir = getCliBinDir({ platform, homeDir, env });
    this.shims = getCliShimPaths({ platform, binDir: this.binDir });
  }

  get metadataPath() {
    return path.join(this.paths.metadataDir, 'cli.json');
  }

  readMetadata() {
    return readJson(this.metadataPath, null, { fsModule: this.fs });
  }

  writeMetadata(metadata) {
    writeJson(this.metadataPath, metadata, { fsModule: this.fs });
  }

  createShims() {
    this.fs.mkdirSync(this.binDir, { recursive: true });
    if (this.platform === 'win32') {
      for (const shimPath of [this.shims.commandPath, this.shims.nodeCommandPath]) {
        this.fs.writeFileSync(shimPath, buildWindowsCmdShim({ runtimePath: this.stableRuntimePath, homeDir: this.paths.home }));
      }
      for (const shimPath of [this.shims.powershellPath, this.shims.nodePowerShellPath]) {
        this.fs.writeFileSync(shimPath, buildWindowsPowerShellShim({ runtimePath: this.stableRuntimePath, homeDir: this.paths.home }));
      }
      return;
    }
    for (const shimPath of [this.shims.commandPath, this.shims.nodeCommandPath]) {
      this.fs.writeFileSync(shimPath, buildPosixShim({ runtimePath: this.stableRuntimePath, homeDir: this.paths.home }));
      this.fs.chmodSync(shimPath, 0o755);
    }
  }

  removeShims() {
    for (const shimPath of Object.values(this.shims)) {
      if (shimPath && this.fs.existsSync(shimPath)) {
        this.fs.rmSync(shimPath, { force: true });
      }
    }
  }

  getPathStatus() {
    const targetExists = this.fs.existsSync(this.stableRuntimePath);
    const shimExists = this.fs.existsSync(this.shims.commandPath);
    const onPath = isDirOnPath(this.binDir, this.env.PATH || '');
    if (!targetExists || !shimExists) {
      return !targetExists ? 'broken target' : 'broken shim';
    }
    return onPath ? 'available in shell' : 'installed but PATH update required';
  }

  async verifyCli() {
    if (!this.fs.existsSync(this.shims.commandPath)) {
      return { ok: false, error: 'CLI shim is missing' };
    }
    if (!this.fs.existsSync(this.stableRuntimePath)) {
      return { ok: false, error: 'CLI runtime target is missing' };
    }
    try {
      const result = await execFilePromise(this.execFile, this.shims.commandPath, ['--version'], { windowsHide: true });
      return { ok: true, versionOutput: (result.stdout || result.stderr || '').trim() };
    } catch (error) {
      return { ok: false, error: error.stderr || error.message };
    }
  }

  async ensurePathConfigured() {
    if (isDirOnPath(this.binDir, this.env.PATH || '')) {
      return { changed: false, pathStatus: 'available in shell' };
    }
    if (this.platform === 'win32') {
      const escapedBinDir = this.binDir.replaceAll("'", "''");
      const script = `$bin='${escapedBinDir}'; $path=[Environment]::GetEnvironmentVariable('Path','User'); if (-not ($path -split ';' | Where-Object { $_ -eq $bin })) { $next = if ($path) { $path + ';' + $bin } else { $bin }; [Environment]::SetEnvironmentVariable('Path', $next, 'User') }`;
      await execFilePromise(this.execFile, 'powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script], { windowsHide: true });
      return { changed: true, pathStatus: 'installed but PATH update required', restartShellRequired: true };
    }
    const shellConfigPath = getShellConfigPath({ platform: this.platform, shell: this.env.SHELL || '', homeDir: this.homeDir });
    if (!shellConfigPath) {
      return { changed: false, pathStatus: 'installed but PATH update required', manualCommand: getPathSetupCommand({ platform: this.platform, shell: this.env.SHELL || '', binDir: this.binDir }) };
    }
    const current = this.fs.existsSync(shellConfigPath) ? this.fs.readFileSync(shellConfigPath, 'utf8') : '';
    if (!current.includes(PATH_MARKER) && !current.includes(this.binDir)) {
      this.fs.mkdirSync(path.dirname(shellConfigPath), { recursive: true });
      this.fs.appendFileSync(shellConfigPath, buildShellPathBlock({ binDir: this.binDir, shell: this.env.SHELL || '' }));
    }
    return { changed: true, pathStatus: 'installed but PATH update required', shellConfigPath, restartShellRequired: true };
  }

  buildMetadata({ pathResult = {}, verification = {}, installed = true } = {}) {
    const pathStatus = this.getPathStatus();
    return {
      cliInstalled: installed,
      cliCommandName: CLI_COMMAND_NAME,
      cliShimPath: this.shims.commandPath,
      cliNodeShimPath: this.shims.nodeCommandPath,
      cliTargetRuntimePath: this.stableRuntimePath,
      cliInstalledAt: this.readMetadata()?.cliInstalledAt || this.now().toISOString(),
      cliLastVerifiedAt: this.now().toISOString(),
      cliRuntimeVersion: this.runtimeMetadata?.version || null,
      cliRuntimeSha256: this.runtimeMetadata?.sha256 || null,
      cliPathStatus: pathStatus,
      cliPathSetupCommand: pathStatus === 'available in shell' ? null : getPathSetupCommand({ platform: this.platform, shell: this.env.SHELL || '', binDir: this.binDir }),
      cliVerificationOk: Boolean(verification.ok),
      cliVerificationError: verification.ok ? null : verification.error || null,
      pathUpdate: pathResult,
    };
  }

  async installOrRepair({ configurePath = true } = {}) {
    this.createShims();
    const pathResult = configurePath ? await this.ensurePathConfigured().catch((error) => ({ changed: false, pathStatus: 'installed but PATH update required', error: error.message, manualCommand: getPathSetupCommand({ platform: this.platform, shell: this.env.SHELL || '', binDir: this.binDir }) })) : {};
    const verification = await this.verifyCli();
    const metadata = this.buildMetadata({ pathResult, verification, installed: true });
    this.writeMetadata(metadata);
    return metadata;
  }

  async uninstall() {
    this.removeShims();
    const previous = this.readMetadata() || {};
    const metadata = {
      ...previous,
      cliInstalled: false,
      cliLastVerifiedAt: this.now().toISOString(),
      cliPathStatus: 'not installed',
      cliVerificationOk: false,
      cliVerificationError: null,
    };
    this.writeMetadata(metadata);
    return metadata;
  }

  async getStatus() {
    const verification = await this.verifyCli();
    const metadata = this.buildMetadata({ verification, installed: this.fs.existsSync(this.shims.commandPath) });
    this.writeMetadata(metadata);
    return metadata;
  }
}

module.exports = {
  CLI_COMMAND_NAME,
  CLI_NODE_COMMAND_NAME,
  CliManager,
  PATH_MARKER,
  buildPosixShim,
  buildWindowsCmdShim,
  buildWindowsPowerShellShim,
  getCliBinDir,
  getCliShimPaths,
  getPathSetupCommand,
  isDirOnPath,
};

const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFile: defaultExecFile } = require('node:child_process');

const LAUNCH_LABEL = 'dev.aethermesh.node';
const WINDOWS_TASK_NAME = 'AetherMesh Node';
const SYSTEMD_SERVICE_NAME = 'aethermesh-node.service';
const UPDATE_INTERVAL_MS = 60_000;

function getStableRuntimePath(paths, platform = process.platform) {
  const executable = platform === 'win32' ? 'aethermesh-node.exe' : 'aethermesh-node';
  return path.join(paths.runtimeDir, executable);
}

function sha256File(filePath, { fsModule = fs } = {}) {
  const hash = crypto.createHash('sha256');
  hash.update(fsModule.readFileSync(filePath));
  return hash.digest('hex');
}

function readJson(filePath, fallback = null, { fsModule = fs } = {}) {
  if (!fsModule.existsSync(filePath)) {
    return fallback;
  }
  return JSON.parse(fsModule.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value, { fsModule = fs } = {}) {
  fsModule.mkdirSync(path.dirname(filePath), { recursive: true });
  fsModule.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function plistEscape(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

function buildLaunchAgentPlist({ runtimePath, homeDir, logsDir, host, port }) {
  const stdout = path.join(logsDir, 'node.log');
  const stderr = path.join(logsDir, 'node.err.log');
  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LAUNCH_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${plistEscape(runtimePath)}</string>
    <string>node</string>
    <string>start</string>
    <string>--host</string>
    <string>${plistEscape(host)}</string>
    <string>--port</string>
    <string>${plistEscape(port)}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${plistEscape(homeDir)}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>AETHERMESH_HOME</key>
    <string>${plistEscape(homeDir)}</string>
  </dict>
  <key>StandardOutPath</key>
  <string>${plistEscape(stdout)}</string>
  <key>StandardErrorPath</key>
  <string>${plistEscape(stderr)}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
`;
}

function buildSystemdUserService({ runtimePath, homeDir, logsDir, host, port }) {
  const stdout = path.join(logsDir, 'node.log');
  const stderr = path.join(logsDir, 'node.err.log');
  return `[Unit]
Description=AetherMesh Node
After=network-online.target

[Service]
Type=simple
WorkingDirectory=${homeDir}
Environment=AETHERMESH_HOME=${homeDir}
ExecStart=${runtimePath} node start --host ${host} --port ${port}
Restart=always
RestartSec=5
StandardOutput=append:${stdout}
StandardError=append:${stderr}

[Install]
WantedBy=default.target
`;
}

function buildWindowsTaskXml({ runtimePath, homeDir, host, port }) {
  return `<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>AetherMesh Node</Description></RegistrationInfo>
  <Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><Enabled>true</Enabled></Settings>
  <Actions Context="Author"><Exec><Command>${runtimePath}</Command><Arguments>node start --host ${host} --port ${port}</Arguments><WorkingDirectory>${homeDir}</WorkingDirectory></Exec></Actions>
</Task>
`;
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

class BackgroundNodeManager {
  constructor({
    paths,
    bundledRuntimePath,
    version,
    host = '127.0.0.1',
    port = 7280,
    platform = process.platform,
    fsModule = fs,
    execFile = defaultExecFile,
    uid = typeof process.getuid === 'function' ? process.getuid() : null,
    now = () => new Date(),
    healthCheck = async () => ({ reachable: false }),
    log = () => {},
  }) {
    this.paths = paths;
    this.bundledRuntimePath = bundledRuntimePath;
    this.version = version;
    this.host = host;
    this.port = port;
    this.platform = platform;
    this.fs = fsModule;
    this.execFile = execFile;
    this.uid = uid;
    this.now = now;
    this.healthCheck = healthCheck;
    this.log = log;
    this.updateTimer = null;
  }

  get stableRuntimePath() {
    return getStableRuntimePath(this.paths, this.platform);
  }

  get metadataPath() {
    return path.join(this.paths.metadataDir, 'runtime.json');
  }

  get backupMetadataPath() {
    return path.join(this.paths.metadataDir, 'runtime.previous.json');
  }

  get launchAgentPath() {
    return path.join(os.homedir(), 'Library', 'LaunchAgents', `${LAUNCH_LABEL}.plist`);
  }

  get systemdServicePath() {
    return path.join(os.homedir(), '.config', 'systemd', 'user', SYSTEMD_SERVICE_NAME);
  }

  ensureDirectories() {
    for (const dir of [this.paths.home, this.paths.logsDir, this.paths.configDir, this.paths.metadataDir, this.paths.runtimeDir]) {
      this.fs.mkdirSync(dir, { recursive: true });
    }
  }

  readRuntimeMetadata() {
    return readJson(this.metadataPath, null, { fsModule: this.fs });
  }

  writeRuntimeMetadata(metadata) {
    writeJson(this.metadataPath, metadata, { fsModule: this.fs });
  }

  copyOrUpdateRuntime({ force = false } = {}) {
    this.ensureDirectories();
    if (!this.fs.existsSync(this.bundledRuntimePath)) {
      throw new Error(`bundled AetherMesh runtime is missing at ${this.bundledRuntimePath}`);
    }
    const sourceSha = sha256File(this.bundledRuntimePath, { fsModule: this.fs });
    const current = this.readRuntimeMetadata();
    const installedExists = this.fs.existsSync(this.stableRuntimePath);
    if (!force && installedExists && current?.sha256 === sourceSha && current?.version === this.version) {
      return { updated: false, metadata: current };
    }
    if (current) {
      writeJson(this.backupMetadataPath, { ...current, backedUpAt: this.now().toISOString() }, { fsModule: this.fs });
    }
    const tmpPath = `${this.stableRuntimePath}.tmp-${process.pid}`;
    this.fs.copyFileSync(this.bundledRuntimePath, tmpPath);
    if (this.platform !== 'win32') {
      this.fs.chmodSync(tmpPath, 0o755);
    }
    this.fs.renameSync(tmpPath, this.stableRuntimePath);
    const metadata = {
      version: this.version,
      sha256: sourceSha,
      sourcePath: this.bundledRuntimePath,
      installedPath: this.stableRuntimePath,
      installedAt: this.now().toISOString(),
    };
    this.writeRuntimeMetadata(metadata);
    return { updated: true, metadata };
  }

  async runInit() {
    await execFilePromise(this.execFile, this.stableRuntimePath, ['init'], {
      cwd: this.paths.home,
      env: { ...process.env, AETHERMESH_HOME: this.paths.home },
      windowsHide: true,
    });
  }

  async installBackgroundNode() {
    const result = this.copyOrUpdateRuntime();
    await this.runInit();
    await this.enableStartAtLogin();
    await this.startBackgroundNode();
    return result;
  }

  async uninstallBackgroundNode() {
    await this.stopBackgroundNode({ ignoreErrors: true });
    await this.disableStartAtLogin({ ignoreErrors: true });
  }

  async enableStartAtLogin() {
    this.ensureDirectories();
    if (this.platform === 'darwin') {
      const plist = buildLaunchAgentPlist({ runtimePath: this.stableRuntimePath, homeDir: this.paths.home, logsDir: this.paths.logsDir, host: this.host, port: this.port });
      this.fs.mkdirSync(path.dirname(this.launchAgentPath), { recursive: true });
      this.fs.writeFileSync(this.launchAgentPath, plist);
      await execFilePromise(this.execFile, 'launchctl', ['bootout', `gui/${this.uid}`, this.launchAgentPath]).catch(() => {});
      await execFilePromise(this.execFile, 'launchctl', ['bootstrap', `gui/${this.uid}`, this.launchAgentPath]);
      return { mechanism: 'launchd', path: this.launchAgentPath };
    }
    if (this.platform === 'win32') {
      const xmlPath = path.join(this.paths.metadataDir, 'aethermesh-node-task.xml');
      this.fs.writeFileSync(xmlPath, buildWindowsTaskXml({ runtimePath: this.stableRuntimePath, homeDir: this.paths.home, host: this.host, port: this.port }), 'utf16le');
      await execFilePromise(this.execFile, 'schtasks.exe', ['/Create', '/TN', WINDOWS_TASK_NAME, '/XML', xmlPath, '/F']);
      return { mechanism: 'schtasks', name: WINDOWS_TASK_NAME };
    }
    const service = buildSystemdUserService({ runtimePath: this.stableRuntimePath, homeDir: this.paths.home, logsDir: this.paths.logsDir, host: this.host, port: this.port });
    this.fs.mkdirSync(path.dirname(this.systemdServicePath), { recursive: true });
    this.fs.writeFileSync(this.systemdServicePath, service);
    try {
      await execFilePromise(this.execFile, 'systemctl', ['--user', 'daemon-reload']);
      await execFilePromise(this.execFile, 'systemctl', ['--user', 'enable', SYSTEMD_SERVICE_NAME]);
      return { mechanism: 'systemd-user', path: this.systemdServicePath };
    } catch (error) {
      throw new Error(`systemd user services are unavailable or failed to enable: ${error.stderr || error.message}`);
    }
  }

  async disableStartAtLogin({ ignoreErrors = false } = {}) {
    try {
      if (this.platform === 'darwin') {
        await execFilePromise(this.execFile, 'launchctl', ['bootout', `gui/${this.uid}`, this.launchAgentPath]).catch(() => {});
        if (this.fs.existsSync(this.launchAgentPath)) this.fs.rmSync(this.launchAgentPath, { force: true });
      } else if (this.platform === 'win32') {
        await execFilePromise(this.execFile, 'schtasks.exe', ['/Delete', '/TN', WINDOWS_TASK_NAME, '/F']).catch(() => {});
      } else {
        await execFilePromise(this.execFile, 'systemctl', ['--user', 'stop', SYSTEMD_SERVICE_NAME]).catch(() => {});
        await execFilePromise(this.execFile, 'systemctl', ['--user', 'disable', SYSTEMD_SERVICE_NAME]).catch(() => {});
        await execFilePromise(this.execFile, 'systemctl', ['--user', 'daemon-reload']).catch(() => {});
        if (this.fs.existsSync(this.systemdServicePath)) this.fs.rmSync(this.systemdServicePath, { force: true });
      }
    } catch (error) {
      if (!ignoreErrors) throw error;
    }
  }

  async startBackgroundNode() {
    if (this.platform === 'darwin') {
      await execFilePromise(this.execFile, 'launchctl', ['kickstart', '-k', `gui/${this.uid}/${LAUNCH_LABEL}`]);
    } else if (this.platform === 'win32') {
      await execFilePromise(this.execFile, 'schtasks.exe', ['/Run', '/TN', WINDOWS_TASK_NAME]);
    } else {
      await execFilePromise(this.execFile, 'systemctl', ['--user', 'start', SYSTEMD_SERVICE_NAME]);
    }
  }

  async stopBackgroundNode({ ignoreErrors = false } = {}) {
    try {
      if (this.platform === 'darwin') {
        await execFilePromise(this.execFile, 'launchctl', ['kill', 'TERM', `gui/${this.uid}/${LAUNCH_LABEL}`]);
      } else if (this.platform === 'win32') {
        await execFilePromise(this.execFile, 'schtasks.exe', ['/End', '/TN', WINDOWS_TASK_NAME]);
      } else {
        await execFilePromise(this.execFile, 'systemctl', ['--user', 'stop', SYSTEMD_SERVICE_NAME]);
      }
    } catch (error) {
      if (!ignoreErrors) throw error;
    }
  }

  async getBackgroundNodeStatus() {
    const health = await this.healthCheck();
    return {
      mode: 'background',
      healthy: health.reachable,
      health,
      runtime: this.readRuntimeMetadata(),
    };
  }

  async checkForRuntimeUpdates() {
    this.ensureDirectories();
    if (!this.fs.existsSync(this.bundledRuntimePath)) {
      return { checkedAt: this.now().toISOString(), available: false, error: `missing bundled runtime at ${this.bundledRuntimePath}` };
    }
    const sourceSha = sha256File(this.bundledRuntimePath, { fsModule: this.fs });
    const current = this.readRuntimeMetadata();
    return {
      checkedAt: this.now().toISOString(),
      available: !current || current.sha256 !== sourceSha || current.version !== this.version || !this.fs.existsSync(this.stableRuntimePath),
      latestVersion: this.version,
      latestSha256: sourceSha,
      installedVersion: current?.version || null,
      installedSha256: current?.sha256 || null,
    };
  }

  async applyRuntimeUpdate({ restart = false } = {}) {
    const update = await this.checkForRuntimeUpdates();
    if (!update.available) {
      return { updated: false, update };
    }
    if (restart) {
      await this.stopBackgroundNode({ ignoreErrors: true });
    }
    const copy = this.copyOrUpdateRuntime({ force: true });
    await this.runInit();
    if (restart) {
      await this.startBackgroundNode();
    }
    return { updated: true, update, metadata: copy.metadata };
  }

  schedulePeriodicUpdateChecks({ intervalMs = UPDATE_INTERVAL_MS, onResult = () => {}, shouldApply = () => true, shouldRestart = () => false } = {}) {
    this.clearPeriodicUpdateChecks();
    this.updateTimer = setInterval(async () => {
      try {
        const result = shouldApply()
          ? await this.applyRuntimeUpdate({ restart: shouldRestart() })
          : { updated: false, update: await this.checkForRuntimeUpdates() };
        onResult(null, result);
      } catch (error) {
        onResult(error);
      }
    }, intervalMs);
    if (this.updateTimer.unref) this.updateTimer.unref();
    return this.updateTimer;
  }

  clearPeriodicUpdateChecks() {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = null;
    }
  }

  readRecentLogs({ maxBytes = 64_000 } = {}) {
    const logs = [];
    for (const logPath of [path.join(this.paths.logsDir, 'node.log'), path.join(this.paths.logsDir, 'node.err.log')]) {
      if (!this.fs.existsSync(logPath)) continue;
      const stat = this.fs.statSync(logPath);
      const start = Math.max(0, stat.size - maxBytes);
      const fd = this.fs.openSync(logPath, 'r');
      try {
        const buffer = Buffer.alloc(stat.size - start);
        this.fs.readSync(fd, buffer, 0, buffer.length, start);
        logs.push(buffer.toString('utf8'));
      } finally {
        this.fs.closeSync(fd);
      }
    }
    return logs.join('\n').trim();
  }
}

module.exports = {
  BackgroundNodeManager,
  LAUNCH_LABEL,
  SYSTEMD_SERVICE_NAME,
  UPDATE_INTERVAL_MS,
  WINDOWS_TASK_NAME,
  buildLaunchAgentPlist,
  buildSystemdUserService,
  buildWindowsTaskXml,
  getStableRuntimePath,
  sha256File,
};

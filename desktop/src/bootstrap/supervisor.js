const { spawn: defaultSpawn } = require('node:child_process');

class NodeSupervisor {
  constructor({
    aethermeshCommand = 'aethermesh',
    env = process.env,
    spawn = defaultSpawn,
  } = {}) {
    this.aethermeshCommand = aethermeshCommand;
    this.env = env;
    this.spawn = spawn;
    this.logs = [];
    this.child = null;
    this.state = { status: 'stopped', error: null, pid: null };
  }

  async start({ host = '127.0.0.1', port = 7280 } = {}) {
    if (this.child && this.state.status === 'running') {
      throw new Error('AetherMesh node is already running');
    }
    this.state = { status: 'starting', error: null, pid: null };
    await this.runInit();
    this.child = this.spawnManaged(['node', 'start', '--host', host, '--port', String(port)]);
    this.state = { status: 'running', error: null, pid: this.child.pid || null };
  }

  runInit() {
    return new Promise((resolve, reject) => {
      const child = this.spawnManaged(['init']);
      child.on('exit', (code) => {
        if (code === 0) {
          resolve();
        } else {
          const error = new Error(`aethermesh init failed with exit code ${code}`);
          this.state = { status: 'error', error: error.message, pid: null };
          reject(error);
        }
      });
    });
  }

  stop({ keepRunning = false } = {}) {
    if (keepRunning) {
      return;
    }
    if (this.child) {
      this.child.kill('SIGTERM');
      this.child = null;
    }
    this.state = { status: 'stopped', error: null, pid: null };
  }

  spawnManaged(args) {
    const child = this.spawn(this.aethermeshCommand, args, {
      env: this.env,
      windowsHide: true,
    });
    this.attachLogs(child);
    child.on('exit', (code, signal) => {
      if (child === this.child) {
        this.state = code === 0 || signal === 'SIGTERM'
          ? { status: 'stopped', error: null, pid: null }
          : { status: 'error', error: `node process exited with code ${code}`, pid: null };
      }
    });
    return child;
  }

  attachLogs(child) {
    if (child.stdout) {
      child.stdout.on('data', (chunk) => this.appendLog(chunk));
    }
    if (child.stderr) {
      child.stderr.on('data', (chunk) => this.appendLog(chunk));
    }
  }

  appendLog(chunk) {
    const text = String(chunk).trimEnd();
    if (!text) {
      return;
    }
    this.logs.push(text);
    if (this.logs.length > 500) {
      this.logs = this.logs.slice(-500);
    }
  }
}

module.exports = { NodeSupervisor };

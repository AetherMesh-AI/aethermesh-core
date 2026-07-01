class LocalApiClient {
  constructor({ baseUrl = 'http://127.0.0.1:7280', fetch: fetchImpl = globalThis.fetch } = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.fetch = fetchImpl;
  }

  async getJson(path) {
    const response = await this.fetch(`${this.baseUrl}${path}`, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`${path} failed with HTTP ${response.status}`);
    }
    return response.json();
  }

  async health() {
    try {
      return { reachable: true, payload: await this.getJson('/health') };
    } catch (error) {
      return { reachable: false, error: error.message };
    }
  }

  async dashboardSnapshot() {
    const [status, peers, jobs, capabilities, packageInfo, network, logs, health] = await Promise.all([
      this.getJson('/api/status'),
      this.getJson('/api/peers'),
      this.getJson('/api/jobs'),
      this.getJson('/api/capabilities'),
      this.getJson('/api/package'),
      this.getJson('/api/network'),
      this.getJson('/api/logs'),
      this.health(),
    ]);
    return { status, peers, jobs, capabilities, package: packageInfo, network, logs, health };
  }
}

module.exports = { LocalApiClient };

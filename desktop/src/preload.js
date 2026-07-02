const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aethermesh', {
  getState: () => ipcRenderer.invoke('aethermesh:get-state'),
  getDashboard: () => ipcRenderer.invoke('aethermesh:get-dashboard'),
  getHealth: () => ipcRenderer.invoke('aethermesh:get-health'),
  startNode: () => ipcRenderer.invoke('aethermesh:start-node'),
  stopNode: () => ipcRenderer.invoke('aethermesh:stop-node'),
  restartNode: () => ipcRenderer.invoke('aethermesh:restart-node'),
  enableBackgroundNode: () => ipcRenderer.invoke('aethermesh:enable-background-node'),
  disableBackgroundNode: () => ipcRenderer.invoke('aethermesh:disable-background-node'),
  removeLocalData: () => ipcRenderer.invoke('aethermesh:remove-local-data'),
  repairCli: () => ipcRenderer.invoke('aethermesh:repair-cli'),
  reinstallCli: () => ipcRenderer.invoke('aethermesh:reinstall-cli'),
  uninstallCli: () => ipcRenderer.invoke('aethermesh:uninstall-cli'),
  getCliStatus: () => ipcRenderer.invoke('aethermesh:get-cli-status'),
  checkRuntimeUpdates: () => ipcRenderer.invoke('aethermesh:check-runtime-updates'),
  readBackgroundLogs: () => ipcRenderer.invoke('aethermesh:read-background-logs'),
  platformNotes: () => ipcRenderer.invoke('aethermesh:platform-notes'),
  onState: (handler) => ipcRenderer.on('aethermesh:state', (_event, state) => handler(state)),
});

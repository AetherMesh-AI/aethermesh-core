const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aethermesh', {
  getState: () => ipcRenderer.invoke('aethermesh:get-state'),
  getDashboard: () => ipcRenderer.invoke('aethermesh:get-dashboard'),
  getHealth: () => ipcRenderer.invoke('aethermesh:get-health'),
  startNode: () => ipcRenderer.invoke('aethermesh:start-node'),
  stopNode: () => ipcRenderer.invoke('aethermesh:stop-node'),
  platformNotes: () => ipcRenderer.invoke('aethermesh:platform-notes'),
  onState: (handler) => ipcRenderer.on('aethermesh:state', (_event, state) => handler(state)),
});

/** Preload：主窗口与主进程 IPC 桥 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAgentCount: () => ipcRenderer.invoke('get-agent-count'),
  onAgentCount: (cb) => ipcRenderer.on('agent-count', (_e, count) => cb(count)),
  addAgent: () => ipcRenderer.send('add-agent'),
  removeAgent: () => ipcRenderer.send('remove-agent'),
  agentPlay: (index) => ipcRenderer.send('agent-play', index),
  agentPause: (index) => ipcRenderer.send('agent-pause', index),
});

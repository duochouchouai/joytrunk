/** Preload：主窗口与主进程 IPC 桥 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAgentCount: () => ipcRenderer.invoke('get-agent-count'),
  getAgentNames: () => ipcRenderer.invoke('get-agent-names'),
  getAgentStates: () => ipcRenderer.invoke('get-agent-states'),
  getIndicatorConfig: () => ipcRenderer.invoke('get-indicator-config'),
  onAgentCount: (cb) => ipcRenderer.on('agent-count', (_e, count) => cb(count)),
  onAgentNames: (cb) => ipcRenderer.on('agent-names', (_e, names) => cb(names)),
  onAgentStates: (cb) => ipcRenderer.on('agent-states', (_e, states) => cb(states)),
  onIndicatorConfig: (cb) => ipcRenderer.on('indicator-config', (_e, config) => cb(config)),
  setAgentName: (index, name) => ipcRenderer.send('set-agent-name', index, name),
  setAgentState: (index, state) => ipcRenderer.send('set-agent-state', index, state),
  setIndicatorConfig: (payload) => ipcRenderer.send('set-indicator-config', payload),
  addAgent: () => ipcRenderer.send('add-agent'),
  removeAgent: () => ipcRenderer.send('remove-agent'),
  agentPlay: (index) => ipcRenderer.send('agent-play', index),
  agentPause: (index) => ipcRenderer.send('agent-pause', index),
});

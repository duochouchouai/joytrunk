/** Preload：悬浮窗与主进程 IPC 桥（video-sources, agent-count/names/states, indicator-config, player-cmd, overlay-drag, open-main, add-agent, remove-agent-at, start-with-agents） */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onVideoSources: (cb) => ipcRenderer.on('video-sources', (_e, sources) => cb(sources)),
  onAgentCount: (cb) => ipcRenderer.on('agent-count', (_e, count) => cb(count)),
  onAgentNames: (cb) => ipcRenderer.on('agent-names', (_e, names) => cb(names)),
  onAgentStates: (cb) => ipcRenderer.on('agent-states', (_e, states) => cb(states)),
  onIndicatorConfig: (cb) => ipcRenderer.on('indicator-config', (_e, config) => cb(config)),
  onPlayerCmd: (cb) => ipcRenderer.on('player-cmd', (_e, cmd, index) => cb(cmd, index)),
  openMain: () => ipcRenderer.send('open-main'),
  addAgent: () => ipcRenderer.send('add-agent'),
  startWithAgents: (n) => ipcRenderer.send('start-with-agents', n),
  removeAgentAt: (index) => ipcRenderer.send('remove-agent-at', index),
  overlayDragStart: (x, y) => ipcRenderer.send('overlay-drag-start', x, y),
  overlayDragMove: (x, y) => ipcRenderer.send('overlay-drag-move', x, y),
  overlayDragEnd: () => ipcRenderer.send('overlay-drag-end'),
});

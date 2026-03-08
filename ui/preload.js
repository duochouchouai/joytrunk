/** Preload：悬浮窗与主进程 IPC 桥 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onVideoPaths: (cb) => ipcRenderer.on('video-paths', (_e, paths) => cb(paths)),
  onAgentCount: (cb) => ipcRenderer.on('agent-count', (_e, count) => cb(count)),
  onPlayerCmd: (cb) => ipcRenderer.on('player-cmd', (_e, cmd, index) => cb(cmd, index)),
  openMain: () => ipcRenderer.send('open-main'),
  overlayDragStart: (x, y) => ipcRenderer.send('overlay-drag-start', x, y),
  overlayDragMove: (x, y) => ipcRenderer.send('overlay-drag-move', x, y),
  overlayDragEnd: () => ipcRenderer.send('overlay-drag-end'),
});

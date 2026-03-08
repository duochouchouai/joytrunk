/**
 * Electron 主进程：悬浮窗 overlay + 主窗口，多 agent 视频网格。
 * - overlay：无边框、圆角、透明、可拖拽，尺寸随 agent 数量变化（1: 100×100, 2: 140×70, 3-4: 120×120）
 * - Windows 下使用 SetWindowRgn 实现圆角
 */
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

// --- 常量 ---
const ASSETS_DIR = path.join(__dirname, 'assets');
const VIDEO_EXT = new Set(['.mp4', '.webm', '.ogg', '.mov']);
const MAX_AGENTS = 4;
/** 每格像素：1 格 | 2 格 | 3-4 格 */
const CELL_1 = 100;
const CELL_2 = 70;
const CELL_3_4 = 60;
const OVERLAY_RADIUS = 24;

let mainWindow = null;
let overlayWindow = null;
let agentCount = 1;
let draggingWindow = null;
let dragStartScreen = null;
let dragStartPos = null;

function isWindowAlive(win) {
  return win && !win.isDestroyed();
}

/** 根据 agent 数量返回 [width, height] */
function getSizeForCount(n) {
  if (n <= 1) return [CELL_1, CELL_1];
  if (n === 2) return [CELL_2 * 2, CELL_2];
  return [CELL_3_4 * 2, CELL_3_4 * 2];
}

function notifyAgentCount() {
  if (isWindowAlive(mainWindow)) mainWindow.webContents.send('agent-count', agentCount);
  if (isWindowAlive(overlayWindow)) overlayWindow.webContents.send('agent-count', agentCount);
}

function setOverlayWindowRgn(win, width, height) {
  if (process.platform !== 'win32') return;
  try {
    const koffi = require('koffi');
    const user32 = koffi.load('user32.dll');
    const gdi32 = koffi.load('gdi32.dll');
    const CreateRoundRectRgn = gdi32.func('CreateRoundRectRgn', 'void*', ['int', 'int', 'int', 'int', 'int', 'int']);
    const SetWindowRgn = user32.func('SetWindowRgn', 'int', ['void*', 'void*', 'int']);
    const rgn = CreateRoundRectRgn(0, 0, width + 1, height + 1, OVERLAY_RADIUS, OVERLAY_RADIUS);
    SetWindowRgn(win.getNativeWindowHandle(), rgn, 1);
  } catch (err) {
    console.error('SetWindowRgn failed:', err);
  }
}

function clearOverlayWindowRgn(win) {
  if (process.platform !== 'win32') return;
  try {
    const koffi = require('koffi');
    const user32 = koffi.load('user32.dll');
    const SetWindowRgn = user32.func('SetWindowRgn', 'int', ['void*', 'void*', 'int']);
    SetWindowRgn(win.getNativeWindowHandle(), null, 1);
  } catch (err) {
    console.error('ClearWindowRgn failed:', err);
  }
}

function getVideoPaths() {
  try {
    return fs.readdirSync(ASSETS_DIR)
      .filter((name) => VIDEO_EXT.has(path.extname(name).toLowerCase()))
      .map((name) => pathToFileURL(path.join(ASSETS_DIR, name)).href);
  } catch (err) {
    console.error('Read ui/assets failed:', err);
    return [];
  }
}

function createOverlay() {
  const [w, h] = getSizeForCount(agentCount);
  const win = new BrowserWindow({
    width: w,
    height: h,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    thickFrame: false,
    fullscreenable: false,
    maximizable: false,
    minimizable: false,
    backgroundColor: '#00000000',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      scrollBounce: false,
      webSecurity: false,
    },
  });

  win.setMenuBarVisibility(false);
  win.setBackgroundColor('#00000000');
  win.setHasShadow(false);
  win.setMinimumSize(CELL_3_4, CELL_3_4);
  win.loadFile(path.join(__dirname, 'index.html'));

  win.webContents.on('did-finish-load', () => {
    win.webContents.send('video-paths', getVideoPaths());
    win.webContents.send('agent-count', agentCount);
    win.webContents.insertCSS(
      'html,body{overflow:hidden!important;outline:none!important;border:none!important}' +
      '*,*::before,*::after{outline:none!important}' +
      '::-webkit-scrollbar{width:0;height:0;display:none}'
    );
    win.center();
    win.show();
    setOverlayWindowRgn(win, w, h);
    win.focus();
  });
  overlayWindow = win;
}

function resizeOverlay() {
  if (!isWindowAlive(overlayWindow)) return;
  const [w, h] = getSizeForCount(agentCount);
  if (process.platform === 'win32') clearOverlayWindowRgn(overlayWindow);
  const [x, y] = overlayWindow.getPosition();
  overlayWindow.setBounds({ x, y, width: w, height: h });
  overlayWindow.webContents.send('agent-count', agentCount);
  if (process.platform === 'win32') {
    setImmediate(() => {
      if (isWindowAlive(overlayWindow)) setOverlayWindowRgn(overlayWindow, w, h);
    });
  } else {
    setOverlayWindowRgn(overlayWindow, w, h);
  }
}

ipcMain.on('open-main', () => {
  if (isWindowAlive(mainWindow)) {
    mainWindow.focus();
    return;
  }
  mainWindow = new BrowserWindow({
    width: 400,
    height: 340,
    frame: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload-main.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.loadFile(path.join(__dirname, 'main.html'));
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.send('agent-count', agentCount);
  });
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });
});

ipcMain.handle('get-agent-count', () => agentCount);

ipcMain.on('add-agent', () => {
  if (agentCount >= MAX_AGENTS) return;
  agentCount++;
  if (isWindowAlive(overlayWindow)) resizeOverlay();
  else createOverlay();
  notifyAgentCount();
});

ipcMain.on('remove-agent', () => {
  if (agentCount <= 1) return;
  agentCount--;
  if (isWindowAlive(overlayWindow)) resizeOverlay();
  notifyAgentCount();
});

ipcMain.on('agent-play', (_e, index) => {
  if (isWindowAlive(overlayWindow)) overlayWindow.webContents.send('player-cmd', 'play', index);
});

ipcMain.on('agent-pause', (_e, index) => {
  if (isWindowAlive(overlayWindow)) overlayWindow.webContents.send('player-cmd', 'pause', index);
});

ipcMain.on('overlay-drag-start', (e, screenX, screenY) => {
  const win = BrowserWindow.fromWebContents(e.sender);
  if (!win || win.isDestroyed()) return;
  draggingWindow = win;
  dragStartScreen = [screenX, screenY];
  dragStartPos = win.getPosition();
});

ipcMain.on('overlay-drag-move', (_e, screenX, screenY) => {
  if (!draggingWindow || draggingWindow.isDestroyed() || !dragStartScreen || !dragStartPos) return;
  draggingWindow.setPosition(
    dragStartPos[0] + screenX - dragStartScreen[0],
    dragStartPos[1] + screenY - dragStartScreen[1]
  );
});

ipcMain.on('overlay-drag-end', () => {
  draggingWindow = null;
  dragStartScreen = null;
  dragStartPos = null;
});

app.whenReady().then(() => {
  createOverlay();
});

app.on('window-all-closed', () => {
  app.quit();
});

/**
 * Electron 主进程：悬浮窗 overlay + 主窗口，多 agent 视频网格。
 * - overlay：无边框、圆角、透明、可拖拽；agentCount=0 时显示小菜单，1~4 时显示对应数量 agent 视频；尺寸随数量变化（0/1: 100×100, 2: 140×70, 3-4: 120×120）；Windows 下使用 SetWindowRgn 实现圆角。
 * - 主窗口：黄金比例默认尺寸、居中、Windows 下圆角与任务栏圆角图标（logo-white-rounded.png）；图标由 ui/scripts/round-icon.js 从 logo-white.png 生成。
 */
const { app, BrowserWindow, ipcMain, screen } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

// --- 常量 ---
const ASSETS_DIR = path.join(__dirname, 'assets');
/** 应用图标（任务栏/标题栏），Windows 下使用；优先使用圆角版 logo-white-rounded.png，否则用 logo-white.png。打包后从 extraResources 的 imgs 读取 */
function getAppIconPath() {
  const imgsDir = app.isPackaged
    ? path.join(process.resourcesPath, 'imgs')
    : path.join(__dirname, '..', 'imgs');
  const rounded = path.join(imgsDir, 'logo-white-rounded.png');
  const normal = path.join(imgsDir, 'logo-white.png');
  try {
    if (fs.existsSync(rounded)) return rounded;
  } catch (_) { /* ignore */ }
  return normal;
}
const APP_ICON_PATH = getAppIconPath();
const MAX_AGENTS = 4;
/** 每格像素：1 格 | 2 格 | 3-4 格 */
const CELL_1 = 100;
const CELL_2 = 70;
const CELL_3_4 = 60;
const OVERLAY_RADIUS = 24;
/** 主窗口圆角半径（Windows SetWindowRgn） */
const MAIN_WINDOW_RADIUS = 12;

let mainWindow = null;
let overlayWindow = null;
/** 0 = 显示小菜单，1-4 = 显示对应数量 agent 视频 */
let agentCount = 0;
/** 每个 agent 的显示名称，长度 MAX_AGENTS */
let agentNames = ['Agent 1', 'Agent 2', 'Agent 3', 'Agent 4'];
/** 每个 agent 的状态：'idle' 空闲(绿) | 'thinking' 思考中(黄) | 'running' 执行中(红) */
let agentStates = ['idle', 'idle', 'idle', 'idle'];
/** 指示灯：旋转一圈时间(s)、呼吸周期(s) */
let spinDuration = 2;
let breatheDuration = 1.6;
let draggingWindow = null;
let dragStartScreen = null;
let dragStartPos = null;

/** joytrunk server / gateway 子进程（UI 启动时 spawn，退出时 kill） */
let serverProcess = null;
let gatewayProcess = null;

/**
 * 发布态：返回捆绑的 joytrunk 可执行文件路径（extraResources/bin 下）。
 * @param {string} name - 如 'joytrunk-server'、'joytrunk-gateway'
 * @returns {string}
 */
function getBundledJoytrunkBin(name) {
  const base = path.join(process.resourcesPath, 'bin', name);
  return process.platform === 'win32' ? base + '.exe' : base;
}

/**
 * 启动 joytrunk server 或 gateway 子进程。开发态从 PATH  spawn joytrunk；发布态从 resources/bin spawn 捆绑的可执行文件。
 * @param {'server'|'gateway'} subcommand
 * @returns {import('child_process').ChildProcess | null} 成功返回 ChildProcess，失败返回 null
 */
function spawnJoytrunkCommand(subcommand) {
  const isPackaged = app.isPackaged;
  const opts = {
    env: { ...process.env },
    stdio: 'ignore',
  };

  if (isPackaged) {
    const binName = subcommand === 'server' ? 'joytrunk-server' : 'joytrunk-gateway';
    const binPath = getBundledJoytrunkBin(binName);
    if (!fs.existsSync(binPath)) {
      console.error('[joytrunk] Bundled binary not found:', binPath);
      return null;
    }
    try {
      return spawn(binPath, [], opts);
    } catch (err) {
      console.error('[joytrunk] Failed to spawn', binName, err);
      return null;
    }
  }

  try {
    return spawn('joytrunk', [subcommand], opts);
  } catch (err) {
    console.error('[joytrunk] Failed to spawn joytrunk', subcommand, err);
    return null;
  }
}

/** 黄金比例 φ ≈ 1.618，主窗口宽高比 width/height */
const GOLDEN_RATIO = 1.618;
/** 主窗口占工作区最大宽度比例（约为原来的 65%） */
const MAIN_WINDOW_MAX_WIDTH_FRACTION = 0.72 * 0.65;
/** 主窗口占工作区最大高度比例（约为原来的 65%） */
const MAIN_WINDOW_MAX_HEIGHT_FRACTION = 0.88 * 0.65;

/** 根据当前屏幕工作区计算主窗口默认宽高（黄金比例，且不超过工作区比例） */
function getDefaultMainWindowSize() {
  const primary = screen.getPrimaryDisplay();
  const workArea = primary.workArea;
  const maxW = Math.floor(workArea.width * MAIN_WINDOW_MAX_WIDTH_FRACTION);
  const maxH = Math.floor(workArea.height * MAIN_WINDOW_MAX_HEIGHT_FRACTION);
  let w = maxW;
  let h = Math.round(w / GOLDEN_RATIO);
  if (h > maxH) {
    h = maxH;
    w = Math.round(h * GOLDEN_RATIO);
    if (w > workArea.width) {
      w = Math.floor(workArea.width * 0.9);
      h = Math.round(w / GOLDEN_RATIO);
    }
  }
  return [Math.max(640, w), Math.max(400, h)];
}

function isWindowAlive(win) {
  return win && !win.isDestroyed();
}

/** 根据 agent 数量返回 [width, height]；0 为菜单模式尺寸（与 1 格相同） */
function getSizeForCount(n) {
  if (n === 0) return [CELL_1, CELL_1];
  if (n <= 1) return [CELL_1, CELL_1];
  if (n === 2) return [CELL_2 * 2, CELL_2];
  return [CELL_3_4 * 2, CELL_3_4 * 2];
}

function notifyAgentCount() {
  if (isWindowAlive(mainWindow)) mainWindow.webContents.send('agent-count', agentCount);
  if (isWindowAlive(overlayWindow)) overlayWindow.webContents.send('agent-count', agentCount);
}

function notifyAgentNames() {
  const names = agentNames.slice(0, MAX_AGENTS);
  if (isWindowAlive(mainWindow)) mainWindow.webContents.send('agent-names', names);
  if (isWindowAlive(overlayWindow)) overlayWindow.webContents.send('agent-names', names);
}

function notifyAgentStates() {
  const states = agentStates.slice(0, MAX_AGENTS);
  if (isWindowAlive(mainWindow)) mainWindow.webContents.send('agent-states', states);
  if (isWindowAlive(overlayWindow)) overlayWindow.webContents.send('agent-states', states);
}

function notifyIndicatorConfig() {
  const config = { spinDuration, breatheDuration };
  if (isWindowAlive(mainWindow)) mainWindow.webContents.send('indicator-config', config);
  if (isWindowAlive(overlayWindow)) overlayWindow.webContents.send('indicator-config', config);
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

/** 主窗口圆角（Windows）；窗口缩放时需重新设置，最大化时清除 */
function setMainWindowRgn(win) {
  if (process.platform !== 'win32' || !win || win.isDestroyed()) return;
  try {
    const koffi = require('koffi');
    const user32 = koffi.load('user32.dll');
    const gdi32 = koffi.load('gdi32.dll');
    const CreateRoundRectRgn = gdi32.func('CreateRoundRectRgn', 'void*', ['int', 'int', 'int', 'int', 'int', 'int']);
    const SetWindowRgn = user32.func('SetWindowRgn', 'int', ['void*', 'void*', 'int']);
    const [width, height] = win.getSize();
    const rgn = CreateRoundRectRgn(0, 0, width + 1, height + 1, MAIN_WINDOW_RADIUS, MAIN_WINDOW_RADIUS);
    SetWindowRgn(win.getNativeWindowHandle(), rgn, 1);
  } catch (err) {
    console.error('SetMainWindowRgn failed:', err);
  }
}

/** 按角色命名的视频文件名（均在 ui/assets 下）；key 与渲染进程 sources 一致 */
const VIDEO_SOURCES = {
  intro: 'in-scene.mp4',    // 启动欢迎：小象掉入镜头，播一次
  working: 'working.mp4',   // 工作/思考中循环
  zoneOut: 'zone-out.mp4',  // 空闲时循环
};

/** 返回 { intro, working, zoneOut } 的 file URL，缺失则为 null */
function getVideoSources() {
  const result = { intro: null, working: null, zoneOut: null };
  try {
    for (const [key, name] of Object.entries(VIDEO_SOURCES)) {
      const p = path.join(ASSETS_DIR, name);
      if (fs.existsSync(p)) result[key] = pathToFileURL(p).href;
    }
  } catch (err) {
    console.error('Read ui/assets video sources failed:', err);
  }
  return result;
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
    win.webContents.send('video-sources', getVideoSources());
    win.webContents.send('agent-count', agentCount);
    win.webContents.send('agent-names', agentNames.slice(0, MAX_AGENTS));
    win.webContents.send('agent-states', agentStates.slice(0, MAX_AGENTS));
    win.webContents.send('indicator-config', { spinDuration, breatheDuration });
    win.webContents.insertCSS(
      'html,body{overflow:hidden!important;outline:none!important;border:none!important}' +
      '*,*::before,*::after{outline:none!important}' +
      '::-webkit-scrollbar{width:0;height:0;display:none}'
    );
    const primary = screen.getPrimaryDisplay();
    const workArea = primary.workArea || primary.bounds;
    const margin = 16;
    const x = workArea.x + workArea.width - w - margin;
    const y = workArea.y + workArea.height - h - margin;
    win.setPosition(x, y);
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
  const [defaultWidth, defaultHeight] = getDefaultMainWindowSize();
  const primary = screen.getPrimaryDisplay();
  const workArea = primary.workArea;
  const x = Math.round(workArea.x + (workArea.width - defaultWidth) / 2);
  const y = Math.round(workArea.y + (workArea.height - defaultHeight) / 2);
  mainWindow = new BrowserWindow({
    width: defaultWidth,
    height: defaultHeight,
    x,
    y,
    minWidth: 640,
    minHeight: 400,
    icon: APP_ICON_PATH,
    frame: false,
    show: false,
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: path.resolve(__dirname, 'preload-main.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });
  mainWindow.loadFile(path.join(__dirname, 'main.html'));
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.send('agent-count', agentCount);
    mainWindow.webContents.send('agent-names', agentNames.slice(0, MAX_AGENTS));
    mainWindow.webContents.send('agent-states', agentStates.slice(0, MAX_AGENTS));
    mainWindow.webContents.send('indicator-config', { spinDuration, breatheDuration });
  });
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
    if (process.platform === 'win32') setMainWindowRgn(mainWindow);
  });
  mainWindow.on('resize', () => {
    if (process.platform !== 'win32' || !isWindowAlive(mainWindow)) return;
    if (mainWindow.isMaximized()) clearOverlayWindowRgn(mainWindow);
    else setMainWindowRgn(mainWindow);
  });
  mainWindow.on('unmaximize', () => {
    if (process.platform === 'win32' && isWindowAlive(mainWindow)) setMainWindowRgn(mainWindow);
  });
});

ipcMain.handle('get-agent-count', () => agentCount);

ipcMain.handle('get-agent-names', () => agentNames.slice(0, MAX_AGENTS));

ipcMain.handle('get-agent-states', () => agentStates.slice(0, MAX_AGENTS));

ipcMain.handle('get-indicator-config', () => ({ spinDuration, breatheDuration }));

ipcMain.on('set-indicator-config', (_e, payload) => {
  if (payload == null || typeof payload !== 'object') return;
  if (typeof payload.spinDuration === 'number' && payload.spinDuration >= 0.5 && payload.spinDuration <= 10) {
    spinDuration = payload.spinDuration;
  }
  if (typeof payload.breatheDuration === 'number' && payload.breatheDuration >= 0.3 && payload.breatheDuration <= 5) {
    breatheDuration = payload.breatheDuration;
  }
  notifyIndicatorConfig();
});

ipcMain.on('set-agent-name', (_e, index, name) => {
  if (typeof index !== 'number' || index < 0 || index >= MAX_AGENTS) return;
  const s = String(name).trim();
  agentNames[index] = s || 'Agent ' + (index + 1);
  notifyAgentNames();
});

const VALID_STATES = new Set(['idle', 'thinking', 'running']);
ipcMain.on('set-agent-state', (_e, index, state) => {
  if (typeof index !== 'number' || index < 0 || index >= MAX_AGENTS) return;
  if (!VALID_STATES.has(state)) return;
  agentStates[index] = state;
  notifyAgentStates();
});

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

/** 关闭指定索引的 agent：从列表中移除该位，后续前移，count 减 1；若变为 0 则 overlay 显示小菜单 */
ipcMain.on('remove-agent-at', (_e, index) => {
  if (typeof index !== 'number' || index < 0 || index >= agentCount) return;
  if (agentCount <= 0) return;
  agentNames.splice(index, 1);
  agentStates.splice(index, 1);
  agentCount--;
  agentNames.push('Agent ' + (agentCount + 1));
  agentStates.push('idle');
  if (isWindowAlive(overlayWindow)) resizeOverlay();
  notifyAgentCount();
  notifyAgentNames();
  notifyAgentStates();
});

/** 从菜单选择“以 n 个 agent 启动”：直接进入视频流程 */
ipcMain.on('start-with-agents', (_e, n) => {
  if (typeof n !== 'number' || n < 1 || n > MAX_AGENTS) return;
  agentCount = n;
  if (isWindowAlive(overlayWindow)) resizeOverlay();
  else createOverlay();
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

/** 主窗口：关闭、最小化（无边框时由渲染进程请求） */
ipcMain.on('main-window-close', () => {
  if (isWindowAlive(mainWindow)) mainWindow.close();
});
ipcMain.on('main-window-minimize', () => {
  if (isWindowAlive(mainWindow)) mainWindow.minimize();
});

app.whenReady().then(() => {
  createOverlay();
  // 后台启动 joytrunk server 与 gateway，便于设备连接
  serverProcess = spawnJoytrunkCommand('server');
  if (serverProcess) {
    serverProcess.on('error', (err) => console.error('[joytrunk server] error', err));
    serverProcess.on('exit', (code, sig) => {
      if (code != null && code !== 0) console.error('[joytrunk server] exit', code, sig);
      serverProcess = null;
    });
  }
  gatewayProcess = spawnJoytrunkCommand('gateway');
  if (gatewayProcess) {
    gatewayProcess.on('error', (err) => console.error('[joytrunk gateway] error', err));
    gatewayProcess.on('exit', (code, sig) => {
      if (code != null && code !== 0) console.error('[joytrunk gateway] exit', code, sig);
      gatewayProcess = null;
    });
  }
});

app.on('before-quit', () => {
  if (serverProcess && !serverProcess.killed) {
    serverProcess.kill('SIGTERM');
    serverProcess = null;
  }
  if (gatewayProcess && !gatewayProcess.killed) {
    gatewayProcess.kill('SIGTERM');
    gatewayProcess = null;
  }
});

app.on('window-all-closed', () => {
  app.quit();
});

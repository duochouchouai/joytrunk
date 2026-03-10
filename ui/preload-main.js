/** Preload：主窗口与主进程 IPC 桥（整体 try/catch，确保任何错误下仍暴露 electronAPI） */
(function () {
  const SERVER_BASE_URL = 'http://127.0.0.1:32901';
  let ownerId = '';

  function getServerBaseUrl() {
    return SERVER_BASE_URL;
  }

  function getHeaders() {
    const h = { 'Content-Type': 'application/json' };
    if (ownerId) h['X-Owner-Id'] = ownerId;
    return h;
  }

  async function apiFetch(method, path, body) {
    const url = SERVER_BASE_URL + path;
    const opts = { method, headers: getHeaders() };
    if (body !== undefined && body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (_) {
      data = null;
    }
    if (!res.ok) {
      const err = new Error(data && data.error ? data.error : text || res.statusText);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  const serverAPI = {
    getServerBaseUrl,
    getOwnerId: () => ownerId,
    setOwnerId: (id) => { ownerId = id || ''; },
    getHealth: () => apiFetch('GET', '/api/health'),
    getOwnersMe: () => apiFetch('GET', '/api/owners/me'),
    getEmployees: () => apiFetch('GET', '/api/employees'),
    createEmployee: (body) => apiFetch('POST', '/api/employees', body),
    getEmployee: (id) => apiFetch('GET', '/api/employees/' + encodeURIComponent(id)),
    getChatHistory: (employeeId) => apiFetch('GET', '/api/employees/' + encodeURIComponent(employeeId) + '/chat-history'),
    postChat: (employeeId, body) => apiFetch('POST', '/api/employees/' + encodeURIComponent(employeeId) + '/chat', body),
  };

  try {
    const { contextBridge, ipcRenderer } = require('electron');
    const path = require('path');

    let logoUrl = '';
    let logoBgUrl = '';
    try {
      const dir = path.join(__dirname, '..', 'imgs');
      logoUrl = 'file:///' + path.join(dir, 'logo-no-word.png').replace(/\\/g, '/');
      logoBgUrl = 'file:///' + path.join(dir, 'logo.png').replace(/\\/g, '/');
    } catch (e) {
      console.error('preload-main logo path:', e);
    }

    contextBridge.exposeInMainWorld('electronAPI', {
      getLogoUrl: () => logoUrl,
      getLogoBgUrl: () => logoBgUrl,
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
      closeWindow: () => ipcRenderer.send('main-window-close'),
      minimizeWindow: () => ipcRenderer.send('main-window-minimize'),
      serverAPI,
    });
  } catch (err) {
    console.error('preload-main failed:', err);
    try {
      const { contextBridge, ipcRenderer } = require('electron');
      contextBridge.exposeInMainWorld('electronAPI', {
        getLogoUrl: () => '',
        getLogoBgUrl: () => '',
        getAgentCount: () => Promise.resolve(0),
        getAgentNames: () => Promise.resolve([]),
        getAgentStates: () => Promise.resolve([]),
        getIndicatorConfig: () => Promise.resolve({}),
        onAgentCount: () => {},
        onAgentNames: () => {},
        onAgentStates: () => {},
        onIndicatorConfig: () => {},
        setAgentName: () => {},
        setAgentState: () => {},
        setIndicatorConfig: () => {},
        addAgent: () => {},
        removeAgent: () => {},
        agentPlay: () => {},
        agentPause: () => {},
        closeWindow: () => ipcRenderer.send('main-window-close'),
        minimizeWindow: () => ipcRenderer.send('main-window-minimize'),
        serverAPI: {
          getServerBaseUrl: () => SERVER_BASE_URL,
          getOwnerId: () => '',
          setOwnerId: () => {},
          getHealth: () => Promise.reject(new Error('preload failed')),
          getOwnersMe: () => Promise.reject(new Error('preload failed')),
          getEmployees: () => Promise.reject(new Error('preload failed')),
          createEmployee: () => Promise.reject(new Error('preload failed')),
          getEmployee: () => Promise.reject(new Error('preload failed')),
          getChatHistory: () => Promise.reject(new Error('preload failed')),
          postChat: () => Promise.reject(new Error('preload failed')),
        },
      });
    } catch (e) {
      console.error('preload-main fallback failed:', e);
    }
  }
})();

/**
 * 官网 API：使用 VITE_API_BASE，为空则同源
 */
function getBase() {
  return import.meta.env.VITE_API_BASE || ''
}

function getToken() {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem('joytrunk_token') || localStorage.getItem('joytrunk_owner_id');
}

function getOwnerId() {
  return typeof localStorage !== 'undefined' ? localStorage.getItem('joytrunk_owner_id') : null;
}

function setToken(tokenOrId) {
  if (typeof localStorage === 'undefined') return;
  if (tokenOrId && typeof tokenOrId === 'string' && tokenOrId.length < 50) {
    localStorage.setItem('joytrunk_owner_id', tokenOrId);
    return;
  }
  if (tokenOrId) localStorage.setItem('joytrunk_token', tokenOrId);
}

function clearToken() {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('joytrunk_token');
    localStorage.removeItem('joytrunk_owner_id');
  }
}

async function request(method, path, body) {
  const url = getBase() + path;
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) {
    if (token.length > 50) headers['Authorization'] = `Bearer ${token}`;
    else headers['X-Owner-Id'] = token;
  }
  const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith('/api/auth/')) {
      clearToken();
      if (typeof window !== 'undefined') window.location.href = '/login';
    }
    const err = new Error(data.error || res.statusText);
    err.code = data.code;
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  getOwnerId,
  auth: {
    register: (body) => request('POST', '/api/auth/register', body),
    login: () => request('POST', '/api/auth/login', {}),
    sendCode: (body) => request('POST', '/api/auth/send-code', body),
    loginByCode: (body) => request('POST', '/api/auth/login-by-code', body),
    sendEmailCode: (body) => request('POST', '/api/auth/send-email-code', body),
    loginByEmailCode: (body) => request('POST', '/api/auth/login-by-email-code', body),
    loginByPassword: (body) => request('POST', '/api/auth/login-by-password', body),
  },
  owners: {
    me: () => request('GET', '/api/owners/me'),
  },
  users: {
    me: () => request('GET', '/api/users/me'),
    updatePassword: (body) => request('PATCH', '/api/users/me/password', body),
    deactivate: () => request('POST', '/api/users/me/deactivate', {}),
  },
  employees: {
    list: () => request('GET', '/api/employees'),
    create: (body) => request('POST', '/api/employees', body),
    get: (id) => request('GET', `/api/employees/${id}`),
    update: (id, body) => request('PATCH', `/api/employees/${id}`, body),
    chat: (id, body) => request('POST', `/api/employees/${id}/chat`, body),
    logs: (id) => request('GET', `/api/employees/${id}/logs`),
  },
  teams: {
    current: () => request('GET', '/api/teams/current'),
  },
  config: () => request('GET', '/api/config'),
  configPatchCustomLLM: (body) => request('PATCH', '/api/config/custom-llm', body),
  configClearCustomLLM: () => request('DELETE', '/api/config/custom-llm'),
  usage: () => request('GET', '/api/usage'),
  im: {
    conversations: () => request('GET', '/api/im/conversations'),
    createConversation: (body) => request('POST', '/api/im/conversations', body),
    participants: (id, params = {}) => {
      const q = new URLSearchParams(params).toString();
      return request('GET', `/api/im/conversations/${id}/participants${q ? '?' + q : ''}`);
    },
    messages: (id, params = {}) => {
      const q = new URLSearchParams(params).toString();
      return request('GET', `/api/im/conversations/${id}/messages${q ? '?' + q : ''}`);
    },
    send: (id, body) => request('POST', `/api/im/conversations/${id}/messages`, body),
    markRead: (id, body) => request('PATCH', `/api/im/conversations/${id}/read`, body),
    leave: (id) => request('POST', `/api/im/conversations/${id}/leave`, {}),
    dismiss: (id) => request('POST', `/api/im/conversations/${id}/dismiss`, {}),
    updateConversation: (id, body) => request('PATCH', `/api/im/conversations/${id}`, body),
    addParticipants: (id, body) => request('POST', `/api/im/conversations/${id}/participants`, body),
    removeParticipant: (id, userId) => request('DELETE', `/api/im/conversations/${id}/participants/${userId}`, {}),
    updateParticipant: (id, userId, body) => request('PATCH', `/api/im/conversations/${id}/participants/${userId}`, body),
  },
};

export { getToken, setToken, clearToken, getOwnerId };

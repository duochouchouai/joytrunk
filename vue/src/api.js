/**
 * 官网 API：使用 VITE_API_BASE，为空则同源
 */
function getBase() {
  return import.meta.env.VITE_API_BASE || ''
}

function getToken() {
  return typeof localStorage !== 'undefined' ? localStorage.getItem('joytrunk_owner_id') : null;
}

function setToken(id) {
  if (typeof localStorage !== 'undefined') localStorage.setItem('joytrunk_owner_id', id);
}

function clearToken() {
  if (typeof localStorage !== 'undefined') localStorage.removeItem('joytrunk_owner_id');
}

async function request(method, path, body) {
  const url = getBase() + path;
  const headers = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) headers['X-Owner-Id'] = t;
  const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

export const api = {
  auth: {
    register: (body) => request('POST', '/api/auth/register', body),
    login: () => request('POST', '/api/auth/login', {}),
    sendCode: (body) => request('POST', '/api/auth/send-code', body),
    loginByCode: (body) => request('POST', '/api/auth/login-by-code', body),
  },
  owners: {
    me: () => request('GET', '/api/owners/me'),
  },
  employees: {
    list: () => request('GET', '/api/employees'),
    create: (body) => request('POST', '/api/employees', body),
    get: (id) => request('GET', `/api/employees/${id}`),
    update: (id, body) => request('PATCH', `/api/employees/${id}`, body),
    chat: (id, body) => request('POST', `/api/employees/${id}/chat`, body),
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
    messages: (id, params = {}) => {
      const q = new URLSearchParams(params).toString()
      return request('GET', `/api/im/conversations/${id}/messages${q ? '?' + q : ''}`)
    },
    send: (id, body) => request('POST', `/api/im/conversations/${id}/messages`, body),
  },
};

export { getToken, setToken, clearToken };

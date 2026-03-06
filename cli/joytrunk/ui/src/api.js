/**
 * 本地管理界面 API：与 server 同源（由 server 提供静态与 /api）
 */
function getBase() {
  return ''
}

function getToken() {
  return typeof localStorage !== 'undefined' ? localStorage.getItem('joytrunk_owner_id') : null
}

function setToken(id) {
  if (typeof localStorage !== 'undefined') localStorage.setItem('joytrunk_owner_id', id)
}

function clearToken() {
  if (typeof localStorage !== 'undefined') localStorage.removeItem('joytrunk_owner_id')
}

async function request(method, path, body) {
  const url = getBase() + path
  const headers = { 'Content-Type': 'application/json' }
  const t = getToken()
  if (t) headers['X-Owner-Id'] = t
  const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = data.error || (res.status === 404 ? '员工不存在或无权访问' : res.statusText)
    throw new Error(msg)
  }
  return data
}

export const api = {
  auth: {
    register: (body) => request('POST', '/api/auth/register', body),
    login: () => request('POST', '/api/auth/login', {}),
  },
  owners: { me: () => request('GET', '/api/owners/me') },
  employees: {
    list: () => request('GET', '/api/employees'),
    create: (body) => request('POST', '/api/employees', body),
    get: (id) => request('GET', `/api/employees/${id}`),
    update: (id, body) => request('PATCH', `/api/employees/${id}`, body),
    chat: (id, body) => request('POST', `/api/employees/${id}/chat`, body),
    chatHistory: (id) => request('GET', `/api/employees/${id}/chat-history`),
    logs: (id) => request('GET', `/api/employees/${id}/logs`),
    memory: (id) => request('GET', `/api/employees/${id}/memory`),
    systemPromptTemplate: async (id) => {
      const t = getToken();
      const res = await fetch(getBase() + `/api/employees/${id}/system-prompt-template`, {
        headers: t ? { 'X-Owner-Id': t } : {},
      });
      if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
      return res.text();
    },
    /** 模板与 memory.db 合并后的系统提示词（供记忆页右侧展示） */
    systemPromptMerged: async (id) => {
      const t = getToken();
      const res = await fetch(getBase() + `/api/employees/${id}/system-prompt-merged`, {
        headers: t ? { 'X-Owner-Id': t } : {},
      });
      if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
      return res.text();
    },
    memoryCategoryCreate: (id, body) => request('POST', `/api/employees/${id}/memory/categories`, body),
    memoryCategoryUpdate: (id, cid, body) => request('PATCH', `/api/employees/${id}/memory/categories/${cid}`, body),
    memoryCategoryDelete: (id, cid) => request('DELETE', `/api/employees/${id}/memory/categories/${cid}`),
    memoryItemCreate: (id, body) => request('POST', `/api/employees/${id}/memory/items`, body),
    memoryItemUpdate: (id, iid, body) => request('PATCH', `/api/employees/${id}/memory/items/${iid}`, body),
    memoryItemDelete: (id, iid) => request('DELETE', `/api/employees/${id}/memory/items/${iid}`),
    memoryResourceCreate: (id, body) => request('POST', `/api/employees/${id}/memory/resources`, body),
    memoryResourceUpdate: (id, rid, body) => request('PATCH', `/api/employees/${id}/memory/resources/${rid}`, body),
    memoryResourceDelete: (id, rid) => request('DELETE', `/api/employees/${id}/memory/resources/${rid}`),
    memoryRelationCreate: (id, body) => request('POST', `/api/employees/${id}/memory/relations`, body),
    memoryRelationDelete: (id, relId) => request('DELETE', `/api/employees/${id}/memory/relations/${relId}`),
  },
  teams: { current: () => request('GET', '/api/teams/current') },
  config: () => request('GET', '/api/config'),
  configPatchCustomLLM: (body) => request('PATCH', '/api/config/custom-llm', body),
  configClearCustomLLM: () => request('DELETE', '/api/config/custom-llm'),
  usage: () => request('GET', '/api/usage'),
}

export { getToken, setToken, clearToken }

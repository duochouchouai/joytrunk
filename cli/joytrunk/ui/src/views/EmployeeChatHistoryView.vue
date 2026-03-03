<template>
  <div class="page">
    <div class="page-header">
      <router-link to="/employees" class="back-link">{{ t('chatHistory.backToEmployees') }}</router-link>
      <h1 class="page-title">{{ t('chatHistory.title') }} · {{ employeeName || employeeId }}</h1>
      <button type="button" class="btn secondary" :disabled="loading" @click="load">
        {{ loading ? t('common.loading') : t('common.refresh') }}
      </button>
    </div>
    <div class="chat-panel">
      <p v-if="loadError" class="error">{{ loadError }}</p>
      <p v-else-if="!loading && messages.length === 0" class="empty-hint">{{ t('chatHistory.empty') }}</p>
      <div v-else class="message-list">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-wrap"
          :class="'role-' + (msg.role || 'user')"
        >
          <div class="message-bubble">
            <div class="message-meta">
              <span class="message-role-label">{{ roleLabel(msg.role) }}</span>
              <span class="message-time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <!-- 用户 / 助手文本 -->
            <div v-if="msg.role === 'tool'" class="message-body tool-body">
              <span class="tool-name">{{ msg.extra?.name || 'tool' }}</span>
              <pre class="tool-content">{{ textContent(msg) }}</pre>
            </div>
            <div v-else class="message-body" v-html="renderContent(msg)"></div>
            <!-- 助手的工具调用 -->
            <div v-if="msg.role === 'assistant' && (msg.extra?.tool_calls?.length)" class="tool-calls">
              <div class="tool-calls-label">{{ t('chatHistory.toolCalls') }}</div>
              <div
                v-for="(tc, i) in msg.extra.tool_calls"
                :key="i"
                class="tool-call-item"
              >
                <span class="tool-call-name">{{ tc.function?.name || tc.name }}</span>
                <pre v-if="tc.function?.arguments" class="tool-call-args">{{ formatArgs(tc.function.arguments) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-input-bar">
      <input
        v-model="inputText"
        type="text"
        class="chat-input"
        :placeholder="t('chatHistory.inputPlaceholder')"
        :disabled="sending"
        @keydown.enter.prevent="sendMessage"
      />
      <button
        type="button"
        class="btn primary send-btn"
        :disabled="sending || !inputText.trim()"
        @click="sendMessage"
      >
        {{ sending ? t('chatHistory.sending') : t('chatHistory.send') }}
      </button>
      <p v-if="sendError" class="send-error">{{ sendError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { marked } from 'marked'
import { api } from '../api'

const THINK_PLACEHOLDER = '<span data-think-placeholder></span>'

const { t } = useI18n()
const route = useRoute()
const employeeId = computed(() => route.params.id)
const messages = ref([])
const loading = ref(false)
const loadError = ref('')
const employeeName = ref('')

function roleLabel(role) {
  const r = (role || 'user').toLowerCase()
  if (r === 'user') return t('chatHistory.roleUser')
  if (r === 'assistant') return t('chatHistory.roleAssistant')
  if (r === 'tool') return t('chatHistory.roleTool')
  return role
}

function formatTime(createdAt) {
  if (!createdAt) return ''
  try {
    const d = new Date(createdAt)
    return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'medium' })
  } catch {
    return createdAt
  }
}

function textContent(msg) {
  const c = msg.content
  if (typeof c === 'string') return c
  if (msg.extra?.content) return typeof msg.extra.content === 'string' ? msg.extra.content : JSON.stringify(msg.extra.content)
  return c != null ? String(c) : ''
}

function extractThinkBlocks(text) {
  const parts = []
  const re = /<think>([\s\S]*?)<\/think>/gi
  const textWithoutThink = text.replace(re, (_, inner) => {
    parts.push(inner)
    return '\n\n' + THINK_PLACEHOLDER + '\n\n'
  })
  return { textWithoutThink, parts }
}

function renderContent(msg) {
  let text = textContent(msg)
  if (!text) return ''
  const { textWithoutThink, parts } = extractThinkBlocks(text)
  let html = marked.parse(textWithoutThink, { async: false })
  parts.forEach((inner) => {
    const escaped = inner
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>')
    const span = `<span class="think-block" title="思考过程"><span class="think-label">${t('chatHistory.thinking')}</span>${escaped}</span>`
    html = html.replace(THINK_PLACEHOLDER, span)
  })
  return html.replace(/<span data-think-placeholder><\/span>/g, '')
}

function formatArgs(args) {
  if (typeof args !== 'string') return ''
  try {
    const o = JSON.parse(args)
    return JSON.stringify(o, null, 2)
  } catch {
    return args
  }
}

async function load() {
  if (!employeeId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const data = await api.employees.chatHistory(employeeId.value)
    messages.value = Array.isArray(data.messages) ? data.messages : []
  } catch (e) {
    const msg = e.message || ''
    const isNetworkError = /fetch failed|Failed to fetch|NetworkError|network error/i.test(msg)
    loadError.value = isNetworkError ? t('chatHistory.networkError') : (msg || t('chatHistory.loadFailed'))
    messages.value = []
  } finally {
    loading.value = false
  }
}

async function loadEmployeeName() {
  if (!employeeId.value) return
  try {
    const team = await api.teams.current()
    const emp = (team.employees || []).find((e) => e.id === employeeId.value)
    employeeName.value = emp ? emp.name : ''
  } catch {
    employeeName.value = ''
  }
}

const inputText = ref('')
const sending = ref(false)
const sendError = ref('')

async function sendMessage() {
  if (!employeeId.value || !inputText.value.trim() || sending.value) return
  sending.value = true
  sendError.value = ''
  const content = inputText.value.trim()
  inputText.value = ''
  try {
    await api.employees.chat(employeeId.value, { content })
    await load()
  } catch (e) {
    const msg = e.message || ''
    const isNetworkError = /fetch failed|Failed to fetch|NetworkError|network error/i.test(msg)
    sendError.value = isNetworkError ? t('chatHistory.networkError') : (msg || t('chatHistory.sendFailed'))
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  loadEmployeeName()
  load()
})
watch(employeeId, () => {
  loadEmployeeName()
  load()
})
</script>

<style scoped>
.page { max-width: 720px; margin: 0 auto; }
.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}
.back-link {
  color: var(--jt-primary);
  text-decoration: none;
  font-size: 0.9375rem;
}
.back-link:hover { text-decoration: underline; }
.page-title { margin: 0; font-size: 1.25rem; font-weight: 600; flex: 1; }
.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  cursor: pointer;
  border: 1px solid var(--jt-border);
  background: var(--jt-card-bg);
}
.btn.secondary:hover:not(:disabled) { background: var(--jt-border); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.chat-panel {
  background: var(--jt-card-bg);
  border-radius: var(--jt-radius);
  box-shadow: var(--jt-card-shadow);
  padding: 1.25rem 1.5rem;
  min-height: 200px;
}
.error { color: #b91c1c; font-size: 0.875rem; margin: 0; }
.empty-hint { color: var(--jt-text-muted); font-size: 0.9375rem; margin: 0; }

.message-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.message-wrap {
  display: flex;
  width: 100%;
}
.message-wrap.role-user { justify-content: flex-end; }
.message-wrap.role-assistant,
.message-wrap.role-tool { justify-content: flex-start; }

.message-bubble {
  max-width: 88%;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  border: 1px solid var(--jt-border);
}
.message-wrap.role-user .message-bubble {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.35);
}
.message-wrap.role-assistant .message-bubble {
  background: var(--jt-bg);
  border-color: var(--jt-border);
}
.message-wrap.role-tool .message-bubble {
  background: rgba(107, 114, 128, 0.08);
  border-color: rgba(107, 114, 128, 0.2);
  max-width: 95%;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
}
.message-role-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--jt-text-muted);
}
.message-time {
  font-size: 0.7rem;
  color: var(--jt-text-muted);
}

.message-body {
  font-size: 0.9375rem;
  line-height: 1.55;
  word-break: break-word;
  white-space: pre-wrap;
}
.message-body :deep(p) { margin: 0.35em 0; }
.message-body :deep(p:first-child) { margin-top: 0; }
.message-body :deep(p:last-child) { margin-bottom: 0; }
.message-body :deep(code) {
  background: var(--jt-bg);
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  font-size: 0.875em;
}
.message-body :deep(pre) {
  margin: 0.5rem 0;
  padding: 0.5rem 0.75rem;
  background: var(--jt-bg);
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.8125rem;
}
.message-body :deep(.think-block) {
  display: block;
  margin: 0.5rem 0;
  padding: 0.5rem 0.75rem;
  background: rgba(107, 114, 128, 0.1);
  border-left: 3px solid #6b7280;
  border-radius: 4px;
  font-size: 0.8125rem;
  color: var(--jt-text-muted);
  white-space: pre-wrap;
}
.message-body :deep(.think-label) {
  display: block;
  font-weight: 600;
  font-size: 0.7rem;
  margin-bottom: 0.25rem;
}

.tool-body { margin-top: 0.25rem; }
.tool-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--jt-primary);
  display: block;
  margin-bottom: 0.25rem;
}
.tool-content {
  margin: 0;
  font-size: 0.8125rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 12rem;
  overflow-y: auto;
}

.tool-calls {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px dashed var(--jt-border);
}
.tool-calls-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--jt-text-muted);
  margin-bottom: 0.35rem;
}
.tool-call-item {
  font-size: 0.8125rem;
  margin-bottom: 0.25rem;
}
.tool-call-name {
  color: var(--jt-primary);
  font-weight: 500;
}
.tool-call-args {
  margin: 0.15rem 0 0 0.75rem;
  padding: 0.25rem 0.5rem;
  background: var(--jt-bg);
  border-radius: 4px;
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
}

.chat-input-bar {
  margin-top: 1rem;
  padding: 1rem 0;
  border-top: 1px solid var(--jt-border);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}
.chat-input {
  flex: 1;
  min-width: 200px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--jt-border);
  border-radius: 6px;
  font-size: 0.9375rem;
}
.chat-input:disabled { opacity: 0.7; cursor: not-allowed; }
.send-btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  cursor: pointer;
  border: none;
  background: var(--jt-primary);
  color: #fff;
}
.send-btn:hover:not(:disabled) { background: var(--jt-primary-hover); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.send-error {
  width: 100%;
  margin: 0;
  font-size: 0.875rem;
  color: #b91c1c;
}
</style>
